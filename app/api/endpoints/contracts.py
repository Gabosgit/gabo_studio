""" CONTRACT ROUTES """

from fastapi import Depends, APIRouter, HTTPException, status
from typing import Annotated
from app.datamanager.exceptions_handler import handle_exceptions
from app.api.dependencies import get_common_dependencies
from app.schemas.pydantic_models import ContractCreatePydantic, ContractUpdatePydantic

# --- Create APIRouter instance ---
router = APIRouter(tags=["Contracts"])

@router.post("/contract")
@handle_exceptions
async def create_contract(
    contract_data: ContractCreatePydantic,
    common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    """
    :param contract_data: data from body request validated with ContractPydantic model
    :param common_dependencies: current_user, data_manager, db
    :return: id new contract or HTTPException
    """
    current_user, db, data_manager = common_dependencies
    id_contract = data_manager.create_contract(contract_data, current_user.id, db)
    return {"contract_id": id_contract}


@router.get("/contract/{contract_id}")
@handle_exceptions
async def get_contract(
    contract_id: int,
    common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    """
    :param contract_id: from path request
    :param common_dependencies: current_user, data_manager, db
    :return: contract data and events in contract or HTTPException
    """
    current_user, db, data_manager = common_dependencies
    contract_dict = data_manager.get_contract_by_id(contract_id, current_user.id, db)
    events_in_contract = data_manager.get_contract_events(contract_id, current_user.id, db)
    #return contract_dict
    return {"contract_data": contract_dict, "contract_event_ids": events_in_contract}


@router.put("/contract/{contract_id}")
@handle_exceptions
async def update_contract(
    contract_id: int,
    contract_data: ContractUpdatePydantic,
    common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    """
    :param contract_id: from path query
    :param contract_data: from body request
    :param common_dependencies: current_user, data_manager, db
    :return: updated data or HTTPException
    """
    current_user, db, data_manager = common_dependencies
    update_contract_data = data_manager.update_contract(contract_id, contract_data, current_user.id, db)
    return update_contract_data


@router.patch("/contract/{contract_id}")
@handle_exceptions
async def disable_contract(
    contract_id: int,
    common_dependencies: Annotated[tuple, Depends(get_common_dependencies)],
    disable_at
):
    """
    :param contract_id: from path query
    :param disable_at: from query parameter
    :param common_dependencies: current_user, data_manager, db
    :return: confirmation dict response or HTTPException
    """
    current_user, db, data_manager = common_dependencies
    response = data_manager.disable_contract(contract_id, disable_at, current_user.id, db)
    return response


@router.get("/contract/itinerary")
@handle_exceptions
async def show_itinerary():
    """

    :return:
    """
    return {"message": "Shows Itinerary"}


@router.get("/contract/{contract_id}/events")
@handle_exceptions
async def get_contract_events_id_and_name(
    contract_id: int,
    common_dependencies: Annotated[tuple, Depends(get_common_dependencies)]
):
    """

    :param contract_id:
    :param common_dependencies:
    :return:
    """
    current_user, db, data_manager = common_dependencies
    events = data_manager.get_contract_events_id_and_name(contract_id, db)
    return {"contract_events": events}