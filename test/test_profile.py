import pytest

@pytest.mark.usefixtures("setup_common_dependencies_override")
class TestProfileEndpoints:

    def test_create_profile(self, test_client, mock_data_manager, mock_db, mock_auth_user):
        """Test profile creation endpoint."""
        # Setup
        mock_profile_id = 123
        mock_data_manager.create_profile.return_value = mock_profile_id
        profile_data = {
            "name": "Test Profile",
            "performance_type": "Test performance",
            "description": "Test Description",
            "bio": "Test Biography",
            "photos": [],
            "videos": [],
            "audios": [],
            "online_press": [],
            "website": None
        }

        # Execute
        response = test_client.post(
            "/profile",
            headers={"Authorization": "Bearer fake.jwt.token"},
            json=profile_data
        )

        # Verify
        assert response.status_code == 200
        assert response.json() == {"profile_id": mock_profile_id}
        mock_data_manager.create_profile.assert_called_once()

        # Verify profile data was passed correctly
        call_args = mock_data_manager.create_profile.call_args
        assert call_args[0][0].name == profile_data["name"]
        assert call_args[0][1] == mock_auth_user.id
        assert call_args[0][2] == mock_db

