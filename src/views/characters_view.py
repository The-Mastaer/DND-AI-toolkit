# src/views/characters_view.py

import flet as ft
from ..services.supabase_service import supabase
from ..services.gemini_service import GeminiService # Keep import for type hinting
from ..components.translate_dialog import TranslateDialog
from ..components.character_form_dialog import CharacterFormDialog
import asyncio

class CharactersView(ft.Column):
    """
    A view that displays a list of characters for a selected campaign.
    Inherits from ft.Column to structure its content vertically.
    """
    def __init__(self, page: ft.Page): # Accept page and gemini_service
        super().__init__()
        self.page = page # Store page immediately
        self.route = "/characters"
        self.appbar = ft.AppBar(title=ft.Text("Characters"), bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST)
        self.expand = True
        self.spacing = 10

        self.characters_list = ft.ListView(expand=True, spacing=10)
        self.progress_ring = ft.ProgressRing(width=32, height=32, stroke_width=4)
        self.selected_campaign_id = None
        self.gemini_service = GeminiService() # Store the passed GeminiService instance

        # Refs for controls that need to be accessed later
        self.character_type_filter_ref = ft.Ref[ft.SegmentedButton]()

        # Initialize dialogs with page and gemini_service directly
        # on_save_callback will trigger a refresh of the character list
        self.translate_dialog = TranslateDialog(page=self.page, on_save_callback=self._get_characters)
        self.character_form_dialog = CharacterFormDialog(page=self.page, on_save_callback=self._get_characters, gemini_service=self.gemini_service)


        # Define the layout in the constructor
        self.controls = [
            ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.ADD,
                        tooltip="Create New Character",
                        on_click=self.open_new_character_dialog,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Divider(),
            # Character type filter (NPC/PC)
            ft.Row(
                [
                    ft.SegmentedButton(
                        ref=self.character_type_filter_ref,
                        selected={ "NPC" }, # Default selected
                        segments=[
                            ft.Segment(value="NPC", label=ft.Text("NPCs")),
                            ft.Segment(value="PC", label=ft.Text("PCs")),
                        ],
                        on_change=self._on_character_type_change,
                        allow_empty_selection=False,
                        allow_multiple_selection=False,
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER
            ),
            self.characters_list,
        ]

    def did_mount(self):
        """
        Called when the control is added to the page.
        Sets up the page reference for dialogs and fetches initial data.
        """
        self.page.run_task(self.load_initial_data)

    async def load_initial_data(self):
        self.selected_campaign_id = self.page.client_storage.get("active_campaign_id")
        # Enable/disable add button based on campaign selection
        self.controls[0].controls[1].disabled = self.selected_campaign_id is None

        # Add dialogs to overlay if not already present
        if self.translate_dialog not in self.page.overlay:
            self.page.overlay.append(self.translate_dialog)

        if self.character_form_dialog not in self.page.overlay:
            self.page.overlay.append(self.character_form_dialog)

        self.page.update() # Update page to ensure overlay is added

        self._get_characters()

    def _on_character_type_change(self, e):
        """
        Handles the change in character type filter (NPC/PC).
        """
        selected_value_set = e.control.selected
        if selected_value_set:
            self.selected_character_type = list(selected_value_set)[0]
        else:
            self.selected_character_type = "NPC"

        print(f"Character type filter changed to: {self.selected_character_type}")
        self._get_characters() # Re-fetch characters with the new filter

    def _get_characters(self):
        """
        Fetches characters from Supabase based on the selected_campaign_id and character_type.
        """
        self.characters_list.controls.clear()

        if not self.selected_campaign_id:
            self.characters_list.controls.append(
                ft.Column([
                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, size=48),
                    ft.Text("No Campaign Selected", style=ft.TextThemeStyle.HEADLINE_SMALL),
                    ft.Text(
                        "Please go back and select a campaign to see its characters.",
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.ElevatedButton("Go to Campaigns", on_click=lambda _: self.page.go("/campaigns")),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                expand=True,
                alignment=ft.MainAxisAlignment.CENTER,
                )
            )
            self.update()
            return

        self.characters_list.controls.append(
            ft.Row(
                [self.progress_ring, ft.Text("Loading characters...")],
                alignment=ft.MainAxisAlignment.CENTER, spacing=10
            )
        )
        self.update()

        current_character_type = list(self.character_type_filter_ref.current.selected)[0] if self.character_type_filter_ref.current and self.character_type_filter_ref.current.selected else "NPC"
        print(f"Fetching characters for campaign ID: {self.selected_campaign_id} and type: {current_character_type}")

        try:
            response = supabase.table('characters').select("*") \
                .eq('campaign_id', self.selected_campaign_id) \
                .eq('character_type', current_character_type) \
                .execute()

            self.characters_list.controls.clear()
            if response.data:
                for character in response.data:
                    character_name = character.get('name', '')
                    character_appearance = character.get('appearance', {}).get('en', 'N/A')

                    self.characters_list.controls.append(
                        ft.ListTile(
                            title=ft.Text(character_name),
                            subtitle=ft.Text(f"Appearance: {character_appearance}"),
                            leading=ft.CircleAvatar(
                                foreground_image_url=character.get('portrait_url'),
                                content=ft.Icon(ft.Icons.PERSON) if not character.get('portrait_url') else None,
                                color=ft.Colors.BLUE_GREY_700,
                            ),
                            trailing=ft.PopupMenuButton(
                                items=[
                                    ft.PopupMenuItem(text="Edit", on_click=lambda e, char=character: self.open_edit_character_dialog(e, char)),
                                    ft.PopupMenuItem(text="Translate (Coming Soon)", disabled=True),
                                    ft.PopupMenuItem(text="Migrate (Coming Soon)", disabled=True),
                                    ft.PopupMenuItem(text="Delete", icon=ft.Icons.DELETE, on_click=lambda e, char_id=character['id']: self.delete_character(e, char_id)),
                                ]
                            ),
                            on_click=lambda e, char=character: self.select_character(e, char),
                            data=character,
                        )
                    )
            else:
                self.characters_list.controls.append(ft.Text(f"No {current_character_type} characters found. Create one!"))

        except Exception as e:
            print(f"Error fetching characters: {e}")
            self.characters_list.controls.clear()
            self.characters_list.controls.append(ft.Text(f"Error loading characters: {e}"))

        self.update()

    def select_character(self, e, character_data):
        """
        Handles the selection of a character.
        """
        self.page.session.set("selected_character_id", character_data['id'])
        print(f"Selected Character ID: {character_data['id']} stored in session.")

    def open_new_character_dialog(self, e):
        """
        Opens a dialog for creating a new character.
        """
        if not self.selected_campaign_id:
            self.page.snack_bar = ft.SnackBar(content=ft.Text("Please select a campaign first to create a character."), bgcolor=ft.Colors.RED_700)
            self.page.snack_bar.open = True
            self.page.update()
            return
        self.character_form_dialog.open_dialog(character_data=None, campaign_id=self.selected_campaign_id)

    def open_edit_character_dialog(self, e, character_data):
        """
        Opens a dialog for editing an existing character.
        """
        self.character_form_dialog.open_dialog(character_data=character_data, campaign_id=self.selected_campaign_id)

    def open_translate_character_dialog(self, e, character_data):
        """
        Placeholder for opening translation dialog. Functionality will be added later.
        """
        self.page.snack_bar = ft.SnackBar(content=ft.Text("Character translation feature coming soon!"), bgcolor=ft.Colors.BLUE_GREY_700)
        self.page.snack_bar.open = True
        self.page.update()

    def open_migrate_character_dialog(self, e, character_data):
        """
        Placeholder for opening migration dialog. Functionality will be added later.
        """
        self.page.snack_bar = ft.SnackBar(content=ft.Text(f"Migrating {character_data['name']} coming soon!"), bgcolor=ft.Colors.BLUE_GREY_700)
        self.page.snack_bar.open = True
        self.page.update()

    def delete_character(self, e, character_id):
        """
        Deletes a character from the database.
        """
        print(f"Attempting to delete character with ID: {character_id}")
        self.page.run_task(self._delete_character_async, character_id)

    async def _delete_character_async(self, character_id):
        """
        Asynchronous deletion of a character.
        """
        try:
            confirm_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Confirm Deletion"),
                content=ft.Text("Are you sure you want to delete this character? This action cannot be undone."),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda e: self.close_dialog(e, confirm_dialog)),
                    ft.FilledButton("Delete", on_click=lambda e: self.confirm_delete_character(e, character_id, confirm_dialog), style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700)),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            self.page.dialog = confirm_dialog
            confirm_dialog.open = True
            self.page.update()

        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(content=ft.Text(f"Error preparing delete: {ex}"), bgcolor=ft.Colors.RED_700)
            self.page.snack_bar.open = True
            self.page.update()

    async def confirm_delete_character(self, e, character_id, dialog):
        """
        Confirms and proceeds with character deletion.
        """
        dialog.open = False
        self.page.update()

        try:
            await supabase.table('characters').delete().eq('id', character_id).execute()
            self.page.snack_bar = ft.SnackBar(content=ft.Text("Character deleted successfully!"), bgcolor=ft.Colors.GREEN_700)
            self.page.snack_bar.open = True
            self._get_characters()
        except Exception as ex:
            print(f"Error deleting character: {ex}")
            self.page.snack_bar = ft.SnackBar(content=ft.Text(f"Error deleting character: {ex}"), bgcolor=ft.Colors.RED_700)
            self.page.snack_bar.open = True
        self.page.update()

    def close_dialog(self, e, dialog):
        """Closes a given dialog."""
        dialog.open = False
        self.page.update()