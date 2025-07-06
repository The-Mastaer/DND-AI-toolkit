DM's AI Toolkit: Project Roadmap V5
The Vision: A World-Centric Campaign Ecosystem
The goal is to evolve the DM's AI Toolkit from a set of discrete tools into a single, interconnected ecosystem for world-building and campaign management. The core principle is that a World is a persistent entity, and a Campaign is a specific story that takes place within that world.

Architectural Pivot V3: The Translation Layer
Based on our collaborative design, we are adopting a robust, professional-grade architecture for multi-language support.

The World/Campaign Model:

World: The top-level entity containing foundational, language-agnostic lore and entities.

Campaign: A child of a "World," containing data specific to one group's playthrough and language.

Core Data vs. Translated Text:

Core Tables (e.g., characters): Store universal, mechanical data. An entity exists here only once.

Translation Tables (e.g., character_translations): Store language-specific text, linked to a core entity.

The Unified characters Table:

A single, efficient characters table for all unique individuals, distinguished by an is_player flag. Monsters are kept in a separate monsters table for clarity and data integrity.

Development Roadmap & Phased Implementation
This roadmap is structured to build this new architecture logically and deliver value quickly.

Phase 1: The World-Building Engine
(Goal: Build the foundational tables and managers for creating and defining your worlds based on the new architecture.)

The Core Data Model

Status: Not Started

Goal: Establish the new database schema with the translation layer.

Difficulty: Medium

Sub-tasks:

Refactor services.py to create all new tables as defined in the Database Schema document.

Ensure all DataManager methods are updated to handle the new schema.

Obstacles: This is a significant refactor that will temporarily break the existing UI. It must be done carefully.

World & Campaign Managers

Status: Not Started

Goal: Create the UIs for managing your worlds and the campaigns within them.

Difficulty: Medium

Sub-tasks:

Build a new world_manager_app.py.

Modify campaign_manager_app.py to be launched from the World Manager.

Update main_menu_app.py to select a campaign.

The Unified Character Manager

Status: Not Started

Goal: Create a single, powerful app for managing both NPCs and PCs with the new translation workflow.

Difficulty: High

Sub-tasks:

Rename npc_manager_app.py to character_manager_app.py.

Overhaul the UI to have separate, detailed tabs for PCs (with fields like motivation, dm_notes) vs. NPCs.

Implement the "Translate" workflow, including the AI auto-translate feature.

Implement the "Generate Stat Block" AI feature.

Phase 2: The Storyteller's Toolkit
(Goal: Implement the high-value AI features and content managers that you'll use for session prep.)

Session Manager

Status: Not Started

Goal: An app to log session notes for a specific campaign.

Difficulty: Medium

Sub-tasks:

Create the sessions table.

Build session_manager_app.py.

Implement AI summarization to update the session_history in the campaigns table.

"What If?" Simulator (MVP)

Status: Not Started

Goal: A tool to generate narrative summaries using the data we have so far.

Difficulty: Medium-High

Sub-tasks:

Build what_if_simulator_app.py.

Engineer a prompt that uses the selected campaign's data (and its parent world's lore).

DM's Dashboard (MVP)

Status: Not Started

Goal: A "mission control" screen for your active campaign.

Difficulty: Medium

Sub-tasks:

Build dm_dashboard_app.py.

Design a UI that shows the active campaign's party info and latest session summary.

Phase 3: Populating the World
(Goal: Flesh out the ecosystem with the remaining content managers, all using the translation layer architecture.)

Item, Location, Monster, History, Quest, & Faction Managers

Status: Not Started

Goal: Build the dedicated apps for all the other key elements of a campaign.

Difficulty: Medium to High

Sub-tasks:

For each module, create its core table and _translations table.

Build the corresponding apps, each with a "Translate" feature.

Crucially, create all the necessary linking_tables as defined in the schema to manage the many-to-many relationships.

Phase 4: Full Integration & Advanced Features
(Goal: Enhance the AI features and add powerful utility functions.)

Full-Power AI Simulators

Status: Not Started

Goal: Upgrade the "What If?" Simulator and DM's Dashboard to use data from all the Phase 3 tables.

Difficulty: High

Obstacles: Requires very complex prompt engineering to weave all the disparate data into a coherent context for the AI.

Import/Export Functionality

Status: Not Started

Goal: Allow exporting an entire World and all its associated data to a single file.

Difficulty: Medium

Sub-tasks:

Write a function to query all tables related to a specific world_id.

Structure the data into a logical JSON object.

Write the corresponding import function to parse the JSON and save it back to the database.