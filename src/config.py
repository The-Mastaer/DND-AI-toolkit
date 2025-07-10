import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from a .env file
load_dotenv()

# --- Type hints added for clarity and IDE support ---

# Supabase configuration
SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
SUPABASE_KEY: Optional[str] = os.getenv("SUPABASE_KEY")

# Gemini API configuration
GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")

# --- Application Settings ---
SUPPORTED_LANGUAGES = {
    "en": "English",
    "de": "German",
    "es": "Spanish",
    "fr": "French",
    "cs": "Czech",
}

# --- AI Model Selections ---
# Using dictionaries to provide both an ID and a user-friendly name for dropdowns.
TEXT_MODELS = {
    "gemini-2.5-pro": "Gemini 2.5 Pro",
    "gemini-2.5-flash": "Gemini 2.5 Flash",
    "gemini-2.5-flash-lite-preview-06-17": "Gemini 2.5 Flash Lite Preview",
}

IMAGE_MODELS = {
    "gemini-2.0-flash-preview-image-generation": "Gemini 2.0 Flash Image Generation",
    "imagen-4.0-generate-preview-06-06": "Imagen 4.0 Generate Preview",
    "imagen-3.0-generate-002": "Imagen 3.0 Generate",
}

# --- Default Model Definitions ---
# These constants define which models are selected by default in the settings.
DEFAULT_TEXT_MODEL = "gemini-2.5-flash"
DEFAULT_IMAGE_MODEL = "gemini-2.0-flash-preview-image-generation"