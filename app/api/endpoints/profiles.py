""" PROFILE ROUTES """
from fastapi import Depends, APIRouter
from typing import Annotated
from sqlalchemy.orm import Session

from app.datamanager.data_manager_SQLAlchemy import SQLAlchemyDataManager
from app.datamanager.database import get_db
from app.datamanager.db_dependencies import get_data_manager
from app.datamanager.exceptions_handler import handle_exceptions
from app.api.dependencies import get_common_dependencies
from app.schemas.pydantic_models import ProfilePydantic, ProfileUpdatePydantic

# --- Create APIRouter instance ---
router = APIRouter(tags=["Profiles"])

@router.post("/profile")
@handle_exceptions
async def create_profile(
    profile_data: ProfilePydantic,
    common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    """
    :param profile_data: data from request validated with ProfilePydantic model
    :param common_dependencies: current_user, data_manager, db
    :return: id new profiler or HTTPException
    """
    current_user, db, data_manager = common_dependencies
    id_profile = data_manager.create_profile(profile_data, current_user.id, db)
    return {"profile_id": id_profile}


@router.get("/profile/{profile_id}")
@handle_exceptions
async def get_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    data_manager: SQLAlchemyDataManager = Depends(get_data_manager)
):
    """
    :param profile_id: from patch request int
    :param db: database
    :param data_manager: Imported to call the get_profile() class method
    :return: profile data or HTTPException
    """
    profile_dict = data_manager.get_profile_by_id(profile_id, db)
    return profile_dict


@router.put("/profile/{profile_id}")
@handle_exceptions
async def update_profile(
    profile_id: int,
    profile_data: ProfileUpdatePydantic,
    common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    """
        :param profile_id: from path query
        :param profile_data: data from request validated with ProfilePydantic model
        :param common_dependencies: current_user, data_manager, db
        :return: updated profile data or HTTPException
        """

    current_user, db, data_manager = common_dependencies
    updated_profile_data = data_manager.update_profile(profile_id, profile_data, current_user.id, db)
    return updated_profile_data


@router.delete("/profile/{profile_id}", response_model=dict)
@handle_exceptions
async def delete_profile(
        profile_id: int,
        common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    """
    :param common_dependencies: current_user, data_manager, db
    :param profile_id: from path query
    :return: successfully message or HTTPException
    """
    current_user, db, data_manager = common_dependencies
    data_manager.delete_profile(profile_id, current_user.id, db)
    return {"message": "Profile deleted successfully"}