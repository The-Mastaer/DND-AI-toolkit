# src/services/gemini_service.py

from google import genai
from ..config import GEMINI_API_KEY


class GeminiService:
    """
    A service class to interact with the Google Gemini API.
    It handles model configuration and text generation requests using the genai.Client.
    """

    def __init__(self):
        """
        Initializes the Gemini API client with the provided API key.
        """
        try:
            # According to the knowledge base, we should use genai.Client
            self.client = genai.Client(api_key=GEMINI_API_KEY)
            print("Gemini Service client initialized successfully.")
        except Exception as e:
            # This is a critical failure, so we print and raise
            print(f"CRITICAL: Failed to initialize Gemini client: {e}")
            raise

    def generate_text(self, prompt: str, model_name: str) -> str:
        """
        Generates text using a specified Gemini model.

        Args:
            prompt: The input prompt for the model.
            model_name: The name of the model to use (e.g., "gemini-1.5-flash").

        Returns:
            The generated text as a string.

        Raises:
            Exception: Propagates any exception from the API call upwards
                       so the UI layer can handle it.
        """
        print(f"Generating text with model: {model_name}")
        try:
            # Use the client.generate_content method as specified
            response = self.client.generate_content(
                model=f"models/{model_name}",
                contents=prompt
            )
            return response.text
        except Exception as e:
            print(f"Error generating text with Gemini: {e}")
            # Re-raise the exception to be caught by the calling view
            raise e