from google import genai
from ..config import GEMINI_API_KEY


class GeminiService:
    """
    A service class to interact with the Google Gemini API.
    This version is simplified to its core function to help expose underlying errors.
    """

    def __init__(self):
        """
        Initializes the Gemini Service and configures the API key.
        """
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set. Please add it to your configuration.")

        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model_name = 'models/gemini-1.5-flash'

    def get_text_response(self, prompt_text: str) -> str:
        """
        Sends a prompt to the Gemini API and returns the text response.
        This function will now let any exception "bubble up" to the caller.

        Args:
            prompt_text: The full prompt to send to the model.

        Returns:
            The generated text as a string.
        """
        print("--- Sending Prompt to Gemini ---")
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt_text
        )

        print("--- Full Gemini Response ---")
        print(response)

        # We will attempt to access .text and let the calling function handle any error.
        return response.text
