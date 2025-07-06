import customtkinter
import logging
import threading
from config import SUPPORTED_LANGUAGES
from world_manager_app import WorldManagerApp
from settings_app import SettingsApp
from app_settings import AppSettings
from ui_components import ChatBubble


class MainMenuApp(customtkinter.CTk):
    """
    The main application window, which serves as a chat-centric dashboard.
    """

    def __init__(self, data_manager, api_service, app_settings):
        super().__init__()
        self.db = data_manager
        self.ai = api_service
        self.settings = app_settings
        self.toplevel_window = None

        customtkinter.set_appearance_mode(self.settings.get("theme"))

        self.title("DM's AI Toolkit")
        self.state('zoomed')
        self.minsize(1000, 700)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._create_widgets()
        self.refresh_display()

    def _create_widgets(self):
        self.sidebar_frame = customtkinter.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsw")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        customtkinter.CTkLabel(self.sidebar_frame, text="Tools",
                               font=customtkinter.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20,
                                                                                        pady=(20, 10))
        self.launch_char_button = customtkinter.CTkButton(self.sidebar_frame, text="Character Manager",
                                                          state="disabled")
        self.launch_char_button.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        customtkinter.CTkLabel(self.sidebar_frame, text="Coming Soon...",
                               font=customtkinter.CTkFont(size=12, slant="italic")).grid(row=2, column=0, padx=20,
                                                                                         pady=20)
        self.manage_worlds_button = customtkinter.CTkButton(self.sidebar_frame, text="Manage Worlds",
                                                            command=self.launch_world_manager)
        self.manage_worlds_button.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        self.settings_button = customtkinter.CTkButton(self.sidebar_frame, text="Settings",
                                                       command=self.launch_settings)
        self.settings_button.grid(row=6, column=0, padx=20, pady=20, sticky="s")

        self.main_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        self.top_bar_frame = customtkinter.CTkFrame(self.main_frame, height=40)
        self.top_bar_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))
        self.top_bar_frame.grid_columnconfigure(0, weight=1)

        self.campaign_title_label = customtkinter.CTkLabel(self.top_bar_frame, text="No Campaign Selected",
                                                           font=customtkinter.CTkFont(size=24, weight="bold"))
        self.campaign_title_label.pack(side="left", padx=20, pady=5)

        self.campaign_info_label = customtkinter.CTkLabel(self.top_bar_frame,
                                                          text="Go to Settings to select a campaign.",
                                                          font=customtkinter.CTkFont(size=14))
        self.campaign_info_label.pack(side="left", padx=20, pady=5)

        self.chat_tab_view = customtkinter.CTkTabview(self.main_frame)
        self.chat_tab_view.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        self.chat_tab_view.add("Lore Master")
        self.chat_tab_view.add("Rules Lawyer")
        self.chat_tab_view.add("NPC Actor")

        self.lore_master_chat_frame = self._create_chat_ui(self.chat_tab_view.tab("Lore Master"), "lore_master")
        self.rules_lawyer_chat_frame = self._create_chat_ui(self.chat_tab_view.tab("Rules Lawyer"), "rules_lawyer")
        customtkinter.CTkLabel(self.chat_tab_view.tab("NPC Actor"), text="NPC Actor Coming Soon!").pack(pady=50)

    def _create_chat_ui(self, parent_tab, persona):
        parent_tab.grid_columnconfigure(0, weight=1)
        parent_tab.grid_rowconfigure(0, weight=1)

        chat_history_frame = customtkinter.CTkScrollableFrame(parent_tab, label_text="Conversation")
        chat_history_frame.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)

        input_frame = customtkinter.CTkFrame(parent_tab, fg_color="transparent")
        input_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        input_frame.grid_columnconfigure(0, weight=1)

        chat_entry = customtkinter.CTkEntry(input_frame,
                                            placeholder_text=f"Ask the {persona.replace('_', ' ').title()}...")
        chat_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        chat_entry.bind("<Return>",
                        lambda event, e=chat_entry, h=chat_history_frame, p=persona: self.send_message(event, e, h, p))

        send_button = customtkinter.CTkButton(input_frame, text="Send", width=100,
                                              command=lambda e=chat_entry, h=chat_history_frame,
                                                             p=persona: self.send_message(None, e, h, p))
        send_button.grid(row=0, column=1, sticky="e")

        clear_button = customtkinter.CTkButton(input_frame, text="Clear", width=70, fg_color="gray50",
                                               hover_color="gray30",
                                               command=lambda h=chat_history_frame, p=persona: self.clear_chat(h, p))
        clear_button.grid(row=0, column=2, padx=(10, 0), sticky="e")

        return chat_history_frame

    def send_message(self, event, entry_widget, history_frame, persona):
        user_message = entry_widget.get()
        if not user_message.strip():
            return

        entry_widget.delete(0, "end")
        ChatBubble(history_frame, message=user_message, role="user")

        thinking_bubble = ChatBubble(history_frame, message="Thinking...", role="model")
        self.update_idletasks()
        history_frame._parent_canvas.yview_moveto(1.0)

        threading.Thread(target=self.get_ai_response, args=(user_message, persona, thinking_bubble),
                         daemon=True).start()

    def get_ai_response(self, user_message, persona, thinking_bubble):
        try:
            response_text = self.ai.send_chat_message(user_message, persona)
            self.after(0, lambda: thinking_bubble.destroy())
            self.after(0, lambda: ChatBubble(thinking_bubble.master, message=response_text, role="model"))
            self.after(0, lambda: thinking_bubble.master._parent_canvas.yview_moveto(1.0))
        except Exception as e:
            logging.error(f"Error getting AI response: {e}")
            self.after(0, lambda: thinking_bubble.destroy())
            self.after(0, lambda: ChatBubble(thinking_bubble.master, message=f"Error: {e}", role="model"))

    def clear_chat(self, history_frame, persona):
        for widget in history_frame.winfo_children():
            widget.destroy()
        self.ai.clear_chat_session(persona)
        logging.info(f"Chat history for '{persona}' cleared.")

    def refresh_display(self):
        logging.info("Refreshing main display...")
        self.settings._load_settings()

        world_id = self.settings.get("active_world_id")
        campaign_id = self.settings.get("active_campaign_id")
        lang = self.settings.get("active_language")

        world_name, campaign_name = "N/A", "No Campaign Selected"
        info_text = "Go to Settings to select your active world and campaign."

        if world_id:
            world_trans = self.db.get_world_translation(world_id, lang)
            if world_trans: world_name = world_trans['world_name']

        if campaign_id:
            all_campaigns = self.db.get_campaigns_for_world(world_id)
            campaign_data = next((c for c in all_campaigns if c['campaign_id'] == campaign_id), None)
            if campaign_data:
                campaign_name = campaign_data['campaign_name']
                info_text = f"World: {world_name}  |  Language: {SUPPORTED_LANGUAGES.get(lang, lang)}"
                self.launch_char_button.configure(state="normal")
            else:
                self.settings.set("active_campaign_id", None);
                self.settings.save()
                self.launch_char_button.configure(state="disabled")
        else:
            self.launch_char_button.configure(state="disabled")

        self.title(f"DM's AI Toolkit - {campaign_name}")
        self.campaign_title_label.configure(text=campaign_name)
        self.campaign_info_label.configure(text=info_text)

    def open_toplevel(self, window_class, **kwargs):
        if self.toplevel_window is not None and self.toplevel_window.winfo_exists():
            self.toplevel_window.destroy()

        self.toplevel_window = window_class(master=self, **kwargs)
        self.toplevel_window.grab_set()

    def launch_world_manager(self):
        self.open_toplevel(WorldManagerApp, data_manager=self.db, api_service=self.ai)

    def launch_settings(self):
        self.open_toplevel(SettingsApp, data_manager=self.db, app_settings=self.settings)