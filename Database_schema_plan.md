# DM's AI Toolkit: Database Schema Plan

This document outlines the complete database structure for the DM's AI Toolkit. The architecture is designed to be scalable, relational, and support the "World-centric" and "Translation Layer" models.

---

### Meta Table

| Column Name | Type    | Notes                               |
|:------------|:--------|:------------------------------------|
| `key`       | TEXT    | PRIMARY KEY, e.g., 'schema_version' |
| `value`     | INTEGER | The value associated with the key.  |

---

### Tier 1: Core & Campaign Tables

#### `worlds`

| Column Name      | Type    | Notes                               |
|:-----------------|:--------|:------------------------------------|
| `world_id`       | INTEGER | PRIMARY KEY, AUTOINCREMENT        |
| `canonical_name` | TEXT    | UNIQUE, NOT NULL. For internal use. |

#### `world_translations`

| Column Name      | Type    | Notes                                  |
|:-----------------|:--------|:---------------------------------------|
| `translation_id` | INTEGER | PRIMARY KEY, AUTOINCREMENT             |
| `world_id`       | INTEGER | FOREIGN KEY to `worlds.world_id`     |
| `language`       | TEXT    | NOT NULL, e.g., 'en', 'cs'.            |
| `world_name`     | TEXT    | NOT NULL. The display name of the world. |
| `world_lore`     | TEXT    | The lore for this specific language.   |

#### `campaigns`

| Column Name       | Type    | Notes                                      |
|:------------------|:--------|:-------------------------------------------|
| `campaign_id`     | INTEGER | PRIMARY KEY, AUTOINCREMENT               |
| `world_id`        | INTEGER | FOREIGN KEY to `worlds.world_id`         |
| `campaign_name`   | TEXT    | NOT NULL                                   |
| `language`        | TEXT    | NOT NULL. Must match a world translation.  |
| `party_info`      | TEXT    | Description of the player party.           |
| `session_history` | TEXT    | AI-generated or manual summary of events.  |

---

### Tier 2: Entity Tables (Core + Translation)

#### `characters` (Core)

| Column Name    | Type    | Notes                                  |
|:---------------|:--------|:---------------------------------------|
| `character_id` | INTEGER | PRIMARY KEY, AUTOINCREMENT           |
| `world_id`     | INTEGER | FOREIGN KEY to `worlds.world_id`     |
| `is_player`    | BOOLEAN | `1` for Player, `0` for NPC.           |
| `level`        | INTEGER |                                        |
| `hp`           | INTEGER | Hit Points.                            |
| `ac`           | INTEGER | Armor Class.                           |
| `strength`     | INTEGER |                                        |
| `dexterity`    | INTEGER |                                        |
| `constitution` | INTEGER |                                        |
| `intelligence` | INTEGER |                                        |
| `wisdom`       | INTEGER |                                        |
| `charisma`     | INTEGER |                                        |
| `skills`       | TEXT    | Prominent skills, e.g., "Perception".  |
| `image_data`   | BLOB    | The character portrait.                |

#### `character_translations`

| Column Name        | Type    | Notes                                  |
|:-------------------|:--------|:---------------------------------------|
| `translation_id`   | INTEGER | PRIMARY KEY, AUTOINCREMENT           |
| `character_id`     | INTEGER | FOREIGN KEY to `characters.character_id` |
| `language`         | TEXT    | e.g., 'en', 'cs'.                      |
| `name`             | TEXT    |                                        |
| `race_class`       | TEXT    |                                        |
| `appearance`       | TEXT    |                                        |
| `personality`      | TEXT    |                                        |
| `backstory`        | TEXT    |                                        |
| `plot_hooks`       | TEXT    |                                        |
| `roleplaying_tips` | TEXT    |                                        |
| `motivation`       | TEXT    | (Primarily for PCs)                    |
| `objectives`       | TEXT    | (Primarily for PCs)                    |
| `dm_notes`         | TEXT    | (Secret notes for the DM)              |

*(This Core + Translation pattern will be repeated for `locations`, `items`, `quests`, `factions`, `monsters`, etc.)*

---

### Tier 3: Narrative & Linking Tables

#### `sessions`

| Column Name      | Type    | Notes                                  |
|:-----------------|:--------|:---------------------------------------|
| `session_id`     | INTEGER | PRIMARY KEY, AUTOINCREMENT           |
| `campaign_id`    | INTEGER | FOREIGN KEY to `campaigns.campaign_id` |
| `session_number` | INTEGER |                                        |
| `session_date`   | TEXT    |                                        |
| `session_notes`  | TEXT    | Raw, detailed notes from the session.  |

#### `quests` (Core)

| Column Name     | Type    | Notes                                  |
|:----------------|:--------|:---------------------------------------|
| `quest_id`      | INTEGER | PRIMARY KEY, AUTOINCREMENT           |
| `campaign_id`   | INTEGER | FOREIGN KEY to `campaigns.campaign_id` |
| `is_main_quest` | BOOLEAN |                                        |
| `status`        | TEXT    | "Not Started", "In Progress", etc.     |

#### Linking Tables (The Web of Connections)

* `character_inventory`: (`character_id`, `item_id`, `quantity`)
* `character_factions`: (`character_id`, `faction_id`, `rank`)
* `quest_characters`: (`quest_id`, `character_id`, `role_in_quest`)
* `event_characters`: (`event_id`, `character_id`)
* `faction_relations`: (`faction_id_1`, `faction_id_2`, `status`)