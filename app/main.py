from fastapi import FastAPI, HTTPException

from app.scoring import analyze_star_structure
from app.schemas import (
    ScoreRequest, ScoreResponse, 
    STARRequest, STARResponse,
    ComprehensiveAnalysisRequest, ComprehensiveAnalysisResponse
)

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper functions
def get_default_tips():
    return {
        "content": "Focus on providing specific examples and clear structure.",
        "voice": "Reduce pauses and maintain consistent pace.",
        "face": "Improve eye contact and maintain confident posture."
    }

def get_basic_response(metrics: dict, transcript: str):
    voice_score = metrics.get('voice', {}).get('score', 3.5)
    face_score = metrics.get('face', {}).get('score', 4.2)
    
    return {
        "content_score": 3.5,
        "voice_score": voice_score,
        "face_score": face_score,
        "tips": get_default_tips(),
        "transcript_debug": transcript
    }

@app.post("/score-session", response_model=ScoreResponse)
async def score_session_api(req: ScoreRequest):
    try:
        return get_basic_response(req.metrics, req.transcript)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-star", response_model=STARResponse)
async def analyze_star_api(req: STARRequest):
    try:
        result = await analyze_star_structure(req.transcript)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/comprehensive-analysis", response_model=ComprehensiveAnalysisResponse)
async def comprehensive_analysis_api(req: ComprehensiveAnalysisRequest):
    """
    Comprehensive analysis endpoint that focuses on STAR analysis
    Simplified to only make one API call for faster response times
    """
    try:
        star_result = await analyze_star_structure(req.transcript)
        basic_response = get_basic_response(req.metrics, req.transcript)
        
        return {
            **basic_response,
            "star_analysis": star_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

