import customtkinter
from tkinter import filedialog
import logging
from config import SUPPORTED_LANGUAGES, AVAILABLE_TEXT_MODELS, AVAILABLE_IMAGE_MODELS


class SettingsApp(customtkinter.CTkToplevel):
    """
    A Toplevel window for managing all user-configurable settings.
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

        self.protocol("WM_DELETE_WINDOW", self.destroy)

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
        tab = self.tabview.tab("Active Campaign")
        tab.grid_columnconfigure(1, weight=1)

        customtkinter.CTkLabel(tab, text="Active Language:", font=customtkinter.CTkFont(weight="bold")).grid(row=0,
                                                                                                             column=0,
                                                                                                             padx=20,
                                                                                                             pady=(20,
                                                                                                                   5),
                                                                                                             sticky="w")
        self.language_dropdown = customtkinter.CTkOptionMenu(tab, variable=self.active_language,
                                                             values=list(SUPPORTED_LANGUAGES.keys()),
                                                             command=self.on_language_selected)
        self.language_dropdown.grid(row=0, column=1, padx=20, pady=(20, 5), sticky="ew")

        customtkinter.CTkLabel(tab, text="Active World:", font=customtkinter.CTkFont(weight="bold")).grid(row=1,
                                                                                                          column=0,
                                                                                                          padx=20,
                                                                                                          pady=5,
                                                                                                          sticky="w")
        self.world_dropdown = customtkinter.CTkOptionMenu(tab, variable=self.active_world_name,
                                                          command=self.on_world_selected)
        self.world_dropdown.grid(row=1, column=1, padx=20, pady=5, sticky="ew")

        customtkinter.CTkLabel(tab, text="Active Campaign:", font=customtkinter.CTkFont(weight="bold")).grid(row=2,
                                                                                                             column=0,
                                                                                                             padx=20,
                                                                                                             pady=5,
                                                                                                             sticky="w")
        self.campaign_dropdown = customtkinter.CTkOptionMenu(tab, variable=self.active_campaign_name,
                                                             command=self.on_campaign_selected)
        self.campaign_dropdown.grid(row=2, column=1, padx=20, pady=5, sticky="ew")

    def _create_ai_settings_tab(self):
        tab = self.tabview.tab("AI Settings")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(3, weight=1)

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

        srd_frame = customtkinter.CTkFrame(tab)
        srd_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        srd_frame.grid_columnconfigure(1, weight=1)
        customtkinter.CTkLabel(srd_frame, text="SRD PDF Path:", font=customtkinter.CTkFont(weight="bold")).grid(row=0,
                                                                                                                column=0,
                                                                                                                padx=10,
                                                                                                                pady=10,
                                                                                                                sticky="w")
        self.srd_path_entry = customtkinter.CTkEntry(srd_frame)
        self.srd_path_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.srd_path_entry.insert(0, self.settings.get("srd_pdf_path", ""))
        customtkinter.CTkButton(srd_frame, text="Browse...", command=self.browse_srd_file).grid(row=0, column=2,
                                                                                                padx=10, pady=10)

        customtkinter.CTkLabel(tab, text="Prompt Overrides", font=customtkinter.CTkFont(size=16, weight="bold")).grid(
            row=2, column=0, padx=20, pady=(10, 0), sticky="w")

        prompt_tab_view = customtkinter.CTkTabview(tab, corner_radius=8)
        prompt_tab_view.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")

        prompts = self.settings.get("prompts", {})
        self.lore_master_prompt_textbox = self._create_prompt_tab(prompt_tab_view, "Lore Master",
                                                                  prompts.get("lore_master", ""))
        self.rules_lawyer_prompt_textbox = self._create_prompt_tab(prompt_tab_view, "Rules Lawyer",
                                                                   prompts.get("rules_lawyer", ""))
        self.npc_prompt_textbox = self._create_prompt_tab(prompt_tab_view, "NPC Generation",
                                                          prompts.get("npc_generation", ""))
        self.trans_prompt_textbox = self._create_prompt_tab(prompt_tab_view, "Translation",
                                                            prompts.get("translation", ""))
        self.sim_short_prompt_textbox = self._create_prompt_tab(prompt_tab_view, "Simulation (Short)",
                                                                prompts.get("npc_simulation_short", ""))
        self.sim_long_prompt_textbox = self._create_prompt_tab(prompt_tab_view, "Simulation (Long)",
                                                               prompts.get("npc_simulation_long", ""))

    def _create_prompt_tab(self, tab_view, name, content):
        """Helper to create a tab and a textbox for a prompt."""
        tab = tab_view.add(name)
        textbox = customtkinter.CTkTextbox(tab, wrap="word")
        textbox.pack(expand=True, fill="both", padx=5, pady=5)
        textbox.insert("1.0", content)
        return textbox

    def browse_srd_file(self):
        filepath = filedialog.askopenfilename(title="Select SRD PDF File", filetypes=[("PDF Files", "*.pdf")])
        if filepath:
            self.srd_path_entry.delete(0, "end")
            self.srd_path_entry.insert(0, filepath)

    def _create_appearance_tab(self):
        tab = self.tabview.tab("Appearance")
        tab.grid_columnconfigure(1, weight=1)

        customtkinter.CTkLabel(tab, text="Theme:", font=customtkinter.CTkFont(weight="bold")).grid(row=0, column=0,
                                                                                                   padx=20,
                                                                                                   pady=(20, 5),
                                                                                                   sticky="w")
        theme_menu = customtkinter.CTkOptionMenu(tab, variable=self.theme_var, values=["Light", "Dark", "System"],
                                                 command=self.on_theme_selected)
        theme_menu.grid(row=0, column=1, padx=20, pady=(20, 5), sticky="ew")

    def on_theme_selected(self, theme):
        logging.info(f"Theme changed to: {theme}")
        customtkinter.set_appearance_mode(theme)

    def load_worlds(self):
        lang = self.active_language.get()
        self.worlds = self.db.get_all_worlds(lang)
        world_names = [w['world_name'] for w in self.worlds]

        active_world_id = self.settings.get("active_world_id")
        active_world = next((w for w in self.worlds if w['world_id'] == active_world_id), None)

        if not world_names:
            self.world_dropdown.configure(values=["No Worlds Found"])
            self.active_world_name.set("No Worlds Found")
        else:
            self.world_dropdown.configure(values=world_names)
            if active_world:
                self.active_world_name.set(active_world['world_name'])
            else:
                self.active_world_name.set(world_names[0])

        self.on_world_selected(self.active_world_name.get())

    def on_language_selected(self, selected_language):
        self.load_worlds()

    def on_world_selected(self, selected_world_name):
        if not selected_world_name or selected_world_name == "No Worlds Found":
            self.campaign_dropdown.configure(values=["No Campaigns Found"])
            self.active_campaign_name.set("No Campaigns Found")
            return

        world_data = next((w for w in self.worlds if w['world_name'] == selected_world_name), None)
        if not world_data: return

        self.settings.set("active_world_id", world_data['world_id'])

        all_campaigns = self.db.get_campaigns_for_world(world_data['world_id'])
        lang = self.active_language.get()
        lang_campaigns = [c for c in all_campaigns if c['language'] == lang]
        campaign_names = [c['campaign_name'] for c in lang_campaigns]

        active_campaign_id = self.settings.get("active_campaign_id")
        active_campaign = next((c for c in lang_campaigns if c['campaign_id'] == active_campaign_id), None)

        if not campaign_names:
            self.campaign_dropdown.configure(values=["No Campaigns Found"])
            self.active_campaign_name.set("No Campaigns Found")
        else:
            self.campaign_dropdown.configure(values=campaign_names)
            if active_campaign:
                self.active_campaign_name.set(active_campaign['campaign_name'])
            else:
                self.active_campaign_name.set(campaign_names[0])

        self.on_campaign_selected(self.active_campaign_name.get())

    def on_campaign_selected(self, selected_campaign_name):
        if not selected_campaign_name or selected_campaign_name == "No Campaigns Found":
            self.settings.set("active_campaign_id", None)
            return

        campaign_data = next((c for c in self.db.get_campaigns_for_world(self.settings.get("active_world_id")) if
                              c['campaign_name'] == selected_campaign_name), None)
        if campaign_data:
            self.settings.set("active_campaign_id", campaign_data['campaign_id'])

    def save_all_settings(self):
        """Collects all settings from the UI and saves them."""
        self.settings.set("active_language", self.active_language.get())
        self.settings.set("text_model", self.text_model_var.get())
        self.settings.set("image_model", self.image_model_var.get())
        self.settings.set("theme", self.theme_var.get())
        self.settings.set("srd_pdf_path", self.srd_path_entry.get())

        prompts = self.settings.get("prompts", {})
        prompts["lore_master"] = self.lore_master_prompt_textbox.get("1.0", "end-1c")
        prompts["rules_lawyer"] = self.rules_lawyer_prompt_textbox.get("1.0", "end-1c")
        prompts["npc_generation"] = self.npc_prompt_textbox.get("1.0", "end-1c")
        prompts["translation"] = self.trans_prompt_textbox.get("1.0", "end-1c")
        prompts["npc_simulation_short"] = self.sim_short_prompt_textbox.get("1.0", "end-1c")
        prompts["npc_simulation_long"] = self.sim_long_prompt_textbox.get("1.0", "end-1c")
        self.settings.set("prompts", prompts)

        self.settings.save()
        logging.info("All settings have been saved.")