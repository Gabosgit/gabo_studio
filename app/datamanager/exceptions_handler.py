from functools import wraps

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from app.datamanager.exception_classes import (
    ResourceNotFoundException,
    ResourceUserMismatchException, ResourcesMismatchException, InvalidContractException
)
from sqlalchemy.exc import IntegrityError
from psycopg2.errors import UniqueViolation


# Custom exception handlers (application-wide)
def register_exception_handlers(app: FastAPI):
    @app.exception_handler(ResourceNotFoundException)
    async def resource_not_found_exception_handler(request: Request, exc: ResourceNotFoundException):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": str(exc)},
        )

    @app.exception_handler(ResourceUserMismatchException)
    async def resource_user_mismatch_found_exception_handler(request: Request, exc: ResourceUserMismatchException):
        print(exc)
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"message": str(exc)}
        )

    @app.exception_handler(ResourcesMismatchException)
    async def resources_mismatch_found_exception_handler(request: Request, exc: ResourcesMismatchException):
        print(exc)
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"message": str(exc)}
        )

    @app.exception_handler(InvalidContractException)
    async def invalid_contract_exception_handler(request: Request, exc: InvalidContractException):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"message": str(exc)}
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):
        errors = exc.errors()
        print(f"Pydantic Validation Error: {errors}")
        return JSONResponse(
            status_code=422,
            content={"detail": f"{errors}"}
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        if isinstance(exc.orig, UniqueViolation):
            return JSONResponse(
                status_code=400,
                content={"detail": "Username or email already exists"},
            )
        else:
            # Handle other types of IntegrityError if needed
            return JSONResponse(
                status_code=500,
                content={"detail": "Database integrity error"},
            )


def handle_exceptions(func):
    @wraps(func)
    async def decorator(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ResourceNotFoundException as e:  # Catch the ResourceNotFoundException
            print(f"{e}\n"
                  f"ResourceNotFoundException")
            raise e  # Re-raise it, to be handled by the @app.exception_handler
        except ResourceUserMismatchException as e:
            print(f"{e}\n"
                  f"ResourceUserMismatchException")
            raise e
        except ResourcesMismatchException as e:
            print(f"{e}\n"
                  f"ResourcesMismatchException")
            raise e
        except InvalidContractException as e:
            print(f"{e}\n"
                  f"InvalidContractException")
            raise e
        except IntegrityError as e:
            print(f"{e}\n"
                  f"IntegrityError: Attempt has been made to enter a value that already exists in the database as a unique value.")
            raise e
        except ValidationError as e:
            print(f"{e}\n"
                  f"ValidationError")
            raise e
        except SQLAlchemyError as e:
            print(f"{e}\n"
                  f"Database error: SQLAlchemyError / Invalid value")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: Invalid value"
            )
        except Exception as e:
            print(f"{e}\n"
                  f"Unexpected exception")  # Log the exception.
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    return decorator
