import customtkinter
import logging
import threading
from config import SUPPORTED_LANGUAGES
from campaign_manager_app import CampaignManagerApp
from ui_components import ConfirmationDialog


class TranslateDialog(customtkinter.CTkToplevel):
    """A dialog for handling the AI translation of a world."""

    def __init__(self, master, world_data, data_manager, api_service):
        super().__init__(master)
        self.master = master
        self.world_data = world_data
        self.db = data_manager
        self.ai = api_service

        self.title("Translate World")
        self.geometry("400x250")
        self.grab_set()  # Modal behavior

        self.source_lang_code = world_data['language']
        self.target_lang_code = customtkinter.StringVar()

        # Filter out the source language from the target options
        target_options = [code for code in SUPPORTED_LANGUAGES.keys() if code != self.source_lang_code]
        if target_options:
            self.target_lang_code.set(target_options[0])

        customtkinter.CTkLabel(self, text=f"Translate '{world_data['world_name']}'",
                               font=customtkinter.CTkFont(size=16, weight="bold")).pack(pady=(20, 10))

        customtkinter.CTkLabel(self, text=f"From: {SUPPORTED_LANGUAGES[self.source_lang_code]}").pack(pady=5)

        target_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        target_frame.pack(pady=10)
        customtkinter.CTkLabel(target_frame, text="To:").pack(side="left")
        self.target_menu = customtkinter.CTkOptionMenu(target_frame, variable=self.target_lang_code,
                                                       values=target_options)
        self.target_menu.pack(side="left", padx=10)

        self.translate_button = customtkinter.CTkButton(self, text="Translate with AI", command=self.start_translation)
        self.translate_button.pack(pady=10)

        self.status_label = customtkinter.CTkLabel(self, text="")
        self.status_label.pack(pady=5)

    def start_translation(self):
        """Starts the AI translation in a separate thread."""
        if not self.ai.is_api_key_valid():
            self.status_label.configure(text="Error: API Key is missing.", text_color="red")
            return

        target_code = self.target_lang_code.get()
        if not target_code:
            self.status_label.configure(text="No target language selected.", text_color="red")
            return

        threading.Thread(target=self.run_translation_task, args=(target_code,), daemon=True).start()

    def run_translation_task(self, target_code):
        """The worker function that calls the AI and saves the result."""
        self.after(0, lambda: self.translate_button.configure(state="disabled"))
        self.after(0, lambda: self.status_label.configure(text=f"Translating...", text_color="gray"))

        try:
            target_name = SUPPORTED_LANGUAGES[target_code]
            # Translate name and lore
            translated_name = self.ai.translate_text(self.world_data['world_name'], target_code, target_name)
            translated_lore = self.ai.translate_text(self.world_data['world_lore'], target_code, target_name)

            # Save the new translation
            self.db.update_world_translation(self.world_data['world_id'], target_code, translated_name, translated_lore)

            self.after(0, lambda: self.status_label.configure(text="Translation successful!", text_color="green"))
            # Refresh the main window's view and close this dialog
            self.after(1000, self.close_and_refresh)

        except Exception as e:
            logging.error(f"Translation failed in dialog: {e}")
            self.after(0, lambda: self.status_label.configure(text="Error: Translation failed.", text_color="red"))
            self.after(0, lambda: self.translate_button.configure(state="normal"))

    def close_and_refresh(self):
        self.master.load_and_display_worlds()
        self.destroy()


class WorldManagerApp(customtkinter.CTkToplevel):
    """
    A top-level window for creating, editing, and selecting Worlds with multi-language support.
    """

    def __init__(self, master, data_manager, api_service):
        super().__init__(master)
        self.master = master
        self.db = data_manager
        self.ai = api_service

        self.title("World Manager")
        self.geometry("1000x650")
        self.minsize(800, 500)

        self.worlds_in_current_lang = []
        self.selected_world_data = None  # Store the full dict for the selected world

        self.active_language = customtkinter.StringVar(value=list(SUPPORTED_LANGUAGES.keys())[0])

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._create_widgets()
        self.load_and_display_worlds()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        """Handles window closing, shows the main menu, and tells it to refresh."""
        self.master.deiconify()
        self.master.refresh_display()
        self.destroy()

    def _create_widgets(self):
        """Initializes and lays out all the main UI components."""
        # --- Sidebar for World List ---
        self.sidebar_frame = customtkinter.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(2, weight=1)

        customtkinter.CTkLabel(self.sidebar_frame, text="Your Worlds",
                               font=customtkinter.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20,
                                                                                        pady=(20, 10))

        language_frame = customtkinter.CTkFrame(self.sidebar_frame, fg_color="transparent")
        language_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        customtkinter.CTkLabel(language_frame, text="Language:").pack(side="left")
        self.language_menu = customtkinter.CTkOptionMenu(language_frame, variable=self.active_language,
                                                         values=list(SUPPORTED_LANGUAGES.keys()),
                                                         command=self.on_language_change)
        self.language_menu.pack(side="left", expand=True, fill="x", padx=(5, 0))

        self.world_list_frame = customtkinter.CTkScrollableFrame(self.sidebar_frame)
        self.world_list_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        self.world_buttons = {}

        button_frame = customtkinter.CTkFrame(self.sidebar_frame, fg_color="transparent")
        button_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        customtkinter.CTkButton(button_frame, text="+ New", command=self.new_world).grid(row=0, column=0, padx=(0, 5),
                                                                                         sticky="ew")
        customtkinter.CTkButton(button_frame, text="- Delete", fg_color="#D32F2F", hover_color="#B71C1C",
                                command=self.delete_selected_world).grid(row=0, column=1, padx=(5, 0), sticky="ew")

        # --- Main Editing Area ---
        self.main_frame = customtkinter.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(3, weight=1)

        customtkinter.CTkLabel(self.main_frame, text="World Name:").grid(row=0, column=0, padx=10, pady=(10, 0),
                                                                         sticky="w")
        self.world_name_entry = customtkinter.CTkEntry(self.main_frame, font=customtkinter.CTkFont(size=14))
        self.world_name_entry.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        customtkinter.CTkLabel(self.main_frame, text="World Lore:").grid(row=2, column=0, padx=10, pady=(0, 5),
                                                                         sticky="nw")
        self.world_lore_textbox = customtkinter.CTkTextbox(self.main_frame, wrap="word")
        self.world_lore_textbox.grid(row=3, column=0, padx=10, pady=(5, 10), sticky="nsew")

        self.status_label = customtkinter.CTkLabel(self.main_frame, text="", text_color="gray")
        self.status_label.grid(row=4, column=0, padx=10, pady=5, sticky="w")

        bottom_button_frame = customtkinter.CTkFrame(self.main_frame, fg_color="transparent")
        bottom_button_frame.grid(row=5, column=0, padx=10, pady=10, sticky="ew")
        bottom_button_frame.grid_columnconfigure(0, weight=1)
        bottom_button_frame.grid_columnconfigure(1, weight=1)
        bottom_button_frame.grid_columnconfigure(2, weight=1)

        self.save_button = customtkinter.CTkButton(bottom_button_frame, text="Save World", height=40,
                                                   command=self.save_world)
        self.save_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        self.translate_button = customtkinter.CTkButton(bottom_button_frame, text="Translate...", height=40,
                                                        command=self.open_translate_dialog, state="disabled")
        self.translate_button.grid(row=0, column=1, padx=5, sticky="ew")
        self.campaign_button = customtkinter.CTkButton(bottom_button_frame, text="Manage Campaigns", height=40,
                                                       command=self.open_campaign_manager)
        self.campaign_button.grid(row=0, column=2, padx=(5, 0), sticky="ew")

    def on_language_change(self, new_language_code):
        self.load_and_display_worlds()

    def load_and_display_worlds(self):
        active_lang = self.active_language.get()
        self.worlds_in_current_lang = self.db.get_all_worlds(active_lang)

        for widget in self.world_list_frame.winfo_children():
            widget.destroy()
        self.world_buttons = {}

        for world_data in self.worlds_in_current_lang:
            button = customtkinter.CTkButton(self.world_list_frame, text=world_data['world_name'],
                                             command=lambda w=world_data: self.select_world(w))
            button.pack(pady=5, padx=5, fill="x")
            self.world_buttons[world_data['world_id']] = button

        if self.worlds_in_current_lang:
            self.select_world(self.worlds_in_current_lang[0])
        else:
            self.new_world()

    def select_world(self, world_data):
        self.selected_world_data = world_data
        self.world_name_entry.delete(0, "end")
        self.world_name_entry.insert(0, world_data.get("world_name", ""))
        self.world_lore_textbox.delete("1.0", "end")
        self.world_lore_textbox.insert("1.0", world_data.get("world_lore", ""))
        self.status_label.configure(
            text=f"Editing '{world_data.get('world_name')}' in {SUPPORTED_LANGUAGES[self.active_language.get()]}",
            text_color="gray")
        self.translate_button.configure(state="normal")
        self.highlight_selected_world()

    def highlight_selected_world(self):
        if not self.selected_world_data:
            return
        for world_id, button in self.world_buttons.items():
            if world_id == self.selected_world_data['world_id']:
                button.configure(fg_color=customtkinter.ThemeManager.theme["CTkButton"]["hover_color"])
            else:
                button.configure(fg_color=customtkinter.ThemeManager.theme["CTkButton"]["fg_color"])

    def new_world(self):
        self.selected_world_data = None
        self.world_name_entry.delete(0, "end")
        self.world_lore_textbox.delete("1.0", "end")
        self.world_name_entry.focus()
        self.status_label.configure(text=f"Creating new world in {SUPPORTED_LANGUAGES[self.active_language.get()]}",
                                    text_color="gray")
        self.translate_button.configure(state="disabled")
        # Deselect all buttons
        for button in self.world_buttons.values():
            button.configure(fg_color=customtkinter.ThemeManager.theme["CTkButton"]["fg_color"])

    def save_world(self):
        name = self.world_name_entry.get().strip()
        lore = self.world_lore_textbox.get("1.0", "end-1c").strip()
        lang = self.active_language.get()

        if not name:
            self.status_label.configure(text="Error: World Name cannot be empty.", text_color="red")
            return

        try:
            if self.selected_world_data:
                world_id = self.selected_world_data['world_id']
                self.db.update_world_translation(world_id, lang, name, lore)
            else:
                world_id = self.db.create_world(name, lang, lore)

            self.load_and_display_worlds()
            # After reloading, find and re-select the saved world
            for world in self.worlds_in_current_lang:
                if world['world_id'] == world_id:
                    self.select_world(world)
                    break
            self.status_label.configure(text="World saved successfully!", text_color="green")
        except Exception as e:
            logging.error(f"Error saving world: {e}")
            self.status_label.configure(text="Error: Could not save world.", text_color="red")

    def open_translate_dialog(self):
        if not self.selected_world_data:
            return
        TranslateDialog(self, self.selected_world_data, self.db, self.ai)

    def _confirm_and_delete_world(self):
        """The actual deletion logic, to be called by the confirmation dialog."""
        if not self.selected_world_data:
            return
        try:
            self.db.delete_world(self.selected_world_data['world_id'])
            self.selected_world_data = None
            self.load_and_display_worlds()
            self.status_label.configure(text="World deleted successfully.", text_color="green")
        except Exception as e:
            logging.error(f"Error deleting world: {e}")
            self.status_label.configure(text="Error: Could not delete world.", text_color="red")

    def delete_selected_world(self):
        """Opens a confirmation dialog before deleting the world."""
        if not self.selected_world_data:
            return

        world_name = self.selected_world_data.get('world_name', 'this world')
        msg = f"Are you sure you want to delete '{world_name}'?\n\nThis will also delete ALL associated campaigns, characters, etc. This action cannot be undone."
        ConfirmationDialog(self, title="Confirm Deletion", message=msg, command=self._confirm_and_delete_world)

    def open_campaign_manager(self):
        if not self.selected_world_data:
            self.status_label.configure(text="Please select a world first.", text_color="orange")
            return
        logging.info(f"Opening campaign manager for world ID: {self.selected_world_data['world_id']}")
        CampaignManagerApp(master=self, data_manager=self.db, api_service=self.ai, world_data=self.selected_world_data)