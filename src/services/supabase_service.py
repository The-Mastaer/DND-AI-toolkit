# src/services/supabase_service.py

from supabase import create_async_client, AsyncClient
from ..config import SUPABASE_URL, SUPABASE_KEY


class SupabaseService:
    """
    A service class to manage all asynchronous interactions with the Supabase backend,
    including database operations and file storage.
    """

    def __init__(self):
        """
        Initializes the service. The client is initially None and will be created
        asynchronously via the initialize method.
        """
        self.client: AsyncClient | None = None

    async def initialize(self):
        """
        Asynchronously creates and initializes the Supabase client.
        This must be called once when the application starts.
        """
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Supabase URL and Key must be provided in .env file.")

        print("--- Initializing Asynchronous Supabase Client ---")
        self.client = await create_async_client(SUPABASE_URL, SUPABASE_KEY)
        print("--- Supabase Client Initialized ---")

    async def sign_up(self, email: str, password: str):
        """Signs up a new user."""
        if not self.client: raise Exception("Supabase client not initialized.")
        return await self.client.auth.sign_up({"email": email, "password": password})

    async def sign_in_with_password(self, email: str, password: str):
        """Signs in a user with their email and password."""
        if not self.client: raise Exception("Supabase client not initialized.")
        return await self.client.auth.sign_in_with_password({"email": email, "password": password})

    async def set_session(self, access_token: str, refresh_token: str):
        """Restores a user session from tokens."""
        if not self.client: raise Exception("Supabase client not initialized.")
        return await self.client.auth.set_session(access_token, refresh_token)

    async def get_user(self):
        """Asynchronously retrieves the current authenticated user."""
        if not self.client: raise Exception("Supabase client not initialized. Call initialize() first.")
        return await self.client.auth.get_user()

    # --- World Methods ---
    async def get_worlds(self, user_id: str):
        """Asynchronously fetches all worlds for a given user."""
        if not self.client: raise Exception("Supabase client not initialized.")
        try:
            return await self.client.postgrest.from_('worlds').select('id, name, lore').eq('user_id', user_id).execute()
        except Exception as e:
            print(f"--- Supabase error fetching worlds: {e} ---")
            return None

    async def get_world_details(self, world_id: int):
        """Asynchronously fetches details for a single world."""
        if not self.client: raise Exception("Supabase client not initialized.")
        try:
            return await self.client.postgrest.from_('worlds').select('name, lore').eq('id',
                                                                                       world_id).single().execute()
        except Exception as e:
            print(f"--- Supabase error fetching world {world_id}: {e} ---")
            return None

    async def create_world(self, world_record: dict):
        """Asynchronously creates a new world record."""
        if not self.client: raise Exception("Supabase client not initialized.")
        try:
            return await self.client.postgrest.from_('worlds').insert(world_record).execute()
        except Exception as e:
            print(f"--- Supabase error creating world: {e} ---")
            return None

    async def update_world(self, world_id: int, world_record: dict):
        """Asynchronously updates an existing world record."""
        if not self.client: raise Exception("Supabase client not initialized.")
        try:
            return await self.client.postgrest.from_('worlds').update(world_record).eq('id', world_id).execute()
        except Exception as e:
            print(f"--- Supabase error updating world {world_id}: {e} ---")
            return None

    async def delete_world(self, world_id: int):
        """Asynchronously deletes a world record."""
        if not self.client: raise Exception("Supabase client not initialized.")
        try:
            return await self.client.postgrest.from_('worlds').delete().eq('id', world_id).execute()
        except Exception as e:
            print(f"--- Supabase error deleting world {world_id}: {e} ---")
            return None

    # --- Campaign Methods ---
    async def get_campaigns_for_world(self, world_id: int):
        """Asynchronously fetches all campaigns for a given world."""
        if not self.client: raise Exception("Supabase client not initialized.")
        try:
            return await self.client.postgrest.from_('campaigns').select('*').eq('world_id', world_id).execute()
        except Exception as e:
            print(f"--- Supabase error fetching campaigns for world {world_id}: {e} ---")
            return None

    async def get_campaign_details(self, campaign_id: int):
        """Asynchronously fetches details for a single campaign."""
        if not self.client: raise Exception("Supabase client not initialized.")
        try:
            return await self.client.postgrest.from_('campaigns').select('*').eq('id', campaign_id).single().execute()
        except Exception as e:
            print(f"--- Supabase error fetching campaign {campaign_id}: {e} ---")
            return None

    async def create_campaign(self, campaign_data: dict):
        """Asynchronously creates a new campaign."""
        if not self.client: raise Exception("Supabase client not initialized.")
        try:
            return await self.client.postgrest.from_('campaigns').insert(campaign_data).execute()
        except Exception as e:
            print(f"--- Supabase error creating campaign: {e} ---")
            return None

    async def update_campaign(self, campaign_id: int, campaign_data: dict):
        """Asynchronously updates an existing campaign."""
        if not self.client: raise Exception("Supabase client not initialized.")
        try:
            return await self.client.postgrest.from_('campaigns').update(campaign_data).eq('id', campaign_id).execute()
        except Exception as e:
            print(f"--- Supabase error updating campaign {campaign_id}: {e} ---")
            return None

    async def delete_campaign(self, campaign_id: int):
        """Asynchronously deletes a campaign."""
        if not self.client: raise Exception("Supabase client not initialized.")
        try:
            return await self.client.postgrest.from_('campaigns').delete().eq('id', campaign_id).execute()
        except Exception as e:
            print(f"--- Supabase error deleting campaign {campaign_id}: {e} ---")
            return None

    # --- File Storage Methods ---
    async def upload_file(self, bucket_name: str, file_path_in_bucket: str, file_body: bytes, content_type: str):
        """Asynchronously uploads a file to a specified Supabase storage bucket."""
        if not self.client: raise Exception("Supabase client not initialized.")
        try:
            return await self.client.storage.from_(bucket_name).upload(
                path=file_path_in_bucket,
                file=file_body,
                file_options={'upsert': 'true', 'content-type': content_type}
            )
        except Exception as e:
            print(f"--- Supabase Async Upload Error ---: {e}")
            raise e

    async def download_file(self, bucket_name: str, path_in_bucket: str) -> bytes:
        """Asynchronously downloads a file from a Supabase storage bucket."""
        if not self.client: raise Exception("Supabase client not initialized.")
        try:
            return await self.client.storage.from_(bucket_name).download(path=path_in_bucket)
        except Exception as e:
            print(f"--- Supabase Async Download Error ---: {e}")
            raise e

    def get_public_url(self, bucket_name: str, file_path_in_bucket: str) -> str:
        """Gets the public URL for a file in a Supabase storage bucket."""
        if not self.client: raise Exception("Supabase client not initialized.")
        return self.client.storage.from_(bucket_name).get_public_url(file_path_in_bucket)


# A single, shared instance of the service that can be imported elsewhere.
supabase = SupabaseService()