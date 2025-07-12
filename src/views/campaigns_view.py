# src/views/campaigns_view.py

import flet as ft
from ..services.supabase_service import supabase
from ..services.gemini_service import GeminiService
from ..config import SUPPORTED_LANGUAGES
import asyncio
import json


class CampaignsView(ft.View):
    """
    A view for managing campaigns within a selected world.
    """

    def __init__(self, page: ft.Page, gemini_service: GeminiService):
        """
        Initializes the CampaignsView.

        Args:
            page (ft.Page): The Flet page object.
            gemini_service (GeminiService): The singleton instance of the Gemini service.
        """
        super().__init__()
        self.page = page
        self.route = "/campaigns"
        # REFACTOR: Store the injected service instance for future use
        self.gemini_service = gemini_service

        # --- State Management ---
        self.campaigns_data = []
        self.selected_campaign_data = None
        self.active_world_id = None
        self.current_language_code = 'en'

        # --- UI Controls ---
        self.appbar = ft.AppBar(
            title=ft.Text("Campaign Manager"),
            leading=ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda _: self.page.go("/worlds")),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        )
        self.campaigns_list = ft.ListView(expand=True, spacing=5)
        self.campaign_name_field = ft.TextField(label="Campaign Name", disabled=True)
        self.party_info_field = ft.TextField(label="Party Info", multiline=True, min_lines=5, disabled=True)
        self.session_history_field = ft.TextField(label="Session History", multiline=True, min_lines=5, disabled=True)

        self.details_tabs = ft.Tabs(
            selected_index=0,
            tabs=[
                ft.Tab(text="Lore", content=self.party_info_field),
                ft.Tab(text="Session History", content=self.session_history_field),
            ],
            expand=True,
        )

        self.new_button = ft.ElevatedButton("New Campaign", icon=ft.Icons.ADD, on_click=self.new_campaign_click)
        self.delete_button = ft.ElevatedButton("Delete Campaign", icon=ft.Icons.DELETE_FOREVER, color=ft.Colors.WHITE,
                                               bgcolor=ft.Colors.RED_700, on_click=self.delete_campaign_click,
                                               disabled=True)
        self.save_button = ft.FilledButton("Save Campaign", icon=ft.Icons.SAVE, on_click=self.save_campaign_click,
                                           disabled=True)

        # --- Layout ---
        left_column = ft.Column(
            [
                ft.Text("Campaigns", style=ft.TextThemeStyle.HEADLINE_SMALL),
                ft.Container(self.campaigns_list, border=ft.border.all(1), border_radius=5, expand=True, padding=5),
                ft.Row([self.new_button, self.delete_button], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ],
            expand=1,
            spacing=10
        )

        right_column = ft.Column(
            [
                self.campaign_name_field,
                self.details_tabs,
                ft.Row([self.save_button], alignment=ft.MainAxisAlignment.END)
            ],
            expand=3,
            spacing=10
        )

        self.controls = [
            ft.Row(
                [left_column, ft.VerticalDivider(width=1), right_column],
                expand=True,
                spacing=20,
            ),
        ]

    def did_mount(self):
        """Load initial data when the view is displayed."""
        self.page.run_task(self.load_initial_data)

    async def load_initial_data(self):
        """Fetches active world/language and then the campaigns for that world."""
        self.active_world_id = await asyncio.to_thread(self.page.client_storage.get, "active_world_id")
        self.current_language_code = await asyncio.to_thread(self.page.client_storage.get,
                                                             "active_language_code") or 'en'

        if not self.active_world_id:
            # Handle case where no world is selected
            self.campaigns_list.controls.clear()
            self.campaigns_list.controls.append(ft.Text("No active world selected. Go back to Worlds and select one."))
            self.update()
            return

        await self.get_campaigns()

    async def get_campaigns(self):
        """Fetches campaigns for the active world and updates the UI."""
        self.campaigns_list.controls.clear()
        self.campaigns_list.controls.append(ft.ProgressIndicator())
        self.update()

        try:
            response = await supabase.get_campaigns_for_world(self.active_world_id)
            self.campaigns_data = response.data
            self.campaigns_list.controls.clear()
            if self.campaigns_data:
                for campaign in self.campaigns_data:
                    campaign_name = campaign.get('name', {}).get(self.current_language_code, "Unnamed Campaign")
                    self.campaigns_list.controls.append(
                        ft.ListTile(
                            title=ft.Text(campaign_name),
                            on_click=self.campaign_selected,
                            data=campaign,
                        )
                    )
                # Auto-select the first campaign
                if not self.selected_campaign_data and self.campaigns_data:
                    await self.select_campaign(self.campaigns_data[0])
            else:
                self.campaigns_list.controls.append(ft.Text("No campaigns found. Create one!"))
        except Exception as e:
            self.campaigns_list.controls.clear()
            self.campaigns_list.controls.append(ft.Text(f"Error loading campaigns: {e}", color=ft.Colors.RED))
        self.update()

    async def campaign_selected(self, e):
        """Handles selection of a campaign from the list."""
        await self.select_campaign(e.control.data)

    async def select_campaign(self, campaign_data):
        """Updates the UI with the data of the selected campaign."""
        self.selected_campaign_data = campaign_data
        self.campaign_name_field.value = self.selected_campaign_data.get('name', {}).get(self.current_language_code, "")
        self.party_info_field.value = self.selected_campaign_data.get('party_info', {}).get(self.current_language_code,
                                                                                            "")
        self.session_history_field.value = self.selected_campaign_data.get('session_history', {}).get(
            self.current_language_code, "")
        self.enable_fields()
        await asyncio.to_thread(self.page.client_storage.set, "active_campaign_id", self.selected_campaign_data['id'])
        self.update()

    def enable_fields(self, is_new=False):
        """Enables or disables form fields based on selection state."""
        is_selected = self.selected_campaign_data is not None or is_new
        self.campaign_name_field.disabled = not is_selected
        self.party_info_field.disabled = not is_selected
        self.session_history_field.disabled = not is_selected
        self.delete_button.disabled = not is_selected or is_new
        self.save_button.disabled = not is_selected

    def new_campaign_click(self, e):
        """Handles the 'New Campaign' button click."""
        self.selected_campaign_data = None
        self.campaign_name_field.value = ""
        self.party_info_field.value = ""
        self.session_history_field.value = ""
        self.enable_fields(is_new=True)
        self.campaign_name_field.focus()
        self.update()

    async def save_campaign_click(self, e):
        """Saves a new or existing campaign."""
        if not self.campaign_name_field.value:
            self.page.snack_bar = ft.SnackBar(ft.Text("Campaign Name is required.", color=ft.Colors.RED))
            self.page.snack_bar.open = True
            self.update()
            return

        try:
            if self.selected_campaign_data:  # Update
                name_json = self.selected_campaign_data.get('name', {})
                party_json = self.selected_campaign_data.get('party_info', {})
                history_json = self.selected_campaign_data.get('session_history', {})

                name_json[self.current_language_code] = self.campaign_name_field.value
                party_json[self.current_language_code] = self.party_info_field.value
                history_json[self.current_language_code] = self.session_history_field.value

                updates = {'name': name_json, 'party_info': party_json, 'session_history': history_json}
                await supabase.client.from_('campaigns').update(updates).eq('id',
                                                                            self.selected_campaign_data['id']).execute()
            else:  # Create
                new_campaign = {
                    'world_id': self.active_world_id,
                    'name': {self.current_language_code: self.campaign_name_field.value},
                    'party_info': {self.current_language_code: self.party_info_field.value},
                    'session_history': {self.current_language_code: self.session_history_field.value}
                }
                await supabase.client.from_('campaigns').insert(new_campaign).execute()

            self.page.snack_bar = ft.SnackBar(ft.Text("Campaign saved!"), bgcolor=ft.Colors.GREEN)
            await self.get_campaigns()
        except Exception as ex:
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error saving campaign: {ex}"), color=ft.Colors.RED)
        finally:
            self.page.snack_bar.open = True
            self.update()

    async def delete_campaign_click(self, e):
        """Handles deletion of the selected campaign."""
        if self.selected_campaign_data:
            try:
                await supabase.client.from_('campaigns').delete().eq('id', self.selected_campaign_data['id']).execute()
                self.selected_campaign_data = None
                self.campaign_name_field.value = ""
                self.party_info_field.value = ""
                self.session_history_field.value = ""
                self.enable_fields()
                await self.get_campaigns()
                self.page.snack_bar = ft.SnackBar(ft.Text("Campaign deleted."), bgcolor=ft.Colors.GREEN)
            except Exception as ex:
                self.page.snack_bar = ft.SnackBar(ft.Text(f"Error deleting campaign: {ex}"), color=ft.Colors.RED)
            finally:
                self.page.snack_bar.open = True
                self.update()
