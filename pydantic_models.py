from typing import List, Optional
from pydantic import BaseModel, EmailStr, HttpUrl, Field, field_validator
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from iso4217 import Currency # List of currency codes
import re

# USER MODELS
class UserAuthPydantic(BaseModel):
    id: int
    username: str
    password: str
    is_active: bool


class UserCreatePydantic(BaseModel):
    username: str
    type_of_entity: str
    password: str
    name: str
    surname: str
    email_address: EmailStr
    phone_number: str
    vat_id: Optional[str] = None
    bank_account: Optional[str] = None # IBAN
    is_active: bool = Field(True)  # Default to True
    deactivation_date: Optional[datetime] = None  # format 2026-10-27T16:00:00
    delete_date: Optional[datetime] = None  # format 2026-10-27T16:00:00

    @field_validator("phone_number")
    def validate_phone_number(cls, v):
        """Allow international format with optional spaces and dashes"""
        if not re.match(r"^\+?\d[\d\s\-]+$", v):
            raise ValueError("Invalid telephone number format")
        return v


class UserNoPwdPydantic(BaseModel):
    id: int
    username: str
    type_of_entity: str
    name: str
    surname: str
    email_address: EmailStr
    phone_number: str
    vat_id: Optional[str] = None
    bank_account: Optional[str] = None
    is_active: bool
    deactivation_date: Optional[datetime] = None  # format 2026-10-27T16:00:00
    delete_date: Optional[datetime] = None  # format 2026-10-27T16:00:00

    @field_validator("phone_number")
    def validate_phone_number(cls, v):
        """llow international format with optional spaces and dashes"""
        if not re.match(r"^\+?\d[\d\s\-]+$", v):
            raise ValueError("Invalid telephone number format")
        return v


class UserUpdatePydantic(BaseModel):
    username: Optional[str] = None
    type_of_entity: Optional[str] = None
    name: Optional[str] = None
    surname: Optional[str] = None
    email_address: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    vat_id: Optional[str] = None
    bank_account: Optional[str] = None
    is_active: Optional[bool] = None
    deactivation_date: Optional[datetime] = None
    delete_date: Optional[datetime] = None

    @field_validator("phone_number")
    def validate_phone_number(cls, v):
        """ Allows international format with optional spaces and dashes"""
        if not re.match(r"^\+?\d[\d\s\-]+$", v):
            raise ValueError("Invalid telephone number format")
        return v


# Pydantic for add a dictionary with title and URL
class TitleAndUrl(BaseModel):
    title: str
    url: HttpUrl

# PROFILE MODELS
class ProfilePydantic(BaseModel):
    id: Optional[int] = None # Optional only for READ operations
    created_at: Optional[datetime] = None # Optional only for READ operations
    name: str # REQUIRED
    performance_type: str # REQUIRED
    description: str # REQUIRED
    bio: str # REQUIRED
    social_media: Optional[List[HttpUrl]] = None
    stage_plan: Optional[HttpUrl] = None
    tech_rider: Optional[HttpUrl] = None

    # all items in it must be valid URLs, and it allows for the field to be completely absent
    # or null if no photos are associated with the profile.
    photos: Optional[List[HttpUrl]] = None
    videos: Optional[List[HttpUrl]] = None
    audios: Optional[List[HttpUrl]] = None

    # Each item will be an instance of TitleAndUrl
    online_press: Optional[List[TitleAndUrl]] = None  # Make the entire list optional
    website: Optional[HttpUrl] = None  # make website optional.


class ProfileUpdatePydantic(BaseModel):
    name: Optional[str] = None  # Add = None for clarity and Pydantic v2 consistency for optionality
    performance_type: Optional[str] = None
    description: Optional[str] = None
    bio: Optional[str] = None
    social_media: Optional[List[HttpUrl]] = None  # Assuming you want to omit the list or clear it
    stage_plan: Optional[HttpUrl] = None
    tech_rider: Optional[HttpUrl] = None
    photos: Optional[List[HttpUrl]] = None
    videos: Optional[List[HttpUrl]] = None
    audios: Optional[List[HttpUrl]] = None
    online_press: Optional[List[TitleAndUrl]] = None  # Make the entire list optional
    website: Optional[HttpUrl] = None


# CONTRACT MODELS
class ContractCreatePydantic(BaseModel):
    name: str  # Contract name
    offeree_id: int
    currency_code: str
    upon_signing: int  # % of total
    upon_completion: int  # % rest
    payment_method: str
    performance_fee: Decimal = Field(decimal_places=2)
    travel_expenses: Optional[Decimal] = Field(default=Decimal(0), decimal_places=2)
    accommodation_expenses: Optional[Decimal] = Field(default=Decimal(0), decimal_places=2)
    other_expenses: Optional[Decimal] = Field(default=Decimal(0), decimal_places=2)
    total_fee: Optional[Decimal] = Field(default=Decimal(0), decimal_places=2)  # Will be auto-filled
    disabled: bool = Field(False)  # Default to False
    disabled_at: Optional[datetime] = None
    signed_at: Optional[datetime] = None
    delete_date: Optional[datetime] = None

    @field_validator("currency_code")
    def validate_currency_code(cls, v):
        """
            :param v: currency code
            :return: currency code or ValueError
        """
        try:
            Currency(v)
            return v
        except ValueError:
            raise ValueError("Invalid ISO 4217 currency code")


class ContractPydantic(BaseModel):
    id: Optional[int] = None # Optional for creation, required for return.
    name: str  # Contract name
    offeror_id: int
    offeree_id: int
    currency_code: str
    upon_signing: int  # % of total
    upon_completion: int  # % rest
    payment_method: str
    performance_fee: Decimal = Field(decimal_places=2)
    travel_expenses: Optional[Decimal] = Field(default=Decimal(0), decimal_places=2)
    accommodation_expenses: Optional[Decimal] = Field(default=Decimal(0), decimal_places=2)
    other_expenses: Optional[Decimal] = Field(default=Decimal(0), decimal_places=2)
    total_fee: Optional[Decimal] = Field(default=Decimal(0), decimal_places=2)  # Will be auto-filled
    disabled: bool = Field(False)  # Default to False
    disabled_at: Optional[datetime] = None
    signed_at: Optional[datetime] = None
    delete_date: Optional[datetime] = None

    @field_validator("currency_code")
    def validate_currency_code(cls, v):
        """
            :param v: currency code
            :return: currency code or ValueError
        """
        try:
            Currency(v)
            return v
        except ValueError:
            raise ValueError("Invalid ISO 4217 currency code")



class ContractUpdatePydantic(BaseModel):
    id: Optional[int] = None # Optional for creation, required for return.
    name: Optional[str] = None # Contract name
    offeree_id: Optional[int] = None
    currency_code: Optional[str] = None
    upon_signing: Optional[int] = None # % of total
    upon_completion: Optional[int] = None # % rest
    payment_method: Optional[str] = None

    performance_fee: Optional[Decimal] = Field(default=None, decimal_places=2)

    travel_expenses: Optional[Decimal] = Field(default=Decimal('0.00'), decimal_places=2)
    accommodation_expenses: Optional[Decimal] = Field(default=Decimal('0.00'), decimal_places=2)
    other_expenses: Optional[Decimal] = Field(default=Decimal('0.00'), decimal_places=2)

    total_fee: Optional[Decimal] = Field(default=None, decimal_places=2, exclude=True)

    disabled: Optional[bool] = Field(default=False)  # Default to False
    # disabled_at: Optional[datetime] = None # format 2026-10-27T16:00:00
    # signed_at: Optional[datetime] = None # format 2026-10-27T16:00:00
    # delete_date: Optional[datetime] = None # format 2026-10-27T16:00:00

    @field_validator("currency_code")
    def validate_currency_code(cls, v):
        """
            :param v: currency code
            :return: currency code or ValueError
        """
        try:
            Currency(v)
            return v
        except ValueError:
            raise ValueError("Invalid ISO 4217 currency code")

    @field_validator("total_fee", mode="before")
    def calculate_total_fee(cls, values):
        """
        mode=before: means that the validation function runs before the field is processed by Pydantic.
        :param values: allows access to other fields of the model to computing values before setting total_fee
        :return: sum of performance_fee, travel_expenses, accommodation_expenses, other_expenses
        """
        return (
                values.get("performance_fee", Decimal(0)) +
                values.get("travel_expenses", Decimal(0)) +
                values.get("accommodation_expenses", Decimal(0)) +
                values.get("other_expenses", Decimal(0))
        )


# EVENT MODELS
class EventPydantic(BaseModel):
    id: Optional[int] = None # Optional for creation, required for return.
    created_at: Optional[datetime] = None # format 2026-10-27T16:00:00
    name: str  # Event name
    contract_id: int
    profile_offeror_id: int
    profile_offeree_id: int
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    date: date
    duration: timedelta # format PT1H30M
    start: time
    end: time
    arrive: Optional[datetime] = None # format 2026-10-27T16:00:00
    stage_set: Optional[time] = None
    stage_check: Optional[time] = None
    catering_open: Optional[time] = None
    catering_close: Optional[time] = None
    meal_time: Optional[time] = None
    meal_location_name: Optional[str]
    meal_location_address: Optional[str]
    accommodation_id: Optional[int] = None

    @field_validator("start", "arrive", "stage_set", "stage_check", "catering_open", "catering_close", "meal_time")
    def validate_time_range(cls, time_val):
        """ Validate the range of hours to 23 and minutes to 59 """
        if time_val and time_val.hour < 0 or time_val.hour > 23 or time_val.minute < 0 or time_val.minute > 59:
            raise ValueError("Time values must be within a valid 24-hour range")
        return time_val

    @field_validator("duration")
    def validate_duration(cls, duration):
        """ Validate an interval greater than 0 """
        if duration.total_seconds() <= 0:
            raise ValueError("Duration must be a positive time interval")
        return duration

    @field_validator("date")
    def validate_future_date(cls, date_val):
        """ Validate a date from today """
        today = date.today()
        if date_val < today:
            raise ValueError("Date must be today or in the future")
        return date_val


class EventUpdatePydantic(BaseModel):
    id: Optional[int] = None # Optional for creation, required for return.
    name: Optional[str] = None  # Event name
    contract_id: Optional[int] = None
    profile_offeror_id: Optional[int] = None
    profile_offeree_id: Optional[int] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    date: Optional[date] = None
    duration: Optional[timedelta] = None # format PT1H30M
    start: Optional[time] = None
    end: Optional[time] = None
    arrive: Optional[datetime] = None # format 2026-10-27T16:00:00
    stage_set: Optional[time] = None
    stage_check: Optional[time] = None
    catering_open: Optional[time] = None
    catering_close: Optional[time] = None
    meal_time: Optional[time] = None
    meal_location_name: Optional[str] = None
    meal_location_address: Optional[str] = None
    accommodation_id: Optional[int] = None

    @field_validator("start", "arrive", "stage_set", "stage_check", "catering_open", "catering_close", "meal_time")
    def validate_time_range(cls, time_val):
        """ Validate the range of hours to 23 and minutes to 59 """
        if time_val and time_val.hour < 0 or time_val.hour > 23 or time_val.minute < 0 or time_val.minute > 59:
            raise ValueError("Time values must be within a valid 24-hour range")
        return time_val

    @field_validator("duration")
    def validate_duration(cls, duration):
        """ Validate an interval greater than 0 """
        if duration.total_seconds() <= 0:
            raise ValueError("Duration must be a positive time interval")
        return duration

    @field_validator("date")
    def validate_future_date(cls, date_val):
        """ Validate a date from today """
        today = date.today()
        if date_val < today:
            raise ValueError("Date must be today or in the future")
        return date_val


# ACCOMMODATION MODELS
class AccommodationPydantic(BaseModel):
    id: Optional[int] = None # Optional for creation, required for return.
    name: str
    contact_person: str
    address: str
    telephone_number: str
    email: Optional[EmailStr] = None # Email optional.
    website: Optional[HttpUrl] = None  # make website optional.
    url: Optional[HttpUrl] = None  # Website optional.
    check_in: Optional[datetime] = None # format 2026-10-27T16:00:00
    check_out: Optional[datetime] = None # format 2026-10-27T16:00:00

    @field_validator("telephone_number")
    def validate_phone_number(cls, v):
        """ Allow international format with optional spaces and dashes"""
        if not re.match(r"^\+?\d[\d\s\-]+$", v):
            raise ValueError("Invalid telephone number format")
        return v


class AccommodationUpdatePydantic(BaseModel):
    name: Optional[str]
    contact_person: Optional[str]
    address: Optional[str]
    telephone_number: Optional[str]
    email: Optional[EmailStr] = None # Email optional.
    website: Optional[HttpUrl] = None  # make website optional.
    url: Optional[HttpUrl] = None  # Website optional.
    check_in: Optional[datetime] = None # format 2026-10-27T16:00:00
    check_out: Optional[datetime] = None # format 2026-10-27T16:00:00

    @field_validator("telephone_number")
    def validate_phone_number(cls, v):
        """ Allow international format with optional spaces and dashes"""
        if not re.match(r"^\+?\d[\d\s\-]+$", v):
            raise ValueError("Invalid telephone number format")
        return v


# Referred to TOKEN
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class UserInDB(BaseModel):
    id: int
    username: str
    hashed_password: str
    type_of_entity: str
    name: str
    surname: str
    email_address: EmailStr
    phone_number: int
    vat_id: Optional[str] = None
    bank_account: Optional[str] = None # IBAN
    disabled: bool = Field(False)  # Default to False