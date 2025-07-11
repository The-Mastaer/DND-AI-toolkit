# src/components/character_form_dialog.py

import flet as ft
from ..services.supabase_service import supabase
from ..services.gemini_service import GeminiService
from ..prompts import GENERATE_NPC_PROMPT # Assuming a new prompt will be added here
import json

class CharacterFormDialog(ft.AlertDialog):
    """
    A comprehensive dialog for creating, editing, and generating characters (NPCs/PCs).
    It includes fields for manual input, AI generation prompts, and portrait generation.
    """
    def __init__(self, page: ft.Page, on_save_callback, gemini_service: GeminiService):
        super().__init__()
        self.page = page
        self.on_save_callback = on_save_callback
        self.gemini_service = gemini_service
        self.modal = True
        self.title = ft.Text("Character Details")
        self.character_data = None # Stores data if in edit mode
        self.is_edit_mode = False

        # --- Input Fields for Character Details ---
        self.name_field = ft.TextField(label="Name", expand=True)
        self.character_type_dropdown = ft.Dropdown(
            label="Character Type",
            options=[
                ft.dropdown.Option("NPC", "NPC"),
                ft.dropdown.Option("PC", "PC"),
            ],
            value="NPC", # Default to NPC
            expand=True
        )
        self.appearance_field = ft.TextField(label="Appearance", multiline=True, min_lines=3, max_lines=5, expand=True)
        self.personality_field = ft.TextField(label="Personality", multiline=True, min_lines=3, max_lines=5, expand=True)
        self.backstory_field = ft.TextField(label="Backstory", multiline=True, min_lines=3, max_lines=5, expand=True)
        self.plot_hooks_field = ft.TextField(label="Plot Hooks", multiline=True, min_lines=2, max_lines=4, expand=True)
        self.roleplaying_tips_field = ft.TextField(label="Roleplaying Tips (Mannerism, Voice)", multiline=True, min_lines=2, max_lines=4, expand=True)
        self.dm_notes_field = ft.TextField(label="DM Notes", multiline=True, min_lines=3, max_lines=5, expand=True)
        self.attributes_field = ft.TextField(label="Attributes (JSON, e.g., {\"str\":10, \"dex\":12})", multiline=True, min_lines=2, max_lines=4, expand=True)
        self.tags_field = ft.TextField(label="Tags (comma-separated)", expand=True)

        # --- AI Generation Fields ---
        self.race_field = ft.TextField(label="Race (for AI Gen)", expand=True)
        self.class_field = ft.TextField(label="Class (for AI Gen)", expand=True)
        self.environment_field = ft.TextField(label="Environment (for AI Gen)", expand=True)
        self.hostility_field = ft.TextField(label="Hostility (for AI Gen)", expand=True)
        self.rarity_field = ft.TextField(label="Rarity (for AI Gen)", expand=True)
        self.background_field = ft.TextField(label="Background (for AI Gen)", expand=True)
        self.custom_prompt_field = ft.TextField(label="Custom Prompt (for AI Gen)", multiline=True, min_lines=2, max_lines=4, expand=True)

        self.generate_npc_button = ft.FilledButton("Generate NPC with AI", on_click=self.generate_npc_click)
        self.generate_portrait_button = ft.FilledButton("Generate Portrait", on_click=self.generate_portrait_click)
        self.portrait_image = ft.Image(width=200, height=200, fit=ft.ImageFit.CONTAIN, visible=False)
        self.generation_progress_ring = ft.ProgressRing(width=20, height=20, stroke_width=2, visible=False)

        # --- Dialog Content Layout ---
        self.content = ft.Column(
            [
                ft.Row([self.name_field, self.character_type_dropdown]),
                self.appearance_field,
                self.personality_field,
                self.backstory_field,
                self.plot_hooks_field,
                self.roleplaying_tips_field,
                self.dm_notes_field,
                self.attributes_field,
                self.tags_field,
                ft.Divider(),
                ft.Text("AI Generation Parameters:", style=ft.TextThemeStyle.TITLE_MEDIUM),
                ft.Row([self.race_field, self.class_field]),
                ft.Row([self.environment_field, self.hostility_field]),
                ft.Row([self.rarity_field, self.background_field]),
                self.custom_prompt_field,
                ft.Row([self.generate_npc_button, self.generate_portrait_button, self.generation_progress_ring]),
                self.portrait_image,
            ],
            tight=True,
            spacing=15,
            width=600, # Adjust width for better layout
            scroll=ft.ScrollMode.ADAPTIVE # Make content scrollable if it exceeds height
        )

        self.actions = [
            ft.TextButton("Cancel", on_click=self.close_dialog),
            ft.FilledButton("Save Character", on_click=self.save_character_click),
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    def open_dialog(self, character_data=None, campaign_id=None):
        """
        Opens the dialog, populating fields if in edit mode.
        """
        self.character_data = character_data
        self.selected_campaign_id = campaign_id # Store campaign_id for new character creation
        self.is_edit_mode = character_data is not None
        self.title.value = "Edit Character" if self.is_edit_mode else "Create New Character"

        self._reset_fields()
        if self.is_edit_mode:
            self._populate_fields(character_data)

        self.open = True
        self.page.dialog = self
        self.page.update()

    def _reset_fields(self):
        """Resets all input fields to their default empty state."""
        self.name_field.value = ""
        self.character_type_dropdown.value = "NPC"
        self.appearance_field.value = ""
        self.personality_field.value = ""
        self.backstory_field.value = ""
        self.plot_hooks_field.value = ""
        self.roleplaying_tips_field.value = ""
        self.dm_notes_field.value = ""
        self.attributes_field.value = ""
        self.tags_field.value = ""
        self.race_field.value = ""
        self.class_field.value = ""
        self.environment_field.value = ""
        self.hostility_field.value = ""
        self.rarity_field.value = ""
        self.background_field.value = ""
        self.custom_prompt_field.value = ""
        self.portrait_image.src = None
        self.portrait_image.visible = False
        self.generation_progress_ring.visible = False
        self.generate_npc_button.disabled = False
        self.generate_portrait_button.disabled = False
        self.update()

    def _populate_fields(self, data):
        """Populates input fields with existing character data."""
        self.name_field.value = data.get('name', '')
        self.character_type_dropdown.value = data.get('character_type', 'NPC')
        self.portrait_image.src = data.get('portrait_url')
        self.portrait_image.visible = bool(data.get('portrait_url'))

        # Handle JSONB fields
        self.appearance_field.value = data.get('appearance', {}).get('en', '')
        self.personality_field.value = data.get('personality', {}).get('en', '')
        self.backstory_field.value = data.get('backstory', {}).get('en', '')
        self.plot_hooks_field.value = data.get('plot_hooks', {}).get('en', '')
        self.roleplaying_tips_field.value = data.get('roleplaying_tips', {}).get('en', '')
        self.dm_notes_field.value = data.get('notes', {}).get('en', '') # 'notes' is 'DM notes'

        # Attributes field (JSONB)
        attributes = data.get('attributes', {})
        self.attributes_field.value = json.dumps(attributes, indent=2) if attributes else ""

        # Tags field (text[])
        tags = data.get('tags', [])
        self.tags_field.value = ", ".join(tags) if tags else ""

        self.update()

    def generate_npc_click(self, e):
        """Wrapper to call the async NPC generation method."""
        self.page.run_task(self._generate_npc)

    async def _generate_npc(self):
        """
        Generates NPC details using Gemini AI based on provided parameters.
        """
        self.generation_progress_ring.visible = True
        self.generate_npc_button.disabled = True
        self.generate_portrait_button.disabled = True
        self.update()

        race = self.race_field.value
        char_class = self.class_field.value
        environment = self.environment_field.value
        hostility = self.hostility_field.value
        rarity = self.rarity_field.value
        background = self.background_field.value
        custom_prompt = self.custom_prompt_field.value

        # Construct the prompt using the new GENERATE_NPC_PROMPT from prompts.py
        # Ensure GENERATE_NPC_PROMPT is defined in prompts.py to accept these parameters
        prompt = GENERATE_NPC_PROMPT.format(
            race=race,
            char_class=char_class,
            environment=environment,
            hostility=hostility,
            rarity=rarity,
            background=background,
            custom_prompt=f"Additional instructions: {custom_prompt}" if custom_prompt else ""
        )

        try:
            generated_text = await self.gemini_service.get_text_response(prompt)
            # Assuming the generated text is in a parsable format (e.g., JSON or structured text)
            # For now, let's just parse it as a simple string and assign to fields.
            # In a real scenario, you'd parse this into a dictionary and populate fields.
            # For demonstration, let's just put it into appearance for now.
            print(f"Generated NPC Text: {generated_text}")

            # A more robust parsing would be needed here if Gemini returns structured data.
            # For now, let's try to parse it as JSON if it looks like JSON, otherwise
            # just put it into the appearance field.
            try:
                parsed_data = json.loads(generated_text)
                self.name_field.value = parsed_data.get('name', self.name_field.value)
                self.appearance_field.value = parsed_data.get('appearance', {}).get('en', self.appearance_field.value)
                self.personality_field.value = parsed_data.get('personality', {}).get('en', self.personality_field.value)
                self.backstory_field.value = parsed_data.get('backstory', {}).get('en', self.backstory_field.value)
                self.plot_hooks_field.value = parsed_data.get('plot_hooks', {}).get('en', self.plot_hooks_field.value)
                self.roleplaying_tips_field.value = parsed_data.get('roleplaying_tips', {}).get('en', self.roleplaying_tips_field.value)
                # Attributes and tags would also need specific parsing
                if 'attributes' in parsed_data:
                    self.attributes_field.value = json.dumps(parsed_data['attributes'], indent=2)
                if 'tags' in parsed_data and isinstance(parsed_data['tags'], list):
                    self.tags_field.value = ", ".join(parsed_data['tags'])

            except json.JSONDecodeError:
                # If not JSON, just put the whole response into appearance for now.
                self.appearance_field.value = generated_text
                self.page.snack_bar = ft.SnackBar(content=ft.Text("AI generated text. Consider refining it manually."), bgcolor=ft.Colors.AMBER_700)
                self.page.snack_bar.open = True


        except Exception as ex:
            print(f"Error generating NPC: {ex}")
            self.page.snack_bar = ft.SnackBar(content=ft.Text(f"Error generating NPC: {ex}"), bgcolor=ft.Colors.RED_700)
            self.page.snack_bar.open = True
        finally:
            self.generation_progress_ring.visible = False
            self.generate_npc_button.disabled = False
            self.generate_portrait_button.disabled = False
            self.update()


    def generate_portrait_click(self, e):
        """Wrapper to call the async portrait generation method."""
        self.page.run_task(self._generate_portrait)

    async def _generate_portrait(self):
        """
        Generates a character portrait using Gemini AI based on the appearance field.
        """
        self.generation_progress_ring.visible = True
        self.generate_npc_button.disabled = True
        self.generate_portrait_button.disabled = True
        self.update()

        appearance_description = self.appearance_field.value
        if not appearance_description:
            self.page.snack_bar = ft.SnackBar(content=ft.Text("Please provide an appearance description first."), bgcolor=ft.Colors.AMBER_700)
            self.page.snack_bar.open = True
            self.generation_progress_ring.visible = False
            self.generate_npc_button.disabled = False
            self.generate_portrait_button.disabled = False
            self.update()
            return

        try:
            # Assuming GeminiService has an image generation method
            # This will need to be implemented in GeminiService
            portrait_url = await self.gemini_service.generate_image_from_text(f"A portrait of a D&D character with the following appearance: {appearance_description}. Fantasy art style.")
            if portrait_url:
                self.portrait_image.src = portrait_url
                self.portrait_image.visible = True
                self.page.snack_bar = ft.SnackBar(content=ft.Text("Portrait generated successfully!"), bgcolor=ft.Colors.GREEN_700)
                self.page.snack_bar.open = True
            else:
                self.page.snack_bar = ft.SnackBar(content=ft.Text("Failed to generate portrait."), bgcolor=ft.Colors.RED_700)
                self.page.snack_bar.open = True

        except Exception as ex:
            print(f"Error generating portrait: {ex}")
            self.page.snack_bar = ft.SnackBar(content=ft.Text(f"Error generating portrait: {ex}"), bgcolor=ft.Colors.RED_700)
            self.page.snack_bar.open = True
        finally:
            self.generation_progress_ring.visible = False
            self.generate_npc_button.disabled = False
            self.generate_portrait_button.disabled = False
            self.update()

    def save_character_click(self, e):
        """Wrapper to call the async save character method."""
        self.page.run_task(self._save_character)

    async def _save_character(self):
        """
        Saves or updates the character data in Supabase.
        """
        # Collect data from fields
        name = self.name_field.value
        character_type = self.character_type_dropdown.value
        portrait_url = self.portrait_image.src if self.portrait_image.visible else None

        # Handle JSONB fields (assuming 'en' as the current language for input)
        appearance = {"en": self.appearance_field.value} if self.appearance_field.value else {}
        personality = {"en": self.personality_field.value} if self.personality_field.value else {}
        backstory = {"en": self.backstory_field.value} if self.backstory_field.value else {}
        plot_hooks = {"en": self.plot_hooks_field.value} if self.plot_hooks_field.value else {}
        roleplaying_tips = {"en": self.roleplaying_tips_field.value} if self.roleplaying_tips_field.value else {}
        dm_notes = {"en": self.dm_notes_field.value} if self.dm_notes_field.value else {}

        # Attributes (parse JSON string)
        attributes = {}
        if self.attributes_field.value:
            try:
                attributes = json.loads(self.attributes_field.value)
            except json.JSONDecodeError:
                self.page.snack_bar = ft.SnackBar(content=ft.Text("Invalid JSON for Attributes!"), bgcolor=ft.Colors.RED_700)
                self.page.snack_bar.open = True
                self.page.update()
                return

        # Tags (parse comma-separated string)
        tags = [tag.strip() for tag in self.tags_field.value.split(',') if tag.strip()] if self.tags_field.value else []

        # Basic validation
        if not name:
            self.page.snack_bar = ft.SnackBar(content=ft.Text("Character Name is required!"), bgcolor=ft.Colors.RED_700)
            self.page.snack_bar.open = True
            self.page.update()
            return

        character_data_to_save = {
            "name": name,
            "character_type": character_type,
            "portrait_url": portrait_url,
            "appearance": appearance,
            "personality": personality,
            "backstory": backstory,
            "plot_hooks": plot_hooks,
            "roleplaying_tips": roleplaying_tips,
            "notes": dm_notes, # Corresponds to 'DM notes'
            "attributes": attributes,
            "tags": tags,
        }

        try:
            if self.is_edit_mode:
                # Update existing character
                response = await supabase.table('characters').update(character_data_to_save).eq('id', self.character_data['id']).execute()
                message = "Character updated successfully!"
            else:
                # Create new character
                character_data_to_save["campaign_id"] = self.selected_campaign_id
                response = await supabase.table('characters').insert([character_data_to_save]).execute()
                message = "Character created successfully!"

            if response.data:
                self.page.snack_bar = ft.SnackBar(content=ft.Text(message), bgcolor=ft.Colors.GREEN_700)
                self.page.snack_bar.open = True
                self.page.update()
                self.close_dialog(None) # Close dialog on success
                if self.on_save_callback:
                    self.on_save_callback() # Refresh character list in parent view
            else:
                raise Exception(f"No data returned from Supabase: {response.status_code}")

        except Exception as ex:
            print(f"Error saving character: {ex}")
            self.page.snack_bar = ft.SnackBar(content=ft.Text(f"Error saving character: {ex}"), bgcolor=ft.Colors.RED_700)
            self.page.snack_bar.open = True
            self.page.update()


    def close_dialog(self, e):
        """Closes the dialog."""
        self.open = False
        self.page.dialog = None # Clear the dialog from the page
        self.page.update()