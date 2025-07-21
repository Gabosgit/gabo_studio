""" EVENT ROUTES """
from app.schemas.pydantic_models import EventPydantic, EventUpdatePydantic

""" USER ROUTES """
from fastapi import Depends, APIRouter
from typing import Annotated

from app.datamanager.exceptions_handler import handle_exceptions
from app.api.dependencies import get_common_dependencies


# --- Create APIRouter instance ---
router = APIRouter(tags=["Events"])


@router.post("/event")
@handle_exceptions
async def create_event(
    event_data: EventPydantic,
    common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    """
    :param event_data: from request body
    :param common_dependencies: current_user, data_manager, db
    :return: id created event or HTTPException
    """
    current_user, db, data_manager = common_dependencies
    id_event = data_manager.create_event(event_data, current_user, db)
    return {"event_id": id_event}


@router.get("/event/{event_id}")
@handle_exceptions
async def get_event(
    event_id: int,
    common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    """
    :param event_id: from path query
    :param common_dependencies: data_base, current_user, db
    :return: event data or HTTPException
    """
    current_user, db, data_manager = common_dependencies
    event_data = data_manager.get_event_by_id(event_id, current_user.id, db).model_dump()
    if event_data['accommodation_id']:
        accommodation_data = data_manager.get_accommodation_by_id(event_data['accommodation_id'] ,db).model_dump()
        event_data["accommodation"] = accommodation_data
    return event_data


@router.put("/event/{event_id}")
@handle_exceptions
async def update_event(
        event_id: int,
        event_data_to_update: EventUpdatePydantic,
        common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    """
    :param event_id: from path query
    :param event_data_to_update: body query
    :param common_dependencies: data_manager, current_user, db
    :return: updated event data or HTTPException
    """
    current_user, db, data_manager = common_dependencies
    updated_event_data = data_manager.update_event(event_id, event_data_to_update, current_user.id, db)
    return updated_event_data


@router.delete("/event/{event_id}")
@handle_exceptions
async def delete_event(
        event_id: int,
        common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    """
    :param event_id: from path query
    :param common_dependencies: data_manager, current_user, db
    :return: confirmation message or HTTPException
    """
    current_user, db, data_manager = common_dependencies
    data_manager.delete_event(event_id, current_user.id, db)
    return {"message": "Event deleted successfully"}