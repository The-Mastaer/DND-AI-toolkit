# src/components/new_world_dialog.py

import flet as ft
from ..services.supabase_service import SupabaseService


class NewWorldDialog(ft.AlertDialog):
    """
    A dialog component for creating a new world.
    It signals its result using the 'data' attribute upon closing.
    """

    def __init__(self, supabase_service: SupabaseService, user_id: str):
        super().__init__()
        self.supabase_service = supabase_service
        self.user_id = user_id

        # This attribute will be checked by the on_dismiss handler in the parent view.
        self.data = "cancelled"

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
        Handles the 'Create' button click. On success, it sets a data flag
        and then closes itself, triggering the on_dismiss event in the parent.
        """
        print("NewWorldDialog: 'Create' button clicked.")
        name = self.name_field.value
        lore = self.lore_field.value

        if not name:
            self.name_field.error_text = "World name cannot be empty"
            self.page.update()
            return

        create_button = e.control
        create_button.disabled = True
        create_button.text = "Creating..."
        self.page.update()
        print("NewWorldDialog: UI locked for creation.")

        try:
            print("NewWorldDialog: Calling Supabase to create world...")
            self.supabase_service.create_world(self.user_id, name, lore)
            print("NewWorldDialog: Supabase call successful.")

            self.page.snack_bar = ft.SnackBar(ft.Text(f"World '{name}' created successfully!"))
            self.page.snack_bar.open = True

            # Set the data attribute to signal success to the on_dismiss handler
            self.data = "created"

            # Now, close the dialog. This will trigger on_dismiss in WorldsView.
            self.open = False
            self.page.update()
            print("NewWorldDialog: Dialog closed, signaling 'created'.")

        except Exception as ex:
            print(f"NewWorldDialog: Error creating world - {ex}")
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error creating world: {ex}"),
                bgcolor=ft.Colors.RED_700
            )
            self.page.snack_bar.open = True
            create_button.disabled = False
            create_button.text = "Create"
            self.page.update()

    def close_dialog(self, _: ft.ControlEvent):
        """Closes the dialog without signaling success."""
        print("NewWorldDialog: 'Cancel' or close action triggered.")
        self.data = "cancelled"
        self.open = False
        self.page.update()
