from fastapi import APIRouter, Depends, HTTPException   
from database import get_db
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from models.models import Admin, User, Role
from schemas import admin
from utils.hashcode import hash_password
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


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
        new_user = User(
            name=admin_data.name,
            email=admin_data.email,
            phone=admin_data.phone,
            password=hashed_pw,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Create admin role
        try:
            new_role = Role(user_id=new_user.id, role_type="admin")
            db.add(new_role)
            db.commit()
            db.refresh(new_role)
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create admin role for user {new_user.id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to create admin role")
        
        # Create admin entry
        try:
            new_admin = Admin(role_id=new_role.id)
            db.add(new_admin)
            db.commit()
            db.refresh(new_admin)
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create admin entry for role {new_role.id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to create admin entry")
        
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
