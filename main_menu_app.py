import customtkinter
import logging
from config import SUPPORTED_LANGUAGES
from world_manager_app import WorldManagerApp
from settings_app import SettingsApp
from app_settings import AppSettings


class MainMenuApp(customtkinter.CTk):
    """
    The main application window, which serves as a clean dashboard displaying
    the active campaign. All configuration is handled in the SettingsApp.
    """

    def __init__(self, data_manager, api_service, app_settings):
        super().__init__()
        self.db = data_manager
        self.ai = api_service
        self.settings = app_settings
        self.toplevel_window = None

        # Apply the theme from settings at startup
        customtkinter.set_appearance_mode(self.settings.get("theme"))

        self.title("DM's AI Toolkit")
        self.geometry("1200x800")
        self.minsize(900, 600)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._create_widgets()
        self.refresh_display()

    def _create_widgets(self):
        # --- Sidebar for Navigation ---
        self.sidebar_frame = customtkinter.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsw")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)  # Push settings to bottom

        customtkinter.CTkLabel(self.sidebar_frame, text="Tools",
                               font=customtkinter.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20,
                                                                                        pady=(20, 10))

        self.launch_char_button = customtkinter.CTkButton(self.sidebar_frame, text="Character Manager",
                                                          state="disabled")  # command=self.launch_character_manager
        self.launch_char_button.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        # Placeholder for future tools
        customtkinter.CTkLabel(self.sidebar_frame, text="Coming Soon...",
                               font=customtkinter.CTkFont(size=12, slant="italic")).grid(row=2, column=0, padx=20,
                                                                                         pady=20)

        # Settings and World Management button at the bottom
        self.manage_worlds_button = customtkinter.CTkButton(self.sidebar_frame, text="Manage Worlds",
                                                            command=self.launch_world_manager)
        self.manage_worlds_button.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        self.settings_button = customtkinter.CTkButton(self.sidebar_frame, text="Settings",
                                                       command=self.launch_settings)
        self.settings_button.grid(row=6, column=0, padx=20, pady=20, sticky="s")

        # --- Main Content Area (The Dashboard) ---
        self.dashboard_frame = customtkinter.CTkFrame(self)
        self.dashboard_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        self.campaign_title_label = customtkinter.CTkLabel(self.dashboard_frame, text="No Campaign Selected",
                                                           font=customtkinter.CTkFont(size=28, weight="bold"))
        self.campaign_title_label.pack(pady=20, padx=40)

        self.campaign_info_label = customtkinter.CTkLabel(self.dashboard_frame,
                                                          text="Go to Settings to select your active campaign.",
                                                          font=customtkinter.CTkFont(size=16))
        self.campaign_info_label.pack(pady=10, padx=40)

    def refresh_display(self):
        """Updates the dashboard display based on the currently saved settings."""
        logging.info("Refreshing main display...")
        self.settings._load_settings()  # Re-load settings from file

        world_id = self.settings.get("active_world_id")
        campaign_id = self.settings.get("active_campaign_id")
        lang = self.settings.get("active_language")

        world_name = "N/A"
        campaign_name = "No Campaign Selected"
        info_text = "Go to Settings to select your active world and campaign."

        if world_id:
            world_trans = self.db.get_world_translation(world_id, lang)
            if world_trans:
                world_name = world_trans['world_name']

        if campaign_id:
            all_campaigns = self.db.get_campaigns_for_world(world_id)
            campaign_data = next((c for c in all_campaigns if c['campaign_id'] == campaign_id), None)
            if campaign_data:
                campaign_name = campaign_data['campaign_name']
                info_text = f"World: {world_name}  |  Language: {SUPPORTED_LANGUAGES[lang]}"
                self.launch_char_button.configure(state="normal")
            else:
                self.settings.set("active_campaign_id", None)
                self.settings.save()
                self.launch_char_button.configure(state="disabled")
        else:
            self.launch_char_button.configure(state="disabled")

        self.campaign_title_label.configure(text=campaign_name)
        self.campaign_info_label.configure(text=info_text)

    def open_toplevel(self, window_class, **kwargs):
        """Creates and manages a new top-level window, ensuring proper focus."""
        if self.toplevel_window is not None and self.toplevel_window.winfo_exists():
            self.toplevel_window.destroy()

        # Hide the main window while the toplevel is open
        self.withdraw()

        self.toplevel_window = window_class(master=self, **kwargs)
        # Make the new window modal and give it focus
        self.toplevel_window.grab_set()

    def launch_world_manager(self):
        self.open_toplevel(WorldManagerApp, data_manager=self.db, api_service=self.ai)

    def launch_settings(self):
        self.open_toplevel(SettingsApp, data_manager=self.db, app_settings=self.settings)