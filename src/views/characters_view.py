# src/views/characters_view.py

import flet as ft
from ..services.supabase_service import supabase
from ..services.gemini_service import GeminiService
import asyncio


class CharactersView(ft.View):
    """
    A view that displays a list of characters and handles navigation
    to the character creation/editing form.
    """
    # DEBUG FIX: Corrected __init__ to accept gemini_service
    def __init__(self, page: ft.Page, gemini_service: GeminiService):
        """
        Initializes the CharactersView.

        Args:
            page (ft.Page): The Flet page object.
            gemini_service (GeminiService): The singleton instance of the Gemini service.
        """
        super().__init__()
        self.page = page
        self.route = "/characters"
        self.gemini_service = gemini_service

        self.appbar = ft.AppBar(
            title=ft.Text("Characters"),
            leading=ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                on_click=self.go_back,
                tooltip="Back to Dashboard"
            ),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST
        )

        # UI Controls
        self.add_character_button = ft.IconButton(
            icon=ft.Icons.ADD_CIRCLE_OUTLINE,
            tooltip="Create New Character",
            on_click=self.open_new_character_form,
            disabled=True
        )
        self.character_type_filter = ft.SegmentedButton(
            selected={"NPC"},
            segments=[
                ft.Segment(value="NPC", label=ft.Text("NPCs")),
                ft.Segment(value="PC", label=ft.Text("PCs")),
            ],
            on_change=self._on_character_type_change,
            allow_empty_selection=False,
        )
        self.characters_list = ft.ListView(expand=True, spacing=10)
        self.progress_ring = ft.ProgressRing(width=32, height=32, stroke_width=4)

        # State
        self.selected_campaign_id = None

        self.controls = [
            ft.Column(
                [
                    ft.Row(
                        controls=[self.add_character_button],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                    ft.Divider(height=1),
                    ft.Row(
                        [self.character_type_filter],
                        alignment=ft.MainAxisAlignment.CENTER
                    ),
                    ft.Container(
                        content=self.characters_list,
                        expand=True,
                        padding=ft.padding.only(top=10)
                    )
                ],
                expand=True,
                spacing=10
            )
        ]

    def go_back(self, e):
        """Navigates back to the main dashboard view."""
        self.page.go("/")

    def did_mount(self):
        """Called when the control is added to the page to fetch initial data."""
        self.page.run_task(self.load_initial_data)

    async def load_initial_data(self):
        """Asynchronously loads the active campaign ID and then fetches the characters."""
        self.selected_campaign_id = await asyncio.to_thread(self.page.client_storage.get, "active_campaign_id")
        self.add_character_button.disabled = self.selected_campaign_id is None
        await self._get_characters()
        self.update()

    def _on_character_type_change(self, e):
        """Handles the change in character type filter and re-fetches characters."""
        self.page.run_task(self._get_characters)

    async def _get_characters(self):
        """Asynchronously fetches characters from Supabase."""
        self.characters_list.controls.clear()
        self.characters_list.controls.append(
            ft.Row([self.progress_ring, ft.Text("Loading...")], alignment=ft.MainAxisAlignment.CENTER)
        )
        self.update()

        if not self.selected_campaign_id:
            self.characters_list.controls.clear()
            self.characters_list.controls.append(
                ft.Column([
                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, size=48),
                    ft.Text("No Campaign Selected", style=ft.TextThemeStyle.HEADLINE_SMALL),
                    ft.Text("Go to Settings and select an active campaign to manage characters.",
                            text_align=ft.TextAlign.CENTER),
                    ft.ElevatedButton("Go to Settings", on_click=lambda _: self.page.go("/settings")),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10, expand=True,
                    alignment=ft.MainAxisAlignment.CENTER)
            )
            self.update()
            return

        current_character_type = list(self.character_type_filter.selected)[0]

        try:
            response = await supabase.client.from_('characters').select("*") \
                .eq('campaign_id', self.selected_campaign_id) \
                .eq('character_type', current_character_type).execute()

            self.characters_list.controls.clear()
            if response.data:
                for character in response.data:
                    self.characters_list.controls.append(
                        ft.ListTile(
                            title=ft.Text(character.get('name', 'Unnamed')),
                            subtitle=ft.Text(character.get('appearance', {}).get('en', 'No description.'), max_lines=2,
                                             overflow=ft.TextOverflow.ELLIPSIS),
                            leading=ft.CircleAvatar(
                                foreground_image_src=character.get('portrait_url'),
                                content=ft.Icon(ft.Icons.PERSON)
                            ),
                            trailing=ft.PopupMenuButton(items=[
                                ft.PopupMenuItem(text="Edit",
                                                 on_click=lambda e, char=character: self.open_edit_character_form(e,
                                                                                                                    char)),
                                ft.PopupMenuItem(text="Delete", icon=ft.Icons.DELETE,
                                                 on_click=lambda e, char_id=character['id']: self.delete_character(e,
                                                                                                                   char_id)),
                            ]),
                        )
                    )
            else:
                self.characters_list.controls.append(
                    ft.Container(
                        content=ft.Text(f"No {current_character_type} characters found. Create one!",
                                        text_align=ft.TextAlign.CENTER),
                        alignment=ft.alignment.center,
                        expand=True
                    )
                )
        except Exception as e:
            self.characters_list.controls.clear()
            self.characters_list.controls.append(ft.Text(f"Error loading characters: {e}", color=ft.Colors.RED))

        self.update()

    def open_new_character_form(self, e):
        """Navigates to the form to create a new character."""
        if self.selected_campaign_id:
            self.page.go(f"/character_edit/new/{self.selected_campaign_id}")

    def open_edit_character_form(self, e, character_data):
        """Navigates to the form to edit an existing character."""
        character_id = character_data.get('id')
        if character_id:
            self.page.go(f"/character_edit/{character_id}")

    def delete_character(self, e, character_id):
        """Shows a confirmation dialog before deleting."""

        def close_dialog(e):
            confirm_dialog.open = False
            self.page.update()

        async def confirm_action(e):
            close_dialog(e)
            await self._delete_character_async(character_id)

        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm Deletion"),
            content=ft.Text("Are you sure? This cannot be undone."),
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.FilledButton("Delete", on_click=confirm_action, style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = confirm_dialog
        confirm_dialog.open = True
        self.page.update()

    async def _delete_character_async(self, character_id):
        """Performs the asynchronous deletion."""
        try:
            await supabase.client.from_('characters').delete().eq('id', character_id).execute()
            self.page.snack_bar = ft.SnackBar(ft.Text("Character deleted."), bgcolor=ft.Colors.GREEN_700)
            await self._get_characters()
        except Exception as e:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {e}"), bgcolor=ft.Colors.RED_700)
        finally:
            self.page.snack_bar.open = True
            self.page.update()
