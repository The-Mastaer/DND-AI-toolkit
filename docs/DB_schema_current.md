# DM's AI Toolkit: Current Database Schema

This document reflects the current, live database schema as implemented in `services.py`. It should be used to track our progress against the `Database_schema_plan.md`.

---

### Meta Table

| Column Name | Type    | Notes                               |
|:------------|:--------|:------------------------------------|
| `key`       | TEXT    | PRIMARY KEY, e.g., 'schema_version' |
| `value`     | INTEGER | The value associated with the key.  |

---

### Tier 1: Core & Campaign Tables

#### `worlds`

| Column Name      | Type    | Notes                                  |
|:-----------------|:--------|:---------------------------------------|
| `world_id`       | INTEGER | PRIMARY KEY, AUTOINCREMENT           |
| `canonical_name` | TEXT    | UNIQUE, NOT NULL. For internal use.    |

#### `world_translations`

| Column Name    | Type    | Notes                                                      |
|:---------------|:--------|:-----------------------------------------------------------|
| `translation_id` | INTEGER | PRIMARY KEY, AUTOINCREMENT                               |
| `world_id`     | INTEGER | FOREIGN KEY to `worlds.world_id`, ON DELETE CASCADE      |
| `language`     | TEXT    | NOT NULL, e.g., 'en', 'cs'.                                |
| `world_name`   | TEXT    | NOT NULL. The display name of the world.                   |
| `world_lore`   | TEXT    | The lore for this specific language.                       |
| **Constraint** |         | `UNIQUE(world_id, language)`                               |

#### `campaigns`

| Column Name       | Type    | Notes                                                      |
|:------------------|:--------|:-----------------------------------------------------------|
| `campaign_id`     | INTEGER | PRIMARY KEY, AUTOINCREMENT                               |
| `world_id`        | INTEGER | FOREIGN KEY to `worlds.world_id`, ON DELETE CASCADE      |
| `campaign_name`   | TEXT    | NOT NULL                                                   |
| `language`        | TEXT    | NOT NULL, e.g., 'en', 'cs'                                 |
| `party_info`      | TEXT    | Description of the player party for this campaign.         |
| `session_history` | TEXT    | AI-generated or manual summary of recent events.           |

---

### Tier 2: Entity Tables (Core + Translation)

#### `characters` (Core)

| Column Name    | Type    | Notes                                                      |
|:---------------|:--------|:-----------------------------------------------------------|
| `character_id` | INTEGER | PRIMARY KEY, AUTOINCREMENT                               |
| `world_id`     | INTEGER | FOREIGN KEY to `worlds.world_id`, ON DELETE CASCADE      |
| `is_player`    | BOOLEAN | NOT NULL, `1` for Player Character, `0` for NPC.         |
| `level`        | INTEGER |                                                            |
| `hp`           | INTEGER | Hit Points.                                                |
| `ac`           | INTEGER | Armor Class.                                               |
| `strength`     | INTEGER |                                                            |
| `dexterity`    | INTEGER |                                                            |
| `constitution` | INTEGER |                                                            |
| `intelligence` | INTEGER |                                                            |
| `wisdom`       | INTEGER |                                                            |
| `charisma`     | INTEGER |                                                            |
| `skills`       | TEXT    | e.g., "Perception, Stealth, Persuasion".                   |
| `image_data`   | BLOB    | The character portrait.                                    |

#### `character_translations`

| Column Name        | Type    | Notes                                                      |
|:-------------------|:--------|:-----------------------------------------------------------|
| `translation_id`   | INTEGER | PRIMARY KEY, AUTOINCREMENT                               |
| `character_id`     | INTEGER | FOREIGN KEY to `characters.character_id`, ON DELETE CASCADE|
| `language`         | TEXT    | NOT NULL, e.g., 'en', 'cs'.                                |
| `name`             | TEXT    |                                                            |
| `race_class`       | TEXT    |                                                            |
| `appearance`       | TEXT    |                                                            |
| `personality`      | TEXT    |                                                            |
| `backstory`        | TEXT    |                                                            |
| `plot_hooks`       | TEXT    |                                                            |
| `roleplaying_tips` | TEXT    |                                                            |
| `motivation`       | TEXT    | Primarily for PCs.                                         |
| `objectives`       | TEXT    | Primarily for PCs.                                         |
| `dm_notes`         | TEXT    | Secret notes for the DM.                                   |
| **Constraint** |         | `UNIQUE(character_id, language)`                           |

---

### Database Views

Views are virtual tables based on the result-set of an SQL statement. They simplify complex queries.

#### `v_full_world_data`
Joins `worlds` and `world_translations` to provide complete world data in a single query.

#### `v_full_character_data`
Joins `characters` and `character_translations` to provide complete character data in a single query.