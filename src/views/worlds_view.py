# src/views/worlds_view.py

import flet as ft
from services.supabase_service import supabase
from services.gemini_service import GeminiService
from config import SUPPORTED_LANGUAGES
from components.translate_dialog import TranslateDialog
import asyncio


class WorldsView(ft.View):
    """
    A view for managing game worlds. It allows creating, editing,
    deleting, and translating worlds.
    """

    def __init__(self, page: ft.Page, gemini_service: GeminiService):
        """
        Initializes the WorldsView.

        Args:
            page (ft.Page): The Flet page object.
            gemini_service (GeminiService): The singleton instance of the Gemini service.
        """
        super().__init__()
        self.page = page
        self.route = "/worlds"
        self.gemini_service = gemini_service

        # --- State Management ---
        self.worlds_data = []
        self.selected_world_data = None
        self.current_language_code = 'en'

        # --- Dialogs ---
        self.translate_dialog = TranslateDialog(self.page, self.gemini_service, self.refresh_view)
        self.page.overlay.append(self.translate_dialog)
        # --- UI Controls ---
        self.appbar = ft.AppBar(
            title=ft.Text("World Manager"),
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda _: self.page.go("/")),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        )
        self.worlds_list = ft.ListView(expand=True, spacing=5)
        self.world_name_field = ft.TextField(label="World Name", disabled=True)
        self.world_lore_field = ft.TextField(label="World Lore", multiline=True, min_lines=10, disabled=True,
                                             expand=True)
        self.language_dropdown = ft.Dropdown(
            label="Language",
            options=[ft.dropdown.Option(code, name) for code, name in SUPPORTED_LANGUAGES.items()],
            value=self.current_language_code,
            on_change=self.language_changed,
            disabled=True
        )
        self.new_button = ft.ElevatedButton("New World", icon=ft.Icons.ADD, on_click=self.new_world_click)
        self.delete_button = ft.ElevatedButton("Delete World", icon=ft.Icons.DELETE_FOREVER, color=ft.Colors.WHITE,
                                               bgcolor=ft.Colors.RED_700, on_click=self.delete_world_click,
                                               disabled=True)
        self.campaigns_button = ft.ElevatedButton("Manage Campaigns", icon=ft.Icons.MAP,
                                                  on_click=self.manage_campaigns_click, disabled=True)
        self.translate_button = ft.ElevatedButton("Translate Lore", icon=ft.Icons.TRANSLATE,
                                                  on_click=self.translate_click, disabled=True)
        self.save_button = ft.FilledButton("Save World", icon=ft.Icons.SAVE, on_click=self.save_world_click,
                                           disabled=True)

        # --- Layout ---
        left_column = ft.Column(
            [
                ft.Text("Your Worlds", style=ft.TextThemeStyle.HEADLINE_SMALL),
                ft.Container(self.worlds_list, border=ft.border.all(1), border_radius=5, expand=True, padding=5),
                ft.Row([self.new_button, self.delete_button], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ],
            expand=1,
            spacing=10
        )

        right_column = ft.Column(
            [
                ft.Row([self.language_dropdown, self.campaigns_button, self.translate_button]),
                self.world_name_field,
                self.world_lore_field,
                ft.Row([self.save_button], alignment=ft.MainAxisAlignment.END)
            ],
            expand=3,
            spacing=10
        )

        self.controls = [
            ft.Row(
                [left_column, ft.VerticalDivider(width=1), right_column],
                expand=True,
                spacing=20,
            ),
        ]

    def did_mount(self):
        """Load initial data when the view is displayed."""
        self.page.run_task(self.load_initial_data)

    async def load_initial_data(self):
        """Fetches worlds from the database and populates the list."""
        self.current_language_code = await asyncio.to_thread(self.page.client_storage.get,
                                                             "active_language_code") or 'en'
        self.language_dropdown.value = self.current_language_code
        await self.get_worlds()

    async def get_worlds(self):
        """Fetches the list of worlds for the current user and updates the UI."""
        self.worlds_list.controls.clear()
        self.worlds_list.controls.append(ft.ProgressRing())
        self.update()

        try:
            # DEBUG FIX: Fetch only worlds for the current user.
            user = await supabase.get_user()
            if not user:
                raise Exception("Authentication error, user not found.")

            response = await supabase.client.from_('worlds').select("*").eq('user_id', user.id).execute()
            self.worlds_data = response.data
            self.worlds_list.controls.clear()
            if self.worlds_data:
                for world in self.worlds_data:
                    self.worlds_list.controls.append(
                        ft.ListTile(
                            title=ft.Text(world['name']),
                            on_click=self.world_selected,
                            data=world,
                        )
                    )
                # Auto-select the first world if none is selected
                if not self.selected_world_data and self.worlds_data:
                    await self.select_world(self.worlds_data[0])
            else:
                self.worlds_list.controls.append(ft.Text("No worlds found. Create one!"))
        except Exception as e:
            self.worlds_list.controls.clear()
            self.worlds_list.controls.append(ft.Text(f"Error loading worlds: {e}", color=ft.Colors.RED))
        self.update()

    async def world_selected(self, e):
        """Handles the selection of a world from the list."""
        await self.select_world(e.control.data)

    async def select_world(self, world_data):
        """Updates the UI with the data of the selected world."""
        self.selected_world_data = world_data
        self.world_name_field.value = self.selected_world_data['name']
        self.world_lore_field.value = self.selected_world_data.get('lore', {}).get(self.current_language_code, "")
        self.enable_fields()
        await asyncio.to_thread(self.page.client_storage.set, "active_world_id", self.selected_world_data['id'])
        self.update()

    def enable_fields(self, is_new=False):
        """Enables or disables form fields based on selection state."""
        is_selected = self.selected_world_data is not None or is_new
        self.world_name_field.disabled = not is_selected
        self.world_lore_field.disabled = not is_selected
        self.language_dropdown.disabled = not is_selected
        self.delete_button.disabled = not is_selected or is_new
        self.campaigns_button.disabled = not is_selected or is_new
        self.translate_button.disabled = not is_selected or is_new
        self.save_button.disabled = not is_selected

    def new_world_click(self, e):
        """Handles the 'New World' button click, clearing fields for new entry."""
        self.selected_world_data = None
        self.world_name_field.value = ""
        self.world_lore_field.value = ""
        self.enable_fields(is_new=True)
        self.world_name_field.focus()
        self.update()

    async def save_world_click(self, e):
        """Saves a new or existing world to the database."""
        if not self.world_name_field.value:
            self.page.snack_bar = ft.SnackBar(ft.Text("World Name is required.", color=ft.Colors.RED))
            self.page.snack_bar.open = True
            self.update()
            return

        try:
            if self.selected_world_data:  # Update existing world
                lore = self.selected_world_data.get('lore', {})
                lore[self.current_language_code] = self.world_lore_field.value
                updates = {'name': self.world_name_field.value, 'lore': lore}
                await supabase.client.from_('worlds').update(updates).eq('id',
                                                                         self.selected_world_data['id']).execute()
            else:  # Create new world
                new_world = {
                    'name': self.world_name_field.value,
                    'lore': {self.current_language_code: self.world_lore_field.value}
                }
                await supabase.client.from_('worlds').insert(new_world).execute()

            self.page.snack_bar = ft.SnackBar(ft.Text("World saved successfully!"), bgcolor=ft.Colors.GREEN)
            await self.get_worlds()
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error saving world: {ex}"), color=ft.Colors.RED)
        finally:
            self.page.snack_bar.open = True
            self.update()

    async def delete_world_click(self, e):
        """Handles the deletion of the currently selected world."""
        if self.selected_world_data:
            try:
                await supabase.client.from_('worlds').delete().eq('id', self.selected_world_data['id']).execute()
                self.selected_world_data = None
                self.world_name_field.value = ""
                self.world_lore_field.value = ""
                self.enable_fields()
                await self.get_worlds()
                self.page.snack_bar = ft.SnackBar(ft.Text("World deleted."), bgcolor=ft.Colors.GREEN)
            except Exception as ex:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Error deleting world: {ex}"), color=ft.Colors.RED)
            finally:
                self.page.snack_bar.open = True
                self.update()

    async def language_changed(self, e):
        """Handles language change and updates the displayed lore."""
        self.current_language_code = e.control.value
        await asyncio.to_thread(self.page.client_storage.set, "active_language_code", self.current_language_code)
        if self.selected_world_data:
            self.world_lore_field.value = self.selected_world_data.get('lore', {}).get(self.current_language_code, "")
            self.update()

    def translate_click(self, e):
        """Opens the translation dialog."""
        if self.selected_world_data:
            self.translate_dialog.open_dialog(self.selected_world_data, self.current_language_code)
            print("Opening dialog")

    def manage_campaigns_click(self, e):
        """Navigates to the campaign management view for the selected world."""
        if self.selected_world_data:
            self.page.go("/campaigns")

    async def refresh_view(self):
        """Callback function to refresh the view, typically after a dialog action."""
        await self.get_worlds()
