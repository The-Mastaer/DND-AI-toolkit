import flet as ft
from src.state import AppState
from typing import List, Dict, Any, Optional


class WorldsView(ft.View):
    """
    A view to display and manage D&D worlds.
    This version uses a simplified, more stable pattern for handling dialogs,
    defining them in-place to ensure event handlers are correctly bound.
    """

    def __init__(self, page: ft.Page, app_state: AppState):
        super().__init__(route="/worlds", padding=20)
        self.page = page
        self.app_state = app_state
        self.worlds: List[Dict[str, Any]] = []
        self.selected_world: Optional[Dict[str, Any]] = None
        self.selected_lang = "en"

        # --- UI Controls ---
        self.world_list_view = ft.ListView(spacing=5, expand=True, padding=0)
        self.new_world_button = ft.ElevatedButton(
            "New World", icon=ft.Icons.ADD, on_click=self.open_new_world_dialog,
            width=250, style=ft.ButtonStyle(padding=15)
        )
        self.world_name_field = ft.TextField(label="World Name", read_only=True)
        self.world_lore_field = ft.TextField(label="World Lore", multiline=True, min_lines=8, read_only=True)
        self.language_dropdown = ft.Dropdown(label="Language", on_change=self.language_changed, disabled=True)
        self.translate_button = ft.ElevatedButton("Translate", icon=ft.Icons.TRANSLATE,
                                                  on_click=self.open_translate_dialog, disabled=True)
        self.save_button = ft.ElevatedButton("Save World", icon=ft.Icons.SAVE, on_click=self.save_world, disabled=True)

        # --- Layout ---
        left_column = ft.Column([
            ft.Text("Your Worlds", size=24, weight=ft.FontWeight.BOLD),
            ft.Container(content=self.world_list_view, expand=True),
            self.new_world_button
        ], expand=1, spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        self.editor_column = ft.Column([
            self.world_name_field,
            ft.Row([self.language_dropdown, self.translate_button], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            self.world_lore_field,
            self.save_button
        ], expand=3, spacing=10, visible=False)

        self.no_world_selected_text = ft.Text("Select a world from the list or create a new one.", size=18,
                                              text_align=ft.TextAlign.CENTER)

        right_container = ft.Container(
            content=ft.Column([self.editor_column, self.no_world_selected_text], alignment=ft.MainAxisAlignment.CENTER,
                              horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=3, padding=20, border=ft.border.all(1, ft.Colors.BLACK26), border_radius=10
        )
        self.controls = [ft.Row([left_column, ft.VerticalDivider(width=20), right_container], expand=True)]

    def did_mount(self):
        """Called after the view is added to the page. Triggers the data load."""
        self.page.run_task(self.load_worlds)

    async def load_worlds(self):
        """Asynchronously loads worlds and populates the list view."""
        self.world_list_view.controls.clear()
        self.worlds = await self.app_state.supabase_service.get_worlds()
        if self.worlds:
            for world in self.worlds:
                self.world_list_view.controls.append(self.create_world_tile_container(world))
        else:
            self.world_list_view.controls.append(ft.Text("No worlds found."))
        if self.page: self.page.update()

    def create_world_tile_container(self, world: Dict[str, Any]) -> ft.Container:
        """Creates a styled, clickable container for a world tile."""
        lore_obj = world.get("lore", {})
        subtitle = lore_obj.get("en", "No English lore available.")
        list_tile = ft.ListTile(
            title=ft.Text(world.get("name", "Unnamed World")),
            subtitle=ft.Text(subtitle, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
            leading=ft.Icon(ft.Icons.PUBLIC),
            trailing=ft.IconButton(icon=ft.Icons.DELETE_FOREVER, icon_color=ft.Colors.RED_400, tooltip="Delete World",
                                   data=world, on_click=self.open_delete_confirmation),
        )
        return ft.Container(content=list_tile, data=world, on_click=self.select_world,
                            border_radius=ft.border_radius.all(5), ink=True)

    def select_world(self, e):
        """Populates the editor with the data of the selected world."""
        self.selected_world = e.control.data
        self.world_name_field.value = self.selected_world.get("name", "")
        self.world_name_field.read_only = False
        self.update_language_options()
        self.language_changed()
        self.save_button.disabled = False
        self.translate_button.disabled = False
        self.editor_column.visible = True
        self.no_world_selected_text.visible = False
        for container in self.world_list_view.controls:
            if isinstance(container, ft.Container):
                container.bgcolor = ft.Colors.PRIMARY_CONTAINER if container.data.get("id") == self.selected_world.get(
                    "id") else None
        self.page.update()

    def update_language_options(self):
        """Updates the language dropdown based on available lore."""
        lore_obj = self.selected_world.get("lore", {})
        self.language_dropdown.options = [ft.dropdown.Option(lang) for lang in lore_obj.keys()]
        self.language_dropdown.value = "en" if "en" in lore_obj else (
            self.language_dropdown.options[0].key if self.language_dropdown.options else None)
        self.language_dropdown.disabled = False
        self.page.update()

    def language_changed(self, e=None):
        """Updates the lore text field when the language selection changes."""
        if not self.selected_world: return
        self.selected_lang = self.language_dropdown.value
        lore_obj = self.selected_world.get("lore", {})
        self.world_lore_field.value = lore_obj.get(self.selected_lang, "")
        self.world_lore_field.read_only = False
        self.page.update()

    async def save_world(self, e):
        """Saves changes to the currently selected world's name and lore."""
        if not self.selected_world: return
        world_id = self.selected_world.get("id")
        new_name = self.world_name_field.value
        current_lore = self.selected_world.get("lore", {})
        current_lore[self.selected_lang] = self.world_lore_field.value
        updated_world = await self.app_state.supabase_service.update_world(world_id, new_name, current_lore)
        if updated_world:
            self.selected_world = updated_world
            await self.load_worlds()
            self.page.snack_bar = ft.SnackBar(content=ft.Text(f"'{new_name}' has been saved."))
        else:
            self.page.snack_bar = ft.SnackBar(content=ft.Text("Error: Could not save world."), bgcolor=ft.Colors.ERROR)
        self.page.snack_bar.open = True
        self.page.update()

    def open_new_world_dialog(self, e):
        """Creates and shows a new world dialog in-place."""
        new_world_name_field = ft.TextField(label="World Name", autofocus=True)
        new_world_lore_field = ft.TextField(label="Initial Lore (English)", multiline=True, min_lines=3, max_lines=5)
        progress_ring = ft.ProgressRing(visible=False)

        def close_dialog(event):
            dialog.open = False
            self.page.update()

        async def create_world_and_close(event):
            if new_world_name_field.value:
                initial_lore = {"en": new_world_lore_field.value}
                await self.create_world(new_world_name_field.value, initial_lore)
                close_dialog(event)
            else:
                new_world_name_field.error_text = "World name cannot be empty"
                self.page.update()

        async def generate_lore(event):
            if not new_world_name_field.value:
                new_world_name_field.error_text = "Enter a world name first"
                self.page.update()
                return
            new_world_lore_field.value = ""
            progress_ring.visible = True
            generate_button.disabled = True
            self.page.update()
            description = await self.page.loop.run_in_executor(None, self.app_state.gemini_service.generate_world_lore,
                                                               new_world_name_field.value)
            new_world_lore_field.value = description
            progress_ring.visible = False
            generate_button.disabled = False
            self.page.update()

        generate_button = ft.ElevatedButton("Generate Lore", icon=ft.Icons.AUTO_AWESOME, on_click=generate_lore)

        dialog = ft.AlertDialog(
            modal=True, title=ft.Text("Create a New World"),
            content=ft.Column([
                new_world_name_field, new_world_lore_field,
                ft.Row([generate_button, progress_ring], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ]),
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.FilledButton("Create", on_click=create_world_and_close),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    async def create_world(self, name: str, lore: Dict[str, str]):
        """Callback to create a world and refresh the view."""
        await self.app_state.supabase_service.add_world(name, lore)
        await self.load_worlds()

    def open_translate_dialog(self, e):
        """Opens a dialog to translate the current world's lore."""
        if not self.selected_world: return
        current_lore_keys = self.selected_world.get("lore", {}).keys()
        all_languages = {"en": "English", "de": "German", "es": "Spanish", "fr": "French", "ja": "Japanese"}
        available_options = [ft.dropdown.Option(code, name) for code, name in all_languages.items() if
                             code not in current_lore_keys]

        lang_dropdown = ft.Dropdown(label="Target Language", options=available_options, autofocus=True)

        def close_dialog(event):
            dialog.open = False
            self.page.update()

        async def translate_and_close(event):
            if lang_dropdown.value:
                await self.translate_lore(lang_dropdown.value)
                close_dialog(event)

        dialog = ft.AlertDialog(
            modal=True, title=ft.Text("Translate World Lore"),
            content=ft.Column([lang_dropdown]),
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.FilledButton("Translate", on_click=translate_and_close, disabled=not available_options),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    async def translate_lore(self, target_lang_code: str):
        """Translates the lore and saves the updated world."""
        source_lore = self.world_lore_field.value
        if not source_lore:
            self.page.snack_bar = ft.SnackBar(content=ft.Text("Error: No text to translate."), bgcolor=ft.Colors.ERROR)
            self.page.snack_bar.open = True
            self.page.update()
            return
        translated_text = await self.page.loop.run_in_executor(None, self.app_state.gemini_service.translate_text,
                                                               source_lore, target_lang_code, self.selected_lang)
        current_lore = self.selected_world.get("lore", {})
        current_lore[target_lang_code] = translated_text
        await self.save_world(None)
        self.update_language_options()
        self.language_dropdown.value = target_lang_code
        self.language_changed()

    def open_delete_confirmation(self, e):
        """Opens a confirmation dialog before deleting a world."""
        world_to_delete = e.control.data

        def close_dialog(event):
            dialog.open = False
            self.page.update()

        def confirm_delete(event):
            close_dialog(event)
            self.page.run_task(self.delete_world, world_to_delete.get("id"))

        dialog = ft.AlertDialog(modal=True, title=ft.Text("Please confirm"),
                                content=ft.Text(f"Are you sure you want to delete '{world_to_delete.get('name')}'?"),
                                actions=[ft.TextButton("Cancel", on_click=close_dialog),
                                         ft.FilledButton("Delete", on_click=confirm_delete, autofocus=True)],
                                actions_alignment=ft.MainAxisAlignment.END)
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    async def delete_world(self, world_id: int):
        """Deletes a world and refreshes the list."""
        success = await self.app_state.supabase_service.delete_world(world_id)
        if success:
            await self.load_worlds()
            if self.selected_world and self.selected_world.get("id") == world_id:
                self.editor_column.visible = False
                self.no_world_selected_text.visible = True
                self.selected_world = None
            self.page.update()
        else:
            self.page.snack_bar = ft.SnackBar(content=ft.Text("Error: Could not delete world."),
                                              bgcolor=ft.Colors.ERROR)
            self.page.snack_bar.open = True
            self.page.update()