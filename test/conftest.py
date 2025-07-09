# tests/conftest.py

import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session # Import Session for mock_db spec if needed

# IMPORTANT: No imports related to 'app' or its dependencies here yet.
# They will be imported inside the set_test_env fixture.

# Import your Pydantic models (these can be imported at the top level
# as they don't depend on environment variables for their definition)
from pydantic_models import UserAuthPydantic, UserNoPwdPydantic

# Optional: If you have AccommodationPydantic or other models, import them here
# from pydantic_models import AccommodationPydantic
# from datetime import datetime
# import re
# from pydantic import EmailStr, HttpUrl, BaseModel, field_validator
# from typing import Optional


@pytest.fixture(scope="session", autouse=True)
def set_test_env():
    """
    Patches environment variables for the entire test session
    before the application (FastAPI app, dependencies, data managers) is imported.
    """
    # Define the environment variables you want to set for testing
    test_env_vars = {
        "DATABASE_URL": "sqlite:///:memory:", # Use in-memory SQLite for tests
        "SECRET_KEY": "testsecretkey",
        "ALGORITHM": "HS256"
    }

    # Use patch.dict to temporarily modify os.environ
    # 'clear=True' ensures a clean environment, removing any existing vars not specified here.
    # Be cautious with 'clear=True' if you rely on other system env vars in tests.
    with patch.dict(os.environ, test_env_vars, clear=True):
        # IMPORTANT: Import your application components *inside* this context manager.
        # This ensures they read the patched environment variables during their initial load.
        from main import app # Your FastAPI app instance
        from dependencies import get_common_dependencies # A common dependency function for auth/db/data_manager
        from datamanager.database import get_db # Your database session dependency
        from datamanager.db_dependencies import get_data_manager # Your data manager dependency
        from datamanager.data_manager_SQLAlchemy import SQLAlchemyDataManager # The actual class you are mocking

        # Yield these imported objects. This makes them available to other fixtures
        # that depend on 'set_test_env'.
        yield app, get_common_dependencies, get_db, get_data_manager, SQLAlchemyDataManager

    # After the yield, the 'with' block exits, and os.environ is automatically restored
    # to its state before the patch.


@pytest.fixture(scope="module")
def app_instance(set_test_env):
    """Provides the FastAPI app instance, imported with test environment variables."""
    app_obj, _, _, _, _ = set_test_env # Unpack the yielded values
    return app_obj

@pytest.fixture(scope="module")
def common_dependencies_func(set_test_env):
    """Provides the get_common_dependencies function, imported with test env."""
    _, common_deps_func, _, _, _ = set_test_env
    return common_deps_func

@pytest.fixture(scope="module")
def get_db_func(set_test_env):
    """Provides the get_db function, imported with test env."""
    _, _, db_func, _, _ = set_test_env
    return db_func

@pytest.fixture(scope="module")
def get_data_manager_func(set_test_env):
    """Provides the get_data_manager function, imported with test env."""
    _, _, _, data_manager_func, _ = set_test_env
    return data_manager_func

@pytest.fixture(scope="module")
def SQLAlchemyDataManager_class(set_test_env):
    """Provides the SQLAlchemyDataManager class, imported with test env."""
    _, _, _, _, cls = set_test_env
    return cls


@pytest.fixture(scope="module")
def test_client(app_instance):
    """Create a test client for the app."""
    return TestClient(app_instance) # TestClient is used to simulate requests to the app


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
    # Use spec=Session for stricter mocking, ensuring mock_db has Session's methods
    return MagicMock(spec=Session)


@pytest.fixture(scope="module")
def mock_data_manager(SQLAlchemyDataManager_class):
    """Create a mock data manager.
        Mimic the API (Interface): The mock will only allow access to attributes and methods
        that exist on the SQLAlchemyDataManager class
    """
    # Use the SQLAlchemyDataManager_class obtained from set_test_env as the spec
    return MagicMock(spec=SQLAlchemyDataManager_class)


@pytest.fixture(scope="module")
def setup_common_dependencies_override(
    app_instance, common_dependencies_func, mock_auth_user, mock_db, mock_data_manager
):
    """
    Setup dependency overrides for `get_common_dependencies`.
    It runs the mock version: `override_get_common_dependencies`,
    instead of the current function in APP `get_common_dependencies`.
    """
    async def override_get_common_dependencies():
        return mock_auth_user, mock_db, mock_data_manager

    # Store original override to ensure proper cleanup
    original_override = app_instance.dependency_overrides.get(common_dependencies_func)
    app_instance.dependency_overrides[common_dependencies_func] = override_get_common_dependencies
    yield
    # Restore original override after tests
    if original_override is None:
        del app_instance.dependency_overrides[common_dependencies_func]
    else:
        app_instance.dependency_overrides[common_dependencies_func] = original_override


@pytest.fixture(scope="module")
def setup_db_and_datamanager_override(
    app_instance, get_db_func, get_data_manager_func, mock_db, mock_data_manager
):
    """
    Overrides FastAPI's get_db and get_data_manager dependencies
    to return mock objects.
    """
    # Store original dependencies to restore them later
    original_get_db_override = app_instance.dependency_overrides.get(get_db_func)
    original_get_data_manager_override = app_instance.dependency_overrides.get(get_data_manager_func)

    # Override the dependencies with functions that return our mocks
    app_instance.dependency_overrides[get_db_func] = lambda: mock_db
    app_instance.dependency_overrides[get_data_manager_func] = lambda: mock_data_manager

    yield # This allows the tests to run

    # Clean up: Restore original dependencies after all tests in the module are done
    if original_get_db_override is None:
        del app_instance.dependency_overrides[get_db_func]
    else:
        app_instance.dependency_overrides[get_db_func] = original_get_db_override

    if original_get_data_manager_override is None:
        del app_instance.dependency_overrides[get_data_manager_func]
    else:
        app_instance.dependency_overrides[get_data_manager_func] = original_get_data_manager_override


@pytest.fixture
def user_data():
    """
        Sample user data for testing. This dictionary serves as a convenient and consistent set of input data.
        Default scope="function" as no specified: it will be executed before every single test function.
        Changes in other functions will not affect subsequent test functions because each test gets its own fresh copy.
    """
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
    """
        Create a mock user model from user data.
        Default scope="function" as no specified.
        This means mock_user will be created before every test function that requests it
        The result of instantiating UserNoPwdPydantic with the sample data is then returned by the mock_user fixture.
    """
    return UserNoPwdPydantic(**user_data)