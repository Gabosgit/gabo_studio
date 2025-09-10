""" UPLOAD ROUTES """
from fastapi import APIRouter, HTTPException, UploadFile, File
from concurrent.futures import ThreadPoolExecutor # This is the key import for the executor
import cloudinary
import cloudinary.uploader
import asyncio
import os
from dotenv import load_dotenv
from typing import List
from pydantic import BaseModel
import re # Import the regular expression module

load_dotenv()
CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME')
API_KEY = os.getenv('CLOUDINARY_API_KEY')
API_SECRET = os.getenv('CLOUDINARY_API_SECRET')

# --- Create APIRouter instance ---
router = APIRouter(tags=["Uploads"]) # Added prefix /users here

# --- ThreadPoolExecutor for Concurrent Cloudinary Uploads ---
# This executor will run synchronous Cloudinary upload calls in separate threads,
# preventing the main FastAPI event loop from being blocked.
# The 'max_workers' parameter controls how many Cloudinary uploads can happen
# simultaneously in the background. Adjust based on your server's capacity and
# Cloudinary's rate limits.
executor = ThreadPoolExecutor(max_workers=10)

# Configuration
cloudinary.config(
    cloud_name = CLOUD_NAME,
    api_key = API_KEY,
    api_secret = API_SECRET, # Click 'View API Keys' above to copy your API secret
    secure=True
)

@router.post("/upload-multiple", response_model=dict)
async def upload_multiple_images(files: list[UploadFile] = File(...)):
    """
    Uploads multiple image files to Cloudinary concurrently.
    Each file is processed in a separate thread to avoid blocking the event loop.
    """
    uploaded_urls = []
    loop = asyncio.get_event_loop()

    assert_folder = "images"  # The folder name where we want to store the files

    # Removed 'async' keyword here to make it a synchronous function,
    # as required by loop.run_in_executor().
    def upload_single_file_to_cloudinary(file_content: bytes):
        """
        Helper function to upload a single file to Cloudinary.
        This function is synchronous and will be run in a separate thread
        using the ThreadPoolExecutor.
        """
        # print("Uploading file to Cloudinary...") # For debugging
        result = cloudinary.uploader.upload(
            file_content,
            resource_type="auto",
            folder = "images")  # Pass the folder name here
        # print(f"Cloudinary upload complete: {result['secure_url']}") # For debugging
        return result

    try:
        upload_tasks = []
        for file in files:
            # Read file contents asynchronously
            contents = await file.read()
            # Schedule the synchronous Cloudinary upload function to run in the executor
            task = loop.run_in_executor(executor, upload_single_file_to_cloudinary, contents)
            upload_tasks.append(task)

        # Wait for all upload tasks to complete concurrently
        results = await asyncio.gather(*upload_tasks)

        for result in results:
            if "secure_url" in result:
                uploaded_urls.append(result["secure_url"])
            else:
                # Handle cases where Cloudinary might not return a URL (e.g., error)
                print(f"Cloudinary upload result missing secure_url: {result}")
                raise HTTPException(status_code=500, detail="Cloudinary upload failed for one or more files.")

        return {"urls": uploaded_urls}

    except Exception as e:
        # Log the full exception for debugging purposes
        print(f"Error during multiple image uploads: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload images: {str(e)}")

@router.post("/upload-multiple-audios", response_model=dict)
async def upload_multiple_audios(files: list[UploadFile] = File(...)):
    """
    Uploads multiple image files to Cloudinary concurrently.
    Each file is processed in a separate thread to avoid blocking the event loop.
    """
    uploaded_urls = []
    loop = asyncio.get_event_loop()

    assert_folder = "audios" # The folder name where we want to store the files

    # Removed 'async' keyword here to make it a synchronous function,
    # as required by loop.run_in_executor().
    def upload_single_file_to_cloudinary(file_content: bytes):
        """
        Helper function to upload a single file to Cloudinary.
        This function is synchronous and will be run in a separate thread
        using the ThreadPoolExecutor.
        """
        result = cloudinary.uploader.upload(
            file_content,
            resource_type="auto",
            folder=assert_folder) # Pass the folder name here
        # print(f"Cloudinary upload complete: {result['secure_url']}") # For debugging
        return result

    try:
        upload_tasks = []
        for file in files:
            # Read file contents asynchronously
            contents = await file.read()
            # Schedule the synchronous Cloudinary upload function to run in the executor
            task = loop.run_in_executor(executor, upload_single_file_to_cloudinary, contents)
            upload_tasks.append(task)

        # Wait for all upload tasks to complete concurrently
        results = await asyncio.gather(*upload_tasks)

        for result in results:
            if "secure_url" in result:
                uploaded_urls.append(result["secure_url"])
            else:
                # Handle cases where Cloudinary might not return a URL (e.g., error)
                print(f"Cloudinary upload result missing secure_url: {result}")
                raise HTTPException(status_code=500, detail="Cloudinary upload failed for one or more files.")

        return {"urls": uploaded_urls}

    except Exception as e:
        # Log the full exception for debugging purposes
        print(f"Error during multiple audio uploads: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload audio: {str(e)}")

# UPLOAD
@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    try:
        # Read the file contents as bytes
        contents = await file.read()

        # Upload directly using bytes
        result = cloudinary.uploader.upload(contents, resource_type="image")

        return {"url": result["secure_url"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# REMOVE FILES
# The frontend will send a list of full URLs, not just public IDs.
class DeletionData(BaseModel):
    urls: List[str]


@router.post("/delete-multiple-assets")
async def delete_multiple_assets(data: DeletionData):
    """
    Deletes multiple assets from Cloudinary based on a list of URLs.
    """
    results = {}

    # Iterate through each URL and attempt to delete the asset
    for url in data.urls:
        try:
            # Step 1: Extract the public ID and resource type from the URL
            # Regex to capture the resource type and the path (public ID)
            match = re.search(r"/(image|video|raw)/upload/(?:v\d+/)?(.+)\.\w+", url)
            if not match:
                raise ValueError("Invalid Cloudinary URL format.")

            resource_type = match.group(1)
            public_id = match.group(2)

            # Step 2: Call the Cloudinary destroy method with the resource type
            result = cloudinary.uploader.destroy(
                public_id,
                resource_type=resource_type
            )

            # Cloudinary returns 'not found' if the asset doesn't exist
            if result.get("result") not in ["ok", "not found"]:
                raise Exception(f"Cloudinary API failed to delete asset: {public_id}")

            # Use the URL as the key for tracking, as it's what the frontend sent
            results[url] = result.get("result", "ok")

        except (ValueError, Exception) as e:
            results[url] = f"error: {str(e)}"

    # Step 3: Check if all deletions were successful
    if all(status == "ok" or status == "not found" for status in results.values()):
        return {"message": "All assets deletion requests processed.", "results": results}
    else:
        raise HTTPException(
            status_code=400,
            detail={"message": "Some assets could not be deleted", "results": results}
        )