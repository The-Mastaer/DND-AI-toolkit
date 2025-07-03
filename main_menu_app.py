import customtkinter
from npc_manager_app import NpcApp
from npc_simulator_app import NpcSimulatorApp


class MainMenuApp(customtkinter.CTk):
    """
    The initial main menu window for the DM's Toolkit.
    From here, users can launch different tools.
    """

    def __init__(self, data_manager, api_service):
        super().__init__()
        self.db = data_manager
        self.ai = api_service

        self.title("DM's AI Toolkit")
        self.geometry("500x400")
        self.resizable(False, False)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._create_widgets()

    def _create_widgets(self):
        """Creates and places the widgets for the main menu."""
        main_frame = customtkinter.CTkFrame(self)
        main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)

        title_label = customtkinter.CTkLabel(main_frame, text="DM's AI Toolkit",
                                             font=customtkinter.CTkFont(size=24, weight="bold"))
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        subtitle_label = customtkinter.CTkLabel(main_frame, text="Your all-in-one assistant for epic campaigns.",
                                                font=customtkinter.CTkFont(size=14))
        subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 20))

        manager_button = customtkinter.CTkButton(main_frame, text="Launch NPC Manager", height=50,
                                                 command=self.launch_npc_manager)
        manager_button.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        simulator_button = customtkinter.CTkButton(main_frame, text="Launch NPC Simulator", height=50,
                                                   command=self.launch_npc_simulator)
        simulator_button.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        api_status_text = "API Key Loaded" if self.ai.is_api_key_valid() else "API Key Missing!"
        api_status_color = "green" if self.ai.is_api_key_valid() else "red"

        api_status_label = customtkinter.CTkLabel(main_frame, text=api_status_text,
                                                  font=customtkinter.CTkFont(size=12), text_color=api_status_color)
        api_status_label.grid(row=4, column=0, padx=20, pady=(10, 20))

    def launch_npc_manager(self):
        """Closes the main menu and launches the NPC Manager application."""
        self.destroy()
        npc_app = NpcApp(self.db, self.ai)
        npc_app.mainloop()

    def launch_npc_simulator(self):
        """Closes the main menu and launches the NPC Simulator application."""
        self.destroy()
        sim_app = NpcSimulatorApp(api_service=self.ai, data_manager=self.db)
        sim_app.mainloop()
