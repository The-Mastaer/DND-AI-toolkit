import customtkinter
import logging
from config import SUPPORTED_LANGUAGES
from ui_components import ConfirmationDialog


class CampaignManagerApp(customtkinter.CTkToplevel):
    """
    A Toplevel window for managing campaigns within a specific World.
    This version correctly inherits its language context from the World Manager.
    """

    def __init__(self, master, data_manager, api_service, world_data):
        super().__init__(master)
        self.master = master
        self.db = data_manager
        self.ai = api_service
        self.world_data = world_data  # This contains world_id, world_name, and the current language context

        self.title(f"Campaigns for '{self.world_data['world_name']}'")
        self.geometry("900x600")
        self.minsize(600, 400)
        self.grab_set()

        self.campaigns_in_view = []
        self.selected_campaign = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._create_widgets()
        self.load_and_display_campaigns()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        """When this window closes, it tells the master (World Manager) to refresh itself."""
        self.master.load_and_display_worlds()
        self.destroy()

    def _create_widgets(self):
        """Initializes and lays out all the main UI components."""
        # --- Sidebar ---
        self.sidebar_frame = customtkinter.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(2, weight=1)

        # Display the current language context clearly
        lang_code = self.world_data.get("language", "N/A")
        lang_name = SUPPORTED_LANGUAGES.get(lang_code, "Unknown")
        customtkinter.CTkLabel(self.sidebar_frame, text="Campaigns",
                               font=customtkinter.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20,
                                                                                        pady=(20, 0))
        customtkinter.CTkLabel(self.sidebar_frame, text=f"Language: {lang_name}",
                               font=customtkinter.CTkFont(size=12, slant="italic")).grid(row=1, column=0, padx=20,
                                                                                         pady=(0, 10))

        self.campaign_list_frame = customtkinter.CTkScrollableFrame(self.sidebar_frame)
        self.campaign_list_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        self.campaign_buttons = {}

        button_frame = customtkinter.CTkFrame(self.sidebar_frame, fg_color="transparent")
        button_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        customtkinter.CTkButton(button_frame, text="+ New", command=self.new_campaign).grid(row=0, column=0,
                                                                                            padx=(0, 5), sticky="ew")
        customtkinter.CTkButton(button_frame, text="- Delete", fg_color="#D32F2F", hover_color="#B71C1C",
                                command=self.delete_selected_campaign).grid(row=0, column=1, padx=(5, 0), sticky="ew")

        # --- Main Editing Area ---
        self.main_frame = customtkinter.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1)

        # Campaign Name
        customtkinter.CTkLabel(self.main_frame, text="Campaign Name:").grid(row=0, column=0, padx=10, pady=(10, 0),
                                                                            sticky="w")
        self.campaign_name_entry = customtkinter.CTkEntry(self.main_frame, font=customtkinter.CTkFont(size=14))
        self.campaign_name_entry.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        # Tabbed view for different context types
        self.tabview = customtkinter.CTkTabview(self.main_frame)
        self.tabview.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        self.tabview.add("Party Info")
        self.tabview.add("Session History")

        self.party_info_textbox = customtkinter.CTkTextbox(self.tabview.tab("Party Info"), wrap="word")
        self.party_info_textbox.pack(expand=True, fill="both", padx=5, pady=5)

        self.session_history_textbox = customtkinter.CTkTextbox(self.tabview.tab("Session History"), wrap="word")
        self.session_history_textbox.pack(expand=True, fill="both", padx=5, pady=5)

        # Frame for bottom buttons
        bottom_button_frame = customtkinter.CTkFrame(self.main_frame, fg_color="transparent")
        bottom_button_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        bottom_button_frame.grid_columnconfigure(0, weight=1)

        customtkinter.CTkButton(bottom_button_frame, text="Save Campaign", height=40, command=self.save_campaign).grid(
            row=0, column=0, sticky="ew")

    def load_and_display_campaigns(self):
        """Loads campaigns for the current world and filters them by the inherited language."""
        all_campaigns = self.db.get_campaigns_for_world(self.world_data['world_id'])
        current_lang = self.world_data['language']

        self.campaigns_in_view = [c for c in all_campaigns if c['language'] == current_lang]

        for widget in self.campaign_list_frame.winfo_children():
            widget.destroy()
        self.campaign_buttons = {}

        for campaign in self.campaigns_in_view:
            button = customtkinter.CTkButton(self.campaign_list_frame, text=campaign['campaign_name'],
                                             command=lambda c=campaign: self.select_campaign(c))
            button.pack(pady=5, padx=5, fill="x")
            self.campaign_buttons[campaign['campaign_id']] = button

        if self.campaigns_in_view:
            self.select_campaign(self.campaigns_in_view[0])
        else:
            self.new_campaign()

    def select_campaign(self, campaign_data):
        """Populates the fields with data from the selected campaign."""
        self.selected_campaign = campaign_data

        self.campaign_name_entry.delete(0, "end")
        self.campaign_name_entry.insert(0, campaign_data.get("campaign_name", ""))

        self.party_info_textbox.delete("1.0", "end")
        self.party_info_textbox.insert("1.0", campaign_data.get("party_info", ""))

        self.session_history_textbox.delete("1.0", "end")
        self.session_history_textbox.insert("1.0", campaign_data.get("session_history", ""))

        self.highlight_selected_campaign()

    def highlight_selected_campaign(self):
        """Visually highlights the currently selected campaign button."""
        if not self.selected_campaign:
            return
        for camp_id, button in self.campaign_buttons.items():
            if camp_id == self.selected_campaign['campaign_id']:
                button.configure(fg_color=customtkinter.ThemeManager.theme["CTkButton"]["hover_color"])
            else:
                button.configure(fg_color=customtkinter.ThemeManager.theme["CTkButton"]["fg_color"])

    def new_campaign(self):
        """Clears the fields to start a new campaign entry in the current language context."""
        self.selected_campaign = None
        self.campaign_name_entry.delete(0, "end")
        self.party_info_textbox.delete("1.0", "end")
        self.session_history_textbox.delete("1.0", "end")
        self.campaign_name_entry.focus()

        for button in self.campaign_buttons.values():
            button.configure(fg_color=customtkinter.ThemeManager.theme["CTkButton"]["fg_color"])

    def save_campaign(self):
        """Gathers data from the fields and saves it to the database."""
        name = self.campaign_name_entry.get().strip()
        if not name:
            logging.error("Campaign name cannot be empty.")
            return

        party_info = self.party_info_textbox.get("1.0", "end-1c")
        session_history = self.session_history_textbox.get("1.0", "end-1c")

        lang = self.world_data['language']

        try:
            if self.selected_campaign:
                camp_id = self.selected_campaign['campaign_id']
                self.db.update_campaign(camp_id, name, lang, party_info, session_history)
            else:
                self.db.create_campaign(self.world_data['world_id'], name, lang, party_info, session_history)

            self.load_and_display_campaigns()
        except Exception as e:
            logging.error(f"Failed to save campaign: {e}")

    def _confirm_and_delete_campaign(self):
        """The actual deletion logic, called by the confirmation dialog."""
        if not self.selected_campaign:
            return
        try:
            self.db.delete_campaign(self.selected_campaign['campaign_id'])
            self.load_and_display_campaigns()
        except Exception as e:
            logging.error(f"Failed to delete campaign: {e}")

    def delete_selected_campaign(self):
        """Opens a confirmation dialog before deleting the campaign."""
        if not self.selected_campaign:
            return

        camp_name = self.selected_campaign.get('campaign_name', 'this campaign')
        msg = f"Are you sure you want to delete the campaign '{camp_name}'?"
        ConfirmationDialog(self, title="Confirm Deletion", message=msg, command=self._confirm_and_delete_campaign)