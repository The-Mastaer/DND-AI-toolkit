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
from services.supabase_service import supabase
from services.gemini_service import gemini_service


async def main(page: ft.Page):
    """
    The main entry point for the Flet application.
    Initializes services and sets up routing.
    """
    await supabase.initialize()

    page.title = "D&D AI Toolkit"
    page.window_width = 1200
    page.window_height = 800

    theme_mode = await asyncio.to_thread(page.client_storage.get, "app.theme_mode") or "dark"
    theme_color = await asyncio.to_thread(page.client_storage.get, "app.theme_color") or "blue"
    page.theme_mode = theme_mode
    page.theme = ft.Theme(color_scheme_seed=theme_color)

    app_views = {
        "/login": LoginView,
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
            print("--- Found saved session. Attempting to restore. ---")
            try:
                # The saved data is the full SignInWithPasswordResponse
                full_session_data = json.loads(saved_session_json)

                # We need to extract the tokens from the nested 'session' object
                session_info = full_session_data.get("session", {})
                access_token = session_info.get("access_token")
                refresh_token = session_info.get("refresh_token")

                if access_token and refresh_token:
                    # **THE FIX:** Pass the tokens as two separate arguments, as the function expects.
                    await supabase.set_session(access_token, refresh_token)
                    print("--- Session successfully set from client storage. ---")
                else:
                    print("--- Incomplete session data in storage. Clearing. ---")
                    await asyncio.to_thread(page.client_storage.remove, "supabase.session")

            except Exception as e:
                print(f"--- Failed to parse or set session, clearing storage: {e} ---")
                await asyncio.to_thread(page.client_storage.remove, "supabase.session")
        else:
            print("--- No saved session found. ---")

        user = await supabase.get_user()
        if user:
            print(f"--- User check successful. User ID: {user.id} ---")
        else:
            print("--- User check failed. No active user session. ---")

        if not user and page.route != "/login":
            page.go("/login")
            return

        if user and page.route == "/login":
            page.go("/")
            return

        page.views.clear()
        base_route_key = "/login" if not user else page.route.split("?")[0]

        if base_route_key == "/login":
            page.views.append(LoginView(page))
        else:
            page.views.append(app_views["/"](page))
            route_parts = base_route_key.strip("/").split("/")
            if route_parts and route_parts[0] and f"/{route_parts[0]}" in app_views:
                current_view_key = f"/{route_parts[0]}"
                if current_view_key == "/character_edit" and len(route_parts) > 1:
                    char_id_or_new = route_parts[1]
                    query_string = (page.route.split('?') + [''])[:2][1]
                    query_params = dict(qc.split('=') for qc in query_string.split('&')) if query_string else {}
                    lang = query_params.get('lang', 'en')
                    if char_id_or_new == 'new' and len(route_parts) > 2:
                        campaign_id = int(route_parts[2])
                        page.views.append(
                            app_views[current_view_key](page, campaign_id=campaign_id, selected_language=lang))
                    else:
                        character_id = int(char_id_or_new)
                        page.views.append(
                            app_views[current_view_key](page, character_id=character_id, selected_language=lang))
                else:
                    page.views.append(app_views[current_view_key](page))

        page.update()

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)


if __name__ == "__main__":
    ft.app(target=main)