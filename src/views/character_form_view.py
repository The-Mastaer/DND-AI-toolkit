# src/views/character_form_view.py

import flet as ft
from services.supabase_service import supabase
from services.gemini_service import GeminiService
from prompts import GENERATE_NPC_PROMPT
from config import (
    DND_RACES, DND_CLASSES, DND_BACKGROUNDS,
    DND_ENVIRONMENTS, DND_HOSTILITIES, DND_RARITIES,
    DEFAULT_TEXT_MODEL
)
from components.ui_components import create_compact_textfield, create_compact_dropdown
import json
import asyncio
import random


class CharacterFormView(ft.View):
    """
    A full-page view for creating and editing characters, with a two-column layout
    and integrated AI generation.
    """

    def __init__(self, page: ft.Page, gemini_service: GeminiService, character_id=None, campaign_id=None):
        """
        Initializes the CharacterFormView.

        Args:
            page (ft.Page): The Flet page object.
            gemini_service (GeminiService): The singleton instance of the Gemini service.
            character_id (int, optional): The ID of the character to edit. Defaults to None.
            campaign_id (int, optional): The ID of the campaign for a new character. Defaults to None.
        """
        super().__init__()
        self.page = page
        self.character_id = character_id
        self.campaign_id = campaign_id
        self.is_edit_mode = character_id is not None
        self.gemini_service = gemini_service

        # --- View Configuration ---
        self.route = f"/characters/edit/{self.character_id}" if self.is_edit_mode else f"/characters/new/{self.campaign_id}"
        self.appbar = ft.AppBar(
            title=ft.Text("Edit Character" if self.is_edit_mode else "Create New Character"),
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=self.go_back),
            actions=[ft.IconButton(icon=ft.Icons.SAVE, on_click=self.save_character_click, tooltip="Save Character")],
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        )
        self.scroll = ft.ScrollMode.ADAPTIVE

        # --- Left Column: Main Character Details ---
        self.name_field = create_compact_textfield("Name")
        self.appearance_field = create_compact_textfield("Appearance", multiline=True, min_lines=4)
        self.personality_field = create_compact_textfield("Personality", multiline=True, min_lines=4)
        self.backstory_field = create_compact_textfield("Backstory", multiline=True, min_lines=4)
        self.plot_hooks_field = create_compact_textfield("Plot Hooks", multiline=True, min_lines=3)
        self.roleplaying_tips_field = create_compact_textfield("Roleplaying Tips", multiline=True, min_lines=3)

        # --- Right Column: AI Generation & Portrait ---
        self.race_dropdown = create_compact_dropdown("Race", DND_RACES, expand=True)
        self.class_dropdown = create_compact_dropdown("Class", DND_CLASSES, expand=True)
        self.environment_dropdown = create_compact_dropdown("Environment", DND_ENVIRONMENTS, expand=True)
        self.hostility_dropdown = create_compact_dropdown("Hostility", DND_HOSTILITIES, expand=True)
        self.rarity_dropdown = create_compact_dropdown("Rarity", DND_RARITIES, expand=True)
        self.background_dropdown = create_compact_dropdown("Background", DND_BACKGROUNDS, expand=True)
        self.custom_prompt_field = create_compact_textfield("Custom Prompt / Instructions", multiline=True, min_lines=3)
        self.generate_npc_button = ft.FilledButton("Generate with AI", on_click=self.generate_npc_click)
        self.generation_progress_ring = ft.ProgressRing(width=20, height=20, stroke_width=2, visible=False)

        # --- Final View Layout ---
        # DEBUG FIX: Encapsulated each major section in a Column with expand=True
        # inside the main Row to ensure proper two-column layout.
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
                        expand=1  # Takes up 1 part of the space
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
                            ft.Text("Portrait (Coming Soon)", style=ft.TextThemeStyle.TITLE_MEDIUM, size=14),
                            ft.Container(height=200, border=ft.border.all(1, ft.Colors.OUTLINE), border_radius=5,
                                         content=ft.Icon(ft.Icons.PORTRAIT, size=64), alignment=ft.alignment.center)
                        ],
                        spacing=10,
                        expand=1  # Takes up 1 part of the space
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
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error loading character: {e}"), bgcolor=ft.Colors.RED)
            self.page.snack_bar.open = True
            self.page.update()

    def _populate_fields(self, data):
        lang_code = 'en'
        self.name_field.value = data.get('name', '')
        self.appearance_field.value = data.get('appearance', {}).get(lang_code, '')
        self.personality_field.value = data.get('personality', {}).get(lang_code, '')
        self.backstory_field.value = data.get('backstory', {}).get(lang_code, '')
        self.plot_hooks_field.value = data.get('plot_hooks', {}).get(lang_code, '')
        self.roleplaying_tips_field.value = data.get('roleplaying_tips', {}).get(lang_code, '')
        self.race_dropdown.value = data.get('race')
        self.class_dropdown.value = data.get('class')
        self.background_dropdown.value = data.get('background')
        self.environment_dropdown.value = data.get('environment')
        self.hostility_dropdown.value = data.get('hostility')
        self.rarity_dropdown.value = data.get('rarity')
        self.custom_prompt_field.value = data.get('custom_prompt', '')

    def save_character_click(self, e):
        """Wrapper to call the async save character method."""
        print("--- Save button clicked. Running save task. ---")
        self.page.run_task(self._save_character)

    async def _save_character(self):
        """Saves new or updated character data to the database."""
        print("--- Starting _save_character method. ---")
        if not self.name_field.value:
            self.name_field.error_text = "Name is required."
            self.page.update()
            print("--- Save failed: Name is required. ---")
            return

        self.name_field.error_text = ""

        lang_code = 'en'
        character_data_to_save = {
            "name": self.name_field.value,
            "character_type": "NPC",
            "appearance": {lang_code: self.appearance_field.value},
            "personality": {lang_code: self.personality_field.value},
            "backstory": {lang_code: self.backstory_field.value},
            "plot_hooks": {lang_code: self.plot_hooks_field.value},
            "roleplaying_tips": {lang_code: self.roleplaying_tips_field.value},
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

        print(f"--- Data to save: {json.dumps(character_data_to_save, indent=2)} ---")

        try:
            if self.is_edit_mode:
                print(f"--- Updating character ID: {self.character_id} ---")
                await supabase.client.from_('characters').update(character_data_to_save).eq('id',
                                                                                            self.character_id).execute()
                message = "Character updated!"
            else:
                if not self.campaign_id:
                    raise Exception("Campaign ID is missing for new character.")

                character_data_to_save["campaign_id"] = self.campaign_id
                print(f"--- Creating new character for campaign ID: {self.campaign_id} ---")
                await supabase.client.from_('characters').insert(character_data_to_save).execute()
                message = "Character created!"

            self.page.snack_bar = ft.SnackBar(content=ft.Text(message), bgcolor=ft.Colors.GREEN_700)
            self.page.snack_bar.open = True
            self.page.update()
        except Exception as ex:
            print(f"--- Supabase Save Error: {ex} ---")
            self.page.snack_bar = ft.SnackBar(content=ft.Text(f"Error saving: {ex}"), bgcolor=ft.Colors.RED_700)
            self.page.snack_bar.open = True
            self.page.update()
        finally:
            self.page.snack_bar.open = True
            self.page.update()

    def generate_npc_click(self, e):
        """Wrapper to call the async AI generation."""
        print("--- Generate button clicked. Running generation task. ---")
        self.page.run_task(self._generate_npc)

    async def _generate_npc(self):
        """Generates NPC data via Gemini and populates the form fields."""
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

            print(f"--- Sending prompt to Gemini with params: {prompt_params} ---")
            prompt = GENERATE_NPC_PROMPT.format(**prompt_params)

            response_text = await self.gemini_service.get_text_response(prompt, model_name=model_name)
            print(f"--- Received response from Gemini: {response_text[:100]}... ---")

            # Clean the response text before parsing
            clean_response = response_text.strip().replace("```json", "").replace("```", "")
            npc_data = json.loads(clean_response)
            print("--- Successfully parsed JSON response. ---")

            # Populate the main text fields
            self.name_field.value = npc_data.get("name", "")
            self.appearance_field.value = npc_data.get("appearance", "")
            self.personality_field.value = npc_data.get("personality", "")
            self.backstory_field.value = npc_data.get("backstory", "")
            self.plot_hooks_field.value = npc_data.get("plot_hooks", "")
            self.roleplaying_tips_field.value = npc_data.get("roleplaying_tips", "")

            # --- Update dropdowns with the generated values ---
            self.race_dropdown.value = prompt_params["race"]
            self.class_dropdown.value = prompt_params["char_class"]
            self.background_dropdown.value = prompt_params["background"]
            self.environment_dropdown.value = prompt_params["environment"]
            self.hostility_dropdown.value = prompt_params["hostility"]
            self.rarity_dropdown.value = prompt_params["rarity"]

            self.page.snack_bar = ft.SnackBar(ft.Text("NPC data generated!"), bgcolor=ft.Colors.GREEN_700)

        except json.JSONDecodeError:
            print("--- Gemini response was not valid JSON. ---")
            self.page.snack_bar = ft.SnackBar(ft.Text("AI response was not valid JSON. Please try again."),
                                              bgcolor=ft.Colors.AMBER_700)
        except Exception as e:
            print(f"--- An error occurred during NPC generation: {e} ---")
            self.page.snack_bar = ft.SnackBar(ft.Text(f"An error occurred: {e}"), bgcolor=ft.Colors.RED_700)
        finally:
            self.generation_progress_ring.visible = False
            self.generate_npc_button.disabled = False
            self.page.snack_bar.open = True
            self.page.update()
