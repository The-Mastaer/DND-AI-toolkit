import flet as ft
from ..app_settings import AppSettings


class SettingsView(ft.Column):
    """
    A view for managing application settings.
    Inherits from ft.Column to structure its content vertically.
    """

    def __init__(self):
        super().__init__()
        self.expand = True
        self.spacing = 20

        self.app_settings = AppSettings()

        self.api_key_field = ft.TextField(
            label="Gemini API Key",
            password=True,
            can_reveal_password=True
        )
        self.theme_mode_dropdown = ft.Dropdown(
            label="Theme",
            options=[
                ft.dropdown.Option("light", "Light"),
                ft.dropdown.Option("dark", "Dark"),
                ft.dropdown.Option("system", "System"),
            ],
        )

        # Define the layout in the constructor
        self.controls = [
            ft.Row(
                [ft.Text("Settings", style=ft.TextThemeStyle.HEADLINE_MEDIUM)],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Divider(),
            self.api_key_field,
            self.theme_mode_dropdown,
            ft.Row(
                [
                    ft.ElevatedButton(
                        text="Save Settings",
                        icon=ft.Icons.SAVE_OUTLINED,
                        on_click=self._save_settings
                    )
                ],
                alignment=ft.MainAxisAlignment.END
            )
        ]

    def did_mount(self):
        """
        Called when the control is added to the page.
        """
        self._load_settings()

    def _load_settings(self):
        """
        Loads settings from the AppSettings object and updates the UI controls.
        """
        self.app_settings.load_settings()
        self.api_key_field.value = self.app_settings.get_setting('api_key', '')
        self.theme_mode_dropdown.value = self.app_settings.get_setting('theme', 'dark')
        self.update()

    def _save_settings(self, e):
        """
        Saves the current values from the UI controls to the settings file.
        """
        self.app_settings.set_setting('api_key', self.api_key_field.value)
        self.app_settings.set_setting('theme', self.theme_mode_dropdown.value)
        self.app_settings.save_settings()

        self.page.snack_bar = ft.SnackBar(
            content=ft.Text("Settings saved successfully!"),
            duration=2000
        )
        self.page.snack_bar.open = True

        self.page.theme_mode = self.theme_mode_dropdown.value
        self.page.update()
