"""
User-related Pydantic schemas for Mockly application
Includes user profiles, progress tracking, and authentication schemas
"""

from pydantic import BaseModel, EmailStr
from fastapi_users import schemas
from typing import Optional, List
from datetime import datetime
import uuid

# FastAPI Users schemas
class UserRead(schemas.BaseUser[uuid.UUID]):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    profile_picture_url: Optional[str] = None
    created_at: Optional[datetime] = None

class UserCreate(schemas.BaseUserCreate):
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserUpdate(schemas.BaseUserUpdate):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    profile_picture_url: Optional[str] = None

# User progress schemas
class UserProgressCreate(BaseModel):
    question_type: Optional[str] = None
    question_text: Optional[str] = None
    content_score: Optional[float] = None
    voice_score: Optional[float] = None
    face_score: Optional[float] = None
    overall_score: Optional[float] = None
    transcript: Optional[str] = None
    star_analysis: Optional[str] = None
    tips_provided: Optional[str] = None
    session_duration_seconds: Optional[int] = None

class UserProgressResponse(BaseModel):
    id: int
    session_date: datetime
    question_type: Optional[str]
    question_text: Optional[str]
    content_score: Optional[float]
    voice_score: Optional[float]
    face_score: Optional[float]
    overall_score: Optional[float]
    transcript: Optional[str]
    star_analysis: Optional[str]
    tips_provided: Optional[str]
    session_duration_seconds: Optional[int]
    completed: bool

    class Config:
        from_attributes = True

# User stats schemas
class UserStatsResponse(BaseModel):
    total_sessions: int
    average_content_score: Optional[float]
    average_voice_score: Optional[float]
    average_face_score: Optional[float]
    average_overall_score: Optional[float]
    best_overall_score: Optional[float]
    most_recent_session: Optional[datetime]
    streak_days: int

    class Config:
        from_attributes = True

# Starred questions schemas
class StarredQuestionCreate(BaseModel):
    question_id: str

class StarredQuestionResponse(BaseModel):
    id: int
    question_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class StarredQuestionsResponse(BaseModel):
    starred_questions: List[StarredQuestionResponse]

# User profile with aggregated data
class UserProfileResponse(BaseModel):
    user: UserRead
    stats: Optional[UserStatsResponse]
    recent_progress: List[UserProgressResponse]
    starred_questions: List[StarredQuestionResponse]

# OAuth profile data
class OAuthAccountCreate(BaseModel):
    oauth_name: str
    access_token: str
    refresh_token: Optional[str] = None
    account_id: str
    account_email: str 