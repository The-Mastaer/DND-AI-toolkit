# src/components/app_bar.py

import flet as ft
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..state import AppState


class AppBar(ft.AppBar):
    """
    A custom AppBar component for consistent navigation across the app.
    """

    def __init__(self, title: str, page: ft.Page, state: 'AppState', show_back_button: bool = False):
        """
        Initializes the AppBar.

        Args:
            title: The text to display in the AppBar's title.
            page: The Flet Page object to handle navigation.
            state: The application's state object.
            show_back_button: If True, shows a back arrow instead of the main menu icon.
        """
        super().__init__()
        self.page = page
        self.state = state

        self.leading = ft.IconButton(
            ft.Icons.ARROW_BACK if show_back_button else ft.Icons.MENU,
            on_click=self.handle_leading_action
        )
        self.leading_width = 40
        self.title = ft.Text(title)
        self.center_title = False

        # Corrected bgcolor to a valid ft.Colors constant.
        # SURFACE_VARIANT is not a direct color, but part of the theme engine.
        # SURFACE_CONTAINER_HIGHEST is a valid and appropriate replacement.
        self.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST

        self.actions = [
            ft.IconButton(ft.Icons.HOME, on_click=lambda _: self.page.go("/")),
            ft.IconButton(ft.Icons.SETTINGS, on_click=lambda _: self.page.go("/settings")),
        ]

    def handle_leading_action(self, e: ft.ControlEvent):
        """Handles the click on the leading icon (back or menu)."""
        # A simple back navigation for now
        if self.page.route != "/":
            self.page.go("/")
        # In a more complex app, this could open a navigation drawer.