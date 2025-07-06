import sqlite3
import logging
from google import genai
from google.genai import types
from google.api_core import exceptions as google_exceptions
import json
import re


# No more prompt imports needed! The service is fully dynamic.

class DataManager:
    """
    Manages all database operations for the DM's AI Toolkit.
    This version implements the new "World-centric" architecture with a translation layer
    and includes a non-destructive migration system for future schema updates.
    """

    def __init__(self, db_filepath):
        """
        Initializes the DataManager and ensures the database schema is up to date.
        """
        self.db_filepath = db_filepath
        self._initialize_database()
        self._run_migrations()

    def _get_connection(self):
        """Establishes and returns a connection to the SQLite database."""
        conn = sqlite3.connect(self.db_filepath)
        conn.execute("PRAGMA foreign_keys = 1")  # Enforce foreign key constraints
        return conn

    def _initialize_database(self):
        """
        Creates all necessary tables and views for the application architecture if they don't exist.
        This method ensures the base schema is present for new or existing databases.
        """
        # Tier 1: Core & Campaign Tables
        create_worlds_table = """
                              CREATE TABLE IF NOT EXISTS worlds \
                              ( \
                                  world_id \
                                  INTEGER \
                                  PRIMARY \
                                  KEY \
                                  AUTOINCREMENT, \
                                  canonical_name \
                                  TEXT \
                                  UNIQUE \
                                  NOT \
                                  NULL
                              ); \
                              """
        create_world_translations_table = """
                                          CREATE TABLE IF NOT EXISTS world_translations \
                                          ( \
                                              translation_id \
                                              INTEGER \
                                              PRIMARY \
                                              KEY \
                                              AUTOINCREMENT, \
                                              world_id \
                                              INTEGER \
                                              NOT \
                                              NULL, \
                                              language \
                                              TEXT \
                                              NOT \
                                              NULL, \
                                              world_name \
                                              TEXT \
                                              NOT \
                                              NULL, \
                                              world_lore \
                                              TEXT, \
                                              FOREIGN \
                                              KEY \
                                          ( \
                                              world_id \
                                          ) REFERENCES worlds \
                                          ( \
                                              world_id \
                                          ) ON DELETE CASCADE,
                                              UNIQUE \
                                          ( \
                                              world_id, \
                                              language \
                                          )
                                              ); \
                                          """
        create_campaigns_table = """
                                 CREATE TABLE IF NOT EXISTS campaigns \
                                 ( \
                                     campaign_id \
                                     INTEGER \
                                     PRIMARY \
                                     KEY \
                                     AUTOINCREMENT, \
                                     world_id \
                                     INTEGER \
                                     NOT \
                                     NULL, \
                                     campaign_name \
                                     TEXT \
                                     NOT \
                                     NULL, \
                                     language \
                                     TEXT \
                                     NOT \
                                     NULL, \
                                     party_info \
                                     TEXT, \
                                     session_history \
                                     TEXT, \
                                     FOREIGN \
                                     KEY \
                                 ( \
                                     world_id \
                                 ) REFERENCES worlds \
                                 ( \
                                     world_id \
                                 ) ON DELETE CASCADE
                                     ); \
                                 """

        # Tier 2: Entity Tables (Core + Translation)
        create_characters_table = """
                                  CREATE TABLE IF NOT EXISTS characters \
                                  ( \
                                      character_id \
                                      INTEGER \
                                      PRIMARY \
                                      KEY \
                                      AUTOINCREMENT, \
                                      world_id \
                                      INTEGER \
                                      NOT \
                                      NULL, \
                                      is_player \
                                      BOOLEAN \
                                      NOT \
                                      NULL, \
                                      level \
                                      INTEGER, \
                                      hp \
                                      INTEGER, \
                                      ac \
                                      INTEGER, \
                                      strength \
                                      INTEGER, \
                                      dexterity \
                                      INTEGER, \
                                      constitution \
                                      INTEGER, \
                                      intelligence \
                                      INTEGER, \
                                      wisdom \
                                      INTEGER, \
                                      charisma \
                                      INTEGER, \
                                      skills \
                                      TEXT, \
                                      image_data \
                                      BLOB, \
                                      FOREIGN \
                                      KEY \
                                  ( \
                                      world_id \
                                  ) REFERENCES worlds \
                                  ( \
                                      world_id \
                                  ) ON DELETE CASCADE
                                      ); \
                                  """
        create_character_translations_table = """
                                              CREATE TABLE IF NOT EXISTS character_translations \
                                              ( \
                                                  translation_id \
                                                  INTEGER \
                                                  PRIMARY \
                                                  KEY \
                                                  AUTOINCREMENT, \
                                                  character_id \
                                                  INTEGER \
                                                  NOT \
                                                  NULL, \
                                                  language \
                                                  TEXT \
                                                  NOT \
                                                  NULL, \
                                                  name \
                                                  TEXT, \
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
                                                  roleplaying_tips \
                                                  TEXT, \
                                                  motivation \
                                                  TEXT, \
                                                  objectives \
                                                  TEXT, \
                                                  dm_notes \
                                                  TEXT, \
                                                  FOREIGN \
                                                  KEY \
                                              ( \
                                                  character_id \
                                              ) REFERENCES characters \
                                              ( \
                                                  character_id \
                                              ) ON DELETE CASCADE,
                                                  UNIQUE \
                                              ( \
                                                  character_id, \
                                                  language \
                                              )
                                                  ); \
                                              """

        # --- VIEWS ---
        create_world_view = """
                            CREATE VIEW IF NOT EXISTS v_full_world_data AS
                            SELECT w.world_id, \
                                   w.canonical_name, \
                                   wt.language, \
                                   wt.world_name, \
                                   wt.world_lore
                            FROM worlds w
                                     LEFT JOIN world_translations wt ON w.world_id = wt.world_id; \
                            """
        create_character_view = """
                                CREATE VIEW IF NOT EXISTS v_full_character_data AS
                                SELECT c.character_id, \
                                       c.world_id, \
                                       c.is_player, \
                                       c.level, \
                                       c.hp, \
                                       c.ac, \
                                       c.strength, \
                                       c.dexterity, \
                                       c.constitution, \
                                       c.intelligence, \
                                       c.wisdom, \
                                       c.charisma, \
                                       c.skills, \
                                       c.image_data, \
                                       ct.language, \
                                       ct.name, \
                                       ct.race_class, \
                                       ct.appearance, \
                                       ct.personality, \
                                       ct.backstory, \
                                       ct.plot_hooks, \
                                       ct.roleplaying_tips, \
                                       ct.motivation, \
                                       ct.objectives, \
                                       ct.dm_notes
                                FROM characters c
                                         LEFT JOIN character_translations ct ON c.character_id = ct.character_id; \
                                """

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                logging.info("Ensuring base tables and views exist...")
                cursor.execute(create_worlds_table)
                cursor.execute(create_world_translations_table)
                cursor.execute(create_campaigns_table)
                cursor.execute(create_characters_table)
                cursor.execute(create_character_translations_table)
                cursor.execute(create_world_view)
                cursor.execute(create_character_view)
                conn.commit()
            logging.info("Base schema check complete.")
        except sqlite3.Error as e:
            logging.error(f"Database error during schema creation: {e}")
            raise

    def _run_migrations(self):
        """
        Runs database migrations to update the schema non-destructively.
        This allows for adding new columns or tables in the future without losing data.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute("CREATE TABLE IF NOT EXISTS db_meta (key TEXT PRIMARY KEY, value INTEGER)")
                cursor.execute("INSERT OR IGNORE INTO db_meta (key, value) VALUES ('schema_version', 1)")
                conn.commit()

                cursor.execute("SELECT value FROM db_meta WHERE key = 'schema_version'")
                current_version = cursor.fetchone()[0]
                logging.info(f"Current database schema version: {current_version}")

                if current_version < 2:
                    logging.info("Migrating database to version 2...")
                    # This migration is for the change to a world translation table.
                    # On a fresh DB, this will just update the version number.
                    # On an old DB from before this change, it would require complex data moving.
                    # We are assuming a fresh DB after this major refactor.
                    cursor.execute("UPDATE db_meta SET value = 2 WHERE key = 'schema_version'")
                    logging.info("Migration to version 2 complete.")
                    current_version = 2

                conn.commit()

        except sqlite3.Error as e:
            logging.error(f"An error occurred during database migration: {e}")
            raise

    def _add_column_if_not_exists(self, cursor, table_name, column_name, column_type):
        """Helper function to safely add a column to a table if it doesn't already exist."""
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        if column_name not in columns:
            logging.info(f"Adding column '{column_name}' to table '{table_name}'...")
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
        else:
            logging.info(f"Column '{column_name}' already exists in table '{table_name}'.")

    # --- World Management ---

    def create_world(self, name, language, lore=""):
        """Creates a new world and its first translation in a single transaction."""
        canonical_name = f"{name.lower().replace(' ', '_')}_{sqlite3.Timestamp.now().timestamp()}"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO worlds (canonical_name) VALUES (?)", (canonical_name,))
                world_id = cursor.lastrowid

                trans_sql = "INSERT INTO world_translations (world_id, language, world_name, world_lore) VALUES (?, ?, ?, ?)"
                cursor.execute(trans_sql, (world_id, language, name, lore))

                conn.commit()
                logging.info(f"Successfully created world '{name}' (ID: {world_id}) with '{language}' translation.")
                return world_id
        except sqlite3.Error as e:
            logging.error(f"Database error while creating world '{name}': {e}")
            raise

    def get_all_worlds(self, language):
        """Retrieves all worlds for a specific language using the view."""
        worlds_list = []
        sql = "SELECT * FROM v_full_world_data WHERE language = ? ORDER BY world_name"
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(sql, (language,))
                rows = cursor.fetchall()
                for row in rows:
                    worlds_list.append(dict(row))
            logging.info(f"Successfully loaded {len(worlds_list)} worlds for language '{language}'.")
            return worlds_list
        except sqlite3.Error as e:
            logging.error(f"Failed to load worlds from database: {e}")
            return []

    def get_world_translation(self, world_id, language):
        """Gets a specific translation for a given world using the view."""
        sql = "SELECT * FROM v_full_world_data WHERE world_id = ? AND language = ?"
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(sql, (world_id, language))
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as e:
            logging.error(f"Failed to get translation for world {world_id} in '{language}': {e}")
            return None

    def update_world_translation(self, world_id, language, name, lore):
        """Updates or creates a specific translation for a world."""
        sql = """
            INSERT OR REPLACE INTO world_translations (world_id, language, world_name, world_lore)
            VALUES (?, ?, ?, ?)
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (world_id, language, name, lore))
                conn.commit()
            logging.info(f"Successfully updated translation for world ID {world_id} in '{language}'.")
        except sqlite3.Error as e:
            logging.error(f"Failed to update world translation for world ID {world_id}: {e}")
            raise

    def delete_world(self, world_id):
        """Deletes a world and all its associated data (translations, campaigns, characters) via CASCADE."""
        sql = "DELETE FROM worlds WHERE world_id = ?"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (world_id,))
                conn.commit()
            logging.info(f"Successfully deleted world ID: {world_id}")
        except sqlite3.Error as e:
            logging.error(f"Failed to delete world ID {world_id}: {e}")
            raise

    # --- Campaign Management ---

    def create_campaign(self, world_id, name, language, party_info="", session_history=""):
        """Creates a new campaign linked to a specific world."""
        sql = """
              INSERT INTO campaigns (world_id, campaign_name, language, party_info, session_history)
              VALUES (?, ?, ?, ?, ?) \
              """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (world_id, name, language, party_info, session_history))
                conn.commit()
                logging.info(f"Successfully created campaign '{name}' in world ID {world_id}.")
                return cursor.lastrowid
        except sqlite3.Error as e:
            logging.error(f"Database error while creating campaign '{name}': {e}")
            raise

    def get_campaigns_for_world(self, world_id):
        """Retrieves all campaigns for a specific world ID."""
        campaigns_list = []
        sql = "SELECT * FROM campaigns WHERE world_id = ? ORDER BY campaign_name"
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(sql, (world_id,))
                rows = cursor.fetchall()
                for row in rows:
                    campaigns_list.append(dict(row))
            logging.info(f"Loaded {len(campaigns_list)} campaigns for world ID {world_id}.")
            return campaigns_list
        except sqlite3.Error as e:
            logging.error(f"Failed to load campaigns for world ID {world_id}: {e}")
            return []

    def update_campaign(self, campaign_id, name, language, party_info, session_history):
        """Updates an existing campaign's details."""
        sql = """
              UPDATE campaigns \
              SET campaign_name   = ?, \
                  language        = ?, \
                  party_info      = ?, \
                  session_history = ?
              WHERE campaign_id = ? \
              """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (name, language, party_info, session_history, campaign_id))
                conn.commit()
            logging.info(f"Successfully updated campaign ID: {campaign_id}")
        except sqlite3.Error as e:
            logging.error(f"Failed to update campaign ID {campaign_id}: {e}")
            raise

    def delete_campaign(self, campaign_id):
        """Deletes a campaign."""
        sql = "DELETE FROM campaigns WHERE campaign_id = ?"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (campaign_id,))
                conn.commit()
            logging.info(f"Successfully deleted campaign ID: {campaign_id}")
        except sqlite3.Error as e:
            logging.error(f"Failed to delete campaign ID {campaign_id}: {e}")
            raise

    # --- Character Management ---

    def create_character(self, world_id, is_player, language, core_data, translation_data):
        """
        Creates a new character by adding a core entry and a translation entry in a single transaction.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                core_sql = """
                           INSERT INTO characters (world_id, is_player, level, hp, ac, strength, dexterity,
                                                   constitution, intelligence, wisdom, charisma, skills, image_data)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) \
                           """
                core_values = (world_id, is_player, core_data.get('level'), core_data.get('hp'), core_data.get('ac'),
                               core_data.get('strength'), core_data.get('dexterity'), core_data.get('constitution'),
                               core_data.get('intelligence'), core_data.get('wisdom'), core_data.get('charisma'),
                               core_data.get('skills'), core_data.get('image_data'))
                cursor.execute(core_sql, core_values)
                character_id = cursor.lastrowid

                trans_sql = """
                            INSERT INTO character_translations (character_id, language, name, race_class, appearance,
                                                                personality, backstory, plot_hooks, roleplaying_tips,
                                                                motivation, objectives, dm_notes)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) \
                            """
                trans_values = (character_id, language, translation_data.get('name'),
                                translation_data.get('race_class'),
                                translation_data.get('appearance'), translation_data.get('personality'),
                                translation_data.get('backstory'), translation_data.get('plot_hooks'),
                                translation_data.get('roleplaying_tips'), translation_data.get('motivation'),
                                translation_data.get('objectives'), translation_data.get('dm_notes'))
                cursor.execute(trans_sql, trans_values)

                conn.commit()
                logging.info(f"Successfully created character ID {character_id} with '{language}' translation.")
                return character_id
        except sqlite3.Error as e:
            logging.error(f"Database error while creating character: {e}")
            raise

    def get_characters_for_world(self, world_id, language):
        """
        Retrieves all characters for a specific world, in a specific language.
        """
        char_list = []
        sql = "SELECT * FROM v_full_character_data WHERE world_id = ? AND language = ? ORDER BY name"
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(sql, (world_id, language))
                rows = cursor.fetchall()
                for row in rows:
                    char_list.append(dict(row))
            logging.info(f"Loaded {len(char_list)} characters for world ID {world_id} in '{language}'.")
            return char_list
        except sqlite3.Error as e:
            logging.error(f"Failed to load characters for world ID {world_id}: {e}")
            return []

    def update_character(self, character_id, language, core_data, translation_data):
        """
        Updates a character's core data and a specific language translation in a single transaction.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                core_sql = """
                           UPDATE characters \
                           SET level=?, \
                               hp=?, \
                               ac=?, \
                               strength=?, \
                               dexterity=?, \
                               constitution=?, \
                               intelligence=?, \
                               wisdom=?, \
                               charisma=?, \
                               skills=?, \
                               image_data=?
                           WHERE character_id = ? \
                           """
                core_values = (core_data.get('level'), core_data.get('hp'), core_data.get('ac'),
                               core_data.get('strength'), core_data.get('dexterity'), core_data.get('constitution'),
                               core_data.get('intelligence'), core_data.get('wisdom'), core_data.get('charisma'),
                               core_data.get('skills'), core_data.get('image_data'), character_id)
                cursor.execute(core_sql, core_values)

                trans_sql = """
                    INSERT OR REPLACE INTO character_translations (character_id, language, name, race_class, appearance,
                                                                 personality, backstory, plot_hooks, roleplaying_tips,
                                                                 motivation, objectives, dm_notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                trans_values = (character_id, language, translation_data.get('name'),
                                translation_data.get('race_class'),
                                translation_data.get('appearance'), translation_data.get('personality'),
                                translation_data.get('backstory'), translation_data.get('plot_hooks'),
                                translation_data.get('roleplaying_tips'), translation_data.get('motivation'),
                                translation_data.get('objectives'), translation_data.get('dm_notes'))
                cursor.execute(trans_sql, trans_values)

                conn.commit()
                logging.info(f"Successfully updated character ID {character_id} for language '{language}'.")
        except sqlite3.Error as e:
            logging.error(f"Database error while updating character {character_id}: {e}")
            raise

    def delete_character(self, character_id):
        """Deletes a character and all its translations via CASCADE."""
        sql = "DELETE FROM characters WHERE character_id = ?"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (character_id,))
                conn.commit()
            logging.info(f"Successfully deleted character ID: {character_id}")
        except sqlite3.Error as e:
            logging.error(f"Failed to delete character ID {character_id}: {e}")
            raise


class GeminiService:
    def __init__(self, api_key, app_settings):
        self.api_key = api_key
        self.settings = app_settings
        self.text_model_name = self.settings.get("text_model")
        self.image_model_name = self.settings.get("image_model")
        self.client = None
        self._configure_api()

    def _configure_api(self):
        if self._is_api_key_format_valid():
            try:
                self.client = genai.Client(api_key=self.api_key)
                logging.info("Gemini API Client configured.")
            except Exception as e:
                logging.error(f"Failed to instantiate Gemini API client: {e}")
                self.client = None

    def _is_api_key_format_valid(self):
        is_valid = self.api_key and "INSERT" not in self.api_key and len(self.api_key) > 10
        if not is_valid: logging.warning("API Key is missing or appears to be a placeholder.")
        return is_valid

    def is_api_key_valid(self):
        return self.client is not None

    def translate_text(self, text, target_language_code, target_language_name):
        """Translates a given text to a target language using the Gemini API."""
        if not self.is_api_key_valid():
            raise ValueError("API Client not configured. Check your API key.")
        if not text:
            return ""

        translation_prompt_template = self.settings.get("prompts", {}).get("translation")

        prompt = translation_prompt_template.format(
            target_language_name=target_language_name,
            target_language_code=target_language_code,
            text_to_translate=text
        )
        logging.info(
            f"Sending translation request to model '{self.text_model_name}' for language '{target_language_code}'.")
        try:
            response = self.client.models.generate_content(model=self.text_model_name, contents=prompt)
            return response.text.strip()
        except Exception as e:
            logging.error(f"An unexpected error occurred during translation: {e}")
            raise

    def generate_npc(self, params, campaign_data=None, include_party=True, include_session=True):
        """Generates an NPC using the Gemini API based on given parameters and full campaign context."""
        if not self.is_api_key_valid(): raise ValueError("API Client not configured. Check your API key.")
        campaign_data = campaign_data or {}

        npc_generation_prompt_template = self.settings.get("prompts", {}).get("npc_generation")

        lore_context = campaign_data.get('campaign_lore', '')
        party_context = campaign_data.get('party_info', '') if include_party else ""
        session_context = campaign_data.get('session_history', '') if include_session else ""
        custom_prompt_text = params.get('custom_prompt', '')

        campaign_context_section = f"\n**Campaign Lore (Follow this lore closely):**\n{lore_context}\n" if lore_context else ""
        party_context_section = f"\n**Player Party Information (Consider their impact):**\n{party_context}\n" if party_context else ""
        session_context_section = f"\n**Recent Session History (The NPC may be aware of these events):**\n{session_context}\n" if session_context else ""
        custom_prompt_section = f"\n**Additional Custom Prompt:**\n- {custom_prompt_text}\n" if custom_prompt_text else ""

        prompt = npc_generation_prompt_template.format(
            gender=params['gender'], attitude=params['attitude'], rarity=params['rarity'],
            environment=params['environment'], race=params['race'], character_class=params['character_class'],
            background=params['background'],
            campaign_context=campaign_context_section,
            party_context=party_context_section,
            session_context=session_context_section,
            custom_prompt_section=custom_prompt_section
        )

        logging.info(f"Sending generation request to model '{self.text_model_name}'.")
        response = self.client.models.generate_content(model=self.text_model_name, contents=prompt)
        raw_text = response.text
        logging.info(f"Received raw response from Gemini:\n{raw_text}")
        try:
            match = re.search(r"```json\s*([\s\S]+?)\s*```", raw_text)
            if match:
                json_str = match.group(1)
            else:
                start_index = raw_text.find('{')
                end_index = raw_text.rfind('}') + 1
                if start_index != -1 and end_index != 0:
                    json_str = raw_text[start_index:end_index]
                else:
                    raise ValueError("No JSON object found in the response.")
            parsed_json = json.loads(json_str)
            return parsed_json, raw_text
        except (json.JSONDecodeError, ValueError) as e:
            logging.error(f"Failed to parse JSON from AI response. Raw text: {raw_text}\nError: {e}")
            raise ValueError(
                f"The AI returned a malformed description. Please try generating again. Details: {e}") from e

    def simulate_reaction(self, npc_data, situation, campaign_data=None, sim_type="Short"):
        """Simulates an NPC's reaction to a given situation using prompts from settings."""
        if not self.is_api_key_valid(): raise ValueError("API Client not configured. Check your API key.")
        campaign_data = campaign_data or {}

        prompts = self.settings.get("prompts", {})
        if sim_type == "Short":
            prompt_template = prompts.get("npc_simulation_short")
        else:
            prompt_template = prompts.get("npc_simulation_long")

        if not prompt_template:
            raise ValueError(f"Simulation prompt for type '{sim_type}' not found in settings.")

        full_context = (f"Appearance: {npc_data.get('appearance', 'N/A')}\n"
                        f"Personality: {npc_data.get('personality', 'N/A')}\n"
                        f"Backstory: {npc_data.get('backstory', 'N/A')}\n"
                        f"Roleplaying Tips: {npc_data.get('roleplaying_tips', 'N/A')}")

        world_lore = ""
        if campaign_data:
            world_id = campaign_data.get('world_id')
            lang = campaign_data.get('language')
            if world_id and lang:
                world_trans = self.get_world_translation(world_id, lang)
                if world_trans:
                    world_lore = world_trans.get('world_lore', '')

        party_context = campaign_data.get('party_info', '')
        session_context = campaign_data.get('session_history', '')

        prompt = prompt_template.format(
            full_context=full_context,
            situation=situation,
            campaign_context=world_lore,
            party_context=party_context,
            session_context=session_context
        )

        logging.info(f"Sending '{sim_type}' simulation request for {npc_data.get('name')}.")
        response = self.client.models.generate_content(model=self.text_model_name, contents=prompt)
        return response.text

    def generate_npc_portrait(self, appearance_prompt):
        if not self.is_api_key_valid(): raise ValueError("API Client not configured. Check your API key.")

        portrait_prompt_template = self.settings.get("prompts", {}).get("npc_portrait")
        if not portrait_prompt_template:
            raise ValueError("Portrait prompt not found in settings.")

        logging.info(f"Sending image generation request to model '{self.image_model_name}'.")
        prompt = portrait_prompt_template.format(appearance_prompt=appearance_prompt)
        try:
            response = self.client.models.generate_images(model=self.image_model_name, prompt=prompt,
                                                          config=types.GenerateImagesConfig(number_of_images=1))
            if hasattr(response, 'generated_images') and response.generated_images:
                return response.generated_images[0].image.image_bytes
            else:
                raise Exception("Image generation call succeeded, but no images were returned.")
        except google_exceptions.PermissionDenied as e:
            logging.error(f"Image generation failed due to a permission error (likely billing): {e}")
            raise PermissionError(
                "Image generation failed. This model often requires a billed Google Cloud account.") from e
        except Exception as e:
            logging.error(f"An unexpected error occurred during image generation: {e}")
            raise