import os
import requests
import json

GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"


def _call_groq(prompt: str, temperature: float = 0.4) -> dict | str:
    api_key = os.environ["GROQ_API_KEY"]
    response = requests.post(
        GROQ_ENDPOINT,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature
        },
        timeout=30
    )
    return response.json()["choices"][0]["message"]["content"]


def generate_interview_questions(resume_text: str, skills: list) -> list:
    """
    Generate 5 personalised interview questions based on the candidate's
    resume text and extracted skills.  Returns a list of question strings.
    """
    skills_str = ", ".join(skills) if skills else "not specified"
    truncated = resume_text[:3000]

    prompt = f"""You are a senior technical interviewer conducting a real job interview.

Based on the following candidate resume and their skills, generate exactly 5 personalised
interview questions that are directly relevant to their background, projects, and skills.

Resume:
---
{truncated}
---

Candidate Skills: {skills_str}

Rules:
- Questions must be specific to THIS candidate's resume (mention their actual projects, roles, or skills)
- Mix question types: 1 introductory, 2 technical/skill-based, 1 behavioural, 1 career-goal
- Keep each question concise (1–2 sentences max)
- Output ONLY a valid JSON array of 5 strings, e.g.:
["Question 1", "Question 2", "Question 3", "Question 4", "Question 5"]
- No preamble, no explanation, ONLY the JSON array.
"""

    raw = _call_groq(prompt, temperature=0.5)

    # Strip markdown code fences if present
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]

    try:
        questions = json.loads(cleaned.strip())
        if isinstance(questions, list) and len(questions) >= 1:
            return questions[:5]
    except Exception:
        pass

    # Fallback: split numbered lines
    lines = [l.strip().lstrip("0123456789.)- ") for l in raw.split("\n") if l.strip()]
    questions = [l for l in lines if len(l) > 10]
    return questions[:5] if questions else [
        "Tell me about yourself and your professional background.",
        "What are your strongest technical skills?",
        "Describe a difficult problem you solved.",
        "Why do you want this role?",
        "Where do you see yourself in five years?"
    ]


def evaluate_answer(question: str, answer: str) -> dict:
    """Evaluate a candidate's answer and return structured scores + feedback."""
    
    if not answer or not answer.strip():
        return {
            "technical_score": 0,
            "communication_score": 0,
            "confidence_score": 0,
            "overall_score": 0,
            "feedback": "No speech detected. Please make sure your microphone is working and try again."
        }

    prompt = f"""You are an expert technical interviewer.

Question:
{question}

Candidate Answer:
{answer}

Evaluate the answer and return ONLY valid JSON (no markdown, no extra text):

{{
  "technical_score": <0-100>,
  "communication_score": <0-100>,
  "confidence_score": <0-100>,
  "overall_score": <0-100>,
  "feedback": "<short, 1-2 sentence improvement advice>"
}}
"""

    raw = _call_groq(prompt, temperature=0.2)

    # Strip markdown code fences
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]

    return json.loads(cleaned.strip())