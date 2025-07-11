# src/views/campaigns_view.py

import flet as ft
from ..services.supabase_service import supabase
from ..config import SUPPORTED_LANGUAGES


class CampaignsView(ft.View):
    """
    View for managing campaigns within a specific world.
    """

    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page
        self.route = "/campaigns"
        self.world_id = None
        self.campaigns_data = []
        self.selected_campaign = None

        # --- UI CONTROLS ---
        self.appbar = ft.AppBar(title=ft.Text("Campaign Manager"), bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST)
        self.campaigns_list = ft.ListView(expand=True, spacing=10)
        self.campaign_name_field = ft.TextField(label="Campaign Name", read_only=True)
        self.party_info_field = ft.TextField(label="Party Info", multiline=True, min_lines=5, read_only=True)
        self.session_history_field = ft.TextField(label="Session History", multiline=True, min_lines=5, read_only=True)

        self.details_tabs = ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(text="Party Info", content=self.party_info_field),
                ft.Tab(text="Session History", content=self.session_history_field),
            ],
            expand=True,
        )

        self.new_campaign_button = ft.IconButton(icon=ft.Icons.ADD, on_click=self.new_campaign_click)
        self.delete_campaign_button = ft.IconButton(icon=ft.Icons.DELETE, on_click=self.delete_campaign_click,
                                                    disabled=True)
        self.save_campaign_button = ft.ElevatedButton("Save Campaign", on_click=self.save_campaign_click,
                                                      visible=False)
        self.error_text = ft.Text("", color=ft.Colors.RED)

        # --- LAYOUT ---
        self.controls = [
            ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text("Campaigns", style=ft.TextThemeStyle.HEADLINE_SMALL),
                            self.campaigns_list,
                            self.error_text,
                            ft.Row([self.new_campaign_button, self.delete_campaign_button]),
                        ],
                        width=300,
                        spacing=10,
                    ),
                    ft.VerticalDivider(width=1),
                    ft.Column(
                        [
                            self.campaign_name_field,
                            self.details_tabs,
                            ft.Row([self.save_campaign_button], alignment=ft.MainAxisAlignment.END),
                        ],
                        expand=True,
                        spacing=10,
                    ),
                ],
                expand=True,
            )
        ]

    def did_mount(self):
        """Called when the view is mounted to parse the world ID and load campaigns."""
        self.parse_world_id()
        if self.world_id:
            self.page.run_task(self.load_campaigns)

    def parse_world_id(self):
        """Extracts the world ID from the page route."""
        try:
            parts = self.page.route.split('/')
            if len(parts) >= 3 and parts[1] == 'worlds':
                self.world_id = int(parts[2])
                print(f"--- CampaignsView loaded for World ID: {self.world_id} ---")
        except (ValueError, IndexError) as e:
            self.error_text.value = f"Error: Could not determine World ID from route '{self.page.route}'."
            print(f"Error parsing world ID: {e}")
            self.update()

    async def load_campaigns(self):
        """Fetches campaigns for the current world from the database."""
        self.campaigns_list.controls.clear()
        self.campaigns_list.controls.append(ft.ProgressRing())
        self.update()

        try:
            response = await supabase.get_campaigns_for_world(self.world_id)
            self.campaigns_data = response.data if response else []
            self.campaigns_list.controls.clear()

            if self.campaigns_data:
                for campaign in self.campaigns_data:
                    campaign_name = campaign.get('name', {}).get('en', f"Campaign {campaign['id']}")
                    self.campaigns_list.controls.append(
                        ft.ListTile(title=ft.Text(campaign_name), on_click=self.select_campaign, data=campaign)
                    )
            else:
                self.campaigns_list.controls.append(ft.Text("No campaigns found."))

        except Exception as e:
            self.error_text.value = f"Error loading campaigns: {e}"
            self.campaigns_list.controls.clear()
        self.update()

    def select_campaign(self, e):
        """Handles selecting a campaign from the list."""
        self.selected_campaign = e.control.data
        lang_code = "en"  # Assuming English for now, can be made dynamic later
        self.campaign_name_field.value = self.selected_campaign.get('name', {}).get(lang_code, "")
        self.party_info_field.value = self.selected_campaign.get('party_info', {}).get(lang_code, "")
        self.session_history_field.value = self.selected_campaign.get('session_history', {}).get(lang_code, "")

        self.campaign_name_field.read_only = False
        self.party_info_field.read_only = False
        self.session_history_field.read_only = False
        self.delete_campaign_button.disabled = False
        self.save_campaign_button.visible = True
        self.update()

    def new_campaign_click(self, e):
        """Clears the form to create a new campaign."""
        self.selected_campaign = None
        self.campaign_name_field.value = ""
        self.party_info_field.value = ""
        self.session_history_field.value = ""
        self.campaign_name_field.read_only = False
        self.party_info_field.read_only = False
        self.session_history_field.read_only = False
        self.save_campaign_button.visible = True
        self.delete_campaign_button.disabled = True
        self.update()

    async def save_campaign_click(self, e):
        """Saves a new or existing campaign."""
        lang_code = "en"
        campaign_name = self.campaign_name_field.value
        if not campaign_name:
            self.error_text.value = "Campaign name cannot be empty."
            self.update()
            return

        campaign_data = {
            "name": {lang_code: campaign_name},
            "party_info": {lang_code: self.party_info_field.value},
            "session_history": {lang_code: self.session_history_field.value},
            "world_id": self.world_id
        }

        if self.selected_campaign:
            await supabase.update_campaign(self.selected_campaign['id'], campaign_data)
        else:
            await supabase.create_campaign(campaign_data)

        await self.load_campaigns()
        self.reset_details_view()

    async def delete_campaign_click(self, e):
        """Deletes the selected campaign."""
        if self.selected_campaign:
            await supabase.delete_campaign(self.selected_campaign['id'])
            await self.load_campaigns()
            self.reset_details_view()

    def reset_details_view(self):
        """Resets the campaign details view to a read-only state."""
        self.selected_campaign = None
        self.campaign_name_field.value = ""
        self.party_info_field.value = ""
        self.session_history_field.value = ""
        self.campaign_name_field.read_only = True
        self.party_info_field.read_only = True
        self.session_history_field.read_only = True
        self.save_campaign_button.visible = False
        self.delete_campaign_button.disabled = True
        self.update()
