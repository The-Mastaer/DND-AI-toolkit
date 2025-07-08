from google import genai
from typing import Optional


class GeminiService:
    """
    A service class to manage interactions with the Google Gemini API.

    This class encapsulates the configuration and usage of the Gemini model,
    adhering to the modern `google-genai` SDK. It provides a clean interface
    for other parts of the application to generate text content without
    needing to know the implementation details of the API.
    """

    def __init__(self, api_key: str):
        """
        Initializes the GeminiService and configures the API.

        Args:
            api_key (str): The Google Gemini API key.
        """
        self.api_key = api_key
        self.client: Optional[genai.Client] = None
        try:
            # The new SDK uses a Client object for interaction.
            self.client = genai.Client(api_key=self.api_key)
            print("GeminiService: Client initialized successfully using 'google-genai' SDK.")
        except Exception as e:
            print(f"GeminiService: Error during initialization - {e}")
            self.client = None

    def generate_text(self, prompt: str) -> str:
        """
        Generates text content based on a given prompt.

        Args:
            prompt (str): The input prompt for the model.

        Returns:
            The generated text as a string. Returns an error message if
            generation fails.
        """
        if not self.client:
            return "Error: Gemini client is not available."

        try:
            print(f"GeminiService: Generating text for prompt: '{prompt[:30]}...'")
            # The method is now called on the client object.
            response = self.client.generate_content(
                model="models/gemini-1.5-flash",
                contents=prompt
            )
            print("GeminiService: Text generated successfully.")
            return response.text
        except Exception as e:
            print(f"GeminiService: Error generating content - {e}")
            return f"Error: Could not generate content due to: {e}"


# Example of how to use this service (for testing purposes)
def main():
    # This requires a .env file in the project root
    from src.config import GEMINI_API_KEY
    if not GEMINI_API_KEY:
        print("Gemini API key not found in environment variables.")
        return

    gemini_service = GeminiService(api_key=GEMINI_API_KEY)

    if gemini_service.client:
        prompt = "In three words, what is the essence of Dungeons & Dragons?"
        result = gemini_service.generate_text(prompt)
        print(f"\nPrompt: {prompt}")
        print(f"Gemini Says: {result}\n")


if __name__ == "__main__":
    # Note: genai.Client() is async under the hood but the generate_content
    # method provided here is synchronous. For a Flet app, long-running
    # generations should be wrapped in page.run_in_executor or similar.
    main()