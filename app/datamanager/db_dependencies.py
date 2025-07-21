"""
    Dependency to create DataManager instance
"""
from sqlalchemy.orm import Session
from fastapi import Depends
from app.datamanager.data_manager_SQLAlchemy import SQLAlchemyDataManager
from app.datamanager.database import get_db


def get_data_manager(db: Session = Depends(get_db)):
    try:
        sql_data_manager_instance = SQLAlchemyDataManager(db)
        yield sql_data_manager_instance
    except Exception:
        db.rollback()  # rollback the database.
        raise  # raise the exception, so fastapi can catch it.
    finally:
        db.close()