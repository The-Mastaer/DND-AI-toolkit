import flet as ft
from flet import AlertDialog, Text, TextField, Column, TextButton, FilledButton
from ..services.supabase_service import supabase

class NewCampaignDialog(AlertDialog):
    """
    A dialog window for creating a new campaign.
    It includes fields for the campaign's name and description
    and handles the database insertion.
    """
    def __init__(self, on_create_callback):
        super().__init__()
        self.on_create_callback = on_create_callback
        self.modal = True
        self.title = Text("Create a New Campaign")
        self.name_field = TextField(label="Campaign Name", autofocus=True)
        self.description_field = TextField(label="Description", multiline=True, min_lines=3)
        self.content = Column([self.name_field, self.description_field], tight=True)
        self.actions = [
            TextButton("Cancel", on_click=self.close_dialog),
            FilledButton("Create", on_click=self.create_campaign),
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    def create_campaign(self, e):
        """
        Validates input and inserts a new campaign record into the database.
        It reads the selected_world_id from the page session.
        """
        if not self.name_field.value:
            self.name_field.error_text = "Campaign name cannot be empty."
            self.name_field.update()
            return

        selected_world_id = self.page.session.get("selected_world_id")
        if not selected_world_id:
            # This is a safeguard, the UI should prevent this case.
            print("Error: No world selected to create a campaign in.")
            return

        try:
            response = supabase.table('campaigns').insert({
                'name': self.name_field.value,
                'description': self.description_field.value,
                'world_id': selected_world_id
            }).execute()
            print("Campaign creation response:", response)

            if self.on_create_callback:
                self.on_create_callback()

            self.close_dialog(e)

        except Exception as ex:
            print(f"Error creating campaign: {ex}")
            # Optionally, show an error to the user in the dialog
            self.title = Text("Error")
            self.content = Text(f"An error occurred: {ex}")
            self.actions = [TextButton("Close", on_click=self.close_dialog)]
            self.update()


    def close_dialog(self, e):
        """
        Closes the dialog and clears the input fields.
        """
        self.open = False
        self.name_field.value = ""
        self.name_field.error_text = ""
        self.description_field.value = ""
        self.page.update()
