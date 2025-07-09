# src/views/main_menu_view.py

import flet as ft
from typing import TYPE_CHECKING
from ..components.app_bar import AppBar

if TYPE_CHECKING:
    from ..state import AppState

class MainMenuView(ft.View):
    """
    The main menu view, acting as a dashboard and navigation hub.
    """
    def __init__(self, page: ft.Page, state: 'AppState'):
        super().__init__(route="/")
        self.page = page
        self.state = state

        self.app_bar = AppBar(
            title="D&D AI Toolkit",
            page=self.page,
            state=self.state,
        )

        self.controls = [
            self.app_bar,
            ft.Column(
                controls=[
                    ft.ElevatedButton("Worlds", on_click=lambda _: page.go("/worlds")),
                    # Removed "Campaigns" button, as it's now accessed via a world.
                    ft.ElevatedButton("Characters", on_click=lambda _: page.go("/characters"), disabled=True),
                    ft.ElevatedButton("Settings", on_click=lambda _: page.go("/settings")),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
                spacing=20,
            )
        ]