DM's AI Toolkit: Database Schema
This document outlines the complete database structure for the DM's AI Toolkit. The architecture is designed to be scalable, relational, and support the "World-centric" and "Translation Layer" models.

Tier 1: Core & Campaign Tables
These tables define the highest level of organization.

worlds
Stores the foundational, language-agnostic settings.

Column Name

Type

Notes

world_id

INTEGER

PRIMARY KEY, AUTOINCREMENT

world_name

TEXT

UNIQUE, NOT NULL. The canonical name of the setting (e.g., "Tara").

world_lore

TEXT

The "World Anvil" text. Core history, cosmology, magic rules.

campaigns
A specific playthrough or story that takes place within a world.

Column Name

Type

Notes

campaign_id

INTEGER

PRIMARY KEY, AUTOINCREMENT

world_id

INTEGER

FOREIGN KEY to worlds.world_id. Links this campaign to a world.

campaign_name

TEXT

NOT NULL. The name of the specific game (e.g., "The Ashen Crown").

language

TEXT

NOT NULL. The language for this campaign (e.g., 'en', 'cs').

party_info

TEXT

Description of the player party for this campaign.

session_history

TEXT

AI-generated or manual summary of recent events.

Tier 2: Entity Tables (Core + Translation)
This pattern is used for all major entities in the world.

characters (Core)
Stores the universal, mechanical data for all unique individuals (NPCs and PCs).

Column Name

Type

Notes

character_id

INTEGER

PRIMARY KEY, AUTOINCREMENT

world_id

INTEGER

FOREIGN KEY to worlds.world_id.

is_player

BOOLEAN

1 for Player Character, 0 for NPC.

level

INTEGER



hp

INTEGER

Hit Points.

ac

INTEGER

Armor Class.

strength

INTEGER



dexterity

INTEGER



constitution

INTEGER



intelligence

INTEGER



wisdom

INTEGER



charisma

INTEGER



skills

TEXT

A list of prominent skills, e.g., "Perception, Stealth, Persuasion".

image_data

BLOB

The character portrait.

character_translations
Stores the language-specific text for each character.

Column Name

Type

Notes

translation_id

INTEGER

PRIMARY KEY, AUTOINCREMENT

character_id

INTEGER

FOREIGN KEY to characters.character_id.

language

TEXT

e.g., 'en', 'cs'.

name

TEXT



race_class

TEXT



appearance

TEXT



personality

TEXT



backstory

TEXT



plot_hooks

TEXT



roleplaying_tips

TEXT



motivation

TEXT

(Primarily for PCs)

objectives

TEXT

(Primarily for PCs)

dm_notes

TEXT

(Secret notes for the DM)

monsters (Core)
Stores stat block templates for non-unique creatures.

Column Name

Type

Notes

monster_id

INTEGER

PRIMARY KEY, AUTOINCREMENT

world_id

INTEGER

FOREIGN KEY to worlds.world_id.

challenge_rating

REAL



hp

INTEGER



ac

INTEGER



speed

TEXT



strength

INTEGER



dexterity

INTEGER



constitution

INTEGER



intelligence

INTEGER



wisdom

INTEGER



charisma

INTEGER



monster_translations
Column Name

Type

Notes

translation_id

INTEGER

PRIMARY KEY, AUTOINCREMENT

monster_id

INTEGER

FOREIGN KEY to monsters.monster_id.

language

TEXT



name

TEXT



description

TEXT



actions

TEXT



special_abilities

TEXT



(This Core + Translation pattern will be repeated for locations, items, quests, factions, etc.)

Tier 3: Narrative & Linking Tables
These tables manage the story and the relationships between entities.

sessions
Detailed notes for each game session.

Column Name

Type

Notes

session_id

INTEGER

PRIMARY KEY, AUTOINCREMENT

campaign_id

INTEGER

FOREIGN KEY to campaigns.campaign_id.

session_number

INTEGER



session_date

TEXT



session_notes

TEXT

The raw, detailed notes from the game session.

quests (Core)
Note: Quests are linked to a specific campaign, not the world.

Column Name

Type

Notes

quest_id

INTEGER

PRIMARY KEY, AUTOINCREMENT

campaign_id

INTEGER

FOREIGN KEY to campaigns.campaign_id.

is_main_quest

BOOLEAN



status

TEXT

e.g., "Not Started", "In Progress", "Completed".

quest_translations
Column Name

Type

Notes

translation_id

INTEGER

PRIMARY KEY, AUTOINCREMENT

quest_id

INTEGER

FOREIGN KEY to quests.quest_id.

language

TEXT



name

TEXT



description

TEXT



objectives

TEXT



factions (Core)
Column Name

Type

Notes

faction_id

INTEGER

PRIMARY KEY, AUTOINCREMENT

world_id

INTEGER

FOREIGN KEY to worlds.world_id.

faction_translations
Column Name

Type

Notes

translation_id

INTEGER

PRIMARY KEY, AUTOINCREMENT

faction_id

INTEGER

FOREIGN KEY to factions.faction_id.

language

TEXT



name

TEXT



description

TEXT



goals

TEXT



history_events (Core)
Column Name

Type

Notes

event_id

INTEGER

PRIMARY KEY, AUTOINCREMENT

world_id

INTEGER

FOREIGN KEY to worlds.world_id.

event_date

TEXT

Can be a year, a date, or a descriptive era.

history_event_translations
Column Name

Type

Notes

translation_id

INTEGER

PRIMARY KEY, AUTOINCREMENT

event_id

INTEGER

FOREIGN KEY to history_events.event_id.

language

TEXT



name

TEXT



description

TEXT



Linking Tables (The Web of Connections)
Character Links:

character_inventory: (character_id, item_id, quantity)

character_factions: (character_id, faction_id, rank)

Quest Links:

quest_characters: (quest_id, character_id, role_in_quest)

quest_items: (quest_id, item_id, purpose)

quest_locations: (quest_id, location_id, relevance)

quest_sessions: (quest_id, session_id) - Links a quest to the session it was started/completed in.

World Links:

event_characters: (event_id, character_id) - Links a character to a historical event.

faction_relations: (faction_id_1, faction_id_2, status) - e.g., "Allied", "Hostile".