import flet as ft
from ..services.supabase_service import supabase
from ..components.new_campaign_dialog import NewCampaignDialog

class CampaignsView(ft.Column):
    """
    A view that displays a list of campaigns for a selected world.
    Inherits from ft.Column to structure its content vertically.
    """
    def __init__(self):
        super().__init__()
        self.expand = True
        self.spacing = 10

        self.campaigns_list = ft.ListView(expand=True, spacing=10)
        self.progress_ring = ft.ProgressRing(width=32, height=32, stroke_width=4)
        self.selected_world_id = None
        self.new_campaign_dialog = NewCampaignDialog(self.on_campaign_created)

        # Define the layout in the constructor
        self.controls = [
            ft.Row(
                controls=[
                    ft.Text("Campaigns", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                    ft.IconButton(
                        icon=ft.Icons.ADD,
                        tooltip="Create New Campaign",
                        on_click=self.open_new_campaign_dialog,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Divider(),
            self.campaigns_list,
        ]

    def did_mount(self):
        """
        Called when the control is added to the page.
        """
        self.page.dialog = self.new_campaign_dialog
        self.selected_world_id = self.page.session.get("selected_world_id")
        # Disable the add button if no world is selected
        self.controls[0].controls[1].disabled = self.selected_world_id is None
        self._get_campaigns()

    def _get_campaigns(self):
        """
        Fetches campaigns from Supabase based on the selected_world_id.
        """
        self.campaigns_list.controls.clear()

        if not self.selected_world_id:
            self.campaigns_list.controls.append(
                ft.Column([
                    ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, size=48),
                    ft.Text("No World Selected", style=ft.TextThemeStyle.HEADLINE_SMALL),
                    ft.Text(
                        "Please go back and select a world to see its campaigns.",
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.ElevatedButton("Go to Worlds", on_click=lambda _: self.page.go("/")),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                expand=True,
                alignment=ft.MainAxisAlignment.CENTER,
                )
            )
            self.update()
            return

        self.campaigns_list.controls.append(
            ft.Row(
                [self.progress_ring, ft.Text("Loading campaigns...")],
                alignment=ft.MainAxisAlignment.CENTER, spacing=10
            )
        )
        self.update()

        try:
            response = supabase.table('campaigns').select("*").eq('world_id', self.selected_world_id).execute()
            self.campaigns_list.controls.clear()
            if response.data:
                for campaign in response.data:
                    self.campaigns_list.controls.append(
                        ft.ListTile(
                            title=ft.Text(campaign['name']),
                            subtitle=ft.Text(campaign['description'], max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                            leading=ft.Icon(ft.Icons.BOOK_OUTLINED),
                            on_click=self.select_campaign,
                            data=campaign,
                        )
                    )
            else:
                self.campaigns_list.controls.append(ft.Text("No campaigns found. Create one!"))

        except Exception as e:
            print(f"Error fetching campaigns: {e}")
            self.campaigns_list.controls.clear()
            self.campaigns_list.controls.append(ft.Text(f"Error loading campaigns: {e}"))

        self.update()

    def select_campaign(self, e):
        """
        Handles the selection of a campaign.
        """
        campaign_id = e.control.data['id']
        self.page.session.set("selected_campaign_id", campaign_id)
        self.page.go("/characters")

    def open_new_campaign_dialog(self, e):
        """Opens the dialog to create a new campaign."""
        self.page.dialog.open = True
        self.page.update()

    def on_campaign_created(self):
        """Callback function to refresh the campaign list after creation."""
        self._get_campaigns()
