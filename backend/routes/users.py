from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from models.models import User, Role
from schemas import user
from utils.hashcode import hash_password, verify_password
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register/", response_model=user.UserRead)
def create_user(user_data: user.UserCreate, db: Session = Depends(get_db)):
    """Register a new user with a default role."""
    try:
        # Check if user already exists
        db_user = db.query(User).filter(User.email == user_data.email).first()
        if db_user:
            logger.warning(f"Registration attempt with existing email: {user_data.email}")
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash password
        try:
            hashed_pw = hash_password(user_data.password)
        except Exception as e:
            logger.error(f"Password hashing failed: {e}")
            raise HTTPException(status_code=500, detail="Password processing failed")
        
        # Create user
        new_user = User(
            name=user_data.name,
            email=user_data.email,
            phone=user_data.phone,
            password=hashed_pw,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Create role for the user
        try:
            new_role = Role(user_id=new_user.id, role_type=user_data.role_type)
            db.add(new_role)
            db.commit()
            db.refresh(new_role)
        except Exception as e:
            logger.error(f"Failed to create role for user {new_user.id}: {e}")
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to create user role")
        
        logger.info(f"User registered successfully: {user_data.email}")
        return new_user
    
    except HTTPException:
        raise
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error during registration: {e}")
        raise HTTPException(status_code=400, detail="Registration failed: Invalid data or duplicate entry")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during registration: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error during registration: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.post("/login", response_model=user.UserRead)
def login(user_data: user.UserCreate, db: Session = Depends(get_db)):
    """Authenticate user and return user data."""
    try:
        # Find user by email
        db_user = db.query(User).filter(User.email == user_data.email).first()
        if not db_user:
            logger.warning(f"Login attempt with non-existent email: {user_data.email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Verify password
        try:
            if not verify_password(user_data.password, db_user.password): #type: ignore
                logger.warning(f"Failed login attempt for user: {user_data.email}")
                raise HTTPException(status_code=401, detail="Invalid credentials")
        except Exception as e:
            logger.error(f"Password verification failed for user {user_data.email}: {e}")
            raise HTTPException(status_code=500, detail="Authentication failed")
        
        logger.info(f"User logged in successfully: {user_data.email}")
        return db_user
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error during login: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error during login: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
