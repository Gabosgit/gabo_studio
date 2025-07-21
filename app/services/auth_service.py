import jwt
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.schemas.pydantic_models import UserAuthPydantic, UserCreatePydantic
from app.datamanager.data_manager_SQLAlchemy import SQLAlchemyDataManager
from app.core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES # <--- Import from config

from app.services.email_service import _send_password_reset_email
from app.datamanager.models import PasswordResetToken

# Define custom exceptions for clarity in the service layer
class InvalidTokenError(Exception):
    """Raised when a password reset token is invalid or not found."""
    pass

class ExpiredTokenError(Exception):
    """Raised when a password reset token has expired."""
    pass

class UserNotFoundError(Exception):
    """Raised when a user associated with a token is not found."""
    pass


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

    async def handle_forgot_password(self, email: str, db: Session, frontend_url: str) -> None:
        """
        Handles the business logic for the forgot password flow.
        Generates a reset token and sends an email if the user exists.
        Always returns without raising an error to prevent user enumeration.
        """
        user = self.data_manager.get_user_by_email(email, db)

        if user:
            # Generate a cryptographically secure, plain token
            token = secrets.token_urlsafe(32)
            # Hash the token for database storage
            hashed_token = pwd_context.hash(token)
            # Set token expiration
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=60)

            # Store the hashed token in the database
            self.data_manager.create_reset_token(user.id, hashed_token, expires_at, db)

            # Send the plain token to the user's email
            await _send_password_reset_email(user.email_address, token, frontend_url)
        else:
            # IMPORTANT: For security (user enumeration prevention),
            # do not indicate whether the email exists or not.
            # Just log internally if needed.
            print(f"Forgot password requested for non-existent email: {email}")

        # Always return None (or True) to the API layer, indicating success
        # from the client's perspective, regardless of user existence.
        return None

    async def reset_user_password(self, token: str, new_password: str, db: Session) -> bool:
        """
        Resets a user's password using a valid password reset token.
        - Verifies the token's validity and expiration.
        - Hashes the new password.
        - Updates the user's password in the database.
        - Invalidates the used token.
        Raises InvalidTokenError, ExpiredTokenError, or UserNotFoundError on failure.
        """
        # 1. Hash the plain token received from the user to look it up in the database
        #    (The token stored in DB is hashed, the one sent to user is plain)
        #    Note: This is a common point of confusion. We hash the *plain* token
        #    received from the user to compare it against the *hashed* token in the DB.
        #    The `verify_password` method of `pwd_context` is perfect for this.
        #    We are using the password context because it handles salting and stretching,
        #    making it robust for token hashing as well, not just passwords.

        # Find the token record by comparing the plain token with the stored hashed token
        reset_token_record = None
        active_tokens = db.query(PasswordResetToken).filter(
            PasswordResetToken.expires_at > datetime.now(timezone.utc)
        ).all()  # Fetch all tokens (for verification loop)
        # In a very large system, you might want to optimize this by fetching only potentially matching tokens
        # if you store a partial hash or a lookup ID with the token.
        # For now, we iterate and verify.

        for t in active_tokens:
            print(f"DEBUG: Type of t: {type(t)}")
            print(f"DEBUG: Value of t: {t}")  # This will show the ORM instance
            print(f"DEBUG: Type of t.token_hash: {type(t.token_hash)}")
            print(f"DEBUG: Value of t.token_hash: {t.token_hash}")

            # This is the line causing the warning/error
            if pwd_context.verify(token, t.token_hash):
                reset_token_record = t
                break

        if not reset_token_record:
            raise InvalidTokenError("Invalid or already used password reset token.")

        # 2. Check if the token has expired
        if reset_token_record.expires_at < datetime.now(timezone.utc):
            # Immediately delete expired token to prevent reuse
            self.data_manager.delete_reset_token(reset_token_record.id, db)
            raise ExpiredTokenError("Password reset token has expired.")

        # 3. Retrieve the user associated with the token
        user_to_reset = self.data_manager.get_user_by_id(reset_token_record.user_id, db)
        if not user_to_reset:
            # This indicates a data inconsistency, token exists but user doesn't
            self.data_manager.delete_reset_token(reset_token_record.id, db)  # Invalidate broken token
            raise UserNotFoundError("User associated with the token not found.")

        # 4. Hash the new password
        hashed_new_password = self.get_password_hash(new_password)

        # 5. Update the user's password
        update_success = self.data_manager.update_user_password(user_to_reset.id, hashed_new_password, db)
        if not update_success:
            # This should ideally not happen if user_to_reset was found
            raise RuntimeError("Failed to update user password in database.")

        # 6. Invalidate the used token by deleting it from the database
        self.data_manager.delete_reset_token(reset_token_record.id, db)

        return True  # Password reset successful