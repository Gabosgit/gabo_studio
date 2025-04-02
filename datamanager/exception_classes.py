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