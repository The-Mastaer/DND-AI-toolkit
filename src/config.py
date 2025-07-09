# src/config.py

import os
from dotenv import load_dotenv

# --- Environment Variable Loading ---
# This function call looks for a file named .env in the project's root directory
# and loads all the key-value pairs defined in it as environment variables.
# This is the standard and secure way to handle secrets in a Python application.
load_dotenv()

# --- API Key and URL Retrieval ---
# We use os.getenv() to retrieve the loaded environment variables.
# If a variable is not found, os.getenv() will return None. This prevents the
# app from crashing but will likely cause errors in the services that depend on these keys.

# Your secret key for the Google Gemini API.
# Found in your Google AI Studio dashboard.
# Example in .env file: GEMINI_API_KEY="AIzaSy...your...key..."
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# The unique URL for your Supabase project.
# Found in your Supabase project settings under 'API'.
# Example in .env file: SUPABASE_URL="https://your-project-ref.supabase.co"
SUPABASE_URL = os.getenv("SUPABASE_URL")

# The 'anon' key for your Supabase project. This key is safe to use in a client-side
# application like this one, as long as you have Row Level Security (RLS) enabled.
# Found in your Supabase project settings under 'API'.
# Example in .env file: SUPABASE_KEY="ey...your...anon...key..."
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


# --- Validation (Optional but Recommended) ---
# It's good practice to check if the essential keys were loaded correctly at startup.
# This provides a clear error message if the .env file is missing or misconfigured.
if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY not found in .env file.")
if not SUPABASE_URL:
    print("WARNING: SUPABASE_URL not found in .env file.")
if not SUPABASE_KEY:
    print("WARNING: SUPABASE_KEY not found in .env file.")