"""
    server_default=func.now() sets the default value to the current timestamp on the database server.
"""
from __future__ import annotations
from sqlalchemy import Integer, String, DateTime, Date, Time, Interval, ForeignKey, Text, ARRAY, func, Numeric, \
    type_coerce
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import mapped_column, relationship, Mapped
# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_base
from datetime import datetime, date, time, timedelta
from typing import Optional, List
from decimal import Decimal
from sqlalchemy.dialects import postgresql # To be allowed to store objects/dictionaries as a field in the database

Base = declarative_base()


class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now()) # func.now() lets the database itself generate the timestamp, in the database's time zone.
    username: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    type_of_entity: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str]= mapped_column(String(255), nullable=False)
    surname: Mapped[str]= mapped_column(String(255), nullable=False)
    email_address: Mapped[str] = mapped_column(String(255), unique=True)
    phone_number: Mapped[str] = mapped_column(String(255), nullable=False)
    vat_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    bank_account: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(default=True)
    deactivation_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)  # date and time.
    delete_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)  # date and time.

    profiles: Mapped[List["Profile"]] = relationship(back_populates="user")

    # Relationship to PasswordResetToken
    # Use Mapped for type hinting, and relationship for ORM mapping
    reset_tokens: Mapped[List["PasswordResetToken"]] = relationship(back_populates="user")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False) # Store the hashed token
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False) # date and time.
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now()) # func.now() lets the database itself generate the timestamp, in the database's time zone.

    # Relationship back to User
    user: Mapped["User"] = relationship(back_populates="reset_tokens")


class Profile(Base):
    __tablename__ = 'profile'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'), nullable=False)
    performance_type: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    bio: Mapped[str] = mapped_column(Text, nullable=True)
    website: Mapped[str] = mapped_column(String(255), nullable=True)
    social_media: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=True)
    stage_plan: Mapped[str] = mapped_column(String(255), nullable=True)
    tech_rider: Mapped[str] = mapped_column(String(255), nullable=True)
    photos: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=True)
    videos: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=True)
    audios: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=True)
    # Change online_press to store JSON/JSONB
    # Use JSONB for better performance and indexing on PostgresSQL
    online_press: Mapped[list[dict]] = mapped_column(postgresql.JSONB, nullable=True)

    # Relationship back to User
    user: Mapped["User"] = relationship(back_populates="profiles")


class Contract(Base):
    __tablename__ = 'contract'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    offeror_id: Mapped[int] = mapped_column(ForeignKey('user.id'), nullable=False)
    offeree_id: Mapped[int] = mapped_column(ForeignKey('user.id'), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default='USD') # Using 3-character ISO 4217 currency codes
    upon_signing: Mapped[int] = mapped_column(Integer, nullable=False)
    upon_completion: Mapped[int] = mapped_column(Integer, nullable=False)
    payment_method: Mapped[str] = mapped_column(String(255), nullable=False)
    performance_fee: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal('0.00'))
    travel_expenses: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=True, default=Decimal('0.00'))
    accommodation_expenses: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=True, default=Decimal('0.00'))
    other_expenses: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=True, default=Decimal('0.00'))
    total_fee: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal('0.00'))
    disabled: Mapped[Optional[bool]] = mapped_column(default=False)
    disabled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)  # date and time.
    signed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)  # Timezone-aware datetime
    delete_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)  # date and time.


class Event(Base):
    __tablename__ = 'event'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    contract_id: Mapped[int] = mapped_column(ForeignKey('contract.id'), nullable=False)
    profile_offeror_id: Mapped[int] = mapped_column(Integer, nullable=False)
    profile_offeree_id: Mapped[int] = mapped_column(Integer, nullable=False)
    contact_person: Mapped[str] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str] = mapped_column(String(255), nullable=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    duration: Mapped[timedelta] = mapped_column(Interval, nullable=False)
    start: Mapped[time] = mapped_column(Time, nullable=False)
    end: Mapped[time] = mapped_column(Time, nullable=True)
    arrive: Mapped[datetime] = mapped_column(DateTime, nullable=False)  # date and time.
    stage_set: Mapped[time] = mapped_column(Time, nullable=False)
    stage_check: Mapped[time] = mapped_column(Time, nullable=False)
    catering_open: Mapped[time] = mapped_column(Time, nullable=True)
    catering_close: Mapped[time] = mapped_column(Time, nullable=True)
    meal_time: Mapped[time] = mapped_column(Time, nullable=True)
    meal_location_name: Mapped[str] = mapped_column(String(255), nullable=True)
    meal_location_address: Mapped[str] = mapped_column(String(255), nullable=True)
    accommodation_id: Mapped[int] = mapped_column(ForeignKey('accommodation.id'), nullable=True)


class Accommodation(Base):
    __tablename__ = 'accommodation'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_person: Mapped[str] = mapped_column(String(255), nullable=True)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    telephone_number: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    website: Mapped[str] = mapped_column(String(255), nullable=True)
    url: Mapped[str] = mapped_column(String(255), nullable=True)
    check_in: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    check_out: Mapped[datetime] = mapped_column(DateTime, nullable=False)