import flet as ft
from ..services.supabase_service import supabase
from ..config import SUPPORTED_LANGUAGES


class CampaignsView(ft.View):
    """
    A view to display and manage campaigns for a specific world.
    Features a two-panel layout for list and details.
    """

    def __init__(self, page: ft.Page, world_id: int, lang_code: str):
        super().__init__()
        self.page = page
        self.world_id = world_id
        self.lang_code = lang_code
        self.selected_campaign = None
        self.route = f"/campaigns/{self.world_id}/{self.lang_code}"

        # --- UI Controls ---
        self.world_name_text = ft.Text("Campaigns in...", style=ft.TextThemeStyle.HEADLINE_MEDIUM)
        self.campaigns_list = ft.ListView(expand=True, spacing=10)
        self.new_campaign_button = ft.IconButton(
            icon=ft.Icons.ADD_CIRCLE_OUTLINE, tooltip="New Campaign", on_click=self.go_to_new_campaign
        )
        self.details_view = ft.Container(
            content=ft.Text("Select a campaign to see details."),
            alignment=ft.alignment.center,
            expand=True,
            padding=20
        )

        # --- Assembling the View ---
        self.appbar = ft.AppBar(
            title=self.world_name_text,
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=self.go_back),
            bgcolor="surfaceVariant"
        )
        self.controls = [
            ft.Row(
                [
                    ft.Container(
                        content=ft.Column(
                            [ft.Row([ft.Text("Campaigns"), self.new_campaign_button]), self.campaigns_list]),
                        width=250, padding=10, border=ft.border.only(right=ft.BorderSide(1, "outline"))
                    ),
                    self.details_view
                ],
                expand=True
            )
        ]

    def did_mount(self):
        self.load_campaign_data()

    def load_campaign_data(self):
        try:
            world_response = supabase.table('worlds').select('name').eq('id', self.world_id).single().execute()
            if world_response.data:
                self.world_name_text.value = f"Campaigns in {world_response.data['name']}"

            campaign_response = supabase.table('campaigns').select('*').eq('world_id', self.world_id).execute()
            self.campaigns_list.controls.clear()
            if campaign_response.data:
                for campaign in campaign_response.data:
                    campaign_name = campaign.get('name', {}).get(self.lang_code, "Unnamed Campaign")
                    self.campaigns_list.controls.append(
                        ft.ListTile(title=ft.Text(campaign_name), data=campaign, on_click=self.select_campaign)
                    )
            else:
                self.campaigns_list.controls.append(ft.Text("No campaigns found."))
            self.update()
        except Exception as e:
            print(f"Error loading campaign data: {e}")

    def select_campaign(self, e):
        self.selected_campaign = e.control.data
        self.update_details_view()

    def update_details_view(self):
        if not self.selected_campaign:
            self.details_view.content = ft.Text("Select a campaign.")
            self.update()
            return

        campaign_data = self.selected_campaign
        campaign_name = campaign_data.get('name', {}).get(self.lang_code, "Unnamed Campaign")
        party_info = campaign_data.get('party_info', {}).get(self.lang_code, "No party info.")
        session_history = campaign_data.get('session_history', {}).get(self.lang_code, "No session history.")

        header = ft.Row([
            ft.Text(campaign_name, style=ft.TextThemeStyle.HEADLINE_SMALL, expand=True),
            ft.IconButton(ft.Icons.EDIT, on_click=self.go_to_edit_campaign, tooltip="Edit Campaign")
        ])

        self.details_view.content = ft.Column(
            [
                header,
                ft.Text("Party Info", style=ft.TextThemeStyle.TITLE_MEDIUM),
                ft.Text(party_info, selectable=True),
                ft.Divider(),
                ft.Text("Session History", style=ft.TextThemeStyle.TITLE_MEDIUM),
                ft.Text(session_history, selectable=True),
            ],
            scroll=ft.ScrollMode.AUTO, spacing=10
        )
        self.update()

    def go_to_new_campaign(self, e):
        self.page.go(f"/new-campaign/{self.world_id}/{self.lang_code}")

    def go_to_edit_campaign(self, e):
        if self.selected_campaign:
            self.page.go(f"/edit-campaign/{self.selected_campaign['id']}/{self.lang_code}")

    def go_back(self, e):
        self.page.go("/worlds")
