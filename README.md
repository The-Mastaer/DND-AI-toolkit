# DM's AI Toolkit

Welcome to the DM's AI Toolkit! This application is designed to be a creative partner for Dungeon Masters, helping you generate and simulate rich, dynamic Non-Player Characters (NPCs) for your campaigns.

This tool uses Google's Gemini AI to power its generation and simulation features. To use the AI capabilities, you'll need to provide your own free API key.

---

## Quick Start: Setting up your API Key

To get the AI features working, you must create a file to hold your secret API key.

1.  **Create the File:** In the same folder where you have the project's files (next to `main.py`), create a new text file and name it exactly `api_key.json`.

2.  **Add the Content:** Open the new file in a text editor and paste the following text inside:

    ```json
    {
        "api_key": "INSERT_YOUR_API_KEY"
    }
    ```

3.  **Get Your Key:** Follow the steps in the next section to get your personal API key from Google.

4.  **Replace the Placeholder:** Replace the text `INSERT_YOUR_API_KEY` with your actual key. Make sure to keep the quotation marks! Save the file.

That's it! Once the `api_key.json` file exists with your key, the application will be fully functional.

---

## How to Get a Free Google AI API Key

Google provides a free tier for its Gemini AI that is more than enough for personal use with this application.

1.  **Go to Google AI Studio:** Open your web browser and navigate to [https://aistudio.google.com/](https://aistudio.google.com/). You may need to sign in with your Google account.

2.  **Get API Key:** Once you're in the AI Studio, look for a button or link that says **"Get API key"**. It's usually near the top-left of the page.

3.  **Create API Key:** In the new screen that opens, click the button that says **"Create API key in new project"**.

4.  **Copy Your Key:** A pop-up will appear with your new key. It will be a long string of letters and numbers. Click the copy icon next to it. **This is your API key.**

5.  **Paste it into `api_key.json`:** Go back to your `api_key.json` file and paste this new key in place of `INSERT_YOUR_API_KEY`. The final result should look something like this (but with your own unique key):

    ```json
    {
        "api_key": "AIzaSy...Your...Long...And...Secret...Key...12345"
    }
    ```

6.  **Save the file and run the toolkit!**

---

## Enjoy the Adventure!

Thank you for being an awesome DM! I hope this tool helps you weave incredible stories and bring your world to life.

Happy adventuring!
