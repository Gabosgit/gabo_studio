import pytest
from unittest.mock import patch

@pytest.mark.usefixtures("setup_common_dependencies_override", "setup_db_and_datamanager_override")
class TestUserEndpoints:
    """Test suite for API endpoints.
        setup_dependencies runs, which in turn causes mock_auth_user, mock_db, and mock_data_manager
        to be created (if they haven't been already for this module).
        The app.dependency_overrides are set, so the FastAPI app will use these mock objects.
    """

    def test_user_get(self, test_client, mock_data_manager, mock_db, user_data, mock_user):
        """Test getting a user by ID.
            test_client: The TestClient instance for making HTTP requests to your FastAPI app. (Likely defined as TestClient(app)).
            mock_data_manager: The MagicMock(spec=SQLAlchemyDataManager) instance.
            mock_db: The MagicMock() instance (representing a database session).
            user_data: The dictionary containing sample user data.
            mock_user: The UserNoPwdPydantic model instance, created from user_data.
        """
        # Setup | Arrange (Setup Phase - "Given")
        user_id = 1
        mock_data_manager.get_user_by_id.return_value = mock_user
        """ It tells the mock_data_manager that when its get_user_by_id method is called, it should return the mock_user Pydantic object.
        """

        # Execute | Act (Execution Phase - "When")
        """ This simulates a client """
        response = test_client.get(f"/user/{user_id}")
        """ The test_client is used to send a simulated GET request to the /user/{user_id} endpoint of the FastAPI application. 
            Because setup_dependencies has overridden the application's dependencies, 
            when the API route for /user/{user_id} internally calls get_common_dependencies (which then likely calls mock_data_manager.get_user_by_id), 
            it will receive the pre-configured mock_data_manager and its behavior. 
            The mock returns the mock_user object as configured in the Arrange phase.
        """

        # Verify | Assert (Verification Phase - "Then")
        assert response.status_code == 200
        response_data = response.json()
        assert response_data == user_data

        mock_data_manager.get_user_by_id.assert_called_once_with(user_id, mock_db)
        """ It verifies that the get_user_by_id method on mock_data_manager was called exactly once, with the specific 
            arguments: user_id (which is 1) and the mock_db instance.
            This assertion confirms that your API endpoint correctly interacted with its data_manager dependency.
        """


    def test_login_for_access_token(self, test_client, mock_auth_user):
        """Test login endpoint that generates access tokens."""
        # Setup
        credentials = {"username": "testuser", "password": "password123"}

        # Execute
        with patch("main.authenticate_user", return_value=mock_auth_user):
            response = test_client.post("/token", data=credentials)

        # Verify
        assert response.status_code == 200
        token_data = response.json()
        assert "access_token" in token_data
        assert len(token_data["access_token"]) > 0
        assert token_data["token_type"] == "bearer"


    def test_user_me_endpoint(self, test_client, mock_data_manager, mock_db, mock_auth_user, user_data, mock_user):
        """Test the /user/me endpoint that returns the current user."""
        # Setup
        mock_data_manager.get_user_by_id.return_value = mock_user

        # Execute
        response = test_client.get(
            "/user/me/",
            headers={"Authorization": "Bearer fake.jwt.token"}
        )

        # Verify
        assert response.status_code == 200
        assert response.json() == user_data
        mock_data_manager.get_user_by_id.assert_called_with(mock_auth_user.id, mock_db)

    def test_create_user(self, test_client, mock_data_manager, mock_db, mock_auth_user):
        """Test user creation endpoint."""
        # Setup
        mock_user_id = 123
        mock_data_manager.create_user.return_value = mock_user_id
        user_data = {
            "username": "Test Name",
            "type_of_entity": "Self-Employee",
            "password": "pass",
            "name": "Test Name",
            "surname": "Test Surname",
            "email_address": "test@email.com",
            "phone_number": "+49 1234 5678",
            "vat_id": None,
            "bank_account": None,  # IBAN
            "is_active": True,  # Default to True
            "deactivation_date": "2026-10-27T16:00:00", # format 2026-10-27T16:00:00
            "delete_date": "2026-10-27T16:00:00"  # format 2026-10-27T16:00:00
        }

        # Execute
        response = test_client.post(
            "/user",
            headers={"Authorization": "Bearer fake.jwt.token"},
            json=user_data
        )

        # Verify
        assert response.status_code == 200
        assert response.json() == {"user_id": mock_user_id}
        mock_data_manager.create_user.assert_called_once()

        # Verify profile data was passed correctly
        call_args = mock_data_manager.create_user.call_args
        assert call_args[0][0].name == user_data["name"]