import flet as ft
from app_settings import AppSettings
from services import GeminiService, DataManager
import config
from views import create_main_menu_view, create_world_manager_view, create_settings_view, create_campaign_manager_view


def main(page: ft.Page):
    """
    Initializes and runs the D&D Toolkit Flet application.
    This is the main entry point and router for the web/desktop app.
    """
    # --- Configuration and Service Initialization ---
    app_settings = AppSettings()
    api_key = config.load_api_key()
    supabase_url, supabase_key = config.load_supabase_credentials()
    data_manager = DataManager(supabase_url=supabase_url, supabase_key=supabase_key)
    gemini_service = GeminiService(api_key=api_key, app_settings=app_settings, data_manager=data_manager)

    # --- Flet App Configuration ---
    page.title = "DM's AI Toolkit"
    page.window_min_width = 1100
    page.window_min_height = 750

    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(color_scheme_seed="brown")

    page.fonts = {
        "Cinzel": "https://github.com/google/fonts/raw/main/ofl/cinzel/Cinzel-Regular.ttf",
        "Roboto": "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Regular.ttf"
    }

    # --- App-wide State Dictionary ---
    app_state = {
        "data_manager": data_manager,
        "api_service": gemini_service,
        "app_settings": app_settings,
        "selected_world_for_campaigns": None  # To pass context between views
    }

    # --- UI Layout Controls ---
    main_content_area = ft.Column(expand=True)

    # --- Routing and View Handling ---
    def route_change(route):
        """
        This function is called every time the page's route changes.
        It swaps the content in the main_content_area.
        """
        main_content_area.controls.clear()

        if page.route == "/worlds":
            main_content_area.controls.append(create_world_manager_view(page, app_state))
        elif page.route == "/campaigns":
            main_content_area.controls.append(create_campaign_manager_view(page, app_state))
        elif page.route == "/settings":
            main_content_area.controls.append(create_settings_view(page, app_state))
        else:  # Default to main menu
            main_content_area.controls.append(create_main_menu_view(page, app_state))

        page.update()

    # --- Page Event Handlers ---
    page.on_route_change = route_change

    # --- Main App Layout ---
    page.add(
        ft.Row(
            [
                ft.NavigationRail(
                    selected_index=0,
                    label_type=ft.NavigationRailLabelType.ALL,
                    min_width=100,
                    min_extended_width=400,
                    group_alignment=-0.9,
                    destinations=[
                        ft.NavigationRailDestination(
                            icon=ft.Icons.HOME_OUTLINED, selected_icon=ft.Icons.HOME, label="Home"
                        ),
                        ft.NavigationRailDestination(
                            icon=ft.Icons.PUBLIC_OUTLINED, selected_icon=ft.Icons.PUBLIC, label="Worlds"
                        ),
                        ft.NavigationRailDestination(
                            icon=ft.Icons.SETTINGS_OUTLINED,
                            selected_icon=ft.Icons.SETTINGS,
                            label="Settings",
                        ),
                    ],
                    on_change=lambda e: page.go(["/", "/worlds", "/settings"][e.control.selected_index]),
                ),
                ft.VerticalDivider(),
                main_content_area,
            ],
            expand=True,
        )
    )

    # --- Initial Load ---
    page.go(page.route)


# --- Application Entry Point ---
if __name__ == "__main__":
    ft.app(target=main)