import logging
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.user import UserUpdate, UserResponse

logger = logging.getLogger(__name__)


async def get_all_users(db: AsyncSession) -> List[UserResponse]:
    """
    Fetch all users from database.
    Admin-only endpoint.
    """
    result = await db.execute(select(User))
    users = result.scalars().all()
    
    logger.info(f"Retrieved {len(users)} users")
    
    # Convert ORM models to Pydantic schemas
    return [UserResponse.model_validate(user) for user in users]


async def get_user_by_id(db: AsyncSession, user_id: int) -> UserResponse:
    """
    Get specific user by ID.
    Admin-only endpoint.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    return UserResponse.model_validate(user)


async def update_user(
    db: AsyncSession,
    user_id: int,
    update_data: UserUpdate
) -> UserResponse:
    """
    Update user information (PATCH - partial update).
    Only fields provided in request are updated.
    """
    # Find user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Apply only provided fields
    update_dict = update_data.model_dump(exclude_unset=True)
    
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update"
        )
    
    # Check email uniqueness if email is being updated
    if "email" in update_dict:
        email_check = await db.execute(
            select(User).where(
                User.email == update_dict["email"],
                User.id != user_id
            )
        )
        if email_check.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
    
    for field, value in update_dict.items():
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    
    logger.info(f"User {user.email} updated: {list(update_dict.keys())}")
    
    return UserResponse.model_validate(user)


async def delete_user(db: AsyncSession, user_id: int) -> dict:
    """
    Delete user by ID.
    Admin-only operation.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    user_email = user.email
    
    await db.delete(user)
    await db.commit()
    
    logger.info(f"User deleted: {user_email} (ID: {user_id})")
    
    return {
        "message": f"User {user_email} deleted successfully",
        "deleted_user_id": user_id
    }
