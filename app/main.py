
from fastapi import FastAPI, HTTPException
from app.scoring import score_session
from app.schemas import ScoreRequest, ScoreResponse
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
