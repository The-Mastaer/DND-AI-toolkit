import customtkinter
import logging
from config import SUPPORTED_LANGUAGES, AVAILABLE_TEXT_MODELS, AVAILABLE_IMAGE_MODELS


class SettingsApp(customtkinter.CTkToplevel):
    """
    A Toplevel window for managing all user-configurable settings,
    including active campaign, AI models, prompts, and app appearance.
    """

    def __init__(self, master, data_manager, app_settings):
        super().__init__(master)
        self.master = master
        self.db = data_manager
        self.settings = app_settings

        self.title("Settings & Configuration")
        self.geometry("800x650")
        self.minsize(700, 550)
        self.grab_set()

        # Local StringVars for UI control
        self.active_language = customtkinter.StringVar(value=self.settings.get("active_language"))
        self.active_world_name = customtkinter.StringVar()
        self.active_campaign_name = customtkinter.StringVar()
        self.text_model_var = customtkinter.StringVar(value=self.settings.get("text_model"))
        self.image_model_var = customtkinter.StringVar(value=self.settings.get("image_model"))
        self.theme_var = customtkinter.StringVar(value=self.settings.get("theme"))

        self._create_widgets()
        self.load_worlds()

        self.protocol("WM_DELETE_WINDOW", self.destroy)  # Just close on 'X'

    def save_and_close(self):
        """Saves all settings, tells the main app to refresh, and closes the window."""
        self.save_all_settings()
        self.master.refresh_display()
        self.destroy()

    def _create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        main_frame = customtkinter.CTkFrame(self)
        main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        self.tabview = customtkinter.CTkTabview(main_frame, corner_radius=10)
        self.tabview.pack(expand=True, fill="both")
        self.tabview.add("Active Campaign")
        self.tabview.add("AI Settings")
        self.tabview.add("Appearance")

        self._create_campaign_tab()
        self._create_ai_settings_tab()
        self._create_appearance_tab()

        save_button = customtkinter.CTkButton(main_frame, text="Save & Close", height=40, command=self.save_and_close)
        save_button.pack(pady=(10, 0), padx=10, fill="x")

    def _create_campaign_tab(self):
        # ... (Content unchanged)
        pass

    def _create_ai_settings_tab(self):
        tab = self.tabview.tab("AI Settings")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        model_frame = customtkinter.CTkFrame(tab)
        model_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        model_frame.grid_columnconfigure(1, weight=1)

        customtkinter.CTkLabel(model_frame, text="Text Model:", font=customtkinter.CTkFont(weight="bold")).grid(row=0,
                                                                                                                column=0,
                                                                                                                padx=10,
                                                                                                                pady=10,
                                                                                                                sticky="w")
        self.text_model_menu = customtkinter.CTkOptionMenu(model_frame, variable=self.text_model_var,
                                                           values=AVAILABLE_TEXT_MODELS)
        self.text_model_menu.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        customtkinter.CTkLabel(model_frame, text="Image Model:", font=customtkinter.CTkFont(weight="bold")).grid(row=1,
                                                                                                                 column=0,
                                                                                                                 padx=10,
                                                                                                                 pady=10,
                                                                                                                 sticky="w")
        self.image_model_menu = customtkinter.CTkOptionMenu(model_frame, variable=self.image_model_var,
                                                            values=AVAILABLE_IMAGE_MODELS)
        self.image_model_menu.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        customtkinter.CTkLabel(tab, text="Prompt Overrides", font=customtkinter.CTkFont(size=16, weight="bold")).grid(
            row=1, column=0, padx=20, pady=(10, 0), sticky="w")

        prompt_tab_view = customtkinter.CTkTabview(tab, corner_radius=8)
        prompt_tab_view.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        prompt_tab_view.add("NPC Generation")
        prompt_tab_view.add("Translation")
        prompt_tab_view.add("Simulation (Short)")
        prompt_tab_view.add("Simulation (Long)")

        # NPC Prompt Tab
        self.npc_prompt_textbox = customtkinter.CTkTextbox(prompt_tab_view.tab("NPC Generation"), wrap="word")
        self.npc_prompt_textbox.pack(expand=True, fill="both", padx=5, pady=5)
        self.npc_prompt_textbox.insert("1.0", self.settings.get("prompts", {}).get("npc_generation", ""))

        # Translation Prompt Tab
        self.trans_prompt_textbox = customtkinter.CTkTextbox(prompt_tab_view.tab("Translation"), wrap="word")
        self.trans_prompt_textbox.pack(expand=True, fill="both", padx=5, pady=5)
        self.trans_prompt_textbox.insert("1.0", self.settings.get("prompts", {}).get("translation", ""))

        # Sim Short Prompt Tab
        self.sim_short_prompt_textbox = customtkinter.CTkTextbox(prompt_tab_view.tab("Simulation (Short)"), wrap="word")
        self.sim_short_prompt_textbox.pack(expand=True, fill="both", padx=5, pady=5)
        self.sim_short_prompt_textbox.insert("1.0", self.settings.get("prompts", {}).get("npc_simulation_short", ""))

        # Sim Long Prompt Tab
        self.sim_long_prompt_textbox = customtkinter.CTkTextbox(prompt_tab_view.tab("Simulation (Long)"), wrap="word")
        self.sim_long_prompt_textbox.pack(expand=True, fill="both", padx=5, pady=5)
        self.sim_long_prompt_textbox.insert("1.0", self.settings.get("prompts", {}).get("npc_simulation_long", ""))

    def _create_appearance_tab(self):
        # ... (Content unchanged)
        pass

    def on_theme_selected(self, theme):
        # ... (Content unchanged)
        pass

    def load_worlds(self):
        # ... (Content unchanged)
        pass

    def on_language_selected(self, selected_language):
        # ... (Content unchanged)
        pass

    def on_world_selected(self, selected_world_name):
        # ... (Content unchanged)
        pass

    def on_campaign_selected(self, selected_campaign_name):
        # ... (Content unchanged)
        pass

    def save_all_settings(self):
        """Collects all settings from the UI and saves them."""
        self.settings.set("active_language", self.active_language.get())
        self.settings.set("text_model", self.text_model_var.get())
        self.settings.set("image_model", self.image_model_var.get())
        self.settings.set("theme", self.theme_var.get())

        prompts = self.settings.get("prompts", {})
        prompts["npc_generation"] = self.npc_prompt_textbox.get("1.0", "end-1c")
        prompts["translation"] = self.trans_prompt_textbox.get("1.0", "end-1c")
        prompts["npc_simulation_short"] = self.sim_short_prompt_textbox.get("1.0", "end-1c")
        prompts["npc_simulation_long"] = self.sim_long_prompt_textbox.get("1.0", "end-1c")
        self.settings.set("prompts", prompts)

        self.settings.save()
        logging.info("All settings have been saved.")