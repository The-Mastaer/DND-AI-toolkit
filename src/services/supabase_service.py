# src/services/supabase_service.py

import os
from supabase import create_client, Client, AClient, acreate_client
from config import SUPABASE_URL, SUPABASE_KEY
from gotrue.types import User, Session
import asyncio


class SupabaseService:
    """
    A service class to manage all interactions with the Supabase backend.
    This class is a singleton, meaning only one instance of it will be created.
    """
    _instance = None
    client: AClient = None
    user: User = None
    session: Session = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseService, cls).__new__(cls)
        return cls._instance

    async def initialize(self):
        """
        Initializes the asynchronous Supabase client.
        This should be called once when the application starts.
        """
        if self.client is None:
            if not SUPABASE_URL or not SUPABASE_KEY:
                raise ValueError("Supabase URL and Key must be set in environment variables.")
            print("--- Initializing Supabase client ---")
            self.client = await acreate_client(SUPABASE_URL, SUPABASE_KEY)

    async def set_session(self, access_token: str, refresh_token: str):
        """
        Sets the user session in the Supabase client.
        """
        if self.client:
            await self.client.auth.set_session(access_token, refresh_token)
        else:
            raise Exception("Supabase client not initialized.")

    async def get_user(self) -> User | None:
        """
        Retrieves the current authenticated user.
        """
        if self.client:
            response = await self.client.auth.get_user()
            if response and response.user:
                self.user = response.user
                return self.user
        self.user = None
        return None

    async def get_all_worlds(self):
        """
        Fetches all worlds for the currently authenticated user.
        """
        if not self.client:
            raise Exception("Supabase client not initialized.")

        response = await self.client.from_('worlds').select("*").execute()
        return response

    async def get_world_details(self, world_id: int):
        """
        Fetches details for a specific world.
        """
        if not self.client:
            raise Exception("Supabase client not initialized.")

        response = await self.client.from_('worlds').select("*").eq('id', world_id).single().execute()
        return response

    async def update_world(self, world_id: int, updates: dict):
        """
        Updates a specific world's data.
        """
        if not self.client:
            raise Exception("Supabase client not initialized.")

        response = await self.client.from_('worlds').update(updates).eq('id', world_id).execute()
        return response

    async def get_campaigns_for_world(self, world_id: int):
        """
        Fetches all campaigns associated with a given world ID.
        """
        if not self.client:
            raise Exception("Supabase client not initialized.")

        response = await self.client.from_('campaigns').select("*").eq('world_id', world_id).execute()
        return response

    async def get_campaign_details(self, campaign_id: int):
        """
        Fetches details for a specific campaign.
        """
        if not self.client:
            raise Exception("Supabase client not initialized.")

        response = await self.client.from_('campaigns').select("*").eq('id', campaign_id).single().execute()
        return response

    async def get_world_and_campaign_details(self, campaign_id: int) -> dict:
        """
        Fetches world and campaign details needed for generating a portrait prompt.
        This is more efficient than separate calls from the view.
        """
        if not self.client:
            raise Exception("Supabase client not initialized.")
        print(f"--- Fetching world and campaign context for campaign ID: {campaign_id} ---")
        try:
            # The 'campaigns' table has a 'world_id' foreign key. We can join them.
            # The syntax `worlds(*)` tells Supabase to fetch all columns from the related 'worlds' table.
            response = await self.client.from_('campaigns').select("*, worlds(*)").eq('id', campaign_id).single().execute()
            if response.data:
                return response.data
            return {}
        except Exception as e:
            print(f"--- ERROR fetching world/campaign context: {e} ---")
            return {}


    async def upload_file(self, bucket_name: str, file_path: str, file_content: bytes) -> dict:
        """
        Uploads a file to the specified Supabase storage bucket.
        """
        if not self.client:
            raise Exception("Supabase client not initialized.")
        print(f"--- Uploading file to Supabase Storage. Bucket: {bucket_name}, Path: {file_path} ---")
        response = await self.client.storage.from_(bucket_name).upload(
            path=file_path,
            file=file_content,
            file_options={"content-type": "image/png"}
        )
        print(f"--- Supabase upload response: {response} ---")
        return response

    async def get_public_url(self, bucket_name: str, file_path: str) -> str:
        """
        Constructs the public URL for a file in Supabase storage.
        This is now an async method to correctly handle the underlying library call.
        """
        if not self.client:
            raise Exception("Supabase client not initialized.")
        public_url = await self.client.storage.from_(bucket_name).get_public_url(path=file_path)
        print(f"--- Constructed public URL: {public_url} ---")
        return public_url

    async def download_file(self, bucket_name: str, file_path: str) -> bytes:
        """
        Downloads a file from the specified Supabase storage bucket.
        """
        if not self.client:
            raise Exception("Supabase client not initialized.")

        response = await self.client.storage.from_(bucket_name).download(path=file_path)
        return response


# Create a single instance of the service to be used throughout the app
supabase = SupabaseService()