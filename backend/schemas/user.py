from orm import ORMBase
from pydantic import Field, EmailStr
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class UserBase(ORMBase):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: str = Field(..., min_length=7, max_length=20)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Plain-text password (will be hashed before storage)")
    gender: Optional[str] = None
    role_type: str
    is_active: bool = False


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserUpdate(ORMBase):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=7, max_length=20)
    password: Optional[str] = Field(None, min_length=8)


class UserRead(UserBase):
    id: int
    created_at: datetime
    gender: Optional[str] = None



    