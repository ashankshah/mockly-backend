"""
- David Chung
- Returns AI-powered STAR analysis using Mistral-7B-Instruct-v0.2
"""

import httpx
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration constants
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_API = "https://openrouter.ai/api/v1/chat/completions"
MISTRAL_MODEL = "mistralai/mistral-7b-instruct-v0.2"

# Default response for error cases
DEFAULT_STAR_RESPONSE = {
    "situation": [],
    "task": [],
    "action": [],
    "result": [],
    "score": 0
}

async def analyze_star_structure(transcript: str):
    """
    Analyze interview response using STAR format with Mistral-7B-Instruct-v0.2
    """
    if not OPENROUTER_KEY:
        print("Warning: OPENROUTER_API_KEY not found")
        return DEFAULT_STAR_RESPONSE

    prompt = f"""
You are an expert behavioral interview coach. Given the following candidate's interview response, break it down into STAR format (Situation, Task, Action, Result).

For each category, extract the relevant sentences. If a category is not present, use an empty array. Then, assign an objective score from 0 to 75 based on clarity, completeness, and impact of the response.

Respond with *only* valid JSON in this exact format:
{{
  "situation": ["Sentence describing the context or background"],
  "task": ["Sentence describing what needed to be accomplished"],
  "action": ["Sentences describing what you did"],
  "result": ["Sentences describing the outcomes and impact"],
  "score": [Score from 0-75, inclusive]
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
        "temperature": 0.2,
        "max_tokens": 300
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(OPENROUTER_API, headers=headers, json=body)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            
            result = json.loads(content)
            return {
                "situation": result.get("situation", []),
                "task": result.get("task", []),
                "action": result.get("action", []),
                "result": result.get("result", []),
                "score": result.get("score", 0)
            }
            
        except Exception as e:
            print("Error in STAR analysis:", e)
            return DEFAULT_STAR_RESPONSE