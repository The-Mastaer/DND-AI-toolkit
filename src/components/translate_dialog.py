import flet as ft
from src.services.gemini_service import GeminiService


class TranslateDialog(ft.AlertDialog):
    """
    A dialog for translating world lore to a new language.
    """

    def __init__(self, gemini_service: GeminiService, on_translate, current_languages):
        super().__init__()
        self.gemini_service = gemini_service
        self.on_translate = on_translate
        self.modal = True
        self.title = ft.Text("Translate World Lore")

        # Supported languages (can be expanded)
        all_languages = {"en": "English", "de": "German", "es": "Spanish", "fr": "French", "ja": "Japanese"}

        # Filter out languages that already exist for this world
        available_options = [
            ft.dropdown.Option(code, name) for code, name in all_languages.items() if code not in current_languages
        ]

        self.language_dropdown = ft.Dropdown(
            label="Target Language",
            options=available_options,
            autofocus=True
        )

        self.progress_ring = ft.ProgressRing(visible=False)

        self.content = ft.Column([
            self.language_dropdown,
            self.progress_ring
        ])

        self.actions = [
            ft.TextButton("Cancel", on_click=self.close_dialog),
            ft.FilledButton("Translate", on_click=self.translate_clicked, disabled=not available_options),
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    def close_dialog(self, e):
        self.open = False
        self.page.update()

    async def translate_clicked(self, e):
        """Handles the translate button click event."""
        target_lang_code = self.language_dropdown.value
        if not target_lang_code:
            self.language_dropdown.error_text = "Please select a language."
            self.page.update()
            return

        self.progress_ring.visible = True
        self.page.update()

        # The on_translate callback is an async function passed from the view
        await self.on_translate(target_lang_code)

        self.progress_ring.visible = False
        self.close_dialog(e)