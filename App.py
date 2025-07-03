import tkinter
import customtkinter
from tkinter import filedialog
import google.generativeai as genai
import json
import threading
import os
import logging
import sqlite3
import base64
import io
import httpx  # Required for making HTTP requests to the image generation API
from PIL import Image  # We need the Pillow library for image handling

# ======================================================================================
# --- SECTION 1: CONFIGURATION (Would be in a separate 'config.py' file) ---
# ======================================================================================
API_KEY = "AIzaSyCifrOD-4dLN05hq_a3KLYU3WLrG82TAbw"
DB_FILE = "dnd_toolkit.db"
TEXT_MODEL_NAME = 'gemini-2.5-flash'
IMAGE_MODEL_NAME = 'imagen-3.0-generate-002'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- D&D Options for Generator ---
GENDER_OPTIONS = ["Random", "Female", "Male", "Non-binary"]
ATTITUDE_OPTIONS = ["Random", "Friendly", "Neutral", "Hostile"]
RARITY_OPTIONS = ["Random", "Commoner", "Uncommon Adventurer", "Rare Hero", "Legendary Boss"]
ENVIRONMENT_OPTIONS = ["Random", "City", "Forest", "Mountains", "Plains", "Swamp", "Dungeon", "Tavern", "Castle"]
RACE_OPTIONS = [
    "Random", "Human", "Elf", "Dwarf", "Halfling", "Gnome", "Half-Elf",
    "Half-Orc", "Dragonborn", "Tiefling", "Aasimar", "Goblin", "Orc", "Kobold"
]
CLASS_OPTIONS = [
    "Random", "Fighter", "Wizard", "Rogue", "Cleric", "Ranger", "Barbarian",
    "Paladin", "Bard", "Monk", "Druid", "Sorcerer", "Warlock", "Artificer", "Commoner"
]
BACKGROUND_OPTIONS = [
    "Random", "Acolyte", "Charlatan", "Criminal", "Entertainer", "Folk Hero", "Guild Artisan",
    "Hermit", "Noble", "Outlander", "Sage", "Sailor", "Soldier", "Urchin"
]


# ======================================================================================
# --- SECTION 2: SERVICES (Would be in 'services.py' or similar) ---
# ======================================================================================
class DataManager:
    def __init__(self, db_filepath):
        self.db_filepath = db_filepath
        self._create_table()

    def _get_connection(self):
        return sqlite3.connect(self.db_filepath)

    def _create_table(self):
        create_table_sql = """
                           CREATE TABLE IF NOT EXISTS npcs \
                           ( \
                               name \
                               TEXT \
                               PRIMARY \
                               KEY, \
                               race_class \
                               TEXT, \
                               appearance \
                               TEXT, \
                               personality \
                               TEXT, \
                               backstory \
                               TEXT, \
                               plot_hooks \
                               TEXT, \
                               attitude \
                               TEXT, \
                               rarity \
                               TEXT, \
                               race \
                               TEXT, \
                               character_class \
                               TEXT, \
                               environment \
                               TEXT, \
                               background \
                               TEXT, \
                               gender \
                               TEXT, \
                               image_data \
                               BLOB
                           ); \
                           """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(create_table_sql)
                conn.commit()
            logging.info("Database table 'npcs' is ready.")
        except sqlite3.Error as e:
            logging.error(f"Database error during table creation: {e}")

    def load_data(self):
        npcs_dict = {}
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM npcs")
                rows = cursor.fetchall()
                for row in rows:
                    npcs_dict[row['name']] = dict(row)
            logging.info(f"Successfully loaded {len(npcs_dict)} NPCs from {self.db_filepath}.")
            return npcs_dict
        except sqlite3.Error as e:
            logging.error(f"Failed to load data from database: {e}")
            return {}

    def save_npc(self, npc_data, old_name=None):
        if old_name and old_name != npc_data['name']:
            self.delete_npc(old_name)

        sql = """
        INSERT OR REPLACE INTO npcs (name, race_class, appearance, personality, backstory, plot_hooks, 
                                     attitude, rarity, race, character_class, environment, background, gender, image_data)
        VALUES (:name, :race_class, :appearance, :personality, :backstory, :plot_hooks,
                :attitude, :rarity, :race, :character_class, :environment, :background, :gender, :image_data)
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, npc_data)
                conn.commit()
            logging.info(f"Successfully saved NPC '{npc_data['name']}' to the database.")
        except sqlite3.Error as e:
            logging.error(f"Failed to save NPC '{npc_data['name']}': {e}")

    def delete_npc(self, npc_name):
        sql = "DELETE FROM npcs WHERE name = ?"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (npc_name,))
                conn.commit()
            logging.info(f"Successfully deleted NPC '{npc_name}' from the database.")
        except sqlite3.Error as e:
            logging.error(f"Failed to delete NPC '{npc_name}': {e}")


class GeminiService:
    def __init__(self, api_key, text_model_name, image_model_name):
        self.api_key = api_key
        self.text_model_name = text_model_name
        self.image_model_name = image_model_name
        self.text_model = None
        self._is_configured = False
        self._configure_api()

    def _configure_api(self):
        if not self._is_configured and self.is_api_key_valid():
            genai.configure(api_key=self.api_key)
            self.text_model = genai.GenerativeModel(self.text_model_name)
            self._is_configured = True
            logging.info(f"Gemini API configured successfully with model {self.text_model_name}.")
            return True
        return self._is_configured

    def is_api_key_valid(self):
        is_valid = self.api_key and self.api_key != "PASTE_YOUR_GEMINI_API_KEY_HERE"
        if not is_valid: logging.warning("API Key is missing.")
        return is_valid

    def generate_npc(self, params):
        if not self.text_model: raise ValueError("API Key/Model not configured.")
        prompt = f"""
        You are a creative Dungeon Master assistant. Your task is to generate a compelling D&D NPC based on the following parameters.
        For any parameter set to "Random", you must invent a suitable value.
        The output MUST be a valid JSON object with the exact keys: "name", "gender", "race_class", "appearance", "personality", "backstory", "plot_hooks", "background", "attitude", "rarity", "race", "character_class", "environment".
        - The values for gender, attitude, rarity, race, character_class, environment, and background in the JSON should reflect the user's choices if they weren't 'Random'. If they were 'Random', you must invent a plausible value for that key.

        **Parameters:**
        - Gender: {params['gender']}
        - Attitude: {params['attitude']}
        - Rarity/Level: {params['rarity']}
        - Environment: {params['environment']}
        - Race: {params['race']}
        - Class: {params['character_class']}
        - Background: {params['background']}

        Generate the NPC now.
        """
        logging.info("Sending generation request to Gemini.")
        response = self.text_model.generate_content(prompt)
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(cleaned_response), response.text

    def simulate_reaction(self, npc_data, situation):
        if not self.text_model: raise ValueError("API Key/Model not configured.")
        full_context = (f"Appearance: {npc_data.get('appearance', 'N/A')}\n"
                        f"Personality: {npc_data.get('personality', 'N/A')}\n"
                        f"Backstory: {npc_data.get('backstory', 'N/A')}")
        prompt = f"""
        Act as a D&D NPC.
        **NPC Profile:**
        - Name: {npc_data.get('name', 'N/A')}, Race/Class: {npc_data.get('race_class', 'N/A')}
        - Character Info: {full_context}
        **Situation:** {situation}
        **Your Reaction (in character):**
        """
        logging.info(f"Sending simulation request for {npc_data.get('name')}.")
        response = self.text_model.generate_content(prompt)
        return response.text

    def generate_npc_portrait(self, appearance_prompt):
        """This function requires a billed Google Cloud account to use the Imagen API."""
        raise NotImplementedError("Imagen API is only accessible to billed users at this time.")

        if not self.is_api_key_valid(): raise ValueError("API Key is not configured.")
        logging.info("Sending image generation request to Imagen...")
        prompt = f"A digital painting portrait of a D&D character: {appearance_prompt}. Fantasy art, character concept, detailed, high quality."
        payload = {"instances": [{"prompt": prompt}], "parameters": {"sampleCount": 1}}
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.image_model_name}:predict?key={self.api_key}"
        headers = {'Content-Type': 'application/json'}

        with httpx.Client() as client:
            response = client.post(api_url, json=payload, headers=headers, timeout=120.0)

        if response.status_code == 200:
            result = response.json()
            if result.get("predictions") and result["predictions"][0].get("bytesBase64Encoded"):
                return base64.b64decode(result["predictions"][0]["bytesBase64Encoded"])
            raise Exception("Image generation failed: No image data in response.")
        raise Exception(f"Image generation failed with status {response.status_code}")


# ======================================================================================
# --- SECTION 3: NPC TOOLKIT APPLICATION (Would be in 'npc_app.py') ---
# ======================================================================================
class NpcApp(customtkinter.CTk):
    def __init__(self, data_manager, api_service):
        super().__init__()
        self.db = data_manager
        self.ai = api_service
        self.title("D&D NPC Manager")
        self.minsize(1000, 750)
        self.npcs = self.db.load_data()
        self.selected_npc_name = None
        self._npc_in_workshop = {}
        self.roster_ctk_image = None
        self.workshop_ctk_image = None
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._create_widgets()
        self.update_npc_list()
        self.select_first_npc()
        self.after(100, lambda: self.state('zoomed'))

    def _create_widgets(self):
        self.sidebar_frame = customtkinter.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(2, weight=1)
        customtkinter.CTkLabel(self.sidebar_frame, text="Your NPCs",
                               font=customtkinter.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20,
                                                                                        pady=(20, 10))
        customtkinter.CTkButton(self.sidebar_frame, text="+ New NPC", command=self.go_to_workshop_new).grid(row=1,
                                                                                                            column=0,
                                                                                                            padx=20,
                                                                                                            pady=10)
        self.npc_list_frame = customtkinter.CTkScrollableFrame(self.sidebar_frame, label_text="NPC List")
        self.npc_list_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        self.npc_buttons = {}
        self.tabview = customtkinter.CTkTabview(self, corner_radius=10, command=self._on_tab_change)
        self.tabview.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.tabview.add("NPC Roster & Simulator")
        self.tabview.add("NPC Workshop")
        self.tabview.tab("NPC Roster & Simulator").grid_columnconfigure(0, weight=1)
        self.tabview.tab("NPC Roster & Simulator").grid_rowconfigure(0, weight=3)
        self.tabview.tab("NPC Roster & Simulator").grid_rowconfigure(1, weight=2)
        self.tabview.tab("NPC Workshop").grid_columnconfigure(0, weight=1)
        self.tabview.tab("NPC Workshop").grid_rowconfigure(0, weight=1)
        self._setup_roster_tab()
        self._setup_workshop_tab()

    def _setup_roster_tab(self):
        roster_tab = self.tabview.tab("NPC Roster & Simulator")

        main_roster_frame = customtkinter.CTkFrame(roster_tab, fg_color="transparent")
        main_roster_frame.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="nsew")
        main_roster_frame.grid_columnconfigure(0, weight=2)
        main_roster_frame.grid_columnconfigure(1, weight=1)
        main_roster_frame.grid_rowconfigure(0, weight=1)

        text_fields_frame = customtkinter.CTkFrame(main_roster_frame)
        text_fields_frame.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        text_fields_frame.grid_columnconfigure(1, weight=1)
        text_fields_frame.grid_rowconfigure(5, weight=2)

        customtkinter.CTkLabel(text_fields_frame, text="Name:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.roster_name_label = customtkinter.CTkLabel(text_fields_frame, text="", anchor="w")
        self.roster_name_label.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        customtkinter.CTkLabel(text_fields_frame, text="Race/Class:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.roster_race_class_label = customtkinter.CTkLabel(text_fields_frame, text="", anchor="w")
        self.roster_race_class_label.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        tags_frame = customtkinter.CTkFrame(text_fields_frame)
        tags_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        customtkinter.CTkLabel(tags_frame, text="Tags:", font=customtkinter.CTkFont(weight="bold")).pack(side="left",
                                                                                                         padx=(10, 5))
        self.roster_tags_label = customtkinter.CTkLabel(tags_frame, text="", anchor="w")
        self.roster_tags_label.pack(side="left", padx=5, fill="x", expand=True)
        customtkinter.CTkLabel(text_fields_frame, text="Appearance:").grid(row=3, column=0, padx=10, pady=5,
                                                                           sticky="nw")
        self.roster_appearance_textbox = customtkinter.CTkTextbox(text_fields_frame, state="disabled")
        self.roster_appearance_textbox.grid(row=3, column=1, padx=10, pady=5, sticky="nsew")
        customtkinter.CTkLabel(text_fields_frame, text="Personality:").grid(row=4, column=0, padx=10, pady=5,
                                                                            sticky="nw")
        self.roster_personality_textbox = customtkinter.CTkTextbox(text_fields_frame, state="disabled")
        self.roster_personality_textbox.grid(row=4, column=1, padx=10, pady=5, sticky="nsew")
        customtkinter.CTkLabel(text_fields_frame, text="Backstory:").grid(row=5, column=0, padx=10, pady=5, sticky="nw")
        self.roster_backstory_textbox = customtkinter.CTkTextbox(text_fields_frame, state="disabled")
        self.roster_backstory_textbox.grid(row=5, column=1, padx=10, pady=5, sticky="nsew")
        customtkinter.CTkLabel(text_fields_frame, text="Plot Hooks:").grid(row=6, column=0, padx=10, pady=5,
                                                                           sticky="nw")
        self.roster_plothooks_textbox = customtkinter.CTkTextbox(text_fields_frame, state="disabled")
        self.roster_plothooks_textbox.grid(row=6, column=1, padx=10, pady=5, sticky="nsew")

        portrait_frame = customtkinter.CTkFrame(main_roster_frame)
        portrait_frame.grid(row=0, column=1, padx=(10, 0), sticky="nsew")
        portrait_frame.grid_rowconfigure(0, weight=1)
        portrait_frame.grid_columnconfigure(0, weight=1)
        self.roster_portrait_label = customtkinter.CTkLabel(portrait_frame, text="No Portrait", width=300, height=300)
        self.roster_portrait_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        simulation_frame = customtkinter.CTkFrame(roster_tab)
        simulation_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        simulation_frame.grid_columnconfigure(0, weight=1)
        simulation_frame.grid_rowconfigure(2, weight=1)
        customtkinter.CTkLabel(simulation_frame, text="NPC Simulator",
                               font=customtkinter.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=2,
                                                                                        padx=10, pady=(10, 5),
                                                                                        sticky="w")
        self.prompt_entry = customtkinter.CTkEntry(simulation_frame,
                                                   placeholder_text="Enter a situation for the NPC...")
        self.prompt_entry.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.simulate_button = customtkinter.CTkButton(simulation_frame, text="Simulate",
                                                       command=self.start_simulation_thread)
        self.simulate_button.grid(row=1, column=1, padx=10, pady=5)
        self.response_textbox = customtkinter.CTkTextbox(simulation_frame, wrap="word")
        self.response_textbox.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.response_textbox.configure(state="disabled")

        bottom_button_frame = customtkinter.CTkFrame(roster_tab, fg_color="transparent")
        bottom_button_frame.grid(row=2, column=0, pady=(0, 10), sticky="s")
        customtkinter.CTkButton(bottom_button_frame, text="Edit this NPC", command=self.go_to_workshop_edit).pack(
            side="left", padx=10)
        customtkinter.CTkButton(bottom_button_frame, text="Delete this NPC", fg_color="#D32F2F", hover_color="#B71C1C",
                                command=self.delete_npc).pack(side="left", padx=10)

    def _setup_workshop_tab(self):
        workshop_tab = self.tabview.tab("NPC Workshop")
        workshop_tab.grid_columnconfigure(0, weight=1)
        workshop_tab.grid_rowconfigure(0, weight=1)

        main_workshop_frame = customtkinter.CTkScrollableFrame(workshop_tab, label_text="Create & Edit NPC")
        main_workshop_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        main_workshop_frame.grid_columnconfigure(0, weight=2)
        main_workshop_frame.grid_columnconfigure(1, weight=1)

        edit_text_frame = customtkinter.CTkFrame(main_workshop_frame)
        edit_text_frame.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        edit_text_frame.grid_columnconfigure(1, weight=1)

        customtkinter.CTkLabel(edit_text_frame, text="Name:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.workshop_name_entry = customtkinter.CTkEntry(edit_text_frame)
        self.workshop_name_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        customtkinter.CTkLabel(edit_text_frame, text="Race/Class:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.workshop_race_entry = customtkinter.CTkEntry(edit_text_frame)
        self.workshop_race_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        customtkinter.CTkLabel(edit_text_frame, text="Appearance:").grid(row=2, column=0, padx=10, pady=5, sticky="nw")
        self.workshop_appearance_textbox = customtkinter.CTkTextbox(edit_text_frame, height=100)
        self.workshop_appearance_textbox.grid(row=2, column=1, padx=10, pady=5, sticky="nsew")
        customtkinter.CTkLabel(edit_text_frame, text="Personality:").grid(row=3, column=0, padx=10, pady=5, sticky="nw")
        self.workshop_personality_textbox = customtkinter.CTkTextbox(edit_text_frame, height=100)
        self.workshop_personality_textbox.grid(row=3, column=1, padx=10, pady=5, sticky="nsew")
        customtkinter.CTkLabel(edit_text_frame, text="Backstory:").grid(row=4, column=0, padx=10, pady=5, sticky="nw")
        self.workshop_backstory_textbox = customtkinter.CTkTextbox(edit_text_frame, height=150)
        self.workshop_backstory_textbox.grid(row=4, column=1, padx=10, pady=5, sticky="nsew")
        customtkinter.CTkLabel(edit_text_frame, text="Plot Hooks:").grid(row=5, column=0, padx=10, pady=5, sticky="nw")
        self.workshop_plothooks_textbox = customtkinter.CTkTextbox(edit_text_frame, height=100)
        self.workshop_plothooks_textbox.grid(row=5, column=1, padx=10, pady=5, sticky="nsew")

        right_panel_frame = customtkinter.CTkFrame(main_workshop_frame)
        right_panel_frame.grid(row=0, column=1, sticky="nsew")
        right_panel_frame.grid_columnconfigure(0, weight=1)

        edit_portrait_frame = customtkinter.CTkFrame(right_panel_frame)
        edit_portrait_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        edit_portrait_frame.grid_columnconfigure(0, weight=1)
        self.workshop_portrait_label = customtkinter.CTkLabel(edit_portrait_frame, text="No Portrait", width=300,
                                                              height=300)
        self.workshop_portrait_label.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        workshop_portrait_buttons = customtkinter.CTkFrame(edit_portrait_frame, fg_color="transparent")
        workshop_portrait_buttons.grid(row=1, column=0, pady=10)
        customtkinter.CTkButton(workshop_portrait_buttons, text="Generate Portrait",
                                command=self.start_image_generation_thread).pack(side="left", padx=5)
        customtkinter.CTkButton(workshop_portrait_buttons, text="Upload Portrait", command=self.upload_portrait).pack(
            side="left", padx=5)

        self.workshop_status_textbox = customtkinter.CTkTextbox(edit_portrait_frame, height=100, wrap="word",
                                                                fg_color="transparent", state="disabled")
        self.workshop_status_textbox.grid(row=2, column=0, sticky="ew", padx=10, pady=10)

        tags_and_gen_frame = customtkinter.CTkFrame(right_panel_frame)
        tags_and_gen_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        tags_and_gen_frame.grid_columnconfigure(0, weight=1)

        customtkinter.CTkLabel(tags_and_gen_frame, text="Character Tags & AI Generator",
                               font=customtkinter.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=2,
                                                                                        padx=10, pady=10)

        self.gender_var = customtkinter.StringVar(value=GENDER_OPTIONS[1])
        self.attitude_var = customtkinter.StringVar(value=ATTITUDE_OPTIONS[1])
        self.rarity_var = customtkinter.StringVar(value=RARITY_OPTIONS[1])
        self.environment_var = customtkinter.StringVar(value=ENVIRONMENT_OPTIONS[1])
        self.race_var = customtkinter.StringVar(value=RACE_OPTIONS[1])
        self.class_var = customtkinter.StringVar(value=CLASS_OPTIONS[1])
        self.background_var = customtkinter.StringVar(value=BACKGROUND_OPTIONS[1])

        option_map = {"Gender": (self.gender_var, GENDER_OPTIONS), "Attitude": (self.attitude_var, ATTITUDE_OPTIONS),
                      "Rarity": (self.rarity_var, RARITY_OPTIONS),
                      "Environment": (self.environment_var, ENVIRONMENT_OPTIONS), "Race": (self.race_var, RACE_OPTIONS),
                      "Class": (self.class_var, CLASS_OPTIONS), "Background": (self.background_var, BACKGROUND_OPTIONS)}

        row_counter = 1
        for label, (var, values) in option_map.items():
            customtkinter.CTkLabel(tags_and_gen_frame, text=label).grid(row=row_counter, column=0, padx=10, pady=5,
                                                                        sticky="w")
            customtkinter.CTkOptionMenu(tags_and_gen_frame, variable=var, values=values).grid(row=row_counter, column=1,
                                                                                              padx=10, pady=5,
                                                                                              sticky="ew")
            row_counter += 1

        self.generate_button = customtkinter.CTkButton(tags_and_gen_frame, text="Generate with AI", height=40,
                                                       command=self.start_generation_thread)
        self.generate_button.grid(row=row_counter, column=0, columnspan=2, padx=10, pady=20, sticky="ew")

        customtkinter.CTkButton(workshop_tab, text="Save NPC in Workshop", height=40,
                                command=self.save_workshop_npc).grid(row=1, column=0, padx=10, pady=(0, 10), sticky="s")

    def update_npc_list(self):
        for widget in self.npc_list_frame.winfo_children(): widget.destroy()
        sorted_npc_names = sorted(self.npcs.keys())
        self.npc_buttons = {}
        for name in sorted_npc_names:
            button = customtkinter.CTkButton(self.npc_list_frame, text=name, command=lambda n=name: self.select_npc(n))
            button.pack(pady=5, padx=5, fill="x")
            self.npc_buttons[name] = button
        self.highlight_selected_npc()

    def highlight_selected_npc(self):
        for name, button in self.npc_buttons.items():
            button.configure(fg_color=customtkinter.ThemeManager.theme["CTkButton"][
                "hover_color"] if name == self.selected_npc_name else customtkinter.ThemeManager.theme["CTkButton"][
                "fg_color"])

    def _set_roster_text(self, widget, text):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", text)
        widget.configure(state="disabled")

    def populate_roster_fields(self, npc_data):
        self.roster_name_label.configure(text=npc_data.get("name", ""))
        self.roster_race_class_label.configure(text=npc_data.get("race_class", ""))
        tags = [npc_data.get('gender', ''), npc_data.get('attitude', ''), npc_data.get('rarity', ''),
                npc_data.get('environment', ''), npc_data.get('race', ''), npc_data.get('character_class', ''),
                npc_data.get('background', '')]
        self.roster_tags_label.configure(text=" | ".join(filter(None, tags)))
        self._set_roster_text(self.roster_appearance_textbox, npc_data.get("appearance", ""))
        self._set_roster_text(self.roster_personality_textbox, npc_data.get("personality", ""))
        self._set_roster_text(self.roster_backstory_textbox, npc_data.get("backstory", ""))
        self._set_roster_text(self.roster_plothooks_textbox, npc_data.get("plot_hooks", ""))

        image_bytes = npc_data.get("image_data")
        if image_bytes:
            try:
                pil_image = Image.open(io.BytesIO(image_bytes))
                self.roster_ctk_image = customtkinter.CTkImage(light_image=pil_image, dark_image=pil_image,
                                                               size=(300, 300))
                self.roster_portrait_label.configure(image=self.roster_ctk_image, text="")
            except:
                self.roster_portrait_label.configure(image=None, text="Invalid Image")
        else:
            self.roster_portrait_label.configure(image=None, text="No Portrait")

    def populate_workshop_fields(self, npc_data):
        self._npc_in_workshop = npc_data.copy()
        self.workshop_name_entry.delete(0, "end")
        self.workshop_name_entry.insert(0, self._npc_in_workshop.get("name", ""))
        self.workshop_race_entry.delete(0, "end")
        self.workshop_race_entry.insert(0, self._npc_in_workshop.get("race_class", ""))
        self.workshop_appearance_textbox.delete("1.0", "end")
        self.workshop_appearance_textbox.insert("1.0", self._npc_in_workshop.get("appearance", ""))
        self.workshop_personality_textbox.delete("1.0", "end")
        self.workshop_personality_textbox.insert("1.0", self._npc_in_workshop.get("personality", ""))
        self.workshop_backstory_textbox.delete("1.0", "end")
        self.workshop_backstory_textbox.insert("1.0", self._npc_in_workshop.get("backstory", ""))
        self.workshop_plothooks_textbox.delete("1.0", "end")
        self.workshop_plothooks_textbox.insert("1.0", self._npc_in_workshop.get("plot_hooks", ""))

        self.gender_var.set(self._npc_in_workshop.get('gender') or GENDER_OPTIONS[0])
        self.attitude_var.set(self._npc_in_workshop.get('attitude') or ATTITUDE_OPTIONS[0])
        self.rarity_var.set(self._npc_in_workshop.get('rarity') or RARITY_OPTIONS[0])
        self.environment_var.set(self._npc_in_workshop.get('environment') or ENVIRONMENT_OPTIONS[0])
        self.race_var.set(self._npc_in_workshop.get('race') or RACE_OPTIONS[0])
        self.class_var.set(self._npc_in_workshop.get('character_class') or CLASS_OPTIONS[0])
        self.background_var.set(self._npc_in_workshop.get('background') or BACKGROUND_OPTIONS[0])

        self._update_workshop_image_display()

    def _update_workshop_image_display(self):
        image_bytes = self._npc_in_workshop.get("image_data")
        if image_bytes:
            try:
                pil_image = Image.open(io.BytesIO(image_bytes))
                self.workshop_ctk_image = customtkinter.CTkImage(light_image=pil_image, dark_image=pil_image,
                                                                 size=(300, 300))
                self.workshop_portrait_label.configure(image=self.workshop_ctk_image, text="")
            except:
                self.workshop_portrait_label.configure(image=None, text="Invalid Image")
        else:
            self.workshop_portrait_label.configure(image=None, text="No Portrait")

    def select_npc(self, name):
        if name in self.npcs:
            self.selected_npc_name = name
            npc_data = self.npcs.get(name, {})
            self.populate_roster_fields(npc_data)
            self.highlight_selected_npc()
            self.tabview.set("NPC Roster & Simulator")
        else:
            logging.warning(f"Attempted to select non-existent NPC: {name}")

    def select_first_npc(self):
        if self.npcs:
            self.select_npc(sorted(self.npcs.keys())[0])
        else:
            self.go_to_workshop_new()

    def go_to_workshop_new(self):
        self.populate_workshop_fields({})
        self.tabview.set("NPC Workshop")

    def go_to_workshop_edit(self):
        if self.selected_npc_name and self.selected_npc_name in self.npcs:
            self.populate_workshop_fields(self.npcs[self.selected_npc_name])
            self.tabview.set("NPC Workshop")
        else:
            logging.warning("Edit button clicked with no NPC selected.")

    def save_workshop_npc(self):
        original_name = self._npc_in_workshop.get('name')
        new_name = self.workshop_name_entry.get().strip()
        if not new_name:
            logging.warning("Save attempt with empty NPC name.")
            return

        self._npc_in_workshop['name'] = new_name
        self._npc_in_workshop['race_class'] = self.workshop_race_entry.get()
        self._npc_in_workshop['appearance'] = self.workshop_appearance_textbox.get("1.0", "end-1c")
        self._npc_in_workshop['personality'] = self.workshop_personality_textbox.get("1.0", "end-1c")
        self._npc_in_workshop['backstory'] = self.workshop_backstory_textbox.get("1.0", "end-1c")
        self._npc_in_workshop['plot_hooks'] = self.workshop_plothooks_textbox.get("1.0", "end-1c")
        self._npc_in_workshop['gender'] = self.gender_var.get()
        self._npc_in_workshop['attitude'] = self.attitude_var.get()
        self._npc_in_workshop['rarity'] = self.rarity_var.get()
        self._npc_in_workshop['environment'] = self.environment_var.get()
        self._npc_in_workshop['race'] = self.race_var.get()
        self._npc_in_workshop['character_class'] = self.class_var.get()
        self._npc_in_workshop['background'] = self.background_var.get()

        all_db_keys = ["name", "race_class", "appearance", "personality", "backstory", "plot_hooks", "attitude",
                       "rarity", "race", "character_class", "environment", "background", "gender", "image_data"]
        for key in all_db_keys:
            if key not in self._npc_in_workshop:
                self._npc_in_workshop[key] = None

        self.db.save_npc(self._npc_in_workshop, old_name=original_name)

        self.npcs = self.db.load_data()
        self.update_npc_list()
        self.select_npc(new_name)

    def delete_npc(self):
        if self.selected_npc_name:
            self.db.delete_npc(self.selected_npc_name)
            self.npcs = self.db.load_data()
            self.selected_npc_name = None
            self.populate_roster_fields({})
            self.update_npc_list()
            self.select_first_npc()

    def upload_portrait(self):
        try:
            file_path = filedialog.askopenfilename(title="Select a Portrait",
                                                   filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.gif")])
            if file_path:
                with open(file_path, 'rb') as f:
                    image_bytes = f.read()
                self._npc_in_workshop['image_data'] = image_bytes
                self._update_workshop_image_display()
                logging.info(f"Image loaded from {file_path}")
        except Exception as e:
            logging.error(f"Failed to upload image: {e}")
            self._set_workshop_status_text("Image Upload Failed")

    def start_generation_thread(self):
        if not self.ai.is_api_key_valid():
            self._set_workshop_status_text("Error: Please set your API_KEY.")
            return
        threading.Thread(target=self._run_generation_task, daemon=True).start()

    def start_image_generation_thread(self):
        if not self.ai.is_api_key_valid():
            self._set_workshop_status_text("API Key Missing")
            return
        appearance_prompt = self.workshop_appearance_textbox.get("1.0", "end-1c").strip()
        if not appearance_prompt:
            self._set_workshop_status_text("Appearance is empty")
            return

        self.workshop_portrait_label.configure(image=None, text="")
        self._set_workshop_status_text("Preparing to generate...")
        threading.Thread(target=self._image_generation_worker, args=(appearance_prompt,), daemon=True).start()

    def start_simulation_thread(self):
        if not self.ai.is_api_key_valid():
            self.update_response_box("Error: Please set your API_KEY.")
            return
        if not self.selected_npc_name:
            self.update_response_box("Error: Please select an NPC to simulate.")
            return
        threading.Thread(target=self._run_simulation_task, daemon=True).start()

    def _run_generation_task(self):
        self._set_workshop_status_text("Generating a new NPC with Gemini...")
        self.generate_button.configure(state="disabled")
        try:
            params = {'gender': self.gender_var.get(), 'attitude': self.attitude_var.get(),
                      'rarity': self.rarity_var.get(), 'environment': self.environment_var.get(),
                      'race': self.race_var.get(), 'character_class': self.class_var.get(),
                      'background': self.background_var.get()}
            npc_data, raw_response = self.ai.generate_npc(params)
            self.populate_workshop_fields(npc_data)
        except Exception as e:
            logging.error(f"Generation failed: {e}")
            self._set_workshop_status_text(f"An error occurred during generation:\n\n{str(e)}")
        finally:
            self.generate_button.configure(state="normal")

    def _run_simulation_task(self):
        self.update_response_box("Simulating... Please wait.")
        self.simulate_button.configure(state="disabled")
        try:
            npc_data = self.npcs.get(self.selected_npc_name)
            situation = self.prompt_entry.get()
            response_text = self.ai.simulate_reaction(npc_data, situation)
            self.update_response_box(response_text)
        except Exception as e:
            logging.error(f"Simulation failed: {e}")
            self.update_response_box(f"An error occurred:\n\n{str(e)}")
        finally:
            self.simulate_button.configure(state="normal")

    def _image_generation_worker(self, appearance_prompt):
        try:
            image_bytes = self.ai.generate_npc_portrait(appearance_prompt)
            self._npc_in_workshop['image_data'] = image_bytes
            self.after(0, self._update_workshop_image_display)
        except NotImplementedError as e:
            logging.warning(f"Image generation skipped: {e}")
            prompt_text = f"A digital painting portrait of a D&D character: {appearance_prompt}. Fantasy art, character concept, detailed, high quality."
            message = f"Feature requires a billed account.\n\nTo generate manually, use a prompt like this in Gemini or another AI:\n\n'{prompt_text}'"
            self.after(0, lambda: self._set_workshop_status_text(message))
        except Exception as e:
            logging.error(f"Image generation failed in worker: {e}")
            self.after(0, lambda: self._set_workshop_status_text("Generation Failed"))

    def _on_tab_change(self):
        """Event handler for when the user switches tabs."""
        selected_tab = self.tabview.get()
        if selected_tab == "NPC Roster & Simulator" and self.selected_npc_name:
            self.populate_roster_fields(self.npcs.get(self.selected_npc_name, {}))

    def update_response_box(self, text):
        self.response_textbox.configure(state="normal")
        self.response_textbox.delete("1.0", "end")
        self.response_textbox.insert("1.0", text)
        self.response_textbox.configure(state="disabled")

    def _set_workshop_status_text(self, text):
        self.workshop_status_textbox.configure(state="normal")
        self.workshop_status_textbox.delete("1.0", "end")
        self.workshop_status_textbox.insert("1.0", text)
        self.workshop_status_textbox.configure(state="disabled")


# ======================================================================================
# --- SECTION 4: MAIN MENU APPLICATION (Would be in 'main_menu.py' or 'main.py') ---
# ======================================================================================
class MainMenuApp(customtkinter.CTk):
    def __init__(self, data_manager, api_service):
        super().__init__()
        self.db = data_manager
        self.ai = api_service

        self.title("DM's AI Toolkit")
        self.minsize(400, 300)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        main_frame = customtkinter.CTkFrame(self)
        main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)

        title_label = customtkinter.CTkLabel(main_frame, text="DM's AI Toolkit",
                                             font=customtkinter.CTkFont(size=24, weight="bold"))
        title_label.grid(row=0, column=0, padx=20, pady=20)

        npc_button = customtkinter.CTkButton(main_frame, text="Launch NPC Manager", height=50,
                                             command=self.launch_npc_app)
        npc_button.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.after(100, lambda: self.state('zoomed'))

    def launch_npc_app(self):
        self.destroy()
        npc_app = NpcApp(self.db, self.ai)
        npc_app.mainloop()


# ======================================================================================
# --- SECTION 5: APPLICATION ENTRY POINT (Would be in 'main.py') ---
# ======================================================================================
if __name__ == "__main__":
    data_manager = DataManager(db_filepath=DB_FILE)
    gemini_service = GeminiService(api_key=API_KEY, text_model_name=TEXT_MODEL_NAME, image_model_name=IMAGE_MODEL_NAME)
    main_menu = MainMenuApp(data_manager=data_manager, api_service=gemini_service)
    main_menu.mainloop()