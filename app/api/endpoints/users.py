""" USER ROUTES """
import secrets

from fastapi import Depends, APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated, Optional
from sqlalchemy.orm import Session

from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES
from app.datamanager.data_manager_SQLAlchemy import SQLAlchemyDataManager
from app.datamanager.database import SessionLocal, get_db
from app.datamanager.db_dependencies import get_data_manager
from app.datamanager.exceptions_handler import handle_exceptions
from app.services.auth_service import AuthService, InvalidTokenError, ExpiredTokenError, UserNotFoundError # <-- Import custom exceptions  # Import the class for type hinting
from app.api.security import get_auth_service
from app.api.dependencies import get_common_dependencies
from app.schemas.pydantic_models import Token, UserCreatePydantic, ChangePasswordRequest, ForgotPasswordRequest, \
    UserNoPwdPydantic, UserUpdatePydantic, ResetPasswordRequest
from datetime import timedelta, datetime


# --- Create APIRouter instance ---
router = APIRouter(tags=["Users"]) # Added prefix /users here

""" LOGIN - generate/return 'bearer token' """
@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], # Depends() tells FastAPI to automatically inject form_data into the function.
    db: SessionLocal = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)  # <--- Inject AuthService here!
) -> Token: #-> Token: This type hint indicates that the function returns an object of type Token
    """
        The client sends a POST request to the /token endpoint with their username and password.
        The server authenticates the user and returns an access token in the response.
        Allows the client to use the returned token to authenticate subsequent requests to protected API endpoints.
        OAuth2PasswordRequestForm is a FastAPI class that automatically handles parsing username and password from the request's form data.
        :param auth_service:
        :param db:
        :param form_data: parameter of type OAuth2PasswordRequestForm
        :return: object of type Token, assumed to be a Pydantic model
    """
    user = auth_service.authenticate_user(db, form_data.username, form_data.password) # Function to verify the user's credentials.
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # function to generate the JWT
    access_token = auth_service.create_access_token(
        data={
            "sub": user.username},
            expires_delta=access_token_expires
        # data: creates the payload for the token, including:
        #   the user's username in the "sub" claim.
    )
    # Returns the access token to the client.
    return Token(access_token=access_token, token_type="bearer")


@router.post("/user", response_model=dict, status_code=status.HTTP_201_CREATED)
@handle_exceptions
async def sign_up(
        user_data: UserCreatePydantic,
        db: Session = Depends(get_db),
        auth_service: AuthService = Depends(get_auth_service)
):
    """Registers a new user.
        :param auth_service:
        :param db:
        :param user_data: dict with all user date from the post request
        :return: id new user or HTTPException
    """
    try:
        user_id = await auth_service.register_user(user_data, db)
        return {"user_id": user_id} # FastAPI automatically converts the Python dictionary {"user_id": user_id} into a JSON response
    except ValueError as e:
        # Caught from AuthService, e.g., "Username 'X' or email 'Y' already exists."
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,  # 409 Conflict for resource already exists
            detail=str(e)
        )
    except RuntimeError as e:
        # Caught from AuthService for unexpected DB errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        # Catch any other unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during user registration."
        )

@router.post("/change_password")
async def change_password(
    request: ChangePasswordRequest,
    common_dependencies: Annotated[tuple, Depends(get_common_dependencies)],
    auth_service: AuthService = Depends(get_auth_service)  # Inject the AuthService instance
):
    """
        Allows a logged-in user to change their password.
        Requires the old password for verification.
    """
    current_user, db, data_manager = common_dependencies
    try:
        # Pass the current_user's ID and the hashed password from the DB (current_user.password)
        await auth_service.change_user_password(
            user_id=current_user.id,
            current_hashed_password_from_db=current_user.password,
            old_password_attempt=request.old_password,
            new_password=request.new_password,
            db=db
        )
        return {"message": "Password changed successfully."}

    except ValueError as e:
        # Catch specific business logic errors from AuthService
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)  # e.g., "Incorrect old password."
        )
    except RuntimeError as e:
        # Catch unexpected operational errors (e.g., user not found for update, which is rare here)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while changing password."
        )
    except Exception as e:
        # Catch any other unexpected exceptions
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}"
        )


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(
    request: ForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service), # Inject AuthService
    db: Session = Depends(get_db) # Inject DB session
):
    """
    Initiates a password reset process. A reset link will be sent to the provided email address
    if an account with that email exists.
    """
    # Define your frontend URL where the user will reset their password
    frontend_reset_url = "http://localhost:5173" # <-- IMPORTANT: Replace with actual frontend URL

    # Delegate the business logic to the AuthService
    await auth_service.handle_forgot_password(request.email, db, frontend_reset_url)

    # Always return a generic success message to prevent user enumeration
    return {"message": "If an account with that email exists, a password reset link has been sent."}


@router.post("/reset-password", status_code=status.HTTP_200_OK, tags=["User Authentication"])
async def reset_password(
    request: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db)
):
    """
    Resets a user's password using a valid password reset token.
    """
    try:
        await auth_service.reset_user_password(request.token, request.new_password, db)
        return {"message": "Password has been successfully reset."}
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, # Or 401 Unauthorized if you prefer
            detail=str(e) # "Invalid or already used password reset token."
        )
    except ExpiredTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, # Or 401 Unauthorized
            detail=str(e) # "Password reset token has expired."
        )
    except UserNotFoundError as e:
        # This case implies a token pointed to a non-existent user,
        # which is an internal inconsistency, so 500 might be appropriate.
        # Or, if you want to be vague for security, return a generic message.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred. Please try again or contact support."
        )
    except Exception as e:
        # Catch any other unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}"
        )


@router.get("/user/me/", response_model=UserNoPwdPydantic)
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


@router.get("/user/{user_id}", response_model=UserNoPwdPydantic)
@handle_exceptions
async def get_user_by_id(
    user_id: int,
    common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    current_user, db, data_manager = common_dependencies
    user_by_id = data_manager.get_user_by_id(user_id, db)
    return  user_by_id


@router.patch("/user")
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


@router.patch("/user/deactivation")
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


@router.get("/user/{user_id}/profiles")
@handle_exceptions
async def get_user_profiles(
    user_id: int,
    common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    """

    :param user_id:
    :param common_dependencies:
    :return:
    """
    current_user, db, data_manager = common_dependencies
    profiles = data_manager.get_user_profiles(user_id, db)
    return {"user_profiles": profiles}


@router.get("/user/{user_id}/contracts")
@handle_exceptions
async def get_user_contracts(
    user_id: int,
    common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    """

    :param user_id:
    :param common_dependencies:
    :return:
    """
    current_user, db, data_manager = common_dependencies
    contracts = data_manager.get_user_contracts(user_id, db)
    return {"user_contracts": contracts}