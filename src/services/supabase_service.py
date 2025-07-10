from supabase import create_client, Client
from ..config import SUPABASE_URL, SUPABASE_KEY


class SupabaseService:
    """
    A service class to manage all interactions with the Supabase backend,
    including database operations and file storage.
    """

    def __init__(self):
        """
        Initializes the Supabase client.
        """
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Supabase URL and Key must be provided.")
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    def get_user(self):
        """
        Retrieves the current authenticated user.

        Returns:
            The user object or None if not authenticated.
        """
        return self.client.auth.get_user()

    def upload_file(self, bucket_name: str, file_path_in_bucket: str, file_body: bytes, content_type: str):
        """
        Uploads a file to a specified Supabase storage bucket.

        Args:
            bucket_name (str): The name of the storage bucket (e.g., 'documents').
            file_path_in_bucket (str): The desired path and filename within the bucket.
            file_body (bytes): The binary content of the file to upload.
            content_type (str): The MIME type of the file (e.g., 'application/pdf').
        """
        print(f"--- Uploading to Supabase Storage ---")
        print(f"Bucket: {bucket_name}, Path: {file_path_in_bucket}, Content-Type: {content_type}")
        try:
            file_options = {'upsert': 'true', 'content-type': content_type}

            response = self.client.storage.from_(bucket_name).upload(
                path=file_path_in_bucket,
                file=file_body,
                file_options=file_options
            )
            print("--- Supabase Upload Successful ---")
            return response
        except Exception as e:
            print(f"--- Supabase Upload Error ---: {e}")
            raise e

    def download_file(self, bucket_name: str, path_in_bucket: str) -> bytes:
        """
        Downloads a file from a Supabase storage bucket.

        Args:
            bucket_name (str): The name of the storage bucket.
            path_in_bucket (str): The path to the file within the bucket.

        Returns:
            bytes: The binary content of the downloaded file.
        """
        print(f"--- Downloading from Supabase Storage ---")
        print(f"Bucket: {bucket_name}, Path: {path_in_bucket}")
        try:
            response = self.client.storage.from_(bucket_name).download(path=path_in_bucket)
            print("--- Supabase Download Successful ---")
            return response
        except Exception as e:
            print(f"--- Supabase Download Error ---: {e}")
            raise e

    def get_public_url(self, bucket_name: str, file_path_in_bucket: str) -> str:
        """
        Gets the public URL for a file in a Supabase storage bucket.

        Args:
            bucket_name (str): The name of the storage bucket.
            file_path_in_bucket (str): The path to the file within the bucket.

        Returns:
            str: The public URL of the file.
        """
        return self.client.storage.from_(bucket_name).get_public_url(file_path_in_bucket)


# A single, shared instance of the service that can be imported elsewhere.
supabase = SupabaseService()