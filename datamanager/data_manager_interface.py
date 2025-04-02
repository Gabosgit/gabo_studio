"""
    Defines an interface for our DataManager using Python’s abc (Abstract Base Classes) module
    The same data manager methods can be used by multiple API routes.
"""
from abc import ABC, abstractmethod
from typing import Optional

class DataManagerInterface(ABC):
    """ Defines methods for managing data entities. """

    # User related
    @abstractmethod
    def create_user(self, user_data: dict) -> int:  # Returns user ID
        """ Creates a new user. """
        pass

    @abstractmethod
    def get_user_by_id(self, user_id: int, db) -> Optional[dict]:
        """ Retrieves a user by ID. """
        pass

    @abstractmethod
    def get_user_by_username(self, username: str, db) -> Optional[dict]:
        """ Retrieves a user by username."""
        pass

    @abstractmethod
    def set_user_deactivation_date(self,deactivation_date, user_data: dict, db) -> bool:
        """ Sets user deactivation date. """
        pass

    @abstractmethod
    def update_user(self, user_data, current_user_id: int, db):
        """ Update user data. """
        pass


    @abstractmethod
    def delete_user(self, user_id: int) -> bool:
        """ Deletes a user. """
        pass

    # Profile related
    @abstractmethod
    def create_profile(self, profile_data: dict, current_user: dict, db) -> int:
        """ Creates a new profile. """
        pass

    @abstractmethod
    def get_profile_by_id(self, profile_id: int, db) -> Optional[dict]:
        """ Retrieves a profile by ID. """
        pass

    @abstractmethod
    def update_profile(self, profile_id: int, profile_data, current_user_id: int, db) -> bool:
        """ Updates a profile. """
        pass

    @abstractmethod
    def delete_profile(self, profile_id: int) -> bool:
        """ Deletes a profile. """
        pass

    # Contract related
    @abstractmethod
    def create_contract(self, contract_data: dict, current_user: dict, db) -> int:
        """ Creates a new contract. """
        pass

    @abstractmethod
    def get_contract_by_id(self, contract_id: int, current_user: dict, db) -> Optional[dict]:
        """ Retrieves a contract by ID. """
        pass

    @abstractmethod
    def update_contract(self, contract_id: int,
            contract_data_to_update,
            current_user_id: int, db) \
            -> Optional[dict]:
        """ Updates a contract. """
        pass

    @abstractmethod
    def soft_delete_contract(self, contract_id: int) -> bool:
        """ Deletes a contract. """
        pass

    # Event related
    @abstractmethod
    def create_event(self, event_data: dict, current_user: dict, db) -> int:
        """ Creates an event. """
        pass

    @abstractmethod
    def get_event(self, event_id: int) -> Optional[dict]:
        """ Retrieves an event by ID. """
        pass

    @abstractmethod
    def update_event(self, event_id: int, event_data: dict) -> bool:
        """ Updates an event. """
        pass

    @abstractmethod
    def delete_event(self, event_id: int) -> bool:
        """ Deletes an event. """
        pass

    # Accommodation related
    @abstractmethod
    def create_accommodation(self, event_data: dict, db) -> int:
        """ Creates Accommodation. """
        pass

    @abstractmethod
    def get_accommodation(self, event_id: int) -> Optional[dict]:
        """ Retrieves accommodation by ID. """
        pass

    @abstractmethod
    def update_accommodation(self, accommodation_id: int, accommodation_data: dict) -> bool:
        """ Updates accommodation. """
        pass

    @abstractmethod
    def delete_accommodation(self, accommodation_id: int) -> bool:
        """ Deletes accommodation. """
        pass

