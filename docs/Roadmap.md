# DM's AI Toolkit: Project Roadmap V7

## The Vision: Your Intelligent Campaign Co-Pilot

The goal is to evolve the DM's AI Toolkit into an intelligent, all-in-one workspace for world-building and campaign management. We are creating a "Campaign Co-Pilot" that understands your world and helps you bring it to life through a seamless, conversational interface.

### Architectural Principles

1.  **World-Centric Design:** The foundation of the app. A **World** is a persistent, language-agnostic setting. A **Campaign** is a specific, language-dependent story that takes place within that world.
2.  **Core + Translation Architecture:** For maximum flexibility, all key entities (Worlds, Characters, etc.) separate their universal data (`Core`) from their descriptive text (`Translation`), enabling robust multi-language support.
3.  **Settings-Driven & User-Customizable:** The application's core behavior, from the active campaign to the AI models and prompts used, is controlled by a user-editable `settings.json` file, not hardcoded.

---

## Development Roadmap & Phased Implementation

### Phase 1: The World-Building Engine (Complete)

*(Goal: To build the robust, foundational data structure for the entire application.)*

1.  **The Core Data Model:** **(Done)**
2.  **World & Campaign Managers:** **(Done)**
3.  **The Settings-Driven Architecture:** **(Done)**

### Phase 2: The Intelligent Workspace (In Progress)

*(Goal: To implement the core AI chat functionality and bring the Campaign Dashboard to life.)*

4.  **The AI Assistant Dashboard:** **(Done)**
5.  **The "Lore Master" Persona:** **(Done)**
6.  **The "Rules Lawyer" Persona:** **(Done)**
7.  **The "NPC Actor" Persona:**
    * **Status:** Not Started
    * **Goal:** Allow the user to select an NPC from the active campaign and have a direct, in-character conversation, with the AI adopting the NPC's personality and knowledge.

### Phase 3: The Unified Character Manager

*(Goal: To create a single, powerful hub for managing all the people in your world, from heroic PCs to lowly goblins.)*

8.  **The Unified Character Manager App:**
    * **Status:** Not Started
    * **Difficulty:** High
    * **Sub-tasks:**
        1.  Create `character_manager_app.py`.
        2.  Design and build a UI that can manage both Player Characters and Non-Player Characters seamlessly.
        3.  Implement full CRUD (Create, Read, Update, Delete) functionality for characters, leveraging our "Core + Translation" database schema.
        4.  Integrate the AI generation features (full NPC generation, portrait generation) directly into the manager's workflow.

### Phase 4: Populating the World

*(Goal: To build out the ecosystem with dedicated managers for every key element of a campaign.)*

9.  **Content Managers (Items, Locations, Quests, Factions):**
    * **Status:** Not Started
    * **Difficulty:** Medium to High
    * **Sub-tasks:**
        1.  For each module, define and create its `core` and `_translations` tables in the database schema.
        2.  Build the corresponding manager apps (e.g., `item_manager.py`, `location_manager.py`).
        3.  Implement the necessary `linking_tables` in the database to manage the many-to-many relationships (e.g., which characters are in which faction, what items are in a location).

### Phase 5: Advanced Integration & Utility

*(Goal: To unlock the full potential of our interconnected data with advanced AI features and quality-of-life improvements.)*

10. **Full-Power AI Simulators:**
    * **Status:** Not Started
    * **Difficulty:** High
    * **Goal:** Enhance the AI personas to be aware of and use data from all the Phase 4 managers (Items, Locations, Quests, etc.), allowing for deeply context-aware responses.
11. **Import/Export Functionality:**
    * **Status:** Not Started
    * **Difficulty:** Medium
    * **Goal:** Allow users to export/import an entire **World** and all its associated data to a single, shareable file. This is the key to community content sharing.