
from pydantic import BaseModel

class ScoreRequest(BaseModel):
    metrics: dict
    transcript: str

class ScoreResponse(BaseModel):
    content_score: float
    voice_score: float
    face_score: float
    tips: dict
