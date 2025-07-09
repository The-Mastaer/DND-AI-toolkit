import json
import os

class AppSettings:
    """
    A class to manage application settings.
    It handles loading settings from a JSON file and saving them back.
    This makes settings persistent across application sessions.
    """
    def __init__(self, settings_file='settings.json'):
        """
        Initializes the AppSettings object.

        Args:
            settings_file (str): The name of the file to store settings.
                                 Defaults to 'settings.json'.
        """
        self.settings_file = settings_file
        self.settings = {}
        self.load_settings()

    def load_settings(self):
        """
        Loads settings from the JSON file.
        If the file doesn't exist, it will be created when settings are saved.
        """
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    self.settings = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading settings file: {e}")
            self.settings = {}

    def save_settings(self):
        """
        Saves the current settings to the JSON file.
        """
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except IOError as e:
            print(f"Error saving settings file: {e}")

    def get_setting(self, key, default=None):
        """
        Retrieves a setting value by its key.

        Args:
            key (str): The key of the setting to retrieve.
            default: The value to return if the key is not found.

        Returns:
            The value of the setting, or the default value if not found.
        """
        return self.settings.get(key, default)

    def set_setting(self, key, value):
        """
        Sets a value for a given setting key.

        Args:
            key (str): The key of the setting to set.
            value: The value to set for the key.
        """
        self.settings[key] = value