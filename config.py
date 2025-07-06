import json
import logging
import os

# --- Core Static Configuration ---
API_KEY_FILE = "api_key.json"
DB_FILE = "dnd_toolkit.db"

# --- Default AI Model Configuration ---
DEFAULT_TEXT_MODEL = 'gemini-2.5-flash'
DEFAULT_IMAGE_MODEL = 'imagen-3.0-generate-002'
AVAILABLE_TEXT_MODELS = ['gemini-2.5-pro', 'gemini-2.5-flash', 'gemini-1.5-pro', 'gemini-1.5-flash']
AVAILABLE_IMAGE_MODELS = ['imagen-4.0-generate-preview-06-06', 'imagen-3.0-generate-002']


# --- Language Configuration ---
SUPPORTED_LANGUAGES = {
    "en": "English",
    "cs": "Čeština",
    "de": "Deutsch",
    "fr": "Français",
    "es": "Español",
    "it": "Italiano",
    "pl": "Polski"
}

# --- Default Prompts ---
# These are the default prompts. Users can override them in settings.
DEFAULT_NPC_GENERATION_PROMPT = "..." # (Content unchanged for brevity)

DEFAULT_TRANSLATION_PROMPT = "..." # (Content unchanged for brevity)

DEFAULT_NPC_SIMULATION_SHORT_PROMPT = """
You are an AI actor performing as a D&D character. Your goal is to provide a rich, in-character response to a situation.
Your response MUST follow this format:
1.  Start with the character's immediate physical action or change in expression, written in the third person and enclosed in italics.
2.  Follow with the character's spoken dialogue, enclosed in double quotes.

Keep the entire response concise and impactful.

**Character Profile:**
{full_context}

**Campaign Context (The character have general knowledge about this):**
World lore: {campaign_context}

**Situation Context (The character might aware of this based on the situation):**
Party context: {party_context}
Session context: {session_context}

**Situation:**
{situation}

**Your Performance:**
"""

DEFAULT_NPC_SIMULATION_LONG_PROMPT = """
You are an AI Dungeon Master simulating a full scene. Your goal is to generate a longer, multi-paragraph response that describes an entire encounter.
Describe the scene, the NPC's actions, and write out a potential back-and-forth dialogue between the NPC and the player characters (see party_context).
The response should be at least 3-4 paragraphs long and feel like a read-aloud section from a D&D module.
Make direct references to the provided Campaign Context, Party Info, and Session History to make the scene feel personal and relevant.

**Character Profile:**
{full_context}

**Campaign Context (The character have general knowledge about this):**
World lore: {campaign_context}

**Situation Context (The character might aware of this based on the situation):**
Party context: {party_context}
Session context: {session_context}

**Situation:**
{situation}

**Your Scene:**
"""

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_api_key():
    """Loads the Gemini API key from a JSON file."""
    if not os.path.exists(API_KEY_FILE):
        logging.warning(f"{API_KEY_FILE} not found. Please create it with your API key.")
        return None
    try:
        with open(API_KEY_FILE, 'r') as f:
            data = json.load(f)
            return data.get("api_key")
    except (IOError, json.JSONDecodeError) as e:
        logging.error(f"Error loading API key from {API_KEY_FILE}: {e}")
        return None