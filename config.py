import json
import logging
import os

# --- Core Configuration ---
API_KEY_FILE = "api_key.json"
DB_FILE = "dnd_toolkit.db"
TEXT_MODEL_NAME = 'gemini-1.5-flash'
IMAGE_MODEL_NAME = 'imagen-3.0-generate-002'

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- D&D Options for Generator ---
GENDER_OPTIONS = ["Random", "Female", "Male", "Non-binary"]
ATTITUDE_OPTIONS = ["Random", "Friendly", "Neutral", "Hostile"]
RARITY_OPTIONS = ["Random", "Commoner", "Uncommon Adventurer", "Rare Hero", "Legendary Boss"]
ENVIRONMENT_OPTIONS = ["Random", "City", "Forest", "Mountains", "Plains", "Swamp", "Dungeon", "Tavern", "Castle"]
RACE_OPTIONS = [
    "Random", "Human", "Elf", "Dwarf", "Halfling", "Gnome", "Half-Elf",
    "Half-Orc", "Dragonborn", "Tiefling", "Aasimar", "Goblin", "Orc", "Kobold"
]
CLASS_OPTIONS = [
    "Random", "Fighter", "Wizard", "Rogue", "Cleric", "Ranger", "Barbarian",
    "Paladin", "Bard", "Monk", "Druid", "Sorcerer", "Warlock", "Artificer", "Commoner"
]
BACKGROUND_OPTIONS = [
    "Random", "Acolyte", "Charlatan", "Criminal", "Entertainer", "Folk Hero", "Guild Artisan",
    "Hermit", "Noble", "Outlander", "Sage", "Sailor", "Soldier", "Urchin"
]

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