# src/main.py

import flet as ft
import os
from dotenv import load_dotenv

# --- Aria's Note: New, structured imports ---
from state import AppState
from services.supabase_service import SupabaseService
from services.gemini_service import GeminiService
from app_settings import AppSettings
from views.home_view import create_main_menu_view
from views.world_manager_view import create_world_manager_view
from views.campaign_manager_view import create_campaign_manager_view
from views.settings_view import create_settings_view


async def main(page: ft.Page):
    """
    Initializes and runs the D&D Toolkit Flet application.
    This is the main entry point and router, refactored for the Phoenix Protocol.
    """
    # --- Configuration and Service Initialization ---
    # Load environment variables from .env file
    load_dotenv()

    # Initialize settings and services
    app_settings = AppSettings()
    supabase_service = SupabaseService(
        url=os.environ.get("SUPABASE_URL"),
        key=os.environ.get("SUPABASE_KEY")
    )
    gemini_service = GeminiService(
        api_key=os.environ.get("GEMINI_API_KEY"),
        app_settings=app_settings,
        db_service=supabase_service  # Pass the Supabase service to Gemini
    )

    # --- Flet App Configuration ---
    page.title = "DM's AI Toolkit"
    page.window_min_width = 1100
    page.window_min_height = 750
    page.theme_mode = ft.ThemeMode(app_settings.get("theme", "DARK").upper())
    page.theme = ft.Theme(color_scheme_seed="orange")
    page.fonts = {
        "Cinzel": "https://github.com/google/fonts/raw/main/ofl/cinzel/Cinzel-Regular.ttf",
        "Roboto": "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Regular.ttf"
    }

    # --- Aria's Note: Centralized Application State ---
    # A single AppState instance holds all our services and runtime state.
    # This instance is passed to all views, ensuring consistent access.
    app_state = AppState(
        supabase_service=supabase_service,
        gemini_service=gemini_service,
        app_settings=app_settings
    )

    # --- UI Layout Controls ---
    main_content_area = ft.Column(expand=True, animate_opacity=300)

    # --- Routing and View Handling ---
    async def route_change(route):
        """
        This function is called every time the page's route changes.
        It swaps the content in the main_content_area based on the route.
        """
        main_content_area.opacity = 0
        await page.update_async()

        main_content_area.controls.clear()

        # Aria's Note: Views are now imported from their own modules
        if page.route == "/worlds":
            main_content_area.controls.append(await create_world_manager_view(page, app_state))
        elif page.route == "/campaigns":
            main_content_area.controls.append(await create_campaign_manager_view(page, app_state))
        elif page.route == "/settings":
            main_content_area.controls.append(await create_settings_view(page, app_state))
        else:  # Default to main menu (home)
            main_content_area.controls.append(await create_main_menu_view(page, app_state))

        main_content_area.opacity = 1
        await page.update_async()

    page.on_route_change = route_change

    # --- Main App Layout ---
    await page.add_async(
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
                            icon=ft.icons.HOME_OUTLINED, selected_icon=ft.icons.HOME, label="Home"
                        ),
                        ft.NavigationRailDestination(
                            icon=ft.icons.PUBLIC_OUTLINED, selected_icon=ft.icons.PUBLIC, label="Worlds"
                        ),
                        ft.NavigationRailDestination(
                            icon=ft.icons.SETTINGS_OUTLINED,
                            selected_icon=ft.icons.SETTINGS,
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

    # Initial load to the current route
    await page.go_async(page.route)


# --- Application Entry Point ---
if __name__ == "__main__":
    ft.app(target=main)
