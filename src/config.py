# src/config.py

import logging

# --- Aria's Note: ---
# This file no longer contains secrets. It's for static, non-sensitive
# configuration data that is shared across the application. Secrets are now
# managed exclusively via the .env file and os.environ.

# --- Default AI Model Configuration ---
DEFAULT_TEXT_MODEL = 'gemini-1.5-flash'
DEFAULT_IMAGE_MODEL = 'imagen-3'
AVAILABLE_TEXT_MODELS = ['gemini-1.5-pro', 'gemini-1.5-flash']
AVAILABLE_IMAGE_MODELS = ['imagen-3']


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

# --- NPC Generator Options ---
GENDER_OPTIONS = ["Any", "Male", "Female", "Non-binary"]
ATTITUDE_OPTIONS = ["Any", "Friendly", "Indifferent", "Hostile"]
RARITY_OPTIONS = ["Any", "Common", "Uncommon", "Rare"]
ENVIRONMENT_OPTIONS = ["Any", "Urban", "Wilderness", "Dungeon", "Aquatic", "Planar"]
RACE_OPTIONS = [
    "Any", "Human", "Elf", "Dwarf", "Halfling", "Gnome", "Half-Elf",
    "Half-Orc", "Tiefling", "Dragonborn", "Aasimar", "Goblin", "Orc"
]
CLASS_OPTIONS = [
    "Any", "Fighter", "Rogue", "Wizard", "Cleric", "Ranger", "Barbarian",
    "Paladin", "Sorcerer", "Warlock", "Monk", "Druid", "Bard", "Artificer"
]
BACKGROUND_OPTIONS = [
    "Any", "Acolyte", "Charlatan", "Criminal", "Entertainer", "Folk Hero",
    "Guild Artisan", "Hermit", "Noble", "Outlander", "Sage", "Sailor",
    "Soldier", "Urchin"
]


# --- Default Prompts ---
# These are the default prompts. Users can override them in settings.
DEFAULT_LORE_MASTER_PROMPT = """
You are the Lore Master, an AI assistant for a Dungeon Master.
Your knowledge is based on the following context. Use it to answer the user's questions.
If the answer is not in the context, say that you don't have that information.

--- WORLD LORE ---
{world_lore}
---
--- ACTIVE CAMPAIGN PARTY INFO ---
{party_info}
---
--- ACTIVE CAMPAIGN SESSION HISTORY ---
{session_history}
---

User's Question: {user_question}
"""

DEFAULT_NPC_GENERATION_PROMPT = """
You are a creative Dungeon Master assistant. Your task is to generate a compelling D&D NPC that fits within the provided campaign context.
The output MUST be a valid JSON object with the exact keys provided in the parameters.
For any parameter set to "Random", you must invent a suitable, creative value that is consistent with the campaign context.
If a parameter has a specific value (e.g., "Friendly", "Fighter", "City"), you MUST use that value.
Descriptions should be concise but evocative. Plot hooks should be actionable and intriguing.

**CONTEXT (Use this information to ground the NPC in the world):**
{campaign_context}
{party_context}
{session_context}
{custom_prompt_section}

**PARAMETERS (Generate values for these keys):**
- name: (Invent a suitable name)
- gender: {gender}
- race_class: (Combine the generated Race and Class into a summary, e.g., "Human Fighter" or "Elf Wizard")
- appearance: (A 4-5 sentence description)
- personality: (A 4-5 sentence description)
- backstory: (A concise 5-10 sentence summary of their history, tied to the provided context)
- plot_hooks: (A 1-3 sentence hook, tied to the provided context)
- roleplaying_tips: (A few bullet points on voice, mannerisms, and demeanor)
- attitude: {attitude}
- rarity: {rarity}
- race: {race}
- character_class: {character_class}
- environment: {environment}
- background: {background}

Generate the NPC now based on these rules. The response must only contain the JSON object.
"""

DEFAULT_TRANSLATION_PROMPT = """
You are an expert translator specializing in fantasy literature. Translate the following text into {target_language_name} ({target_language_code}).
Maintain the original tone, style, and formatting. The text is for a Dungeons & Dragons world-building tool.
It is critical that you ONLY return the translated text. Do not add any commentary, greetings, or explanations.

--- TEXT TO TRANSLATE ---
{text_to_translate}
--- END OF TEXT ---
"""

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

DEFAULT_RULES_LAWYER_PROMPT = """
You are a D&D 5th Edition Rules Lawyer assistant. Your task is to answer the user's question based *only* on the provided text from the System Reference Document (SRD).
First, find the relevant section(s) in the SRD text that answer the user's question.
Then, synthesize those sections into a clear and concise answer. If the SRD does not contain the answer, state that clearly.
Do not use any knowledge outside of the provided SRD text.

SRD CONTEXT:
---
{srd_context}
---

USER'S QUESTION:
{user_question}

Your Answer:
"""

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')