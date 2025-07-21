import pytest

from app.schemas.pydantic_models import EventPydantic, AccommodationPydantic, EventUpdatePydantic


@pytest.fixture
def event_data():
    """
        Sample event data recorded in DB, for testing.
        Default scope="function" as no specified: it will be executed before every single test function.
        Changes in other functions will not affect subsequent test functions because each test gets its own fresh copy.
    """
    return {
        "id": 3,
        "created_at": "2025-05-06T20:16:42.757742+02:00",
        "name": "Event User_1 and User_2",
        "contract_id": 9,
        "profile_offeror_id": 3,
        "profile_offeree_id": 2,
        "contact_person": "Contact Test",
        "contact_phone": "+35 1234 1234",
        "date": "2026-01-02",
        "duration": 5400.0,
        "start": "20:00:00",
        "end": "21:30:00",
        "arrive": "2026-01-02T16:00:00",
        "stage_set": "17:00:00",
        "stage_check": "18:00:00",
        "catering_open": "16:00:00",
        "catering_close": "20:00:00",
        "meal_time": "22:00:00",
        "meal_location_name": "Test Restaurant",
        "meal_location_address": "Test Address",
        "accommodation_id": 1
    }

@pytest.fixture
def mock_event(event_data):
    """
        Create a mock profiler model from profile data.
        Default scope="function" as no specified. This means mock_profile will be created before every test function that requests it
        The result of instantiating ProfilePydantic with the sample data is then returned by the mock_profile fixture.
    """
    return EventPydantic(**event_data)  # ** dictionary unpacking operator


@pytest.fixture
def event_data_to_update():
    """
        Sample profile data for testing an update.
        Default scope="function" as no specified: it will be executed before every single test function.
        This fixture should ideally contain *changes* from the original profile_data to simulate an update.
    """
    return {
        "name": "Updated Event Name",
        "contact_person": "Updated Event Contact",
        "start": "20:30:00"
    }

@pytest.fixture
def accommodation_data():
    """
        Sample event data recorded in DB, for testing.
        Default scope="function" as no specified: it will be executed before every single test function.
        Changes in other functions will not affect subsequent test functions because each test gets its own fresh copy.
    """
    return {
        "id": 1,
        "name": "Accommodation_1",
        "contact_person": "Test Person",
        "address": "Test Address",
        "telephone_number": "+35 1234 1234",
        "email": "test_email@server.com",
        "website": "https://www.testweb.com/",
        "url": "https://testurl.com/",
        "check_in": "2026-10-27T14:00:00",
        "check_out": "2026-11-27T12:00:00"
    }

@pytest.fixture
def mock_accommodation(accommodation_data):
    """
        Create a mock profiler model from profile data.
        Default scope="function" as no specified. This means mock_profile will be created before every test function that requests it
        The result of instantiating ProfilePydantic with the sample data is then returned by the mock_profile fixture.
    """
    return AccommodationPydantic(**accommodation_data)  # ** dictionary unpacking operator


@pytest.mark.usefixtures("setup_common_dependencies_override")
class TestEventEndpoints:

    def test_create_event(self, test_client, mock_data_manager, mock_db, mock_auth_user):
        """Test event creation endpoint."""
        # Setup
        mock_event_id = 123
        mock_data_manager.create_event.return_value = mock_event_id
        event_data = {
            "id": None,  # Optional for creation, required for return.
            "created_at": None,  # format 2026-10-27T16:00:00
            "name": "Test Event",  # Event name
            "contract_id": 1,
            "profile_offeror_id": 123,
            "profile_offeree_id": 234,
            "contact_person": "Test Contact Person",
            "contact_phone": "+49 1234 5678",
            "date": "2026-01-01",
            "duration": "PT1H30M",  # format PT1H30M
            "start": "20:00",
            "end": "21:00",
            "arrive": "2026-10-27T16:00:00",  # format 2026-10-27T16:00:00
            "stage_set": "18:00",
            "stage_check": "19:00",
            "catering_open": "17:00",
            "catering_close": "22:00",
            "meal_time": "22:00",
            "meal_location_name": "Test Meal Location",
            "meal_location_address": "Test Meal Location Address",
            "accommodation_id": 123
        }

        # Execute
        response = test_client.post(
            "/event",
            headers={"Authorization": "Bearer fake.jwt.token"},
            json=event_data
        )

        # Verify
        assert response.status_code == 200
        assert response.json() == {"event_id": mock_event_id}
        mock_data_manager.create_event.assert_called_once()

        # Verify event data was passed correctly
        call_args = mock_data_manager.create_event.call_args
        assert call_args[0][0].name == event_data["name"]
        assert call_args[0][1] == mock_auth_user
        assert call_args[0][2] == mock_db


    def test_get_event(self, test_client, mock_data_manager, mock_db, event_data, mock_event, accommodation_data,
                       mock_accommodation):
        """Get profile by iD
            test_client: The TestClient instance for making HTTP requests to the FastAPI app. (Likely defined as TestClient(app)).
            mock_data_manager: The MagicMock(spec=SQLAlchemyDataManager) instance.
            mock_db: The MagicMock() instance (representing a database session).
            event_data: The dictionary containing sample event data.
            mock_event: The EventPydantic model instance, created from event_data.
        """
        #Setup
        event_id = 1
        mock_data_manager.get_event_by_id.return_value = mock_event
        """ It tells the mock_data_manager that when its get_event_by_id method is called, it should return the mock_event Pydantic object.
        """

        mock_data_manager.get_accommodation_by_id.return_value = mock_accommodation
        """ It tells the mock_data_manager that when its get_event_by_id method is called, it should return the mock_event Pydantic object.
        """

        # Execute
        """ This simulates a client """
        response = test_client.get(f"/event/{event_id}")
        """ 
            The test_client is used to send a simulated GET request to the /event/{event_id} endpoint of the FastAPI application. 
            Because setup_db_and_datamanager_override has overridden the application's dependencies, 
            when the API route for /event/{event_id} internally calls get_db and get_data_manager (which then likely calls mock_data_manager.get_event_by_id), 
            it will receive the pre-configured mock_data_manager and its behavior. 
            The mock returns the mock_event object as configured in the Arrange phase.
        """

        # Verify
        assert response.status_code == 200
        response_data = response.json()
        #pdb.set_trace()
        assert response_data['accommodation']['name'] == 'Accommodation_1'

    def test_update_event(self, test_client, mock_data_manager, mock_db, mock_auth_user, event_data_to_update, mock_event):
        """ Test update profile """
        # Setup
        event_id_to_update = 123  # The ID from the URL

        # Create an expected Pydantic object that reflects the *result* of the update
        # This combines the original mock_event's data with the changes from event_data_to_update.
        # We also set the ID to match what the endpoint expects.
        expected_returned_event = mock_event.model_copy(update=event_data_to_update)
        # Ensure the ID matches the one being updated in the URL
        expected_returned_event.id = event_id_to_update

        mock_data_manager.update_event.return_value = expected_returned_event

        # Execute
        response = test_client.put(
            f"/event/{event_id_to_update}",  # Use the actual ID here
            headers={"Authorization": "Bearer fake.jwt.token"},
            json=event_data_to_update  # Send the data for updating
        )

        # Verify
        assert response.status_code == 200
        assert response.json() == expected_returned_event.model_dump(mode='json')

        # Create a Pydantic model that matches the structure `update_profile`
        # method expects for the data to be updated.
        expected_update_payload = EventUpdatePydantic(**event_data_to_update)

        mock_data_manager.update_event.assert_called_once_with(
            # The order of arguments to the mocked method matters for assert_called_with.
            event_id_to_update,
            expected_update_payload,  # `update_event` expects a EventUpdatePydantic model
            mock_auth_user.id,  # Ensure the user ID is passed
            mock_db
        )