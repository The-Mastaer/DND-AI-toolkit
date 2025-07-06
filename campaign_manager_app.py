import customtkinter
import logging


class CampaignManagerApp(customtkinter.CTkToplevel):
    """
    A dedicated window for creating, editing, and deleting campaign lore,
    now with a tabbed interface for better organization.
    """

    def __init__(self, master, data_manager):
        super().__init__(master)
        self.master = master
        self.db = data_manager

        self.title("Campaign Manager")
        self.geometry("900x600")
        self.minsize(600, 400)

        self.campaigns = self.db.load_campaigns()
        self.selected_campaign_name = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._create_widgets()
        self.update_campaign_list()
        self.select_first_campaign()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        """Handles window closing and triggers a refresh in the main menu."""
        self.master.refresh_campaign_list()
        self.destroy()

    def _create_widgets(self):
        """Initializes and lays out all the main UI components."""
        # --- Sidebar ---
        self.sidebar_frame = customtkinter.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(1, weight=1)

        customtkinter.CTkLabel(self.sidebar_frame, text="Campaigns",
                               font=customtkinter.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20,
                                                                                        pady=(20, 10))

        self.campaign_list_frame = customtkinter.CTkScrollableFrame(self.sidebar_frame)
        self.campaign_list_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.campaign_buttons = {}

        button_frame = customtkinter.CTkFrame(self.sidebar_frame, fg_color="transparent")
        button_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        customtkinter.CTkButton(button_frame, text="+ New", command=self.new_campaign).grid(row=0, column=0,
                                                                                            padx=(0, 5), sticky="ew")
        customtkinter.CTkButton(button_frame, text="- Delete", fg_color="#D32F2F", hover_color="#B71C1C",
                                command=self.delete_campaign).grid(row=0, column=1, padx=(5, 0), sticky="ew")

        # --- Main Editing Area ---
        self.main_frame = customtkinter.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1)  # Let the tabview expand

        customtkinter.CTkLabel(self.main_frame, text="Campaign Name:").grid(row=0, column=0, padx=10, pady=(10, 0),
                                                                            sticky="w")
        self.campaign_name_entry = customtkinter.CTkEntry(self.main_frame, font=customtkinter.CTkFont(size=14))
        self.campaign_name_entry.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        # Tabbed view for different context types
        self.tabview = customtkinter.CTkTabview(self.main_frame)
        self.tabview.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        self.tabview.add("Lore")
        self.tabview.add("Party Info")
        self.tabview.add("Session History")

        self.campaign_lore_textbox = customtkinter.CTkTextbox(self.tabview.tab("Lore"), wrap="word")
        self.campaign_lore_textbox.pack(expand=True, fill="both")

        self.party_info_textbox = customtkinter.CTkTextbox(self.tabview.tab("Party Info"), wrap="word")
        self.party_info_textbox.pack(expand=True, fill="both")

        self.session_history_textbox = customtkinter.CTkTextbox(self.tabview.tab("Session History"), wrap="word")
        self.session_history_textbox.pack(expand=True, fill="both")

        # Frame for bottom buttons
        bottom_button_frame = customtkinter.CTkFrame(self.main_frame, fg_color="transparent")
        bottom_button_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        bottom_button_frame.grid_columnconfigure(0, weight=1)
        bottom_button_frame.grid_columnconfigure(1, weight=1)

        customtkinter.CTkButton(bottom_button_frame, text="Save Campaign", height=40, command=self.save_campaign).grid(
            row=0, column=0, padx=(0, 5), sticky="ew")
        customtkinter.CTkButton(bottom_button_frame, text="Close", height=40, fg_color="gray50", hover_color="gray30",
                                command=self.on_close).grid(row=0, column=1, padx=(5, 0), sticky="ew")

    def update_campaign_list(self):
        """Clears and repopulates the campaign list in the sidebar."""
        for widget in self.campaign_list_frame.winfo_children():
            widget.destroy()
        sorted_campaign_names = sorted(self.campaigns.keys())
        self.campaign_buttons = {}
        for name in sorted_campaign_names:
            button = customtkinter.CTkButton(self.campaign_list_frame, text=name,
                                             command=lambda n=name: self.select_campaign(n))
            button.pack(pady=5, padx=5, fill="x")
            self.campaign_buttons[name] = button
        self.highlight_selected_campaign()

    def highlight_selected_campaign(self):
        """Visually highlights the currently selected campaign."""
        for name, button in self.campaign_buttons.items():
            is_selected = (name == self.selected_campaign_name)
            button.configure(fg_color=customtkinter.ThemeManager.theme["CTkButton"]["hover_color"] if is_selected else
            customtkinter.ThemeManager.theme["CTkButton"]["fg_color"])

    def select_campaign(self, name):
        """Handles the selection of a campaign from the list and populates the fields."""
        if name in self.campaigns:
            self.selected_campaign_name = name
            campaign_data = self.campaigns.get(name, {})
            self.populate_fields(campaign_data)
            self.highlight_selected_campaign()
        else:
            logging.warning(f"Attempted to select non-existent campaign: {name}")

    def select_first_campaign(self):
        """Selects the first campaign in the list, or prepares a new one."""
        if self.campaigns:
            first_name = sorted(self.campaigns.keys())[0]
            self.select_campaign(first_name)
        else:
            self.new_campaign()

    def populate_fields(self, campaign_data):
        """Fills the editing fields with data from a given campaign."""
        self.campaign_name_entry.delete(0, "end")
        self.campaign_name_entry.insert(0, campaign_data.get("campaign_name", ""))

        self.campaign_lore_textbox.delete("1.0", "end")
        self.campaign_lore_textbox.insert("1.0", campaign_data.get("campaign_lore", ""))

        self.party_info_textbox.delete("1.0", "end")
        self.party_info_textbox.insert("1.0", campaign_data.get("party_info", ""))

        self.session_history_textbox.delete("1.0", "end")
        self.session_history_textbox.insert("1.0", campaign_data.get("session_history", ""))

    def new_campaign(self):
        """Clears the fields to start a new campaign entry."""
        self.selected_campaign_name = None
        self.populate_fields({})
        self.highlight_selected_campaign()
        self.campaign_name_entry.focus()

    def save_campaign(self):
        """Gathers data from the fields and saves it to the database."""
        new_name = self.campaign_name_entry.get().strip()
        if not new_name:
            logging.error("Campaign name cannot be empty.")
            return

        campaign_data = {
            "campaign_name": new_name,
            "campaign_lore": self.campaign_lore_textbox.get("1.0", "end-1c"),
            "party_info": self.party_info_textbox.get("1.0", "end-1c"),
            "session_history": self.session_history_textbox.get("1.0", "end-1c")
        }

        self.db.save_campaign(campaign_data, old_name=self.selected_campaign_name)

        if self.selected_campaign_name and self.selected_campaign_name != new_name:
            del self.campaigns[self.selected_campaign_name]
        self.campaigns[new_name] = campaign_data

        self.update_campaign_list()
        self.select_campaign(new_name)

    def delete_campaign(self):
        """Deletes the currently selected campaign."""
        if not self.selected_campaign_name:
            return
        self.db.delete_campaign(self.selected_campaign_name)
        del self.campaigns[self.selected_campaign_name]
        self.update_campaign_list()
        self.select_first_campaign()