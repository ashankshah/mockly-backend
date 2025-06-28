"""
- David Chung
- Returns AI-powered scores + tips using Mistral-7B-Instruct-v0.2
"""

import httpx
import json
import os
from dotenv import load_dotenv
load_dotenv()
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
print("OpenRouter Key:", OPENROUTER_KEY) #for debugging -> check that api key is being processed correctly

OPENROUTER_API = "https://openrouter.ai/api/v1/chat/completions"
MISTRAL_MODEL = "mistralai/mistral-7b-instruct-v0.2"

async def score_session(req):
    # Get AI-powered content evaluation
    content_score, content_tips = await evaluate_content_quality(req.transcript)
    
    voice_score = req.metrics.get('voice', {}).get('score', 3.5)
    face_score = req.metrics.get('face', {}).get('score', 4.2)
    
    # Combine tips from content analysis with generic tips
    tips = {
        "content": content_tips,
        "voice": "Reduce pauses and maintain consistent pace.",
        "face": "Improve eye contact and maintain confident posture."
    }
    
    return {
        "content_score": content_score,
        "voice_score": voice_score,
        "face_score": face_score,
        "tips": tips,
        "transcript_debug": req.transcript
    }

async def evaluate_content_quality(transcript: str):
    """
    Evaluate interview response content quality using Mistral-7B-Instruct-v0.2
    Returns: (score, tips)
    """
    prompt = f"""
You are an expert interview evaluator. Analyze the following interview response and provide a score from 1-5 and specific improvement tips.

Evaluation Criteria:
- Clarity and structure (1-5)
- Specific examples and details (1-5)
- Professional communication (1-5)
- Relevance to question (1-5)
- Overall impact and persuasiveness (1-5)

Respond with *only* valid JSON in this exact format:
{{
  "score": 4.2,
  "tips": "Provide more specific examples and structure your response using the STAR method."
}}

Interview Response:
\"\"\"
{transcript}
\"\"\"
"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": MISTRAL_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,  # Lower temperature for more consistent scoring
        "max_tokens": 200
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(OPENROUTER_API, headers=headers, json=body)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            print("Content Evaluation Response:", content)
            
            result = json.loads(content)
            return result.get("score", 3.0), result.get("tips", "Focus on providing specific examples and clear structure.")
            
        except Exception as e:
            print("Error in content evaluation:", e)
            return 3.0, "Focus on providing specific examples and clear structure."

async def analyze_star_structure(transcript: str):
    """
    Analyze interview response using STAR format with Mistral-7B-Instruct-v0.2
    """
    prompt = f"""
Analyze the following interview response and break it down into the STAR format (Situation, Task, Action, Result).

For each category, extract the relevant sentences. If a category is not present, use an empty array.

Respond with *only* valid JSON in this exact format:
{{
  "situation": ["Sentence describing the context or background"],
  "task": ["Sentence describing what needed to be accomplished"],
  "action": ["Sentences describing what you did"],
  "result": ["Sentences describing the outcomes and impact"]
}}

Interview Response:
\"\"\"
{transcript}
\"\"\"
"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": MISTRAL_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,  # Lower temperature for more consistent parsing
        "max_tokens": 300
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(OPENROUTER_API, headers=headers, json=body)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            print("STAR Analysis Response:", content)
            
            result = json.loads(content)
            return {
                "situation": result.get("situation", []),
                "task": result.get("task", []),
                "action": result.get("action", []),
                "result": result.get("result", [])
            }
            
        except Exception as e:
            print("Error in STAR analysis:", e)
            return {
                "situation": [],
                "task": [],
                "action": [],
                "result": []
            }