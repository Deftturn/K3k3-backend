from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from database import get_db
from models.models import Driver, Role
from schemas import driver
from services.location import update_driver_location
from services.ws_manager import manager
import logging
from typing import List

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/drivers", tags=['Driver'])


@router.post("/register/", response_model=driver.DriverRead)
def create_driver(driver_data: driver.DriverCreate, db: Session = Depends(get_db)):
    """Register a new driver with a role."""
    try:
        # Check if role exists
        role = db.query(Role).filter(Role.id == driver_data.role_id).first()
        if not role:
            logger.warning(f"Driver registration attempt with non-existent role: {driver_data.role_id}")
            raise HTTPException(status_code=404, detail="Role not found")
        
        # Create driver
        new_driver = Driver(
            role_id=driver_data.role_id,
            rating=driver_data.rating,
            is_available=driver_data.is_available,
            location=driver_data.location
        )
        db.add(new_driver)
        db.commit()
        db.refresh(new_driver)
        
        logger.info(f"Driver registered successfully with role {driver_data.role_id}")
        return new_driver
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during driver registration: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error during driver registration: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@router.get("/", response_model=List[driver.DriverRead])
def get_drivers(db:Session = Depends(get_db)):
    """Retrieve Drivers"""
    try:
        return db.query(Driver).all()
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving drivers: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error retrieving drivers: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.get("/{driver_id}", response_model=driver.DriverRead)
def get_driver(driver_id: int, db: Session = Depends(get_db)):
    """Retrieve driver information by ID."""
    try:
        driver_obj = db.query(Driver).filter(Driver.id == driver_id).first()
        if not driver_obj:
            logger.info(f"Driver not found: {driver_id}")
            raise HTTPException(status_code=404, detail="Driver not found")
        return driver_obj
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving driver {driver_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error retrieving driver {driver_id}: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.put("/{driver_id}/location")
async def update_location(driver_id: int, lat: float, lng: float, db: Session = Depends(get_db)):
    """Update driver location and notify connected clients."""
    try:
        # Validate coordinates
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            logger.warning(f"Invalid coordinates provided for driver {driver_id}: lat={lat}, lng={lng}")
            raise HTTPException(status_code=400, detail="Invalid coordinates: latitude must be -90 to 90, longitude must be -180 to 180")
        
        # Get driver
        driver_obj = db.query(Driver).filter(Driver.id == driver_id).first()
        if not driver_obj:
            logger.info(f"Driver not found for location update: {driver_id}")
            raise HTTPException(status_code=404, detail="Driver not found")
        
        # Update location in database
        location_str = f"{lat},{lng}"
        driver_obj.location = location_str #type: ignore
        db.add(driver_obj)
        db.commit()
        db.refresh(driver_obj)
        
        # Update Redis cache
        success = update_driver_location(driver_id, lat, lng)
        if not success:
            logger.warning(f"Failed to update driver {driver_id} location in Redis")
        
        # Notify connected clients
        sent = await manager.send(driver_id, {
            "type": "location_update",
            "driver_id": driver_id,
            "lat": lat,
            "lng": lng
        })
        logger.debug(f"Location update sent to {sent} client(s) for driver {driver_id}")
        
        return {"status": "updated", "clients_notified": sent}
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error updating location for driver {driver_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error updating location for driver {driver_id}: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.put("/{driver_id}/availability")
def update_availability(driver_id: int, is_available: bool, db: Session = Depends(get_db)):
    """Update driver availability status."""
    try:
        driver_obj = db.query(Driver).filter(Driver.id == driver_id).first()
        if not driver_obj:
            logger.info(f"Driver not found for availability update: {driver_id}")
            raise HTTPException(status_code=404, detail="Driver not found")
        
        driver_obj.is_available = is_available #type: ignore
        db.add(driver_obj)
        db.commit()
        db.refresh(driver_obj)
        
        logger.info(f"Driver {driver_id} availability set to {is_available}")
        return {"status": "updated", "is_available": is_available}
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error updating availability for driver {driver_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error updating availability for driver {driver_id}: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
