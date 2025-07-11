# src/services/gemini_service.py

from google import genai
from google.genai import types
from ..config import GEMINI_API_KEY
from ..services.supabase_service import supabase
import tempfile
import pathlib
import asyncio


class GeminiService:
    """
    Service class for all interactions with the Google Gemini API.
    """

    def __init__(self):
        """
        Initializes the Gemini client.
        """
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set in the environment variables.")
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model_name = 'gemini-1.5-flash'

    def start_chat_session(self, initial_context: str):
        """
        Starts a new conversational chat session.
        """
        print("--- Starting new Gemini Chat Session ---")
        history = [
            {'role': 'user', 'parts': [{'text': initial_context}]},
            {'role': 'model',
             'parts': [{'text': "Understood. I am ready to answer questions based on the provided context."}]}
        ]
        chat = self.client.chats.create(model=self.model_name, history=history)
        return chat

    async def upload_srd_to_gemini(self, srd_bucket_path: str):
        """
        Downloads the SRD from Supabase and uploads it to the Gemini File API.
        """
        try:
            print("--- Downloading SRD from Supabase for Gemini upload... ---")
            file_bytes = await supabase.download_file("documents", srd_bucket_path)
            print("--- Download complete. Uploading to Gemini File API... ---")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(file_bytes)
                tmp_file_path = pathlib.Path(tmp_file.name)

            try:
                print(f"Uploading file from temporary path: {tmp_file_path}")
                srd_file = await asyncio.to_thread(
                    self.client.files.upload,
                    file=tmp_file_path,
                    display_name="D&D SRD Document"
                )
                print(f"--- Successfully uploaded to Gemini as: {srd_file.name} ---")
                return srd_file
            finally:
                tmp_file_path.unlink()
        except Exception as e:
            print(f"--- ERROR during SRD upload to Gemini: {e} ---")
            return None

    async def query_srd_file(self, question: str, srd_file: types.File, system_prompt: str):
        """
        Queries the already-uploaded SRD file with a user's question.
        """
        print(f"--- Querying Gemini with file {srd_file.name}... ---")

        # *** FIX: Combine the system prompt and the user's question ***
        full_prompt = f"{system_prompt}\n\nUSER QUESTION: {question}"

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=[full_prompt, srd_file]
            )
            return response.text
        except Exception as e:
            print(f"--- ERROR during SRD query: {e} ---")
            return f"An error occurred while querying the SRD: {e}"

    async def get_text_response(self, prompt: str) -> str:
        """
        Gets a simple text response from the model for non-chat tasks.
        """
        print("--- Getting simple text response from Gemini ---")
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text
        except Exception as e:
            print(f"--- ERROR during text generation: {e} ---")
            return f"An error occurred: {e}"
