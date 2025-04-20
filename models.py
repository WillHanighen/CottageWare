# models.py - This file contains all model definitions for the CottageWare application.

from sqlalchemy import Boolean, Column, Integer, String, Text, ForeignKey, DateTime, Table
import sqlalchemy
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from datetime import datetime

# Association table for user roles
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('role_id', Integer, ForeignKey('roles.id'))
)

class User(Base):
    """User model for authentication and forum participation"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    username = Column(String(50), unique=True, index=True)
    hashed_password = Column(String(255), nullable=True)  # Nullable for OAuth users
    is_active = Column(Boolean, default=True)
    is_oauth = Column(Boolean, default=False)
    oauth_provider = Column(String(50), nullable=True)
    oauth_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now())
    avatar_url = Column(String(255), nullable=True)
    
    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    threads = relationship("Thread", back_populates="author")
    posts = relationship("Post", back_populates="author")
    profile = relationship("UserProfile", back_populates="user", uselist=False)

class Role(Base):
    """Role model for user permissions"""
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True)
    description = Column(String(255))
    
    # Relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")

class UserProfile(Base):
    """Extended user profile information"""
    __tablename__ = "user_profiles"
    
    # Account tier levels
    TIER_UNREGISTERED = 0
    TIER_REGISTERED = 1
    TIER_CUSTOMER = 2
    TIER_MODERATOR = 3
    TIER_ADMIN = 4
    TIER_OWNER = 5
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    bio = Column(Text, nullable=True)
    location = Column(String(100), nullable=True)
    website = Column(String(255), nullable=True)
    signature = Column(Text, nullable=True)
    account_tier = Column(Integer, default=1)  # Default to registered
    reputation = Column(Integer, default=0)
    discord = Column(String(100), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="profile")
    
    @property
    def tier_name(self):
        """Returns the name of the account tier"""
        tier_names = {
            self.TIER_UNREGISTERED: "Unregistered",
            self.TIER_REGISTERED: "Registered",
            self.TIER_CUSTOMER: "Customer",
            self.TIER_MODERATOR: "Moderator",
            self.TIER_ADMIN: "Administrator",
            self.TIER_OWNER: "Owner"
        }
        return tier_names.get(self.account_tier, "Unknown")

class Category(Base):
    """Forum category model"""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True)
    description = Column(String(255))
    order = Column(Integer, default=0)
    is_public = Column(Boolean, default=True)
    
    # Relationships
    forums = relationship("Forum", back_populates="category")

class Forum(Base):
    """Forum model within categories"""
    __tablename__ = "forums"
    
    # Access level constants
    ACCESS_PUBLIC = 0  # Everyone can access
    ACCESS_REGISTERED = 1  # Only registered users
    ACCESS_CUSTOMER = 2  # Only customers (tier 2+)
    ACCESS_MODERATOR = 3  # Only moderators (tier 3+)
    ACCESS_ADMIN = 4  # Only admins (tier 4+)
    ACCESS_OWNER = 5  # Only owner (tier 5)
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"))
    name = Column(String(100))
    description = Column(String(255))
    order = Column(Integer, default=0)
    is_public = Column(Boolean, default=True)
    access_level = Column(Integer, default=0)  # Default to public access
    
    # Relationships
    category = relationship("Category", back_populates="forums")
    threads = relationship("Thread", back_populates="forum")
    
    def can_access(self, user):
        """Check if a user can access this forum based on their account tier"""
        if self.access_level == self.ACCESS_PUBLIC:
            return True
            
        if not user:
            return False
            
        if not user.profile:
            return False
            
        return user.profile.account_tier >= self.access_level
            
    @property
    def post_count(self):
        """Get the total number of posts across all threads in this forum"""
        count = 0
        for thread in self.threads:
            # Count the initial post (thread content) plus all replies
            count += 1 + len(thread.posts)
        return count
        
    @property
    def latest_thread(self):
        """Get the most recent thread in this forum"""
        if not self.threads:
            return None
        return sorted(self.threads, key=lambda t: t.created_at, reverse=True)[0]

class Thread(Base):
    """Thread model for forum discussions"""
    __tablename__ = "threads"
    
    id = Column(Integer, primary_key=True, index=True)
    forum_id = Column(Integer, ForeignKey("forums.id"))
    author_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(255))
    content = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_sticky = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    views = Column(Integer, default=0)
    
    # Relationships
    forum = relationship("Forum", back_populates="threads")
    author = relationship("User", back_populates="threads")
    posts = relationship("Post", back_populates="thread")

class ThreadView(Base):
    """Model to track which users have viewed which threads"""
    __tablename__ = "thread_views"
    
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey("threads.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    viewed_at = Column(DateTime, default=func.now())
    
    # Relationships
    thread = relationship("Thread")
    user = relationship("User")
    
    # Composite unique constraint to ensure each user/thread combo is unique
    __table_args__ = (sqlalchemy.UniqueConstraint('thread_id', 'user_id', name='_thread_user_view_uc'),)

class Post(Base):
    """Post model for thread replies"""
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey("threads.id"))
    author_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_solution = Column(Boolean, default=False)
    
    # Relationships
    thread = relationship("Thread", back_populates="posts")
    author = relationship("User", back_populates="posts")

class Shoutbox(Base):
    """Shoutbox messages model"""
    __tablename__ = "shoutbox"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(String(255))
    created_at = Column(DateTime, default=func.now())
    # Add shoutbox type to distinguish between public and private messages
    shoutbox_type = Column(String(20), default="public")
    
    # Relationships
    user = relationship("User")

class Product(Base):
    """Product model for reselling"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    description = Column(Text)
    price = Column(String(50))  # Stored as string to handle different pricing models
    image_url = Column(String(255), nullable=True)
    external_url = Column(String(255))  # Link to the actual product
    is_featured = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
