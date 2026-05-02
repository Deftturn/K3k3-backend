from typing import Optional
from orm import ORMBase
from pydantic import Field


class AdminBase(ORMBase):
    name: str = Field(..., min_length=1, max_length=255)
    email: str = Field(..., min_length=1)
    phone: str = Field(..., min_length=7, max_length=20)
    password: str = Field(..., min_length=8, description="Plain-text password (will be hashed before storage)")
    role_type: str = Field(..., min_length=1, max_length=10)
    gender: Optional[str] = None
    is_active: bool = True


class AdminCreate(AdminBase):
    pass
    

class AdminUpdate(AdminCreate):
    pass

class AdminRead(AdminBase):
    id: int