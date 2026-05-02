from orm import ORMBase
from decimal import Decimal
from typing import Optional
from pydantic import Field

#RIDER SCHEMAS / DRIVER SCHEMAS


class RiderBase(ORMBase):
    rating: Optional[Decimal] = Field(None, ge=0, le=5, decimal_places=2)
    is_available: bool = True
    location: Optional[str] = None
    gender: Optional[str] = None


class RiderCreate(RiderBase):
    user_id: int


class RiderUpdate(ORMBase):
    rating: Optional[Decimal] = Field(None, ge=0, le=5, decimal_places=2)
    is_available: Optional[bool] = None
    location: Optional[str] = None
    gender: Optional[str] = None

class RiderRead(RiderBase):
    id: int
    user_id: int
