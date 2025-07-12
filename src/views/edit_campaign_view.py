import flet as ft
from services.supabase_service import supabase
from config import SUPPORTED_LANGUAGES


class EditCampaignView(ft.View):
    """
    A dedicated view for editing an existing campaign's details, including
    name, party info, and session history for a specific language.
    """

    def __init__(self, page: ft.Page, campaign_id: int, lang_code: str):
        super().__init__()
        self.page = page
        self.campaign_id = campaign_id
        self.lang_code = lang_code
        self.campaign_data = None  # To store the full campaign data

        self.route = f"/edit-campaign/{self.campaign_id}/{self.lang_code}"

        # --- UI Controls ---
        lang_name = SUPPORTED_LANGUAGES.get(lang_code, lang_code)
        self.name_field = ft.TextField(label=f"Campaign Name ({lang_name})", autofocus=True)
        self.party_info_field = ft.TextField(label="Party Info", multiline=True, min_lines=3)
        self.session_history_field = ft.TextField(label="Session History", multiline=True, min_lines=5)
        self.save_button = ft.FilledButton("Save Changes", icon=ft.Icons.SAVE, on_click=self.save_changes)

        # --- Assembling the View ---
        self.appbar = ft.AppBar(
            title=ft.Text("Edit Campaign"),
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

    def did_mount(self):
        """Fetch the campaign data when the view is mounted."""
        self.load_campaign_data()

    def load_campaign_data(self):
        """Fetches campaign data from Supabase and populates the fields."""
        try:
            response = supabase.table('campaigns').select('*').eq('id', self.campaign_id).single().execute()
            if response.data:
                self.campaign_data = response.data
                self.name_field.value = self.campaign_data.get('name', {}).get(self.lang_code, '')
                self.party_info_field.value = self.campaign_data.get('party_info', {}).get(self.lang_code, '')
                self.session_history_field.value = self.campaign_data.get('session_history', {}).get(self.lang_code, '')
                self.update()
            else:
                # Handle case where campaign is not found
                self.page.snack_bar = ft.SnackBar(content=ft.Text("Error: Campaign not found."), bgcolor=ft.Colors.RED)
                self.page.snack_bar.open = True
                self.update()
        except Exception as e:
            print(f"Error loading campaign data: {e}")

    def save_changes(self, e):
        """Saves the updated campaign data to the database."""
        if not self.campaign_data:
            return

        # Update the JSONB objects with the edited text for the current language
        updated_name = self.campaign_data.get('name', {})
        updated_name[self.lang_code] = self.name_field.value

        updated_party_info = self.campaign_data.get('party_info', {})
        updated_party_info[self.lang_code] = self.party_info_field.value

        updated_session_history = self.campaign_data.get('session_history', {})
        updated_session_history[self.lang_code] = self.session_history_field.value

        try:
            supabase.table('campaigns').update({
                'name': updated_name,
                'party_info': updated_party_info,
                'session_history': updated_session_history
            }).eq('id', self.campaign_id).execute()

            self.page.snack_bar = ft.SnackBar(content=ft.Text("Campaign updated!"), bgcolor=ft.Colors.GREEN_700)
            self.page.snack_bar.open = True
            self.go_back(e)
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(content=ft.Text(f"Error: {ex}"), bgcolor=ft.Colors.RED_700)
            self.page.snack_bar.open = True
            self.update()

    def go_back(self, e):
        """Navigates back to the campaigns view."""
        world_id = self.campaign_data.get('world_id')
        self.page.go(f"/campaigns/{world_id}/{self.lang_code}")