# src/views/campaigns_view.py

import flet as ft
from typing import TYPE_CHECKING
from ..components.app_bar import AppBar

if TYPE_CHECKING:
    from ..state import AppState


class CampaignsView(ft.View):
    """
    The view for managing D&D campaigns within a selected world.
    """

    def __init__(self, page: ft.Page, state: 'AppState'):
        super().__init__(route="/campaigns")
        self.page = page
        self.state = state

        self.app_bar = AppBar(
            title="Campaigns",  # Title will be updated on mount
            page=self.page,
            state=self.state,
            show_back_button=True
        )

        self.controls = [
            self.app_bar,
            ft.Container(
                content=ft.Text("Select a world to see its campaigns."),
                padding=20,
            )
        ]

        # Update content when the view is mounted
        self.on_mount = self.on_view_mount

    def on_view_mount(self, e):
        """
        Called when the view is shown. Updates the content based on the
        currently selected world in the application state.
        """
        selected_world = self.state.get_selected_world()
        if selected_world:
            self.app_bar.title = ft.Text(f"Campaigns in {selected_world['name']}")
            # Placeholder for actual campaign list
            self.controls[1].content = ft.Text(f"Campaign management for '{selected_world['name']}' will be here.")
        else:
            self.app_bar.title = ft.Text("No World Selected")
            self.controls[1].content = ft.Text("Go back to the Worlds view and select a world first.")

        self.update()