import flet as ft
from services.supabase_service import supabase
from config import SUPPORTED_LANGUAGES


class EditWorldView(ft.View):
    """
    A dedicated view for editing an existing world's name and lore
    for a specific language.
    """

    def __init__(self, page: ft.Page, world_id: int, lang_code: str):
        super().__init__()
        self.page = page
        self.world_id = world_id
        self.lang_code = lang_code
        self.world_data = None  # To store the full world data

        self.route = f"/edit-world/{self.world_id}/{self.lang_code}"

        # --- UI Controls ---
        self.name_field = ft.TextField(label="World Name", autofocus=True)
        self.language_text = ft.Text(f"Editing Lore for: {SUPPORTED_LANGUAGES.get(lang_code, lang_code)}")
        self.lore_field = ft.TextField(
            label="World Lore",
            multiline=True,
            min_lines=5,
            max_lines=10,
        )
        self.save_button = ft.FilledButton("Save Changes", icon=ft.Icons.SAVE, on_click=self.save_changes)

        # --- Assembling the View ---
        self.appbar = ft.AppBar(
            title=ft.Text("Edit World"),
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=self.go_back),
            bgcolor="surfaceVariant"
        )
        self.controls = [
            ft.Container(
                content=ft.Column(
                    [
                        self.name_field,
                        self.language_text,
                        self.lore_field,
                        ft.Row([self.save_button], alignment=ft.MainAxisAlignment.END),
                    ],
                    spacing=10
                ),
                padding=20
            )
        ]

    def did_mount(self):
        """Fetch the world data when the view is mounted."""
        self.load_world_data()

    def load_world_data(self):
        """Fetches world data from Supabase and populates the fields."""
        try:
            response = supabase.table('worlds').select('*').eq('id', self.world_id).single().execute()
            if response.data:
                self.world_data = response.data
                self.name_field.value = self.world_data.get('name', '')

                # Get the specific lore for the language we're editing
                lore_text = self.world_data.get('lore', {}).get(self.lang_code, '')
                self.lore_field.value = lore_text
                self.update()
            else:
                self.name_field.value = "Error: World not found."
                self.lore_field.disabled = True
                self.save_button.disabled = True
                self.update()
        except Exception as e:
            print(f"Error loading world data: {e}")

    def save_changes(self, e):
        """Saves the updated world data to the database."""
        if not self.world_data:
            return  # Should not happen if data loaded correctly

        # Update the lore JSONB object with the edited text
        updated_lore = self.world_data.get('lore', {})
        updated_lore[self.lang_code] = self.lore_field.value

        try:
            supabase.table('worlds').update({
                'name': self.name_field.value,
                'lore': updated_lore
            }).eq('id', self.world_id).execute()

            self.page.snack_bar = ft.SnackBar(content=ft.Text("World updated successfully!"),
                                              bgcolor=ft.Colors.GREEN_700)
            self.page.snack_bar.open = True
            self.go_back(e)  # Navigate back after saving
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(content=ft.Text(f"Error: {ex}"), bgcolor=ft.Colors.RED_700)
            self.page.snack_bar.open = True
            self.update()

    def go_back(self, e):
        """Navigates back to the main worlds view."""
        self.page.go("/worlds")