from main_menu_app import MainMenuApp
from services import DataManager, GeminiService
import config


def main():
    """
    Initializes and runs the D&D Toolkit application.
    """
    api_key = config.load_api_key()
    data_manager = DataManager(db_filepath=config.DB_FILE)
    gemini_service = GeminiService(
        api_key=api_key,
        text_model_name=config.TEXT_MODEL_NAME,
        image_model_name=config.IMAGE_MODEL_NAME
    )

    app = MainMenuApp(data_manager=data_manager, api_service=gemini_service)
    app.mainloop()


if __name__ == "__main__":
    main()