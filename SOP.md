# DM's AI Toolkit: Standard Operating Procedure & Getting Started

Welcome to your new AI Co-Pilot for world-building and campaign management! This guide will walk you through setting up the toolkit and the core workflow for bringing your stories to life.

---

## Part 1: One-Time Setup (Required)

Before you can unleash your creativity, you need to give the AI its brain and its lawbook.

### 1. Configure Your API Key

The AI features are powered by Google's Gemini models. You'll need a free API key to use them.

1.  **Create the File:** In the same folder as `Main.py`, create a new file named exactly `api_key.json`.
2.  **Add Content:** Paste the following into the file:
    ```json
    {
        "api_key": "INSERT_YOUR_API_KEY"
    }
    ```
3.  **Get Your Key:** Go to [Google AI Studio](https://aistudio.google.com/) and create a new API key.
4.  **Paste Your Key:** Replace `INSERT_YOUR_API_KEY` with the key you just copied. Keep the quotation marks!

### 2. Set Up the "Rules Lawyer"

The "Rules Lawyer" AI needs the official D&D rulebook to answer your questions accurately.

1.  **Download the SRD:** You need the official **System Reference Document (SRD)**. A quick search for "D&D 5.1 SRD PDF" will lead you to the free version from Wizards of the Coast. Download it to your computer.
2.  **Set the Path in the App:**
    * Launch the toolkit and click the **Settings** button.
    * Go to the **AI Settings** tab.
    * Next to **SRD PDF Path**, click **Browse...** and select the SRD PDF file you just downloaded.
    * Click **Save & Close**.

With this setup complete, your AI is ready for action!

---

## Part 2: The Creative Workflow

The toolkit is built on a simple but powerful idea: **Worlds** are the settings, and **Campaigns** are the stories that happen within them.

### Step 1: Create Your World

First, you need a place for your adventures to happen.

1.  **Open the World Manager:** From the main menu, click **Manage Worlds**.
2.  **Start a New World:** Click the **+ New** button. The panel on the right will clear, ready for your input.
3.  **Define Your World:**
    * **World Name:** Give your setting a name (e.g., "Aethelgard," "The Shattered Isles").
    * **World Lore:** This is the most important field! This is your private wiki. Write down the core truths of your setting: creation myths, major gods, key kingdoms, how magic works, etc. The AI will use this as its ultimate source of truth.
4.  **Save Your World:** Click **Save World**. It will now appear in the list on the left.

### Step 2: Create Your Campaign

Now that you have a world, you can create a story within it.

1.  **Select Your World:** In the World Manager, make sure your desired world is selected.
2.  **Open the Campaign Manager:** Click the **Manage Campaigns** button.
3.  **Start a New Campaign:** Just like with worlds, click **+ New**.
4.  **Define Your Campaign:**
    * **Campaign Name:** Give your adventure a title (e.g., "The Crimson Throne," "Echoes of the Abyss").
    * **Party Info:** Describe the player characters. Who are they? What are their goals? The AI will use this to make its responses relevant to your players.
    * **Session History:** Keep a running summary of what has happened in recent game sessions. This gives the AI crucial context about the current state of the story.
5.  **Save Your Campaign:** Click **Save Campaign**.

### Step 3: Use Your AI Co-Pilot

Return to the main menu. You'll see the dashboard is now alive with your campaign info. The chat tabs are your primary tools.

* **Lore Master:** This is your creative partner. It has a **continuous memory** of your conversation. You can ask it to brainstorm ideas, flesh out details, or summarize information based on the World Lore, Party Info, and Session History you provided. Treat it like an ongoing conversation.

* **Rules Lawyer:** This is your rulebook expert. It has **no memory** of past questions. Each query is a fresh, one-time lookup in the SRD PDF. For best results, ask clear, self-contained questions like: *"What are the rules for grappling?"* or *"How does the spell Fireball work?"*

* **NPC Actor:** (Coming Soon!) This will be where you can have in-character conversations with the NPCs you create.

---

## Part 3: Managing Settings

The **Settings** window is your control panel.

* **Active Campaign:** This is where you select which World and Campaign are currently active. The AI Co-Pilot will only use the lore from the active selection.
* **AI Settings:** Here you can change the AI models and, most importantly, view and **override the default prompts**. If you ever feel a prompt is missing (like the Rules Lawyer one), you can delete your `settings.json` file, and the app will generate a fresh one with all the defaults when it next starts.
* **Appearance:** Change the look and feel of the app.

Congratulations, DM! You're now ready to use the toolkit to its full potential. Happy world-building!
