# src/main.py

import flet as ft
import asyncio
import json

from views.main_view import MainView
from views.worlds_view import WorldsView
from views.settings_view import SettingsView
from views.login_view import LoginView
from views.campaigns_view import CampaignsView
from views.characters_view import CharactersView
from views.character_form_view import CharacterFormView
# Import the singleton service instances
from services.supabase_service import supabase
from services.gemini_service import gemini_service


async def main(page: ft.Page):
    """
    The main entry point for the Flet application.
    Initializes services and sets up routing.
    """
    # Initialize services at the very beginning
    await supabase.initialize()
    # GeminiService is now also initialized here implicitly by being a singleton

    page.title = "D&D AI Toolkit"
    page.window_width = 1200
    page.window_height = 800

    # Load and apply theme settings on startup for persistence
    theme_mode = await asyncio.to_thread(page.client_storage.get, "app.theme_mode") or "dark"
    theme_color = await asyncio.to_thread(page.client_storage.get, "app.theme_color") or "blue"
    page.theme_mode = theme_mode
    page.theme = ft.Theme(color_scheme_seed=theme_color)

    # REFACTOR: Pass the gemini_service instance to all views that need it
    app_views = {
        "/login": lambda p: LoginView(p),
        # Views that need the Gemini service
        "/": lambda p: MainView(p, gemini_service),
        "/worlds": lambda p: WorldsView(p, gemini_service),
        "/settings": lambda p: SettingsView(p, gemini_service),
        "/campaigns": lambda p: CampaignsView(p, gemini_service),
        "/characters": lambda p: CharactersView(p, gemini_service),
        "/character_edit": lambda p, **params: CharacterFormView(p, gemini_service, **params),
    }

    async def route_change(route):
        """
        Handles route changes by checking authentication and directing
        the user to the appropriate view.
        """
        print(f"Current route: {route.route}")

        saved_session_json = await asyncio.to_thread(page.client_storage.get, "supabase.session")
        if saved_session_json:
            session_data = json.loads(saved_session_json)
            try:
                await supabase.set_session(session_data['access_token'], session_data['refresh_token'])
                print("--- Successfully restored session from client storage. ---")
            except Exception as e:
                print(f"--- Failed to restore session, clearing storage: {e} ---")
                await asyncio.to_thread(page.client_storage.remove, "supabase.session")

        user_session = await supabase.get_user()

        if not user_session and page.route != "/login":
            page.go("/login")
            return

        if user_session and page.route == "/login":
            page.go("/")
            return

        page.views.clear()

        # Determine the base view (Login or Main)
        base_route = "/login" if not user_session else "/"
        page.views.append(app_views[base_route](page))

        # Handle other routes by parsing them and passing parameters
        route_parts = page.route.strip("/").split("/")

        current_view_key = f"/{route_parts[0]}" if route_parts[0] else "/"

        if current_view_key in app_views and current_view_key not in ["/", "/login"]:
            if current_view_key == "/character_edit" and len(route_parts) > 1:
                # Handle /character_edit/:id or /character_edit/new/:campaign_id
                char_id_or_new = route_parts[1]
                if char_id_or_new == 'new' and len(route_parts) > 2:
                    campaign_id = route_parts[2]
                    page.views.append(app_views[current_view_key](page, campaign_id=campaign_id))
                else:
                    page.views.append(app_views[current_view_key](page, character_id=char_id_or_new))
            else:
                # This is where the call to other views happens
                page.views.append(app_views[current_view_key](page))

        page.update()

    def view_pop(view):
        """
        Handles the 'back' action, popping the current view from the stack
        and navigating to the previous one.
        """
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)


if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.FLET_APP)
