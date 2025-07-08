import customtkinter
import logging
from ui_components import ConfirmationDialog
from config import (
    GENDER_OPTIONS, ATTITUDE_OPTIONS, RARITY_OPTIONS, ENVIRONMENT_OPTIONS,
    RACE_OPTIONS, CLASS_OPTIONS, BACKGROUND_OPTIONS
)
import threading
import io
from PIL import Image, UnidentifiedImageError
from npc_simulator_app import NpcSimulatorApp  # Import the simulator


class CharacterManagerApp(customtkinter.CTkToplevel):
    """
    A unified Toplevel window for managing both Player Characters (PCs) and Non-Player Characters (NPCs)
    within a selected world and campaign.
    """

    def __init__(self, master, data_manager, api_service, world_data, campaign_data):
        super().__init__(master)
        self.master = master
        self.db = data_manager
        self.ai = api_service
        self.world_data = world_data
        self.campaign_data = campaign_data

        self.title(f"Character Manager - {campaign_data['campaign_name']}")
        self.geometry("1200x800")
        self.minsize(1000, 700)
        self.grab_set()

        self.characters_in_view = []
        self.selected_character_id = None
        self.current_character_data = {}  # Full data for the selected character
        self.workshop_image_data = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._create_widgets()
        self.load_and_display_characters()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        """Handles window closing."""
        self.master.deiconify()
        self.destroy()

    def _create_widgets(self):
        # --- Sidebar for Character List ---
        self.sidebar_frame = customtkinter.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(1, weight=1)

        customtkinter.CTkLabel(self.sidebar_frame, text="Characters",
                               font=customtkinter.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20,
                                                                                        pady=(20, 10), columnspan=2)

        self.character_list_frame = customtkinter.CTkScrollableFrame(self.sidebar_frame, label_text="Roster")
        self.character_list_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=10, sticky="nsew")
        self.character_buttons = {}

        button_frame = customtkinter.CTkFrame(self.sidebar_frame, fg_color="transparent")
        button_frame.grid(row=2, column=0, columnspan=2, padx=20, pady=10, sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        customtkinter.CTkButton(button_frame, text="+ New", command=self.new_character).grid(row=0, column=0,
                                                                                             padx=(0, 5), sticky="ew")
        customtkinter.CTkButton(button_frame, text="- Delete", fg_color="#D32F2F", hover_color="#B71C1C",
                                command=self.delete_selected_character).grid(row=0, column=1, padx=(5, 0), sticky="ew")

        # --- Main Editing Area ---
        self.main_frame = customtkinter.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        self.tabview = customtkinter.CTkTabview(self.main_frame, corner_radius=10)
        self.tabview.pack(expand=True, fill="both", padx=10, pady=10)
        self.tabview.add("PC Sheet")
        self.tabview.add("NPC Sheet")
        self.tabview.add("NPC Generator")

        self._create_pc_sheet_tab(self.tabview.tab("PC Sheet"))
        self._create_npc_sheet_tab(self.tabview.tab("NPC Sheet"))
        self._create_npc_generator_tab(self.tabview.tab("NPC Generator"))

    def _create_pc_sheet_tab(self, tab):
        tab.grid_columnconfigure(0, weight=2)
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # --- PC Main Info Frame ---
        pc_info_frame = customtkinter.CTkFrame(tab)
        pc_info_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew", columnspan=2)
        pc_info_frame.grid_columnconfigure(1, weight=1)

        customtkinter.CTkLabel(pc_info_frame, text="Name:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.pc_name_entry = customtkinter.CTkEntry(pc_info_frame)
        self.pc_name_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        customtkinter.CTkLabel(pc_info_frame, text="Race/Class:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.pc_race_class_entry = customtkinter.CTkEntry(pc_info_frame)
        self.pc_race_class_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        # --- PC Stats Frame ---
        pc_stats_frame = customtkinter.CTkFrame(tab)
        pc_stats_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        pc_stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        customtkinter.CTkLabel(pc_stats_frame, text="Core Stats", font=customtkinter.CTkFont(weight="bold")).grid(row=0,
                                                                                                                  column=0,
                                                                                                                  columnspan=4,
                                                                                                                  pady=10)

        self.pc_level_entry = self._create_labeled_entry(pc_stats_frame, "Level:", 1, 0)
        self.pc_hp_entry = self._create_labeled_entry(pc_stats_frame, "HP:", 1, 2)
        self.pc_ac_entry = self._create_labeled_entry(pc_stats_frame, "AC:", 2, 0)

        self.pc_str_entry = self._create_labeled_entry(pc_stats_frame, "STR:", 3, 0)
        self.pc_dex_entry = self._create_labeled_entry(pc_stats_frame, "DEX:", 3, 2)
        self.pc_con_entry = self._create_labeled_entry(pc_stats_frame, "CON:", 4, 0)
        self.pc_int_entry = self._create_labeled_entry(pc_stats_frame, "INT:", 4, 2)
        self.pc_wis_entry = self._create_labeled_entry(pc_stats_frame, "WIS:", 5, 0)
        self.pc_cha_entry = self._create_labeled_entry(pc_stats_frame, "CHA:", 5, 2)

        customtkinter.CTkLabel(pc_stats_frame, text="Skills:").grid(row=6, column=0, padx=10, pady=5, sticky="w")
        self.pc_skills_entry = customtkinter.CTkEntry(pc_stats_frame)
        self.pc_skills_entry.grid(row=6, column=1, columnspan=3, padx=10, pady=5, sticky="ew")

        # --- PC Details Frame ---
        pc_details_frame = customtkinter.CTkFrame(tab)
        pc_details_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        pc_details_frame.grid_rowconfigure(1, weight=1)
        pc_details_frame.grid_columnconfigure(0, weight=1)

        pc_details_tabview = customtkinter.CTkTabview(pc_details_frame)
        pc_details_tabview.pack(expand=True, fill="both")
        pc_details_tabview.add("Appearance")
        pc_details_tabview.add("Personality")
        pc_details_tabview.add("Backstory")

        self.pc_appearance_textbox = customtkinter.CTkTextbox(pc_details_tabview.tab("Appearance"), wrap="word")
        self.pc_appearance_textbox.pack(expand=True, fill="both")
        self.pc_personality_textbox = customtkinter.CTkTextbox(pc_details_tabview.tab("Personality"), wrap="word")
        self.pc_personality_textbox.pack(expand=True, fill="both")
        self.pc_backstory_textbox = customtkinter.CTkTextbox(pc_details_tabview.tab("Backstory"), wrap="word")
        self.pc_backstory_textbox.pack(expand=True, fill="both")

        # --- PC Save Button ---
        customtkinter.CTkButton(tab, text="Save PC", command=lambda: self.save_character(is_player=True)).grid(row=2,
                                                                                                               column=0,
                                                                                                               columnspan=2,
                                                                                                               pady=10,
                                                                                                               padx=10,
                                                                                                               sticky="ew")

    def _create_npc_sheet_tab(self, tab):
        tab.grid_columnconfigure(0, weight=2)
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # --- NPC Main Info ---
        npc_info_frame = customtkinter.CTkFrame(tab)
        npc_info_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        npc_info_frame.grid_columnconfigure(1, weight=1)

        customtkinter.CTkLabel(npc_info_frame, text="Name:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.npc_name_entry = customtkinter.CTkEntry(npc_info_frame)
        self.npc_name_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        customtkinter.CTkLabel(npc_info_frame, text="Race/Class:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.npc_race_class_entry = customtkinter.CTkEntry(npc_info_frame)
        self.npc_race_class_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        # --- NPC Text Details ---
        npc_text_frame = customtkinter.CTkFrame(tab)
        npc_text_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        npc_text_frame.grid_columnconfigure(0, weight=1)
        npc_text_frame.grid_rowconfigure(0, weight=1)

        npc_details_tabview = customtkinter.CTkTabview(npc_text_frame)
        npc_details_tabview.pack(expand=True, fill="both")
        npc_details_tabview.add("Appearance")
        npc_details_tabview.add("Personality")
        npc_details_tabview.add("Backstory")
        npc_details_tabview.add("Plot Hooks")
        npc_details_tabview.add("Roleplaying Tips")

        self.npc_appearance_textbox = customtkinter.CTkTextbox(npc_details_tabview.tab("Appearance"), wrap="word")
        self.npc_appearance_textbox.pack(expand=True, fill="both")
        self.npc_personality_textbox = customtkinter.CTkTextbox(npc_details_tabview.tab("Personality"), wrap="word")
        self.npc_personality_textbox.pack(expand=True, fill="both")
        self.npc_backstory_textbox = customtkinter.CTkTextbox(npc_details_tabview.tab("Backstory"), wrap="word")
        self.npc_backstory_textbox.pack(expand=True, fill="both")
        self.npc_plothooks_textbox = customtkinter.CTkTextbox(npc_details_tabview.tab("Plot Hooks"), wrap="word")
        self.npc_plothooks_textbox.pack(expand=True, fill="both")
        self.npc_roleplaying_textbox = customtkinter.CTkTextbox(npc_details_tabview.tab("Roleplaying Tips"),
                                                                wrap="word")
        self.npc_roleplaying_textbox.pack(expand=True, fill="both")

        # --- NPC Portrait and Actions ---
        npc_portrait_frame = customtkinter.CTkFrame(tab)
        npc_portrait_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="nsew")
        npc_portrait_frame.grid_rowconfigure(0, weight=1)
        npc_portrait_frame.grid_columnconfigure(0, weight=1)

        self.npc_portrait_label = customtkinter.CTkLabel(npc_portrait_frame, text="No Portrait", width=250, height=250)
        self.npc_portrait_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        customtkinter.CTkButton(npc_portrait_frame, text="Upload Portrait", command=self.upload_portrait).pack(pady=10,
                                                                                                               padx=10,
                                                                                                               fill="x")
        customtkinter.CTkButton(npc_portrait_frame, text="Launch Simulator", command=self.launch_simulator).pack(
            pady=10, padx=10, fill="x")

        # --- NPC Save Button ---
        customtkinter.CTkButton(tab, text="Save NPC", command=lambda: self.save_character(is_player=False)).grid(row=2,
                                                                                                                 column=0,
                                                                                                                 columnspan=2,
                                                                                                                 pady=10,
                                                                                                                 padx=10,
                                                                                                                 sticky="ew")

    def _create_npc_generator_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        generator_frame = customtkinter.CTkScrollableFrame(tab, label_text="NPC Generation Parameters")
        generator_frame.pack(expand=True, fill="both", padx=10, pady=10)
        generator_frame.grid_columnconfigure(0, weight=1)

        # Options for generation
        options_frame = customtkinter.CTkFrame(generator_frame)
        options_frame.pack(fill="x", pady=10)
        options_frame.grid_columnconfigure((1, 3), weight=1)

        self.gender_var = customtkinter.StringVar(value=GENDER_OPTIONS[0])
        self.attitude_var = customtkinter.StringVar(value=ATTITUDE_OPTIONS[0])
        self.rarity_var = customtkinter.StringVar(value=RARITY_OPTIONS[0])
        self.environment_var = customtkinter.StringVar(value=ENVIRONMENT_OPTIONS[0])
        self.race_var = customtkinter.StringVar(value=RACE_OPTIONS[0])
        self.class_var = customtkinter.StringVar(value=CLASS_OPTIONS[0])
        self.background_var = customtkinter.StringVar(value=BACKGROUND_OPTIONS[0])

        option_map = {
            "Gender": (self.gender_var, GENDER_OPTIONS), "Attitude": (self.attitude_var, ATTITUDE_OPTIONS),
            "Rarity": (self.rarity_var, RARITY_OPTIONS), "Environment": (self.environment_var, ENVIRONMENT_OPTIONS),
            "Race": (self.race_var, RACE_OPTIONS), "Class": (self.class_var, CLASS_OPTIONS),
            "Background": (self.background_var, BACKGROUND_OPTIONS)
        }
        row_counter = 0
        for i, (label, (var, values)) in enumerate(option_map.items()):
            col = (i % 2) * 2
            if i > 0 and col == 0: row_counter += 1
            self._create_workshop_option_menu(options_frame, label, var, values, row_counter, col)

        # Generation Button
        self.generate_button = customtkinter.CTkButton(generator_frame, text="Generate NPC with AI", height=40,
                                                       command=self.start_generation_thread)
        self.generate_button.pack(pady=20, fill="x", padx=10)

        # Status Textbox
        self.generator_status_textbox = customtkinter.CTkTextbox(generator_frame, height=100, wrap="word",
                                                                 state="disabled")
        self.generator_status_textbox.pack(pady=10, fill="x", expand=True, padx=10)

    def _create_labeled_entry(self, parent, text, row, col):
        customtkinter.CTkLabel(parent, text=text).grid(row=row, column=col, padx=10, pady=5, sticky="w")
        entry = customtkinter.CTkEntry(parent)
        entry.grid(row=row, column=col + 1, padx=10, pady=5, sticky="ew")
        return entry

    def _create_workshop_option_menu(self, parent, text, variable, values, row, col):
        customtkinter.CTkLabel(parent, text=text).grid(row=row, column=col, padx=(10, 5), pady=5, sticky="w")
        customtkinter.CTkOptionMenu(parent, variable=variable, values=values).grid(row=row, column=col + 1,
                                                                                   padx=(0, 10), pady=5, sticky="ew")

    def load_and_display_characters(self):
        """Loads all characters for the current world and displays them in the sidebar."""
        lang = self.campaign_data.get('language')
        world_id = self.world_data.get('world_id')
        self.characters_in_view = self.db.get_characters_for_world(world_id, lang)

        # Clear existing buttons
        for widget in self.character_list_frame.winfo_children():
            widget.destroy()
        self.character_buttons = {}

        # Sort characters alphabetically by name
        sorted_characters = sorted(self.characters_in_view, key=lambda c: c.get('name', ''))

        for char_data in sorted_characters:
            char_id = char_data['character_id']
            char_name = char_data.get('name', 'Unnamed')
            prefix = "[PC] " if char_data.get('is_player') else "[NPC] "

            button = customtkinter.CTkButton(self.character_list_frame, text=f"{prefix}{char_name}",
                                             command=lambda c=char_data: self.select_character(c))
            button.pack(pady=5, padx=5, fill="x")
            self.character_buttons[char_id] = button

        if sorted_characters:
            self.select_character(sorted_characters[0])
        else:
            self.new_character()

    def select_character(self, char_data):
        self.selected_character_id = char_data['character_id']
        self.current_character_data = char_data

        if char_data.get('is_player'):
            self.tabview.set("PC Sheet")
            self.populate_pc_sheet(char_data)
        else:
            self.tabview.set("NPC Sheet")
            self.populate_npc_sheet(char_data)

        self.highlight_selected_character()

    def highlight_selected_character(self):
        if not self.selected_character_id:
            return
        for char_id, button in self.character_buttons.items():
            if char_id == self.selected_character_id:
                button.configure(fg_color=customtkinter.ThemeManager.theme["CTkButton"]["hover_color"])
            else:
                button.configure(fg_color=customtkinter.ThemeManager.theme["CTkButton"]["fg_color"])

    def new_character(self):
        self.selected_character_id = None
        self.current_character_data = {}
        self.clear_all_fields()
        self.tabview.set("PC Sheet")
        self.pc_name_entry.focus()
        self.highlight_selected_character()

    def clear_all_fields(self):
        # PC Fields
        self.pc_name_entry.delete(0, "end")
        self.pc_race_class_entry.delete(0, "end")
        self.pc_level_entry.delete(0, "end")
        self.pc_hp_entry.delete(0, "end")
        self.pc_ac_entry.delete(0, "end")
        self.pc_str_entry.delete(0, "end")
        self.pc_dex_entry.delete(0, "end")
        self.pc_con_entry.delete(0, "end")
        self.pc_int_entry.delete(0, "end")
        self.pc_wis_entry.delete(0, "end")
        self.pc_cha_entry.delete(0, "end")
        self.pc_skills_entry.delete(0, "end")
        self.pc_appearance_textbox.delete("1.0", "end")
        self.pc_personality_textbox.delete("1.0", "end")
        self.pc_backstory_textbox.delete("1.0", "end")

        # NPC Fields
        self.npc_name_entry.delete(0, "end")
        self.npc_race_class_entry.delete(0, "end")
        self.npc_appearance_textbox.delete("1.0", "end")
        self.npc_personality_textbox.delete("1.0", "end")
        self.npc_backstory_textbox.delete("1.0", "end")
        self.npc_plothooks_textbox.delete("1.0", "end")
        self.npc_roleplaying_textbox.delete("1.0", "end")
        self.npc_portrait_label.configure(image=None, text="No Portrait")
        self.workshop_image_data = None

    def populate_pc_sheet(self, data):
        self.clear_all_fields()
        self.pc_name_entry.insert(0, data.get("name", ""))
        self.pc_race_class_entry.insert(0, data.get("race_class", ""))
        self.pc_level_entry.insert(0, str(data.get("level", "")))
        self.pc_hp_entry.insert(0, str(data.get("hp", "")))
        self.pc_ac_entry.insert(0, str(data.get("ac", "")))
        self.pc_str_entry.insert(0, str(data.get("strength", "")))
        self.pc_dex_entry.insert(0, str(data.get("dexterity", "")))
        self.pc_con_entry.insert(0, str(data.get("constitution", "")))
        self.pc_int_entry.insert(0, str(data.get("intelligence", "")))
        self.pc_wis_entry.insert(0, str(data.get("wisdom", "")))
        self.pc_cha_entry.insert(0, str(data.get("charisma", "")))
        self.pc_skills_entry.insert(0, data.get("skills", ""))
        self.pc_appearance_textbox.insert("1.0", data.get("appearance", ""))
        self.pc_personality_textbox.insert("1.0", data.get("personality", ""))
        self.pc_backstory_textbox.insert("1.0", data.get("backstory", ""))

    def populate_npc_sheet(self, data):
        self.clear_all_fields()
        self.npc_name_entry.insert(0, data.get("name", ""))
        self.npc_race_class_entry.insert(0, data.get("race_class", ""))
        self.npc_appearance_textbox.insert("1.0", data.get("appearance", ""))
        self.npc_personality_textbox.insert("1.0", data.get("personality", ""))
        self.npc_backstory_textbox.insert("1.0", data.get("backstory", ""))
        self.npc_plothooks_textbox.insert("1.0", data.get("plot_hooks", ""))
        self.npc_roleplaying_textbox.insert("1.0", data.get("roleplaying_tips", ""))

        self.workshop_image_data = data.get("image_data")
        self._update_npc_portrait()

    def save_character(self, is_player):
        """Saves the character currently being edited."""
        core_data = {}
        translation_data = {}

        if is_player:
            translation_data['name'] = self.pc_name_entry.get().strip()
            if not translation_data['name']:
                logging.error("PC Name cannot be empty.")
                return
            translation_data['race_class'] = self.pc_race_class_entry.get()
            translation_data['appearance'] = self.pc_appearance_textbox.get("1.0", "end-1c")
            translation_data['personality'] = self.pc_personality_textbox.get("1.0", "end-1c")
            translation_data['backstory'] = self.pc_backstory_textbox.get("1.0", "end-1c")

            # Helper to convert to int, returns None if empty or invalid
            def to_int(value):
                try:
                    return int(value)
                except (ValueError, TypeError):
                    return None

            core_data['level'] = to_int(self.pc_level_entry.get())
            core_data['hp'] = to_int(self.pc_hp_entry.get())
            core_data['ac'] = to_int(self.pc_ac_entry.get())
            core_data['strength'] = to_int(self.pc_str_entry.get())
            core_data['dexterity'] = to_int(self.pc_dex_entry.get())
            core_data['constitution'] = to_int(self.pc_con_entry.get())
            core_data['intelligence'] = to_int(self.pc_int_entry.get())
            core_data['wisdom'] = to_int(self.pc_wis_entry.get())
            core_data['charisma'] = to_int(self.pc_cha_entry.get())
            core_data['skills'] = self.pc_skills_entry.get()
            core_data['image_data'] = self.current_character_data.get('image_data')  # Preserve image if any
        else:  # is_npc
            translation_data['name'] = self.npc_name_entry.get().strip()
            if not translation_data['name']:
                logging.error("NPC Name cannot be empty.")
                return
            translation_data['race_class'] = self.npc_race_class_entry.get()
            translation_data['appearance'] = self.npc_appearance_textbox.get("1.0", "end-1c")
            translation_data['personality'] = self.npc_personality_textbox.get("1.0", "end-1c")
            translation_data['backstory'] = self.npc_backstory_textbox.get("1.0", "end-1c")
            translation_data['plot_hooks'] = self.npc_plothooks_textbox.get("1.0", "end-1c")
            translation_data['roleplaying_tips'] = self.npc_roleplaying_textbox.get("1.0", "end-1c")
            core_data['image_data'] = self.workshop_image_data

        try:
            world_id = self.world_data['world_id']
            lang = self.campaign_data['language']

            if self.selected_character_id:
                # Update existing character
                # Make sure to pass the original core data for fields not on the form
                original_core = {k: self.current_character_data.get(k) for k in
                                 ['level', 'hp', 'ac', 'strength', 'dexterity', 'constitution', 'intelligence',
                                  'wisdom', 'charisma', 'skills', 'image_data']}
                original_core.update(core_data)  # Overwrite with new data from form
                self.db.update_character(self.selected_character_id, lang, original_core, translation_data)
            else:
                # Create new character
                self.db.create_character(world_id, is_player, lang, core_data, translation_data)

            self.load_and_display_characters()
            logging.info(f"Character '{translation_data['name']}' saved successfully.")

        except Exception as e:
            logging.error(f"Error saving character: {e}")

    def delete_selected_character(self):
        if not self.selected_character_id:
            return

        char_name = self.current_character_data.get('name', 'this character')
        msg = f"Are you sure you want to delete '{char_name}'?"
        ConfirmationDialog(self, title="Confirm Deletion", message=msg, command=self._confirm_and_delete)

    def _confirm_and_delete(self):
        if not self.selected_character_id:
            return
        try:
            self.db.delete_character(self.selected_character_id)
            self.load_and_display_characters()
        except Exception as e:
            logging.error(f"Failed to delete character: {e}")

    def start_generation_thread(self):
        if not self.ai.is_api_key_valid():
            self._update_textbox(self.generator_status_textbox, "Error: Gemini API Key is missing or invalid.")
            return
        threading.Thread(target=self._run_generation_task, daemon=True).start()

    def _run_generation_task(self):
        self.after(0, lambda: self.generate_button.configure(state="disabled"))
        self.after(0, lambda: self._update_textbox(self.generator_status_textbox, "Generating NPC with Gemini..."))
        try:
            params = {
                'gender': self.gender_var.get(), 'attitude': self.attitude_var.get(),
                'rarity': self.rarity_var.get(), 'environment': self.environment_var.get(),
                'race': self.race_var.get(), 'character_class': self.class_var.get(),
                'background': self.background_var.get(),
                'custom_prompt': ""  # Can add a textbox for this later if needed
            }

            npc_data, _ = self.ai.generate_npc(
                params,
                campaign_data=self.campaign_data,
                include_party=True,
                include_session=True
            )

            self.after(0, lambda: self._update_textbox(self.generator_status_textbox, "Generating portrait..."))
            image_bytes = self.ai.generate_npc_portrait(npc_data.get("appearance", ""))
            npc_data['image_data'] = image_bytes

            self.after(0, self.populate_npc_sheet_from_generator, npc_data)
            self.after(0, lambda: self._update_textbox(self.generator_status_textbox,
                                                       "NPC generated! Review and save in the 'NPC Sheet' tab."))

        except Exception as e:
            logging.error(f"Generation failed: {e}")
            self.after(0,
                       lambda err=e: self._update_textbox(self.generator_status_textbox, f"Generation Error:\n\n{err}"))
        finally:
            self.after(0, lambda: self.generate_button.configure(state="normal"))

    def populate_npc_sheet_from_generator(self, data):
        """Populates the NPC sheet with data from the generator, but doesn't select or save it yet."""
        self.selected_character_id = None  # This is a new character
        self.current_character_data = {}
        self.populate_npc_sheet(data)
        self.tabview.set("NPC Sheet")
        self.npc_name_entry.focus()
        self.highlight_selected_character()

    def upload_portrait(self):
        try:
            file_path = filedialog.askopenfilename(title="Select a Portrait",
                                                   filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.gif")])
            if file_path:
                with open(file_path, 'rb') as f:
                    image_bytes = f.read()
                self.workshop_image_data = image_bytes
                self._update_npc_portrait()
                logging.info(f"Image loaded from {file_path}")
        except Exception as e:
            logging.error(f"Failed to upload image: {e}")

    def launch_simulator(self):
        """Launches the NPC simulator for the currently selected NPC."""
        if not self.selected_character_id or self.current_character_data.get('is_player'):
            logging.warning("Simulator launch attempted without a valid NPC selected.")
            # Optionally, show a message to the user
            return

        # The master of CharacterManagerApp is MainMenuApp, which has the open_toplevel method
        # However, to keep it simple, we can just open a new toplevel window directly.
        NpcSimulatorApp(
            master=self,
            api_service=self.ai,
            data_manager=self.db,
            npc_data=self.current_character_data,
            campaign_data=self.campaign_data
        )

    def _update_npc_portrait(self):
        ctk_image = self._create_ctk_image_from_data(self.workshop_image_data, size=(250, 250))
        self.npc_portrait_label.configure(image=ctk_image, text="" if ctk_image else "No Portrait")
        self.npc_portrait_label.image = ctk_image

    def _create_ctk_image_from_data(self, image_bytes, size=(300, 300)):
        if not image_bytes: return None
        try:
            pil_image = Image.open(io.BytesIO(image_bytes))
            return customtkinter.CTkImage(light_image=pil_image, dark_image=pil_image, size=size)
        except (UnidentifiedImageError, io.UnsupportedOperation) as e:
            logging.error(f"Failed to create image from data: {e}")
            return None

    def _update_textbox(self, textbox, text, state="disabled"):
        textbox.configure(state="normal")
        textbox.delete("1.0", "end")
        textbox.insert("1.0", text)
        textbox.configure(state=state)