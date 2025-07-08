"""
Database models for Mockly application
Includes User model for authentication and Profile model for progress tracking
"""

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base

class User(SQLAlchemyBaseUserTableUUID, Base):
    """
    User model extending FastAPI Users base model
    """
    # Additional fields beyond the base user model
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    profile_picture_url = Column(String(255), nullable=True)
    linkedin_id = Column(String(100), nullable=True, unique=True)
    google_id = Column(String(100), nullable=True, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship to user progress
    progress_records = relationship("UserProgress", back_populates="user")

class UserProgress(Base):
    """
    Model to track user's interview progress and scores
    """
    __tablename__ = "user_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    
    # Interview session details
    session_date = Column(DateTime(timezone=True), server_default=func.now())
    question_type = Column(String(100), nullable=True)  # e.g., "behavioral", "technical"
    question_text = Column(Text, nullable=True)
    
    # Scores
    content_score = Column(Float, nullable=True)
    voice_score = Column(Float, nullable=True)
    face_score = Column(Float, nullable=True)
    overall_score = Column(Float, nullable=True)
    
    # Analysis results
    transcript = Column(Text, nullable=True)
    star_analysis = Column(Text, nullable=True)  # JSON string of STAR analysis
    tips_provided = Column(Text, nullable=True)  # JSON string of tips
    
    # Session metadata
    session_duration_seconds = Column(Integer, nullable=True)
    completed = Column(Boolean, default=True)
    
    # Relationship back to user
    user = relationship("User", back_populates="progress_records")

class UserStats(Base):
    """
    Aggregated statistics for user performance
    """
    __tablename__ = "user_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, unique=True)
    
    # Aggregate scores
    total_sessions = Column(Integer, default=0)
    average_content_score = Column(Float, nullable=True)
    average_voice_score = Column(Float, nullable=True)
    average_face_score = Column(Float, nullable=True)
    average_overall_score = Column(Float, nullable=True)
    
    # Progress tracking
    best_overall_score = Column(Float, nullable=True)
    most_recent_session = Column(DateTime(timezone=True), nullable=True)
    streak_days = Column(Integer, default=0)
    
    # Last updated
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    
    # Relationship to user
    user = relationship("User") 