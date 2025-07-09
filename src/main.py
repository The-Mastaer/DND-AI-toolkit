import flet as ft
import asyncio

# --- Project Imports ---
from src import config
from src.state import AppState
from src.app_settings import AppSettings
from src.services.supabase_service import SupabaseService
from src.services.gemini_service import GeminiService
from src.components.app_bar import AppAppBar

# --- View Imports ---
from src.views.main_menu_view import MainMenuView
from src.views.worlds_view import WorldsView
from src.views.settings_view import SettingsView


async def main(page: ft.Page):
    """
    The main entry point for the Flet application.
    This function initializes the application, sets up services, configures the UI,
    and defines the routing logic.
    """
    # --- 1. Application Setup ---
    page.title = "D&D AI Toolkit"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    if not config.validate_keys():
        page.add(ft.Text("Fatal Error: Missing API keys. Check console and .env file.", color=ft.Colors.ERROR))
        return

    # --- 2. Load Settings and Initialize Services ---
    print("Main: Loading application settings...")
    settings_json = await page.loop.run_in_executor(
        None, page.client_storage.get, "app_settings"
    )
    app_settings = AppSettings.from_json(settings_json)

    page.theme_mode = ft.ThemeMode.DARK if app_settings.theme_mode == "dark" else ft.ThemeMode.LIGHT

    print("Main: Initializing services...")
    supabase_service = SupabaseService(url=config.SUPABASE_URL, key=config.SUPABASE_ANON_KEY)
    await supabase_service.initialize_client()

    gemini_service = GeminiService(api_key=config.GEMINI_API_KEY)

    app_state = AppState(
        supabase_service=supabase_service,
        gemini_service=gemini_service,
        settings=app_settings,
    )
    print("Main: Services and state initialized.")

    # --- 3. Routing Logic ---
    async def route_change(route_event: ft.RouteChangeEvent):
        """
        Handles navigation by building the view and placing it on the page.
        The view itself is responsible for its own data loading via did_mount.
        """
        print(f"Main: Route changed to: {route_event.route}")

        # Logic for managing the FloatingActionButton has been removed for simplicity.
        page.floating_action_button = None
        page.views.clear()

        view_map = {
            "/": MainMenuView,
            "/worlds": WorldsView,
            "/settings": SettingsView,
        }

        view_class = view_map.get(route_event.route)
        if view_class:
            view = view_class(page, app_state)
        else:
            view = ft.View(route="/404", controls=[ft.Text("404: Page not found", size=32)])

        view.appbar = AppAppBar(page)

        page.views.append(view)
        page.update()

    def view_pop(view_event: ft.ViewPopEvent):
        """Handles the user clicking the 'back' button in the AppBar."""
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    # --- 4. Page Event Handlers ---
    page.on_route_change = route_change
    page.on_view_pop = view_pop

    # --- 5. Initial Page Load ---
    print("Main: Performing initial route...")
    page.go("/")


if __name__ == "__main__":
    ft.app(target=main)