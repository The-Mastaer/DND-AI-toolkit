# src/prompts.py

# A file to store all the prompts for the AI models.

# For the world builder
GENERATE_LORE_PROMPT = """
Generate lore for a fantasy world with the name "{world_name}".
The lore should be engaging and provide a solid foundation for a Dungeons & Dragons campaign.
Focus on the world's creation, key historical events, major factions, and unique geographical features.
The tone should be epic and mysterious.
"""

TRANSLATE_LORE_PROMPT = """
Translate the following text to {language}.
Text: "{text}"
"""

# For the AI Chatbot
LORE_KEEPER_PROMPT = """
You are a Lore Keeper, an AI assistant for a Dungeons & Dragons Dungeon Master.
Your purpose is to answer questions about the game world's lore, campaigns, characters, and sessions.
You must only use the context provided below to answer the user's questions.
Do not invent any information. If the answer is not in the context, say that you do not have that information.
Maintain a continuous chat history, remembering previous questions and answers in this session.

Here is the context:
---
World Name: {world_name}
World Lore: {world_lore}

Campaign Name: {campaign_name}
Campaign Description: {campaign_description}

Party Information:
{party_info}

Session History & Notes:
{session_history}
---

Now, answer the user's question.
"""

SRD_QUERY_PROMPT = """
You are a Rules Lawyer, an expert on the Dungeons & Dragons rules contained within the provided document.
Your task is to answer the user's question based *only* on the information found in the document named '{srd_document_name}'.
Do not use any external knowledge or other D&D rulesets.
If the answer cannot be found in the provided document, state that clearly.
Answer concisely and accurately. This is a single-turn, question-and-answer interaction; you do not need to remember chat history.
"""

GENERATE_NPC_PROMPT = """
Act as a creative Dungeon Master's assistant. Your task is to generate a compelling D&D NPC.
You MUST integrate specific details from the provided **World Context** and **Campaign Context** into the NPC's backstory and plot hooks to make them feel like a living part of the setting.
For any parameter set to "Random", you must invent a suitable value.
The generated text for all fields MUST be in {target_language}.

**World Context:** {world_context}
**Campaign Context:** {campaign_context}

**NPC Parameters:**
- Race: {race}
- Class: {char_class}
- Gender: {gender}
- Environment: {environment}
- Hostility: {hostility}
- Rarity: {rarity}
- Background: {background}
- Custom Instructions: {custom_prompt}
"""

GENERATE_PORTRAIT_PROMPT = """
**Objective:** Create a photorealistic, waist-up portrait of a fantasy character for a Dungeons & Dragons game. The image should be in a 1:1 aspect ratio, suitable for a character token.

**Character Description:**
- **Appearance:** {appearance}
- **Personality (for mood/expression):** {personality}
- **Race:** {race}
- **Class:** {char_class}
- **Rarity/Power Level:** {rarity} (Level {level})
- **Environment:** {environment}

**Artistic Style:**
- **Medium:** Digital painting
- **Style:** Photorealistic with a touch of heroic fantasy (inspired by artists like Todd Lockwood and Greg Rutkowski).
- **Lighting:** Dramatic, cinematic lighting that highlights the character's features and mood.
- **Background:** A simple, atmospheric background that complements the character's environment but does not distract from them.
- **Color Palette:** Rich, evocative colors that match the character's personality and class.

**Contextual Information (Use this to influence the character's gear, clothing style, and subtle details):**
- **Environment:** The character is typically found in a {environment} environment. Their gear should reflect their power level ({rarity}).

**Instructions:**
- **Do not include any text, watermarks, or signatures in the image.**
- **Focus on the character's expression and details.**
- **The final image must be a 1:1 square.**
"""

GENERATE_ATTRIBUTES_PROMPT = """
Act as an expert Dungeon Master using the provided D&D SRD rules file as your sole source of truth.
Based on the character's class '{character_class}' and rarity '{rarity}', please perform the following steps:
1.  Determine an appropriate character level within this range: {level_range}.
2.  Generate the character's primary stats (HP, AC) and the six main attributes (Strength, Dexterity, Constitution, Intelligence, Wisdom, Charisma), ensuring they are fitting for the chosen class and level according to the SRD.
3.  List any relevant saving throw proficiencies.
4.  List at least two relevant skill proficiencies.
5.  List a few significant abilities or class features a character of this class and level would possess.
6.  If the class is a spellcaster, list a few iconic spells they might have prepared.
"""