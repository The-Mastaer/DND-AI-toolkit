import asyncio
from supabase import acreate_client, AsyncClient
from typing import Optional, Dict, Any, List

class SupabaseService:
    """
    A service class to manage interactions with the Supabase backend.

    This class abstracts all Supabase-related operations, such as authentication
    and database queries. It uses the asynchronous client from the `supabase-py`
    library to ensure non-blocking I/O operations.
    """
    def __init__(self, url: str, key: str):
        """
        Initializes the SupabaseService.

        Args:
            url (str): The URL of the Supabase project.
            key (str): The anon key for the Supabase project.
        """
        self.url = url
        self.key = key
        self.client: Optional[AsyncClient] = None
        print("SupabaseService: Initialized.")

    async def initialize_client(self):
        """Asynchronously creates and initializes the Supabase client."""
        if not self.client:
            try:
                self.client: AsyncClient = await acreate_client(self.url, self.key)
                print("SupabaseService: Client created successfully.")
            except Exception as e:
                print(f"SupabaseService: Error creating client - {e}")
                self.client = None

    async def get_worlds(self) -> List[Dict[str, Any]]:
        """Asynchronously fetches all worlds from the database."""
        if not self.client:
            print("SupabaseService: Client not initialized. Cannot fetch worlds.")
            return []
        try:
            response = await self.client.from_("worlds").select("*").order("created_at", desc=True).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"SupabaseService: Error fetching worlds - {e}")
            return []

    async def add_world(self, name: str, description: str) -> Optional[Dict[str, Any]]:
        """
        Adds a new world to the database.

        Args:
            name (str): The name of the new world.
            description (str): The description for the new world.
            # TODO: Add user_id when authentication is implemented.

        Returns:
            The newly created world data as a dictionary, or None if it fails.
        """
        if not self.client:
            print("SupabaseService: Client not initialized. Cannot add world.")
            return None
        try:
            world_data = {"name": name, "description": description}
            response = await self.client.from_("worlds").insert(world_data).execute()
            if response.data:
                print(f"SupabaseService: World '{name}' added successfully.")
                return response.data[0]
            return None
        except Exception as e:
            print(f"SupabaseService: Error adding world - {e}")
            return None

    async def delete_world(self, world_id: int) -> bool:
        """
        Deletes a world from the database.

        Args:
            world_id (int): The ID of the world to delete.

        Returns:
            True if deletion was successful, False otherwise.
        """
        if not self.client:
            print("SupabaseService: Client not initialized. Cannot delete world.")
            return False
        try:
            await self.client.from_("worlds").delete().eq("id", world_id).execute()
            print(f"SupabaseService: Deleted world with ID: {world_id}")
            return True
        except Exception as e:
            print(f"SupabaseService: Error deleting world - {e}")
            return False