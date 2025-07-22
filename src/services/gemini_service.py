# src/services/gemini_service.py

import httpx
import json
import base64
from typing import List, Dict, Optional, Any

from src.config import SUPABASE_URL, SUPABASE_KEY
from src.prompts import GENERATE_ATTRIBUTES_PROMPT, GENERATE_NPC_PROMPT

from pydantic import BaseModel, Field, ConfigDict
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
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Supabase URL and Key must be set.")
        print("--- Initializing Gemini Service (Pragmatic Proxy Mode) ---")
        self.client = httpx.AsyncClient(timeout=60.0)
        self.proxy_url = f"{SUPABASE_URL}/functions/v1/quick-api"
        self.headers = {
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }

        self.client = httpx.AsyncClient(timeout=90.0)

    async def _invoke_proxy(self, payload: dict) -> dict:
        """Private helper to call our master proxy."""
        try:
            response = await self.client.post(self.proxy_url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"--- PROXY ERROR: {e.response.status_code} - {e.response.text} ---")
            raise

    def _clean_json_from_text(self, text: str) -> Dict[str, Any]:
        """Utility to safely extract and parse JSON from the model's markdown-formatted text response."""
        if "```json" in text:
            # More robustly find the start and end of the JSON block
            try:
                json_part = text.split("```json")[1]
                json_part = json_part.split("```")[0]
                return json.loads(json_part.strip())
            except (IndexError, json.JSONDecodeError):
                print("--- WARNING: Could not parse JSON from model response. ---")
                raise ValueError("Invalid JSON format in model response")
        else:
            # If no markdown, assume the whole text is JSON
            return json.loads(text.strip())

    def start_chat_session(self, initial_context: str, model_name: str) -> List[Dict[str, Any]]:
        """
        Pragmatic replacement for chat. Instead of a stateful server object,
        it returns the initial history list. The client is responsible for storing it.
        """
        print(f"--- Creating initial history for chat session ---")
        # This is the initial state that the Flet app will hold and manage
        return [
            {'role': 'user', 'parts': [{'text': initial_context}]},
            {'role': 'model', 'parts': [{'text': "Understood. I am ready to answer questions based on the provided context."}]}
        ]

    async def send_chat_message(self, model_name: str, message: str, history: List[Dict[str, Any]]) -> (str, List[Dict[str, Any]]):
        """
        Sends a message as part of a stateless chat. The client provides the full
        history and gets the updated history back.
        """
        payload = {
            "model": model_name,
            "prompt": message,
            "history": history
        }
        try:
            proxy_response = await self._invoke_proxy(payload)
            response_text = proxy_response['candidates'][0]['content']['parts'][0]['text']

            # Return the new text and the updated history list for the client to store
            updated_history = history + [
                {'role': 'user', 'parts': [{'text': message}]},
                {'role': 'model', 'parts': [{'text': response_text}]}
            ]
            return response_text, updated_history
        except Exception as e:
            print(f"--- ERROR in send_chat_message: {e} ---")
            # Return error message and the original, unmodified history
            return f"An error occurred: {e}", history

    async def get_gemini_file_by_name(self, file_name: str):
        """DEPRECATED: File management is now handled by the backend."""
        print("--- WARNING: get_gemini_file_by_name is deprecated. ---")
        raise NotImplementedError("File management must be handled server-side and cannot be done via this proxy service.")

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
        payload = {
            "model": model_name,
            "prompt": prompt,
            "response_schema": manual_npc_schema
        }
        try:
            print("--- Calling proxy for structured NPC data... ---")
            proxy_response = await self._invoke_proxy(payload)

            # --- NEW: Robust Response Validation ---
            if not proxy_response.get('candidates'):
                # Check for a safety block reason in the prompt feedback
                feedback = proxy_response.get('promptFeedback', {})
                block_reason = feedback.get('blockReason', 'Unknown')
                raise ValueError(f"API call failed or was blocked. Reason: {block_reason}. Response: {proxy_response}")

            # Ensure the expected structure exists before accessing it
            candidate = proxy_response['candidates'][0]
            if 'content' not in candidate or 'parts' not in candidate['content'] or not candidate['content']['parts']:
                finish_reason = candidate.get('finishReason', 'Unknown')
                raise ValueError(
                    f"Response from API is incomplete. Finish Reason: {finish_reason}. Check for safety blocks.")

            response_text = candidate['content']['parts'][0].get('text', '')
            if not response_text:
                raise ValueError("API returned an empty text response. This is often due to safety filters.")
            # --- End of New Validation ---

            data = self._clean_json_from_text(response_text)
            return NPCData(**data)

        except ValueError as ve:
            # Catch our specific validation errors and print them clearly
            print(f"--- VALIDATION ERROR in generate_npc_data: {ve} ---")
            return None
        except Exception as e:
            # Catch other unexpected errors
            print(f"--- UNEXPECTED ERROR in generate_npc_data: {e} ---")
            return None


    async def generate_character_attributes(self, character_class: str, rarity: str, srd_file_uri: str,
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

        payload = {
            "model": model_name,
            "prompt": prompt,
            "file_uri": srd_file_uri,
            "response_schema": manual_character_stats_schema
        }

        try:
            print(f"--- Calling proxy for stats for {rarity} {character_class}... ---")
            proxy_response = await self._invoke_proxy(payload)
            response_text = proxy_response['candidates'][0]['content']['parts'][0]['text']
            data = self._clean_json_from_text(response_text)

            # Convert the list-of-objects from the schema back to the dicts your Pydantic model expects
            data['saving_throws'] = {item['name']: item['modifier'] for item in data.get('saving_throws', [])}
            data['skills'] = {item['name']: item['modifier'] for item in data.get('skills', [])}
            return CharacterStats(**data)
        except Exception as e:
            print(f"--- ERROR generating character stats: {e} ---")
            return None


    async def generate_image(self, prompt: str, model_name: str) -> Optional[bytes]:
        """Generates an image by calling the secure proxy."""
        print(f"--- Calling proxy for image generation... ---")
        payload = {
            "model": model_name,
            "prompt": prompt,
            "image_response": True # Signal to our proxy that we want an image
        }
        try:
            # We need a separate call for image bytes, assuming the proxy returns raw bytes
            response = await self.client.post(self.proxy_url, headers=self.headers, json=payload, timeout=120.0)
            response.raise_for_status()
            return response.content
        except Exception as e:
            print(f"--- ERROR in generate_image: {e} ---")
            return None


# A single, shared instance of the service.
gemini_service = GeminiService()