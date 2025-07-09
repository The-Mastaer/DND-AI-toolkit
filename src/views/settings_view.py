import flet as ft
from src.state import AppState
from src.app_settings import AppSettings


class SettingsView(ft.View):
    """
    A view for managing application settings.

    This view allows users to configure AI model parameters and appearance.
    Settings are loaded from and saved to Flet's `page.client_storage`
    for persistence across sessions.
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

        # --- UI Controls ---
        self.theme_switch = ft.Switch(
            label="Dark Mode",
            on_change=self.toggle_dark_mode,
            value=(self.settings.theme_mode == "dark")
        )

        self.text_model_dropdown = ft.Dropdown(
            label="Text Generation Model",
            value=self.settings.text_model,
            options=[
                ft.dropdown.Option("gemini-2.5-pro"),
                ft.dropdown.Option("gemini-2.5-flash"),
                ft.dropdown.Option("gemini-2.5-flash-lite-preview-06-17"),
            ]
        )

        self.image_model_dropdown = ft.Dropdown(
            label="Image Generation Model",
            value=self.settings.image_model,
            options=[
                ft.dropdown.Option("gemini-2.0-flash-preview-image-generation"),
                ft.dropdown.Option("imagen-4.0-generate-preview-06-06"),
                ft.dropdown.Option("imagen-3.0-generate-002"),
            ]
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
                    ft.Text("Note: API keys are managed in the .env file for security."),
                    self.text_model_dropdown,
                    self.image_model_dropdown,
                    self.temperature_slider,
                    self.top_p_slider,
                    ft.ElevatedButton("Save Settings", on_click=self.save_settings, icon=ft.Icons.SAVE),
                ],
                spacing=15,
                width=600,
                alignment=ft.MainAxisAlignment.START,
            )
        ]

    def toggle_dark_mode(self, e):
        """Event handler to toggle the application's theme and save it."""
        current_theme = "dark" if e.control.value else "light"
        self.page.theme_mode = ft.ThemeMode.DARK if current_theme == "dark" else ft.ThemeMode.LIGHT
        self.settings.theme_mode = current_theme
        self.save_settings(e, show_snackbar=False)  # Save without showing snackbar
        self.page.update()

    def save_settings(self, e, show_snackbar=True):
        """
        Event handler for saving all settings to client storage.

        Args:
            show_snackbar (bool): If True, displays a confirmation message.
        """
        print("SettingsView: Saving settings...")

        # Update settings object from all UI controls
        self.settings.theme_mode = "dark" if self.theme_switch.value else "light"
        self.settings.text_model = self.text_model_dropdown.value
        self.settings.image_model = self.image_model_dropdown.value
        self.settings.temperature = self.temperature_slider.value
        self.settings.top_p = self.top_p_slider.value

        # Persist to client storage
        settings_json = self.settings.to_json()
        self.page.client_storage.set("app_settings", settings_json)

        # Update the global app state
        self.app_state.settings = self.settings

        if show_snackbar:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Settings have been saved."),
                duration=2000
            )
            self.page.snack_bar.open = True

        self.page.update()