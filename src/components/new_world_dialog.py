import flet as ft
# --- Use relative imports to go up to 'src' and then down ---
from ..services.supabase_service import supabase

class NewWorldDialog(ft.AlertDialog):
    """
    A dialog window for creating a new world.
    It includes fields for the world's name and description
    and handles the database insertion.
    """
    def __init__(self, on_create_callback):
        super().__init__()
        self.on_create_callback = on_create_callback
        self.modal = True
        self.title = ft.Text("Create a New World")
        self.name_field = ft.TextField(label="World Name", autofocus=True)
        self.description_field = ft.TextField(label="Description", multiline=True, min_lines=3)
        self.content = ft.Column([self.name_field, self.description_field], tight=True)
        self.actions = [
            ft.TextButton("Cancel", on_click=self.close_dialog),
            ft.FilledButton("Create", on_click=self.create_world),
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    def create_world(self, e):
        """
        Validates input and inserts a new world record into the database.
        """
        if not self.name_field.value:
            self.name_field.error_text = "World name cannot be empty."
            self.name_field.update()
            return

        try:
            response = supabase.table('worlds').insert({
                'name': self.name_field.value,
                'description': self.description_field.value
            }).execute()
            print("World creation response:", response)

            if self.on_create_callback:
                self.on_create_callback()

            self.close_dialog(e)

        except Exception as ex:
            print(f"Error creating world: {ex}")
            self.title = ft.Text("Error")
            self.content = ft.Text(f"An error occurred: {ex}")
            self.actions = [ft.TextButton("Close", on_click=self.close_dialog)]
            self.update()


    def close_dialog(self, e):
        """
        Closes the dialog and clears the input fields.
        """
        self.open = False
        self.name_field.value = ""
        self.name_field.error_text = ""
        self.description_field.value = ""
        self.page.update()
