# upload_srd.py

import os
import pathlib
from google import genai
from dotenv import load_dotenv


def upload_srd_file():
    """
    Uploads the local srd.pdf file to the Gemini File API using the
    application's API key and prints the resulting resource name.
    """
    load_dotenv()

    api_key = "AIzaSyDc60XV-OjPtDy9G9YQ9CJj2Cu-L5IcQXc"
    if not api_key:
        print("Error: GEMINI_API_KEY not found in .env file or environment.")
        return

    srd_path = pathlib.Path("assets/srd.pdf")
    if not srd_path.exists():
        print(f"Error: The file '{srd_path}' was not found in the project directory.")
        print("Please place your SRD PDF in the project root and name it 'srd.pdf'.")
        return

    client = genai.Client(api_key=api_key)
    print(f"Uploading '{srd_path}' to the Gemini File API...")

    try:
        srd_file_response = client.files.upload(file=srd_path)

        print("\n" + "=" * 50)
        print("✅ File Upload Successful!")
        print(f"Your new Gemini file name is: {srd_file_response.name}")
        print("\nCOPY the above file name and PASTE it into your .env file for the")
        print("GEMINI_SRD_FILE_NAME variable.")
        print("=" * 50)

    except Exception as e:
        print(f"\nAn error occurred during upload: {e}")
        print("Please ensure your GEMINI_API_KEY is correct and has File API permissions.")


if __name__ == "__main__":
    upload_srd_file()