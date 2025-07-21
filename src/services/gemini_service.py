# src/services/gemini_service.py

from google import genai
from google.genai import types
from config import GEMINI_API_KEY
from prompts import GENERATE_ATTRIBUTES_PROMPT, GENERATE_NPC_PROMPT
import json
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict


# --- Pydantic Models for Structured Output ---

class NPCData(BaseModel):
    # **FIX:** Configure the model to generate a Gemini-compatible schema.
    model_config = ConfigDict(extra='allow')
    name: str = Field(description="A fantasy name appropriate for the given race")
    appearance: str = Field(description="A detailed physical description of the character, 3-5 sentences")
    personality: str = Field(description="Describe their traits, demeanor, and motivations, 2-3 sentences")
    backstory: str = Field(description="A brief history of the character, 2-3 sentences")
    plot_hooks: str = Field(
        description="A bulleted list of 2-3 specific, actionable plot hooks for a DM, using '*' for bullets")
    roleplaying_tips: str = Field(
        description="Provide tips on mannerisms, voice, and attitude for the DM, 2-3 sentences")


class NPCAttributes(BaseModel):
    model_config = ConfigDict(extra='allow')
    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    wisdom: int
    charisma: int


class Ability(BaseModel):
    model_config = ConfigDict(extra='allow')
    name: str
    description: str


class Spell(BaseModel):
    model_config = ConfigDict(extra='allow')
    name: str
    description: str


class CharacterStats(BaseModel):
    model_config = ConfigDict(extra='allow')
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
        Generates structured NPC narrative data using a Pydantic schema.
        """
        prompt = GENERATE_NPC_PROMPT.format(**prompt_params)
        print("--- Generating structured NPC data... ---")
        try:
            response = await self.client.aio.models.generate_content(
                model=model_name,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": NPCData,
                }
            )
            return response.candidates[0].content.parts[0].json
        except Exception as e:
            print(f"--- ERROR generating NPC data: {e} ---")
            return None

    async def generate_character_attributes(self, character_class: str, rarity: str, srd_file: types.File,
                                            model_name: str) -> CharacterStats | None:
        """
        Generates structured character stats using the SRD file and a Pydantic schema.
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

        try:
            contents = [srd_file, prompt]

            response = await self.client.aio.models.generate_content(
                model=model_name,
                contents=contents,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": CharacterStats
                }
            )
            return response.candidates[0].content.parts[0].json
        except Exception as e:
            print(f"--- ERROR generating character stats: {e} ---")
            return None

    async def query_srd_file(self, question: str, srd_file: types.File, system_prompt: str, model_name: str):
        """Queries the SRD file with a question and a system prompt."""
        print(f"--- Querying Gemini with file {srd_file.name} using model {model_name} ---")
        try:
            # **FIX:** This is the correct pattern for using a system instruction.
            model = self.client.models.get(model_name)
            model.system_instruction = system_prompt
            contents = [srd_file, question]
            response = await model.aio.generate_content(contents=contents)
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