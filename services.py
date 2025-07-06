import sqlite3
import logging
from google import genai
from google.genai import types
from google.api_core import exceptions as google_exceptions
import json
import re

from prompts import (
    NPC_GENERATION_PROMPT,
    NPC_SIMULATION_SHORT_PROMPT,
    NPC_SIMULATION_LONG_PROMPT,
    NPC_PORTRAIT_PROMPT
)


class DataManager:
    # ... (no changes in this class)
    def __init__(self, db_filepath):
        self.db_filepath = db_filepath
        self._create_npc_table()
        self._create_campaign_table()

    def _get_connection(self):
        return sqlite3.connect(self.db_filepath)

    def _create_npc_table(self):
        create_table_sql = "CREATE TABLE IF NOT EXISTS npcs (name TEXT PRIMARY KEY, race_class TEXT, appearance TEXT, personality TEXT, backstory TEXT, plot_hooks TEXT, attitude TEXT, rarity TEXT, race TEXT, character_class TEXT, environment TEXT, background TEXT, gender TEXT, image_data BLOB, custom_prompt TEXT, roleplaying_tips TEXT);"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(create_table_sql)
                conn.commit()
            logging.info("Database table 'npcs' is ready.")
        except sqlite3.Error as e:
            logging.error(f"Database error during NPC table creation: {e}")

    def _create_campaign_table(self):
        create_table_sql = "CREATE TABLE IF NOT EXISTS campaigns (campaign_name TEXT PRIMARY KEY, campaign_lore TEXT, party_info TEXT, session_history TEXT);"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(create_table_sql)
                try:
                    cursor.execute("ALTER TABLE campaigns ADD COLUMN party_info TEXT")
                except sqlite3.OperationalError:
                    pass
                try:
                    cursor.execute("ALTER TABLE campaigns ADD COLUMN session_history TEXT")
                except sqlite3.OperationalError:
                    pass
                conn.commit()
            logging.info("Database table 'campaigns' is ready.")
        except sqlite3.Error as e:
            logging.error(f"Database error during campaign table creation: {e}")

    def load_data(self):
        npcs_dict = {}
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM npcs")
                rows = cursor.fetchall()
                for row in rows: npcs_dict[row['name']] = dict(row)
            logging.info(f"Successfully loaded {len(npcs_dict)} NPCs from {self.db_filepath}.")
            return npcs_dict
        except sqlite3.Error as e:
            logging.error(f"Failed to load data from database: {e}")
            return {}

    def save_npc(self, npc_data, old_name=None):
        if old_name and old_name != npc_data['name']: self.delete_npc(old_name)
        columns = ["name", "race_class", "appearance", "personality", "backstory", "plot_hooks", "attitude", "rarity",
                   "race", "character_class", "environment", "background", "gender", "image_data", "custom_prompt",
                   "roleplaying_tips"]
        placeholders = ", ".join(["?"] * len(columns))
        sql = f"INSERT OR REPLACE INTO npcs ({', '.join(columns)}) VALUES ({placeholders})"
        values = tuple(npc_data.get(col) for col in columns)
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, values)
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

    def load_campaigns(self):
        campaigns_dict = {}
        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM campaigns")
                rows = cursor.fetchall()
                for row in rows: campaigns_dict[row['campaign_name']] = dict(row)
            logging.info(f"Successfully loaded {len(campaigns_dict)} campaigns.")
            return campaigns_dict
        except sqlite3.Error as e:
            logging.error(f"Failed to load campaigns from database: {e}")
            return {}

    def save_campaign(self, campaign_data, old_name=None):
        if old_name and old_name != campaign_data['campaign_name']: self.delete_campaign(old_name)
        sql = "INSERT OR REPLACE INTO campaigns (campaign_name, campaign_lore, party_info, session_history) VALUES (?, ?, ?, ?)"
        values = (campaign_data['campaign_name'], campaign_data.get('campaign_lore'), campaign_data.get('party_info'),
                  campaign_data.get('session_history'))
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, values)
                conn.commit()
            logging.info(f"Successfully saved campaign '{campaign_data['campaign_name']}'.")
        except sqlite3.Error as e:
            logging.error(f"Failed to save campaign '{campaign_data['campaign_name']}': {e}")

    def delete_campaign(self, campaign_name):
        sql = "DELETE FROM campaigns WHERE campaign_name = ?"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (campaign_name,))
                conn.commit()
            logging.info(f"Successfully deleted campaign '{campaign_name}'.")
        except sqlite3.Error as e:
            logging.error(f"Failed to delete campaign '{campaign_name}': {e}")


class GeminiService:
    def __init__(self, api_key, text_model_name, image_model_name):
        self.api_key = api_key
        self.text_model_name = text_model_name
        self.image_model_name = image_model_name
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

    def generate_npc(self, params, campaign_data=None, include_party=True, include_session=True):
        """Generates an NPC using the Gemini API based on given parameters and full campaign context."""
        if not self.is_api_key_valid(): raise ValueError("API Client not configured. Check your API key.")
        campaign_data = campaign_data or {}

        lore_context = campaign_data.get('campaign_lore', '')
        party_context = campaign_data.get('party_info', '') if include_party else ""
        session_context = campaign_data.get('session_history', '') if include_session else ""
        custom_prompt_text = params.get('custom_prompt', '')

        campaign_context_section = f"\n**Campaign Lore (Follow this lore closely):**\n{lore_context}\n" if lore_context else ""
        party_context_section = f"\n**Player Party Information (Consider their impact):**\n{party_context}\n" if party_context else ""
        session_context_section = f"\n**Recent Session History (The NPC may be aware of these events):**\n{session_context}\n" if session_context else ""
        custom_prompt_section = f"\n**Additional Custom Prompt:**\n- {custom_prompt_text}\n" if custom_prompt_text else ""

        prompt = NPC_GENERATION_PROMPT.format(
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
        """Simulates an NPC's reaction to a given situation."""
        if not self.is_api_key_valid(): raise ValueError("API Client not configured. Check your API key.")
        campaign_data = campaign_data or {}

        full_context = (f"Appearance: {npc_data.get('appearance', 'N/A')}\n"
                        f"Personality: {npc_data.get('personality', 'N/A')}\n"
                        f"Backstory: {npc_data.get('backstory', 'N/A')}\n"
                        f"Roleplaying Tips: {npc_data.get('roleplaying_tips', 'N/A')}")

        lore_context = campaign_data.get('campaign_lore', '')
        party_context = campaign_data.get('party_info', '')
        session_context = campaign_data.get('session_history', '')

        prompt_template = NPC_SIMULATION_SHORT_PROMPT if sim_type == "Short" else NPC_SIMULATION_LONG_PROMPT

        prompt = prompt_template.format(
            full_context=full_context,
            situation=situation,
            campaign_context=lore_context,
            party_context=party_context,
            session_context=session_context
        )

        logging.info(f"Sending '{sim_type}' simulation request for {npc_data.get('name')}.")
        response = self.client.models.generate_content(model=self.text_model_name, contents=prompt)
        return response.text

    def generate_npc_portrait(self, appearance_prompt):
        if not self.is_api_key_valid(): raise ValueError("API Client not configured. Check your API key.")
        logging.info(f"Sending image generation request to model '{self.image_model_name}'.")
        prompt = NPC_PORTRAIT_PROMPT.format(appearance_prompt=appearance_prompt)
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