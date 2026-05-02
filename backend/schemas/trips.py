from orm import ORMBase
from pydantic import Field
from typing import Optional
from decimal import Decimal
from datetime import datetime


class TripBase(ORMBase):
    pickup_lat: float = Field(..., ge=-90, le=90)
    pickup_lng: float = Field(..., ge=-180, le=180)
    dest_lat: float = Field(..., ge=-90, le=90)
    dest_lng: float = Field(..., ge=-180, le=180)
    fare_estimate: Optional[Decimal] = Field(None, ge=0, decimal_places=2)


class TripCreate(TripBase):
    passenger_id: int
    rider_id: Optional[int] = None   # assigned later by matching logic


class TripUpdate(ORMBase):
    rider_id: Optional[int] = None
    status: Optional[str] = None
    actual_fare: Optional[Decimal] = Field(None, ge=0, decimal_places=2)


class TripRead(TripBase):
    id: int
    rider_id: Optional[int]
    passenger_id: int
    status: str
    actual_fare: Optional[Decimal]
    requested_at: datetime