"""
Script to create admin user with command-line arguments.
Usage: 
    python create_admin.py                              # Uses defaults
    python create_admin.py admin@custom.com MyPass123   # Custom credentials
"""
import asyncio
import sys
from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.core.security import hash_password


# Default credentials
DEFAULT_EMAIL = "admin@email.com"
DEFAULT_PASSWORD = "admin123!"


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    END = '\033[0m'


def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")


def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")


def print_info(msg):
    print(f"{Colors.YELLOW}ℹ {msg}{Colors.END}")


async def create_admin_user(email: str, password: str) -> bool:
    """Create a new admin user with auto-verification"""
    async with AsyncSessionLocal() as session:
        # Check if user already exists
        result = await session.execute(select(User).where(User.email == email))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            if existing_user.role == UserRole.ADMIN:
                print_info(f"User '{email}' already exists and is an admin")
                return True
            else:
                # Promote existing user to admin
                existing_user.role = UserRole.ADMIN
                existing_user.is_verified = True
                await session.commit()
                print_success(f"Existing user '{email}' promoted to admin")
                return True
        
        # Create new admin user
        admin_user = User(
            email=email,
            hashed_password=hash_password(password),
            first_name="Admin",
            last_name="User",
            role=UserRole.ADMIN,
            is_verified=True  # Auto-verify admin users
        )
        
        session.add(admin_user)
        await session.commit()
        
        print_success(f"Admin user created successfully!")
        print_info(f"Email: {email}")
        print_info(f"Password: {password}")
        print_info(f"Role: ADMIN")
        print_info(f"Verified: Yes")
        
        return True


async def main():
    """Main entry point"""
    # Parse command line arguments
    if len(sys.argv) == 1:
        # No arguments - use defaults
        email = DEFAULT_EMAIL
        password = DEFAULT_PASSWORD
        print_info(f"Using default credentials: {email}")
    elif len(sys.argv) == 3:
        # Email and password provided
        email = sys.argv[1]
        password = sys.argv[2]
    else:
        # Wrong number of arguments
        print_error("Invalid arguments")
        print("\nUsage:")
        print(f"  python create_admin.py                    # Use defaults ({DEFAULT_EMAIL})")
        print(f"  python create_admin.py <email> <password>  # Custom credentials")
        print("\nExamples:")
        print(f"  python create_admin.py")
        print(f"  python create_admin.py admin@example.com MySecurePass123")
        sys.exit(1)
    
    # Validate password length
    if len(password) < 8:
        print_error("Password must be at least 8 characters")
        sys.exit(1)
    
    # Create admin
    try:
        await create_admin_user(email, password)
    except Exception as e:
        print_error(f"Failed to create admin: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Operation cancelled{Colors.END}")
    except Exception as e:
        print_error(f"Error: {e}")
        raise
