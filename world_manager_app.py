import logging
import flet as ft
from config import SUPPORTED_LANGUAGES


class WorldManagerApp(ft.AlertDialog):
    def __init__(self, main_view, data_manager, api_service):
        super().__init__(modal=True, title=ft.Text("World Manager"), content_padding=ft.padding.all(5))
        self.main_view = main_view
        self.page = main_view.page
        self.db = data_manager
        self.ai = api_service
        self.worlds_in_current_lang = []
        self.selected_world_data = None

        self.language_dropdown = ft.Dropdown(
            options=[ft.dropdown.Option(code, name) for code, name in SUPPORTED_LANGUAGES.items()],
            value=self.main_view.settings.get("active_language", "en"),
            on_change=self.on_language_change,
            expand=True,
        )
        self.world_list_view = ft.ListView(expand=True, spacing=5)
        self.world_name_entry = ft.TextField(label="World Name", border_radius=10, disabled=True)
        self.world_lore_textbox = ft.TextField(
            label="World Lore", multiline=True, min_lines=15, max_lines=15, expand=True, border_radius=10, disabled=True
        )
        self.status_label = ft.Text("Select a world or create a new one.", italic=True)
        self.new_button = ft.ElevatedButton("New", icon=ft.Icons.ADD, on_click=self.new_world)
        self.delete_button = ft.IconButton(ft.Icons.DELETE_FOREVER, icon_color="red", tooltip="Delete Selected World",
                                           on_click=self.delete_selected_world, disabled=True)

        sidebar = ft.Column(
            [
                ft.Text("Your Worlds", size=20, weight=ft.FontWeight.BOLD),
                ft.Row([ft.Text("Language:"), self.language_dropdown]),
                ft.Container(content=self.world_list_view, expand=True, border_radius=10, padding=5),
                ft.Row([self.new_button, self.delete_button], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ],
            width=300, spacing=10, horizontal_alignment=ft.CrossAxisAlignment.STRETCH
        )
        main_content = ft.Column(
            [self.world_name_entry, self.world_lore_textbox, self.status_label],
            expand=True, spacing=10
        )
        self.content = ft.Container(
            content=ft.Row([sidebar, main_content], expand=True, vertical_alignment=ft.CrossAxisAlignment.STRETCH),
            width=1000, height=650
        )
        self.actions = [
            ft.ElevatedButton("Save", icon=ft.Icons.SAVE, on_click=self.save_world, disabled=True),
            ft.ElevatedButton("Translate...", icon=ft.Icons.TRANSLATE, on_click=self.open_translate_dialog,
                              disabled=True),
            ft.ElevatedButton("Manage Campaigns", icon=ft.Icons.GROUP_WORK, on_click=self.open_campaign_manager,
                              disabled=True),
            ft.ElevatedButton("Close", on_click=self.close_dialog)
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    async def load_and_display_worlds(self):
        active_lang = self.language_dropdown.value
        # Running database calls in a thread to not block the UI
        self.worlds_in_current_lang = await self.page.run_in_executor(
            None, self.db.get_all_worlds, active_lang
        )
        self.world_list_view.controls.clear()
        for world_data in self.worlds_in_current_lang:
            world_button = ft.ElevatedButton(
                text=world_data['world_name'],
                on_click=lambda e, w=world_data: self.select_world(w),
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5))
            )
            self.world_list_view.controls.append(world_button)

        await self._clear_main_panel()

    async def select_world(self, world_data):
        self.selected_world_data = world_data
        self.world_name_entry.value = world_data.get("world_name", "")
        self.world_lore_textbox.value = world_data.get("world_lore", "")
        self.status_label.value = f"Editing '{world_data.get('world_name')}'"

        self.world_name_entry.disabled = False
        self.world_lore_textbox.disabled = False
        self.delete_button.disabled = False
        self.actions[0].disabled = False
        self.actions[1].disabled = False
        self.actions[2].disabled = False

        await self.highlight_selected_world()
        await self.update_async()

    async def highlight_selected_world(self):
        if not self.selected_world_data: return
        for button in self.world_list_view.controls:
            is_selected = (button.on_click.keywords['w']['world_id'] == self.selected_world_data['world_id'])
            button.style.bgcolor = ft.colors.TEAL_600 if is_selected else "transparent"

    async def new_world(self, e=None):
        self.selected_world_data = None
        self.world_name_entry.value = ""
        self.world_lore_textbox.value = ""
        self.status_label.value = f"Creating new world in {SUPPORTED_LANGUAGES[self.language_dropdown.value]}"

        self.world_name_entry.disabled = False
        self.world_lore_textbox.disabled = False
        self.delete_button.disabled = True
        self.actions[0].disabled = False
        self.actions[1].disabled = True
        self.actions[2].disabled = True

        for button in self.world_list_view.controls:
            button.style.bgcolor = "transparent"
        await self.update_async()

    async def _clear_main_panel(self):
        self.selected_world_data = None
        self.world_name_entry.value = ""
        self.world_lore_textbox.value = ""
        self.world_name_entry.disabled = True
        self.world_lore_textbox.disabled = True
        self.status_label.value = "Select a world from the list or create a new one."
        self.delete_button.disabled = True
        self.actions[0].disabled = True
        self.actions[1].disabled = True
        self.actions[2].disabled = True
        for button in self.world_list_view.controls:
            button.style.bgcolor = "transparent"
        await self.update_async()

    async def save_world(self, e):
        name = self.world_name_entry.value.strip()
        lore = self.world_lore_textbox.value.strip()
        lang = self.language_dropdown.value
        if not name:
            self.status_label.value = "Error: World Name cannot be empty."
            await self.update_async()
            return
        try:
            if self.selected_world_data:
                world_id = self.selected_world_data['world_id']
                await self.page.run_in_executor(None, self.db.update_world_translation, world_id, lang, name, lore)
            else:
                world_id = await self.page.run_in_executor(None, self.db.create_world, name, lang, lore)

            await self.load_and_display_worlds()

            newly_selected = next((w for w in self.worlds_in_current_lang if w['world_id'] == world_id), None)
            if newly_selected:
                await self.select_world(newly_selected)

            self.status_label.value = "World saved successfully!"
        except Exception as ex:
            logging.error(f"Error saving world: {ex}")
            self.status_label.value = "Error: Could not save world."
        await self.update_async()

    async def delete_selected_world(self, e):
        if not self.selected_world_data: return

        async def confirm_delete(e):
            try:
                await self.page.run_in_executor(None, self.db.delete_world, self.selected_world_data['world_id'])
                await self.load_and_display_worlds()
                self.status_label.value = "World deleted successfully."
            except Exception as ex:
                logging.error(f"Error deleting world: {ex}")
                self.status_label.value = "Error: Could not delete world."

            confirm_dialog.open = False
            await self.page.update_async()

        async def cancel_delete(e):
            confirm_dialog.open = False
            await self.page.update_async()

        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm Deletion"),
            content=ft.Text(
                f"Are you sure you want to delete '{self.selected_world_data['world_name']}'?\nThis will delete ALL associated data and cannot be undone."),
            actions=[
                ft.ElevatedButton("Delete", on_click=confirm_delete, color="white", bgcolor=ft.colors.RED),
                ft.ElevatedButton("Cancel", on_click=cancel_delete)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        self.page.dialog = confirm_dialog
        confirm_dialog.open = True
        await self.page.update_async()

    async def on_language_change(self, e):
        await self.load_and_display_worlds()

    async def close_dialog(self, e):
        self.open = False
        self.main_view.refresh_display()
        await self.page.update_async()

    async def open_campaign_manager(self, e):
        self.page.snack_bar = ft.SnackBar(ft.Text("Campaign Manager not yet implemented in Flet."))
        self.page.snack_bar.open = True
        await self.page.update_async()

    async def open_translate_dialog(self, e):
        self.page.snack_bar = ft.SnackBar(ft.Text("Translate dialog not yet implemented in Flet."))
        self.page.snack_bar.open = True
        await self.page.update_async()