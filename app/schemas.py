"""
Data models using Pydantic for Mockly backend API
Author: David Chung
Creation Date: 6/22/2025
"""

from pydantic import BaseModel
from typing import Optional

class ScoreRequest(BaseModel):
    metrics: dict
    transcript: str
    question_id: Optional[str] = None

class ScoreResponse(BaseModel):
    content_score: float
    voice_score: float
    face_score: float
    tips: dict
    transcript_debug: str

# Response back to client with STAR evaluation

class STARRequest(BaseModel):
    transcript: str

class STARResponse(BaseModel):
    situation: list[str]
    task: list[str]
    action: list[str]
    result: list[str]

# Comprehensive analysis combining scoring and STAR
class ComprehensiveAnalysisRequest(BaseModel):
    metrics: dict
    transcript: str
    question_id: Optional[str] = None

class ComprehensiveAnalysisResponse(BaseModel):
    content_score: float
    voice_score: float
    face_score: float
    tips: dict
    transcript_debug: str
    star_analysis: dict
