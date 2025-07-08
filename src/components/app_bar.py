import flet as ft

def AppAppBar(page: ft.Page) -> ft.AppBar:
    """
    Creates and returns a standard AppBar for the application.

    This is a reusable UI component. It centralizes the appearance and
    functionality of the top navigation bar, ensuring consistency across all views.
    The primary navigation button now correctly points to the "Worlds" view.

    Args:
        page (ft.Page): The Flet page object, used for navigation.

    Returns:
        An ft.AppBar control.
    """
    return ft.AppBar(
        leading=ft.Icon(ft.Icons.AUTO_STORIES),
        leading_width=40,
        title=ft.Text("D&D AI Toolkit"),
        center_title=False,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST, # Corrected: Replaced non-existent color
        actions=[
            ft.IconButton(
                icon=ft.Icons.HOME,
                tooltip="Home",
                on_click=lambda _: page.go('/')
            ),
            ft.IconButton(
                icon=ft.Icons.PUBLIC,
                tooltip="Worlds",
                on_click=lambda _: page.go('/worlds')
            ),
            ft.IconButton(
                icon=ft.Icons.SETTINGS,
                tooltip="Settings",
                on_click=lambda _: page.go('/settings')
            )
        ],
    )
