import flet as ft

from .services.supabase_service import supabase
from .views.main_view import MainView
from .views.worlds_view import WorldsView
from .views.settings_view import SettingsView
from .views.new_world_view import NewWorldView
from .views.edit_world_view import EditWorldView
from .views.campaigns_view import CampaignsView
from .views.new_campaign_view import NewCampaignView
from .views.edit_campaign_view import EditCampaignView


def main(page: ft.Page):
    """
    The main entry point for the Flet application.
    """
    page.title = "D&D AI Toolkit"
    page.window_width = 800
    page.window_height = 600

    # --- Load and apply theme settings at startup ---
    # This ensures the app opens with the user's saved theme.
    theme_mode_str = page.client_storage.get("theme_mode") or "system"
    color_scheme_seed = page.client_storage.get("color_scheme") or "blue"
    page.theme_mode = ft.ThemeMode(theme_mode_str)
    page.theme = ft.Theme(color_scheme_seed=color_scheme_seed)
    page.dark_theme = ft.Theme(color_scheme_seed=color_scheme_seed)

    # ------------------------------------------------

    def route_change(e):
        """
        Handles navigation by changing the views displayed on the page.
        """
        print(f"Current route: {e.route}")
        page.views.clear()
        page.views.append(MainView(page))

        troute = ft.TemplateRoute(e.route)

        if troute.match("/worlds"):
            page.views.append(WorldsView(page))
        elif troute.match("/new-world"):
            page.views.append(NewWorldView(page))
        elif troute.match("/settings"):
            page.views.append(SettingsView(page))
        elif troute.match("/edit-world/:world_id/:lang_code"):
            page.views.append(EditWorldView(page, int(troute.world_id), troute.lang_code))
        elif troute.match("/campaigns/:world_id/:lang_code"):
            page.views.append(CampaignsView(page, int(troute.world_id), troute.lang_code))
        elif troute.match("/new-campaign/:world_id/:lang_code"):
            page.views.append(NewCampaignView(page, int(troute.world_id), troute.lang_code))
        elif troute.match("/edit-campaign/:campaign_id/:lang_code"):
            page.views.append(EditCampaignView(page, int(troute.campaign_id), troute.lang_code))

        page.update()

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route)


if __name__ == "__main__":
    ft.app(target=main, port=8550, view=ft.AppView.FLET_APP)
