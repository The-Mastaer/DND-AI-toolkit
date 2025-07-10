import flet as ft
import traceback  # Import the traceback module for detailed error logging
from ..config import SUPPORTED_LANGUAGES
from ..services.gemini_service import GeminiService
from ..prompts import TRANSLATE_LORE_PROMPT
from ..services.supabase_service import supabase


class TranslateDialog(ft.AlertDialog):
    """
    A dialog for translating world lore from one language to another using the Gemini API.
    """

    def __init__(self, on_save_callback):
        super().__init__()
        self.on_save_callback = on_save_callback
        self.modal = True
        self.title = ft.Text("Translate World Lore")
        self.world_data = None
        self.source_lang_code = None

        # --- UI Controls ---
        self.source_language_text = ft.Text()
        self.target_language_dropdown = ft.Dropdown(label="Translate to")
        self.progress_ring = ft.ProgressRing(visible=False)
        self.translate_button = ft.FilledButton("Translate", on_click=self.generate_translation)
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
            ft.FilledButton("Save Translation", on_click=self.save_translation, disabled=True),
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    def open_dialog(self, world_data, source_lang_code):
        """
        Sets up and opens the dialog with the specific world's data.
        """
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

        self.page.dialog = self
        self.open = True
        self.page.update()

    def generate_translation(self, e):
        """
        Calls the Gemini API to generate the translation and logs detailed errors.
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
            # Corrected the keyword to match the placeholder in the prompt string.
            prompt = TRANSLATE_LORE_PROMPT.format(
                source_language=SUPPORTED_LANGUAGES.get(self.source_lang_code),
                target_language=target_lang_name,
                text=source_lore  # Changed from 'text_to_translate' to 'text'
            )

            service = GeminiService()
            translated_text = service.get_text_response(prompt)

            self.translated_lore_field.value = translated_text
            self.translated_lore_field.read_only = False
            self.actions[1].disabled = False

        except Exception as ex:
            print("--- Detailed Traceback in Translation Dialog ---")
            traceback.print_exc()
            print("--- End of Traceback ---")
            self.show_error(f"Error: {type(ex).__name__}. See console for details.")

        finally:
            self.progress_ring.visible = False
            self.translate_button.disabled = False
            self.update()

    def save_translation(self, e):
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
            supabase.table('worlds').update({'lore': updated_lore}).eq('id', self.world_data['id']).execute()

            self.page.snack_bar = ft.SnackBar(content=ft.Text("Translation saved!"), bgcolor=ft.Colors.GREEN_700)
            self.page.snack_bar.open = True

            if self.on_save_callback:
                self.on_save_callback()

            self.close_dialog(e)

        except Exception as ex:
            self.show_error(f"Database Error: {ex}")

    def show_error(self, message):
        """Helper to display an error in the dialog's title."""
        self.title = ft.Text(message, color=ft.Colors.RED)
        self.update()

    def close_dialog(self, e):
        """Closes the dialog and resets its state."""
        self.open = False
        self.title = ft.Text("Translate World Lore")
        self.page.update()
