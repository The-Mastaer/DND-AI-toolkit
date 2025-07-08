import flet as ft
from src.state import AppState

def MainMenuView(page: ft.Page, app_state: AppState) -> ft.View:
    """
    The main menu view of the application.

    This view serves as the landing page, providing top-level navigation
    to the different modules of the toolkit. It now correctly directs the user
    to the "World Manager".

    Args:
        page (ft.Page): The Flet page object.
        app_state (AppState): The global state of the application.

    Returns:
        An ft.View object representing the main menu screen.
    """
    welcome_message = "Welcome, Dungeon Master!"

    return ft.View(
        route="/",
        controls=[
            ft.Column(
                [
                    ft.Text(welcome_message, size=32, weight=ft.FontWeight.BOLD),
                    ft.Text("Select a module to begin:", size=18),
                    ft.ElevatedButton(
                        text="World Manager",
                        icon=ft.Icons.PUBLIC, # Corrected: ft.Icons
                        on_click=lambda _: page.go("/worlds"),
                        width=250
                    ),
                    ft.ElevatedButton(
                        text="Settings",
                        icon=ft.Icons.SETTINGS, # Corrected: ft.Icons
                        on_click=lambda _: page.go("/settings"),
                        width=250
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
                expand=True,
            )
        ],
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
