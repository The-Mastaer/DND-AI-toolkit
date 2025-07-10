import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from a .env file
load_dotenv()

# --- Type hints added for clarity and IDE support ---

# Supabase configuration
# The Optional[str] type hint tells the IDE that these variables will be strings
# (or None if not set), resolving the "unresolved reference" warning.
SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
SUPABASE_KEY: Optional[str] = os.getenv("SUPABASE_KEY")

# Gemini API configuration
GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")

# A centralized dictionary for supported languages.
# This makes it easy to add or remove languages in one place.
SUPPORTED_LANGUAGES = {
    "en": "English",
    "de": "German",
    "es": "Spanish",
    "fr": "French",
    "cs": "Czech",
}