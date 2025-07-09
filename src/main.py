import flet as ft
# --- Use relative imports for modules within the 'src' package ---
from .views.worlds_view import WorldsView
from .views.campaigns_view import CampaignsView
from .views.characters_view import CharactersView
from .views.settings_view import SettingsView
from .components.app_bar import main_app_bar

def main(page: ft.Page):
    """
    The main entry point of the application.
    Initializes the page and handles routing.
    """
    page.title = "D&D AI Toolkit"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 400
    page.window_height = 800

    # Application state initialization using page.session
    if not page.session.contains_key("selected_world_id"):
        page.session.set("selected_world_id", None)
    if not page.session.contains_key("selected_campaign_id"):
        page.session.set("selected_campaign_id", None)
    if not page.session.contains_key("selected_character_id"):
        page.session.set("selected_character_id", None)

    def route_change(route):
        """
        Handles the navigation between different views in the app.
        """
        page.views.clear()
        page.views.append(
            ft.View(
                "/",
                [WorldsView()],
                appbar=main_app_bar(page),
            )
        )
        if page.route == "/campaigns":
            page.views.append(
                ft.View(
                    "/campaigns",
                    [CampaignsView()],
                    appbar=main_app_bar(page),
                )
            )
        elif page.route == "/characters":
            page.views.append(
                ft.View(
                    "/characters",
                    [CharactersView()],
                    appbar=main_app_bar(page),
                )
            )
        elif page.route == "/settings":
            page.views.append(
                ft.View(
                    "/settings",
                    [SettingsView()],
                    appbar=main_app_bar(page),
                )
            )
        page.update()

    def view_pop(view):
        """
        Handles the back button logic.
        """
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)

if __name__ == "__main__":
    # This part is tricky for package execution.
    # The recommended way to run is `python -m src.main` from the project root.
    # To allow direct execution for simple testing, we can modify the path.
    import sys
    import os
    # Add the project root to the Python path
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from src.main import main as app_main
    ft.app(target=app_main)