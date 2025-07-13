# src/services/gemini_service.py

from google import genai
from google.genai import types
from config import GEMINI_API_KEY, DEFAULT_IMAGE_MODEL
from services.supabase_service import supabase
import tempfile
import pathlib
import asyncio


class GeminiService:
    """
    Service class for all interactions with the Google Gemini API.
    This is now a singleton, initialized once at app startup.
    """

    def __init__(self):
        """
        Initializes the Gemini client.
        """
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set in the environment variables.")
        print("--- Initializing Gemini Service ---")
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def start_chat_session(self, initial_context: str, model_name: str):
        """
        Starts a new conversational chat session using the correct SDK method.
        """
        print(f"--- Starting new Gemini Chat Session with model: {model_name} ---")
        chat_session = self.client.chats.create(
            model=model_name,
            history=[
                {'role': 'user', 'parts': [{'text': initial_context}]},
                {'role': 'model',
                 'parts': [{'text': "Understood. I am ready to answer questions based on the provided context."}]}
            ]
        )
        return chat_session

    async def upload_srd_to_gemini(self, srd_bucket_path: str) -> str | None:
        """
        Downloads the SRD from Supabase and uploads it to the Gemini File API.
        Returns the Gemini File URI (name) if successful, None otherwise.
        """
        try:
            print("--- Downloading SRD from Supabase for Gemini upload... ---")
            file_bytes = await supabase.download_file("documents", srd_bucket_path)
            if not file_bytes:
                print("--- ERROR: Failed to download SRD file from Supabase. ---")
                return None
            print("--- Download complete. Uploading to Gemini File API... ---")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(file_bytes)
                tmp_file_path = pathlib.Path(tmp_file.name)

            try:
                print(f"Uploading file from temporary path: {tmp_file_path}")
                srd_file = await asyncio.to_thread(
                    self.client.files.upload,
                    file=tmp_file_path,
                )
                print(f"--- Successfully uploaded to Gemini as: {srd_file.name} ---")
                return srd_file.name
            finally:
                if tmp_file_path.exists():
                    tmp_file_path.unlink()
        except Exception as e:
            print(f"--- ERROR during SRD upload to Gemini: {e} ---")
            return None

    async def get_gemini_file_by_name(self, file_name: str) -> types.File | None:
        """
        Retrieves a Gemini File object by its name (URI).
        """
        try:
            file_info = await asyncio.to_thread(self.client.files.get, name=file_name)
            if file_info.state.name == 'ACTIVE':
                print(f"--- Successfully retrieved Gemini file: {file_info.name} ---")
                return file_info
            else:
                print(f"--- Gemini file {file_info.name} is not active. State: {file_info.state.name} ---")
                return None
        except Exception as e:
            print(f"--- ERROR retrieving Gemini file {file_name}: {e} ---")
            return None

    async def query_srd_file(self, question: str, srd_file: types.File, system_prompt: str, model_name: str):
        """
        Queries the already-uploaded SRD file with a user's question.
        """
        print(f"--- Querying Gemini with file {srd_file.name} using model {model_name} ---")
        try:
            generation_config = types.GenerateContentConfig(
                system_instruction=system_prompt
            )
            contents = [srd_file, question]
            response = await self.client.aio.models.generate_content(
                model=model_name,
                contents=contents,
                config=generation_config
            )
            return response.text
        except Exception as e:
            print(f"--- ERROR during SRD query: {e} ---")
            return f"An error occurred while querying the SRD: {e}"

    async def get_text_response(self, prompt: str, model_name: str) -> str:
        """
        Gets a simple text response from the model for non-chat tasks.
        """
        print(f"--- Getting simple text response from Gemini using model {model_name} ---")
        try:
            response = await self.client.aio.models.generate_content(
                model=model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            print(f"--- ERROR during text generation: {e} ---")
            return f"An error occurred: {e}"

    async def generate_image(self, prompt: str, model_name: str) -> bytes | None:
        """
        Generates an image using the specified model and prompt.

        Args:
            prompt (str): The text prompt for image generation.
            model_name (str): The image generation model to use.

        Returns:
            bytes | None: The image bytes if successful, otherwise None.
        """
        print(f"--- Generating portrait with Gemini using model: {model_name} ---")
        try:
            response = await self.client.aio.models.generate_images(
                model=model_name,
                prompt=prompt,
                config=types.GenerateImagesConfig(number_of_images=1)
            )
            if response.generated_images:
                print("--- Image generated successfully. ---")
                return response.generated_images[0].image.image_bytes
            else:
                print("--- Gemini returned no images. ---")
                return None
        except Exception as e:
            print(f"--- ERROR during image generation: {e} ---")
            return None


# A single, shared instance of the service that can be imported elsewhere.
gemini_service = GeminiService()