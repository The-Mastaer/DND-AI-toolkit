# src/main.py

import flet as ft
import asyncio
import json

from src.views.main_view import MainView
from src.views.worlds_view import WorldsView
from src.views.settings_view import SettingsView
from src.views.login_view import LoginView
from src.views.campaigns_view import CampaignsView
from src.views.characters_view import CharactersView
from src.views.character_form_view import CharacterFormView
from src.services.supabase_service import supabase


async def main(page: ft.Page):
    """
    The main entry point for the Flet application.
    """
    await supabase.initialize()

    page.title = "D&D AI Toolkit"
    page.window_width = 1200
    page.window_height = 800

    # *** FIX: Load and apply theme settings on startup for persistence ***
    theme_mode = await asyncio.to_thread(page.client_storage.get, "app.theme_mode") or "dark"
    theme_color = await asyncio.to_thread(page.client_storage.get, "app.theme_color") or "blue"
    page.theme_mode = theme_mode
    page.theme = ft.Theme(color_scheme_seed=theme_color)

    app_views = {
        "/": MainView,
        "/worlds": WorldsView,
        "/settings": SettingsView,
        "/login": LoginView,
        "/campaigns": CampaignsView,
        "/characters": CharactersView,
        "/character_edit": CharacterFormView
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

        base_view_class = app_views.get("/login") if not user_session else app_views.get("/")
        page.views.append(base_view_class(page))

        if page.route != "/" and page.route != "/login":
            if page.route in app_views:
                page.views.append(app_views[page.route](page))
                print("Route added to {page}")
            elif page.route.startswith("/worlds/") and page.route.endswith("/campaigns"):
                page.views.append(app_views["/campaigns"](page))
                print("Route to Campaigns added")
            elif page.route.startswith("/characters/") and page.route.endswith("/character_edit"):
                page.views.append(app_views["/character_edit"](page))
                print("Route to Character edit added")

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
    ft.app(target=main)