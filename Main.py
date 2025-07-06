from main_menu_app import MainMenuApp
from services import GeminiService, DataManager
from app_settings import AppSettings
import config

def main():
    """
    Initializes and runs the D&D Toolkit application.
    """
    # Load user-configurable settings
    app_settings = AppSettings()

    # Load static API key
    api_key = config.load_api_key()

    # Initialize services with configured settings
    data_manager = DataManager(db_filepath=config.DB_FILE)
    gemini_service = GeminiService(
        api_key=api_key,
        app_settings=app_settings
    )

    # Pass all dependencies to the main app
    app = MainMenuApp(
        data_manager=data_manager,
        api_service=gemini_service,
        app_settings=app_settings
    )
    app.mainloop()

if __name__ == "__main__":
    main()