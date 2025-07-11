# src/components/translate_dialog.py

import flet as ft
import traceback
from ..config import SUPPORTED_LANGUAGES
from ..services.gemini_service import GeminiService
from ..prompts import TRANSLATE_LORE_PROMPT
from ..services.supabase_service import supabase


class TranslateDialog(ft.AlertDialog):
    """
    A dialog for translating world lore from one language to another using the Gemini API.
    """

    def __init__(self, page: ft.Page, on_save_callback):
        super().__init__()
        self.page = page
        self.on_save_callback = on_save_callback
        self.modal = True
        self.title = ft.Text("Translate World Lore")
        self.world_data = None
        self.source_lang_code = None
        self.gemini_service = GeminiService()

        # --- UI Controls ---
        self.source_language_text = ft.Text()
        self.target_language_dropdown = ft.Dropdown(label="Translate to")
        self.progress_ring = ft.ProgressRing(visible=False)
        self.translate_button = ft.FilledButton("Translate", on_click=self.generate_translation_click)
        self.translated_lore_field = ft.TextField(
            label="Translated Lore",
            multiline=True,
            min_lines=5,
            read_only=True
        )

        self.content = ft.Column(
            [
                self.source_language_text,
                self.target_language_dropdown,
                ft.Row([self.translate_button, self.progress_ring]),
                self.translated_lore_field,
            ],
            tight=True,
            spacing=15,
            width=400,
        )

        self.actions = [
            ft.TextButton("Cancel", on_click=self.close_dialog),
            ft.FilledButton("Save Translation", on_click=self.save_translation_click, disabled=True),
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    def open_dialog(self, world_data, source_lang_code):
        """
        Sets up the dialog with the specific world's data and prepares its content.
        Note: This method no longer sets self.open = True or calls page.update().
        The parent view (WorldsView) is now responsible for setting self.open = True
        and calling page.open(self).
        """
        print("TranslateDialog.open_dialog: Method called (preparing content).")
        self.world_data = world_data
        self.source_lang_code = source_lang_code
        self.actions[1].disabled = True
        self.translated_lore_field.value = ""
        self.translated_lore_field.read_only = True

        source_lang_name = SUPPORTED_LANGUAGES.get(source_lang_code, "Unknown")
        self.source_language_text.value = f"Translate from: {source_lang_name}"

        self.target_language_dropdown.options = [
            ft.dropdown.Option(code, name)
            for code, name in SUPPORTED_LANGUAGES.items()
            if code != source_lang_code
        ]
        if self.target_language_dropdown.options:
            self.target_language_dropdown.value = self.target_language_dropdown.options[0].key
        print("TranslateDialog.open_dialog: Dialog content prepared.")


    def generate_translation_click(self, e):
        """Wrapper to call the async generation method."""
        self.page.run_task(self.generate_translation)

    async def generate_translation(self):
        """
        Calls the Gemini API to generate the translation.
        """
        self.progress_ring.visible = True
        self.translate_button.disabled = True
        self.update()

        source_lore = self.world_data.get('lore', {}).get(self.source_lang_code, "")
        target_lang_name = SUPPORTED_LANGUAGES.get(self.target_language_dropdown.value)

        if not source_lore or not target_lang_name:
            self.show_error("Source lore or target language is missing.")
            self.progress_ring.visible = False
            self.translate_button.disabled = False
            self.update()
            return

        try:
            prompt = TRANSLATE_LORE_PROMPT.format(
                language=target_lang_name,
                text=source_lore
            )
            translated_text = await self.gemini_service.get_text_response(prompt)
            self.translated_lore_field.value = translated_text
            self.translated_lore_field.read_only = False
            self.actions[1].disabled = False

        except Exception as ex:
            print("--- Detailed Traceback in Translation Dialog ---")
            traceback.print_exc()
            self.show_error(f"Error: {type(ex).__name__}. See console for details.")

        finally:
            self.progress_ring.visible = False
            self.translate_button.disabled = False
            self.update()

    def save_translation_click(self, e):
        """Wrapper to call the async save method."""
        self.page.run_task(self.save_translation)

    async def save_translation(self):
        """
        Saves the new translation to the world's lore in the database.
        """
        target_lang_code = self.target_language_dropdown.value
        translated_text = self.translated_lore_field.value

        if not translated_text:
            self.show_error("Translated text is empty.")
            return

        updated_lore = self.world_data.get('lore', {})
        updated_lore[target_lang_code] = translated_text

        try:
            world_record = {'lore': updated_lore}
            await supabase.update_world(self.world_data['id'], world_record)

            self.page.snack_bar = ft.SnackBar(content=ft.Text("Translation saved!"), bgcolor=ft.Colors.GREEN_700)
            self.page.snack_bar.open = True

            if self.on_save_callback:
                self.on_save_callback()

            # Using page.close() to explicitly close the dialog
            self.page.close(self)

        except Exception as ex:
            self.show_error(f"Database Error: {ex}")

    def show_error(self, message):
        """Helper to display an error in the dialog's title."""
        self.title = ft.Text(message, color=ft.Colors.RED)
        self.update()

    def close_dialog(self, e):
        """Closes the dialog and resets its state."""
        # Using page.close() to explicitly close the dialog
        self.page.close(self)
        self.title = ft.Text("Translate World Lore")
        self.open = False # Reset open state for next time if it's reused without full re-instantiation.
        self.page.update() # Update the page to reflect the closed state (this might be redundant with page.close())