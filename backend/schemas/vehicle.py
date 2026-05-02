from orm import ORMBase
from typing import Optional
from pydantic import Field



class VehicleBase(ORMBase):
    license_number: str = Field(..., max_length=50)
    make: str = Field(..., max_length=100)
    model: str = Field(..., max_length=100)
    year: int = Field(..., ge=1900, le=2100)
    plate_number: str = Field(..., max_length=20)
    color: Optional[str] = Field(None, max_length=50)


class VehicleCreate(VehicleBase):
    rider_id: int


class VehicleUpdate(ORMBase):
    license_number: Optional[str] = Field(None, max_length=50)
    make: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    year: Optional[int] = Field(None, ge=1900, le=2100)
    plate_number: Optional[str] = Field(None, max_length=20)
    color: Optional[str] = Field(None, max_length=50)


class VehicleRead(VehicleBase):
    id: int
    rider_id: int
