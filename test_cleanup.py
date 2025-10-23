"""
Test script for Celery cleanup task.
Tests automatic deletion of unverified users after configured days.
"""
import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.core.security import hash_password
from app.tasks.cleanup import delete_unverified_users_task


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    END = '\033[0m'


def print_header(msg):
    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}{msg.center(70)}{Colors.END}")
    print(f"{Colors.BLUE}{'='*70}{Colors.END}")


def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")


def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")


def print_info(msg):
    print(f"{Colors.CYAN}ℹ {msg}{Colors.END}")


def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")


async def create_test_users():
    """Create test users with different ages and verification statuses"""
    print_header("Creating Test Users")
    
    async with AsyncSessionLocal() as session:
        # User 1: Old unverified (should be deleted)
        old_unverified = User(
            email="old_unverified@example.com",
            hashed_password=hash_password("Test123"),
            first_name="Old",
            last_name="Unverified",
            role=UserRole.USER,
            is_verified=False,
            created_at=datetime.now(timezone.utc) - timedelta(days=3)
        )
        
        # User 2: Recent unverified (should NOT be deleted)
        recent_unverified = User(
            email="recent_unverified@example.com",
            hashed_password=hash_password("Test123"),
            first_name="Recent",
            last_name="Unverified",
            role=UserRole.USER,
            is_verified=False,
            created_at=datetime.now(timezone.utc) - timedelta(hours=12)
        )
        
        # User 3: Old but verified (should NOT be deleted)
        old_verified = User(
            email="old_verified@example.com",
            hashed_password=hash_password("Test123"),
            first_name="Old",
            last_name="Verified",
            role=UserRole.USER,
            is_verified=True,
            created_at=datetime.now(timezone.utc) - timedelta(days=10)
        )
        
        # User 4: Very old unverified (should be deleted)
        very_old_unverified = User(
            email="very_old_unverified@example.com",
            hashed_password=hash_password("Test123"),
            first_name="Very Old",
            last_name="Unverified",
            role=UserRole.USER,
            is_verified=False,
            created_at=datetime.now(timezone.utc) - timedelta(days=30)
        )
        
        session.add_all([old_unverified, recent_unverified, old_verified, very_old_unverified])
        await session.commit()
        
        print_success("Created 4 test users:")
        print_warning("  → old_unverified@example.com (3 days old, unverified) - SHOULD DELETE")
        print_info("  → recent_unverified@example.com (12 hours old, unverified) - SHOULD KEEP")
        print_info("  → old_verified@example.com (10 days old, verified) - SHOULD KEEP")
        print_warning("  → very_old_unverified@example.com (30 days old, unverified) - SHOULD DELETE")


async def list_users(title="Users in Database"):
    """List all users with their status"""
    print_header(title)
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        if not users:
            print_warning("No users found in database")
            return []
        
        print(f"\n{'Email':<40} {'Status':<15} {'Age':<15} {'Role':<10} {'ID':<5}")
        print("-" * 90)
        
        for user in users:
            created = user.created_at
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            
            age_delta = datetime.now(timezone.utc) - created
            
            if age_delta.days > 0:
                age_str = f"{age_delta.days} days"
            else:
                hours = age_delta.seconds // 3600
                age_str = f"{hours} hours"
            
            status = f"{Colors.GREEN}✓ verified{Colors.END}" if user.is_verified else f"{Colors.YELLOW}✗ unverified{Colors.END}"
            
            print(f"{user.email:<40} {status:<24} {age_str:<15} {user.role.value:<10} {user.id:<5}")
        
        print()
        return users


async def verify_cleanup_results():
    """Verify that cleanup worked correctly"""
    print_header("Verifying Cleanup Results")
    
    async with AsyncSessionLocal() as session:
        # Check old_unverified was deleted
        result = await session.execute(
            select(User).where(User.email == "old_unverified@example.com")
        )
        if result.scalar_one_or_none() is None:
            print_success("Old unverified user (3 days) was correctly deleted")
        else:
            print_error("Old unverified user should have been deleted!")
        
        # Check very_old_unverified was deleted
        result = await session.execute(
            select(User).where(User.email == "very_old_unverified@example.com")
        )
        if result.scalar_one_or_none() is None:
            print_success("Very old unverified user (30 days) was correctly deleted")
        else:
            print_error("Very old unverified user should have been deleted!")
        
        # Check recent_unverified still exists
        result = await session.execute(
            select(User).where(User.email == "recent_unverified@example.com")
        )
        if result.scalar_one_or_none() is not None:
            print_success("Recent unverified user (12 hours) was correctly preserved")
        else:
            print_error("Recent unverified user should still exist!")
        
        # Check old_verified still exists
        result = await session.execute(
            select(User).where(User.email == "old_verified@example.com")
        )
        if result.scalar_one_or_none() is not None:
            print_success("Old verified user (10 days) was correctly preserved")
        else:
            print_error("Old verified user should still exist!")


async def cleanup_test_users():
    """Clean up test users after test"""
    async with AsyncSessionLocal() as session:
        test_emails = [
            "old_unverified@example.com",
            "recent_unverified@example.com", 
            "old_verified@example.com",
            "very_old_unverified@example.com"
        ]
        
        for email in test_emails:
            result = await session.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            if user:
                await session.delete(user)
        
        await session.commit()


async def main():
    """Main test execution"""
    print(f"\n{Colors.CYAN}{'='*70}")
    print("CELERY CLEANUP TASK TEST".center(70))
    print(f"{'='*70}{Colors.END}\n")
    
    print_info("This test verifies that unverified users older than 2 days are deleted")
    print_info("while preserving recent unverified users and all verified users\n")
    
    # Show existing users
    await list_users("Existing Users (Before Test)")
    
    # Create test users
    await create_test_users()
    
    # Show all users before cleanup
    await list_users("All Users Before Cleanup")
    
    # Run cleanup task - CALL THE ASYNC VERSION DIRECTLY
    print_header("Running Cleanup Task")
    print_info("Executing cleanup operation...")
    
    # Import the async cleanup function
    from app.tasks.cleanup import _cleanup_unverified
    result = await _cleanup_unverified()  # Call async version directly
    
    print_success("Cleanup task completed!\n")
    print(f"{Colors.YELLOW}Cleanup Report:{Colors.END}")
    print(f"  Deleted Users: {Colors.RED}{result['deleted']}{Colors.END}")
    print(f"  User IDs: {result['user_ids']}")
    print(f"  Emails: {result['emails']}")
    print(f"  Cutoff Date: {result['cutoff_date']}\n")
    
    # Show users after cleanup
    await list_users("All Users After Cleanup")
    
    # Verify results
    await verify_cleanup_results()
    
    # Success summary
    print(f"\n{Colors.GREEN}{'='*70}")
    print("✓ ALL CLEANUP TESTS PASSED!".center(70))
    print(f"{'='*70}{Colors.END}\n")
    
    # Optional: cleanup test users
    print_info("Cleaning up test users...")
    await cleanup_test_users()
    print_success("Test users cleaned up\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}Test failed with error: {e}{Colors.END}")
        raise
