# src/views/character_form_view.py

import flet as ft
from services.supabase_service import supabase
from services.gemini_service import GeminiService
from prompts import GENERATE_NPC_PROMPT, GENERATE_PORTRAIT_PROMPT
from config import (
    DND_RACES, DND_CLASSES, DND_BACKGROUNDS,
    DND_ENVIRONMENTS, DND_HOSTILITIES, DND_RARITIES,
    DEFAULT_TEXT_MODEL, DEFAULT_IMAGE_MODEL
)
from components.ui_components import create_compact_textfield, create_compact_dropdown
import json
import asyncio
import random
import time


class CharacterFormView(ft.View):
    """
    A full-page view for creating and editing characters, with a two-column layout
    and integrated AI generation for both data and portraits.
    """

    def __init__(self, page: ft.Page, gemini_service: GeminiService, character_id=None, campaign_id=None):
        """
        Initializes the CharacterFormView.
        """
        super().__init__()
        self.page = page
        self.character_id = character_id
        self.campaign_id = campaign_id
        self.is_edit_mode = character_id is not None
        self.gemini_service = gemini_service
        self.portrait_url = None

        self.file_picker = ft.FilePicker(on_result=self.on_file_picker_result)
        self.page.overlay.append(self.file_picker)

        self.route = f"/character_edit/{self.character_id}" if self.is_edit_mode else f"/character_edit/new/{self.campaign_id}"
        self.appbar = ft.AppBar(
            title=ft.Text("Edit Character" if self.is_edit_mode else "Create New Character"),
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=self.go_back),
            actions=[ft.IconButton(icon=ft.Icons.SAVE, on_click=self.save_character_click, tooltip="Save Character")],
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        )
        self.scroll = ft.ScrollMode.ADAPTIVE

        self.name_field = create_compact_textfield("Name")
        self.appearance_field = create_compact_textfield("Appearance", multiline=True, min_lines=4)
        self.personality_field = create_compact_textfield("Personality", multiline=True, min_lines=4)
        self.backstory_field = create_compact_textfield("Backstory", multiline=True, min_lines=4)
        self.plot_hooks_field = create_compact_textfield("Plot Hooks", multiline=True, min_lines=3)
        self.roleplaying_tips_field = create_compact_textfield("Roleplaying Tips", multiline=True, min_lines=3)

        self.race_dropdown = create_compact_dropdown("Race", DND_RACES, expand=True)
        self.class_dropdown = create_compact_dropdown("Class", DND_CLASSES, expand=True)
        self.environment_dropdown = create_compact_dropdown("Environment", DND_ENVIRONMENTS, expand=True)
        self.hostility_dropdown = create_compact_dropdown("Hostility", DND_HOSTILITIES, expand=True)
        self.rarity_dropdown = create_compact_dropdown("Rarity", DND_RARITIES, expand=True)
        self.background_dropdown = create_compact_dropdown("Background", DND_BACKGROUNDS, expand=True)
        self.custom_prompt_field = create_compact_textfield("Custom Prompt / Instructions", multiline=True, min_lines=3)
        self.generate_npc_button = ft.FilledButton("Generate with AI", on_click=self.generate_npc_click)
        self.generation_progress_ring = ft.ProgressRing(width=20, height=20, stroke_width=2, visible=False)

        self.portrait_image = ft.Image(
            src=None,
            width=256,
            height=256,
            fit=ft.ImageFit.COVER,
            border_radius=5,
            error_content=ft.Container(
                content=ft.Icon(ft.Icons.PORTRAIT, size=64),
                alignment=ft.alignment.center,
                width=256,
                height=256,
                border=ft.border.all(1, ft.Colors.OUTLINE),
                border_radius=5,
            )
        )
        self.upload_portrait_button = ft.ElevatedButton("Upload Portrait", on_click=self.upload_portrait_click)
        self.generate_portrait_button = ft.FilledButton("Generate Portrait", on_click=self.generate_portrait_click)
        self.portrait_progress_ring = ft.ProgressRing(width=20, height=20, stroke_width=2, visible=False)

        self.controls = [
            ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            self.name_field,
                            self.appearance_field,
                            self.personality_field,
                            self.backstory_field,
                            self.plot_hooks_field,
                            self.roleplaying_tips_field,
                        ],
                        spacing=10,
                        expand=1
                    ),
                    ft.Column(
                        controls=[
                            ft.Text("AI Generation Parameters", style=ft.TextThemeStyle.TITLE_MEDIUM, size=14),
                            ft.Row([self.race_dropdown, self.class_dropdown]),
                            ft.Row([self.environment_dropdown, self.hostility_dropdown]),
                            ft.Row([self.rarity_dropdown, self.background_dropdown]),
                            self.custom_prompt_field,
                            ft.Row([self.generate_npc_button, self.generation_progress_ring]),
                            ft.Divider(),
                            ft.Text("Character Portrait", style=ft.TextThemeStyle.TITLE_MEDIUM, size=14),
                            ft.Container(
                                content=self.portrait_image,
                                alignment=ft.alignment.center
                            ),
                            ft.Row(
                                [
                                    self.upload_portrait_button,
                                    self.generate_portrait_button,
                                    self.portrait_progress_ring
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            )
                        ],
                        spacing=10,
                        expand=1
                    )
                ],
                spacing=20,
                vertical_alignment=ft.CrossAxisAlignment.START
            )
        ]

    def did_mount(self):
        if self.is_edit_mode:
            self.page.run_task(self.load_character_data)

    def go_back(self, e):
        self.page.go("/characters")

    async def load_character_data(self):
        try:
            response = await supabase.client.from_('characters').select("*").eq('id',
                                                                                self.character_id).single().execute()
            if response.data:
                self._populate_fields(response.data)
                self.page.update()
        except Exception as e:
            self.page.open(ft.SnackBar(ft.Text(f"Error loading character: {e}"), bgcolor=ft.Colors.RED_700))
            self.page.update()

    def _populate_fields(self, data):
        print("--- Populating form fields with loaded data. ---")
        lang_code = 'en'
        self.name_field.value = data.get('name', '')
        self.appearance_field.value = data.get('appearance', {}).get(lang_code, '')
        self.personality_field.value = data.get('personality', {}).get(lang_code, '')
        self.backstory_field.value = data.get('backstory', {}).get(lang_code, '')
        self.plot_hooks_field.value = data.get('plot_hooks', {}).get(lang_code, '')
        self.roleplaying_tips_field.value = data.get('roleplaying_tips', {}).get(lang_code, '')

        # PLACEHOLDER: attributes = data.get('attributes', {})
        self.race_dropdown.value = data.get('race')
        self.class_dropdown.value = data.get('class')
        self.background_dropdown.value = data.get('background')
        self.environment_dropdown.value = data.get('environment')
        self.hostility_dropdown.value = data.get('hostility')
        self.rarity_dropdown.value = data.get('rarity')
        self.custom_prompt_field.value = data.get('custom_prompt', '')

        self.portrait_url = data.get('portrait_url')
        if self.portrait_url:
            print(f"--- Loading portrait from URL: {self.portrait_url} ---")
            self.portrait_image.src = self.portrait_url
        else:
            self.portrait_image.src = None

    def save_character_click(self, e):
        self.page.run_task(self._save_character)

    async def _save_character(self):
        print("--- Starting _save_character method. ---")
        if not self.name_field.value:
            self.name_field.error_text = "Name is required."
            self.page.update()
            return

        self.name_field.error_text = ""
        lang_code = 'en'
        character_data_to_save = {
            "name": self.name_field.value,
            "character_type": "NPC",
            "portrait_url": self.portrait_url,
            "appearance": {lang_code: self.appearance_field.value or ""},
            "personality": {lang_code: self.personality_field.value or ""},
            "backstory": {lang_code: self.backstory_field.value or ""},
            "plot_hooks": {lang_code: self.plot_hooks_field.value or ""},
            "roleplaying_tips": {lang_code: self.roleplaying_tips_field.value or ""},
            "notes": {lang_code: ""},
            "attributes": {},
            "tags": [],
            "race": self.race_dropdown.value,
            "class": self.class_dropdown.value,
            "background": self.background_dropdown.value,
            "environment": self.environment_dropdown.value,
            "hostility": self.hostility_dropdown.value,
            "rarity": self.rarity_dropdown.value,
            "custom_prompt": self.custom_prompt_field.value,
        }

        try:
            if self.is_edit_mode:
                await supabase.client.from_('characters').update(character_data_to_save).eq('id',
                                                                                            self.character_id).execute()
                message = "Character updated!"
            else:
                if not self.campaign_id:
                    raise Exception("Campaign ID is missing for new character.")
                character_data_to_save["campaign_id"] = self.campaign_id
                await supabase.client.from_('characters').insert(character_data_to_save).execute()
                message = "Character created!"

            self.page.open(ft.SnackBar(ft.Text(message), bgcolor=ft.Colors.GREEN_700))
            self.page.update()
        except Exception as ex:
            print(f"--- Supabase Save Error: {ex} ---")
            self.page.open(ft.SnackBar(ft.Text(f"Error saving: {ex}"), bgcolor=ft.Colors.RED_700))
            self.page.update()

    def generate_npc_click(self, e):
        self.page.run_task(self._generate_npc)

    async def _generate_npc(self):
        self.generation_progress_ring.visible = True
        self.generate_npc_button.disabled = True
        self.page.update()

        def get_choice(dropdown, choices):
            return random.choice(choices) if dropdown.value == "Random" else dropdown.value

        try:
            model_name = await asyncio.to_thread(self.page.client_storage.get, "ai.model") or DEFAULT_TEXT_MODEL
            prompt_params = {
                "race": get_choice(self.race_dropdown, DND_RACES),
                "char_class": get_choice(self.class_dropdown, DND_CLASSES),
                "environment": get_choice(self.environment_dropdown, DND_ENVIRONMENTS),
                "hostility": get_choice(self.hostility_dropdown, DND_HOSTILITIES),
                "rarity": get_choice(self.rarity_dropdown, DND_RARITIES),
                "background": get_choice(self.background_dropdown, DND_BACKGROUNDS),
                "custom_prompt": self.custom_prompt_field.value or "None"
            }
            prompt = GENERATE_NPC_PROMPT.format(**prompt_params)
            response_text = await self.gemini_service.get_text_response(prompt, model_name=model_name)
            clean_response = response_text.strip().replace("```json", "").replace("```", "")
            npc_data = json.loads(clean_response)
            self.name_field.value = npc_data.get("name", "")
            self.appearance_field.value = npc_data.get("appearance", "")
            self.personality_field.value = npc_data.get("personality", "")
            self.backstory_field.value = npc_data.get("backstory", "")
            self.plot_hooks_field.value = npc_data.get("plot_hooks", "")
            self.roleplaying_tips_field.value = npc_data.get("roleplaying_tips", "")
            self.race_dropdown.value = prompt_params["race"]
            self.class_dropdown.value = prompt_params["char_class"]
            self.background_dropdown.value = prompt_params["background"]
            self.environment_dropdown.value = prompt_params["environment"]
            self.hostility_dropdown.value = prompt_params["hostility"]
            self.rarity_dropdown.value = prompt_params["rarity"]
            self.page.open(ft.SnackBar(ft.Text("NPC data generated!"), bgcolor=ft.Colors.GREEN_700))
        except Exception as e:
            self.page.open(ft.SnackBar(ft.Text(f"An error occurred: {e}"), bgcolor=ft.Colors.RED_700))
        finally:
            self.generation_progress_ring.visible = False
            self.generate_npc_button.disabled = False
            self.page.update()

    def upload_portrait_click(self, e):
        print("--- Upload portrait button clicked. ---")
        self.file_picker.pick_files(allow_multiple=False, allowed_extensions=["png", "jpg", "jpeg"])

    def generate_portrait_click(self, e):
        print("--- Generate portrait button clicked. ---")
        if not self.appearance_field.value:
            self.page.open(ft.SnackBar(ft.Text("Please provide an appearance description first."),
                                       bgcolor=ft.Colors.AMBER_700))
            self.page.update()
            return
        self.page.run_task(self._generate_portrait_async)

    async def on_file_picker_result(self, e: ft.FilePickerResultEvent):
        if not e.files:
            print("--- File picker cancelled. ---")
            return
        selected_file = e.files[0]
        self.portrait_progress_ring.visible = True
        self.upload_portrait_button.disabled = True
        self.generate_portrait_button.disabled = True
        self.page.update()
        try:
            with open(selected_file.path, "rb") as f:
                file_bytes = f.read()
            await self._upload_and_update_portrait(file_bytes, selected_file.name)
        except Exception as ex:
            self.page.open(ft.SnackBar(ft.Text(f"Error reading file: {ex}"), bgcolor=ft.Colors.RED_700))
        finally:
            self.portrait_progress_ring.visible = False
            self.upload_portrait_button.disabled = False
            self.generate_portrait_button.disabled = False
            self.page.update()

    async def _generate_portrait_async(self):
        self.portrait_progress_ring.visible = True
        self.upload_portrait_button.disabled = True
        self.generate_portrait_button.disabled = True
        self.page.update()
        try:
            model_name = await asyncio.to_thread(self.page.client_storage.get, "picture.model") or DEFAULT_IMAGE_MODEL
            prompt = GENERATE_PORTRAIT_PROMPT
            image_bytes = await self.gemini_service.generate_image(prompt, model_name)
            if image_bytes:
                await self._upload_and_update_portrait(image_bytes, "generated_portrait.png")
            else:
                raise Exception("AI did not return an image.")
        except Exception as ex:
            self.page.open(ft.SnackBar(ft.Text(f"Error generating portrait: {ex}"), bgcolor=ft.Colors.RED_700))
        finally:
            self.portrait_progress_ring.visible = False
            self.upload_portrait_button.disabled = False
            self.generate_portrait_button.disabled = False
            self.page.update()

    async def _upload_and_update_portrait(self, file_bytes: bytes, file_name: str):
        user = await supabase.get_user()
        if not user: raise Exception("User not authenticated.")
        timestamp = int(time.time())
        storage_path = f"portraits/{user.id}/{timestamp}_{file_name}"
        await supabase.upload_file("assets", storage_path, file_bytes)

        # --- FIX: Added 'await' to the call to the async get_public_url method. ---
        public_url = await supabase.get_public_url("assets", storage_path)

        self.portrait_url = public_url
        self.portrait_image.src = public_url
        self.page.open(ft.SnackBar(ft.Text("Portrait updated successfully!"), bgcolor=ft.Colors.GREEN_700))
        self.page.update()