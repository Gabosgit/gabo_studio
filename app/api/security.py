# security.py
import os
from typing import Annotated
from dotenv import load_dotenv

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from app.datamanager.db_dependencies import get_data_manager
from app.schemas.pydantic_models import TokenData, UserAuthPydantic # Import your Pydantic models
from app.datamanager.database import get_db  # Import database session helpers
from app.datamanager.data_manager_SQLAlchemy import SQLAlchemyDataManager # Import DataManager for get_user_by_username
from app.services.auth_service import AuthService

# Load environment variables
load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY') # to get a string like this run: openssl rand -hex 32
ALGORITHM = os.getenv('ALGORITHM')

# This dependency provides an instance of AuthService, with its DataManager injected
def get_auth_service(
    data_manager: SQLAlchemyDataManager = Depends(get_data_manager)
) -> AuthService:
    """Dependency that provides an AuthService instance."""
    return AuthService(data_manager)


""" Authorization """
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # Instance of OAuth2PasswordBearer from fastapi.security.
# Handles the extraction and validation of OAuth 2.0 bearer tokens from the "Authorization" header.

async def get_current_user(
        token: Annotated[str, Depends(oauth2_scheme)],
        db: Session = Depends(get_db), # Inject DB session
        auth_service: AuthService = Depends(get_auth_service)  # Inject AuthService here
) -> UserAuthPydantic:
    """
    Ensures that only authenticated users can access protected resources.
    Extracts a JWT token from the request.
    Decodes the token and extracts the username.
    Retrieves the corresponding user from the database.
    Returns the user object if authentication is successful; otherwise, it raises an HTTPException indicating unauthorized access.
    :param auth_service:
    :param token: JWT token from the request
    :param db: Database session
    :return: user object
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception

    # Use DataManager to get the user
    user = auth_service.data_manager.get_user_by_username(username=token_data.username, db=db)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[UserAuthPydantic, Depends(get_current_user)],
) -> UserAuthPydantic:
    """
        Relies on the get_current_user dependency to retrieve the authenticated user.
        Checks if the user's account is disabled.
        Raises an HTTPException if the user is disabled.
        Returns the active user object if the user is not disabled.
        :param current_user: from get_current_user()
        :return: user object
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
