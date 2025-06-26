"""
- David Chung
- Creation Date: 6/22/2025
- Defines data models using pydantic:
"""


from pydantic import BaseModel

class ScoreRequest(BaseModel):
    metrics: dict
    transcript: str

class ScoreResponse(BaseModel):
    content_score: float
    voice_score: float
    face_score: float
    tips: dict
    transcript_debug: str
