# src/app_settings.py

import json
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .state import AppState


class AppSettings:
    """
    Handles loading and saving application settings to a JSON file.
    """

    def __init__(self, settings_file: str = "settings.json"):
        self.settings_file = settings_file

    def save_settings(self, state: 'AppState'):
        """Saves relevant parts of the application state to the settings file."""
        settings_data = {
            "selected_world_id": state.selected_world_id,
            "selected_campaign_id": state.selected_campaign_id,
            "selected_text_model": state.selected_text_model,
            "selected_image_model": state.selected_image_model,
            "theme_mode": state.theme_mode,
        }
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings_data, f, indent=4)
            print(f"Settings saved to {self.settings_file}")
        except IOError as e:
            print(f"Error saving settings: {e}")

    def load_settings(self, state: 'AppState'):
        """Loads settings from the settings file and applies them to the state."""
        if not os.path.exists(self.settings_file):
            print("Settings file not found. Using default state.")
            return

        try:
            with open(self.settings_file, 'r') as f:
                settings_data = json.load(f)

            # Load selections
            state.selected_world_id = settings_data.get("selected_world_id")
            state.selected_campaign_id = settings_data.get("selected_campaign_id")

            # Load theme
            state.theme_mode = settings_data.get("theme_mode", "dark")

            # Load models, falling back to default if saved model is no longer valid
            loaded_text_model = settings_data.get("selected_text_model")
            if loaded_text_model and loaded_text_model in state.available_text_models:
                state.selected_text_model = loaded_text_model

            loaded_image_model = settings_data.get("selected_image_model")
            if loaded_image_model and loaded_image_model in state.available_image_models:
                state.selected_image_model = loaded_image_model

            print(f"Settings loaded from {self.settings_file}")

        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading settings: {e}. Using default state.")