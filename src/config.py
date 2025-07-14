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

# Permanent ID for the master SRD document on Gemini's File API
GEMINI_SRD_FILE_NAME = os.getenv("GEMINI_SRD_FILE_NAME")

# --- Application Settings ---
SUPPORTED_LANGUAGES = {
    "en": "English",
    "de": "German",
    "es": "Spanish",
    "fr": "French",
    "cs": "Czech",
    "pl": "Polish",
}

# Available themes for the application
AVAILABLE_THEMES = ["light", "dark"]

# Available theme colors
THEME_COLORS = [
    "red", "pink", "purple", "indigo", "blue", "cyan", "teal", "green",
    "lime", "yellow", "amber", "orange", "brown", "grey"
]


# --- AI Model Selections ---
# Using dictionaries to provide both an ID and a user-friendly name for dropdowns.
TEXT_MODELS = {
    "gemini-2.5-pro": "Gemini 2.5 Pro",
    "gemini-2.5-flash": "Gemini 2.5 Flash",
    "gemini-2.5-flash-lite-preview-06-17": "Gemini 2.5 Flash Lite Preview",
}

IMAGE_MODELS = {
    "imagen-4.0-generate-preview-06-06": "Imagen 4.0 Generate Preview",
    "imagen-3.0-generate-002": "Imagen 3.0 Generate",
}

# --- Default Model Definitions ---
# These constants define which models are selected by default in the settings.
DEFAULT_TEXT_MODEL = "gemini-2.5-flash"
DEFAULT_IMAGE_MODEL = "imagen-3.0-generate-002"

# --- D&D Specific Constants ---
DND_RACES = ["Human", "Elf", "Dwarf", "Halfling", "Dragonborn", "Gnome", "Half-Elf", "Half-Orc", "Tiefling"]
DND_CLASSES = ["Barbarian", "Bard", "Cleric", "Druid", "Fighter", "Monk", "Paladin", "Ranger", "Rogue", "Sorcerer", "Warlock", "Wizard"]
DND_BACKGROUNDS = ["Acolyte", "Charlatan", "Criminal", "Entertainer", "Folk Hero", "Guild Artisan", "Hermit", "Noble", "Outlander", "Sage", "Sailor", "Soldier", "Urchin"]
DND_ENVIRONMENTS = ["Arctic", "Coastal", "Desert", "Forest", "Grassland", "Mountain", "Swamp", "Underdark", "Urban"]
DND_HOSTILITIES = ["Friendly", "Neutral", "Hostile"]
DND_RARITIES = ["Common", "Uncommon", "Rare", "Very Rare", "Legendary"]