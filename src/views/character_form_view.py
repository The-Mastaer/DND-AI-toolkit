# src/views/character_form_view.py

import flet as ft
from services.supabase_service import supabase
from services.gemini_service import gemini_service, NPCData, CharacterStats
from config import GEMINI_SRD_FILE_NAME, DEFAULT_TEXT_MODEL, DEFAULT_IMAGE_MODEL
from prompts import GENERATE_PORTRAIT_PROMPT
import asyncio
import json
import random
import time

# Sample data for dropdowns
GENDERS = ["Male", "Female", "Non-binary","Random"]
RARITIES = ["Common", "Uncommon", "Rare", "Very Rare", "Legendary","Random"]
ATTITUDES = ["Friendly", "Neutral", "Hostile", "Indifferent","Random"]
RACES = ["Human", "Elf", "Dwarf", "Halfling", "Dragonborn", "Gnome", "Half-Elf", "Half-Orc", "Tiefling","Random"]
CLASSES = ["Fighter", "Wizard", "Rogue", "Cleric", "Barbarian", "Bard", "Druid", "Monk", "Paladin", "Ranger",
           "Sorcerer", "Warlock","Random"]
ENVIRONMENTS = ["Urban", "Forest", "Mountain", "Dungeon", "Aquatic", "Desert", "Arctic","Random"]
BACKGROUNDS = ["Acolyte", "Charlatan", "Criminal", "Entertainer", "Folk Hero", "Guild Artisan", "Hermit", "Noble",
               "Outlander", "Sage", "Sailor", "Soldier", "Urchin","Random"]


class CharacterFormView(ft.View):
    """
    A view for creating, editing, and generating NPC/PC characters.
    """

    def __init__(self, page: ft.Page, gemini_service: gemini_service, character_id=None, campaign_id=None,
                 selected_language="en"):
        super().__init__()
        self.page = page
        self.gemini_service = gemini_service
        self.character_id = character_id
        # **FIX:** Removed the blocking client_storage call from the constructor.
        # campaign_id is passed directly when creating a new character.
        # For an existing character, we will get it from the character's data.
        self.campaign_id = campaign_id
        self.selected_language = selected_language
        self.is_new_character = character_id is None
        self.route = f"/character_edit/{character_id or f'new/{self.campaign_id}'}?lang={selected_language}"

        self.appbar = ft.AppBar(
            title=ft.Text("New NPC" if self.is_new_character else "Edit Character"),
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda _: self.page.go("/characters")),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        )

        # --- Define UI Controls ---
        self.name_field = ft.TextField(label="Name")
        self.appearance_field = ft.TextField(label="Appearance", multiline=True, min_lines=4, max_lines=6)
        self.personality_field = ft.TextField(label="Personality", multiline=True, min_lines=4, max_lines=6)
        self.backstory_field = ft.TextField(label="Backstory", multiline=True, min_lines=5, max_lines=8)

        self.plot_hooks_field = ft.TextField(label="Plot Hooks", multiline=True, min_lines=5, max_lines=10)
        self.roleplaying_tips_field = ft.TextField(label="Roleplaying Tips", multiline=True, min_lines=5, max_lines=10)
        self.notes_field = ft.TextField(label="DM Notes", multiline=True, min_lines=5, max_lines=10)

        self.level_field = ft.TextField(label="Level", read_only=True, width=100)
        self.hp_field = ft.TextField(label="HP", read_only=True, width=100)
        self.ac_field = ft.TextField(label="AC", read_only=True, width=100)
        self.attributes_field = ft.TextField(label="Attributes & Abilities", multiline=True, min_lines=10)

        self.portrait_image = ft.Image(src="/images/placeholder.png", width=256, height=256, fit=ft.ImageFit.COVER,
                                       border_radius=10)
        self.generate_portrait_button = ft.ElevatedButton("Generate Portrait", icon=ft.Icons.AUTO_AWESOME,
                                                          on_click=self.generate_portrait_clicked)
        self.portrait_loading_indicator = ft.ProgressRing(visible=False)

        self.gender_dropdown = ft.Dropdown(label="Gender",value="Random", options=[ft.dropdown.Option(g) for g in GENDERS])
        self.rarity_dropdown = ft.Dropdown(label="Rarity",value="Random", options=[ft.dropdown.Option(r) for r in RARITIES])
        self.attitude_dropdown = ft.Dropdown(label="Attitude",value="Random", options=[ft.dropdown.Option(a) for a in ATTITUDES])
        self.race_dropdown = ft.Dropdown(label="Race",value="Random", options=[ft.dropdown.Option(r) for r in RACES])
        self.class_dropdown = ft.Dropdown(label="Class",value="Random", options=[ft.dropdown.Option(c) for c in CLASSES])
        self.environment_dropdown = ft.Dropdown(label="Environment",value="Random",
                                                options=[ft.dropdown.Option(e) for e in ENVIRONMENTS])
        self.background_dropdown = ft.Dropdown(label="Background",value="Random", options=[ft.dropdown.Option(b) for b in BACKGROUNDS])
        self.custom_prompt_field = ft.TextField(label="Custom Prompt", multiline=True)
        self.generate_npc_button = ft.ElevatedButton("Generate with AI", icon=ft.Icons.AUTO_AWESOME,
                                                     on_click=self.generate_npc_clicked)
        self.npc_loading_indicator = ft.ProgressRing(visible=False)
        self.attribute_loading_indicator = ft.ProgressRing(visible=False)

        self.generate_stats_button = ft.ElevatedButton("Generate Stats with AI", icon=ft.Icons.CASINO,
                                                       on_click=self.generate_stats_clicked,
                                                       tooltip="Generates Level, HP, AC, and attributes based on Class and Rarity using the SRD.")

        self.save_button = ft.FilledButton("Save NPC in Workshop", icon=ft.Icons.SAVE,
                                           on_click=self.save_character_clicked)
        self.save_loading_indicator = ft.ProgressRing(visible=False)

        # --- Layout ---
        self.controls = [
            ft.Row(
                [
                    ft.Column(
                        controls=[
                            self.name_field,
                            self.appearance_field,
                            self.personality_field,
                            self.backstory_field,
                            ft.Tabs(
                                expand=True,
                                tabs=[
                                    ft.Tab(text="Plot Hooks", content=ft.Container(self.plot_hooks_field, padding=10)),
                                    ft.Tab(text="Roleplaying",
                                           content=ft.Container(self.roleplaying_tips_field, padding=10)),
                                    ft.Tab(text="Notes", content=ft.Container(self.notes_field, padding=10)),
                                    ft.Tab(text="Stats", content=ft.Container(
                                        ft.Column(scroll=ft.ScrollMode.AUTO, controls=[
                                            ft.Row([self.level_field, self.hp_field, self.ac_field], spacing=10),
                                            self.attributes_field
                                        ]),
                                        padding=10
                                    ))
                                ]
                            )
                        ],
                        expand=3, spacing=10
                    ),
                    ft.Column(
                        [
                            ft.Tabs(
                                expand=True,
                                tabs=[
                                    ft.Tab(text="Portrait", content=ft.Container(ft.Column([
                                        ft.Container(self.portrait_image, alignment=ft.alignment.center),
                                        ft.Row([self.generate_portrait_button, self.portrait_loading_indicator],
                                               alignment=ft.MainAxisAlignment.CENTER)
                                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER), padding=10)),
                                    ft.Tab(text="NPC Workshop", content=ft.Container(ft.Column([
                                        ft.Row([self.gender_dropdown, self.attitude_dropdown]),
                                        ft.Row([self.rarity_dropdown, self.environment_dropdown]),
                                        ft.Row([self.race_dropdown, self.class_dropdown]),
                                        self.background_dropdown,
                                        self.custom_prompt_field,
                                        ft.Row([self.generate_npc_button, self.npc_loading_indicator]),
                                        ft.Divider(),
                                        ft.Row([self.generate_stats_button,self.attribute_loading_indicator])
                                    ], scroll=ft.ScrollMode.ADAPTIVE), padding=10, alignment=ft.alignment.top_center))
                                ]
                            ),
                            ft.Row([self.save_button, self.save_loading_indicator], alignment=ft.MainAxisAlignment.END),
                        ],
                        expand=2, spacing=10
                    )
                ],
                expand=True, spacing=20
            )
        ]

    def get_randomized_value(self, dropdown: ft.Dropdown) -> str:
        """
        Checks a dropdown's value. If it's 'Random', it returns a random
        choice from the dropdown's options. Otherwise, returns the selected value.
        """
        selected_value = dropdown.value
        if selected_value == "Random":
            # Get all options except the "Random" placeholder itself
            options = [opt.key for opt in dropdown.options if opt.key != "Random"]
            if options:
                return random.choice(options)
            return ""  # Return empty string if no other options exist
        return selected_value

    def did_mount(self):
        self.page.run_task(self.load_character_data)
        self.current_npc_data: NPCData | None = None
        self.current_character_stats: CharacterStats | None = None

    async def load_character_data(self):
        if self.is_new_character:
            print("--- Opening form for new character. ---")
            if not self.campaign_id:
                # Fallback to get campaign_id from storage if it wasn't in the route for some reason
                self.campaign_id = int(await asyncio.to_thread(self.page.client_storage.get, "active_campaign_id"))
            return

        print(f"--- Loading data for character ID: {self.character_id} ---")
        try:
            response = await supabase.get_character_by_id(self.character_id)
            if response.data:
                character = response.data

                # Helper function to extract text from localized JSONB fields
                def get_text(field, lang='en', default=''):
                    if isinstance(field, dict):
                        return field.get(lang, field.get('en', default))
                    return field if field is not None else default

                    # --- NEW: Create and store Pydantic objects from loaded data ---
                try:
                    # 1. Prepare a dictionary that matches the NPCData model (with simple strings)
                    prepared_npc_data = {
                        "name": get_text(character.get('name')),
                        "gender": get_text(character.get('gender')),
                        "appearance": get_text(character.get('appearance'), self.selected_language),
                        "personality": get_text(character.get('personality'), self.selected_language),
                        "backstory": get_text(character.get('backstory'), self.selected_language),
                        "plot_hooks": get_text(character.get('plot_hooks'), self.selected_language),
                        "roleplaying_tips": get_text(character.get('roleplaying_tips'), self.selected_language),
                    }
                    # 2. Create and store the NPCData object
                    self.current_npc_data = NPCData(**prepared_npc_data)

                    # 3. Create and store the CharacterStats object if attributes exist
                    if character.get("attributes"):
                        self.current_character_stats = CharacterStats(**character["attributes"])

                except Exception as e:
                    print(f"Error creating Pydantic models from loaded data: {e}")
                    self.page.open(
                        ft.SnackBar(ft.Text("Could not parse loaded character data."), bgcolor=ft.Colors.RED))
                    return

                # **FIX:** Set the instance's campaign_id from the loaded character data
                self.campaign_id = character.get('campaign_id')

                def get_text(field, lang='en', default=''):
                    if isinstance(field, dict):
                        return field.get(lang, field.get('en', default))
                    return field if field is not None else default

                self.name_field.value = get_text(character.get('name'))
                self.appearance_field.value = get_text(character.get('appearance'), self.selected_language)
                self.personality_field.value = get_text(character.get('personality'), self.selected_language)
                self.backstory_field.value = get_text(character.get('backstory'), self.selected_language)
                self.plot_hooks_field.value = get_text(character.get('plot_hooks'), self.selected_language)
                self.roleplaying_tips_field.value = get_text(character.get('roleplaying_tips'), self.selected_language)
                self.notes_field.value = get_text(character.get('notes'), self.selected_language)

                attributes = character.get('attributes') or {}
                if isinstance(attributes, dict):
                    self.level_field.value = str(attributes.get('level', ''))
                    self.hp_field.value = str(attributes.get('hp', ''))
                    self.ac_field.value = str(attributes.get('ac', ''))
                    self.attributes_field.value = json.dumps(attributes, indent=2)

                self.portrait_image.src = character.get('portrait_url') or "/images/placeholder.png"

                print(f"--- Populating dropdowns from dedicated columns ---")
                self.gender_dropdown.value = get_text(character.get('gender'))
                self.rarity_dropdown.value = get_text(character.get('rarity'))
                self.attitude_dropdown.value = get_text(character.get('hostility'))
                self.race_dropdown.value = get_text(character.get('race'))
                self.class_dropdown.value = get_text(character.get('class'))
                self.environment_dropdown.value = get_text(character.get('environment'))
                self.background_dropdown.value = get_text(character.get('background'))
                self.custom_prompt_field.value = get_text(character.get('custom_prompt'))

                print("--- Character data loaded into form. ---")
                self.update()
            else:
                self.page.open(ft.SnackBar(ft.Text("Character not found."), bgcolor=ft.Colors.RED))
        except Exception as e:
            print(f"Error loading character data: {e}")
            self.page.open(ft.SnackBar(ft.Text(f"Error: {e}"), bgcolor=ft.Colors.RED))

        finally:
            self.update()

    async def generate_npc_clicked(self, e):
        print("--- 'Generate with AI' button clicked. ---")
        self.npc_loading_indicator.visible = True
        self.generate_npc_button.disabled = True
        self.update()

        try:
            model_name = await asyncio.to_thread(self.page.client_storage.get, "ai.model") or DEFAULT_TEXT_MODEL

            world_id_str = await asyncio.to_thread(self.page.client_storage.get, "active_world_id")
            campaign_id_str = str(self.campaign_id)  # Use the instance campaign_id

            if not world_id_str or not campaign_id_str:
                self.page.open(ft.SnackBar(ft.Text("Please set your active world and campaign in Settings."),
                                           bgcolor=ft.Colors.ORANGE))
                return

            world_id = int(world_id_str)
            campaign_id = int(campaign_id_str)

            world_resp = await supabase.get_world_details(world_id)
            campaign_resp = await supabase.get_campaign_details(campaign_id)

            world_context = world_resp.data.get('lore', {}).get(self.selected_language, "")

            campaign_context = ""
            if campaign_resp.data:
                c = campaign_resp.data
                campaign_context = f"Campaign Name: {c.get('name', {}).get(self.selected_language, '')}\nParty Info: {c.get('party_info', {}).get(self.selected_language, '')}\nSession History: {c.get('session_history', {}).get(self.selected_language, '')}"

            prompt_params = {
                "race": self.get_randomized_value(self.race_dropdown),
                "char_class": self.get_randomized_value(self.class_dropdown),
                "gender": self.get_randomized_value(self.gender_dropdown),
                "environment": self.get_randomized_value(self.environment_dropdown),
                "hostility": self.get_randomized_value(self.attitude_dropdown),
                "rarity": self.get_randomized_value(self.rarity_dropdown),
                "background": self.get_randomized_value(self.background_dropdown),
                "custom_prompt": self.custom_prompt_field.value or "None",
                "target_language": "English",
                "world_context": world_context,
                "campaign_context": campaign_context
            }

            print("--- Updating dropdowns with potentially randomized values ---")
            self.race_dropdown.value = prompt_params["race"]
            self.class_dropdown.value = prompt_params["char_class"]
            self.gender_dropdown.value = prompt_params["gender"]
            self.environment_dropdown.value = prompt_params["environment"]
            self.attitude_dropdown.value = prompt_params["hostility"]
            self.rarity_dropdown.value = prompt_params["rarity"]
            self.background_dropdown.value = prompt_params["background"]

            npc_data = await self.gemini_service.generate_npc_data(model_name=model_name, **prompt_params)

            if npc_data:
                self.current_npc_data = npc_data
                self.name_field.value = npc_data.name
                self.appearance_field.value = npc_data.appearance
                self.personality_field.value = npc_data.personality
                self.backstory_field.value = npc_data.backstory
                self.plot_hooks_field.value = npc_data.plot_hooks
                self.roleplaying_tips_field.value = npc_data.roleplaying_tips
                self.page.open(ft.SnackBar(ft.Text("NPC data generated successfully!"), bgcolor=ft.Colors.GREEN))
            else:
                self.page.open(ft.SnackBar(ft.Text("Failed to generate NPC data from AI."), bgcolor=ft.Colors.RED))

        except Exception as ex:
            print(f"Error during NPC generation: {ex}")
            self.page.open(ft.SnackBar(ft.Text(f"An error occurred: {ex}"), bgcolor=ft.Colors.RED))
        finally:
            self.npc_loading_indicator.visible = False
            self.generate_npc_button.disabled = False
            self.update()

    async def generate_portrait_clicked(self, e):
        """
           Generates a portrait, uploads it to Supabase, and updates the UI.
           """
        print("--- 'Generate Portrait' button clicked. ---")

        # 1. Check if there's character data to base the portrait on
        if not self.current_npc_data:
            self.page.open(
                ft.SnackBar(ft.Text("Please generate or load character data first."), bgcolor=ft.Colors.ORANGE))
            return

        self.generate_portrait_button.disabled = True
        # Assuming you have a loading indicator for the portrait
        # self.portrait_loading_indicator.visible = True
        self.update()

        try:
            # 1. Gather data from the correct sources
            npc_narrative = self.current_npc_data

            # Get level from stats object if it exists, otherwise default to 1
            level = self.current_character_stats.level if self.current_character_stats else 1

            # 2. Format the prompt with data from both sources
            image_prompt = GENERATE_PORTRAIT_PROMPT.format(
                appearance=npc_narrative.appearance,
                personality=npc_narrative.personality,
                race=self.race_dropdown.value,
                char_class=self.class_dropdown.value,
                environment=self.environment_dropdown.value,
                rarity=self.rarity_dropdown.value,
                level=level
            )
            # 3. Call Gemini to generate the image bytes
            # You may want to use a specific image model name here
            image_model = DEFAULT_IMAGE_MODEL  # Example model
            image_bytes = await gemini_service.generate_image(prompt=image_prompt, model_name=image_model)

            if not image_bytes:
                raise Exception("AI did not return an image.")

            # 4. Upload the image bytes to Supabase Storage
            user = await supabase.get_user()
            if not user:
                self.page.open(
                    ft.SnackBar(ft.Text("Error: User session not found. Please log in again."), bgcolor=ft.colors.RED))
                raise Exception("User not authenticated.")
            bucket_name = "assets"
            # Assuming you have the user's ID, required for the path
            user_id = user.id
            file_name = f"{int(time.time())}.png"
            file_path = f"portraits/{user_id}/{file_name}"

            await supabase.upload_file(
                bucket_name=bucket_name,
                file_path=file_path,
                file_content=image_bytes
            )

            # 5. Get the public URL of the newly uploaded file
            public_url = await supabase.get_public_url(bucket_name=bucket_name, file_path=file_path)

            # 6. Update the character record in the database with the new URL
            if not self.is_new_character:
                await supabase.update_character(self.character_id, {"portrait_url": public_url})

            # 7. Update the UI to display the new portrait
            # Assuming you have an ft.Image control named self.portrait_image
            self.portrait_image.src = public_url
            self.page.open(ft.SnackBar(ft.Text("Portrait generated and saved successfully!"), bgcolor=ft.Colors.GREEN))

        except Exception as ex:
            print(f"Error during portrait generation: {ex}")
            self.page.open(ft.SnackBar(ft.Text(f"An error occurred: {ex}"), bgcolor=ft.Colors.RED))
        finally:
            self.generate_portrait_button.disabled = False
            # self.portrait_loading_indicator.visible = False
            self.update()

    async def generate_stats_clicked(self, e):
        print("--- 'Generate Stats' button clicked. ---")
        npc_class = self.class_dropdown.value
        rarity = self.rarity_dropdown.value
        if not npc_class or not rarity:
            self.page.open(ft.SnackBar(ft.Text("Please select a Class and Rarity first."), bgcolor=ft.Colors.ORANGE))
            return

        self.generate_stats_button.disabled = True
        self.attribute_loading_indicator.visible = True
        self.update()

        try:
            srd_file = await self.gemini_service.get_gemini_file_by_name(GEMINI_SRD_FILE_NAME)
            if not srd_file:
                self.page.open(
                    ft.SnackBar(ft.Text("SRD file not found. Check settings and ensure it has been uploaded."),
                                bgcolor=ft.Colors.RED))
                return

            model_name = await asyncio.to_thread(self.page.client_storage.get, "ai.model") or DEFAULT_TEXT_MODEL

            stats_pydantic_obj = await self.gemini_service.generate_character_attributes(
                character_class=npc_class,
                rarity=rarity,
                srd_file=srd_file,
                model_name=model_name
            )

            if stats_pydantic_obj:
                self.current_character_stats = stats_pydantic_obj
                stats_dict = stats_pydantic_obj.model_dump()
                self.level_field.value = str(stats_dict.get("level", ""))
                self.hp_field.value = str(stats_dict.get("hp", ""))
                self.ac_field.value = str(stats_dict.get("ac", ""))
                self.attributes_field.value = json.dumps(stats_dict, indent=2)
                self.page.open(ft.SnackBar(ft.Text("Stats generated successfully!"), bgcolor=ft.Colors.GREEN))
            else:
                self.page.open(ft.SnackBar(ft.Text("Failed to generate stats from AI."), bgcolor=ft.Colors.RED))
        finally:
            self.generate_stats_button.disabled = False
            self.attribute_loading_indicator.visible = False
            self.update()

    async def save_character_clicked(self, e):
        """
        Saves the character data to the Supabase database.
        """
        print("--- 'Save' button clicked. ---")
        if not self.current_npc_data:
            self.page.open(
                ft.SnackBar(ft.Text("No NPC data to save. Please generate data first."), bgcolor=ft.Colors.ORANGE))
            return

        print("--- 'Save' button clicked. ---")
        self.save_loading_indicator.visible = True
        self.save_button.disabled = True
        self.update()

        try:
            # Pydantic's model_dump() creates a dictionary perfect for JSONB.
            attributes_data = self.current_character_stats.model_dump() if self.current_character_stats else {}

            # Build the dictionary from our state objects and dropdowns
            character_data = {
                "name": self.current_npc_data.name,
                "gender": self.current_npc_data.gender,
                "appearance": {self.selected_language: self.current_npc_data.appearance},
                "personality": {self.selected_language: self.current_npc_data.personality},
                "backstory": {self.selected_language: self.current_npc_data.backstory},
                "plot_hooks": {self.selected_language: self.current_npc_data.plot_hooks},
                "roleplaying_tips": {self.selected_language: self.current_npc_data.roleplaying_tips},
                "attributes": attributes_data,
                "notes": {self.selected_language: self.notes_field.value},  # Notes are still manual input
                # These are selections, so we still read them from the UI
                "rarity": self.rarity_dropdown.value,
                "hostility": self.attitude_dropdown.value,
                "race": self.race_dropdown.value,
                "class": self.class_dropdown.value,
                "environment": self.environment_dropdown.value,
                "background": self.background_dropdown.value,
                "custom_prompt": self.custom_prompt_field.value,
                "portrait_url": self.portrait_image.src if self.portrait_image.src and self.portrait_image.src.startswith(
                    "http") else None,
            }

            if self.is_new_character:
                print("--- Creating new character... ---")
                character_data["campaign_id"] = self.campaign_id
                character_data["character_type"] = "NPC"
                response = await supabase.create_character(character_data)
            else:
                print(f"--- Updating character ID: {self.character_id} ---")
                response = await supabase.update_character(self.character_id, character_data)

            # Supabase-py-async responses might not have an 'error' attribute.
            # A successful operation returns a response where the data list is not empty.
            if response.data:
                self.page.open(ft.SnackBar(ft.Text("Character saved successfully!"), bgcolor=ft.Colors.GREEN))
                await asyncio.sleep(1)
                self.page.go("/characters")
            else:
                # The response object itself might contain error details
                raise Exception(str(response))

        except Exception as ex:
            print(f"Error saving character: {ex}")
            self.page.open(ft.SnackBar(ft.Text(f"Error saving character: {ex}"), bgcolor=ft.Colors.RED))
        finally:
            self.save_loading_indicator.visible = False
            self.save_button.disabled = False
            self.update()