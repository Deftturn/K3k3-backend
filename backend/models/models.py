import enum
from uuid import UUID
import uuid 
from datetime import datetime
from database import Base

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func



# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class RoleType(str, enum.Enum):
    driver = "driver"
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
# User & Role
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    role = relationship("Role", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    role_type = Column(Enum(RoleType), nullable=False)

    # Relationships
    user = relationship("User", back_populates="role")
    driver = relationship("Driver", back_populates="role", uselist=False, cascade="all, delete-orphan")
    passenger = relationship("Passenger", back_populates="role", uselist=False, cascade="all, delete-orphan")
    admin = relationship("Admin", back_populates="role", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Role id={self.id} role_type={self.role_type}>"


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    driver_id = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, unique=True)
    rating = Column(Numeric(3, 2), default=0.00)
    is_available = Column(Boolean, default=True, nullable=False)
    location = Column(String(500), nullable=True)  # e.g. "lat,lng" or PostGIS point

    # Relationships
    role = relationship("Role", back_populates="driver")
    vehicle = relationship("Vehicle", back_populates="driver", uselist=False, cascade="all, delete-orphan")
    trips = relationship("Trip", back_populates="driver", foreign_keys="Trip.driver_id")

    def __repr__(self) -> str:
        return f"<Driver id={self.id} available={self.is_available}>"


# ---------------------------------------------------------------------------
# Passenger
# ---------------------------------------------------------------------------

class Passenger(Base):
    __tablename__ = "passengers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, unique=True)
    location = Column(String(500), nullable=True)
    gender = Column(Enum(GenderType), nullable=True)

    # Relationships
    role = relationship("Role", back_populates="passenger")
    trips = relationship("Trip", back_populates="passenger", foreign_keys="Trip.passenger_id")

    def __repr__(self) -> str:
        return f"<Passenger id={self.id}>"


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------

class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, unique=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    role = relationship("Role", back_populates="admin")
    trip = relationship("Trip", foreign_keys=[trip_id])

    def __repr__(self) -> str:
        return f"<Admin id={self.id}>"


# ---------------------------------------------------------------------------
# Trip
# ---------------------------------------------------------------------------

class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, autoincrement=True)
    driver_id = Column(Integer, ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True)
    passenger_id = Column(Integer, ForeignKey("passengers.id", ondelete="SET NULL"), nullable=True)

    pickup_lat = Column(Float, nullable=False)
    pickup_lng = Column(Float, nullable=False)
    dest_lat = Column(Float, nullable=False)
    dest_lng = Column(Float, nullable=False)

    status = Column(Enum(TripStatus), nullable=False, default=TripStatus.requested)
    fare_estimate = Column(Numeric(10, 2), nullable=True)
    actual_fare = Column(Numeric(10, 2), nullable=True)
    requested_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    driver = relationship("Driver", back_populates="trips", foreign_keys=[driver_id])
    passenger = relationship("Passenger", back_populates="trips", foreign_keys=[passenger_id])
    log = relationship("Log", back_populates="trip", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Trip id={self.id} status={self.status}>"


# ---------------------------------------------------------------------------
# Vehicle
# ---------------------------------------------------------------------------

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    driver_id = Column(Integer, ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False, unique=True)
    license_number = Column(String(50), unique=True, nullable=False)
    make = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    year = Column(Integer, nullable=False)
    plate_number = Column(String(20), unique=True, nullable=False)
    color = Column(String(50), nullable=True)

    # Relationships
    driver = relationship("Driver", back_populates="vehicle")

    def __repr__(self) -> str:
        return f"<Vehicle id={self.id} plate={self.plate_number!r}>"


# ---------------------------------------------------------------------------
# Log
# ---------------------------------------------------------------------------

class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trip_id = Column(Integer, ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, unique=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    trip = relationship("Trip", back_populates="log")

    def __repr__(self) -> str:
        return f"<Log id={self.id} trip_id={self.trip_id}>"