# import os
# import pytest
# from fastapi.testclient import TestClient
# from unittest.mock import patch, MagicMock
#
# from datamanager.database import get_db
# from datamanager.db_dependencies import get_data_manager
# from pydantic_models import UserAuthPydantic, UserNoPwdPydantic
#
# # Patch environment variables before importing app
# with patch.dict(os.environ, {
#     "DATABASE_URL": "sqlite:///",
#     "SECRET_KEY": "testsecretkey",
#     "ALGORITHM": "HS256"
# }):
#     from main import app
#     from dependencies import get_common_dependencies
#     from datamanager.data_manager_SQLAlchemy import SQLAlchemyDataManager
#
#
# @pytest.fixture(scope="module")
# def test_client():
#     """Create a test client for the app."""
#     return TestClient(app) # TestClient is used to simulate requests to the app
#
#
# @pytest.fixture(scope="module")
# def mock_auth_user():
#     """Create a mock authenticated user."""
#     return UserAuthPydantic(
#         id=1,
#         username="testuser",
#         password="hashedpassword",
#         is_active=True
#     )
#
#
# @pytest.fixture(scope="module")
# def mock_db():
#     """Create a mock database session."""
#     return MagicMock()
#
#
# @pytest.fixture(scope="module")
# def mock_data_manager():
#     """Create a mock data manager.
#         Mimic the API (Interface): The mock will only allow access to attributes and methods
#         that exist on the SQLAlchemyDataManager class
#     """
#     return MagicMock(spec=SQLAlchemyDataManager)
#
#
# @pytest.fixture(scope="module")
# def setup_dependencies(mock_auth_user, mock_db, mock_data_manager):
#     """
#         Setup dependency overrides for testing.
#         it runs the mock version: override_get_common_dependencies,
#         instead the current function in APP get_common_dependencies.
#     """
#     async def override_get_common_dependencies():
#         return mock_auth_user, mock_db, mock_data_manager
#
#     app.dependency_overrides[get_common_dependencies] = override_get_common_dependencies
#     yield
#     app.dependency_overrides = {}
#
# @pytest.fixture(scope="module")
# def setup_db_and_datamanager(mock_db, mock_data_manager):
#     """
#     Overrides FastAPI's get_db and get_data_manager dependencies
#     to return mock objects.
#     """
#     # Store original dependencies to restore them later
#     original_get_db = app.dependency_overrides.get(get_db)
#     original_get_data_manager = app.dependency_overrides.get(get_data_manager)
#
#     # Override the dependencies with functions that return our mocks
#     app.dependency_overrides[get_db] = lambda: mock_db
#     app.dependency_overrides[get_data_manager] = lambda: mock_data_manager
#
#     yield # This allows the tests to run
#
#     # Clean up: Restore original dependencies after all tests in the module are done
#     if original_get_db is None:
#         del app.dependency_overrides[get_db]
#     else:
#         app.dependency_overrides[get_db] = original_get_db
#
#     if original_get_data_manager is None:
#         del app.dependency_overrides[get_data_manager]
#     else:
#         app.dependency_overrides[get_data_manager] = original_get_data_manager
#
#
# @pytest.fixture
# def user_data():
#     """
#         Sample user data for testing. This dictionary serves as a convenient and consistent set of input data.
#         Default scope="function" as no specified: it will be executed before every single test function.
#         Changes in other functions will not affect subsequent test functions because each test gets its own fresh copy.
#     """
#     return {
#         "id": 1,
#         "username": "testuser",
#         "type_of_entity": "individual",
#         "name": "Test",
#         "surname": "User",
#         "email_address": "test@example.com",
#         "phone_number": "+1234567890",
#         "is_active": True,
#         "vat_id": None,
#         "bank_account": None,
#         "deactivation_date": None,
#         "delete_date": None
#     }
#
#
# @pytest.fixture
# def mock_user(user_data):
#     """
#         Create a mock user model from user data.
#         Default scope="function" as no specified.
#         This means mock_user will be created before every test function that requests it
#         The result of instantiating UserNoPwdPydantic with the sample data is then returned by the mock_user fixture.
#     """
#     return UserNoPwdPydantic(**user_data)
#
# """ usefixtures: This marker tells Pytest that all test methods within this class
#     implicitly need the setup_dependencies fixture to run.
#     It ensures that the dependency overrides are set up before any test in this class runs and torn down after all tests
#     in this class are done. Applied at the class level here, its setup/teardown will effectively wrap the entire test class execution
# """
# @pytest.mark.usefixtures("setup_dependencies", "setup_db_and_datamanager")
# class TestAPI:
#     """Test suite for API endpoints.
#         setup_dependencies runs, which in turn causes mock_auth_user, mock_db, and mock_data_manager
#         to be created (if they haven't been already for this module).
#         The app.dependency_overrides are set, so the FastAPI app will use these mock objects.
#     """
#
#     def test_user_get(self, test_client, mock_data_manager, mock_db, user_data, mock_user):
#         """Test getting a user by ID.
#             test_client: The TestClient instance for making HTTP requests to your FastAPI app. (Likely defined as TestClient(app)).
#             mock_data_manager: The MagicMock(spec=SQLAlchemyDataManager) instance.
#             mock_db: The MagicMock() instance (representing a database session).
#             user_data: The dictionary containing sample user data.
#             mock_user: The UserNoPwdPydantic model instance, created from user_data.
#         """
#         # Setup | Arrange (Setup Phase - "Given")
#         user_id = 1
#         mock_data_manager.get_user_by_id.return_value = mock_user
#         """ It tells the mock_data_manager that when its get_user_by_id method is called, it should return the mock_user Pydantic object.
#         """
#
#         # Execute | Act (Execution Phase - "When")
#         """ This simulates a client """
#         response = test_client.get(f"/user/{user_id}")
#         """ The test_client is used to send a simulated GET request to the /user/{user_id} endpoint of the FastAPI application.
#             Because setup_dependencies has overridden the application's dependencies,
#             when the API route for /user/{user_id} internally calls get_common_dependencies (which then likely calls mock_data_manager.get_user_by_id),
#             it will receive the pre-configured mock_data_manager and its behavior.
#             The mock returns the mock_user object as configured in the Arrange phase.
#         """
#
#         # Verify | Assert (Verification Phase - "Then")
#         assert response.status_code == 200
#         response_data = response.json()
#         assert response_data == user_data
#
#         mock_data_manager.get_user_by_id.assert_called_once_with(user_id, mock_db)
#         """ It verifies that the get_user_by_id method on mock_data_manager was called exactly once, with the specific
#             arguments: user_id (which is 1) and the mock_db instance.
#             This assertion confirms that your API endpoint correctly interacted with its data_manager dependency.
#         """
#
#
#     def test_login_for_access_token(self, test_client, mock_auth_user):
#         """Test login endpoint that generates access tokens."""
#         # Setup
#         credentials = {"username": "testuser", "password": "password123"}
#
#         # Execute
#         with patch("main.authenticate_user", return_value=mock_auth_user):
#             response = test_client.post("/token", data=credentials)
#
#         # Verify
#         assert response.status_code == 200
#         token_data = response.json()
#         assert "access_token" in token_data
#         assert len(token_data["access_token"]) > 0
#         assert token_data["token_type"] == "bearer"
#
#
#     def test_user_me_endpoint(self, test_client, mock_data_manager, mock_db, mock_auth_user, user_data, mock_user):
#         """Test the /user/me endpoint that returns the current user."""
#         # Setup
#         mock_data_manager.get_user_by_id.return_value = mock_user
#
#         # Execute
#         response = test_client.get(
#             "/user/me/",
#             headers={"Authorization": "Bearer fake.jwt.token"}
#         )
#
#         # Verify
#         assert response.status_code == 200
#         assert response.json() == user_data
#         mock_data_manager.get_user_by_id.assert_called_with(mock_auth_user.id, mock_db)
#
#
#     def test_create_profile(self, test_client, mock_data_manager, mock_db, mock_auth_user):
#         """Test profile creation endpoint."""
#         # Setup
#         mock_profile_id = 123
#         mock_data_manager.create_profile.return_value = mock_profile_id
#         profile_data = {
#             "name": "Test Profile",
#             "performance_type": "Test performance",
#             "description": "Test Description",
#             "bio": "Test Biography",
#             "photos": [],
#             "videos": [],
#             "audios": [],
#             "online_press": [],
#             "website": None
#         }
#
#         # Execute
#         response = test_client.post(
#             "/profile",
#             headers={"Authorization": "Bearer fake.jwt.token"},
#             json=profile_data
#         )
#
#         # Verify
#         assert response.status_code == 200
#         assert response.json() == {"profile_id": mock_profile_id}
#         mock_data_manager.create_profile.assert_called_once()
#
#         # Verify profile data was passed correctly
#         call_args = mock_data_manager.create_profile.call_args
#         assert call_args[0][0].name == profile_data["name"]
#         assert call_args[0][1] == mock_auth_user.id
#         assert call_args[0][2] == mock_db
#
#
#     def test_create_contract(self, test_client, mock_data_manager, mock_db, mock_auth_user):
#         """Test contract creation endpoint."""
#         # Setup
#         mock_contract_id = 123
#         mock_data_manager.create_contract.return_value = mock_contract_id
#
#         contract_data = {
#             "name": "Test Contract",
#             "offeree_id": 2,
#             "currency_code": "USD",
#             "upon_signing": 50,
#             "upon_completion": 50,
#             "payment_method": "bank_transfer",
#             "performance_fee": "1000.00",
#             "travel_expenses": "100.00",
#             "accommodation_expenses": "200.00"
#         }
#
#         # Execute
#         response = test_client.post(
#             "/contract",
#             headers={"Authorization": "Bearer fake.jwt.token"},
#             json=contract_data
#         )
#
#         # Verify
#         assert response.status_code == 200
#         assert response.json() == {"contract_id": mock_contract_id}
#         mock_data_manager.create_contract.assert_called_once()
#
#         # Verify contract data was passed correctly
#         call_args = mock_data_manager.create_contract.call_args
#         assert call_args[0][0].name == contract_data["name"]
#         assert call_args[0][1] == mock_auth_user.id
#         assert call_args[0][2] == mock_db
#
#
#     def test_create_event(self, test_client, mock_data_manager, mock_db, mock_auth_user):
#         """Test event creation endpoint."""
#         # Setup
#         mock_event_id = 123
#         mock_data_manager.create_event.return_value = mock_event_id
#         event_data = {
#             "id": None,  # Optional for creation, required for return.
#             "created_at": None,  # format 2026-10-27T16:00:00
#             "name": "Test Event",  # Event name
#             "contract_id": 1,
#             "profile_offeror_id": 123,
#             "profile_offeree_id": 234,
#             "contact_person": "Test Contact Person",
#             "contact_phone": "+49 1234 5678",
#             "date": "2026-01-01",
#             "duration": "PT1H30M",  # format PT1H30M
#             "start": "20:00",
#             "end": "21:00",
#             "arrive": "2026-10-27T16:00:00",  # format 2026-10-27T16:00:00
#             "stage_set": "18:00",
#             "stage_check": "19:00",
#             "catering_open": "17:00",
#             "catering_close": "22:00",
#             "meal_time": "22:00",
#             "meal_location_name": "Test Meal Location",
#             "meal_location_address": "Test Meal Location Address",
#             "accommodation_id": 123
#         }
#
#         # Execute
#         response = test_client.post(
#             "/event",
#             headers={"Authorization": "Bearer fake.jwt.token"},
#             json=event_data
#         )
#
#         # Verify
#         assert response.status_code == 200
#         assert response.json() == {"event_id": mock_event_id}
#         mock_data_manager.create_profile.assert_called_once()
#
#         # Verify event data was passed correctly
#         call_args = mock_data_manager.create_event.call_args
#         assert call_args[0][0].name == event_data["name"]
#         assert call_args[0][1] == mock_auth_user
#         assert call_args[0][2] == mock_db
#
#
#     def test_create_accommodation(self, test_client, mock_data_manager, mock_db):
#         """ Test accommodation creation endpoint."""
#         mock_accommodation_id = 123
#         mock_data_manager.create_accommodation.return_value = mock_accommodation_id
#         accommodation_data = {
#             "id": None,  # Optional for creation, required for return.
#             "created_at": None,
#             "name": "Test Accommodation",
#             "contact_person": "Test Contact Person",
#             "address": "Test Address",
#             "telephone_number": "+49 8765 4321",
#             "email": "Test@email.com", # Email optional.
#             "website": "https://www.test_web.com",  # make website optional.
#             "url": "https://www.test_url.com",  # Website optional.
#             "check_in": "2026-10-27T16:00:00",  # format 2026-10-27T16:00:00
#             "check_out": "2026-10-27T16:00:00"  # format 2026-10-27T16:00:00
#         }
#
#         # Execute
#         response = test_client.post(
#             "/accommodation",
#             headers={"Authorization": "Bearer fake.jwt.token"},
#             json=accommodation_data
#         )
#
#         # Verify
#         assert response.status_code == 200
#         assert response.json() == {"accommodation_id": mock_accommodation_id}
#         mock_data_manager.create_accommodation.assert_called_once()
#
#         # Verify event data was passed correctly
#         call_args = mock_data_manager.create_accommodation.call_args
#         assert call_args[0][0].name == accommodation_data["name"]
#         assert call_args[0][1] == mock_db
