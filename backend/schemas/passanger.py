from typing import Optional
from orm import ORMBase
from pydantic import Field, EmailStr
from datetime import datetime


class PassengerBase(ORMBase):
    location: Optional[str] = None
    gender: Optional[str] = None


class PassengerCreate(ORMBase):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: str = Field(..., min_length=7, max_length=20)
    password: str = Field(..., min_length=8, description="Plain-text password (will be hashed before storage)")
    location: Optional[str] = None
    gender: Optional[str] = None


class PassengerUpdate(PassengerBase):
    pass


class PassengerRead(PassengerBase):
    id: int
    role_id: int