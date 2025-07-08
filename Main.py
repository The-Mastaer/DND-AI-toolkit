import flet as ft
from main_menu_app import MainMenuApp
from services import GeminiService, DataManager
from app_settings import AppSettings
import config


def main(page: ft.Page):
    """
    Initializes and runs the D&D Toolkit Flet application.
    This is the main entry point for the web/desktop app.
    """
    # --- Configuration Loading ---
    # Load user-configurable settings from settings.json
    app_settings = AppSettings()

    # Load API keys and credentials from their respective JSON files
    api_key = config.load_api_key()
    supabase_url, supabase_key = config.load_supabase_credentials()

    # --- Service Initialization ---
    # Initialize the DataManager with Supabase credentials.
    # This single instance will be passed throughout the app.
    data_manager = DataManager(supabase_url=supabase_url, supabase_key=supabase_key)

    # Initialize the GeminiService with the API key and other services.
    # This single instance will also be passed throughout the app.
    gemini_service = GeminiService(
        api_key=api_key,
        app_settings=app_settings,
        data_manager=data_manager
    )

    # --- Flet App Initialization ---
    # Configure the main Flet page/window properties.
    page.title = "DM's AI Toolkit"
    page.window_min_width = 1100
    page.window_min_height = 750

    # Set the theme based on user settings. Flet uses lowercase strings.
    theme_setting = app_settings.get("theme", "system")
    page.theme_mode = ft.ThemeMode(theme_setting.lower())

    # Create an instance of the main app UI control.
    # We pass all the necessary services and settings to it.
    app = MainMenuApp(
        data_manager=data_manager,
        api_service=gemini_service,
        app_settings=app_settings
    )

    # Add the app's root control to the page. Flet will then render it.
    page.add(app)

    # Ensure the page updates to show the initial UI.
    page.update()


# --- Application Entry Point ---
# This is the standard way to run a Flet application.
if __name__ == "__main__":
    ft.app(target=main)
