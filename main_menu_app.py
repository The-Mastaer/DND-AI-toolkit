import customtkinter
from npc_manager_app import NpcApp
from npc_simulator_app import NpcSimulatorApp
from campaign_manager_app import CampaignManagerApp


class MainMenuApp(customtkinter.CTk):
    """
    The main application window, which now manages all other windows and active campaign.
    """

    def __init__(self, data_manager, api_service):
        super().__init__()
        self.db = data_manager
        self.ai = api_service
        self.toplevel_window = None

        self.campaigns = {}
        self.active_campaign_name = customtkinter.StringVar()

        self.title("DM's AI Toolkit")
        self.geometry("500x480")
        self.resizable(False, False)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._create_widgets()
        self.refresh_campaign_list()

    def _create_widgets(self):
        main_frame = customtkinter.CTkFrame(self)
        main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)

        title_label = customtkinter.CTkLabel(main_frame, text="DM's AI Toolkit",
                                             font=customtkinter.CTkFont(size=24, weight="bold"))
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        subtitle_label = customtkinter.CTkLabel(main_frame, text="Your all-in-one assistant for epic campaigns.",
                                                font=customtkinter.CTkFont(size=14))
        subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 20))

        customtkinter.CTkLabel(main_frame, text="Active Campaign:", font=customtkinter.CTkFont(weight="bold")).grid(
            row=2, column=0, padx=20, pady=(10, 0), sticky="w")
        self.campaign_dropdown = customtkinter.CTkOptionMenu(main_frame, variable=self.active_campaign_name,
                                                             values=["No Campaigns Found"])
        self.campaign_dropdown.grid(row=3, column=0, padx=20, pady=5, sticky="ew")

        campaign_button = customtkinter.CTkButton(main_frame, text="Manage Campaigns",
                                                  command=self.launch_campaign_manager)
        campaign_button.grid(row=4, column=0, padx=20, pady=(5, 20), sticky="ew")

        manager_button = customtkinter.CTkButton(main_frame, text="Launch NPC Manager", height=50,
                                                 command=self.launch_npc_manager)
        manager_button.grid(row=5, column=0, padx=20, pady=10, sticky="ew")
        simulator_button = customtkinter.CTkButton(main_frame, text="Launch NPC Simulator", height=50,
                                                   command=self.launch_npc_simulator)
        simulator_button.grid(row=6, column=0, padx=20, pady=10, sticky="ew")

        api_status_text = "API Key Loaded" if self.ai.is_api_key_valid() else "API Key Missing!"
        api_status_color = "green" if self.ai.is_api_key_valid() else "red"
        api_status_label = customtkinter.CTkLabel(main_frame, text=api_status_text, font=customtkinter.CTkFont(size=12),
                                                  text_color=api_status_color)
        api_status_label.grid(row=7, column=0, padx=20, pady=(10, 20))

    def refresh_campaign_list(self):
        """Reloads campaigns from the DB and updates the dropdown menu."""
        self.campaigns = self.db.load_campaigns()
        campaign_names = sorted(self.campaigns.keys())
        if not campaign_names:
            self.campaign_dropdown.configure(values=["No Campaigns Found"])
            self.active_campaign_name.set("No Campaigns Found")
        else:
            current_selection = self.active_campaign_name.get()
            self.campaign_dropdown.configure(values=campaign_names)
            if current_selection in campaign_names:
                self.active_campaign_name.set(current_selection)
            else:
                self.active_campaign_name.set(campaign_names[0])

    def open_toplevel(self, window_class, **kwargs):
        if self.toplevel_window is not None and self.toplevel_window.winfo_exists():
            self.toplevel_window.destroy()
        if window_class not in [CampaignManagerApp]:
            self.withdraw()
        self.toplevel_window = window_class(master=self, **kwargs)
        self.toplevel_window.grab_set()

    def launch_campaign_manager(self):
        self.open_toplevel(CampaignManagerApp, data_manager=self.db)

    def launch_npc_manager(self):
        """Opens the NPC Manager, passing the full active campaign data dictionary."""
        active_campaign_name = self.active_campaign_name.get()
        campaign_data = self.campaigns.get(active_campaign_name, {})
        self.open_toplevel(NpcApp, data_manager=self.db, api_service=self.ai, campaign_data=campaign_data)

    def launch_npc_simulator(self, npc_data=None, campaign_data=None):
        """
        Opens the NPC Simulator. If campaign_data is not provided (i.e., called
        from the main menu button), it gets the active one.
        """
        if campaign_data is None:
            active_campaign_name = self.active_campaign_name.get()
            campaign_data = self.campaigns.get(active_campaign_name, {})

        self.open_toplevel(NpcSimulatorApp, data_manager=self.db, api_service=self.ai, npc_data=npc_data,
                           campaign_data=campaign_data)