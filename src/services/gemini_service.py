# src/services/gemini_service.py

from google import genai
from google.genai import types
from config import GEMINI_API_KEY
from prompts import GENERATE_ATTRIBUTES_PROMPT, GENERATE_NPC_PROMPT
import json
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict
import random


# --- Pydantic Models for Structured Output ---

class NPCData(BaseModel):
    # **FIX:** Configure the model to generate a Gemini-compatible schema.
    model_config = ConfigDict(extra='forbid')
    name: str = Field(description="A fantasy name appropriate for the given race")
    gender: str = Field(description="The character's gender (e.g., Male, Female, Non-binary)")
    appearance: str = Field(description="A detailed physical description of the character, 3-5 sentences")
    personality: str = Field(description="Describe their traits, demeanor, and motivations, 2-3 sentences")
    backstory: str = Field(description="A brief history of the character, 2-3 sentences")
    plot_hooks: str = Field(
        description="A bulleted list of 2-3 specific, actionable plot hooks for a DM, using '*' for bullets")
    roleplaying_tips: str = Field(
        description="Provide tips on mannerisms, voice, and attitude for the DM, 2-3 sentences")


class NPCAttributes(BaseModel):
    model_config = ConfigDict(extra='forbid')
    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    wisdom: int
    charisma: int


class Ability(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str
    description: str


class Spell(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str
    description: str


class CharacterStats(BaseModel):
    model_config = ConfigDict(extra='forbid')
    level: int
    hp: int
    ac: int
    attributes: NPCAttributes
    saving_throws: Dict[str, str]
    skills: Dict[str, str]
    abilities: List[Ability]
    spells: List[Spell]


class GeminiService:
    """
    Service class for all interactions with the Google Gemini API,
    updated to use the latest SDK features for structured output.
    """

    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set in the environment variables.")
        print("--- Initializing Gemini Service ---")
        self.client = genai.Client(api_key=GEMINI_API_KEY)

    def start_chat_session(self, initial_context: str, model_name: str):
        """
        Starts a new conversational chat session.
        This is corrected to use the proper client.chats.create method.
        """
        print(f"--- Starting new Gemini Chat Session with model: {model_name} ---")
        # **FIX:** Reverted to the correct method for creating a chat session with history.
        chat_session = self.client.chats.create(
            model=model_name,
            history=[
                {'role': 'user', 'parts': [{'text': initial_context}]},
                {'role': 'model',
                 'parts': [{'text': "Understood. I am ready to answer questions based on the provided context."}]}
            ]
        )
        return chat_session

    async def get_text_response(self, prompt: str, model_name: str) -> str:
        """Gets a simple text response from the model for non-chat tasks."""
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

    async def get_gemini_file_by_name(self, file_name: str) -> types.File | None:
        """Retrieves a Gemini File object by its name (URI)."""
        try:
            file_info = self.client.files.get(name=file_name)
            if file_info.state.name == 'ACTIVE':
                print(f"--- Successfully retrieved Gemini file: {file_info.name} ---")
                return file_info
            else:
                print(f"--- Gemini file {file_info.name} is not active. State: {file_info.state.name} ---")
                return None
        except Exception as e:
            print(f"--- ERROR retrieving Gemini file {file_name}: {e} ---")
            return None

    async def generate_npc_data(self, model_name: str, **prompt_params) -> NPCData | None:
        """
        Generates structured NPC narrative data using a MANUALLY DEFINED schema
        to bypass any Pydantic conversion issues.
        """
        prompt = GENERATE_NPC_PROMPT.format(**prompt_params)
        print("--- Generating structured NPC data with a MANUAL schema... ---")

        # Manually define the schema as a dictionary.
        # This structure is based on the OpenAPI 3.0 subset Gemini uses[cite: 191].
        manual_npc_schema = {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "A fantasy name appropriate for the given race"
                },
                "gender": {
                    "type": "string",
                    "description": "The character's gender (e.g., Male, Female, Non-binary)"
                },
                "appearance": {
                    "type": "string",
                    "description": "A detailed physical description of the character, 3-5 sentences"
                },
                "personality": {
                    "type": "string",
                    "description": "Describe their traits, demeanor, and motivations, 2-3 sentences"
                },
                "backstory": {
                    "type": "string",
                    "description": "A brief history of the character, 2-3 sentences"
                },
                "plot_hooks": {
                    "type": "string",
                    "description": "A bulleted list of 2-3 specific, actionable plot hooks for a DM, using '*' for bullets"
                },
                "roleplaying_tips": {
                    "type": "string",
                    "description": "Provide tips on mannerisms, voice, and attitude for the DM, 2-3 sentences"
                }
            },
            # We explicitly require all fields to be present.
            "required": ["name", "appearance", "personality", "backstory", "plot_hooks", "roleplaying_tips"]
        }

        try:
            response = await self.client.aio.models.generate_content(
                model=model_name,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    # Use our manually defined dictionary instead of the Pydantic class
                    "response_schema": manual_npc_schema,
                }
            )

            # We can't use response.parsed here since we didn't give it a class,
            # so we'll construct the NPCData object from the returned json.
            if response.text:
                import json
                data = json.loads(response.text)
                return NPCData(**data)
            return None

        except Exception as e:
            print(f"--- ERROR generating NPC data with MANUAL schema: {e} ---")
            return None

    async def generate_character_attributes(self, character_class: str, rarity: str, srd_file: types.File,
                                            model_name: str) -> CharacterStats | None:
        """
        Generates structured character stats using a MANUAL schema.
        """
        rarity_map = {
            "Common": "a single, specific level between 1 and 2",
            "Uncommon": "a single, specific level between 3 and 5",
            "Rare": "a single, specific level between 6 and 10",
            "Very Rare": "a single, specific level between 10 and 15",
            "Legendary": "a single, specific level between 16 and 20",
        }
        level_range = rarity_map.get(rarity, "1")

        prompt = GENERATE_ATTRIBUTES_PROMPT.format(
            character_class=character_class,
            rarity=rarity,
            level_range=level_range
        )
        print(f"--- Generating stats for {rarity} {character_class} (Levels: {level_range}) ---")

        # This complete manual schema defines the entire expected structure,
        # including the improved list-of-objects for skills and saving throws.
        manual_character_stats_schema = {
            "type": "object",
            "properties": {
                "level": {"type": "integer"},
                "hp": {"type": "integer", "description": "Hit Points"},
                "ac": {"type": "integer", "description": "Armor Class"},
                "attributes": {
                    "type": "object",
                    "properties": {
                        "strength": {"type": "integer"},
                        "dexterity": {"type": "integer"},
                        "constitution": {"type": "integer"},
                        "intelligence": {"type": "integer"},
                        "wisdom": {"type": "integer"},
                        "charisma": {"type": "integer"}
                    },
                    "required": ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
                },
                "saving_throws": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "e.g., Dexterity"},
                            "modifier": {"type": "string", "description": "e.g., +5"}
                        },
                        "required": ["name", "modifier"]
                    }
                },
                "skills": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "e.g., Stealth"},
                            "modifier": {"type": "string", "description": "e.g., +8"}
                        },
                        "required": ["name", "modifier"]
                    }
                },
                "abilities": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"}
                        },
                        "required": ["name", "description"]
                    }
                },
                "spells": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"}
                        },
                        "required": ["name", "description"]
                    }
                }
            },
            "required": ["level", "hp", "ac", "attributes", "saving_throws", "skills", "abilities", "spells"]
        }

        try:
            contents = [srd_file, prompt]
            response = await self.client.aio.models.generate_content(
                model=model_name,
                contents=contents,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": manual_character_stats_schema
                }
            )
            # Manually parse the JSON and construct the Pydantic model
            if response.text:
                data = json.loads(response.text)

                # Before creating the final object, we must convert the list-of-objects
                # for skills and saving_throws back into the dictionaries your Pydantic model expects.
                data['saving_throws'] = {item['name']: item['modifier'] for item in data.get('saving_throws', [])}
                data['skills'] = {item['name']: item['modifier'] for item in data.get('skills', [])}

                return CharacterStats(**data)
            return None
        except Exception as e:
            print(f"--- ERROR generating character stats: {e} ---")
            return None

    async def query_srd_file(self, question: str, srd_file: types.File, system_prompt: str, model_name: str):
        """Queries the SRD file with a question and a system prompt."""
        print(f"--- Querying Gemini with file {srd_file.name} using model {model_name} ---")
        try:
            # **FIX:** This is the correct pattern for using a system instruction.
            response = await self.client.aio.models.generate_content(
                model=model_name,
                contents=[srd_file, question],
                # The file object and text prompt are correctly combined [cite: 384, 401]
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt)
            )
            return response.text
        except Exception as e:
            print(f"--- ERROR during SRD query: {e} ---")
            return f"An error occurred while querying the SRD. Details: {e}"

    async def generate_image(self, prompt: str, model_name: str) -> bytes | None:
        """Generates an image using the specified model and prompt."""
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


# A single, shared instance of the service.
gemini_service = GeminiService()