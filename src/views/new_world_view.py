import flet as ft
# Restoring the Supabase import
from ..services.supabase_service import supabase
from ..config import SUPPORTED_LANGUAGES


class NewWorldView(ft.View):
    """
    A dedicated view for creating a new world. It now saves the data
    to Supabase without requiring a user ID.
    """

    def __init__(self, page: ft.Page):
        """
        Initializes the NewWorldView.
        """
        super().__init__()
        self.page = page
        self.route = "/new-world"

        # --- UI Controls ---
        self.name_field = ft.TextField(label="World Name", autofocus=True)

        self.language_dropdown = ft.Dropdown(
            label="Language",
            options=[
                ft.dropdown.Option(code, name) for code, name in SUPPORTED_LANGUAGES.items()
            ],
            value="en"
        )

        self.lore_field = ft.TextField(
            label="World Lore",
            multiline=True,
            min_lines=5,
            max_lines=10,
        )

        # The button now calls the real create_world method
        self.save_button = ft.FilledButton(
            "Save World",
            icon=ft.Icons.SAVE,
            on_click=self.create_world
        )

        # --- Assembling the View ---
        self.appbar = ft.AppBar(
            title=ft.Text("Create New World"),
            leading=ft.IconButton(
                icon=ft.Icons.ARROW_BACK,
                on_click=self.go_back,
                tooltip="Back to Worlds"
            ),
            bgcolor="surfaceVariant"
        )

        self.controls = [
            ft.Container(
                content=ft.Column(
                    [
                        self.name_field,
                        self.language_dropdown,
                        self.lore_field,
                        ft.Row(
                            controls=[self.save_button],
                            alignment=ft.MainAxisAlignment.END,
                        ),
                    ],
                    spacing=10
                ),
                padding=20,
            )
        ]

    def go_back(self, e):
        """Navigates back to the worlds view using Flet's routing."""
        self.page.go("/worlds")

    def create_world(self, e):
        """
        Validates input and inserts a new world record into the database.
        The user_id is omitted, as the column is now nullable.
        """
        if not self.name_field.value:
            self.name_field.error_text = "World name cannot be empty."
            self.update()
            return
        else:
            self.name_field.error_text = ""
            self.update()

        lore_data = {self.language_dropdown.value: self.lore_field.value or ""}

        try:
            # The user_id is no longer included in the insert dictionary.
            response = supabase.table('worlds').insert({
                'name': self.name_field.value,
                'lore': lore_data
            }).execute()

            if response.data:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"World '{self.name_field.value}' created!"),
                    bgcolor=ft.Colors.GREEN_700
                )
                self.page.snack_bar.open = True
                self.page.go("/worlds")
            else:
                self.show_error_snackbar("Creation failed. Check database logs.")

        except Exception as ex:
            print(f"Error creating world (Exception): {ex}")
            self.show_error_snackbar(str(ex))

    def show_error_snackbar(self, message):
        """
        Displays a standardized error message in a SnackBar for user feedback.
        """
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(f"Error: {message}"),
            bgcolor=ft.Colors.RED_700
        )
        self.page.snack_bar.open = True
        self.page.update()