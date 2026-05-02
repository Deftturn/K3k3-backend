import enum
import uuid

from database import Base

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class RoleType(str, enum.Enum):
    rider = "rider"
    passenger = "passenger"
    admin = "admin"


class TripStatus(str, enum.Enum):
    requested = "requested"
    accepted = "accepted"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class GenderType(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"
    prefer_not_to_say = "prefer_not_to_say"


# ---------------------------------------------------------------------------
# User  (role_type lives here now — Role table dropped)
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    name        = Column(String(255), nullable=False)
    email       = Column(String(255), unique=True, nullable=False, index=True)
    phone       = Column(String(20),  unique=True, nullable=False, index=True)
    password    = Column(String(255), nullable=False)
    gender      = Column(Enum(GenderType), nullable=True)  # ← moved from Passenger for easier access in auth
    role_type   = Column(Enum(RoleType), nullable=False, index=True)   # ← was a whole table
    is_active   = Column(Boolean, default=True, nullable=False)
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    rider     = relationship("Rider",     back_populates="user", uselist=False, cascade="all, delete-orphan")
    passenger = relationship("Passenger", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User id={self.id} role={self.role_type} email={self.email!r}>"


# ---------------------------------------------------------------------------
# Rider
# ---------------------------------------------------------------------------

class Rider(Base):
    __tablename__ = "riders"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    public_id   = Column(PG_UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)  # native UUID, not String(36)
    user_id     = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    rating      = Column(Numeric(3, 2), default=5.00, nullable=False)
    rating_count = Column(Integer, default=0, nullable=False)   # needed to recompute average correctly
    gender      = Column(Enum(GenderType), nullable=True)
    is_available = Column(Boolean, default=False, nullable=False)
    current_lat  = Column(Float, nullable=True)                 # ← was String "lat,lng"
    current_lng  = Column(Float, nullable=True)
    location_updated_at = Column(DateTime(timezone=True), nullable=True)  # staleness tracking

    # Relationships
    user    = relationship("User",    back_populates="rider",   uselist=False)
    vehicle = relationship("Vehicle", back_populates="rider",   uselist=False, cascade="all, delete-orphan")
    trips   = relationship("Trip",    back_populates="rider",   foreign_keys="Trip.rider_id")

    __table_args__ = (
        # Composite index: proximity queries always filter available riders first
        Index("ix_riders_available_lat_lng", "is_available", "current_lat", "current_lng"),
    )

    def __repr__(self) -> str:
        return f"<Rider id={self.id} available={self.is_available}>"


# ---------------------------------------------------------------------------
# Passenger
# ---------------------------------------------------------------------------

class Passenger(Base):
    __tablename__ = "passengers"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    user_id     = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    gender      = Column(Enum(GenderType), nullable=True)
    current_lat = Column(Float, nullable=True)
    current_lng = Column(Float, nullable=True)

    # Relationships
    user  = relationship("User", back_populates="passenger", uselist=False)
    trips = relationship("Trip", back_populates="passenger", foreign_keys="Trip.passenger_id")

    def __repr__(self) -> str:
        return f"<Passenger id={self.id}>"


# ---------------------------------------------------------------------------
# Admin  
# ---------------------------------------------------------------------------

class Admin(Base):
    __tablename__ = "admins"

    id      = Column(Integer, primary_key=True, autoincrement=True)
    name    = Column(String(255), nullable=True)  # Optional, can be null
    email   = Column(String(255), nullable=True)  # Optional, can be null
    phone   = Column(String(20), nullable=True)   # Optional, can be null
    password = Column(String(255), nullable=True)  # Optional, can be null
    role_type    = Column(String(50), nullable=True) 
    is_active = Column(Boolean, default=True, nullable=False)
    gender = Column(Enum(GenderType), nullable=True)  # Optional, can be null
    # Relationships
    
    

    def __repr__(self) -> str:
        return f"<Admin id={self.id}>"


# ---------------------------------------------------------------------------
# Trips
# ---------------------------------------------------------------------------

class Trip(Base):
    __tablename__ = "trips"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    rider_id     = Column(Integer, ForeignKey("riders.id",     ondelete="SET NULL"), nullable=True)
    passenger_id = Column(Integer, ForeignKey("passengers.id", ondelete="SET NULL"), nullable=True)

    pickup_lat = Column(Float, nullable=False)
    pickup_lng = Column(Float, nullable=False)
    dest_lat   = Column(Float, nullable=False)
    dest_lng   = Column(Float, nullable=False)

    status        = Column(Enum(TripStatus), nullable=False, default=TripStatus.requested)
    fare_estimate = Column(Numeric(10, 2), nullable=True)
    actual_fare   = Column(Numeric(10, 2), nullable=True)

    # Full lifecycle — Log table dropped, no JOIN needed for timestamps
    requested_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    accepted_at   = Column(DateTime(timezone=True), nullable=True)
    started_at    = Column(DateTime(timezone=True), nullable=True)
    completed_at  = Column(DateTime(timezone=True), nullable=True)
    cancelled_at  = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    rider     = relationship("Rider",     back_populates="trips", foreign_keys=[rider_id])
    passenger = relationship("Passenger", back_populates="trips", foreign_keys=[passenger_id])

    __table_args__ = (
        Index("ix_trips_rider_id",              "rider_id"),
        Index("ix_trips_passenger_id",          "passenger_id"),
        Index("ix_trips_status",                "status"),
        # Composite indexes for the two most common filtered queries
        Index("ix_trips_rider_status",          "rider_id",     "status"),
        Index("ix_trips_passenger_status",      "passenger_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<Trip id={self.id} status={self.status}>"


# ---------------------------------------------------------------------------
# Vehicle  (unchanged — already well designed)
# ---------------------------------------------------------------------------

class Vehicle(Base):
    __tablename__ = "vehicles"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    rider_id       = Column(Integer, ForeignKey("riders.id", ondelete="CASCADE"), nullable=False, unique=True)
    license_number = Column(String(50), unique=True, nullable=False)
    make           = Column(String(100), nullable=False)
    model          = Column(String(100), nullable=False)
    year           = Column(Integer, nullable=False)
    plate_number   = Column(String(20), unique=True, nullable=False)
    color          = Column(String(50), nullable=True)

    # Relationships
    rider = relationship("Rider", back_populates="vehicle")

    def __repr__(self) -> str:
        return f"<Vehicle id={self.id} plate={self.plate_number!r}>"