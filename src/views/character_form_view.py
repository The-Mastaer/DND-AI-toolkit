# src/views/character_form_view.py

import flet as ft
from ..services.supabase_service import supabase
from ..services.gemini_service import GeminiService
from ..prompts import GENERATE_NPC_PROMPT
from ..config import (
    DND_RACES, DND_CLASSES, DND_BACKGROUNDS,
    DND_ENVIRONMENTS, DND_HOSTILITIES, DND_RARITIES
)
import json
import asyncio
import random


class CharacterFormView(ft.View):
    """
    A full-page view for creating and editing characters, with a two-column layout
    and integrated AI generation.
    """

    def __init__(self, page: ft.Page, character_id=None, campaign_id=None):
        super().__init__()
        self.page = page
        self.character_id = character_id
        self.campaign_id = campaign_id
        self.is_edit_mode = character_id is not None
        self.gemini_service = GeminiService()

        # --- View Configuration ---
        self.route = f"/characters/edit/{self.character_id}" if self.is_edit_mode else f"/characters/new/{self.campaign_id}"
        self.appbar = ft.AppBar(
            title=ft.Text("Edit Character" if self.is_edit_mode else "Create New Character"),
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=self.go_back),
            actions=[ft.IconButton(icon=ft.Icons.SAVE, on_click=self.save_character_click, tooltip="Save Character")],
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        )

        # --- Helper for compact controls ---
        def create_compact_textfield(label, multiline=False, min_lines=1):
            return ft.TextField(
                label=label, multiline=multiline, min_lines=min_lines,
                text_size=12, dense=True
            )

        def create_compact_dropdown(label, options):
            return ft.Dropdown(
                label=label,
                options=[ft.dropdown.Option("Random")] + [ft.dropdown.Option(opt) for opt in options],
                value="Random", text_size=12, dense=True, expand=True
            )

        # --- Left Column: Main Character Details ---
        self.name_field = create_compact_textfield("Name")
        self.appearance_field = create_compact_textfield("Appearance", multiline=True, min_lines=4)
        self.personality_field = create_compact_textfield("Personality", multiline=True, min_lines=4)
        self.backstory_field = create_compact_textfield("Backstory", multiline=True, min_lines=4)
        self.plot_hooks_field = create_compact_textfield("Plot Hooks", multiline=True, min_lines=3)
        self.roleplaying_tips_field = create_compact_textfield("Roleplaying Tips", multiline=True, min_lines=3)

        left_column = ft.Column(
            controls=[
                self.name_field,
                self.appearance_field,
                self.personality_field,
                self.backstory_field,
                self.plot_hooks_field,
                self.roleplaying_tips_field,
            ],
            spacing=10,
            expand=True
        )

        # --- Right Column: AI Generation & Portrait ---
        self.race_dropdown = create_compact_dropdown("Race", DND_RACES)
        self.class_dropdown = create_compact_dropdown("Class", DND_CLASSES)
        self.environment_dropdown = create_compact_dropdown("Environment", DND_ENVIRONMENTS)
        self.hostility_dropdown = create_compact_dropdown("Hostility", DND_HOSTILITIES)
        self.rarity_dropdown = create_compact_dropdown("Rarity", DND_RARITIES)
        self.background_dropdown = create_compact_dropdown("Background", DND_BACKGROUNDS)
        self.custom_prompt_field = create_compact_textfield("Custom Prompt / Instructions", multiline=True, min_lines=3)
        self.generate_npc_button = ft.FilledButton("Generate with AI", on_click=self.generate_npc_click)
        self.generation_progress_ring = ft.ProgressRing(width=20, height=20, stroke_width=2, visible=False)

        right_column = ft.Column(
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
            expand=True
        )

        # --- Final View Layout ---
        self.controls = [
            ft.Row(
                controls=[left_column, right_column],
                spacing=20,
                expand=True
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
        }

        print(f"--- Data to save: {json.dumps(character_data_to_save, indent=2)} ---")

        try:
            if self.is_edit_mode:
                print(f"--- Updating character ID: {self.character_id} ---")
                await supabase.client.from_('characters').update(character_data_to_save).eq('id',
                                                                                            self.character_id).execute()
                message = "Character updated!"
            else:
                active_campaign_id = await asyncio.to_thread(self.page.client_storage.get, "active_campaign_id")
                if not active_campaign_id:
                    raise Exception("No active campaign selected. Please set one in Settings.")

                character_data_to_save["campaign_id"] = active_campaign_id
                print(f"--- Creating new character for campaign ID: {active_campaign_id} ---")
                await supabase.client.from_('characters').insert(character_data_to_save).execute()
                message = "Character created!"

            self.page.snack_bar = ft.SnackBar(content=ft.Text(message), bgcolor=ft.Colors.GREEN_700)
            self.go_back(None)
        except Exception as ex:
            print(f"--- Supabase Save Error: {ex} ---")
            self.page.snack_bar = ft.SnackBar(content=ft.Text(f"Error saving: {ex}"), bgcolor=ft.Colors.RED_700)
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

        # Helper function to get a random choice if "Random" is selected
        def get_choice(dropdown, choices):
            return random.choice(choices) if dropdown.value == "Random" else dropdown.value

        try:
            # Resolve "Random" selections before sending to AI
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

            response_text = await self.gemini_service.get_text_response(prompt)
            print(f"--- Received response from Gemini: {response_text[:100]}... ---")

            npc_data = json.loads(response_text)
            print("--- Successfully parsed JSON response. ---")

            # Populate the form fields with the parsed data
            self.name_field.value = npc_data.get("name", "")
            self.appearance_field.value = npc_data.get("appearance", "")
            self.personality_field.value = npc_data.get("personality", "")
            self.backstory_field.value = npc_data.get("backstory", "")
            self.plot_hooks_field.value = npc_data.get("plot_hooks", "")
            self.roleplaying_tips_field.value = npc_data.get("roleplaying_tips", "")

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