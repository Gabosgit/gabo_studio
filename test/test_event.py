import pytest

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
