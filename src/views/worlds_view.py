import flet as ft
from src.state import AppState
from src.components.new_world_dialog import NewWorldDialog
from typing import List, Dict, Any


class WorldsView(ft.View):
    """
    A view to display and manage D&D worlds.
    This view now includes functionality to add and delete worlds.
    """

    def __init__(self, page: ft.Page, app_state: AppState):
        super().__init__(
            route="/worlds",
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            vertical_alignment=ft.MainAxisAlignment.START
        )
        self.page = page
        self.app_state = app_state
        self.worlds: List[Dict[str, Any]] = []

        # UI Controls
        self.loading_indicator = ft.ProgressRing(visible=True)
        self.world_list_view = ft.ListView(spacing=10, expand=True)
        self.error_text = ft.Text(visible=False, color=ft.Colors.ERROR)

        self.controls = [
            ft.Row([ft.Text("Worlds", size=32, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.CENTER),
            self.loading_indicator,
            self.error_text,
            self.world_list_view,
        ]

        self.fab = ft.FloatingActionButton(
            icon=ft.Icons.ADD,
            text="New World",
            on_click=self.open_new_world_dialog
        )

        self.on_view_load = self.load_worlds

    async def load_worlds(self):
        """Asynchronously loads worlds from the Supabase service and updates the UI."""
        self.loading_indicator.visible = True
        self.world_list_view.controls.clear()
        self.page.update()

        self.worlds = await self.app_state.supabase_service.get_worlds()
        self.loading_indicator.visible = False

        if not self.worlds and not self.app_state.supabase_service.client:
            self.error_text.value = "Error: Supabase client not initialized."
            self.error_text.visible = True
        else:
            self.error_text.visible = False
            if not self.worlds:
                self.world_list_view.controls.append(
                    ft.Text("No worlds found. Create one to get started!")
                )
            else:
                for world in self.worlds:
                    self.world_list_view.controls.append(self.create_world_tile(world))

        self.page.update()

    def create_world_tile(self, world: Dict[str, Any]) -> ft.ListTile:
        """Creates a ListTile control for a given world."""
        return ft.ListTile(
            title=ft.Text(world.get("name", "Unnamed World")),
            subtitle=ft.Text(world.get("description", "No description."), max_lines=2),
            leading=ft.Icon(ft.Icons.PUBLIC),
            trailing=ft.IconButton(
                icon=ft.Icons.DELETE_FOREVER,
                icon_color=ft.Colors.RED_400,
                tooltip="Delete World",
                data=world,  # Attach world data to the button
                on_click=self.open_delete_confirmation,
            ),
            on_click=self.world_clicked,
            data=world,
        )

    def world_clicked(self, e):
        """Handler for when a world list tile is clicked."""
        world_name = e.control.data.get("name")
        self.page.snack_bar = ft.SnackBar(content=ft.Text(f"Clicked on '{world_name}'"))
        self.page.snack_bar.open = True
        self.page.update()

    def open_new_world_dialog(self, e):
        """Opens the dialog to create a new world."""
        dialog = NewWorldDialog(self.app_state.gemini_service, self.create_world)
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    async def create_world(self, name: str, description: str):
        """Callback function to create a world and refresh the view."""
        new_world = await self.app_state.supabase_service.add_world(name, description)
        if new_world:
            # Add the new world to the top of the list for immediate feedback
            self.world_list_view.controls.insert(0, self.create_world_tile(new_world))
            if len(self.world_list_view.controls) == 1 and isinstance(self.world_list_view.controls[0], ft.Text):
                self.world_list_view.controls.clear()  # Clear "No worlds found" message
                self.world_list_view.controls.append(self.create_world_tile(new_world))
            self.page.update()
        else:
            self.page.snack_bar = ft.SnackBar(content=ft.Text("Error: Could not create world."),
                                              bgcolor=ft.Colors.ERROR)
            self.page.snack_bar.open = True
            self.page.update()

    def open_delete_confirmation(self, e):
        """Opens a confirmation dialog before deleting a world."""
        world_to_delete = e.control.data

        def confirm_delete(event):
            self.page.dialog.open = False
            self.page.update()
            # We need to run the async delete in a task
            self.page.run_task(self.delete_world, world_to_delete.get("id"))

        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Please confirm"),
            content=ft.Text(f"Are you sure you want to delete the world '{world_to_delete.get('name')}'?"),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self.close_dialog()),
                ft.FilledButton("Delete", on_click=confirm_delete),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = confirm_dialog
        confirm_dialog.open = True
        self.page.update()

    async def delete_world(self, world_id: int):
        """Deletes a world and refreshes the list."""
        success = await self.app_state.supabase_service.delete_world(world_id)
        if success:
            # Find and remove the tile from the view
            self.world_list_view.controls = [
                tile for tile in self.world_list_view.controls
                if tile.data.get("id") != world_id
            ]
            if not self.world_list_view.controls:
                self.world_list_view.controls.append(ft.Text("No worlds found."))
            self.page.update()
        else:
            self.page.snack_bar = ft.SnackBar(content=ft.Text("Error: Could not delete world."),
                                              bgcolor=ft.Colors.ERROR)
            self.page.snack_bar.open = True
            self.page.update()

    def close_dialog(self):
        self.page.dialog.open = False
        self.page.update()
