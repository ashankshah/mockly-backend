"""
User profile and progress endpoints for Mockly application
Handles user profile management, progress tracking, and statistics
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional
import json

from app.database import get_async_session
from app.models import User, UserProgress, UserStats
from app.user_schemas import (
    UserRead, UserUpdate, UserProgressCreate, UserProgressResponse,
    UserStatsResponse, UserProfileResponse, StarredQuestionCreate, 
    StarredQuestionResponse, StarredQuestionsResponse
)
from app.auth import current_active_user

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserRead)
async def get_current_user(user: User = Depends(current_active_user)):
    """Get current user information"""
    return user

@router.patch("/me", response_model=UserRead)
async def update_current_user(
    user_update: UserUpdate,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Update current user profile"""
    update_data = user_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    return user

@router.post("/progress", response_model=UserProgressResponse)
async def create_progress_record(
    progress_data: UserProgressCreate,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Create a new progress record for the current user"""
    
    # Calculate overall score if individual scores are provided
    overall_score = None
    scores = [progress_data.content_score, progress_data.voice_score, progress_data.face_score]
    valid_scores = [score for score in scores if score is not None]
    if valid_scores:
        overall_score = sum(valid_scores) / len(valid_scores)
    
    progress_record = UserProgress(
        user_id=user.id,
        question_type=progress_data.question_type,
        question_text=progress_data.question_text,
        content_score=progress_data.content_score,
        voice_score=progress_data.voice_score,
        face_score=progress_data.face_score,
        overall_score=overall_score,
        transcript=progress_data.transcript,
        star_analysis=progress_data.star_analysis,
        tips_provided=progress_data.tips_provided,
        session_duration_seconds=progress_data.session_duration_seconds
    )
    
    session.add(progress_record)
    await session.commit()
    await session.refresh(progress_record)
    
    # Update user statistics
    await update_user_stats(user.id, session)
    
    return progress_record

@router.get("/progress", response_model=List[UserProgressResponse])
async def get_user_progress(
    limit: int = 20,
    offset: int = 0,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get user's progress records"""
    
    query = select(UserProgress).where(
        UserProgress.user_id == user.id
    ).order_by(desc(UserProgress.session_date)).offset(offset).limit(limit)
    
    result = await session.execute(query)
    progress_records = result.scalars().all()
    
    return progress_records

@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get user's aggregated statistics"""
    
    query = select(UserStats).where(UserStats.user_id == user.id)
    result = await session.execute(query)
    user_stats = result.scalar_one_or_none()
    
    if not user_stats:
        # Create initial stats if none exist
        user_stats = UserStats(user_id=user.id)
        session.add(user_stats)
        await session.commit()
        await session.refresh(user_stats)
    
    return user_stats

@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get complete user profile with stats and recent progress"""
    
    # Get user stats
    stats_query = select(UserStats).where(UserStats.user_id == user.id)
    stats_result = await session.execute(stats_query)
    user_stats = stats_result.scalar_one_or_none()
    
    # Get recent progress (last 10 records)
    progress_query = select(UserProgress).where(
        UserProgress.user_id == user.id
    ).order_by(desc(UserProgress.session_date)).limit(10)
    
    progress_result = await session.execute(progress_query)
    recent_progress = progress_result.scalars().all()
    
    # Get starred questions
    from app.models import UserStarredQuestions
    starred_query = select(UserStarredQuestions).where(
        UserStarredQuestions.user_id == user.id
    ).order_by(UserStarredQuestions.created_at.desc())
    
    starred_result = await session.execute(starred_query)
    starred_questions = starred_result.scalars().all()
    
    return UserProfileResponse(
        user=user,
        stats=user_stats,
        recent_progress=recent_progress,
        starred_questions=starred_questions
    )

async def update_user_stats(user_id: str, session: AsyncSession):
    """Update aggregated user statistics"""
    
    # Get all progress records for the user
    progress_query = select(UserProgress).where(UserProgress.user_id == user_id)
    result = await session.execute(progress_query)
    progress_records = result.scalars().all()
    
    if not progress_records:
        return
    
    # Calculate aggregated statistics
    total_sessions = len(progress_records)
    
    content_scores = [p.content_score for p in progress_records if p.content_score is not None]
    voice_scores = [p.voice_score for p in progress_records if p.voice_score is not None]
    face_scores = [p.face_score for p in progress_records if p.face_score is not None]
    overall_scores = [p.overall_score for p in progress_records if p.overall_score is not None]
    
    avg_content = sum(content_scores) / len(content_scores) if content_scores else None
    avg_voice = sum(voice_scores) / len(voice_scores) if voice_scores else None
    avg_face = sum(face_scores) / len(face_scores) if face_scores else None
    avg_overall = sum(overall_scores) / len(overall_scores) if overall_scores else None
    
    best_overall = max(overall_scores) if overall_scores else None
    most_recent = max(p.session_date for p in progress_records)
    
    # Get or create user stats record
    stats_query = select(UserStats).where(UserStats.user_id == user_id)
    stats_result = await session.execute(stats_query)
    user_stats = stats_result.scalar_one_or_none()
    
    if not user_stats:
        user_stats = UserStats(user_id=user_id)
        session.add(user_stats)
    
    # Update stats
    user_stats.total_sessions = total_sessions
    user_stats.average_content_score = avg_content
    user_stats.average_voice_score = avg_voice
    user_stats.average_face_score = avg_face
    user_stats.average_overall_score = avg_overall
    user_stats.best_overall_score = best_overall
    user_stats.most_recent_session = most_recent
    
    await session.commit() 

@router.get("/starred-questions", response_model=StarredQuestionsResponse)
async def get_starred_questions(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Get all starred questions for the current user"""
    
    from app.models import UserStarredQuestions
    
    query = select(UserStarredQuestions).where(
        UserStarredQuestions.user_id == user.id
    ).order_by(UserStarredQuestions.created_at.desc())
    
    result = await session.execute(query)
    starred_questions = result.scalars().all()
    
    return StarredQuestionsResponse(starred_questions=starred_questions)

@router.post("/starred-questions", response_model=StarredQuestionResponse)
async def star_question(
    starred_data: StarredQuestionCreate,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Star a question for the current user"""
    
    from app.models import UserStarredQuestions
    
    # Check if already starred
    existing_query = select(UserStarredQuestions).where(
        UserStarredQuestions.user_id == user.id,
        UserStarredQuestions.question_id == starred_data.question_id
    )
    existing_result = await session.execute(existing_query)
    existing_star = existing_result.scalar_one_or_none()
    
    if existing_star:
        return existing_star  # Already starred
    
    # Create new starred question
    starred_question = UserStarredQuestions(
        user_id=user.id,
        question_id=starred_data.question_id
    )
    
    session.add(starred_question)
    await session.commit()
    await session.refresh(starred_question)
    
    return starred_question

@router.delete("/starred-questions/{question_id}")
async def unstar_question(
    question_id: str,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Unstar a question for the current user"""
    
    from app.models import UserStarredQuestions
    
    query = select(UserStarredQuestions).where(
        UserStarredQuestions.user_id == user.id,
        UserStarredQuestions.question_id == question_id
    )
    
    result = await session.execute(query)
    starred_question = result.scalar_one_or_none()
    
    if not starred_question:
        raise HTTPException(status_code=404, detail="Question not starred")
    
    await session.delete(starred_question)
    await session.commit()
    
    return {"message": "Question unstarred successfully"} 