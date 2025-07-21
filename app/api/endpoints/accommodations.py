""" ACCOMMODATION ROUTES """
from fastapi import Depends, APIRouter
from typing import Annotated
from sqlalchemy.orm import Session

from app.datamanager.data_manager_SQLAlchemy import SQLAlchemyDataManager
from app.datamanager.database import get_db
from app.datamanager.db_dependencies import get_data_manager
from app.datamanager.exceptions_handler import handle_exceptions
from app.api.dependencies import get_common_dependencies
from app.schemas.pydantic_models import AccommodationPydantic, AccommodationUpdatePydantic

# --- Create APIRouter instance ---
router = APIRouter(tags=["Accommodations"])



@router.post("/accommodation")
@handle_exceptions
async def create_accommodation(
    accommodation_data: AccommodationPydantic,
    db: Session = Depends(get_db),
    data_manager: SQLAlchemyDataManager = Depends(get_data_manager)
):
    """
    :param accommodation_data: from request body
    :param db: database
    :param data_manager: Imported to call create_accommodation() class method
    :return: id new accommodation or HTTPException
    """
    id_accommodation = data_manager.create_accommodation(accommodation_data, db)
    return {"accommodation_id": id_accommodation}


@router.get("/accommodation/{accommodation_id}")
@handle_exceptions
async def get_accommodation(
        accommodation_id: int,
        common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    """
    :param accommodation_id: from path query
    :param common_dependencies: data_manager, current_user, db
    :return: accommodation data or HTTPException
    """
    current_user, db, data_manager = common_dependencies
    accommodation_data = data_manager.get_accommodation_by_id(accommodation_id, db)
    return accommodation_data


@router.put("/accommodation/{accommodation_id}")
@handle_exceptions
async def update_accommodation(
        accommodation_id: int,
        accommodation_data: AccommodationUpdatePydantic,
        common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    """
    :param accommodation_id:  from path query
    :param accommodation_data: from body query
    :param common_dependencies: data_manager, current_user, db
    :return: updated accommodation data or HTTPException
    """
    current_user, db, data_manager = common_dependencies
    updated_accommodation_data = data_manager.update_accommodation(accommodation_id, accommodation_data, db)
    return updated_accommodation_data


@router.delete("/accommodation/{accommodation_id}")
@handle_exceptions
async def delete_accommodation(
        accommodation_id: int,
        common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    """
    :param accommodation_id:  from path query
    :param common_dependencies: data_manager, current_user, db
    :return: confirmation message or HTTPException
    """
    current_user, db, data_manager = common_dependencies
    data_manager.delete_accommodation(accommodation_id, db)
    return {"message": "Accommodation deleted successfully"}