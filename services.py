import sqlite3
import logging
from google import genai
from google.genai import types
import json
import re  # Import the regular expression module


class DataManager:
    """Handles all database operations for NPCs."""

    def __init__(self, db_filepath):
        self.db_filepath = db_filepath
        self._create_table()

    def _get_connection(self):
        """Establishes a connection to the SQLite database."""
        return sqlite3.connect(self.db_filepath)

    def _create_table(self):
        """Creates the npcs table if it doesn't already exist."""
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
                               BLOB, \
                               custom_prompt \
                               TEXT, \
                               roleplaying_tips \
                               TEXT
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
        """Loads all NPCs from the database into a dictionary."""
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
        """Saves or updates an NPC in the database."""
        if old_name and old_name != npc_data['name']:
            self.delete_npc(old_name)

        sql = """
        INSERT OR REPLACE INTO npcs (name, race_class, appearance, personality, backstory, plot_hooks, 
                                     attitude, rarity, race, character_class, environment, background, gender, 
                                     image_data, custom_prompt, roleplaying_tips)
        VALUES (:name, :race_class, :appearance, :personality, :backstory, :plot_hooks,
                :attitude, :rarity, :race, :character_class, :environment, :background, :gender, 
                :image_data, :custom_prompt, :roleplaying_tips)
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
        """Deletes an NPC from the database."""
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
    """Handles interactions with the Gemini API using the modern SDK."""

    def __init__(self, api_key, text_model_name, image_model_name):
        self.api_key = api_key
        self.text_model_id = text_model_name
        self.image_model_id = image_model_name
        self.client = None
        self._configure_api()

    def _configure_api(self):
        """Configures the Gemini API client if a valid key is provided."""
        if self.is_api_key_valid():
            self.client = genai.Client(api_key=self.api_key)
            logging.info("Gemini API Client configured successfully.")

    def is_api_key_valid(self):
        """Checks if the API key is present and not a placeholder."""
        is_valid = self.api_key and self.api_key != "PASTE_YOUR_API_KEY_HERE"
        if not is_valid:
            logging.warning("API Key is missing or is a placeholder.")
        return is_valid

    def generate_npc(self, params):
        """Generates an NPC using the Gemini API based on given parameters."""
        if not self.client:
            raise ValueError("API Client not configured.")

        custom_prompt_text = params.get('custom_prompt', '')
        custom_prompt_section = f"\n**Additional Custom Prompt:**\n- {custom_prompt_text}\n" if custom_prompt_text else ""

        prompt = f"""
        You are a creative Dungeon Master assistant. Your task is to generate a compelling D&D NPC based on the following parameters.
        For any parameter set to "Random", you must invent a suitable value.
        **Keep descriptions concise and to the point (2-3 sentences max for appearance, personality, and backstory).**
        The output MUST be a valid JSON object with the exact keys: "name", "gender", "race_class", "appearance", "personality", "backstory", "plot_hooks", "background", "attitude", "rarity", "race", "character_class", "environment", and "roleplaying_tips".
        The "roleplaying_tips" key should contain a few bullet points on how a DM can portray the character, including notes on their voice, mannerisms, and general demeanor.
        The JSON object must be the only thing in your response. Do not include markdown formatting like ```json or any other explanatory text.

        **Parameters:**
        - Gender: {params['gender']}
        - Attitude: {params['attitude']}
        - Rarity/Level: {params['rarity']}
        - Environment: {params['environment']}
        - Race: {params['race']}
        - Class: {params['character_class']}
        - Background: {params['background']}
        {custom_prompt_section}
        Generate the NPC now.
        """
        logging.info(f"Sending generation request to model '{self.text_model_id}'.")

        response = self.client.models.generate_content(
            model=self.text_model_id,
            contents=prompt
        )
        raw_text = response.text

        logging.info(f"Received raw response from Gemini:\n{raw_text}")

        json_str = ""
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
                    raise json.JSONDecodeError("No JSON object found in the response.", raw_text, 0)

            parsed_json = json.loads(json_str)
            return parsed_json, raw_text

        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode JSON from AI response. Error: {e}")
            raise ValueError(f"The AI returned a malformed description. Please try generating again. Error: {e}") from e

    def simulate_reaction(self, npc_data, situation):
        """Simulates an NPC's reaction to a given situation."""
        if not self.client:
            raise ValueError("API Client not configured.")

        full_context = (f"Appearance: {npc_data.get('appearance', 'N/A')}\n"
                        f"Personality: {npc_data.get('personality', 'N/A')}\n"
                        f"Backstory: {npc_data.get('backstory', 'N/A')}\n"
                        f"Roleplaying Tips: {npc_data.get('roleplaying_tips', 'N/A')}")

        prompt = f"""
        Act as a D&D NPC. Use the roleplaying tips provided to inform your response, including voice, mannerisms, and demeanor.
        **NPC Profile:**
        - Name: {npc_data.get('name', 'N/A')}, Race/Class: {npc_data.get('race_class', 'N/A')}
        - Character Info: {full_context}
        **Situation:** {situation}
        **Your Reaction (in character):**
        """
        logging.info(f"Sending simulation request for {npc_data.get('name')}.")
        response = self.client.models.generate_content(
            model=self.text_model_id,
            contents=prompt
        )
        return response.text

    def generate_npc_portrait(self, appearance_prompt):
        """
        Generates an NPC portrait using the Imagen API via the `google-genai` SDK.
        """
        if not self.client:
            raise ValueError("API Client not configured.")

        logging.info(f"Sending image generation request to model '{self.image_model_id}'.")
        prompt = f"A digital painting portrait of a D&D character: {appearance_prompt}. Fantasy art, character concept, detailed, high quality."

        try:
            result = self.client.models.generate_images(
                model=self.image_model_id,
                prompt=prompt,
                config=dict(
                    number_of_images=1,
                    person_generation="ALLOW_ADULT",
                    aspect_ratio="1:1"
                )
            )

            if result.generated_images:
                # Return the raw bytes of the first generated image
                return result.generated_images[0].image.image_bytes
            else:
                raise Exception("Image generation succeeded, but no image data was returned.")

        except types.PermissionDeniedError as e:
            logging.error(f"Image generation failed due to a permission error (likely billing): {e}")
            # Re-raise as a more specific error for the UI to catch
            raise PermissionError(
                "Image generation failed. This model often requires a billed Google Cloud account.") from e
        except Exception as e:
            logging.error(f"An unexpected error occurred during image generation: {e}")
            raise
