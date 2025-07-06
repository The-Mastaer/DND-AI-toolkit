# DM's AI Toolkit: Project Roadmap V5

## The Vision: A World-Centric Campaign Ecosystem

The goal is to evolve the DM's AI Toolkit from a set of discrete tools into a single, interconnected ecosystem for world-building and campaign management. The core principle is that a **World** is a persistent entity, and a **Campaign** is a specific story that takes place within that world.

### Architectural Pivot V3: The Translation Layer

Based on our collaborative design, we are adopting a robust, professional-grade architecture for multi-language support.

1.  **The World/Campaign Model:**
    * **World:** The top-level entity containing foundational, language-agnostic lore and entities.
    * **Campaign:** A child of a "World," containing data specific to one group's playthrough and language.

2.  **Core Data vs. Translated Text:**
    * **Core Tables (e.g., `characters`):** Store universal, mechanical data. An entity exists here only *once*.
    * **Translation Tables (e.g., `character_translations`):** Store language-specific text, linked to a core entity.

3.  **The Unified `characters` Table:**
    * A single, efficient `characters` table for all unique individuals, distinguished by an `is_player` flag. Monsters are kept in a separate `monsters` table for clarity and data integrity.

---

## Development Roadmap & Phased Implementation

This roadmap is structured to build this new architecture logically and deliver value quickly.

### Phase 1: The World-Building Engine

*(Goal: Build the foundational tables and managers for creating and defining your worlds based on the new architecture.)*

1.  **The Core Data Model**
    * **Status:** Not Started
    * **Goal:** Establish the new database schema with the translation layer.
    * **Difficulty:** Medium
    * **Sub-tasks:**
        1.  Refactor `services.py` to create all new tables as defined in the Database Schema document.
        2.  Ensure all `DataManager` methods are updated to handle the new schema.
    * **Obstacles:** This is a significant refactor that will temporarily break the existing UI. It must be done carefully.

2.  **World & Campaign Managers**
    * **Status:** Not Started
    * **Goal:** Create the UIs for managing your worlds and the campaigns within them.
    * **Difficulty:** Medium
    * **Sub-tasks:**
        1.  Build a new `world_manager_app.py`.
        2.  Modify `campaign_manager_app.py` to be launched from the World Manager.
        3.  Update `main_menu_app.py` to select a `campaign`.

3.  **The Unified Character Manager**
    * **Status:** Not Started
    * **Goal:** Create a single, powerful app for managing both NPCs and PCs with the new translation workflow.
    * **Difficulty:** High
    * **Sub-tasks:**
        1.  Rename `npc_manager_app.py` to `character_manager_app.py`.
        2.  Overhaul the UI to have separate, detailed tabs for PCs (with fields like `motivation`, `dm_notes`) vs. NPCs.
        3.  Implement the **"Translate"** workflow, including the AI auto-translate feature.
        4.  Implement the **"Generate Stat Block"** AI feature.

### Phase 2: The Storyteller's Toolkit

*(Goal: Implement the high-value AI features and content managers that you'll use for session prep.)*

4.  **Session Manager**
    * **Status:** Not Started
    * **Goal:** An app to log session notes for a specific campaign.
    * **Difficulty:** Medium
    * **Sub-tasks:**
        1.  Create the `sessions` table.
        2.  Build `session_manager_app.py`.
        3.  Implement AI summarization to update the `session_history` in the `campaigns` table.

5.  **"What If?" Simulator (MVP)**
    * **Status:** Not Started
    * **Goal:** A tool to generate narrative summaries using the data we have so far.
    * **Difficulty:** Medium-High
    * **Sub-tasks:**
        1.  Build `what_if_simulator_app.py`.
        2.  Engineer a prompt that uses the selected campaign's data (and its parent world's lore).

6.  **DM's Dashboard (MVP)**
    * **Status:** Not Started
    * **Goal:** A "mission control" screen for your active campaign.
    * **Difficulty:** Medium
    * **Sub-tasks:**
        1.  Build `dm_dashboard_app.py`.
        2.  Design a UI that shows the active campaign's party info and latest session summary.

### Phase 3: Populating the World

*(Goal: Flesh out the ecosystem with the remaining content managers, all using the translation layer architecture.)*

7.  **Item, Location, Monster, History, Quest, & Faction Managers**
    * **Status:** Not Started
    * **Goal:** Build the dedicated apps for all the other key elements of a campaign.
    * **Difficulty:** Medium to High
    * **Sub-tasks:**
        1.  For each module, create its `core` table and `_translations` table.
        2.  Build the corresponding apps, each with a "Translate" feature.
        3.  **Crucially, create all the necessary `linking_tables`** as defined in the schema to manage the many-to-many relationships.

### Phase 4: Full Integration & Advanced Features

*(Goal: Enhance the AI features and add powerful utility functions.)*

8.  **Full-Power AI Simulators**
    * **Status:** Not Started
    * **Goal:** Upgrade the "What If?" Simulator and DM's Dashboard to use data from all the Phase 3 tables.
    * **Difficulty:** High
    * **Obstacles:** Requires very complex prompt engineering to weave all the disparate data into a coherent context for the AI.

9.  **Import/Export Functionality**
    * **Status:** Not Started
    * **Goal:** Allow exporting an entire *World* and all its associated data to a single file.
    * **Difficulty:** Medium
    * **Sub-tasks:**
        1.  Write a function to query all tables related to a specific `world_id`.
        2.  Structure the data into a logical JSON object.
        3.  Write the corresponding import function to parse the JSON and save it back to the database.