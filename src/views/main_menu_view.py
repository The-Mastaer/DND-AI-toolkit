import flet as ft
from src.state import AppState


def MainMenuView(page: ft.Page, app_state: AppState) -> ft.View:
    """
    The main menu view of the application.

    This view serves as the landing page, providing top-level navigation
    to the different modules of the toolkit.

    Args:
        page (ft.Page): The Flet page object.
        app_state (AppState): The global state of the application.

    Returns:
        An ft.View object representing the main menu screen.
    """

    # This is a simple demonstration of accessing a service from the app_state.
    # We could, for example, have Gemini generate a "welcome" message.
    welcome_message = "Welcome, Dungeon Master!"
    if app_state.gemini_service:
        # Note: In a real app, you wouldn't block the UI thread like this.
        # You'd use page.run_thread_safe or similar for long-running tasks.
        # For a quick, one-off generation, this might be acceptable.
        # welcome_message = app_state.gemini_service.generate_text("Generate a short, epic welcome for a Dungeon Master starting the D&D AI Toolkit.")
        pass  # Disabling for now to keep UI snappy on startup.

    return ft.View(
        route="/",
        controls=[
            ft.Column(
                [
                    ft.Text(welcome_message, size=32, weight=ft.FontWeight.BOLD),
                    ft.Text("Select a module to begin:", size=18),
                    ft.ElevatedButton(
                        text="Campaign Manager",
                        icon=ft.icons.BOOK,
                        on_click=lambda _: page.go("/campaigns"),
                        width=250
                    ),
                    ft.ElevatedButton(
                        text="Settings",
                        icon=ft.icons.SETTINGS,
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