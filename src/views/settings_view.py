# src/views/settings_view.py

import flet as ft
from services.supabase_service import supabase
from services.gemini_service import GeminiService
from config import THEME_COLORS, TEXT_MODELS, DEFAULT_TEXT_MODEL, IMAGE_MODELS, DEFAULT_IMAGE_MODEL
import asyncio


class SettingsView(ft.View):
    """
    A view for configuring application settings, such as theme,
    active world/campaign, and AI model/prompts.
    """

    def __init__(self, page: ft.Page, gemini_service: GeminiService):
        """
        Initializes the SettingsView.

        Args:
            page (ft.Page): The Flet page object.
            gemini_service (GeminiService): The singleton instance of the Gemini service.
        """
        super().__init__()
        self.page = page
        self.route = "/settings"
        self.gemini_service = gemini_service

        self.appbar = ft.AppBar(
            title=ft.Text("Settings"),
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda _: self.page.go("/")),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            actions=[ft.IconButton(icon=ft.Icons.LOGOUT, on_click=self.logout_clicked, tooltip="Logout")]
        )


        # --- UI Controls ---
        # Appearance Card
        self.theme_mode_switch = ft.Switch(label="Dark Mode")
        self.theme_color_dropdown = ft.Dropdown(
            label="Theme Color",
            options=[ft.dropdown.Option(color) for color in THEME_COLORS],
            expand=True
        )
        appearance_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.ListTile(leading=ft.Icon(ft.Icons.COLOR_LENS), title=ft.Text("Appearance")),
                    self.theme_mode_switch,
                    self.theme_color_dropdown,
                ]),
                padding=16
            )
        )

        # Active Selections Card
        self.worlds_dropdown = ft.Dropdown(label="Active World", on_change=self.world_changed, expand=True)
        self.campaigns_dropdown = ft.Dropdown(label="Active Campaign", expand=True)
        selections_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.ListTile(leading=ft.Icon(ft.Icons.PUBLIC), title=ft.Text("Active Selections")),
                    self.worlds_dropdown,
                    self.campaigns_dropdown,
                ]),
                padding=16
            )
        )

        # AI Configuration Card
        self.model_dropdown = ft.Dropdown(
            label="AI Model",
            # DEBUG FIX: Use the TEXT_MODELS dictionary from config
            options=[ft.dropdown.Option(key, text) for key, text in TEXT_MODELS.items()],
            expand=True
        )
        self.model_dropdown_pic = ft.Dropdown(
            label="AI Model",
            # DEBUG FIX: Use the TEXT_MODELS dictionary from config
            options=[ft.dropdown.Option(key, text) for key, text in IMAGE_MODELS.items()],
            expand=True
        )
        self.rules_lawyer_prompt_field = ft.TextField(
            label="Rules Lawyer System Prompt",
            multiline=True,
            min_lines=3
        )

        self.upload_status = ft.Text(size=12)
        ai_config_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.ListTile(leading=ft.Icon(ft.Icons.SMART_TOY), title=ft.Text("AI Configuration")),
                    self.model_dropdown,
                    self.model_dropdown_pic,
                    self.rules_lawyer_prompt_field,
                ]),
                padding=16
            )
        )

        self.save_button = ft.FilledButton("Save All Settings", icon=ft.Icons.SAVE, on_click=self.save_settings_clicked)

        self.controls = [
            ft.Column(
                [
                    appearance_card,
                    selections_card,
                    ai_config_card,
                    ft.Row([self.save_button], alignment=ft.MainAxisAlignment.END)
                ],
                spacing=20,
                width=600,
                alignment=ft.MainAxisAlignment.START,
                scroll=ft.ScrollMode.ADAPTIVE
            )
        ]
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.scroll = ft.ScrollMode.ADAPTIVE

    def did_mount(self):
        """Load initial settings when the view is displayed."""
        self.page.run_task(self.load_settings)

    async def load_settings(self):
        """Fetches and applies saved settings from client storage and the database."""
        # Define keys and their default values
        settings_map = {
            "app.theme_mode": (self.theme_mode_switch, "value", "dark"),
            "app.theme_color": (self.theme_color_dropdown, "value", "blue"),
            "ai.model": (self.model_dropdown, "value", DEFAULT_TEXT_MODEL),
            "picture.model": (self.model_dropdown_pic, "value", DEFAULT_IMAGE_MODEL),
            "active_world_id": (self.worlds_dropdown, "value", None),
            "active_campaign_id": (self.campaigns_dropdown, "value", None),
        }

        # Fetch all settings from client storage
        keys = list(settings_map.keys())
        tasks = [asyncio.to_thread(self.page.client_storage.get, key) for key in keys]
        results = await asyncio.gather(*tasks)
        stored_settings = dict(zip(keys, results))

        # Apply settings to controls
        for key, (control, prop, default) in settings_map.items():
            value = stored_settings.get(key) or default
            if key == "app.theme_mode":
                setattr(control, prop, value == "dark")
            elif value is not None:
                setattr(control, prop, int(value) if 'id' in key else value)

        # Load worlds dropdown
        try:
            worlds_response = await supabase.get_all_worlds()
            if worlds_response.data:
                self.worlds_dropdown.options = [ft.dropdown.Option(w['id'], w['name']) for w in worlds_response.data]
                if self.worlds_dropdown.value:
                    await self.load_campaigns_for_world(int(self.worlds_dropdown.value))
        except Exception as e:
            print(f"Error loading worlds: {e}")

        self.update()

    async def save_settings_clicked(self, e):
        """Saves all current settings to client storage."""
        settings_to_save = {
            "app.theme_mode": "dark" if self.theme_mode_switch.value else "light",
            "app.theme_color": self.theme_color_dropdown.value,
            "ai.model": self.model_dropdown.value,
            "picture_model": self.model_dropdown.value,
            "prompt.rules_lawyer": self.rules_lawyer_prompt_field.value,
            "active_world_id": self.worlds_dropdown.value,
            "active_campaign_id": self.campaigns_dropdown.value,
        }

        tasks = [asyncio.to_thread(self.page.client_storage.set, key, value) for key, value in settings_to_save.items()
                 if value is not None]
        await asyncio.gather(*tasks)

        # Apply theme changes immediately
        self.page.theme_mode = settings_to_save["app.theme_mode"]
        self.page.theme = ft.Theme(color_scheme_seed=settings_to_save["app.theme_color"])

        self.page.snack_bar = ft.SnackBar(ft.Text("Settings saved!"), bgcolor=ft.Colors.GREEN)
        self.page.snack_bar.open = True
        self.page.update()

    async def world_changed(self, e):
        """Handles active world change."""
        world_id = int(e.control.value)
        # Clear active campaign when world changes
        self.campaigns_dropdown.value = None
        await self.load_campaigns_for_world(world_id)
        self.update()

    async def load_campaigns_for_world(self, world_id):
        """Loads campaigns for the selected world into the dropdown."""
        try:
            campaigns_response = await supabase.get_campaigns_for_world(world_id)
            if campaigns_response.data:
                self.campaigns_dropdown.options = [ft.dropdown.Option(c['id'], c['name'].get('en', 'Unnamed')) for c in
                                                   campaigns_response.data]
                # Keep existing selection if it's valid for the new world
                active_campaign_id = await asyncio.to_thread(self.page.client_storage.get, "active_campaign_id")
                if active_campaign_id and any(
                        opt.key == int(active_campaign_id) for opt in self.campaigns_dropdown.options):
                    self.campaigns_dropdown.value = int(active_campaign_id)
                else:
                    self.campaigns_dropdown.value = None
            else:
                self.campaigns_dropdown.options = []
                self.campaigns_dropdown.value = None
        except Exception as e:
            print(f"Error loading campaigns: {e}")
            self.campaigns_dropdown.options = []
        self.update()

    async def logout_clicked(self, e):
        """Logs the user out and clears the session."""
        await supabase.client.auth.sign_out()
        await asyncio.to_thread(self.page.client_storage.remove, "supabase.session")
        self.page.go("/login")
