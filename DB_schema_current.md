DM's AI Toolkit: Current Database Schema
This document reflects the current, live database schema as implemented in services.py. It should be used to track our progress against the Database_schema_plan.md.

Meta Table
This table is used by the application to track schema changes and perform non-destructive migrations.

db_meta
Column Name

Type

Notes

key

TEXT

PRIMARY KEY, e.g., 'schema_version'

value

INTEGER

The value associated with the key.

Tier 1: Core & Campaign Tables
These tables define the highest level of organization.

worlds
Column Name

Type

Notes

world_id

INTEGER

PRIMARY KEY, AUTOINCREMENT

canonical_name

TEXT

UNIQUE, NOT NULL. For internal use.

world_translations
Column Name

Type

Notes

translation_id

INTEGER

PRIMARY KEY, AUTOINCREMENT

world_id

INTEGER

FOREIGN KEY to worlds.world_id, ON DELETE CASCADE

language

TEXT

NOT NULL, e.g., 'en', 'cs'.

world_name

TEXT

NOT NULL. The display name of the world.

world_lore

TEXT

The lore for this specific language.

Constraint



UNIQUE(world_id, language)

campaigns
Column Name

Type

Notes

campaign_id

INTEGER

PRIMARY KEY, AUTOINCREMENT

world_id

INTEGER

FOREIGN KEY to worlds.world_id, ON DELETE CASCADE

campaign_name

TEXT

NOT NULL

language

TEXT

NOT NULL, e.g., 'en', 'cs'

party_info

TEXT

Description of the player party for this campaign.

session_history

TEXT

AI-generated or manual summary of recent events.

Tier 2: Entity Tables (Core + Translation)
This pattern is used for all major entities in the world.

characters (Core)
Column Name

Type

Notes

character_id

INTEGER

PRIMARY KEY, AUTOINCREMENT

world_id

INTEGER

FOREIGN KEY to worlds.world_id, ON DELETE CASCADE

is_player

BOOLEAN

NOT NULL, 1 for Player Character, 0 for NPC.

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

e.g., "Perception, Stealth, Persuasion".

image_data

BLOB

The character portrait.

character_translations
Column Name

Type

Notes

translation_id

INTEGER

PRIMARY KEY, AUTOINCREMENT

character_id

INTEGER

FOREIGN KEY to characters.character_id, ON DELETE CASCADE

language

TEXT

NOT NULL, e.g., 'en', 'cs'.

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

Primarily for PCs.

objectives

TEXT

Primarily for PCs.

dm_notes

TEXT

Secret notes for the DM.

Constraint



UNIQUE(character_id, language)

