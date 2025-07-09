# src/views/settings_view.py

import flet as ft
from ..state import AppState
from ..components.app_bar import AppBar
from ..app_settings import AppSettings


class SettingsView(ft.View):
    """
    The view for managing application settings.
    """

    def __init__(self, page: ft.Page, state: AppState, settings: AppSettings):
        super().__init__(route="/settings")
        self.page = page
        self.state = state
        self.settings = settings

        self.app_bar = AppBar(
            title="Settings",
            page=self.page,
            state=self.state,
            show_back_button=True
        )

        # --- Controls ---
        self.api_key_field = ft.TextField(
            label="Gemini API Key",
            password=True,
            value="**************",
            read_only=True,
            tooltip="API Key is loaded from your .env file and cannot be changed here."
        )

        self.theme_switch = ft.Switch(
            label="Dark Mode",
            on_change=self.toggle_theme
        )

        self.text_model_dropdown = ft.Dropdown(
            label="AI Text Model",
            options=[ft.dropdown.Option(model) for model in self.state.available_text_models],
            on_change=self.text_model_changed,
            tooltip="Select the Gemini model for text generation"
        )

        self.image_model_dropdown = ft.Dropdown(
            label="AI Image Model",
            options=[ft.dropdown.Option(model) for model in self.state.available_image_models],
            on_change=self.image_model_changed,
            tooltip="Select the model for image generation"
        )

        self.save_button = ft.ElevatedButton(
            text="Save Settings",
            icon=ft.Icons.SAVE,
            on_click=self.save_settings_clicked
        )

        self.controls = [
            self.app_bar,
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("AI Configuration", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                        ft.Divider(),
                        self.api_key_field,
                        self.text_model_dropdown,
                        self.image_model_dropdown,
                        ft.Divider(),
                        ft.Text("Appearance", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                        self.theme_switch,
                        ft.Divider(),
                        ft.Row([self.save_button], alignment=ft.MainAxisAlignment.END),
                    ],
                    spacing=15,
                ),
                padding=20,
                expand=True,
            )
        ]

        self.on_mount = self.sync_controls_with_state

    def sync_controls_with_state(self, e=None):
        """Ensure UI controls reflect the current application state."""
        print("SettingsView: sync_controls_with_state called.")
        self.theme_switch.value = self.state.theme_mode == "dark"
        self.text_model_dropdown.value = self.state.selected_text_model
        self.image_model_dropdown.value = self.state.selected_image_model
        print(
            f"SettingsView: Synced dropdowns to '{self.state.selected_text_model}' and '{self.state.selected_image_model}'.")
        self.update()

    def toggle_theme(self, e: ft.ControlEvent):
        """Updates the theme in the UI and state, but does not save yet."""
        new_mode = "dark" if e.control.value else "light"
        print(f"SettingsView: Theme toggled to {new_mode}.")
        self.page.theme_mode = new_mode.upper()
        self.state.theme_mode = new_mode
        self.page.update()

    def text_model_changed(self, e: ft.ControlEvent):
        """Updates the selected text model in the state."""
        self.state.selected_text_model = e.control.value
        print(f"SettingsView: Text model changed in state to {self.state.selected_text_model}.")

    def image_model_changed(self, e: ft.ControlEvent):
        """Updates the selected image model in the state."""
        self.state.selected_image_model = e.control.value
        print(f"SettingsView: Image model changed in state to {self.state.selected_image_model}.")

    def save_settings_clicked(self, e: ft.ControlEvent):
        """Saves all current settings to the settings file."""
        print("SettingsView: 'Save' button clicked.")
        try:
            self.settings.save_settings(self.state)
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Settings saved successfully!"),
                bgcolor=ft.Colors.GREEN_700
            )
            print("SettingsView: Settings saved successfully.")
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error saving settings: {ex}"),
                bgcolor=ft.Colors.RED_700
            )
            print(f"SettingsView: Error saving settings - {ex}")

        self.page.snack_bar.open = True
        self.page.update()
