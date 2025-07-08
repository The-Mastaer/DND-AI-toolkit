import flet as ft
from src.state import AppState
from src.app_settings import AppSettings


class SettingsView(ft.View):
    """
    A view for managing application settings.

    This view allows users to configure AI model parameters. Settings are
    loaded from and saved to Flet's `page.client_storage` for persistence.
    API keys are not managed here for security reasons.
    """

    def __init__(self, page: ft.Page, app_state: AppState):
        super().__init__(
            route="/settings",
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            vertical_alignment=ft.MainAxisAlignment.START
        )
        self.page = page
        self.app_state = app_state
        self.settings = app_state.settings

        # UI Controls
        self.theme_switch = ft.Switch(
            label="Dark Mode",
            on_change=self.toggle_dark_mode,
            value=page.theme_mode == ft.ThemeMode.DARK
        )

        self.temperature_slider = ft.Slider(
            min=0, max=1, divisions=20, label="Temperature: {value}",
            value=self.settings.temperature
        )

        self.top_p_slider = ft.Slider(
            min=0, max=1, divisions=20, label="Top P: {value}",
            value=self.settings.top_p
        )

        self.controls = [
            ft.Column(
                [
                    ft.Text("Settings", size=32, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    ft.Text("Appearance", size=18, weight=ft.FontWeight.BOLD),
                    self.theme_switch,
                    ft.Divider(),
                    ft.Text("AI Configuration", size=18, weight=ft.FontWeight.BOLD),
                    ft.Text("Note: API keys are managed in the .env file in the project root for security."),
                    self.temperature_slider,
                    self.top_p_slider,
                    ft.ElevatedButton("Save Settings", on_click=self.save_settings),
                ],
                spacing=15,
                width=600,
                alignment=ft.MainAxisAlignment.START,
            )
        ]

    def toggle_dark_mode(self, e):
        """Event handler to toggle the application's theme."""
        self.page.theme_mode = (
            ft.ThemeMode.DARK
            if self.page.theme_mode == ft.ThemeMode.LIGHT
            else ft.ThemeMode.LIGHT
        )
        self.page.update()

    def save_settings(self, e):
        """Event handler for saving the settings to client storage."""
        print("SettingsView: Saving settings...")

        # Update settings object from UI controls
        self.settings.temperature = self.temperature_slider.value
        self.settings.top_p = self.top_p_slider.value

        # Persist to client storage
        settings_json = self.settings.to_json()
        self.page.client_storage.set("app_settings", settings_json)

        # Update the global app state
        self.app_state.settings = self.settings

        self.page.snack_bar = ft.SnackBar(
            content=ft.Text("Settings have been saved."),
            duration=2000
        )
        self.page.snack_bar.open = True
        self.page.update()

