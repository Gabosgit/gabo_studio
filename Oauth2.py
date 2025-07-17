import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from typing import Annotated


import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from pydantic_models import TokenData, UserAuthPydantic
from datamanager.models import User #Import the SQLAlchemy model.
from datamanager.database import get_db, SessionLocal

load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY') # to get a string like this run: openssl rand -hex 32
ALGORITHM = os.getenv('ALGORITHM')
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


app = FastAPI()


def verify_password(plain_password, hashed_password):
    """
        Returns True if the provided plain_password matches the stored hashed_password
        :param plain_password: from user
        :param hashed_password: from database
    :return: boolean
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """
        Takes a plain password and converts it into a secure, one-way hashed string using bcrypt.
        This hashed string is then stored in the database
        :param password: plane password from user
        :return: hashed password
    """
    return pwd_context.hash(password)


def get_user(username: str, db: Session = Depends(get_db)):
    """
    Retrieves a user from the database by username.
    """
    user = db.query(User).filter(User.username == username).first()

    if user:
        return UserAuthPydantic(
            id=user.id,
            # created_at=user.created_at,
            username=user.username,
            password=user.password,
            # type_of_entity=user.type_of_entity,
            # name=user.name,
            # surname=user.surname,
            # email_address=user.email_address,
            # phone_number=user.phone_number,
            # vat_id=user.vat_id,
            # bank_account=user.bank_account,
            is_active=user.is_active
        )
    else:
        return None


def authenticate_user(db, username: str, password: str):
    """
    The returned user object can be used to check the user's roles or permissions, determining what resources they are allowed to access.
    The returned user object can be used to log the user's activity, providing an audit trail of who accessed what resources.
    The returned user object contains the necessary user information, that is needed to be included in the token's payload,
    typically used to generate an authentication token.
    :param db: database
    :param username: from user login
    :param password: from user login
    :return: user object
    """
    user = get_user(username, db)
    if not user:
        return False
    # password from user input / user.password = hashed password in db
    if not verify_password(password, user.password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """
    Creates a JWT with that data and expiration, signs it using a secret key, and returns the encoded JWT.
    data: parameter takes a dictionary containing the data you want to include in the JWT's payload, typically user-related information.
    expires_delta: This parameter allows you to specify the expiration time of the token. It's a timedelta object.
    If not provided, a default expiration time of 15 minutes is used.
    The token is then sent to the client, allowing them to make authenticated requests to the API.
    :param data: user data
    :param expires_delta: expiration time (optional)
    :return: encoded JWT
    """
    to_encode = data.copy() # Copy to avoid modifying the original data dictionary

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta # adds that timedelta to the current UTC time
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15) # adds a default of x minutes to the current UTC time

    to_encode.update({"exp": int(expire.timestamp())})  # Convert datetime to Unix timestamp (seconds since epoch)
        # The "exp" claim is a standard JWT claim that represents the expiration time.

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    # The jwt.encode function from the jwt library creates the JWT.
        # to_encode: The dictionary containing the payload data (including the expiration time).
        # SECRET_KEY: The secret key used to sign the JWT.
        # algorithm=ALGORITHM: The algorithm used to sign the JWT. (e.g., "HS256").
    return encoded_jwt # This token can then be used by clients to authenticate with the API.


""" Authorization """
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # Instance of OAuth2PasswordBearer from fastapi.security.
# Handles the extraction and validation of OAuth 2.0 bearer tokens from the "Authorization" header.

async def get_current_user(
        token: Annotated[str, Depends(oauth2_scheme)]
):
    """
    Ensures that only authenticated users can access protected resources.
    Extracts a JWT token from the request.
    Decodes the token and extracts the username.
    Retrieves the corresponding user from the database.
    Returns the user object if authentication is successful; otherwise, it raises an HTTPException indicating unauthorized access.
    :param token: JWT token from the request
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
    db = SessionLocal()  # create a session.
    try:
        user = get_user(username=token_data.username, db=db)  # db pass the session.
    finally:
        db.close()  # close the session.
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[UserAuthPydantic, Depends(get_current_user)],
):
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