import json
import logging
import os
from config import (
    DEFAULT_TEXT_MODEL, DEFAULT_IMAGE_MODEL,
    DEFAULT_LORE_MASTER_PROMPT, DEFAULT_RULES_LAWYER_PROMPT,
    DEFAULT_NPC_GENERATION_PROMPT, DEFAULT_TRANSLATION_PROMPT,
    DEFAULT_NPC_SIMULATION_SHORT_PROMPT, DEFAULT_NPC_SIMULATION_LONG_PROMPT
)

SETTINGS_FILE = "settings.json"


class AppSettings:
    """
    Manages loading and saving user-configurable application settings
    from a JSON file.
    """

    def __init__(self):
        self.settings = self._load_settings()

    def _get_defaults(self):
        """Returns a dictionary with the default settings."""
        return {
            "active_language": "en",
            "active_world_id": None,
            "active_campaign_id": None,
            "text_model": DEFAULT_TEXT_MODEL,
            "image_model": DEFAULT_IMAGE_MODEL,
            "theme": "System",
            "srd_pdf_path": "",
            "prompts": {
                "lore_master": DEFAULT_LORE_MASTER_PROMPT,
                "rules_lawyer": DEFAULT_RULES_LAWYER_PROMPT,
                "npc_generation": DEFAULT_NPC_GENERATION_PROMPT,
                "translation": DEFAULT_TRANSLATION_PROMPT,
                "npc_simulation_short": DEFAULT_NPC_SIMULATION_SHORT_PROMPT,
                "npc_simulation_long": DEFAULT_NPC_SIMULATION_LONG_PROMPT,
            }
        }

    def _load_settings(self):
        """
        Loads settings from the JSON file, intelligently merging them with
        defaults to ensure all keys are present and new defaults are added.
        """
        defaults = self._get_defaults()
        if not os.path.exists(SETTINGS_FILE):
            logging.info(f"'{SETTINGS_FILE}' not found. Creating with default settings.")
            self.settings = defaults
            self.save()
            return self.settings

        try:
            with open(SETTINGS_FILE, 'r') as f:
                user_settings = json.load(f)

            # This is the corrected deep merge logic.
            # Start with the full set of default prompts.
            merged_prompts = defaults['prompts'].copy()
            # Let the user's saved prompts override the defaults.
            if 'prompts' in user_settings and isinstance(user_settings['prompts'], dict):
                merged_prompts.update(user_settings['prompts'])

            # Update the main settings object
            defaults.update(user_settings)
            # Place the correctly merged prompts back into the settings.
            defaults['prompts'] = merged_prompts

            logging.info(f"Settings loaded and merged from '{SETTINGS_FILE}'.")
            return defaults
        except (IOError, json.JSONDecodeError) as e:
            logging.error(f"Error loading settings from {SETTINGS_FILE}: {e}. Using defaults.")
            return defaults

    def get(self, key, default=None):
        """Gets a setting value by key."""
        return self.settings.get(key, default)

    def set(self, key, value):
        """Sets a setting value by key."""
        self.settings[key] = value

    def save(self):
        """Saves the current settings to the JSON file."""
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(self.settings, f, indent=4)
            logging.info(f"Settings saved to '{SETTINGS_FILE}'.")
        except IOError as e:
            logging.error(f"Error saving settings to {SETTINGS_FILE}: {e}")