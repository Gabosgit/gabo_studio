"""
    API to manage Users, User-Profiles, User_Contracts, User_Events, and Accommodations
"""
import pdb

from fastapi import Depends, APIRouter, FastAPI, HTTPException, status, File, UploadFile
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from datamanager.exceptions_handler import register_exception_handlers, handle_exceptions
from pydantic_models import *
from datamanager.data_manager_SQLAlchemy import SQLAlchemyDataManager
from datamanager.database import SessionLocal, get_db
from datamanager.db_dependencies import get_data_manager

from typing import Annotated
from datetime import timedelta, datetime
from Oauth2 import ACCESS_TOKEN_EXPIRE_MINUTES, authenticate_user, create_access_token
from dependencies import get_common_dependencies

from fastapi.middleware.cors import CORSMiddleware # To allow requests from a react app

import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url

from concurrent.futures import ThreadPoolExecutor # This is the key import for the executor
import asyncio

# --- ThreadPoolExecutor for Concurrent Cloudinary Uploads ---
# This executor will run synchronous Cloudinary upload calls in separate threads,
# preventing the main FastAPI event loop from being blocked.
# The 'max_workers' parameter controls how many Cloudinary uploads can happen
# simultaneously in the background. Adjust based on your server's capacity and
# Cloudinary's rate limits.
executor = ThreadPoolExecutor(max_workers=10)

# Configuration
cloudinary.config(
    cloud_name = "dqkdbvnac",
    api_key = "135642772133192",
    api_secret = "1eAuh8WmfFjp7NPgE6nw8eIpSxo", # Click 'View API Keys' above to copy your API secret
    secure=True
)

app = FastAPI()
register_exception_handlers(app) #register the handlers.
router = APIRouter()

# Allow requests from your frontend (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React frontend
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

@app.post("/upload-multiple", response_model=dict)
async def upload_multiple_images(files: List[UploadFile] = File(...)):
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
@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    try:
        # Read the file contents as bytes
        contents = await file.read()

        # Upload directly using bytes
        result = cloudinary.uploader.upload(contents, resource_type="image")

        return {"url": result["secure_url"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ROOT ROUTE
@app.get("/", tags=["Home"])
async def root():
    """ Welcome message """
    return {"message": "Welcome to my MVP"}


# USER ROUTES
""" LOGIN - generate 'bearer token' """
@app.post("/token", tags=["User"])
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], # Depends() tells FastAPI to automatically inject form_data into the function.
    db: SessionLocal = Depends(get_db)
) -> Token: #-> Token: This type hint indicates that the function returns an object of type Token
    """
        The client sends a POST request to the /token endpoint with their username and password.
        The server authenticates the user and returns an access token in the response.
        Allows the client to use the returned token to authenticate subsequent requests to protected API endpoints.
        OAuth2PasswordRequestForm is a FastAPI class that automatically handles parsing username and password from the request's form data.
        :param db:
        :param form_data: parameter of type OAuth2PasswordRequestForm
        :return: object of type Token, assumed to be a Pydantic model
    """
    user = authenticate_user(db, form_data.username, form_data.password) # Function to verify the user's credentials.
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token( # function to generate the JWT
        data={"sub": user.username}, expires_delta=access_token_expires
    )  #data: creates the payload for the token, including the user's username in the "sub" claim.
    return Token(access_token=access_token, token_type="bearer") # Returns the access token to the client.


@app.post("/user", tags=["User"])
@handle_exceptions
async def sign_up(
        user_data: UserCreatePydantic,
        data_manager: SQLAlchemyDataManager = Depends(get_data_manager)):
    """
    :param user_data: dict with all user date from the post request
    :param data_manager: to call the create_user() function from data_manager_SQL_Alchemy.py
    :return: id new user or HTTPException
    """
    user_id = data_manager.create_user(user_data)
    return {"user_id": user_id} # FastAPI automatically converts the Python dictionary {"user_id": user_id} into a JSON response


@app.get("/user/me/", response_model=UserNoPwdPydantic, tags=["User"])
@handle_exceptions
async def get_user_me(
    common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    """
    The "Authorization" header is sent by the client in the GET request to /users/me/,
    and the get_current_active_user dependency uses it to authenticate and retrieve the user's information.
    :param common_dependencies: current_user, data_manager, db
    :return: current user data or HTTPException
    """
    current_user, db, data_manager = common_dependencies
    user = data_manager.get_user_by_id(current_user.id, db)
    return user


@app.get("/user/{user_id}", response_model=UserNoPwdPydantic, tags=["User"])
@handle_exceptions
async def get_user_by_id(
    user_id: int,
    common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    current_user, db, data_manager = common_dependencies
    user_by_id = data_manager.get_user_by_id(user_id, db)
    return  user_by_id

@app.patch("/user", tags=["User"])
@handle_exceptions
async def update_user(
        user_data_to_update: UserUpdatePydantic,
        common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    """
    :param user_data_to_update: dict with fields to update
    :param common_dependencies: current_user, data_manager, db
    :return: updated user data or HTTPException
    """
    current_user, db, data_manager = common_dependencies
    updated_user_data = data_manager.update_user(user_data_to_update, current_user.id, db)
    return updated_user_data


@app.patch("/user/deactivation", tags=["User"])
@handle_exceptions
async def soft_delete_user(
    common_dependencies: Annotated[tuple, Depends(get_common_dependencies)],
    deactivation_date: Optional[datetime] = None
):
    """
    :param common_dependencies: current_user, data_manager, db
    :param deactivation_date: query parameter
    :return: confirmation dict response with user id, user name and deactivation date or HTTPException
    """
    current_user, db, data_manager = common_dependencies
    response = data_manager.soft_delete_user(deactivation_date, current_user.id, db)
    return response


@app.get("/user/{user_id}/profiles", tags=["User"])
@handle_exceptions
async def get_user_profiles(
    user_id: int,
    common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    current_user, db, data_manager = common_dependencies
    profiles = data_manager.get_user_profiles(user_id, db)
    return {"user_profiles": profiles}


@app.get("/user/{user_id}/contracts", tags=["User"])
@handle_exceptions
async def get_user_contracts(
    user_id: int,
    common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    current_user, db, data_manager = common_dependencies
    contracts = data_manager.get_user_contracts(user_id, db)
    return {"user_contracts": contracts}


# PROFILE ROUTES
@app.post("/profile", tags=["Profile"])
@handle_exceptions
async def create_profile(
    profile_data: ProfilePydantic,
    common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    """
    :param profile_data: data from request validated with ProfilePydantic model
    :param common_dependencies: current_user, data_manager, db
    :return: id new profiler or HTTPException
    """
    current_user, db, data_manager = common_dependencies
    id_profile = data_manager.create_profile(profile_data, current_user.id, db)
    return {"profile_id": id_profile}


@app.get("/profile/{profile_id}", tags=["Profile"])
@handle_exceptions
async def get_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    data_manager: SQLAlchemyDataManager = Depends(get_data_manager)
):
    """
    :param profile_id: from patch request int
    :param db: database
    :param data_manager: Imported to call the get_profile() class method
    :return: profile data or HTTPException
    """
    profile_dict = data_manager.get_profile_by_id(profile_id, db)
    return profile_dict


@app.put("/profile/{profile_id}", tags=["Profile"])
@handle_exceptions
async def update_profile(
    profile_id: int,
    profile_data: ProfilePydantic,
    common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    """
        :param profile_id: from path query
        :param profile_data: data from request validated with ProfilePydantic model
        :param common_dependencies: current_user, data_manager, db
        :return: updated profile data or HTTPException
        """
    current_user, db, data_manager = common_dependencies
    updated_profile_data = data_manager.update_profile(profile_id, profile_data, current_user.id, db)
    return updated_profile_data


@app.delete("/profile/{profile_id}", tags=["Profile"], response_model=dict)
@handle_exceptions
async def delete_profile(
        profile_id: int,
        common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    """
    :param common_dependencies: current_user, data_manager, db
    :param profile_id: from path query
    :return: successfully message or HTTPException
    """
    current_user, db, data_manager = common_dependencies
    data_manager.delete_profile(profile_id, current_user.id, db)
    return {"message": "Profile deleted successfully"}


# CONTRACT ROUTES
@app.post("/contract", tags=["Contract"])
@handle_exceptions
async def create_contract(
    contract_data: ContractCreatePydantic,
    common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    """
    :param contract_data: data from body request validated with ContractPydantic model
    :param common_dependencies: current_user, data_manager, db
    :return: id new contract or HTTPException
    """
    current_user, db, data_manager = common_dependencies
    id_contract = data_manager.create_contract(contract_data, current_user.id, db)
    return {"contract_id": id_contract}


@app.get("/contract/{contract_id}", tags=["Contract"])
@handle_exceptions
async def get_contract(
    contract_id: int,
    common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    """
    :param contract_id: from path request
    :param common_dependencies: current_user, data_manager, db
    :return: contract data and events in contract or HTTPException
    """
    current_user, db, data_manager = common_dependencies
    contract_dict = data_manager.get_contract_by_id(contract_id, current_user.id, db)
    events_in_contract = data_manager.get_contract_events(contract_id, current_user.id, db)
    return {"contract_data": contract_dict, "contract_event_ids": events_in_contract}


@app.put("/contract/{contract_id}", tags=["Contract"])
@handle_exceptions
async def update_contract(
    contract_id: int,
    contract_data: ContractUpdatePydantic,
    common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    """
    :param contract_id: from path query
    :param contract_data: from body request
    :param common_dependencies: current_user, data_manager, db
    :return: updated data or HTTPException
    """
    current_user, db, data_manager = common_dependencies
    update_contract_data = data_manager.update_contract(contract_id, contract_data, current_user.id, db)
    return update_contract_data


@app.patch("/contract/{contract_id}", tags=["Contract"])
@handle_exceptions
async def disable_contract(
    contract_id: int,
    common_dependencies: Annotated[tuple, Depends(get_common_dependencies)],
    disable_at
):
    """
    :param contract_id: from path query
    :param disable_at: from query parameter
    :param common_dependencies: current_user, data_manager, db
    :return: confirmation dict response or HTTPException
    """
    current_user, db, data_manager = common_dependencies
    response = data_manager.disable_contract(contract_id, disable_at, current_user.id, db)
    return response


@app.get("/contract/itinerary", tags=["Contract"])
@handle_exceptions
async def show_itinerary():
    return {"message": "Shows Itinerary"}


@app.get("/contract/{contract_id}/events", tags=["Contract"])
@handle_exceptions
async def get_contract_events_id_and_name(
    contract_id: int,
    common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    current_user, db, data_manager = common_dependencies
    events = data_manager.get_contract_events_id_and_name(contract_id, db)
    return {"contract_events": events}



# EVENT ROUTES
@app.post("/event", tags=["Event"])
@handle_exceptions
async def create_event(
    event_data: EventPydantic,
    common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    """
    :param event_data: from request body
    :param common_dependencies: current_user, data_manager, db
    :return: id created event or HTTPException
    """
    current_user, db, data_manager = common_dependencies
    id_event = data_manager.create_event(event_data, current_user, db)
    return {"event_id": id_event}


@app.get("/event/{event_id}", tags=["Event"])
@handle_exceptions
async def get_event(
    event_id: int,
    common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    """
    :param event_id: from path query
    :param common_dependencies: data_base, current_user, db
    :return: event data or HTTPException
    """
    current_user, db, data_manager = common_dependencies
    event_data = data_manager.get_event_by_id(event_id, current_user.id, db).dict()
    if event_data['accommodation_id']:
        accommodation_data = data_manager.get_accommodation_by_id(event_data['accommodation_id'] ,db).dict()
        event_data["accommodation"] = accommodation_data
    return event_data


@app.put("/event/{event_id}", tags=["Event"])
@handle_exceptions
async def update_event(
        event_id: int,
        event_data_to_update: EventUpdatePydantic,
        common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    """
    :param event_id: from path query
    :param event_data_to_update: body query
    :param common_dependencies: data_manager, current_user, db
    :return: updated event data or HTTPException
    """
    current_user, db, data_manager = common_dependencies
    updated_event_data = data_manager.update_event(event_id, event_data_to_update, current_user.id, db)
    return updated_event_data


@app.delete("/event/{event_id}", tags=["Event"])
@handle_exceptions
async def delete_event(
        event_id: int,
        common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    """
    :param event_id: from path query
    :param common_dependencies: data_manager, current_user, db
    :return: confirmation message or HTTPException
    """
    current_user, db, data_manager = common_dependencies
    data_manager.delete_event(event_id, current_user.id, db)
    return {"message": "Event deleted successfully"}


# ACCOMMODATION ROUTES
@app.post("/accommodation", tags=["Accommodation"])
@handle_exceptions
async def create_accommodation(
    accommodation_data: AccommodationPydantic,
    db: Session = Depends(get_db),
    data_manager: SQLAlchemyDataManager = Depends(get_data_manager)
):
    """
    :param accommodation_data: from request body
    :param db: database
    :param data_manager: Imported to call create_accommodation() class method
    :return: id new accommodation or HTTPException
    """
    id_accommodation = data_manager.create_accommodation(accommodation_data, db)
    return {"accommodation_id": id_accommodation}


@app.get("/accommodation/{accommodation_id}", tags=["Accommodation"])
@handle_exceptions
async def get_accommodation(
        accommodation_id: int,
        common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    """
    :param accommodation_id: from path query
    :param common_dependencies: data_manager, current_user, db
    :return: accommodation data or HTTPException
    """
    current_user, db, data_manager = common_dependencies
    accommodation_data = data_manager.get_accommodation_by_id(accommodation_id, db)
    return accommodation_data


@app.put("/accommodation/{accommodation_id}", tags=["Accommodation"])
@handle_exceptions
async def update_accommodation(
        accommodation_id: int,
        accommodation_data: AccommodationUpdatePydantic,
        common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    """
    :param accommodation_id:  from path query
    :param accommodation_data: from body query
    :param common_dependencies: data_manager, current_user, db
    :return: updated accommodation data or HTTPException
    """
    current_user, db, data_manager = common_dependencies
    updated_accommodation_data = data_manager.update_accommodation(accommodation_id, accommodation_data, db)
    return updated_accommodation_data


@app.delete("/accommodation/{accommodation_id}", tags=["Accommodation"])
@handle_exceptions
async def delete_accommodation(
        accommodation_id: int,
        common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    """
    :param accommodation_id:  from path query
    :param common_dependencies: data_manager, current_user, db
    :return: confirmation message or HTTPException
    """
    current_user, db, data_manager = common_dependencies
    data_manager.delete_accommodation(accommodation_id, db)
    return {"message": "Accommodation deleted successfully"}

