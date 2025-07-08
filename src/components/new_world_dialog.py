import flet as ft
from src.services.gemini_service import GeminiService


class NewWorldDialog(ft.AlertDialog):
    """
    A dialog component for creating a new world.

    This component encapsulates the UI and logic for the new world creation form,
    including text fields for name and description, and a button to generate
    a description using the Gemini AI service.
    """

    def __init__(self, gemini_service: GeminiService, on_create):
        super().__init__()
        self.gemini_service = gemini_service
        self.on_create = on_create  # Callback function to execute on creation
        self.modal = True
        self.title = ft.Text("Create a New World")

        self.world_name = ft.TextField(label="World Name", autofocus=True)
        self.world_description = ft.TextField(
            label="Description",
            multiline=True,
            min_lines=3,
            max_lines=5,
        )
        self.generate_button = ft.ElevatedButton(
            "Generate Description",
            icon=ft.Icons.AUTO_AWESOME,
            on_click=self.generate_description
        )
        self.progress_ring = ft.ProgressRing(visible=False)

        self.content = ft.Column([
            self.world_name,
            self.world_description,
            ft.Row([self.generate_button, self.progress_ring], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        ])

        self.actions = [
            ft.TextButton("Cancel", on_click=self.close_dialog),
            ft.FilledButton("Create", on_click=self.create_clicked),
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    def close_dialog(self, e):
        """Closes the dialog."""
        self.open = False
        self.page.update()

    def create_clicked(self, e):
        """Handles the create button click event."""
        if self.world_name.value:
            # Call the passed-in on_create callback with the new data
            self.on_create(self.world_name.value, self.world_description.value)
            self.close_dialog(e)
        else:
            self.world_name.error_text = "World name cannot be empty"
            self.page.update()

    def generate_description(self, e):
        """
        Generates a world description using the Gemini service.
        This runs in a separate thread to avoid blocking the UI.
        """
        if not self.world_name.value:
            self.world_name.error_text = "Enter a world name first"
            self.page.update()
            return

        self.world_description.value = ""
        self.progress_ring.visible = True
        self.generate_button.disabled = True
        self.page.update()

        prompt = f"Generate a brief, evocative description for a fantasy world named '{self.world_name.value}'. Focus on the key themes, conflicts, or unique features of this world."

        # Use run_in_executor to avoid blocking the event loop
        description = self.page.run_in_executor(
            self.gemini_service.generate_text, prompt
        )

        self.world_description.value = description
        self.progress_ring.visible = False
        self.generate_button.disabled = False
        self.page.update()