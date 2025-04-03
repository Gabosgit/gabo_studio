"""
    API to manage Users, User-Profiles, User_Contracts, User_Events, and Accommodations
"""
import os

from fastapi import Depends, APIRouter, FastAPI, HTTPException, status
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

from datamanager.exception_classes import EventNotFoundException, EventUserMismatchException, AccommodationNotFoundException
from sqlalchemy.exc import SQLAlchemyError

app = FastAPI()
register_exception_handlers(app) #register the handlers.
router = APIRouter()

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
async def sign_up(
        user_data: UserCreatePydantic,
        data_manager: SQLAlchemyDataManager = Depends(get_data_manager)):
    """
    :param user_data: dict with all user date from the post request
    :param data_manager: to call the create_user() function from data_manager_SQL_Alchemy.py
    :return: ID of the created user.
    """
    try:
        user_id = data_manager.create_user(user_data)
        return {"user_id": user_id} # FastAPI automatically converts the Python dictionary {"user_id": user_id} into a JSON response
    except ValueError as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error."
        )


@app.get("/users/me/", response_model=UserNoPwdPydantic, tags=["User"])
async def get_user_me(
    common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    """
    The "Authorization" header is sent by the client in the GET request to /users/me/,
    and the get_current_active_user dependency uses it to authenticate and retrieve the user's information.
    :param common_dependencies: current_user, data_manager, db
    :return: user's information
    """
    current_user, db, data_manager = common_dependencies
    user = data_manager.get_user_by_id(current_user.id, db)
    return user


@app.put("/user", tags=["User"])
async def update_user(
        user_data_to_update: UserUpdatePydantic,
        common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    """
    :param user_data_to_update: dict with fields to update
    :param common_dependencies: current_user, data_manager, db
    :return: user data
    """
    current_user, db, data_manager = common_dependencies

    user_data = data_manager.update_user(user_data_to_update, current_user.id, db)
    return user_data
    # except ValueError as e:
    #     print(e)
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail=str(e))
    # except SQLAlchemyError as e:
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail=f"Database error. {e}"
    #     )
    # except Exception as e:
    #     print(e)
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail=f"Internal server error. {e}"
    #     )


@app.patch("/user", tags=["User"])
async def soft_delete_user(
    common_dependencies: Annotated[tuple, Depends(get_common_dependencies)],
    deactivation_date: Optional[datetime] = None
):
    """
    :param common_dependencies: current_user, data_manager, db
    :param deactivation_date: query parameter
    :return: confirmation dict response or HTTPException
    """
    current_user, db, data_manager = common_dependencies

    response = data_manager.soft_delete_user(deactivation_date, current_user.id, db)
    return response
    # except Exception as e:
    #     raise HTTPException(
    #         status_code=500,
    #         detail=f"Internal Server Error: {e}")



# PROFILE ROUTES
@app.post("/profile/", tags=["Profile"])
async def create_profile(
    profile_data: ProfilePydantic,
    common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    """
    :param profile_data: data from request validated with ProfilePydantic model
    :param common_dependencies: current_user, data_manager, db
    :return: profile ID
    """
    current_user, db, data_manager = common_dependencies
    try:
        id_profile = data_manager.create_profile(profile_data, current_user.id, db)
        return {"profile_id": id_profile}
    except ValueError as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


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
    :return:
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
        :return: update_profile return updated_profile_data or raise an exception.
        """
    current_user, db, data_manager = common_dependencies
    updated_profile_data = data_manager.update_profile(profile_id, profile_data, current_user.id, db)
    return updated_profile_data



@app.delete("/profile/{profile_id}", tags=["Profile"], response_model=dict)
@handle_exceptions
def delete_profile_endpoint(
        profile_id: int,
        common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    """
    :param common_dependencies: current_user, data_manager, db
    :param profile_id: from path query
    :return: successfully message or Exception
    """
    current_user, db, data_manager = common_dependencies
    data_manager.delete_profile(profile_id, current_user.id, db)
    return {"message": "Profile deleted successfully"}


# CONTRACT ROUTES
@app.post("/contract", tags=["Contract"])
async def create_contract(
    contract_data: ContractPydantic,
    common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    """
    :param contract_data: data from body request validated with ContractPydantic model
    :param common_dependencies: current_user, data_manager, db
    :return: id contract
    """
    current_user, db, data_manager = common_dependencies
    try:
        id_contract = data_manager.create_contract(contract_data, current_user, db)
        return {"contract_id": id_contract}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@app.get("/contract/{contract_id}", tags=["Contract"])
@handle_exceptions
async def get_contract(
    contract_id: int,
    common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    """
    :param contract_id: from path request
    :param common_dependencies: current_user, data_manager, db
    :return: Dictionary with contract infos
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
    :return: updated data or exception
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
async def show_itinerary():
    return {"message": "Shows Itinerary"}


# EVENT ROUTES
@app.post("/event", tags=["Event"])
async def create_event(
    event_data: EventPydantic,
    common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    """
    :param event_data: from request body
    :param common_dependencies: current_user, data_manager, db
    :return: id created event
    """
    current_user, db, data_manager = common_dependencies
    try:
        id_event = data_manager.create_event(event_data, current_user, db)
        return {"event_id": id_event}
    except ValueError as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error. {e}"
        )


@app.get("/event/{event_id}", tags=["Event"])
async def get_event(
    event_id: int,
    common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    current_user, db, data_manager = common_dependencies
    event_data = data_manager.get_event_by_id(event_id, current_user.id, db)
    return event_data



@app.put("/event/{event_id}", tags=["Event"])
async def update_event(
        event_id: int,
        event_data_to_update: EventUpdatePydantic,
        common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    current_user, db, data_manager = common_dependencies
    try:
        updated_event_data = data_manager.update_event(event_id, event_data_to_update, current_user.id, db)
        return updated_event_data
    except EventNotFoundException as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error. {e}"
        )


@app.delete("/event/{event_id}", tags=["Event"])
async def delete_event(
        event_id: int,
        common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    current_user, db, data_manager = common_dependencies
    try:
        data_manager.delete_event(event_id, current_user.id, db)
        return {"message": "Event deleted successfully"}
    except EventNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event not found. {e}"
        )
    except EventUserMismatchException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Event does not belong to the current user."
        )
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error. {e}"
        )


# ACCOMMODATION ROUTES
@app.post("/accommodation", tags=["Accommodation"])
async def create_accommodation(
    accommodation_data: AccommodationPydantic,
    db: Session = Depends(get_db),
    data_manager: SQLAlchemyDataManager = Depends(get_data_manager)
):
    """
    :param accommodation_data: from request body
    :param db: database
    :param data_manager: Imported to call create_accommodation() class method
    :return: id created accommodation
    """
    try:
        id_accommodation = data_manager.create_accommodation(accommodation_data, db)
        return {"accommodation_id": id_accommodation}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

@app.get("/accommodation/{accommodation_id}", tags=["Accommodation"])
async def get_accommodation(
        accommodation_id: int,
        common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    current_user, db, data_manager = common_dependencies
    try:
        accommodation_data = data_manager.get_accommodation_by_id(accommodation_id, db)
        return accommodation_data
    except AccommodationNotFoundException as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error. {e}"
        )

@app.put("/accommodation/{accommodation_id}", tags=["Accommodation"])
async def update_accommodation(
        accommodation_id: int,
        accommodation_data: AccommodationUpdatePydantic,
        common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    current_user, db, data_manager = common_dependencies
    try:
        updated_accommodation_data = data_manager.update_accommodation(accommodation_id, accommodation_data, db)
        return updated_accommodation_data
    except AccommodationNotFoundException as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error. {e}"
        )

@app.delete("/accommodation/{accommodation_id}", tags=["Accommodation"])
async def delete_accommodation(
        accommodation_id: int,
        common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    current_user, db, data_manager = common_dependencies
    try:
        data_manager.delete_accommodation(accommodation_id, db)
        return {"message": "Accommodation deleted successfully"}
    except AccommodationNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Accommodation not found. {e}"
        )
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error. {e}"
        )
