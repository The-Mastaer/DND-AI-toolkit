import flet as ft
from ..services.supabase_service import supabase

class CharactersView(ft.Column):
    """
    A view that displays a list of characters for a selected campaign.
    Inherits from ft.Column to structure its content vertically.
    """
    def __init__(self):
        super().__init__()
        self.expand = True
        self.spacing = 10

        self.characters_list = ft.ListView(expand=True, spacing=10)
        self.progress_ring = ft.ProgressRing(width=32, height=32, stroke_width=4)
        self.selected_campaign_id = None

        # Define the layout in the constructor
        self.controls = [
            ft.Row(
                controls=[
                    ft.Text("Characters", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                    ft.IconButton(
                        icon=ft.Icons.ADD,
                        tooltip="Create New Character",
                        # on_click=self.open_new_character_dialog,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Divider(),
            self.characters_list,
        ]

    def did_mount(self):
        """
        Called when the control is added to the page.
        """
        self.selected_campaign_id = self.page.session.get("selected_campaign_id")
        self.controls[0].controls[1].disabled = self.selected_campaign_id is None
        self._get_characters()

    def _get_characters(self):
        """
        Fetches characters from Supabase based on the selected_campaign_id.
        """
        self.characters_list.controls.clear()

        if not self.selected_campaign_id:
            self.characters_list.controls.append(
                ft.Column([
                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, size=48),
                    ft.Text("No Campaign Selected", style=ft.TextThemeStyle.HEADLINE_SMALL),
                    ft.Text(
                        "Please go back and select a campaign to see its characters.",
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.ElevatedButton("Go to Campaigns", on_click=lambda _: self.page.go("/campaigns")),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                expand=True,
                alignment=ft.MainAxisAlignment.CENTER,
                )
            )
            self.update()
            return

        self.characters_list.controls.append(
            ft.Row(
                [self.progress_ring, ft.Text("Loading characters...")],
                alignment=ft.MainAxisAlignment.CENTER, spacing=10
            )
        )
        self.update()

        try:
            response = supabase.table('characters').select("*").eq('campaign_id', self.selected_campaign_id).execute()
            self.characters_list.controls.clear()
            if response.data:
                for character in response.data:
                    self.characters_list.controls.append(
                        ft.ListTile(
                            title=ft.Text(character['name']),
                            subtitle=ft.Text(f"Class: {character.get('class', 'N/A')} | Race: {character.get('race', 'N/A')}"),
                            leading=ft.Icon(ft.Icons.PERSON_OUTLINE),
                            on_click=self.select_character,
                            data=character,
                        )
                    )
            else:
                self.characters_list.controls.append(ft.Text("No characters found. Create one!"))

        except Exception as e:
            print(f"Error fetching characters: {e}")
            self.characters_list.controls.clear()
            self.characters_list.controls.append(ft.Text(f"Error loading characters: {e}"))

        self.update()

    def select_character(self, e):
        """
        Handles the selection of a character.
        """
        character_id = e.control.data['id']
        self.page.session.set("selected_character_id", character_id)
        print(f"Selected Character ID: {character_id} stored in session.")
