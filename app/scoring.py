
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

async def score_session(req):
    # Mock GPT content eval
    content_score = 4.0
    voice_score = req.metrics.get('voice', {}).get('score', 3.5)
    face_score = req.metrics.get('face', {}).get('score', 4.2)
    tips = {"content": "Structure using STAR.", "voice": "Reduce pauses.", "face": "Improve eye contact."}
    return {
        "content_score": content_score,
        "voice_score": voice_score,
        "face_score": face_score,
        "tips": tips
    }
