"""
    Data manager for SQLAlchemy
"""
from fastapi import HTTPException, status
from pydantic import HttpUrl

from datamanager.data_manager_interface import DataManagerInterface
from sqlalchemy.orm import Session
from typing import Optional
from sqlalchemy import exc, or_  # Import exception handling
from .models import User, Profile, Contract, Event, Accommodation
from pydantic_models import ProfilePydantic, ContractPydantic, UserCreatePydantic, UserNoPwdPydantic, \
    EventPydantic, AccommodationPydantic, ProfileUpdatePydantic, ContractUpdatePydantic, \
    EventUpdatePydantic, AccommodationUpdatePydantic, ContractCreatePydantic, UserAuthPydantic, TitleAndUrl, \
    ChangePasswordRequest
from datamanager.exception_classes import (ResourceNotFoundException, ResourceUserMismatchException,
                                           ResourcesMismatchException, InvalidContractException)


class SQLAlchemyDataManager(DataManagerInterface):
    def __init__(self, session: Session):
        self.session = session

### User related
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
            return new_user.id

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

    @staticmethod
    def change_password(request: ChangePasswordRequest, current_user, db: Session):
        """
            Allows a logged-in user to change their password.
            Requires the old password for verification.
        """
        # 1. Verify the old password
        from Oauth2 import verify_password, get_password_hash
        # current_user.password holds the hashed password from the DB (due to UserAuthPydantic mapping)
        if not verify_password(request.old_password, current_user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect old password."
            )

        # 2. Hash the new password
        hashed_new_password = get_password_hash(request.new_password)

        # 3. Update the user's password in the database
        # Retrieve the actual SQLAlchemy ORM object to update
        db_user = db.query(User).filter(User.username == current_user.username).first()
        if not db_user:
            # This should ideally not happen if the get_current_active_user works correctly
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found in DB.")

        db_user.password = hashed_new_password  # Update the password field
        db.add(db_user)  # Mark the object as dirty
        db.commit()  # Commit the transaction
        db.refresh(db_user)  # Refresh the instance to get updated values

        # 4. (Optional but Recommended) Invalidate current sessions/tokens
        # For JWTs, relying on expiration is common. If you need immediate invalidation,
        # you'd implement a JWT blacklist (e.g., in Redis) and check it in get_current_user.
        # For this example, we'll just return a success message.

        return True  # Indicate successful password change


    def get_user_by_id(self, user_id: int, db: Session) -> Optional[UserNoPwdPydantic]:
        """
            Retrieves a user by id, excluding the hashed password.
            Return a UserNoPwdPydantic object with the user infos, no password.
        """
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise ResourceNotFoundException(resource_name="User", resource_id=user_id)

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


    def update_user(self, user_data_to_update: UserAuthPydantic, current_user_id: int, db):

        user = db.query(User).filter(User.id == current_user_id).first()

        if not user:
            raise ResourceNotFoundException(resource_name="User", resource_id=current_user_id)

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


    def soft_delete_user(self, deactivation_date, current_user_id: int, db) -> dict:

        user = db.query(User).filter(User.id == current_user_id).first()

        if not user:
            raise ResourceNotFoundException(resource_name="User", resource_id=current_user_id)
        # datetime format 2026-10-27T16:00:00
        user.deactivation_date = deactivation_date
        db.commit()
        db.refresh(user)

        return {"message": "Deactivation date successfully registered",
                "User id": user.id,
                "User name": user.username,
                "deactivation date": deactivation_date
                }


    def delete_user(self, user_id: int) -> bool:
        """ Deletes a user. """
        pass


    def get_user_profiles(self, user_id: int, db: Session):
        """
        :param user_id:
        :param db: database
        :return: JSON with a List of dictionaries with profile ID and name
        """
        profiles = db.query(Profile.id, Profile.name, Profile.performance_type).filter(Profile.user_id == user_id).all()

        if not profiles:
            return profiles

        if profiles:
            return [{"id": profile.id, "name": profile.name, "performance_type": profile.performance_type} for profile in profiles]

        else:
            return None

    @staticmethod
    def get_user_contracts(user_id: int, db: Session):
        """
        :param user_id:
        :param db: database
        :return: JSON with a List of dictionaries with profile ID and name
        """
        contracts = db.query(Contract.id, Contract.name).filter(or_(Contract.offeror_id == user_id, Contract.offeree_id == user_id)).all()

        if not contracts:
            return contracts

        if contracts:
            return [{"id": contract.id, "name": contract.name} for contract in contracts]

        else:
            return None



# Profile related
    def create_profile(self, profile_data: ProfilePydantic, current_user_id: int, db: Session):
        """
            Creates a new profile in the database.
            Validate the input data with ProfilePydantic and UserAuthPydantic
        """
        try:
            # --- Process online_press specifically for JSONB column ---
            processed_online_press = [
                {"title": item.title, "url": str(item.url)}  # Access title and url attributes
                for item in profile_data.online_press
            ] if profile_data.online_press else []
            # Note: if profile_data.online_press is an empty list (default),
            # the comprehension correctly results in an empty list.
            # ensures that if the incoming online_press list from Pydantic is empty
            # (which is its default and common when no data is provided),
            # processed_online_press also becomes an empty list, which is valid for a JSONB column

            # --- Process other HttpUrl lists (social_media, photos, videos, audios) ---
            # Ensure None values from Pydantic's Optional[HttpUrl] are handled
            processed_social_media = [str(url) for url in profile_data.social_media if
                                      url is not None] if profile_data.social_media else []
            processed_photos = [str(url) for url in profile_data.photos if
                                url is not None] if profile_data.photos else []
            processed_videos = [str(url) for url in profile_data.videos if
                                url is not None] if profile_data.videos else []
            processed_audios = [str(url) for url in profile_data.audios if
                                url is not None] if profile_data.audios else []

            # --- Process optional single HttpUrl fields (stage_plan, tech_rider, website) ---
            # Your existing logic is correct for these
            processed_stage_plan = str(profile_data.stage_plan) if profile_data.stage_plan else None
            processed_tech_rider = str(profile_data.tech_rider) if profile_data.tech_rider else None
            processed_website = str(profile_data.website) if profile_data.website else None

            new_profile = Profile(
                user_id=current_user_id,
                name=profile_data.name,
                performance_type=profile_data.performance_type,
                description=profile_data.description,
                bio=profile_data.bio,
                social_media=processed_social_media,
                stage_plan=processed_stage_plan,
                tech_rider=processed_tech_rider,
                photos=processed_photos,
                videos=processed_videos,
                audios=processed_audios,
                online_press=processed_online_press,  # <--- THIS IS THE KEY CHANGE HERE
                website=processed_website,
            )
            db.add(new_profile)
            db.commit()
            db.refresh(new_profile)
            return new_profile.id
        except KeyError as e: # Handle missing keys
            self.session.rollback() # It could use db.rollback() as db is the session object
            print(f"Missing key in user_data: {e}")
            raise ValueError(f"Missing key in user_data: {e}")
        except Exception as e:
            db.rollback()
            raise e


    def get_profile_by_id(self, profile_id: int, db: Session) -> Optional[ProfilePydantic] | None:
        """
            Retrieves a profile by ID.
            Return a dictionary with the profile infos.
        """
        profile = db.query(Profile).filter(Profile.id == profile_id).first()

        if not profile:
            raise ResourceNotFoundException(resource_name="Profile", resource_id=profile_id)

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
            -> Optional[ProfilePydantic]:

            profile = db.query(Profile).filter(Profile.id == profile_id).first()

            if not profile:
                raise ResourceNotFoundException(resource_name="Profile", resource_id=profile_id)

            if profile.user_id != current_user_id:
                raise ResourceUserMismatchException(resource_name="Profile", resource_id=profile_id, user_id=current_user_id)

            # Converts Pydantic model to a dictionary.
            # Excludes any fields that were not provided (unset) in the request.
            # Uses the exclude_unset=True pydantic method
            for key, value in profile_data_to_update.model_dump(exclude_unset=True).items():
                if isinstance(value, HttpUrl):
                    setattr(profile, key, str(value))
                elif isinstance(value, list):  # Check if it's a list first
                    # Check for list of HttpUrl
                    if all(isinstance(item, HttpUrl) for item in value):
                        setattr(profile, key, [str(item) for item in value])
                    # Check for list of TitleAndUrl
                    elif all(isinstance(item, TitleAndUrl) for item in value):
                        # It's stored as a list of dicts:
                        setattr(profile, key, [item.model_dump() for item in value])
                    else:
                        # If there are other list types, handle them or raise error
                        setattr(profile, key, value)  # Fallback for other list types
                else:
                    # For all other scalar types (str, int, bool, etc.)
                    setattr(profile, key, value)

            db.commit()
            db.refresh(profile)

            profile_data = self.get_profile_by_id(profile_id, db)
            return profile_data

    def delete_profile(self, profile_id: int, current_user_id: int, db: Session) -> bool:

        profile = db.query(Profile).filter(Profile.id == profile_id).first()

        if not profile:
            raise ResourceNotFoundException(resource_name="Profile", resource_id=profile_id)

        if profile.user_id != current_user_id:
            raise ResourceUserMismatchException(resource_name="Profile", resource_id=profile_id, user_id=current_user_id)

        self.session.delete(profile)
        self.session.commit()
        return True


# Contract related
    def create_contract(self, contract_data: ContractCreatePydantic, current_user_id: int, db: Session):
        """
        Creates a new contract in the database.
        Validate input data with ContractPydantic and UserAuthPydantic
        """
        try:
            # Check if the offeree_id exists in the database
            offeree_exists = db.query(User).filter(User.id == contract_data.offeree_id).first()
            if not offeree_exists:
                raise ResourceNotFoundException(resource_name="Offeree", resource_id=contract_data.offeree_id)

            # Check if the offeror_id is the same as offeree_id
            if contract_data.offeree_id == current_user_id:
                raise InvalidContractException

            total_fee = contract_data.performance_fee + contract_data.travel_expenses + contract_data.accommodation_expenses + contract_data.other_expenses

            new_contract = Contract(
                name=contract_data.name, # Contract name
                offeror_id=current_user_id, # Current user create the contract as offeror
                offeree_id=contract_data.offeree_id,
                currency_code=contract_data.currency_code,
                upon_signing=contract_data.upon_signing,  # % of total
                upon_completion=contract_data.upon_completion, # % rest
                payment_method=contract_data.payment_method,
                performance_fee=contract_data.performance_fee,
                travel_expenses=contract_data.travel_expenses,
                accommodation_expenses=contract_data.accommodation_expenses,
                other_expenses=contract_data.other_expenses,
                total_fee=total_fee
            )
            db.add(new_contract)
            db.commit()
            db.refresh(new_contract)
            return new_contract.id
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def get_contract_events(contract_id: int, current_user_id: int, db: Session) -> list:
        """
        :param contract_id: to get events
        :param current_user_id: to check if the contract belongs to the user
        :param db: database
        :return: tuple with event ids
        """
        contract = (db.query(Contract)
                    .filter(Contract.id == contract_id)
                    .filter(or_(Contract.offeror_id == current_user_id, Contract.offeree_id == current_user_id))
                    .first())

        events_in_contract: list = db.query(Event.id, Event.name).filter(Event.contract_id == contract_id).all()

        if not contract:
            raise ResourceNotFoundException(resource_name="Contract", resource_id=contract_id)


        if not events_in_contract:
            return []

        # Extract the IDs from the list of tuples in result events_in_contract
        return [event_id[0] for event_id in events_in_contract]


    def get_contract_by_id(self, contract_id: int, current_user_id: int, db: Session) -> Optional[ContractPydantic]:
        """
            Retrieves a contract by ID.
            Return a dictionary with the contract infos
        """
        contract = (db.query(Contract)
                    .filter(Contract.id == contract_id)
                    .filter(or_(Contract.offeror_id == current_user_id, Contract.offeree_id == current_user_id))
                    .first())

        if not contract:
            raise ResourceUserMismatchException(resource_name="Contract", resource_id=contract_id, user_id=current_user_id)


        return ContractPydantic(
            id=contract.id,
            created_at=contract.created_at,
            name=contract.name,
            offeror_id=contract.offeror_id,
            offeree_id=contract.offeree_id,
            currency_code=contract.currency_code,
            upon_signing=contract.upon_signing,
            upon_completion=contract.upon_completion,
            payment_method=contract.payment_method,
            performance_fee=contract.performance_fee,
            travel_expenses=contract.travel_expenses,
            accommodation_expenses=contract.accommodation_expenses,
            other_expenses=contract.other_expenses,
            total_fee=contract.total_fee,
            disabled=contract.disabled,
            disabled_at=contract.disabled_at,
            signed_at=contract.signed_at,
            delete_date=contract.delete_date
        )


    def update_contract(
            self, contract_id: int,
            contract_data_to_update: ContractUpdatePydantic,
            current_user_id, db: Session) \
            -> Optional[ContractUpdatePydantic]:

            contract = db.query(Contract).filter(Contract.id == contract_id).first()

            if not contract:
                raise ResourceNotFoundException(resource_name="Contract", resource_id=contract_id)

            if contract.offeror_id != current_user_id:
                raise ResourceUserMismatchException(resource_name="Contract", resource_id=contract_id,
                                                    user_id=current_user_id)

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


    def disable_contract(
            self, contract_id: int,
            disabled_at, # datetime format 2026-10-27T16:00:00
            current_user_id: int,
            db: Session) -> dict:
            """
            :param contract_id: to update
            :param disabled_at: datetime to disable the contract
            :param current_user_id: to allow the access
            :param db: database
            :return: confirmation ot exception
            """

            contract = db.query(Contract).filter(Contract.id == contract_id).first()

            if not contract:
                raise ResourceNotFoundException(resource_name="Contract", resource_id=contract_id)

            if contract.offeror_id != current_user_id:
                raise ResourceUserMismatchException(resource_name="Contract", resource_id=contract_id,
                                                    user_id=current_user_id)

            # datetime format 2026-10-27T16:00:00
            contract.disabled_at = disabled_at
            db.commit()
            db.refresh(contract)

            return {"message": "Contract disablement date successfully recorded",
                    "Contract id": contract.id,
                    "Contract name": contract.name,
                    "deactivation date": disabled_at
                    }

    @staticmethod
    def get_contract_events_id_and_name(contract_id: int, db: Session):
        """
        :param contract_id:
        :param db:
        :return:
        """
        events = db.query(Event.id, Event.name).filter(Event.contract_id == contract_id).all()

        if not events:
            raise ResourcesMismatchException(resource_name_A="Events", resource_name_B="Contract",
                                             resource_id_B=contract_id)

        if events:
            return [{"id": event.id, "name": event.name} for event in events]

        else:
            return None


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

        event = db.query(Event).filter(Event.id == event_id).first()

        if not event:
            raise ResourceNotFoundException(resource_name="Event", resource_id=event_id)

        offeror_id = db.query(Contract.offeror_id).filter(Contract.id == event.contract_id)
        offeror_id = offeror_id[0][0]

        if offeror_id != current_user_id:
            raise ResourceUserMismatchException(resource_name="Event", resource_id=event_id, user_id=current_user_id)

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


    def update_event(
            self, event_id: int,
            event_data_to_update: EventUpdatePydantic,
            current_user_id: int,
            db: Session) -> Optional[EventPydantic]:
        """ Updates an event. """

        event = db.query(Event).filter(Event.id == event_id).first()

        if not event:
            raise ResourceNotFoundException(resource_name="Event", resource_id=event_id)

        offeror_id = db.query(Contract.offeror_id).filter(Contract.id == event.contract_id)
        offeror_id = offeror_id[0][0]

        if offeror_id != current_user_id:
            raise ResourceUserMismatchException(resource_name="Event", resource_id=event_id, user_id=current_user_id)

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


    def delete_event(self, event_id: int, current_user_id: int, db: Session) -> bool:
        event = db.query(Event).filter(Event.id == event_id).first()

        if not event:
            raise ResourceNotFoundException(resource_name="Event", resource_id=event_id)

        offeror_id = db.query(Contract.offeror_id).filter(Contract.id == event.contract_id)
        offeror_id = offeror_id[0][0]

        if offeror_id != current_user_id:
            raise ResourceUserMismatchException(resource_name="Event", resource_id=event_id,
                                                user_id=current_user_id)

        self.session.delete(event)
        self.session.commit()
        return True


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
        accommodation = db.query(Accommodation).filter(Accommodation.id == accommodation_id).first()

        if not accommodation:
            raise ResourceNotFoundException(resource_name="Accommodation", resource_id=accommodation_id)

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


    def update_accommodation(
            self, accommodation_id: int,
            accommodation_data_to_update: AccommodationUpdatePydantic,
            db) -> AccommodationPydantic:
        """ Updates accommodation. """
        accommodation = db.query(Accommodation).filter(Accommodation.id == accommodation_id).first()

        if not accommodation:
            raise ResourceNotFoundException(resource_name="Accommodation", resource_id=accommodation_id)

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



    def delete_accommodation(self, accommodation_id: int, db) -> bool:
        """ Deletes accommodation. """

        accommodation = db.query(Accommodation).filter(Accommodation.id == accommodation_id).first()

        if not accommodation:
            raise ResourceNotFoundException(resource_name="Accommodation", resource_id=accommodation_id)

        self.session.delete(accommodation)
        self.session.commit()
        return True