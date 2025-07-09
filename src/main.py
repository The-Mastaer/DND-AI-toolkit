# src/main.py

import flet as ft
import uuid
from .state import AppState
from .app_settings import AppSettings
from .services.supabase_service import SupabaseService
from .services.gemini_service import GeminiService
from .views.main_menu_view import MainMenuView
from .views.worlds_view import WorldsView
from .views.campaigns_view import CampaignsView
from .views.settings_view import SettingsView


def main(page: ft.Page):
    """
    The main entry point for the Flet application.
    Initializes services, state, and routing.
    """
    print("--- Application Starting ---")
    # --- Dependency Injection & State Initialization ---
    state = AppState()
    settings = AppSettings()
    settings.load_settings(state)

    # --- Application Setup ---
    page.title = "D&D AI Toolkit"
    page.theme_mode = state.theme_mode.upper()
    page.window_width = 400
    page.window_height = 600

    try:
        supabase_service = SupabaseService()
        gemini_service = GeminiService()
        state.user = {'id': str(uuid.uuid4())}
        print(f"Mock user initialized with ID: {state.user['id']}")
    except Exception as e:
        page.add(ft.Text(
            f"Fatal Error: Could not initialize services. Please check .env configuration. Details: {e}",
            color=ft.Colors.RED_700
        ))
        return

    # --- Views Dictionary ---
    views = {
        "/": MainMenuView(page, state),
        "/worlds": WorldsView(page, state, supabase_service),
        "/campaigns": CampaignsView(page, state),
        "/settings": SettingsView(page, state, settings),
    }

    # --- Routing Logic ---
    def route_change(route):
        print(f"Route changing to: {page.route}")
        page.views.clear()

        view_to_display = views.get(page.route, views["/"])
        page.views.append(view_to_display)

        if page.route != "/":
            page.views.insert(0, views["/"])

        page.update()
        print("Route change complete.")

    def view_pop(_: ft.View):
        print("View pop event triggered.")
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    # --- Page Event Handlers ---
    page.on_route_change = route_change
    page.on_view_pop = view_pop

    # --- Initial Route ---
    print("Setting initial route...")
    page.go("/")


if __name__ == "__main__":
    ft.app(target=main)