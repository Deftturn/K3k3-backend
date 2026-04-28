from fastapi import APIRouter, Depends, HTTPException
from database import get_db
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from models.models import Role, User
from schemas import role
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/roles", tags=["roles"])


@router.post("/", response_model=role.RoleRead)
def create_role(role_data: role.RoleCreate, user_id: int, db: Session = Depends(get_db)):
    """Create a new role for a user."""
    try:
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"Role creation attempt with non-existent user: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        # Create role
        new_role = Role(role_type=role_data.role_type, user_id=user_id)
        db.add(new_role)
        db.commit()
        db.refresh(new_role)
        
        logger.info(f"Role {role_data.role_type} created for user {user_id}")
        return new_role
    
    except HTTPException:
        raise
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error during role creation: {e}")
        raise HTTPException(status_code=400, detail="Role creation failed: User may already have a role or invalid data")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during role creation: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error during role creation: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@router.get("/{role_id}", response_model=role.RoleRead)
def get_role(role_id: int, db: Session = Depends(get_db)):
    """Retrieve role information by ID."""
    try:
        role_obj = db.query(Role).filter(Role.id == role_id).first()
        if not role_obj:
            logger.info(f"Role not found: {role_id}")
            raise HTTPException(status_code=404, detail="Role not found")
        return role_obj
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error retrieving role {role_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error retrieving role {role_id}: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
