from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.sql import func
import enum

from app.db.database import Base


class UserRole(str, enum.Enum):
    """User roles for access control. Inherits str for JSON compatibility."""
    USER = "user"
    ADMIN = "admin"


class User(Base):
    """
    User model for authentication and profile data.
    Maps to 'users' table in the database.
    """
    __tablename__ = "users"
    
    # Core fields
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # Profile info (optional)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    
    # Access control
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    
    # Verification flow
    is_verified = Column(Boolean, default=False, nullable=False)
    verification_code = Column(String, nullable=True)  # Hashed code
    verification_code_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    def __repr__(self):
        """String representation for debugging."""
        return f"<User(id={self.id}, email={self.email}, role={self.role.value}, verified={self.is_verified})>"
    
    @property
    def full_name(self) -> str:
        """Get user's full name if available."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.email


