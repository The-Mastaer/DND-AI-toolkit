import flet as ft
from services.supabase_service import supabase
from config import SUPPORTED_LANGUAGES

class NewCampaignView(ft.View):
    """
    A dedicated view for creating a new campaign within a world,
    including fields for party info and session history.
    """
    def __init__(self, page: ft.Page, world_id: int, lang_code: str):
        super().__init__()
        self.page = page
        self.world_id = world_id
        self.lang_code = lang_code
        self.route = f"/new-campaign/{self.world_id}/{self.lang_code}"

        # --- UI Controls ---
        lang_name = SUPPORTED_LANGUAGES.get(lang_code, lang_code)
        self.name_field = ft.TextField(label=f"Campaign Name ({lang_name})", autofocus=True)
        self.party_info_field = ft.TextField(label="Party Info", multiline=True, min_lines=3)
        self.session_history_field = ft.TextField(label="Session History", multiline=True, min_lines=5)
        self.save_button = ft.FilledButton("Save Campaign", icon=ft.Icons.SAVE, on_click=self.save_campaign)

        # --- Assembling the View ---
        self.appbar = ft.AppBar(
            title=ft.Text("Create New Campaign"),
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=self.go_back),
            bgcolor="surfaceVariant"
        )
        self.controls = [
            ft.Container(
                content=ft.Column(
                    [
                        self.name_field,
                        self.party_info_field,
                        self.session_history_field,
                        ft.Row([self.save_button], alignment=ft.MainAxisAlignment.END),
                    ],
                    spacing=10,
                    scroll=ft.ScrollMode.AUTO,
                ),
                padding=20,
                expand=True,
            )
        ]

    def save_campaign(self, e):
        """Saves the new campaign to the database."""
        if not self.name_field.value:
            self.name_field.error_text = "Campaign name cannot be empty."
            self.update()
            return

        # Create JSONB objects for all text fields, starting with the current language
        campaign_name_json = {self.lang_code: self.name_field.value}
        party_info_json = {self.lang_code: self.party_info_field.value}
        session_history_json = {self.lang_code: self.session_history_field.value}

        try:
            response = supabase.table('campaigns').insert({
                'world_id': self.world_id,
                'name': campaign_name_json,
                'party_info': party_info_json,
                'session_history': session_history_json,
            }).execute()

            if response.data:
                self.page.snack_bar = ft.SnackBar(content=ft.Text("Campaign created!"), bgcolor=ft.Colors.GREEN_700)
                self.page.snack_bar.open = True
                self.go_back(e)
            else:
                self.page.snack_bar = ft.SnackBar(content=ft.Text("Error creating campaign."), bgcolor=ft.Colors.RED_700)
                self.page.snack_bar.open = True
                self.update()
        except Exception as ex:
            print(f"Error saving campaign: {ex}")

    def go_back(self, e):
        """Navigates back to the campaigns view for the current world."""
        self.page.go(f"/campaigns/{self.world_id}/{self.lang_code}")