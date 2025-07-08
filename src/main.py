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
    page.theme_mode = ft.ThemeMode.LIGHT

    if not config.validate_keys():
        page.add(ft.Text("Fatal Error: Missing API keys. Check console and .env file.", color=ft.Colors.ERROR))
        return

    # --- 2. Load Settings and Initialize Services ---
    print("Main: Loading application settings...")
    # Run the synchronous, blocking call in an executor via the page's event loop
    settings_json = await page.loop.run_in_executor(
        None, page.client_storage.get, "app_settings"
    )
    app_settings = AppSettings.from_json(settings_json)

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
        """Handles navigation, building the appropriate view based on the route."""
        print(f"Main: Route changed to: {route_event.route}")
        page.views.clear()

        view_map = {
            "/": MainMenuView,
            "/worlds": WorldsView,
            "/settings": SettingsView,
        }

        # Instantiate the view from the map or a 404 view
        view_class = view_map.get(route_event.route)
        if view_class:
            view = view_class(page, app_state)
        else:
            view = ft.View(
                route="/404",
                controls=[ft.Text("404: Page not found", size=32)],
                vertical_alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )

        view.appbar = AppAppBar(page)
        # Add FAB to worlds view
        if isinstance(view, WorldsView):
            page.floating_action_button = view.fab
        else:
            page.floating_action_button = None

        page.views.append(view)

        if hasattr(view, 'on_view_load') and callable(view.on_view_load):
            await view.on_view_load()

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
