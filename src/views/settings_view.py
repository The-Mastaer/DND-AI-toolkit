# src/views/settings_view.py

import flet as ft
import asyncio
from ..services.supabase_service import supabase
from ..config import THEME_COLORS, AVAILABLE_THEMES, TEXT_MODELS, IMAGE_MODELS, DEFAULT_TEXT_MODEL, DEFAULT_IMAGE_MODEL
from ..prompts import TRANSLATE_LORE_PROMPT, SRD_QUERY_PROMPT


class SettingsView(ft.View):
    """
    View for managing all application settings.
    """

    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.route = "/settings"
        self.appbar = ft.AppBar(title=ft.Text("Settings"), bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST)

        # --- UI Controls ---
        self.api_key_field = ft.TextField(label="Gemini API Key", password=True, can_reveal_password=True)
        self.theme_mode_dropdown = ft.Dropdown(
            label="Theme Mode",
            options=[ft.dropdown.Option(mode.capitalize()) for mode in AVAILABLE_THEMES]
        )
        self.theme_color_dropdown = ft.Dropdown(
            label="Theme Color",
            options=[ft.dropdown.Option(color) for color in THEME_COLORS]
        )
        self.text_model_dropdown = ft.Dropdown(
            label="Text Model",
            options=[ft.dropdown.Option(key, value) for key, value in TEXT_MODELS.items()]
        )
        self.image_model_dropdown = ft.Dropdown(
            label="Image Model",
            options=[ft.dropdown.Option(key, value) for key, value in IMAGE_MODELS.items()]
        )
        self.active_world_dropdown = ft.Dropdown(label="Active World", on_change=self.on_world_selected, expand=True)
        self.active_campaign_dropdown = ft.Dropdown(label="Active Campaign", expand=True)

        self.srd_picker = ft.FilePicker(on_result=self.on_srd_picked)
        self.page.overlay.append(self.srd_picker)

        self.srd_status_text = ft.Text("No SRD document uploaded.")
        self.lore_prompt_field = ft.TextField(label="Lore Master Prompt", value=TRANSLATE_LORE_PROMPT, multiline=True,
                                              min_lines=5)
        self.srd_prompt_field = ft.TextField(label="Rules Lawyer Prompt", value=SRD_QUERY_PROMPT, multiline=True,
                                             min_lines=5)

        self.save_button = ft.ElevatedButton("Save Settings", on_click=self.save_settings_click)
        self.progress_ring = ft.ProgressRing(visible=False)

        # --- LAYOUT ---
        self.controls = [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("General", style=ft.TextThemeStyle.HEADLINE_SMALL),
                        ft.Row([self.theme_mode_dropdown, self.theme_color_dropdown]),
                        ft.Divider(),
                        ft.Text("API Configuration", style=ft.TextThemeStyle.HEADLINE_SMALL),
                        self.api_key_field,
                        ft.Row([self.text_model_dropdown, self.image_model_dropdown]),
                        ft.Divider(),
                        ft.Text("Active Selection", style=ft.TextThemeStyle.HEADLINE_SMALL),
                        ft.Row([self.active_world_dropdown, self.active_campaign_dropdown]),
                        ft.Divider(),
                        ft.Text("Rules Document (SRD)", style=ft.TextThemeStyle.HEADLINE_SMALL),
                        ft.Row([ft.ElevatedButton("Upload SRD PDF", on_click=lambda _: self.srd_picker.pick_files()),
                                self.srd_status_text]),
                        ft.Divider(),
                        ft.Text("Prompt Engineering", style=ft.TextThemeStyle.HEADLINE_SMALL),
                        self.lore_prompt_field,
                        self.srd_prompt_field,
                        ft.Divider(),
                        ft.Row([self.save_button, self.progress_ring])
                    ],
                    spacing=15,
                    scroll=ft.ScrollMode.AUTO,
                ),
                padding=20,
                expand=True,
            )
        ]

    def did_mount(self):
        self.page.run_task(self.load_initial_data)

    async def load_initial_data(self):
        self.progress_ring.visible = True
        self.update()
        try:
            keys_to_fetch = [
                "gemini.api_key", "app.theme_mode", "app.theme_color",
                "gemini.text_model", "gemini.image_model", "active_world_id",
                "srd_document_uploaded", "prompt.lore_master", "prompt.rules_lawyer"
            ]
            tasks = [asyncio.to_thread(self.page.client_storage.get, key) for key in keys_to_fetch]
            results = await asyncio.gather(*tasks, supabase.get_user())

            settings = dict(zip(keys_to_fetch, results[:-1]))
            user = results[-1]

            self.api_key_field.value = settings.get("gemini.api_key") or ""
            self.theme_mode_dropdown.value = settings.get("app.theme_mode", "dark").capitalize()
            self.theme_color_dropdown.value = settings.get("app.theme_color", "blue")
            self.text_model_dropdown.value = settings.get("gemini.text_model", DEFAULT_TEXT_MODEL)
            self.image_model_dropdown.value = settings.get("gemini.image_model", DEFAULT_IMAGE_MODEL)
            self.lore_prompt_field.value = settings.get("prompt.lore_master") or TRANSLATE_LORE_PROMPT
            self.srd_prompt_field.value = settings.get("prompt.rules_lawyer") or SRD_QUERY_PROMPT

            if user:
                worlds_response = await supabase.get_worlds(user.user.id)
                worlds = worlds_response.data if worlds_response else []
                if worlds:
                    self.active_world_dropdown.options = [ft.dropdown.Option(w['id'], w['name']) for w in worlds]
                    if settings.get("active_world_id"):
                        self.active_world_dropdown.value = int(settings.get("active_world_id"))
                        await self.on_world_selected()

            if settings.get("srd_document_uploaded"):
                self.srd_status_text.value = "SRD document is uploaded."
                self.srd_status_text.color = ft.Colors.GREEN
        except Exception as e:
            print(f"Error loading settings: {e}")
        finally:
            self.progress_ring.visible = False
            self.update()

    async def on_world_selected(self, e=None):
        world_id = self.active_world_dropdown.value
        if not world_id: return
        self.active_campaign_dropdown.options = []
        campaigns_response = await supabase.get_campaigns_for_world(world_id)
        campaigns = campaigns_response.data if campaigns_response else []
        if campaigns:
            self.active_campaign_dropdown.options = [
                ft.dropdown.Option(c['id'], c.get('name', {}).get('en', f"Campaign {c['id']}")) for c in campaigns]
            active_campaign_id = await asyncio.to_thread(self.page.client_storage.get, "active_campaign_id")
            if active_campaign_id:
                self.active_campaign_dropdown.value = int(active_campaign_id)
        self.update()

    async def on_srd_picked(self, e: ft.FilePickerResultEvent):
        if not e.files: return
        self.progress_ring.visible = True
        self.update()
        picked_file = e.files[0]
        with open(picked_file.path, "rb") as f:
            file_bytes = f.read()
        try:
            user = await supabase.get_user()
            if not user: raise Exception("Authentication error.")
            bucket_path = f"{user.user.id}/srd.pdf"
            await supabase.upload_file("documents", bucket_path, file_bytes, "application/pdf")
            await asyncio.to_thread(self.page.client_storage.set, "srd_document_uploaded", True)
            await asyncio.to_thread(self.page.client_storage.set, "srd_document_bucket_path", bucket_path)
            self.srd_status_text.value = "SRD uploaded successfully!"
            self.srd_status_text.color = ft.Colors.GREEN
        except Exception as ex:
            self.srd_status_text.value = f"Upload failed: {ex}"
            self.srd_status_text.color = ft.Colors.RED
        finally:
            self.progress_ring.visible = False
            self.update()

    async def save_settings_click(self, e):
        self.progress_ring.visible = True
        self.update()
        try:
            settings_to_save = {
                "gemini.api_key": self.api_key_field.value,
                "app.theme_mode": self.theme_mode_dropdown.value.lower(),
                "app.theme_color": self.theme_color_dropdown.value,
                "gemini.text_model": self.text_model_dropdown.value,
                "gemini.image_model": self.image_model_dropdown.value,
                "active_world_id": self.active_world_dropdown.value,
                "active_campaign_id": self.active_campaign_dropdown.value,
                "prompt.lore_master": self.lore_prompt_field.value,
                "prompt.rules_lawyer": self.srd_prompt_field.value,
            }
            tasks = [asyncio.to_thread(self.page.client_storage.set, key, value) for key, value in
                     settings_to_save.items()]
            await asyncio.gather(*tasks)

            self.page.theme_mode = settings_to_save["app.theme_mode"]
            self.page.theme = ft.Theme(color_scheme_seed=settings_to_save["app.theme_color"])

            self.page.snack_bar = ft.SnackBar(content=ft.Text("Settings saved!"), bgcolor=ft.Colors.GREEN)
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(content=ft.Text(f"Error saving: {ex}"), bgcolor=ft.Colors.RED)
        finally:
            self.progress_ring.visible = False
            self.page.snack_bar.open = True
            self.update()
