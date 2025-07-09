import flet as ft
from ..services.supabase_service import supabase
from ..components.new_world_dialog import NewWorldDialog

# The class now inherits from ft.Column, not the deprecated ft.UserControl.
class WorldsView(ft.Column):
    """
    A view that displays a list of worlds from the database.
    It inherits from ft.Column to structure its content vertically.
    """
    def __init__(self):
        super().__init__()
        # Configure the Column properties
        self.expand = True
        self.spacing = 10

        # --- UI Controls ---
        self.progress_ring = ft.ProgressRing(width=32, height=32, stroke_width=4)
        self.worlds_list = ft.ListView(expand=True, spacing=10)
        self.new_world_dialog = NewWorldDialog(self.on_world_created)

        # --- Build the initial layout in the constructor ---
        self.controls = [
            ft.Row(
                controls=[
                    ft.Text("Worlds", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                    ft.IconButton(
                        icon=ft.Icons.ADD,
                        tooltip="Create New World",
                        on_click=self.open_new_world_dialog,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Divider(),
            self.worlds_list, # Add the ListView to the Column
        ]

    def did_mount(self):
        """
        Called when the control is added to the page.
        This is the ideal place to perform initial data loading.
        """
        self.page.dialog = self.new_world_dialog
        self._get_worlds()

    def _get_worlds(self):
        """
        Fetches the list of worlds from the Supabase database.
        Updates the worlds_list control with the fetched data.
        """
        self.worlds_list.controls.clear()
        self.worlds_list.controls.append(
            ft.Row(
                controls=[self.progress_ring, ft.Text("Loading worlds...")],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10
            )
        )
        self.update()

        try:
            response = supabase.table('worlds').select("*").execute()
            print("Supabase response:", response)
            self.worlds_list.controls.clear() # Clear the loading indicator

            if response.data:
                for world in response.data:
                    self.worlds_list.controls.append(
                        ft.ListTile(
                            title=ft.Text(world['name']),
                            subtitle=ft.Text(world['description'], max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                            leading=ft.Icon(ft.Icons.PUBLIC),
                            on_click=self.select_world,
                            data=world,
                        )
                    )
            else:
                self.worlds_list.controls.append(ft.Text("No worlds found. Create one to get started!"))

        except Exception as e:
            print(f"Error fetching worlds: {e}")
            self.worlds_list.controls.clear()
            self.worlds_list.controls.append(ft.Text(f"Error loading worlds: {e}"))

        self.update()

    def select_world(self, e):
        """
        Handles the event when a user clicks on a world in the list.
        """
        world_id = e.control.data['id']
        self.page.session.set("selected_world_id", world_id)
        print(f"Selected World ID: {world_id} stored in session.")
        self.page.go("/campaigns")

    def open_new_world_dialog(self, e):
        """
        Opens the dialog to create a new world.
        """
        self.page.dialog.open = True
        self.page.update()

    def on_world_created(self):
        """
        Callback to refresh the list after a new world is created.
        """
        self._get_worlds()

    # The build() method is no longer needed when inheriting from a layout control.
    # The layout is defined in the __init__ method.