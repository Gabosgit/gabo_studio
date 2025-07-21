import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from datamanager.db_dependencies import get_data_manager
from pydantic_models import UserAuthPydantic, UserCreatePydantic
from datamanager.data_manager_SQLAlchemy import SQLAlchemyDataManager
from core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES # <--- Import from config

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(self, data_manager: SQLAlchemyDataManager):
        self.data_manager = data_manager

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Returns True if the provided plain_password matches the stored hashed_password
        :param plain_password: from user
        :param hashed_password: from database
        :return: boolean
        """
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """
        Takes a plain password and converts it into a secure, one-way hashed string using bcrypt.
        This hashed string is then stored in the database
        :param password: plane password from user
        :return: hashed password
        """
        return pwd_context.hash(password)

    def authenticate_user(self, db: Session, username: str, password: str) -> Optional[UserAuthPydantic]:
        """
        Authenticates a user by username and password.
        Returns the UserAuthPydantic object if authentication is successful, False otherwise.
        """
        # Use the DataManager to get the user by username
        user = self.data_manager.get_user_by_username(username, db)
        if not user:
            return None # User not found

        # password from user input / user.password = hashed password in db
        if not self.verify_password(password, user.password):
            return None # Password does not match
        return user

    def create_access_token(self, data: dict, expires_delta: timedelta | None = None):
        """
        Creates a JWT with that data and expiration, signs it using a secret key, and returns the encoded JWT.
        This method is here because it's part of the authentication *process* of generating a token after login.
        However, the `get_current_user` dependency (which *validates* tokens) will remain in security.py.
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": int(expire.timestamp())})

        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt


    async def register_user(self, user_data: UserCreatePydantic, db: Session) -> int:
        """
        Registers a new user by hashing the password and then saving the user data
        via the DataManager.
        Returns the ID of the created user.
        Raises ValueError if the username or email already exists.
        Raises RuntimeError for unexpected database errors during creation.
        """
        # 1. Hash the plain password
        hashed_pwd = self.get_password_hash(user_data.password)

        # 2. Create the user in the database via DataManager
        try:
            user_id = self.data_manager.create_user(user_data, hashed_pwd, db)
            return user_id
        except ValueError as e:
            # Re-raise the ValueError from DataManager for duplicate user/email
            raise e
        except Exception as e:
            # Catch any other unexpected errors from DataManager and re-raise as RuntimeError
            raise RuntimeError(f"Failed to register user due to an internal error: {e}")


    async def change_user_password(
            self,
            user_id: int,
            current_hashed_password_from_db: str,  # The hashed password for verification
            old_password_attempt: str,
            new_password: str,
            db: Session
    ) -> bool:
        """
        Handles the business logic for changing a user's password.
        - Verifies the old password.
        - Hashes the new password.
        - Updates the password in the database via the DataManager.
        Raises ValueError for invalid old password, RuntimeError for unexpected DB issues.
        """
        # 1. Verify the old password using the stored hashed password
        if not self.verify_password(old_password_attempt, current_hashed_password_from_db):
            raise ValueError("Incorrect old password.")

        # 2. Hash the new password
        hashed_new_password = self.get_password_hash(new_password)

        # 3. Update the user's password in the database via DataManager
        success = self.data_manager.update_user_password(user_id, hashed_new_password, db)

        if not success:
            # This case means the user_id wasn't found during the update, which
            # should ideally not happen if current_user comes from a valid session.
            raise RuntimeError("Failed to update password: User not found in database for update.")

        # 4. (Optional but Recommended) Invalidate current sessions/tokens
        # If using JWTs, token expiration handles this. For immediate invalidation,
        # you'd need a JWT blacklist mechanism (e.g., Redis lookup in get_current_user).
        # This is beyond the scope of this function but is a consideration.

        return True  # Indicate successful password change