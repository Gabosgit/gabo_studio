import pytest

from app.schemas.pydantic_models import ContractPydantic, ContractUpdatePydantic


@pytest.fixture
def contract_data():
    """
        Sample contract data recorded in DB, for testing.
        Default scope="function" as no specified: it will be executed before every single test function.
        Changes in other functions will not affect subsequent test functions because each test gets its own fresh copy.
    """
    return {
        "name": "SOMMER FESTIVAL",
        "offeror_id": 5,
        "offeree_id": 2,
        "currency_code": "EUR",
        "upon_signing": 60,
        "upon_completion": 40,
        "payment_method": "transfer",
        "performance_fee": "1000.00",
        "travel_expenses": "500.00",
        "accommodation_expenses": "1500.00",
        "other_expenses": "300.00",
        "total_fee": "3300.00",
        "disabled": False,
        "disabled_at": None,
        "signed_at": None,
        "delete_date": None
    }

@pytest.fixture
def mock_contract(contract_data):
    """
        Create a mock contract model from contract_data.
        Default scope="function" as no specified. This means mock_contract will be created before every test function that requests it
        The result of instantiating ContractPydantic with the sample data is then returned by the mock_contract fixture.
    """
    return ContractPydantic(**contract_data)  # ** dictionary unpacking operator


@pytest.fixture
def contract_data_to_update():
    """
        Sample profile data for testing an update.
        Default scope="function" as no specified: it will be executed before every single test function.
        This fixture should ideally contain *changes* from the original profile_data to simulate an update.
    """
    return {
        "name": "UPDATED CONTRACT NAME",
        "payment_method": "cash",
        "disabled": True
    }


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


    def test_get_contract(self, test_client, mock_data_manager, mock_db, mock_auth_user, contract_data, mock_contract):
        """Get contract by iD
            test_client: The TestClient instance for making HTTP requests to the FastAPI app. (Likely defined as TestClient(app)).
            mock_data_manager: The MagicMock(spec=SQLAlchemyDataManager) instance.
            mock_db: The MagicMock() instance (representing a database session).
            contract_data: The dictionary containing sample profile data.
            mock_profile: The ProfilePydantic model instance, created from profile_data.
        """
        #Setup
        contract_id = 1
        mock_data_manager.get_contract_by_id.return_value = mock_contract
        """ It tells the mock_data_manager that when its get_contract_by_id method is called, it should return the mock_contract Pydantic object.
        """

        # Execute
        """ This simulates a client """
        response = test_client.get(f"/contract/{contract_id}")
        """ 
            The test_client is used to send a simulated GET request to the /contract/{contract_id} endpoint of the FastAPI application. 
            Because setup_db_and_datamanager_override has overridden the application's dependencies, 
            when the API route for /contract/{contract_id} internally calls get_db and get_data_manager (which then likely calls mock_data_manager.get_contract_by_id), 
            it will receive the pre-configured mock_data_manager and its behavior. 
            The mock returns the mock_contract object as configured in the Arrange phase.
        """

        # Verify
        assert response.status_code == 200
        response_data = response.json()
        #assert response_data == mock_contract.model_dump(mode='json') # Use model_dump to compare Pydantic with JSON

        # Verify get_contract_by_id was called with the correct arguments
        mock_data_manager.get_contract_by_id.assert_called_once_with(
            contract_id,
            mock_auth_user.id,
            mock_db
        )


    def test_update_contract(self, test_client, mock_data_manager, mock_db, mock_auth_user, contract_data_to_update, mock_contract):
        """ Test update profile """
        # Setup
        contract_id_to_update = 123  # The ID from the URL

        # Create an expected Pydantic object that reflects the *result* of the update
        # This combines the original mock_contract's data with the changes from contract_data_to_update.
        # We also set the ID to match what the endpoint expects.
        expected_returned_contract = mock_contract.model_copy(update=contract_data_to_update)
        # Ensure the ID matches the one being updated in the URL
        expected_returned_contract.id = contract_id_to_update

        mock_data_manager.update_contract.return_value = expected_returned_contract

        # Execute
        response = test_client.put(
            f"/contract/{contract_id_to_update}",  # Use the actual ID here
            headers={"Authorization": "Bearer fake.jwt.token"},
            json=contract_data_to_update  # Send the data for updating
        )

        # Verify
        assert response.status_code == 200
        assert response.json() == expected_returned_contract.model_dump(mode='json')

        # Create a Pydantic model that matches the structure `update_contract`
        # method expects for the data to be updated.
        expected_update_payload = ContractUpdatePydantic(**contract_data_to_update)

        mock_data_manager.update_contract.assert_called_once_with(
            # The order of arguments to the mocked method matters for assert_called_with.
            contract_id_to_update,
            expected_update_payload,  # `update_contract` expects a ContractUpdatePydantic model
            mock_auth_user.id,  # Ensure the user ID is passed
            mock_db
        )