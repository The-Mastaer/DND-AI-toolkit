# src/views/worlds_view.py

import flet as ft
from ..services.supabase_service import supabase
from ..config import SUPPORTED_LANGUAGES
from ..components.translate_dialog import TranslateDialog


class WorldsView(ft.View):
    """
    View for managing D&D worlds. It allows users to view, create, edit,
    and delete their worlds.
    """

    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.route = "/worlds"
        self.worlds_data = []
        self.selected_world = None

        # --- UI CONTROLS ---
        self.appbar = ft.AppBar(title=ft.Text("World Manager"), bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST)

        self.worlds_list = ft.ListView(expand=1, spacing=10)
        self.language_dropdown = ft.Dropdown(
            label="Lore Language",
            options=[ft.dropdown.Option(code, name) for code, name in SUPPORTED_LANGUAGES.items()],
            value="en",
            on_change=self.on_language_change,
        )
        self.world_name_field = ft.TextField(label="World Name", read_only=True)
        self.world_lore_field = ft.TextField(
            label="World Lore",
            multiline=True,
            read_only=True,
            expand=True
        )
        self.error_text = ft.Text("", color=ft.Colors.RED)

        # --- BUTTONS ---
        self.new_world_button = ft.IconButton(icon=ft.Icons.ADD, on_click=self.new_world_click)
        self.delete_world_button = ft.IconButton(icon=ft.Icons.DELETE, on_click=self.delete_world_click, disabled=True)
        self.manage_campaigns_button = ft.ElevatedButton("Manage Campaigns", on_click=self.manage_campaigns_click,
                                                         disabled=True)
        self.translate_button = ft.ElevatedButton("Translate", on_click=self.translate_click, disabled=True)
        self.save_world_button = ft.ElevatedButton("Save World", on_click=self.save_world_click, visible=False)

        # --- LAYOUT ---
        self.controls = [
            ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text("Your Worlds", style=ft.TextThemeStyle.HEADLINE_SMALL),
                            self.language_dropdown,
                            self.worlds_list,
                            self.error_text,
                            ft.Row([self.new_world_button, self.delete_world_button]),
                        ],
                        width=300,
                        spacing=10,
                    ),
                    ft.VerticalDivider(width=1),
                    ft.Column(
                        [
                            self.world_name_field,
                            self.world_lore_field,
                            ft.Row(
                                [
                                    self.manage_campaigns_button,
                                    self.translate_button,
                                    self.save_world_button,
                                ],
                                alignment=ft.MainAxisAlignment.END,
                            ),
                        ],
                        expand=True,
                        spacing=10,
                    ),
                ],
                expand=True,
            )
        ]

    def did_mount(self):
        """Called when the view is mounted."""
        self.page.run_task(self.load_worlds)

    async def load_worlds(self):
        """
        Fetches worlds from the Supabase database and populates the list view.
        """
        self.worlds_list.controls.clear()
        self.worlds_list.controls.append(ft.ProgressRing())
        self.update()

        try:
            user = await supabase.get_user()
            if not user:
                self.error_text.value = "User not authenticated. Should not happen."
                self.worlds_list.controls.clear()
                self.update()
                return

            worlds_response = await supabase.get_worlds(user.user.id)
            # Correctly access the .data attribute from the response
            self.worlds_data = worlds_response.data if worlds_response else []

            self.worlds_list.controls.clear()
            if self.worlds_data:
                for world in self.worlds_data:
                    self.worlds_list.controls.append(
                        ft.ListTile(
                            title=ft.Text(world['name']),
                            on_click=self.select_world,
                            data=world,
                        )
                    )
            else:
                self.worlds_list.controls.append(ft.Text("No worlds found. Create one!"))

        except Exception as e:
            self.error_text.value = f"Error: {e}"
            self.worlds_list.controls.clear()

        self.update()

    def select_world(self, e):
        """Handles the selection of a world from the list."""
        self.selected_world = e.control.data
        lang_code = self.language_dropdown.value
        self.world_name_field.value = self.selected_world['name']
        self.world_lore_field.value = self.selected_world.get('lore', {}).get(lang_code, "")

        self.delete_world_button.disabled = False
        self.manage_campaigns_button.disabled = False
        self.translate_button.disabled = False
        self.world_name_field.read_only = False
        self.world_lore_field.read_only = False
        self.save_world_button.visible = True
        self.update()

    def on_language_change(self, e):
        """Updates the lore text when the language is changed."""
        if self.selected_world:
            lang_code = self.language_dropdown.value
            self.world_lore_field.value = self.selected_world.get('lore', {}).get(lang_code, "")
            self.update()

    def new_world_click(self, e):
        """Clears the form to create a new world."""
        self.selected_world = None
        self.world_name_field.value = ""
        self.world_lore_field.value = ""
        self.world_name_field.read_only = False
        self.world_lore_field.read_only = False
        self.save_world_button.visible = True
        self.delete_world_button.disabled = True
        self.manage_campaigns_button.disabled = True
        self.translate_button.disabled = True
        self.update()

    async def save_world_click(self, e):
        """Saves a new or existing world to the database."""
        user = await supabase.get_user()
        if not user:
            self.error_text.value = "Authentication error."
            self.update()
            return

        lang_code = self.language_dropdown.value
        world_name = self.world_name_field.value
        world_lore_text = self.world_lore_field.value

        if not world_name:
            self.error_text.value = "World name cannot be empty."
            self.update()
            return

        if self.selected_world:
            lore_data = self.selected_world.get('lore', {})
            lore_data[lang_code] = world_lore_text
            world_record = {
                'name': world_name,
                'lore': lore_data,
            }
            await supabase.update_world(self.selected_world['id'], world_record)
        else:
            world_record = {
                'name': world_name,
                'lore': {lang_code: world_lore_text},
                'user_id': user.user.id,
            }
            await supabase.create_world(world_record)

        await self.load_worlds()

    async def delete_world_click(self, e):
        """Deletes the selected world."""
        if self.selected_world:
            await supabase.delete_world(self.selected_world['id'])
            self.selected_world = None
            self.world_name_field.value = ""
            self.world_lore_field.value = ""
            self.world_name_field.read_only = True
            self.world_lore_field.read_only = True
            self.save_world_button.visible = False
            self.delete_world_button.disabled = True
            self.manage_campaigns_button.disabled = True
            self.translate_button.disabled = True
            await self.load_worlds()

    def manage_campaigns_click(self, e):
        """Navigates to the campaign management view for the selected world."""
        if self.selected_world:
            self.page.go(f"/worlds/{self.selected_world['id']}/campaigns")

    def translate_click(self, e):
        """Opens the translation dialog."""
        print("translate_click: Method called.")
        if self.selected_world:
            print(f"translate_click: selected_world is present: {self.selected_world['name']}")
            translate_dialog = TranslateDialog(page=self.page, on_save_callback=self.on_translation_saved)
            print("translate_click: TranslateDialog instantiated.")

            # 1. Prepare the dialog's content and internal state
            translate_dialog.open_dialog(self.selected_world, self.language_dropdown.value)
            print("translate_click: open_dialog method called on TranslateDialog (dialog prepared).")

            # 2. Explicitly set the dialog's 'open' property to True
            translate_dialog.open = True
            print("translate_click: translate_dialog.open set to True.")

            # 3. Open the dialog on the page's overlay
            self.page.open(translate_dialog)
            print("translate_click: page.open(translate_dialog) called.")
        else:
            print("translate_click: No world selected. Button disabled or selection issue.")

    def on_translation_saved(self):
        """Callback function after a translation is saved."""
        self.page.run_task(self.load_worlds)