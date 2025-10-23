import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import List

from sqlalchemy import select, delete

from app.core.celery_app import celery
from app.db.database import AsyncSessionLocal
from app.models.user import User
from app.core.config import settings

logger = logging.getLogger(__name__)


async def _cleanup_unverified():
    """
    Internal async function to delete unverified users.
    Can be called directly from async context or via Celery task.
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(
        days=settings.UNVERIFIED_USER_DELETE_DAYS
    )
    
    logger.info(f"Starting cleanup of unverified users older than {cutoff_date.isoformat()}")
    
    async with AsyncSessionLocal() as session:
        try:
            # Find unverified users past the cutoff date
            result = await session.execute(
                select(User).where(
                    User.is_verified == False,
                    User.created_at < cutoff_date
                )
            )
            
            users_to_delete = result.scalars().all()
            
            if not users_to_delete:
                logger.info("No unverified users to delete")
                return {"deleted": 0, "user_ids": [], "emails": []}
            
            # Filter and handle timezone-naive datetimes
            valid_deletions = []
            current_time = datetime.now(timezone.utc)
            
            for user in users_to_delete:
                created = user.created_at
                if created.tzinfo is None:
                    created = created.replace(tzinfo=timezone.utc)
                
                if created < cutoff_date:
                    valid_deletions.append(user)
            
            if not valid_deletions:
                logger.info("No unverified users to delete after filtering")
                return {"deleted": 0, "user_ids": [], "emails": []}
            
            # Collect user info for logging
            user_ids: List[int] = [u.id for u in valid_deletions]
            user_emails = [u.email for u in valid_deletions]
            
            # Bulk delete
            await session.execute(
                delete(User).where(User.id.in_(user_ids))
            )
            await session.commit()
            
            logger.info(
                f"Deleted {len(user_ids)} unverified users: {user_emails}"
            )
            
            return {
                "deleted": len(user_ids),
                "user_ids": user_ids,
                "emails": user_emails,
                "cutoff_date": cutoff_date.isoformat()
            }
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error during cleanup task: {e}", exc_info=True)
            raise


@celery.task(name="app.tasks.cleanup.delete_unverified_users_task")
def delete_unverified_users_task() -> dict:
    """
    Celery task wrapper for cleanup operation.
    This runs in a synchronous Celery worker context.
    """
    # Check if we're already in an event loop (testing context)
    try:
        loop = asyncio.get_running_loop()
        # We're in an async context already - this shouldn't happen in Celery
        # but can happen during testing
        logger.warning("Already in event loop - creating new loop for task")
        import nest_asyncio
        nest_asyncio.apply()
        return asyncio.run(_cleanup_unverified())
    except RuntimeError:
        # No event loop running - normal Celery context
        return asyncio.run(_cleanup_unverified())
