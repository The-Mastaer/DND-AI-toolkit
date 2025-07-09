# src/services/supabase_service.py

from supabase import create_client, Client
from ..config import SUPABASE_URL, SUPABASE_KEY


class SupabaseService:
    """
    A service class to interact with the Supabase backend.
    Handles all database operations for the application.
    """

    def __init__(self):
        """
        Initializes the Supabase client.
        """
        try:
            self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            print("Supabase Service initialized successfully.")
        except Exception as e:
            print(f"CRITICAL: Failed to initialize Supabase client: {e}")
            raise

    def get_worlds(self, user_id: str):
        """
        Fetches all worlds associated with a user_id.

        Raises:
            Exception: Propagates API errors to the caller.
        """
        try:
            response = self.client.table('worlds').select('*').eq('user_id', user_id).execute()
            return response.data
        except Exception as e:
            print(f"Error fetching worlds from Supabase: {e}")
            raise e

    def create_world(self, user_id: str, name: str, lore: str):
        """
        Creates a new world in the database.

        Raises:
            Exception: Propagates API errors to the caller.
        """
        try:
            response = self.client.table('worlds').insert({
                'user_id': user_id,
                'name': name,
                'lore': lore
            }).execute()
            return response.data
        except Exception as e:
            print(f"Error creating world in Supabase: {e}")
            raise e

    def delete_world(self, world_id: int):
        """
        Deletes a world by its ID.

        Raises:
            Exception: Propagates API errors to the caller.
        """
        try:
            response = self.client.table('worlds').delete().eq('id', world_id).execute()
            return response.data
        except Exception as e:
            print(f"Error deleting world from Supabase: {e}")
            raise e