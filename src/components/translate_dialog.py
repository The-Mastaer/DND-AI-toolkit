# src/components/new_world_dialog.py

import flet as ft
from typing import Callable
from ..services.supabase_service import SupabaseService


class NewWorldDialog(ft.AlertDialog):
    """
    A dialog component for creating a new world.
    It is decoupled from the view that calls it by using a callback.
    """

    def __init__(self, supabase_service: SupabaseService, user_id: str, on_create_callback: Callable[[], None]):
        """
        Initializes the dialog.

        Args:
            supabase_service: An instance of the Supabase service for DB operations.
            user_id: The ID of the current user.
            on_create_callback: A function to call after a world is successfully created.
        """
        super().__init__()
        self.supabase_service = supabase_service
        self.user_id = user_id
        self.on_create_callback = on_create_callback

        self.modal = True
        self.title = ft.Text("Create New World")

        self.name_field = ft.TextField(label="World Name", autofocus=True)
        self.lore_field = ft.TextField(label="World Lore", multiline=True, min_lines=3)

        self.content = ft.Column(
            controls=[
                self.name_field,
                self.lore_field,
            ],
            spacing=10,
            tight=True,
        )

        self.actions = [
            ft.TextButton("Cancel", on_click=self.close_dialog),
            ft.FilledButton("Create", on_click=self.create_world),
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    def create_world(self, e: ft.ControlEvent):
        """
        Handles the 'Create' button click. Validates input and calls the
        Supabase service to create the new world.
        """
        name = self.name_field.value
        lore = self.lore_field.value

        if not name:
            self.name_field.error_text = "World name cannot be empty"
            self.page.update()
            return

        e.control.disabled = True
        e.control.text = "Creating..."
        self.page.update()

        try:
            self.supabase_service.create_world(self.user_id, name, lore)
            # Use a success snackbar on the page
            self.page.snack_bar = ft.SnackBar(ft.Text(f"World '{name}' created successfully!"))
            self.page.snack_bar.open = True

            self.on_create_callback()
            self.close_dialog(e)

        except Exception as ex:
            # Use an error snackbar on the page
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error creating world: {ex}"),
                bgcolor=ft.Colors.RED_700
            )
            self.page.snack_bar.open = True
        finally:
            e.control.disabled = False
            e.control.text = "Create"
            self.page.update()

    def close_dialog(self, _: ft.ControlEvent):
        """Closes the dialog. The event argument is unused but required by Flet."""
        self.open = False
        self.page.update()
