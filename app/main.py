from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager

from app.scoring import analyze_star_structure
from app.schemas import (
    ScoreRequest, ScoreResponse, 
    STARRequest, STARResponse,
    ComprehensiveAnalysisRequest, ComprehensiveAnalysisResponse
)
from app.database import Base, async_engine
from app.models import User
from app.auth import (
    fastapi_users, auth_backend, google_oauth_client, linkedin_oauth_client,
    current_active_user, current_active_user_optional, get_user_manager
)
from app.user_schemas import UserRead, UserCreate, UserUpdate
from app.users import router as users_router, create_progress_record, UserProgressCreate

from fastapi.middleware.cors import CORSMiddleware
import json
import os

# Frontend URL configuration
FRONTEND_URL = os.getenv("FRONTEND_URL")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(
    title="Mockly API",
    description="Interview practice platform with user authentication and progress tracking",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS origins from environment variable
cors_origins = os.getenv("CORS_ORIGINS").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication routes
app.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)

# Include custom user routes FIRST (before generic FastAPI Users routes)
app.include_router(users_router)

# Include FastAPI Users generic routes AFTER custom routes
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

# OAuth routes - Remove the default ones and add custom ones
from app.auth import SECRET

# Custom OAuth authorization routes
@app.get("/auth/google/authorize")
async def google_authorize():
    authorization_url = await google_oauth_client.get_authorization_url(
        redirect_uri=f"{os.getenv('BACKEND_URL')}/auth/google/callback",
        scope=["openid", "email", "profile"]
    )
    return {"authorization_url": authorization_url}

@app.get("/auth/linkedin/authorize")
async def linkedin_authorize():
    authorization_url = await linkedin_oauth_client.get_authorization_url(
        redirect_uri=f"{os.getenv('BACKEND_URL')}/auth/linkedin/callback"
    )
    return {"authorization_url": authorization_url}

# Custom OAuth callback routes that redirect to frontend
@app.get("/auth/google/callback")
async def google_callback(
    code: str,
    state: str = None,
    user_manager = Depends(get_user_manager)
):
    try:
        print(f"🔍 OAuth callback started - code: {code[:10]}... state: {state}")
        # Get the OAuth access token
        redirect_uri = f"{os.getenv('BACKEND_URL')}/auth/google/callback"
        print(f"🔍 Using redirect_uri: {redirect_uri}")
        token = await google_oauth_client.get_access_token(code, redirect_uri)
        print(f"✅ Got access token from Google")
        
        # Fetch user info from Google using the access token
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {token['access_token']}"}
            )
            response.raise_for_status()
            user_data = response.json()
        
        # Extract user info
        google_id = user_data["id"]
        email = user_data["email"]
        
        # Handle OAuth callback through user manager
        user = await user_manager.oauth_callback(
            oauth_name="google",
            access_token=token['access_token'],
            account_id=google_id,
            account_email=email,
            is_verified_by_default=True
        )
        
        # Generate JWT token for the user
        strategy = auth_backend.get_strategy()
        jwt_token = await strategy.write_token(user)
        
        # Redirect to frontend with token
        redirect_url = f"{FRONTEND_URL}/auth/google/callback?access_token={jwt_token}&token_type=bearer"
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        print(f"OAuth callback error: {e}")
        import traceback
        traceback.print_exc()
        # Redirect to frontend with error
        return RedirectResponse(url=f"{FRONTEND_URL}/auth/google/callback?error=authentication_failed")

@app.get("/auth/linkedin/callback")
async def linkedin_callback(
    code: str,
    state: str = None,
    user_manager = Depends(get_user_manager)
):
    try:
        # Get the OAuth access token
        redirect_uri = f"{os.getenv('BACKEND_URL')}/auth/linkedin/callback"
        token = await linkedin_oauth_client.get_access_token(code, redirect_uri)
        
        # Fetch user info from LinkedIn using the access token
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.linkedin.com/v2/people/~:(id,firstName,lastName,profilePicture(displayImage~:playableStreams))",
                headers={"Authorization": f"Bearer {token['access_token']}"}
            )
            response.raise_for_status()
            profile_data = response.json()
            
            # Get email separately (LinkedIn requires different endpoint)
            email_response = await client.get(
                "https://api.linkedin.com/v2/emailAddresses?q=members&projection=(elements*(handle~))",
                headers={"Authorization": f"Bearer {token['access_token']}"}
            )
            email_response.raise_for_status()
            email_data = email_response.json()
        
        # Extract user info
        linkedin_id = profile_data["id"]
        email = email_data["elements"][0]["handle~"]["emailAddress"]
        
        # Handle OAuth callback through user manager
        user = await user_manager.oauth_callback(
            oauth_name="linkedin",
            access_token=token['access_token'],
            account_id=linkedin_id,
            account_email=email,
            is_verified_by_default=True
        )
        
        # Generate JWT token for the user
        strategy = auth_backend.get_strategy()
        jwt_token = await strategy.write_token(user)
        
        # Redirect to frontend with token
        redirect_url = f"{FRONTEND_URL}/auth/linkedin/callback?access_token={jwt_token}&token_type=bearer"
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        print(f"OAuth callback error: {e}")
        import traceback
        traceback.print_exc()
        # Redirect to frontend with error
        return RedirectResponse(url=f"{FRONTEND_URL}/auth/linkedin/callback?error=authentication_failed")

# Remove the default OAuth routes to avoid conflicts
# OAuth authorization routes (keep the original ones for getting auth URLs)
# app.include_router(
#     fastapi_users.get_oauth_router(google_oauth_client, auth_backend, SECRET),
#     prefix="/auth/google",
#     tags=["auth"],
# )
# app.include_router(
#     fastapi_users.get_oauth_router(linkedin_oauth_client, auth_backend, SECRET),
#     prefix="/auth/linkedin",
#     tags=["auth"],
# )

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
async def score_session_api(
    req: ScoreRequest,
    user: User = Depends(current_active_user_optional)
):
    try:
        response = get_basic_response(req.metrics, req.transcript)
        
        # Save progress for authenticated users
        if user:
            try:
                from app.database import get_async_session
                from sqlalchemy.ext.asyncio import AsyncSession
                
                async def save_progress_background():
                    async for session in get_async_session():
                        try:
                            progress_data = UserProgressCreate(
                                question_type=req.metrics.get('question_type', 'general'),
                                question_text=req.question_id or req.metrics.get('question_text', req.metrics.get('selectedQuestion')),
                                content_score=response["content_score"],
                                voice_score=response["voice_score"],
                                face_score=response["face_score"],
                                transcript=req.transcript,
                                tips_provided=json.dumps(response["tips"])
                            )
                            
                            # Create progress record
                            from app.models import UserProgress
                            progress_record = UserProgress(
                                user_id=user.id,
                                question_type=progress_data.question_type,
                                question_text=progress_data.question_text,
                                content_score=progress_data.content_score,
                                voice_score=progress_data.voice_score,
                                face_score=progress_data.face_score,
                                transcript=progress_data.transcript,
                                tips_provided=progress_data.tips_provided
                            )
                            
                            session.add(progress_record)
                            await session.commit()
                            
                            # Update user statistics
                            from app.users import update_user_stats
                            await update_user_stats(user.id, session)
                            
                        except Exception as e:
                            print(f"Error saving progress: {e}")
                            await session.rollback()
                        finally:
                            break
                
                # Run progress saving in background
                import asyncio
                asyncio.create_task(save_progress_background())
                
            except Exception as e:
                print(f"Error setting up progress saving: {e}")
                # Continue without saving progress
            
        return response
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
async def comprehensive_analysis_api(
    req: ComprehensiveAnalysisRequest,
    user: User = Depends(current_active_user_optional)
):
    """
    Comprehensive analysis endpoint that focuses on STAR analysis
    Simplified to only make one API call for faster response times
    """
    try:
        star_result = await analyze_star_structure(req.transcript)
        basic_response = get_basic_response(req.metrics, req.transcript)
        
        response = {
            **basic_response,
            "star_analysis": star_result
        }
        
        # Save progress for authenticated users
        if user:
            try:
                from app.database import get_async_session
                from sqlalchemy.ext.asyncio import AsyncSession
                
                async def save_progress_background():
                    async for session in get_async_session():
                        try:
                            progress_data = UserProgressCreate(
                                question_type=req.metrics.get('question_type', 'behavioral'),
                                question_text=req.question_id or req.metrics.get('question_text', req.metrics.get('selectedQuestion')),
                                content_score=response["content_score"],
                                voice_score=response["voice_score"],
                                face_score=response["face_score"],
                                transcript=req.transcript,
                                star_analysis=json.dumps(star_result),
                                tips_provided=json.dumps(response["tips"])
                            )
                            
                            # Create progress record
                            from app.models import UserProgress
                            progress_record = UserProgress(
                                user_id=user.id,
                                question_type=progress_data.question_type,
                                question_text=progress_data.question_text,
                                content_score=progress_data.content_score,
                                voice_score=progress_data.voice_score,
                                face_score=progress_data.face_score,
                                transcript=progress_data.transcript,
                                star_analysis=progress_data.star_analysis,
                                tips_provided=progress_data.tips_provided
                            )
                            
                            session.add(progress_record)
                            await session.commit()
                            
                            # Update user statistics
                            from app.users import update_user_stats
                            await update_user_stats(user.id, session)
                            
                        except Exception as e:
                            print(f"Error saving progress: {e}")
                            await session.rollback()
                        finally:
                            break
                
                # Run progress saving in background
                import asyncio
                asyncio.create_task(save_progress_background())
                
            except Exception as e:
                print(f"Error setting up progress saving: {e}")
                # Continue without saving progress
            
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

