from fastapi import Depends
from sqlalchemy.orm import Session
from typing import Annotated, Tuple
from app.api.security import get_current_active_user
from app.schemas.pydantic_models import UserAuthPydantic
from app.datamanager.database import get_db
from app.datamanager.data_manager_SQLAlchemy import SQLAlchemyDataManager
from app.datamanager.db_dependencies import get_data_manager

async def get_common_dependencies(
    current_user: Annotated[UserAuthPydantic, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
    data_manager: SQLAlchemyDataManager = Depends(get_data_manager)
) -> Tuple[UserAuthPydantic, Session, SQLAlchemyDataManager]:
    return current_user, db, data_manager