import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from pydantic_models import UserAuthPydantic, UserNoPwdPydantic
from decimal import Decimal

# Patch environment variables before importing app
with patch.dict(os.environ, {
    "DATABASE_URL": "sqlite:///",
    "SECRET_KEY": "testsecretkey",
    "ALGORITHM": "HS256"
}):
    from main import app
    from dependencies import get_common_dependencies
    from datamanager.data_manager_SQLAlchemy import SQLAlchemyDataManager


@pytest.fixture(scope="module")
def test_client():
    """Create a test client for the app."""
    return TestClient(app)


@pytest.fixture(scope="module")
def mock_auth_user():
    """Create a mock authenticated user."""
    return UserAuthPydantic(
        id=1,
        username="testuser",
        password="hashedpassword",
        is_active=True
    )


@pytest.fixture(scope="module")
def mock_db():
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture(scope="module")
def mock_data_manager():
    """Create a mock data manager."""
    return MagicMock(spec=SQLAlchemyDataManager)


@pytest.fixture(scope="module")
def setup_dependencies(mock_auth_user, mock_db, mock_data_manager):
    """Setup dependency overrides for testing."""

    async def override_get_common_dependencies():
        return mock_auth_user, mock_db, mock_data_manager

    app.dependency_overrides[get_common_dependencies] = override_get_common_dependencies
    yield
    app.dependency_overrides = {}


@pytest.fixture
def user_data():
    """Sample user data for testing."""
    return {
        "id": 1,
        "username": "testuser",
        "type_of_entity": "individual",
        "name": "Test",
        "surname": "User",
        "email_address": "test@example.com",
        "phone_number": "+1234567890",
        "is_active": True,
        "vat_id": None,
        "bank_account": None,
        "deactivation_date": None,
        "delete_date": None
    }


@pytest.fixture
def mock_user(user_data):
    """Create a mock user model from user data."""
    return UserNoPwdPydantic(**user_data)


@pytest.mark.usefixtures("setup_dependencies")
class TestAPI:
    """Test suite for API endpoints."""

    def test_user_get(self, test_client, mock_data_manager, mock_db, user_data, mock_user):
        """Test getting a user by ID."""
        # Setup
        user_id = 1
        mock_data_manager.get_user_by_id.return_value = mock_user

        # Execute
        response = test_client.get(f"/user/{user_id}")

        # Verify
        assert response.status_code == 200
        response_data = response.json()
        assert response_data == user_data
        mock_data_manager.get_user_by_id.assert_called_once_with(user_id, mock_db)

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

    def test_create_contract(self, test_client, mock_data_manager, mock_db, mock_auth_user):
        """Test contract creation endpoint."""
        # Setup
        mock_contract_id = 123
        mock_data_manager.create_contract.return_value = mock_contract_id

        contract_data = {
            "name": "Test Contract",
            "offeree_id": 2,
            "currency_code": "USD",
            "upon_signing": 50,
            "upon_completion": 50,
            "payment_method": "bank_transfer",
            "performance_fee": "1000.00",
            "travel_expenses": "100.00",
            "accommodation_expenses": "200.00"
        }

        # Execute
        response = test_client.post(
            "/contract",
            headers={"Authorization": "Bearer fake.jwt.token"},
            json=contract_data
        )

        # Verify
        assert response.status_code == 200
        assert response.json() == {"contract_id": mock_contract_id}
        mock_data_manager.create_contract.assert_called_once()

        # Verify contract data was passed correctly
        call_args = mock_data_manager.create_contract.call_args
        assert call_args[0][0].name == contract_data["name"]
        assert call_args[0][1] == mock_auth_user.id
        assert call_args[0][2] == mock_db