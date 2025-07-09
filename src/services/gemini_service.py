from google import genai
from typing import Optional
from src import prompts  # Import the new prompts module


class GeminiService:
    """
    A service class to manage interactions with the Google Gemini API.
    This service now uses externalized prompt templates for better maintainability.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client: Optional[genai.Client] = None
        try:
            self.client = genai.Client(api_key=self.api_key)
            print("GeminiService: Client initialized successfully.")
        except Exception as e:
            print(f"GeminiService: Error during initialization - {e}")
            self.client = None

    def _generate_content(self, prompt: str) -> str:
        """Private helper method to call the Gemini API."""
        if not self.client: return "Error: Gemini client not available."
        try:
            # Note: In a real app, you would also pass model settings from AppState here
            response = self.client.generate_content("models/gemini-1.5-flash", prompt)
            return response.text
        except Exception as e:
            print(f"GeminiService: Error generating content - {e}")
            return f"Error: Could not generate content due to: {e}"

    def generate_world_lore(self, world_name: str) -> str:
        """
        Generates lore for a new world using a dedicated prompt template.

        Args:
            world_name (str): The name of the world to generate lore for.

        Returns:
            The generated lore as a string.
        """
        prompt = prompts.GENERATE_WORLD_LORE_PROMPT.format(world_name=world_name)
        return self._generate_content(prompt)

    def translate_text(self, text: str, target_language: str, source_language: str = "English") -> str:
        """
        Translates text to a target language using a dedicated prompt template.

        Args:
            text (str): The text to translate.
            target_language (str): The language to translate to (e.g., "German").
            source_language (str): The source language of the text.

        Returns:
            The translated text as a string.
        """
        prompt = prompts.TRANSLATE_LORE_PROMPT.format(
            source_language=source_language,
            target_language=target_language,
            text=text
        )
        return self._generate_content(prompt)