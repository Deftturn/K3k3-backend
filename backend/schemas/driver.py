from orm import ORMBase
from decimal import Decimal
from typing import Optional
from pydantic import Field


class DriverBase(ORMBase):
    rating: Optional[Decimal] = Field(None, ge=0, le=5, decimal_places=2)
    is_available: bool = True
    location: Optional[str] = None


class DriverCreate(DriverBase):
    role_id: int


class DriverUpdate(ORMBase):
    rating: Optional[Decimal] = Field(None, ge=0, le=5, decimal_places=2)
    is_available: Optional[bool] = None
    location: Optional[str] = None


class DriverRead(DriverBase):
    id: int
    role_id: int