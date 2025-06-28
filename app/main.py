from fastapi import FastAPI, HTTPException

from app.scoring import score_session, analyze_star_structure
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

@app.post("/score-session", response_model=ScoreResponse)
async def score_session_api(req: ScoreRequest):
    try:
        result = await score_session(req)
        return result
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
    Comprehensive analysis endpoint that combines scoring and STAR analysis
    """
    try:
        # Get scoring results
        scoring_result = await score_session(req)
        
        # Get STAR analysis
        star_result = await analyze_star_structure(req.transcript)
        
        # Combine results
        return {
            **scoring_result,
            "star_analysis": star_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

