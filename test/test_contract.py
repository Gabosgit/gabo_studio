import pytest

@pytest.mark.usefixtures("setup_common_dependencies_override")
class TestContractEndpoints:

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
