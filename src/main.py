import flet as ft
# The import 'from flet.routing import TemplateRoute' has been removed.

# --- All other imports remain the same ---
from .services.supabase_service import supabase
from .views.main_view import MainView
from .views.worlds_view import WorldsView
from .views.settings_view import SettingsView
from .views.new_world_view import NewWorldView
from .views.edit_world_view import EditWorldView


def main(page: ft.Page):
    """
    The main entry point for the Flet application.
    """
    page.title = "D&D AI Toolkit"
    page.window_width = 800
    page.window_height = 600

    def route_change(e):
        """
        Handles navigation by changing the views displayed on the page.
        """
        print(f"Current route: {e.route}")
        page.views.clear()
        page.views.append(MainView(page))

        # Corrected to use ft.TemplateRoute directly
        troute = ft.TemplateRoute(e.route)

        if troute.match("/worlds"):
            page.views.append(WorldsView(page))
        elif troute.match("/new-world"):
            page.views.append(NewWorldView(page))
        elif troute.match("/settings"):
            page.views.append(SettingsView(page))
        elif troute.match("/edit-world/:world_id/:lang_code"):
            page.views.append(
                EditWorldView(
                    page,
                    world_id=int(troute.world_id),
                    lang_code=troute.lang_code
                )
            )

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
