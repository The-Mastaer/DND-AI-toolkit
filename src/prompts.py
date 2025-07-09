# src/prompts.py

"""
A centralized library for all AI prompt templates used in the application.
This allows for easy management, editing, and potential future customization
of the AI's behavior without altering the service logic.
"""

# Prompt for generating the initial lore for a new world.
# - world_name: The name of the fantasy world.
GENERATE_WORLD_LORE_PROMPT = """
Generate a brief, evocative description for a fantasy world named '{world_name}'.
Focus on the key themes, conflicts, or unique features of this world. The tone should be suitable for a Dungeons & Dragons campaign.
"""

# Prompt for translating text from a source language to a target language.
# - source_language: The language of the original text (e.g., "English").
# - target_language: The language to translate the text into (e.g., "German").
# - text: The actual text content to be translated.
TRANSLATE_LORE_PROMPT = """
Translate the following text from {source_language} to {target_language}.
Do not add any extra commentary, citations, or explanations. Only provide the raw translated text.

TEXT TO TRANSLATE:
---
{text}
"""