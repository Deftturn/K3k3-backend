from fastapi import APIRouter, Depends, HTTPException   
from database import get_db
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from models.models import Admin, User
from schemas import admin
from utils.hashcode import hash_password
import logging
from typing import List

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/", response_model=List[admin.AdminRead])
def get_admins(db:Session = Depends(get_db)):
    """Retrieve Admins"""
    try:
        return db.query(Admin).all()
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving admins: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error retrieving admins: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@router.post("/register/", response_model=admin.AdminRead)
def create_admin(admin_data: admin.AdminCreate, db: Session = Depends(get_db)):
    """Register a new admin user with full admin privileges."""
    try:
        # Check if user already exists
        db_user = db.query(User).filter(User.email == admin_data.email).first()
        if db_user:
            logger.warning(f"Admin registration attempt with existing email: {admin_data.email}")
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash password
        try:
            hashed_pw = hash_password(admin_data.password)
        except Exception as e:
            logger.error(f"Password hashing failed: {e}")
            raise HTTPException(status_code=500, detail="Password processing failed")
        
        # Create user
        new_admin = Admin(
            name=admin_data.name,
            email=admin_data.email,
            phone=admin_data.phone,
            password=hashed_pw,
            role_type=admin_data.role_type,
            gender=admin_data.gender,
            is_active=admin_data.is_active
        )
        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)
        
        # Create admin role
    
        
        # Create admin entry
        # try:
        #     new_admin = Admin(user_id=new_user.id)
        #     db.add(new_admin)
        #     db.commit()
        #     db.refresh(new_admin)
        # except Exception as e:
        #     db.rollback()
        #     logger.error(f"Failed to create admin entry for user {new_user.id}: {e}")
        #     raise HTTPException(status_code=500, detail="Failed to create admin entry")
        
        logger.info(f"Admin registered successfully: {admin_data.email}")
        return new_admin
    
    except HTTPException:
        raise
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error during admin registration: {e}")
        raise HTTPException(status_code=400, detail="Registration failed: Invalid data or duplicate entry")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during admin registration: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error during admin registration: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

# --------------------------------------------
# Update admin endpoint
# --------------------------------------------
@router.put("/{admin_id}", response_model=admin.AdminRead)
def update_admin(admin_id: int, admin_data: admin.AdminUpdate, db: Session = Depends(get_db)):
    """Update admin information by ID."""
    try:
        admin_obj = db.query(Admin).filter(Admin.id == admin_id).first()
        if not admin_obj:
            logger.warning(f"Admin update attempt for non-existent ID: {admin_id}")
            raise HTTPException(status_code=404, detail="Admin not found")
        
        # Update fields
        admin_obj.name = admin_data.name #type: ignore
        admin_obj.email = admin_data.email #type: ignore
        admin_obj.phone = admin_data.phone #type: ignore
        if admin_data.password:
            try:
                admin_obj.password = hash_password(admin_data.password) #type: ignore
            except Exception as e:
                logger.error(f"Password hashing failed during admin update: {e}")
                raise HTTPException(status_code=500, detail="Password processing failed")
        admin_obj.role_type = admin_data.role_type #type: ignore
        db.commit()
        db.refresh(admin_obj)
        logger.info(f"Admin updated successfully: {admin_id}")
        return admin_obj
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error during admin update: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")