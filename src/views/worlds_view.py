import flet as ft
from ..services.supabase_service import supabase
from ..config import SUPPORTED_LANGUAGES
from ..components.translate_dialog import TranslateDialog


class WorldsView(ft.View):
    """
    The main view for managing worlds. It displays a list of existing worlds
    and provides controls to create, edit, or delete them.
    """

    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.route = "/worlds"
        self.selected_world = None

        # --- UI Controls ---
        self.new_world_button = ft.IconButton(icon=ft.Icons.ADD_CIRCLE_OUTLINE, tooltip="Create New World",
                                              on_click=lambda _: self.page.go("/new-world"))
        self.language_dropdown = ft.Dropdown(label="Lore Language",
                                             options=[ft.dropdown.Option(code, name) for code, name in
                                                      SUPPORTED_LANGUAGES.items()], value="en",
                                             on_change=self.language_changed)
        self.worlds_list = ft.ListView(expand=True, spacing=10)
        self.world_details = ft.Container(content=ft.Text("Select a world to see details or create a new one."),
                                          alignment=ft.alignment.center, expand=True, padding=20)
        self.translate_dialog = TranslateDialog(on_save_callback=self.load_worlds)

        # --- Assembling the View ---
        self.appbar = ft.AppBar(title=ft.Text("World Manager"), bgcolor="surfaceVariant")
        self.controls = [
            ft.Row(
                [
                    ft.Container(
                        content=ft.Column(
                            [ft.Text("Your Worlds", style=ft.TextThemeStyle.HEADLINE_SMALL), self.language_dropdown,
                             self.worlds_list, ft.Row([self.new_world_button])]),
                        width=250, padding=10, border=ft.border.only(right=ft.BorderSide(1, "outline"))
                    ),
                    self.world_details
                ],
                expand=True,
            )
        ]

    def did_mount(self):
        self.page.overlay.append(self.translate_dialog)
        self.page.update()
        self.load_worlds()

    def load_worlds(self):
        current_selection_id = self.selected_world['id'] if self.selected_world else None
        self.worlds_list.controls.clear()
        try:
            response = supabase.table('worlds').select('*').is_('user_id', 'NULL').execute()
            if response.data:
                for world in response.data:
                    self.worlds_list.controls.append(
                        ft.ListTile(title=ft.Text(world['name']), data=world, on_click=self.select_world))
                    if world['id'] == current_selection_id:
                        self.selected_world = world
            else:
                self.worlds_list.controls.append(ft.Text("No worlds found. Create one!"))
        except Exception as e:
            print(f"Error loading worlds: {e}")
            self.worlds_list.controls.append(ft.Text(f"Error: {e}"))
        self.update()
        if self.selected_world:
            self.update_details_view()

    def select_world(self, e):
        self.selected_world = e.control.data
        self.update_details_view()

    def language_changed(self, e):
        if self.selected_world:
            self.update_details_view()

    def open_translate_dialog(self, e):
        if self.selected_world:
            self.translate_dialog.open_dialog(self.selected_world, self.language_dropdown.value)

    def open_edit_view(self, e):
        if self.selected_world:
            self.page.go(f"/edit-world/{self.selected_world['id']}/{self.language_dropdown.value}")

    def open_campaigns_view(self, e):
        """Navigates to the campaigns view for the current world."""
        if self.selected_world:
            self.page.go(f"/campaigns/{self.selected_world['id']}/{self.language_dropdown.value}")

    def update_details_view(self):
        if not self.selected_world:
            self.world_details.content = ft.Text("Select a world.")
            self.update()
            return

        world_data = self.selected_world
        selected_lang_code = self.language_dropdown.value

        # The "Manage Campaigns" button is now part of the header row
        header = ft.Row(
            [
                ft.Text(f"Details for {world_data['name']}", style=ft.TextThemeStyle.HEADLINE_MEDIUM, expand=True),
                ft.FilledButton("Manage Campaigns", icon=ft.Icons.LIBRARY_BOOKS, on_click=self.open_campaigns_view),
                ft.IconButton(ft.Icons.EDIT, tooltip="Edit World", on_click=self.open_edit_view),
                ft.IconButton(ft.Icons.TRANSLATE, tooltip="Translate Lore", on_click=self.open_translate_dialog),
            ],
            alignment=ft.MainAxisAlignment.START,  # Changed to START to group buttons
            spacing=10
        )
        lore_text = world_data.get('lore', {}).get(selected_lang_code)
        lore_content = ft.Text(lore_text, selectable=True) if lore_text else ft.Text(
            f"No lore available in {SUPPORTED_LANGUAGES.get(selected_lang_code, 'the selected language')}.",
            italic=True)

        # The button is no longer at the bottom of the column
        self.world_details.content = ft.Column(
            [header, ft.Divider(), lore_content],
            spacing=10,
            scroll=ft.ScrollMode.AUTO
        )
        self.update()
