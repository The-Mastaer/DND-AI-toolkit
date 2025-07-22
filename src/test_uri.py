import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables from your .env file
load_dotenv()

# --- Configuration ---
# Make sure your .env file has these two variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_SRD_FILE_NAME = os.getenv("GEMINI_SRD_FILE_NAME") # Should be "files/0ukyk160vb06"
MODEL_NAME = "gemini-2.5-flash" # Or your preferred model

# --- Verification ---
if not GEMINI_API_KEY or not GEMINI_SRD_FILE_NAME:
    print("Error: Please make sure GEMINI_API_KEY and GEMINI_SRD_FILE_NAME are in your .env file.")
    exit()

print(f"--- Testing with API Key: ...{GEMINI_API_KEY[-4:]}")
print(f"--- Testing with File URI: {GEMINI_SRD_FILE_NAME}")

# --- Direct API Call ---
url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={GEMINI_API_KEY}"

headers = {
    'Content-Type': 'application/json'
}

# This mimics the payload our Supabase function sends
payload = {
    "contents": [
        {
            "role": "user",
            "parts": [
                {
                    "fileData": {
                        "mime_type": "application/pdf",
                        "file_uri": GEMINI_SRD_FILE_NAME
                    }
                },
                {
                    "text": "Briefly summarize the document's purpose."
                }
            ]
        }
    ]
}

try:
    print("--- Sending direct request to Gemini API... ---")
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status() # Raise an error for bad responses

    print("\n--- SUCCESS! ---")
    print("The API key and file URI are working correctly together.")
    print("Response:")
    print(json.dumps(response.json(), indent=2))

except requests.exceptions.HTTPError as e:
    print("\n--- FAILED! ---")
    print(f"Status Code: {e.response.status_code}")
    print("Response Body:")
    print(e.response.text)
    print("\nThis indicates a problem with the file URI or API key permissions itself.")