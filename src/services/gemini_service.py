from google import genai
from ..config import GEMINI_API_KEY
from ..services.supabase_service import supabase
import tempfile
import pathlib


class _ChatSessionWrapper:
    """
    A helper class to manage a conversational chat session's history.
    """

    def __init__(self, client: genai.Client, model_name: str, initial_prompt: str = None):
        self.client = client
        self.model_name = model_name
        self.history = []
        if initial_prompt:
            self.history.extend([
                {'role': 'user', 'parts': [{'text': initial_prompt}]},
                {'role': 'model',
                 'parts': [{'text': "Understood. I am ready to answer questions based on the provided context."}]}
            ])

    def send_message(self, message: str):
        """Sends a message, including history, to the model."""
        self.history.append({'role': 'user', 'parts': [{'text': message}]})
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=self.history
        )
        try:
            response_text = response.text
        except Exception:
            response_text = "My response was blocked. Please try rephrasing your message."
        self.history.append({'role': 'model', 'parts': [{'text': response_text}]})
        return response


class GeminiService:
    """
    Service class for interacting with the Google Gemini API.
    """

    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set.")
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model_name = 'models/gemini-1.5-flash'

    def start_chat_session(self, initial_prompt: str = None):
        """Starts a new conversational chat for the Lore Master."""
        return _ChatSessionWrapper(
            client=self.client,
            model_name=self.model_name,
            initial_prompt=initial_prompt
        )

    def upload_srd_to_gemini(self, srd_bucket_path: str):
        """
        Downloads the SRD from Supabase and uploads it to the Gemini File API.
        This is now a separate, one-time operation.
        """
        try:
            print("Downloading SRD from Supabase for Gemini upload...")
            file_bytes = supabase.download_file("documents", srd_bucket_path)
            print("Download complete. Uploading to Gemini File API...")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(file_bytes)
                tmp_file_path = pathlib.Path(tmp_file.name)

            try:
                srd_file = self.client.files.upload(
                    path=tmp_file_path,
                    display_name="SRD Document"
                )
                print(f"Successfully uploaded to Gemini as: {srd_file.name}")
                return srd_file
            finally:
                tmp_file_path.unlink()
        except Exception as e:
            print(f"--- ERROR during SRD upload to Gemini: {e} ---")
            return None

    def query_srd_file(self, question: str, srd_file: genai.files):
        """
        Queries the already-uploaded SRD file with a user's question.
        This is the new, efficient method for the Rules Lawyer.
        """
        print(f"Querying Gemini with file {srd_file.name}...")
        prompt = (
            f"You are a D&D Rules Lawyer. Your answers must be based *only* on the provided SRD document. "
            f"If the answer isn't in the document, say 'That rule is not covered in the provided SRD document.'\n\n"
            f"--- USER QUESTION ---\n{question}"
        )
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[prompt, srd_file]
        )
        return response.text
