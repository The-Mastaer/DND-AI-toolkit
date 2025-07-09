import asyncio
from supabase import acreate_client, AsyncClient
from typing import Optional, Dict, Any, List

class SupabaseService:
    """
    A service class to manage interactions with the Supabase backend.
    This class now correctly handles the 'lore' column as a JSONB type for
    multi-language support.
    """
    def __init__(self, url: str, key: str):
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
        if not self.client: return []
        try:
            response = await self.client.from_("worlds").select("*").order("created_at", desc=True).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"SupabaseService: Error fetching worlds - {e}")
            return []

    async def add_world(self, name: str, lore: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Adds a new world with its initial lore content.
        The 'lore' column is expected to be JSONB.
        """
        if not self.client: return None
        try:
            # Correctly passing 'lore' as a dictionary for the JSONB column
            world_data = {"name": name, "lore": lore}
            response = await self.client.from_("worlds").insert(world_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"SupabaseService: Error adding world - {e}")
            return None

    async def update_world(self, world_id: int, name: str, lore: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Updates an existing world's name and its JSONB lore data.
        """
        if not self.client: return None
        try:
            # Correctly passing 'lore' as a dictionary for the JSONB column
            update_data = {"name": name, "lore": lore}
            response = await self.client.from_("worlds").update(update_data).eq("id", world_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"SupabaseService: Error updating world - {e}")
            return None

    async def delete_world(self, world_id: int) -> bool:
        """Deletes a world from the database."""
        if not self.client: return False
        try:
            await self.client.from_("worlds").delete().eq("id", world_id).execute()
            return True
        except Exception as e:
            print(f"SupabaseService: Error deleting world - {e}")
            return False