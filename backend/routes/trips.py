from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from database import get_db
from models.models import Trip, Passenger
from schemas import trips
from services.matching import find_nearest_rider
from services.ws_manager import manager
import logging
from typing import List

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/trips", tags=["Trip"])

@router.get("/", response_model=List[trips.TripRead])
def get_trips(db:Session = Depends(get_db)):
    """Retrieve Trips"""
    try:
        return db.query(Trip).all()
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving trips: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error retrieving trips: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.post("/", response_model=trips.TripRead)
async def create_trip(trip_data: trips.TripCreate, db: Session = Depends(get_db)):
    """Create a new trip request and assign to nearest available rider."""
    try:
        # Validate coordinates
        if not (-90 <= trip_data.pickup_lat <= 90 and -180 <= trip_data.pickup_lng <= 180):
            logger.warning(f"Invalid pickup coordinates: lat={trip_data.pickup_lat}, lng={trip_data.pickup_lng}")
            raise HTTPException(status_code=400, detail="Invalid pickup coordinates")
        
        if not (-90 <= trip_data.dest_lat <= 90 and -180 <= trip_data.dest_lng <= 180):
            logger.warning(f"Invalid destination coordinates: lat={trip_data.dest_lat}, lng={trip_data.dest_lng}")
            raise HTTPException(status_code=400, detail="Invalid destination coordinates")
        
        # Verify passenger exists
        passenger = db.query(Passenger).filter(Passenger.id == trip_data.passenger_id).first()
        if not passenger:
            logger.warning(f"Trip creation attempt with non-existent passenger: {trip_data.passenger_id}")
            raise HTTPException(status_code=404, detail="Passenger not found")
        
        # Find nearest rider if not specified
        rider_id = trip_data.rider_id
        if rider_id is None:
            rider_id = find_nearest_rider(db, trip_data.pickup_lat, trip_data.pickup_lng)
        
        if rider_id is None:
            logger.warning(f"No riders available for trip at ({trip_data.pickup_lat}, {trip_data.pickup_lng})")
            raise HTTPException(status_code=503, detail="No riders available at this location")
        
        # Create trip
        new_trip = Trip(
            passenger_id=trip_data.passenger_id,
            rider_id=rider_id,
            pickup_lat=trip_data.pickup_lat,
            pickup_lng=trip_data.pickup_lng,
            dest_lat=trip_data.dest_lat,
            dest_lng=trip_data.dest_lng,
            fare_estimate=trip_data.fare_estimate,
            status="requested"
        )
        db.add(new_trip)
        db.commit()
        db.refresh(new_trip)
        
        # Notify rider about new trip
        if rider_id:
            try:
                sent = await manager.send(rider_id, {
                    "type": "new_trip",
                    "trip_id": new_trip.id,
                    "passenger_id": trip_data.passenger_id,
                    "pickup": {"lat": trip_data.pickup_lat, "lng": trip_data.pickup_lng},
                    "destination": {"lat": trip_data.dest_lat, "lng": trip_data.dest_lng},
                    "fare_estimate": str(trip_data.fare_estimate) if trip_data.fare_estimate else None
                })
                logger.debug(f"Trip {new_trip.id} notification sent to {sent} client(s)")
            except Exception as e:
                logger.error(f"Failed to notify rider about trip {new_trip.id}: {e}")
                # Don't fail the trip creation if notification fails
        
        logger.info(f"Trip created successfully: {new_trip.id}")
        return new_trip
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during trip creation: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error during trip creation: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.get("/{trip_id}", response_model=trips.TripRead)
def get_trip(trip_id: int, db: Session = Depends(get_db)):
    """Retrieve trip information by ID."""
    try:
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            logger.info(f"Trip not found: {trip_id}")
            raise HTTPException(status_code=404, detail="Trip not found")
        return trip
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving trip {trip_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error retrieving trip {trip_id}: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.put("/{trip_id}", response_model=trips.TripRead)
def update_trip(trip_id: int, trip_data: trips.TripUpdate, db: Session = Depends(get_db)):
    """Update trip status and fare information."""
    try:
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            logger.info(f"Trip not found for update: {trip_id}")
            raise HTTPException(status_code=404, detail="Trip not found")
        
        # Update fields
        update_data = trip_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(trip, key):
                setattr(trip, key, value)
        
        db.add(trip)
        db.commit()
        db.refresh(trip)
        
        logger.info(f"Trip {trip_id} updated successfully")
        return trip
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error updating trip {trip_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error updating trip {trip_id}: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
