import flet as ft
from src.state import AppState
from typing import List, Dict, Any


class CampaignsView(ft.View):
    """
    A view to display and manage D&D campaigns.

    This class extends ft.View and manages its own state for the campaign list.
    It demonstrates how to fetch data from a service (SupabaseService) and
    dynamically build UI controls to display it.
    """

    def __init__(self, page: ft.Page, app_state: AppState):
        super().__init__(route="/campaigns")
        self.page = page
        self.app_state = app_state
        self.campaigns: List[Dict[str, Any]] = []

        # UI Controls
        self.loading_indicator = ft.ProgressRing(visible=True)
        self.campaign_list_view = ft.ListView(spacing=10, expand=True)
        self.error_text = ft.Text(visible=False, color=ft.colors.ERROR)

        self.controls = [
            ft.Column(
                [
                    ft.Text("Campaigns", size=32, weight=ft.FontWeight.BOLD),
                    self.loading_indicator,
                    self.error_text,
                    self.campaign_list_view,
                ],
                expand=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        ]

        # The on_view_load event is a custom event we'll call from the router
        # to trigger data loading when the view becomes visible.
        self.on_view_load = self.load_campaigns

    async def load_campaigns(self):
        """
        Asynchronously loads campaigns from the Supabase service and updates the UI.
        """
        print("CampaignsView: Loading campaigns...")
        self.loading_indicator.visible = True
        self.error_text.visible = False
        self.campaign_list_view.controls.clear()
        await self.page.update_async()

        if self.app_state.supabase_service:
            self.campaigns = await self.app_state.supabase_service.get_campaigns()

            if not self.campaigns:
                # Handle case where there's an error or no data
                if not self.app_state.supabase_service.client:
                    self.error_text.value = "Error: Supabase client not initialized."
                    self.error_text.visible = True
                else:
                    # No error, just no campaigns
                    self.campaign_list_view.controls.append(
                        ft.Text("No campaigns found. Create one to get started!")
                    )
            else:
                for campaign in self.campaigns:
                    self.campaign_list_view.controls.append(
                        ft.ListTile(
                            title=ft.Text(campaign.get("name", "Unnamed Campaign")),
                            subtitle=ft.Text(f"ID: {campaign.get('id')}"),
                            leading=ft.Icon(ft.icons.BOOK_ONLINE),
                            on_click=self.campaign_clicked
                        )
                    )
        else:
            self.error_text.value = "Error: Supabase service not available."
            self.error_text.visible = True

        self.loading_indicator.visible = False
        await self.page.update_async()
        print("CampaignsView: UI updated.")

    def campaign_clicked(self, e):
        """Handler for when a campaign list tile is clicked."""
        # In the future, this would navigate to a detailed view for the campaign.
        # For now, it just shows a snackbar.
        list_tile = e.control
        campaign_name = list_tile.title.value
        print(f"Clicked on campaign: {campaign_name}")
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(f"Navigating to '{campaign_name}'... (Not implemented)"),
            duration=2000
        )
        self.page.snack_bar.open = True
        self.page.update()