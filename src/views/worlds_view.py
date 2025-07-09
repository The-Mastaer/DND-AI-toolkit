# src/views/worlds_view.py

import flet as ft
from ..state import AppState
from ..services.supabase_service import SupabaseService
from ..components.app_bar import AppBar
from ..components.new_world_dialog import NewWorldDialog


class WorldsView(ft.View):
    """
    The view for managing D&D worlds. Displays a list of worlds and allows
    for creation, deletion, and selection to navigate to campaigns.
    """

    def __init__(self, page: ft.Page, state: AppState, supabase_service: SupabaseService):
        super().__init__(route="/worlds")
        self.page = page
        self.state = state
        self.supabase_service = supabase_service

        self.app_bar = AppBar(
            title="Worlds",
            page=self.page,
            state=self.state,
            show_back_button=True
        )

        self.worlds_list = ft.ListView(expand=True, spacing=10)
        self.progress_ring = ft.ProgressRing()

        self.controls = [
            self.app_bar,
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text("Your Worlds", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                                ft.IconButton(
                                    icon=ft.Icons.ADD_CIRCLE_OUTLINE,
                                    tooltip="Create New World",
                                    on_click=self.open_new_world_dialog,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Divider(),
                        ft.Stack(
                            controls=[
                                self.worlds_list,
                                self.progress_ring,
                            ],
                            expand=True,
                        ),
                    ]
                ),
                padding=20,
                expand=True,
            )
        ]

        self.on_mount = self.load_worlds

    def load_worlds(self, e=None):
        """Fetches the user's worlds from Supabase and populates the list view."""
        print("WorldsView: load_worlds called.")
        self.progress_ring.visible = True
        self.worlds_list.visible = False
        if self.page: self.page.update()
        print("WorldsView: UI set to loading state.")

        user_id = self.state.user.get('id') if self.state.user else None
        if not user_id:
            self.show_error_snackbar("Could not load worlds: User not logged in.")
            self.progress_ring.visible = False
            if self.page: self.page.update()
            return

        try:
            print("WorldsView: Fetching worlds from Supabase...")
            worlds = self.supabase_service.get_worlds(user_id)
            print(f"WorldsView: Found {len(worlds)} worlds.")
            self.state.worlds = worlds
            self.worlds_list.controls.clear()

            if not worlds:
                self.worlds_list.controls.append(ft.Text("No worlds found. Create one to get started!"))
            else:
                for world in worlds:
                    self.worlds_list.controls.append(self.create_world_card(world))

        except Exception as ex:
            print(f"WorldsView: Error loading worlds - {ex}")
            self.show_error_snackbar(f"Failed to load worlds: {ex}")
            self.worlds_list.controls.append(ft.Text("Could not load worlds. Please try again later."))
        finally:
            self.progress_ring.visible = False
            self.worlds_list.visible = True
            print("WorldsView: UI updated with world list.")
            if self.page: self.page.update()

    def create_world_card(self, world: dict) -> ft.Card:
        """Creates a clickable Card control for a single world."""
        return ft.Card(
            content=ft.Container(
                padding=10,
                content=ft.Row(
                    controls=[
                        ft.Column(
                            [
                                ft.Text(world['name'], style=ft.TextThemeStyle.TITLE_LARGE),
                                ft.Text(world['lore'], max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                            ],
                            expand=True,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_FOREVER,
                            icon_color=ft.Colors.RED_400,
                            tooltip="Delete World",
                            data=world,
                            on_click=self.confirm_delete_world,
                        ),
                    ]
                ),
            ),
            on_click=self.world_clicked,
            data=world['id'],
        )

    def world_clicked(self, e: ft.ControlEvent):
        """Handles navigation when a world card is clicked."""
        world_id = e.control.data
        self.state.selected_world_id = world_id
        print(f"WorldsView: World {world_id} selected. Navigating to /campaigns.")
        self.page.go("/campaigns")

    def open_new_world_dialog(self, _: ft.ControlEvent):
        """Opens the dialog to create a new world."""
        print("WorldsView: open_new_world_dialog called.")
        user_id = self.state.user.get('id') if self.state.user else None
        if not user_id:
            self.show_error_snackbar("Cannot create world: User not logged in.")
            return

        # Alternative Solution: Use the on_dismiss event to refresh the list.
        # This is a more robust pattern than a direct callback.
        new_world_dialog = NewWorldDialog(
            supabase_service=self.supabase_service,
            user_id=user_id,
        )
        new_world_dialog.on_dismiss = self.on_dialog_dismiss
        self.page.dialog = new_world_dialog
        new_world_dialog.open = True
        print("WorldsView: Dialog opened.")
        self.page.update()

    def on_dialog_dismiss(self, e: ft.ControlEvent):
        """Called when the NewWorldDialog is dismissed."""
        print("WorldsView: on_dialog_dismiss called.")
        # The dialog's data attribute can be used to signal if a refresh is needed.
        if e.control.data == "created":
            print("WorldsView: Dialog signaled creation, reloading worlds.")
            self.load_worlds()
        else:
            print("WorldsView: Dialog was cancelled, no action taken.")

    def confirm_delete_world(self, e: ft.ControlEvent):
        """Shows a confirmation dialog before deleting a world."""
        world_to_delete = e.control.data
        print(f"WorldsView: confirm_delete_world called for world ID {world_to_delete['id']}.")

        confirm_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm Deletion"),
            content=ft.Text(f"Are you sure you want to permanently delete the world '{world_to_delete['name']}'?"),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self.close_dialog()),
                ft.FilledButton("Delete", on_click=lambda _: self.delete_world(world_to_delete['id']),
                                style=ft.ButtonStyle(bgcolor=ft.Colors.RED)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.dialog = confirm_dialog
        confirm_dialog.open = True
        self.page.update()

    def delete_world(self, world_id: int):
        """Deletes the world after confirmation."""
        print(f"WorldsView: delete_world called for world ID {world_id}.")
        self.close_dialog()
        try:
            self.supabase_service.delete_world(world_id)
            self.show_success_snackbar("World deleted successfully.")
            self.load_worlds()
        except Exception as e:
            self.show_error_snackbar(f"Failed to delete world: {e}")

    def close_dialog(self):
        """Helper function to close the current dialog."""
        if self.page.dialog:
            print("WorldsView: Closing dialog.")
            self.page.dialog.open = False
            self.page.update()

    def show_error_snackbar(self, message: str):
        """Displays a standardized error message in a SnackBar."""
        if self.page:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(message),
                bgcolor=ft.Colors.RED_700,
            )
            self.page.snack_bar.open = True
            self.page.update()

    def show_success_snackbar(self, message: str):
        """Displays a standardized success message in a SnackBar."""
        if self.page:
            self.page.snack_bar = ft.SnackBar(content=ft.Text(message))
            self.page.snack_bar.open = True
            self.page.update()
