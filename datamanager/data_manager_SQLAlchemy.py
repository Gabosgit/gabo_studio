"""
    Data manager for SQLAlchemy
"""

import sqlalchemy
from fastapi import HTTPException, status
from pydantic import HttpUrl

from datamanager.data_manager_interface import DataManagerInterface
from sqlalchemy.orm import Session
from typing import Optional
from sqlalchemy import exc  # Import exception handling
from .models import User, Profile, Contract, Event, Accommodation
from pydantic_models import UserAuthPydantic, ProfilePydantic, ContractPydantic, UserCreatePydantic, UserNoPwdPydantic, \
    EventPydantic, AccommodationPydantic, UserUpdatePydantic, ProfileUpdatePydantic, ContractUpdatePydantic, \
    EventUpdatePydantic, AccommodationUpdatePydantic
from datamanager.exception_classes import (ProfileNotFoundException, ProfileUserMismatchException, DatabaseError,
                                           ContractNotFoundException,
                                           ContractUserMismatchException, EventNotFoundException,
                                           EventUserMismatchException, AccommodationNotFoundException,
                                           UserNotFoundException)
from sqlalchemy.exc import SQLAlchemyError


class SQLAlchemyDataManager(DataManagerInterface):
    def __init__(self, session: Session):
        self.session = session

    # User related
    def create_user(self, user_data: UserCreatePydantic) -> int:
        """
            Creates a new user and returns the user ID.
            Validate the input data with UserCreatePydantic
            :param user_data: from query body
            :return: id created user
        """
        print("anything")
        from Oauth2 import get_password_hash # Imported here to avoid loop
        try:
            hashed_pwd = get_password_hash(user_data.password)  # Hash the password
            new_user = User(
                username=user_data.username,
                type_of_entity=user_data.type_of_entity,
                password=hashed_pwd,  # Use the hashed password
                name=user_data.name,
                surname=user_data.surname,
                email_address=user_data.email_address,
                phone_number=user_data.phone_number,
                vat_id=user_data.vat_id,
                bank_account=user_data.bank_account,
                is_active=user_data.is_active,
                deactivation_date=user_data.deactivation_date
            )
            self.session.add(new_user)
            self.session.commit()
            return new_user.iy

        # IntegrityError is a reporting from SQLAlchemy
        except exc.IntegrityError:  # Handle unique constraint violations EX: username or email already exists
            self.session.rollback()
            raise ValueError(f"Username '{user_data.username}' or email '{user_data.email_address}' already exists.") # Or other exception.
        except KeyError as e: # Handle missing keys
            self.session.rollback()
            print(f"Missing key in user_data: {e}")
            raise ValueError(f"Missing key in user_data: {e}")
        except Exception as e: # Handle all other errors.
            self.session.rollback()
            print(f"An unexpected error occurred: {e}")
            raise ValueError(f"An unexpected error occurred: {e}")


    def get_user_by_id(self, user_id: int, db: Session) -> Optional[UserNoPwdPydantic]:
        """
            Retrieves a user by id, excluding the hashed password.
            Return a UserNoPwdPydantic object with the user infos, no password.
        """
        user = db.query(User).filter(User.id == user_id).first()

        if user:
            return UserNoPwdPydantic(
                id=user.id,
                username=user.username,
                type_of_entity=user.type_of_entity,
                name=user.name,
                surname=user.surname,
                email_address=user.email_address,
                phone_number=user.phone_number,
                vat_id=user.vat_id,
                bank_account=user.bank_account,
                is_active=user.is_active
            )
        else:
            return None


    def get_user_by_username(self, username: str, db: Session) -> Optional[UserNoPwdPydantic]:
        """
            Retrieves a user by username, excluding the hashed password.
            Return a UserNoPwdPydantic object with the user infos, no password.
        """
        user = db.query(User).filter(User.username == username).first()

        if user:
            return UserNoPwdPydantic(
                id=user.id,
                username=user.username,
                type_of_entity=user.type_of_entity,
                name=user.name,
                surname=user.surname,
                email_address=user.email_address,
                phone_number=user.phone_number,
                vat_id=user.vat_id,
                bank_account=user.bank_account,
                is_active=user.is_active
            )
        else:
            return None


    def set_user_deactivation_date(self, deactivation_date, current_user_id: int, db) -> dict:
        try:
            user = db.query(User).filter(User.id == current_user_id).first()

            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            # datetime format 2026-10-27T16:00:00
            user.deactivation_date = deactivation_date
            db.commit()
            db.refresh(user)

            return {"message": "Deactivation date successfully registered",
                    "User id": user.id,
                    "User name": user.username,
                    "deactivation date": deactivation_date
                    }

        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


    def update_user(self, user_data_to_update: UserUpdatePydantic, current_user_id: int, db):
        try:
            user = db.query(User).filter(User.id == current_user_id).first()

            if not user:
                raise UserNotFoundException(f"User with ID {current_user_id} not found.")

            # Converts Pydantic model to a dictionary.
            # Excludes any fields that were not provided (unset) in the request.
            # Uses the exclude_unset=True pydantic method
            user_data_to_update = user_data_to_update.model_dump(exclude_unset=True)
            for key, value in user_data_to_update.items():
                setattr(user, key, value)

            db.commit()
            db.refresh(user)

            user_data = self.get_user_by_id(current_user_id, db)
            return user_data

        except exc.IntegrityError:  # Handle unique constraint violations EX: username or email already exists
            db.rollback()
            raise ValueError(f"Username {user_data_to_update['username']} or email {user_data_to_update['email_address']} already exists.") # Or other exception.
        except UserNotFoundException as e:
            db.rollback()
            print(f"Database error: {e}")
            raise e
        except SQLAlchemyError as e:
            db.rollback()
            print(f"Database error: {e}")
            raise e  # Re raise the exception to be handled in the route.
        except Exception as e:
            db.rollback()
            raise e


    def delete_user(self, user_id: int) -> bool:
        """ Deletes a user. """
        pass


# Profile related
    def create_profile(self, profile_data: ProfilePydantic, current_user_id: int, db: Session):
        """
            Creates a new profile in the database.
            Validate the input data with ProfilePydantic and UserAuthPydantic
        """
        try:
            new_profile = Profile(
                user_id=current_user_id,
                name=profile_data.name,
                performance_type=profile_data.performance_type,
                description=profile_data.description,
                bio=profile_data.bio,
                social_media=[str(url) for url in profile_data.social_media] if profile_data.social_media else [], # Convert to list of strings.
                stage_plan=str(profile_data.stage_plan) if profile_data.stage_plan else None,  # Convert to string.
                tech_rider=str(profile_data.tech_rider) if profile_data.tech_rider else None,  # Convert to string.
                photos=[str(url) for url in profile_data.photos] if profile_data.photos else [], # Convert to list of strings.
                videos=[str(url) for url in profile_data.videos] if profile_data.videos else [], # Convert to list of strings.
                audios=[str(url) for url in profile_data.audios] if profile_data.audios else [], # Convert to list of strings.
                online_press=[str(url) for url in profile_data.online_press] if profile_data.online_press else [],# Convert to list of strings.
                website=str(profile_data.website) if profile_data.website else None, #Convert to string or return None.
            )
            db.add(new_profile)
            db.commit()
            db.refresh(new_profile)
            return new_profile.id
        except Exception as e:
            db.rollback()
            raise e


    def get_profile_by_id(self, profile_id: int, db: Session) -> Optional[ProfilePydantic] | None:
        """
            Retrieves a profile by ID.
            Return a dictionary with the profile infos.
        """
        profile = db.query(Profile).filter(Profile.id == profile_id).first()
        if profile:
            return ProfilePydantic(
                id=profile.id,
                name=profile.name,
                performance_type=profile.performance_type,
                description=profile.description,
                bio=profile.bio,
                social_media=profile.social_media,
                stage_plan=profile.stage_plan,
                tech_rider=profile.tech_rider,
                photos=profile.photos,
                videos=profile.videos,
                audios=profile.audios,
                online_press=profile.online_press,
                website=profile.website
            )
        else:
            return None


    def update_profile(
            self, profile_id: int,
            profile_data_to_update: ProfileUpdatePydantic,
            current_user_id,
            db: Session)\
            -> Optional[ProfileUpdatePydantic]:
        try:
            profile = db.query(Profile).filter(Profile.id == profile_id).first()

            if not profile:
                raise ProfileNotFoundException(f"Profile with ID {profile_id} not found.")

            if profile.user_id != current_user_id:
                raise ProfileUserMismatchException(
                    f"Profile with ID {profile_id} does not belong to the current user with ID {current_user_id}.")

            # Converts Pydantic model to a dictionary.
            # Excludes any fields that were not provided (unset) in the request.
            # Uses the exclude_unset=True pydantic method
            profile_data_to_update = profile_data_to_update.model_dump(exclude_unset=True)

            # Convert HttpUrl objects to strings
            # If a value is an HttpUrl object, it's converted to a string using str(value).
            # If a value is a list of HttpUrl objects, the list is converted to a list of strings.
            for key, value in profile_data_to_update.items():
                if isinstance(value, HttpUrl):
                    profile_data_to_update[key] = str(value)
                elif isinstance(value, list) and all(isinstance(item, HttpUrl) for item in value):
                    profile_data_to_update[key] = [str(item) for item in value]

            # Updates the values of the corresponding fields
            for key, value in profile_data_to_update.items():
                setattr(profile, key, value)

            db.commit()
            db.refresh(profile)

            profile_data = self.get_profile_by_id(profile_id, db)
            return profile_data

        except (ProfileNotFoundException, ProfileUserMismatchException) as e:
            db.rollback()
            print(e)
            raise e  # Re raise the exception to be handled in the route.

        except SQLAlchemyError as e:
            db.rollback()
            print(f"Database error: {e}")
            raise e  # Re raise the exception to be handled in the route.

        except Exception as e:
            db.rollback()
            print(f"General error: {e}")
            raise e  # Re raise the exception to be handled in the route.


    def delete_profile(self, profile_id: int, current_user_id: int, db: Session) -> bool:
        try:
            profile = db.query(Profile).filter(Profile.id == profile_id).first()

            if not profile:
                raise ProfileNotFoundException(f"Profile with ID {profile_id} not found.")

            if profile.user_id != current_user_id:
                raise ProfileUserMismatchException(
                    f"Profile with ID {profile_id} does not belong to the current user with ID {current_user_id}.")

            self.session.delete(profile)
            self.session.commit()
            return True

        except (ProfileNotFoundException, ProfileUserMismatchException) as e:
            print(e)
            raise e  # Re raise the exception to be handled in the route.
        except sqlalchemy.exc.SQLAlchemyError as e:  # Specific database error.
            self.session.rollback()
            print(f"Database error deleting profile: {e}")
            raise DatabaseError(f"Database error occurred: {e}")  # Custom exception.
        except Exception as e:
            self.session.rollback()
            print(f"Unexpected error deleting profile: {e}")
            raise DatabaseError(f"An unexpected error occurred: {e}")


# Contract related
    def create_contract(self, contract_data: ContractPydantic, current_user: UserAuthPydantic, db: Session):
        """
        Creates a new contract in the database.
        Validate input data with ContractPydantic and UserAuthPydantic
        """
        try:
            new_contract = Contract(
                name=contract_data.name, # Contract name
                offeror_id=current_user.id, # Current user create the contract as offeror
                offeree_id=contract_data.offeree_id,
                total_fee=contract_data.total_fee,
                currency_code=contract_data.currency_code,
                upon_signing=contract_data.upon_signing,  # % of total
                upon_completion=contract_data.upon_completion, # % rest
                payment_method=contract_data.payment_method,
                travel_expenses=contract_data.travel_expenses,
                accommodation_expenses=contract_data.accommodation_expenses,
                other_expenses=contract_data.other_expenses
            )
            db.add(new_contract)
            db.commit()
            db.refresh(new_contract)
            return new_contract.id
        except Exception as e:
            db.rollback()
            raise e


    def get_contract_by_id(self, contract_id: int, current_user_id: int, db: Session) -> Optional[ContractPydantic]:
        """
            Retrieves a contract by ID.
            Return a dictionary with the contract infos
        """
        try:
            contract = (
                db.query(Contract)
                .filter(Contract.id == contract_id)
                .filter((Contract.offeror_id == current_user_id) | (Contract.offeree_id == current_user_id))
                .first()
            )
            if not contract:
                raise ContractNotFoundException(f"Contract with ID {contract_id} for current user with ID {current_user_id} not found.")

            if contract.offeror_id != current_user_id:
                raise ContractUserMismatchException(
                    f"Contract with ID {contract_id} does not belong to the current user with ID {current_user_id}.")

            return ContractPydantic(
                id=contract.id,
                created_at=contract.created_at,
                name=contract.name,
                offeror_id=contract.offeror_id,
                offeree_id=contract.offeree_id,
                total_fee=contract.total_fee,
                currency_code=contract.currency_code,
                upon_signing=contract.upon_signing,
                upon_completion=contract.upon_completion,
                payment_method=contract.payment_method,
                travel_expenses=contract.travel_expenses,
                accommodation_expenses=contract.accommodation_expenses,
                other_expenses=contract.other_expenses,
                disabled=contract.disabled,
                disabled_at=contract.disabled_at,
                signed_at=contract.signed_at,
                delete_at=contract.delete_at
            )
        except (ContractNotFoundException, ContractUserMismatchException) as e:
            print(e)
            raise e  # Re raise the exception to be handled in the route.

        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            raise e  # Re raise the exception to be handled in the route.

        except Exception as e:
            print(f"General error: {e}")
            raise e  # Re raise the exception to be handled in the route.


    def update_contract(
            self, contract_id: int,
            contract_data_to_update: ContractUpdatePydantic,
            current_user_id, db: Session) \
            -> Optional[ContractUpdatePydantic]:
        try:
            contract = db.query(Contract).filter(Contract.id == contract_id).first()

            if not contract:
                raise ContractNotFoundException(f"Contract with ID {contract_id} not found.")

            if contract.offeror_id != current_user_id:
                raise ContractUserMismatchException(
                    f"Contract with ID {contract_id} does not belong to the current user with ID {current_user_id}.")

            # Converts Pydantic model to a dictionary.
            # Excludes any fields that were not provided (unset) in the request.
            # Uses the exclude_unset=True pydantic method
            contract_data_to_update = contract_data_to_update.model_dump(exclude_unset=True)

            # Updates the values of the corresponding fields
            for key, value in contract_data_to_update.items():
                setattr(contract, key, value)

            db.commit()
            db.refresh(contract)

            contract_data = self.get_contract_by_id(contract_id, current_user_id, db)
            return contract_data

        except (ContractNotFoundException, ContractUserMismatchException) as e:
            db.rollback()
            print(e)
            raise e  # Re raise the exception to be handled in the route.

        except SQLAlchemyError as e:
            db.rollback()
            print(f"Database error: {e}")
            raise e  # Re raise the exception to be handled in the route.

        except Exception as e:
            db.rollback()
            print(f"General error: {e}")
            raise e  # Re raise the exception to be handled in the route.

    def get_contract_events(
            self, contract_id: int,
            current_user_id: int,
            db: Session) -> list:
        """
        :param contract_id: to get events
        :param current_user_id: to check if the contract belongs to the user
        :param db: database
        :return: tuple with event ids
        """
        try:
            contract = db.query(Contract).filter(Contract.id == contract_id).first()
            events_in_contract: list = db.query(Event.id).filter(Event.contract_id == contract_id).all()

            if not contract:
                raise ContractNotFoundException(f"Contract with ID {contract_id} not found.")

            if contract.offeror_id != current_user_id:
                raise ContractUserMismatchException(
                    f"Contract with ID {contract_id} does not belong to the current user with ID {current_user_id}.")

            if not events_in_contract:
                raise EventNotFoundException(f"No event found for the contract with ID {contract_id}.")

            # Extract the IDs from the list of tuples in result events_in_contract
            return [event_id[0] for event_id in events_in_contract]

        except (EventNotFoundException, ContractNotFoundException, ContractUserMismatchException) as e:
            print(e)
            raise e  # Re raise the exception to be handled in the route.

        except SQLAlchemyError as e:
            db.rollback()
            print(f"Database error: {e}")
            raise e  # Re raise the exception to be handled in the route.

        except Exception as e:
            db.rollback()
            print(f"General error: {e}")
            raise e  # Re raise the exception to be handled in the route.


    def soft_delete_contract(self, contract_id: int) -> bool:
        """ Deletes a contract. """
        pass


# Event related
    def create_event(self, event_data: EventPydantic, current_user_id: int, db: Session):
        """
            Creates a new event in the database.
            Validate the input data with EventPydantic and UserAuthPydantic
            Returns the new event ID.
        """
        try:
            new_event = Event(
                name=event_data.name,
                contract_id=event_data.contract_id,
                profile_offeror_id=event_data.profile_offeror_id,
                profile_offeree_id=event_data.profile_offeree_id,
                contact_person=event_data.contact_person,
                contact_phone=event_data.contact_phone,
                date=event_data.date,
                duration=event_data.duration,
                start=event_data.start,
                end=event_data.end,
                arrive=event_data.arrive,
                stage_set=event_data.stage_set,
                stage_check=event_data.stage_check,
                catering_open=event_data.catering_open,
                catering_close=event_data.catering_close,
                meal_time=event_data.meal_time,
                meal_location_name=event_data.meal_location_name,
                meal_location_address=event_data.meal_location_address,
                accommodation_id=event_data.accommodation_id
            )
            db.add(new_event)
            db.commit()
            db.refresh(new_event)
            return new_event.id
        except KeyError as e:  # Handle missing keys
            self.session.rollback()
            print(f"Missing key in event_data: {e}")
            raise ValueError(f"Missing key in event_data: {e}")
        except Exception as e:  # Handle all other errors.
            self.session.rollback()
            print(f"An unexpected error occurred: {e}")
            raise ValueError(f"An unexpected error occurred: {e}")


    def get_event_by_id(self, event_id: int, current_user_id: int, db: Session) -> Optional[EventPydantic]:
        """ Retrieves an event by ID. """
        try:
            event = db.query(Event).filter(Event.id == event_id).first()

            if not event:
                raise EventNotFoundException(f"Event with ID {event_id} not found.")

            offeror_id = db.query(Contract.offeror_id).filter(Contract.id == event.contract_id)
            offeror_id = offeror_id[0][0]

            if offeror_id != current_user_id:
                raise EventUserMismatchException(
                    f"Event with ID {event_id} does not belong to the current user with ID {current_user_id}.")

            return EventPydantic(
                id=event.id,
                created_at=event.created_at,
                name=event.name,
                contract_id=event.contract_id,
                profile_offeror_id=event.profile_offeror_id,
                profile_offeree_id=event.profile_offeree_id,
                contact_person=event.contact_person,
                contact_phone=event.contact_phone,
                date=event.date,
                duration=event.duration,
                start=event.start,
                end=event.end,
                arrive=event.arrive,
                stage_set=event.stage_set,
                stage_check=event.stage_check,
                catering_open=event.catering_open,
                catering_close=event.catering_close,
                meal_time=event.meal_time,
                meal_location_name=event.meal_location_name,
                meal_location_address=event.meal_location_address,
                accommodation_id=event.accommodation_id
            )
        except (EventNotFoundException, EventUserMismatchException) as e:
            print(e)
            raise e

        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            raise e  # Re raise the exception to be handled in the route.

        except Exception as e:
            print(f"General error: {e}")
            raise e  # Re raise the exception to be handled in the route.


    def update_event(
            self, event_id: int,
            event_data_to_update: EventUpdatePydantic,
            current_user_id: int,
            db: Session) -> Optional[EventPydantic]:
        """ Updates an event. """
        try:
            event = db.query(Event).filter(Event.id == event_id).first()

            if not event:
                raise EventNotFoundException(f"Event with ID {event_id} not found.")

            offeror_id = db.query(Contract.offeror_id).filter(Contract.id == event.contract_id)
            offeror_id = offeror_id[0][0]

            if offeror_id != current_user_id:
                raise EventUserMismatchException(
                    f"Event with ID {event_id} does not belong to the current user with ID {current_user_id}.")

            # Converts Pydantic model to a dictionary.
            # Excludes any fields that were not provided (unset) in the request.
            # Uses the exclude_unset=True pydantic method
            contract_data_to_update = event_data_to_update.model_dump(exclude_unset=True)

            # Updates the values of the corresponding fields
            for key, value in contract_data_to_update.items():
                setattr(event, key, value)

            db.commit()
            db.refresh(event)

            event_data = self.get_event_by_id(event_id, current_user_id, db)
            return event_data

        except (EventNotFoundException, EventUserMismatchException) as e:
            db.rollback()
            print(e)
            raise e # Re raise the exception to be handled in the route.

        except SQLAlchemyError as e:
            db.rollback()
            print(f"Database error: {e}")
            raise e  # Re raise the exception to be handled in the route.

        except Exception as e:
            db.rollback()
            print(f"General error: {e}")
            raise e  # Re raise the exception to be handled in the route.


    def delete_event(self, event_id: int, current_user_id: int, db: Session) -> bool:
        try:
            event = db.query(Event).filter(Event.id == event_id).first()

            if not event:
                raise EventNotFoundException(f"Event with ID {event_id} not found.")

            offeror_id = db.query(Contract.offeror_id).filter(Contract.id == event.contract_id)
            offeror_id = offeror_id[0][0]

            if offeror_id != current_user_id:
                raise EventUserMismatchException(
                    f"Event with ID {event_id} does not belong to the current user with ID {current_user_id}.")

            self.session.delete(event)
            self.session.commit()
            return True

        except (EventNotFoundException, EventUserMismatchException) as e:
            print(e)
            raise e  # Re raise the exception to be handled in the route.
        except sqlalchemy.exc.SQLAlchemyError as e:  # Specific database error.
            self.session.rollback()
            print(f"Database error deleting event: {e}")
            raise DatabaseError(f"Database error occurred: {e}")  # Custom exception.
        except Exception as e:
            self.session.rollback()
            print(f"Unexpected error deleting event: {e}")
            raise DatabaseError(f"An unexpected error occurred: {e}")


# Accommodation related
    def create_accommodation(self, accommodation_data: AccommodationPydantic, db: Session) -> int:
        """
            Creates new accommodation in the database.
            Validate the input data with AccommodationPydantic
            Returns the new accommodation ID.
        """
        try:
            new_accommodation = Accommodation(
                name=accommodation_data.name,
                contact_person=accommodation_data.contact_person,
                address=accommodation_data.address,
                telephone_number=accommodation_data.telephone_number,
                email=accommodation_data.email,
                website=str(accommodation_data.website) if accommodation_data.website else None, # Convert to string or return None.
                url=str(accommodation_data.url) if accommodation_data.url else None, # Convert to string or return None.
                check_in=accommodation_data.check_in,
                check_out=accommodation_data.check_out
            )
            db.add(new_accommodation)
            db.commit()
            db.refresh(new_accommodation)
            return new_accommodation.id
        except Exception as e:
            db.rollback()
            raise e


    def get_accommodation_by_id(self, accommodation_id: int, db: Session) -> Optional[AccommodationPydantic]:
        """ Retrieves accommodation by ID. """
        try:
            accommodation = db.query(Accommodation).filter(Accommodation.id == accommodation_id).first()

            if not accommodation:
                raise AccommodationNotFoundException(f"Accommodation with ID {accommodation_id} not found.")

            return AccommodationPydantic(
                id=accommodation.id,
                name=accommodation.name,
                contact_person=accommodation.contact_person,
                address=accommodation.address,
                telephone_number=accommodation.telephone_number,
                email=accommodation.email,
                website=accommodation.website,
                url=accommodation.url,
                check_in=accommodation.check_in,
                check_out=accommodation.check_out
            )
        except AccommodationNotFoundException as e:
            print(e)
            raise e

        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            raise e  # Re raise the exception to be handled in the route.

        except Exception as e:
            print(f"General error: {e}")
            raise e  # Re raise the exception to be handled in the route.


    def update_accommodation(
            self, accommodation_id: int,
            accommodation_data_to_update: AccommodationUpdatePydantic,
            db) -> AccommodationPydantic:
        """ Updates accommodation. """
        try:
            accommodation = db.query(Accommodation).filter(Accommodation.id == accommodation_id).first()

            if not accommodation:
                raise AccommodationNotFoundException(f"Accommodation with ID {accommodation_id} not found.")

            # Converts Pydantic model to a dictionary.
            # Excludes any fields that were not provided (unset) in the request.
            # Uses the exclude_unset=True pydantic method
            accommodation_data_to_update = accommodation_data_to_update.model_dump(exclude_unset=True)

            # Convert HttpUrl objects to strings
            # If a value is an HttpUrl object, it's converted to a string using str(value).
            # If a value is a list of HttpUrl objects, the list is converted to a list of strings.
            for key, value in accommodation_data_to_update.items():
                if isinstance(value, HttpUrl):
                    accommodation_data_to_update[key] = str(value)
                elif isinstance(value, list) and all(isinstance(item, HttpUrl) for item in value):
                    accommodation_data_to_update[key] = [str(item) for item in value]

            # Updates the values of the corresponding fields
            for key, value in accommodation_data_to_update.items():
                setattr(accommodation, key, value)

            db.commit()
            db.refresh(accommodation)

            accommodation_data = self.get_accommodation_by_id(accommodation_id, db)
            return accommodation_data

        except (AccommodationNotFoundException) as e:
            db.rollback()
            print(e)
            raise e # Re raise the exception to be handled in the route.

        except SQLAlchemyError as e:
            db.rollback()
            print(f"Database error: {e}")
            raise e  # Re raise the exception to be handled in the route.

        except Exception as e:
            db.rollback()
            print(f"General error: {e}")
            raise e  # Re raise the exception to be handled in the route.


    def delete_accommodation(self, accommodation_id: int, db) -> bool:
        """ Deletes accommodation. """
        try:
            accommodation = db.query(Accommodation).filter(Accommodation.id == accommodation_id).first()

            if not accommodation:
                raise AccommodationNotFoundException(f"Accommodation with ID {accommodation_id} not found.")
            self.session.delete(accommodation)
            self.session.commit()
            return True

        except (AccommodationNotFoundException) as e:
            self.session.rollback()
            print(e)
            raise e  # Re raise the exception to be handled in the route.
        except sqlalchemy.exc.SQLAlchemyError as e:  # Specific database error.
            self.session.rollback()
            print(f"Database error deleting event: {e}")
            raise DatabaseError(f"Database error occurred: {e}")  # Custom exception.
        except Exception as e:
            self.session.rollback()
            print(f"Unexpected error deleting event: {e}")
            raise DatabaseError(f"An unexpected error occurred: {e}")