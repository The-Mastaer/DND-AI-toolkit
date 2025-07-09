import flet as ft
from src.services.gemini_service import GeminiService


class NewWorldDialog(ft.AlertDialog):
    """
    A dialog component for creating a new world.
    This now calls the dedicated lore generation method in the Gemini service.
    """

    def __init__(self, gemini_service: GeminiService, on_create):
        super().__init__()
        self.gemini_service = gemini_service
        self.on_create = on_create
        self.modal = True
        self.title = ft.Text("Create a New World")

        self.world_name = ft.TextField(label="World Name", autofocus=True)
        self.world_lore = ft.TextField(
            label="Initial Lore (English)",
            multiline=True,
            min_lines=3,
            max_lines=5,
        )
        self.generate_button = ft.ElevatedButton(
            "Generate Lore",
            icon=ft.Icons.AUTO_AWESOME,
            on_click=self.generate_lore
        )
        self.progress_ring = ft.ProgressRing(visible=False)

        self.content = ft.Column([
            self.world_name,
            self.world_lore,
            ft.Row([self.generate_button, self.progress_ring], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        ])

        self.actions = [
            ft.TextButton("Cancel", on_click=self.close_dialog),
            ft.FilledButton("Create", on_click=self.create_clicked),
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    def close_dialog(self, e):
        self.open = False
        self.page.update()

    def create_clicked(self, e):
        """Handles the create button click event."""
        if self.world_name.value:
            initial_lore = {"en": self.world_lore.value}
            self.page.run_task(self.on_create, self.world_name.value, initial_lore)
            self.close_dialog(e)
        else:
            self.world_name.error_text = "World name cannot be empty"
            self.page.update()

    async def generate_lore(self, e):
        """Asynchronously generates world lore using the Gemini service."""
        if not self.world_name.value:
            self.world_name.error_text = "Enter a world name first"
            self.page.update()
            return

        self.world_lore.value = ""
        self.progress_ring.visible = True
        self.generate_button.disabled = True
        self.page.update()

        # Call the dedicated service method instead of formatting the prompt here
        description = await self.page.loop.run_in_executor(
            None, self.gemini_service.generate_world_lore, self.world_name.value
        )

        self.world_lore.value = description
        self.progress_ring.visible = False
        self.generate_button.disabled = False
        self.page.update()
