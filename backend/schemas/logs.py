from orm import ORMBase
from pydantic import field_validator
from typing import Optional
from datetime import datetime

class LogBase(ORMBase):
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @field_validator("completed_at", mode="before")
    @classmethod
    def completed_after_started(cls, v: Optional[datetime], info) -> Optional[datetime]:
        started = info.data.get("started_at")
        if v and started and v < started:
            raise ValueError("completed_at must be after started_at")
        return v


class LogCreate(LogBase):
    trip_id: int


class LogUpdate(ORMBase):
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class LogRead(LogBase):
    id: int
    trip_id: int