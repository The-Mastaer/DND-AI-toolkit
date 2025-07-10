import flet as ft
import asyncio
from ..services.supabase_service import supabase
from ..config import (
    SUPPORTED_LANGUAGES,
    TEXT_MODELS,
    IMAGE_MODELS,
    DEFAULT_TEXT_MODEL,
    DEFAULT_IMAGE_MODEL
)
from .. import prompts


class SettingsView(ft.View):
    """
    A comprehensive settings view organized into tabs for managing the
    application's active context, appearance, AI models, and prompts.
    All settings are persisted in client storage for a seamless user experience.
    """

    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.route = "/settings"
        self.appbar = ft.AppBar(title=ft.Text("Settings"), bgcolor="surfaceVariant")

        # --- UI Controls ---

        # Tab 1: Active Context
        self.language_dropdown = ft.Dropdown(label="Active Language", on_change=self.context_changed, width=400)
        self.world_dropdown = ft.Dropdown(label="Active World", on_change=self.world_changed, disabled=True, width=400)
        self.campaign_dropdown = ft.Dropdown(label="Active Campaign", on_change=self.context_changed, disabled=True,
                                             width=400)
        self.save_context_button = ft.FilledButton("Save Context", on_click=self.save_context, disabled=True)
        self.current_selection_text = ft.Text("No active campaign set.")

        # Tab 2: Appearance
        self.theme_mode_switch = ft.Switch(label="Dark Mode")
        self.color_scheme_dropdown = ft.Dropdown(label="Color Scheme", options=[ft.dropdown.Option(c) for c in
                                                                                ["blue", "green", "red", "indigo",
                                                                                 "orange", "teal"]])
        self.save_appearance_button = ft.FilledButton("Save Appearance", on_click=self.save_appearance_settings)
        self.appearance_save_status = ft.Text()  # Confirmation text

        # Tab 3: AI Models
        self.text_model_dropdown = ft.Dropdown(label="Text Generation Model",
                                               options=[ft.dropdown.Option(k, v) for k, v in TEXT_MODELS.items()])
        self.image_model_dropdown = ft.Dropdown(label="Image Generation Model",
                                                options=[ft.dropdown.Option(k, v) for k, v in IMAGE_MODELS.items()])
        self.save_models_button = ft.FilledButton("Save Model Settings", on_click=self.save_models)
        self.models_save_status = ft.Text()  # Confirmation text

        # Tab 4: Prompts
        self.prompt_fields = {}
        prompt_controls = []
        for prompt_name, prompt_text in vars(prompts).items():
            if not prompt_name.startswith("__") and isinstance(prompt_text, str):
                field = ft.TextField(label=prompt_name, value=prompt_text, multiline=True, min_lines=3, max_lines=5)
                self.prompt_fields[prompt_name] = field
                prompt_controls.append(field)
        self.save_prompts_button = ft.FilledButton("Save Custom Prompts", on_click=self.save_prompts)
        self.prompts_save_status = ft.Text()  # Confirmation text
        prompt_controls.extend([self.save_prompts_button, self.prompts_save_status])

        # Tab 5: Advanced
        self.reset_button = ft.FilledButton("Reset All Settings", on_click=self.reset_all_settings,
                                            icon=ft.Icons.WARNING, color=ft.Colors.ON_ERROR, bgcolor=ft.Colors.ERROR)

        # --- Assembling the View with Tabs ---
        self.controls = [
            ft.Tabs(
                selected_index=0,
                animation_duration=300,
                tabs=[
                    ft.Tab("Active Context", icon=ft.Icons.FILTER_CENTER_FOCUS, content=self.build_tab_content(
                        [self.language_dropdown, self.world_dropdown, self.campaign_dropdown, self.save_context_button,
                         ft.Divider(), self.current_selection_text])),
                    ft.Tab("Appearance", icon=ft.Icons.BRUSH, content=self.build_tab_content(
                        [self.theme_mode_switch, self.color_scheme_dropdown, self.save_appearance_button,
                         self.appearance_save_status])),
                    ft.Tab("AI Models", icon=ft.Icons.SMART_TOY, content=self.build_tab_content(
                        [self.text_model_dropdown, self.image_model_dropdown, self.save_models_button,
                         self.models_save_status])),
                    ft.Tab("Prompts", icon=ft.Icons.EDIT_DOCUMENT,
                           content=self.build_tab_content(prompt_controls, scroll=ft.ScrollMode.AUTO)),
                    ft.Tab("Advanced", icon=ft.Icons.WARNING_AMBER_ROUNDED, content=self.build_tab_content(
                        [ft.Text("Warning: This will reset all saved settings to their defaults."),
                         self.reset_button])),
                ],
                expand=True,
            )
        ]

    def build_tab_content(self, controls, scroll=None):
        return ft.Container(content=ft.Column(controls, spacing=15, scroll=scroll), padding=20)

    def did_mount(self):
        self.load_all_settings()

    def load_all_settings(self):
        self.load_context_settings()
        self.load_appearance_settings()
        self.load_model_settings()
        self.load_custom_prompts()

    # --- Context Tab Logic ---
    def load_context_settings(self):
        self.language_dropdown.options = [ft.dropdown.Option(c, n) for c, n in SUPPORTED_LANGUAGES.items()]
        self.language_dropdown.value = self.page.client_storage.get("active_language_code") or "en"
        self.load_worlds()
        self.update_current_selection_text()

    def load_worlds(self):
        try:
            response = supabase.table('worlds').select('id, name').execute()
            if response.data:
                self.world_dropdown.options = [ft.dropdown.Option(w['id'], w['name']) for w in response.data]
                self.world_dropdown.disabled = False
                active_world_id = self.page.client_storage.get("active_world_id")
                if active_world_id:
                    self.world_dropdown.value = int(active_world_id)
                    self.load_campaigns(active_world_id)
            self.update()
        except Exception as e:
            print(f"Error loading worlds: {e}")

    def load_campaigns(self, world_id):
        try:
            response = supabase.table('campaigns').select('id, name').eq('world_id', world_id).execute()
            self.campaign_dropdown.options.clear()
            if response.data:
                lang_code = self.language_dropdown.value
                for c in response.data:
                    self.campaign_dropdown.options.append(
                        ft.dropdown.Option(c['id'], c.get('name', {}).get(lang_code, f"Campaign {c['id']}")))
                self.campaign_dropdown.disabled = False
                active_campaign_id = self.page.client_storage.get("active_campaign_id")
                if active_campaign_id:
                    self.campaign_dropdown.value = int(active_campaign_id)
            self.update()
        except Exception as e:
            print(f"Error loading campaigns: {e}")

    def language_changed(self, e):
        if self.world_dropdown.value:
            self.load_campaigns(self.world_dropdown.value)
        self.context_changed(e)

    def world_changed(self, e):
        self.campaign_dropdown.value = None;
        self.campaign_dropdown.disabled = True
        self.load_campaigns(self.world_dropdown.value)
        self.context_changed(e)

    def context_changed(self, e):
        self.save_context_button.disabled = not all(
            [self.language_dropdown.value, self.world_dropdown.value, self.campaign_dropdown.value])
        self.update()

    async def save_context(self, e):
        self.page.client_storage.set("active_language_code", self.language_dropdown.value)
        self.page.client_storage.set("active_world_id", self.world_dropdown.value)
        self.page.client_storage.set("active_campaign_id", self.campaign_dropdown.value)
        self.update_current_selection_text()
        self.page.snack_bar = ft.SnackBar(content=ft.Text("Active context saved!"), bgcolor=ft.Colors.GREEN_700)
        self.page.snack_bar.open = True
        self.page.update()

    def update_current_selection_text(self):
        world_id = self.page.client_storage.get("active_world_id")
        campaign_id = self.page.client_storage.get("active_campaign_id")
        self.current_selection_text.value = f"Current Context: World ID {world_id}, Campaign ID {campaign_id}" if world_id and campaign_id else "No active campaign set."
        self.update()

    # --- Appearance Tab Logic ---
    def load_appearance_settings(self):
        theme_mode_str = self.page.client_storage.get("theme_mode") or "system"
        self.theme_mode_switch.value = theme_mode_str == "dark"
        self.color_scheme_dropdown.value = self.page.client_storage.get("color_scheme") or "blue"
        self.update()

    async def save_appearance_settings(self, e):
        new_mode_str = "dark" if self.theme_mode_switch.value else "light"
        self.page.theme_mode = ft.ThemeMode(new_mode_str)
        color = self.color_scheme_dropdown.value
        self.page.theme = self.page.dark_theme = ft.Theme(color_scheme_seed=color)
        self.page.client_storage.set("theme_mode", new_mode_str)
        self.page.client_storage.set("color_scheme", color)
        self.appearance_save_status.value = "Appearance settings saved!"
        self.page.update()
        await asyncio.sleep(2)
        self.appearance_save_status.value = ""
        self.page.update()

    # --- AI Models Tab Logic ---
    def load_model_settings(self):
        self.text_model_dropdown.value = self.page.client_storage.get("text_model") or DEFAULT_TEXT_MODEL
        self.image_model_dropdown.value = self.page.client_storage.get("image_model") or DEFAULT_IMAGE_MODEL
        self.update()

    async def save_models(self, e):
        self.page.client_storage.set("text_model", self.text_model_dropdown.value)
        self.page.client_storage.set("image_model", self.image_model_dropdown.value)
        self.models_save_status.value = "Model settings saved!"
        self.page.update()
        await asyncio.sleep(2)
        self.models_save_status.value = ""
        self.page.update()

    # --- Prompts Tab Logic ---
    def load_custom_prompts(self):
        for name, field in self.prompt_fields.items():
            field.value = self.page.client_storage.get(f"prompt.{name}") or getattr(prompts, name, "")
        self.update()

    async def save_prompts(self, e):
        for name, field in self.prompt_fields.items():
            self.page.client_storage.set(f"prompt.{name}", field.value)
        self.prompts_save_status.value = "Custom prompts saved!"
        self.page.update()
        await asyncio.sleep(2)
        self.prompts_save_status.value = ""
        self.page.update()

    # --- Advanced Tab Logic ---
    async def reset_all_settings(self, e):
        keys_to_remove = [
            "active_language_code", "active_world_id", "active_campaign_id",
            "theme_mode", "color_scheme",
            "text_model", "image_model"
        ]
        for key in keys_to_remove:
            if self.page.client_storage.contains_key(key):
                self.page.client_storage.remove(key)

        for name in self.prompt_fields.keys():
            if self.page.client_storage.contains_key(f"prompt.{name}"):
                self.page.client_storage.remove(f"prompt.{name}")

        self.load_all_settings()

        self.page.snack_bar = ft.SnackBar(content=ft.Text("All settings have been reset to default."),
                                          bgcolor=ft.Colors.BLUE_GREY_700)
        self.page.snack_bar.open = True
        self.page.update()
