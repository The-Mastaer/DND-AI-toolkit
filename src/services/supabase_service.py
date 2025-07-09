import os
from supabase import create_client, Client
# --- Use a relative import to get config from the parent 'src' package ---
from ..config import SUPABASE_URL, SUPABASE_KEY

# Initialize Supabase client
# This ensures that we don't try to initialize the client if the keys are missing.
url: str = SUPABASE_URL if SUPABASE_URL else ""
key: str = SUPABASE_KEY if SUPABASE_KEY else ""

supabase: Client = None
if url and key:
    supabase = create_client(url, key)
else:
    print("Warning: Supabase URL or Key is not configured. Database functionality will be disabled.")
