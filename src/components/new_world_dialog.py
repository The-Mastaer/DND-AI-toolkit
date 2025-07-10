import flet as ft
# --- Use relative imports to go up to 'src' and then down ---
from ..services.supabase_service import supabase

class NewWorldDialog(ft.AlertDialog):
    """
    A dialog window for creating a new world.
    It includes fields for the world's name, its initial lore,
    and the language of the lore. It handles the database insertion.
    """
    def __init__(self, on_create_callback):
        super().__init__()
        self.on_create_callback = on_create_callback
        self.modal = True
        self.title = ft.Text("Create a New World")

        self.name_field = ft.TextField(label="World Name", autofocus=True)
        self.language_dropdown = ft.Dropdown(
            label="Language",
            options=[
                ft.dropdown.Option("en", "English"),
                ft.dropdown.Option("de", "German"),
                ft.dropdown.Option("es", "Spanish"),
                ft.dropdown.Option("fr", "French"),
            ],
            value="en" # Default to English
        )
        self.lore_field = ft.TextField(label="World Lore", multiline=True, min_lines=3)

        self.content = ft.Column(
            [self.name_field, self.language_dropdown, self.lore_field],
            tight=True
        )

        self.actions = [
            ft.TextButton("Cancel", on_click=self.close_dialog),
            ft.FilledButton("Create", on_click=self.create_world),
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    def create_world(self, e):
        """
        Validates input and inserts a new world record into the database.
        The lore is stored in a JSONB object with the language as the key.
        """
        if not self.name_field.value:
            self.name_field.error_text = "World name cannot be empty."
            self.name_field.update()
            return

        # The lore is structured as a JSON object, e.g., {"en": "This is the lore."}
        lore_data = {
            self.language_dropdown.value: self.lore_field.value
        }

        try:
            # According to the schema, 'lore' is a jsonb field.
            # 'description' is not in the new schema for the 'worlds' table.
            response = supabase.table('worlds').insert({
                'name': self.name_field.value,
                'lore': lore_data,
                'user_id': self.page.session.get("user_id") # Assuming user_id is stored in session
            }).execute()
            print("World creation response:", response)

            if self.on_create_callback:
                self.on_create_callback()

            self.close_dialog(e)

        except Exception as ex:
            print(f"Error creating world: {ex}")
            # Display a snackbar for better user feedback
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error creating world: {ex}"),
                bgcolor=ft.colors.RED_700
            )
            self.page.snack_bar.open = True
            self.page.update()


    def close_dialog(self, e):
        """
        Closes the dialog and clears the input fields.
        """
        self.open = False
        # Clear fields for the next time it's opened
        self.name_field.value = ""
        self.name_field.error_text = ""
        self.lore_field.value = ""
        self.language_dropdown.value = "en"
        self.page.update()