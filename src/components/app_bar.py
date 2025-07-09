import flet as ft

def main_app_bar(page: ft.Page) -> ft.AppBar:
    """
    Creates and returns the main application bar.
    This is a simple function that returns a configured ft.AppBar.
    It is completely stateless and uses the page object for navigation.
    This version uses the correct, modern Flet API syntax.

    Args:
        page (ft.Page): The Flet page object, used for navigation.

    Returns:
        ft.AppBar: The configured application bar.
    """
    return ft.AppBar(
        leading=ft.Icon(ft.Icons.DATA_OBJECT_ROUNDED),
        title=ft.Text("D&D AI Toolkit"),
        center_title=False,
        # Corrected the deprecated color name to its modern equivalent.
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        actions=[
            ft.IconButton(
                icon=ft.Icons.PUBLIC,
                tooltip="Worlds",
                on_click=lambda _: page.go("/"),
            ),
            ft.IconButton(
                icon=ft.Icons.BOOK_OUTLINED,
                tooltip="Campaigns",
                on_click=lambda _: page.go("/campaigns"),
            ),
            ft.IconButton(
                icon=ft.Icons.PERSON_OUTLINE,
                tooltip="Characters",
                on_click=lambda _: page.go("/characters"),
            ),
            ft.IconButton(
                icon=ft.Icons.SETTINGS_OUTLINED,
                tooltip="Settings",
                on_click=lambda _: page.go("/settings"),
            ),
        ],
    )
