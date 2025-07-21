""" UPLOAD ROUTES """
from fastapi import APIRouter, HTTPException, UploadFile, File
from concurrent.futures import ThreadPoolExecutor # This is the key import for the executor
import cloudinary
import cloudinary.uploader
import asyncio
import os
from dotenv import load_dotenv

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

    # Removed 'async' keyword here to make it a synchronous function,
    # as required by loop.run_in_executor().
    def upload_single_file_to_cloudinary(file_content: bytes):
        """
        Helper function to upload a single file to Cloudinary.
        This function is synchronous and will be run in a separate thread
        using the ThreadPoolExecutor.
        """
        # print("Uploading file to Cloudinary...") # For debugging
        result = cloudinary.uploader.upload(file_content, resource_type="image")
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