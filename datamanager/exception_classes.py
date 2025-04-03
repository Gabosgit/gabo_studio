
class ResourceNotFoundException(Exception):
    """Exception raised when a requested resource is not found."""
    def __init__(self, resource_name: str, resource_id: int):
        self.resource_name = resource_name,
        self.resource_id = resource_id
        super().__init__(f"{resource_name} with ID {resource_id} not found.")

class ResourceUserMismatchException(Exception):
    """Exception raised by a requested resource Mismatch."""
    def __init__(self, resource_name: str, resource_id: int, user_id: int):
        self.resource_name = resource_name,
        self.resource_id = resource_id,
        self.user_id = user_id
        super().__init__(f"{resource_name} with ID {resource_id} does not belong to the current user with ID {user_id}.")

class ResourcesMismatchException(Exception):
    """Exception raised by a requested resource Mismatch."""
    def __init__(self, resource_name_A: str, resource_name_B: str, resource_id_B: int):
        self.resource_name_A = resource_name_A,
        self.resource_name_B = resource_name_B,
        self.resource_id_B = resource_id_B
        super().__init__(f"No {resource_name_A} for {resource_name_B} with ID {resource_id_B}.")




class UserNotFoundException(Exception):
    """Exception raised when an user with the given ID is not found."""
    pass

class ProfileNotFoundException(Exception):
    """Exception raised when a profile with the given ID is not found."""
    pass

class ProfileUserMismatchException(Exception):
    """Exception raised when a profile does not belong to the given user."""
    pass

class DatabaseError(Exception):
    """Custom exception for database-related errors."""
    pass


class ContractNotFoundException(Exception):
    """Exception raised when a contract with the given ID is not found."""
    pass

class ContractUserMismatchException(Exception):
    """Exception raised when a contract does not belong to the given user."""
    pass

class EventNotFoundException(Exception):
    """Exception raised when no event is found."""

class EventUserMismatchException(Exception):
    """Exception raised when an event does not belong to the given user."""

class AccommodationNotFoundException(Exception):
    """Exception raised when no accommodation is found."""