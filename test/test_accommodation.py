import pytest

@pytest.mark.usefixtures("setup_db_and_datamanager_override")
class TestAccommodationEndpoints:

    def test_create_accommodation(self, test_client, mock_data_manager, mock_db):
        """ Test accommodation creation endpoint."""
        mock_accommodation_id = 123
        mock_data_manager.create_accommodation.return_value = mock_accommodation_id
        accommodation_data = {
            "id": None,  # Optional for creation, required for return.
            "created_at": None,
            "name": "Test Accommodation",
            "contact_person": "Test Contact Person",
            "address": "Test Address",
            "telephone_number": "+49 8765 4321",
            "email": "Test@email.com",  # Email optional.
            "website": "https://www.test_web.com",  # make website optional.
            "url": "https://www.test_url.com",  # Website optional.
            "check_in": "2026-10-27T16:00:00",  # format 2026-10-27T16:00:00
            "check_out": "2026-10-27T16:00:00"  # format 2026-10-27T16:00:00
        }

        # Execute
        response = test_client.post(
            "/accommodation",
            headers={"Authorization": "Bearer fake.jwt.token"},
            json=accommodation_data
        )

        # Verify
        assert response.status_code == 200
        assert response.json() == {"accommodation_id": mock_accommodation_id}
        mock_data_manager.create_accommodation.assert_called_once()

        # Verify event data was passed correctly
        call_args = mock_data_manager.create_accommodation.call_args
        assert call_args[0][0].name == accommodation_data["name"]
        assert call_args[0][1] == mock_db
