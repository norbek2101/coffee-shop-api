from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.database import get_db
from app.schemas.user import UserResponse, UserUpdate, UserListResponse
from app.services import user_service
from app.core.dependencies import get_current_user, require_admin
from app.models.user import User

router = APIRouter()


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Retrieve the authenticated user's profile information."
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get logged-in user's profile"""
    return UserResponse.model_validate(current_user)


@router.get(
    "/",
    response_model=List[UserResponse],
    summary="List all users",
    description="Get list of all registered users. Admin only.",
    dependencies=[Depends(require_admin)]
)
async def list_all_users(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """List all users (admin only)"""
    return await user_service.get_all_users(db)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
    description="Retrieve specific user's information by ID. Admin only.",
    dependencies=[Depends(require_admin)]
)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Get user by ID (admin only)"""
    return await user_service.get_user_by_id(db, user_id)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user",
    description="Partially update user information. Only provided fields are updated. Admin only.",
    dependencies=[Depends(require_admin)]
)
async def update_user(
    user_id: int,
    update_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Update user information (admin only)"""
    return await user_service.update_user(db, user_id, update_data)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete user",
    description="Permanently delete user by ID. Admin only.",
    dependencies=[Depends(require_admin)]
)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Delete user permanently (admin only)"""
    return await user_service.delete_user(db, user_id)
