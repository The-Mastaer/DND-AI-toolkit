import flet as ft

def AppAppBar(page: ft.Page) -> ft.AppBar:
    """
    Creates and returns a standard AppBar for the application.

    This is a reusable UI component. It centralizes the appearance and
    functionality of the top navigation bar, ensuring consistency across
all views.

    Args:
        page (ft.Page): The Flet page object, used for navigation.

    Returns:
        An ft.AppBar control.
    """
    return ft.AppBar(
        leading=ft.Icon(ft.icons.DRAGON),
        leading_width=40,
        title=ft.Text("D&D AI Toolkit"),
        center_title=False,
        bgcolor=ft.colors.SURFACE_VARIANT,
        actions=[
            ft.IconButton(
                icon=ft.icons.HOME,
                tooltip="Home",
                on_click=lambda _: page.go('/')
            ),
            ft.IconButton(
                icon=ft.icons.BOOK,
                tooltip="Campaigns",
                on_click=lambda _: page.go('/campaigns')
            ),
            ft.IconButton(
                icon=ft.icons.SETTINGS,
                tooltip="Settings",
                on_click=lambda _: page.go('/settings')
            )
        ],
    )