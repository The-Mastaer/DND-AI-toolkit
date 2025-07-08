import os
from dotenv import load_dotenv

def load_env():
    """
    Loads environment variables from a .env file located in the project root.

    This function traverses up the directory tree from the current file's location
    to find the project root (identified by the presence of a .git directory or
    the .env file itself) and then loads the .env file.
    """
    # Start from the directory of the current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = current_dir

    # Traverse up to find the project root (e.g., where .git or .env is)
    while not os.path.exists(os.path.join(project_root, '.env')) and \
          not os.path.exists(os.path.join(project_root, '.git')) and \
          os.path.dirname(project_root) != project_root:
        project_root = os.path.dirname(project_root)

    # Construct the path to the .env file
    dotenv_path = os.path.join(project_root, '.env')

    # Load the .env file if it exists
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path)
    else:
        print("Warning: .env file not found. Please create one in the project root.")

# Load environment variables at module import time
load_env()

# --- Retrieve credentials from environment variables ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def validate_keys():
    """
    Validates that all necessary API keys and URLs are present.
    Returns True if all keys are present, False otherwise.
    """
    if not all([SUPABASE_URL, SUPABASE_ANON_KEY, GEMINI_API_KEY]):
        print("CRITICAL ERROR: One or more environment variables are missing.")
        print("Please check your .env file in the project root.")
        return False
    return True