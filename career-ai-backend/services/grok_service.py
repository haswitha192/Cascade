import os
import requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"


def generate_learning_roadmap(job_title, missing_skills):

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
    A candidate is missing the following skills for the job role '{job_title}':

    {missing_skills}

    Generate a structured learning roadmap including:
    - Total duration
    - Weekly breakdown
    - Certifications
    - Projects
    """

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    response = requests.post(GROQ_ENDPOINT, headers=headers, json=payload)

    print("GROQ STATUS:", response.status_code)
    print("GROQ RAW RESPONSE:", response.text)

    result = response.json()

    if "choices" not in result:
        return f"Groq API error: {result}"

    return result["choices"][0]["message"]["content"]