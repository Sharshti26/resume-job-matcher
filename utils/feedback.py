"""
utils/feedback.py
Resume, JD, aur match score ke basis par LLM se auto-feedback, chat, roadmap
aur interview questions generate karne ke liye.

AI providers (is order me try hote hain, ek fail ho to agla):
1. Groq  (GROQ_API_KEY ho to) - llama-3.3-70b, phir llama-3.1-8b (fast, free)
2. Gemini (GEMINI_API_KEY)    - flash-lite, phir flash
"""

import os
import json
import time
from dotenv import load_dotenv
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

try:
    from groq import Groq
except ImportError:  # groq package install na ho to bhi app chalta rahe
    Groq = None

# .env file se GEMINI_API_KEY load karta hai
load_dotenv()

# IMPORTANT: Apni API key .env file me daalo, seedha code me mat likho
# API key free me yahan se milegi: https://aistudio.google.com/app/apikey
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Main model: Flash-Lite (free tier me ~500 requests/day, 10/minute)
model = genai.GenerativeModel("gemini-flash-lite-latest")
# Backup model: main model busy ya limit khatam ho to ye try hota hai (alag quota)
backup_model = genai.GenerativeModel("gemini-flash-latest")

# Groq (pehli pasand): alag-alag models ke alag free quota hote hain
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_MODELS = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
groq_client = Groq(api_key=GROQ_API_KEY) if (Groq and GROQ_API_KEY) else None

BUSY_MESSAGE = "AI abhi busy hai. Kripya 1 minute ruk kar dobara try karo."

# Google ki taraf ki temporary dikkatein (server busy / timeout)
TRANSIENT_ERRORS = (
    google_exceptions.ServiceUnavailable,
    google_exceptions.InternalServerError,
    google_exceptions.DeadlineExceeded,
)


class AIBusyError(Exception):
    """Gemini busy hai ya free limit (429) lag gayi."""


def _generate(llm, prompt):
    # retry=None: library ka auto-retry band (har retry quota me count hota hai)
    response = llm.generate_content(prompt, request_options={"retry": None, "timeout": 60})
    return response.text.strip()


def _generate_groq(model_name, prompt):
    response = groq_client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=1200,
    )
    return response.choices[0].message.content.strip()


def _extract_json(raw_text):
    """
    AI ke jawab me se JSON nikalta hai - chahe ```json fences ho ya
    aage-peeche extra text. Pehle '{' se aakhri '}' tak ka hissa parse karta hai.
    """
    start = raw_text.find("{")
    end = raw_text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("JSON nahi mila")
    return json.loads(raw_text[start:end + 1])


def _ask(prompt):
    """
    Gemini ko call karta hai - pehle main model, phir backup model:
    - Server busy (503): 3 second ruk kar ek baar aur try, phir agla model
    - Free limit (429) ya model nahi mila: seedha agle model par
    - Sab fail ho jaye to AIBusyError (friendly message dikhta hai)
    """
    # 1) Groq pehle (agar key set hai)
    if groq_client:
        for name in GROQ_MODELS:
            try:
                return _generate_groq(name, prompt)
            except Exception as e:
                print("[AI DEBUG] Groq", name, "fail:", type(e).__name__, str(e)[:150])

    # 2) Phir Gemini
    for llm in (model, backup_model):
        for attempt in range(2):
            try:
                return _generate(llm, prompt)
            except google_exceptions.ResourceExhausted as e:
                print("[AI DEBUG] Free limit (429):", str(e)[:200])
                break
            except google_exceptions.NotFound as e:
                print("[AI DEBUG] Model nahi mila:", str(e)[:200])
                break
            except TRANSIENT_ERRORS as e:
                print("[AI DEBUG] Model busy:", type(e).__name__)
                if attempt == 0:
                    time.sleep(3)
            except ValueError as e:
                # response.text fail (jaise safety block / khali jawab)
                print("[AI DEBUG] Khali ya blocked jawab:", e)
                raise AIBusyError(BUSY_MESSAGE)
            except google_exceptions.GoogleAPIError as e:
                print("[AI DEBUG] API error:", type(e).__name__, str(e)[:200])
                break

    raise AIBusyError(BUSY_MESSAGE)


def generate_feedback(resume_text, jd_text, match_score, missing_keywords=None):
    """
    Resume aur JD ke basis par LLM se structured feedback generate karta hai:
    - strengths
    - missing_skills
    - suggestions
    """
    missing_str = ", ".join(missing_keywords) if missing_keywords else "N/A"

    prompt = f"""
You are an expert career coach and resume reviewer.

Resume:
{resume_text}

Job Description:
{jd_text}

Match Score: {match_score}%
Possible Missing Keywords: {missing_str}

Based on the above, respond ONLY with valid JSON (no markdown, no extra text) in this exact format:
{{
  "strengths": ["point 1", "point 2"],
  "missing_skills": ["skill 1", "skill 2"],
  "suggestions": ["suggestion 1", "suggestion 2", "suggestion 3"]
}}
"""

    try:
        raw_text = _ask(prompt)
    except AIBusyError:
        return {"strengths": [], "missing_skills": [], "suggestions": [BUSY_MESSAGE]}

    try:
        feedback_json = _extract_json(raw_text)
    except ValueError:
        print("[AI DEBUG] Feedback JSON parse fail. Raw:", raw_text[:300])
        feedback_json = {
            "strengths": [],
            "missing_skills": [],
            "suggestions": [raw_text]  # fallback: raw text hi de do
        }

    return feedback_json


def chat_about_resume(resume_text, jd_text, chat_history, user_message):
    """
    Resume aur JD ke context ke saath conversational chat chalata hai.
    chat_history: list of {"role": "user"/"assistant", "text": "..."} dicts (pichli baatcheet)
    user_message: naya sawaal jo user ne abhi poocha
    """
    history_text = ""
    for turn in chat_history:
        speaker = "User" if turn["role"] == "user" else "Assistant"
        history_text += f"{speaker}: {turn['text']}\n"

    prompt = f"""
You are a friendly, expert career coach helping a candidate improve their resume
for a specific job. Keep answers short, practical, and specific to their resume
and the job description below.

Resume:
{resume_text}

Job Description:
{jd_text}

Conversation so far:
{history_text}

User's new question: {user_message}

Reply with a short, helpful, conversational answer (2-5 sentences). Plain text only, no JSON.
"""

    try:
        return _ask(prompt)
    except AIBusyError:
        return BUSY_MESSAGE


def generate_roadmap(missing_skills, jd_text):
    """
    Missing skills ke basis par ek priority-order learning roadmap banata hai,
    har skill ke saath ek free resource suggestion ke saath.
    """
    skills_str = ", ".join(missing_skills) if missing_skills else "N/A"

    prompt = f"""
Based on this job description and these missing skills, create a learning roadmap.

Job Description:
{jd_text}

Missing Skills: {skills_str}

Respond ONLY with valid JSON (no markdown, no extra text) in this exact format - order
skills from most important/urgent to least important for this job:
{{
  "roadmap": [
    {{"skill": "skill name", "why": "one short sentence on why it matters for this job", "resource": "a specific free resource or platform to learn it (e.g. 'freeCodeCamp - SQL course')"}}
  ]
}}
Include at most 5 skills.
"""

    try:
        raw_text = _ask(prompt)
    except AIBusyError:
        return []

    try:
        return _extract_json(raw_text).get("roadmap", [])
    except ValueError:
        print("[AI DEBUG] Roadmap JSON parse fail. Raw:", raw_text[:300])
        return []


# Quick test
if __name__ == "__main__":
    sample_resume_text = "Experienced Python developer skilled in Flask, SQL and Machine Learning."
    sample_jd_text = "Looking for a backend developer with Python, Flask, SQL and cloud deployment experience."
    sample_score = 75.5
    sample_missing = ["cloud", "deployment"]

    result = generate_feedback(sample_resume_text, sample_jd_text, sample_score, sample_missing)
    print(json.dumps(result, indent=2))


def generate_interview_questions(resume_text, jd_text, missing_skills=None):
    """
    Resume aur JD ke basis par likely interview questions generate karta hai,
    har sawaal ke saath ek chhota answering tip.
    """
    missing_str = ", ".join(missing_skills) if missing_skills else "N/A"

    prompt = f"""
You are a technical interviewer preparing to interview this candidate for the role below.

Resume:
{resume_text}

Job Description:
{jd_text}

Gaps identified: {missing_str}

Generate 5 likely interview questions this candidate should prepare for - a mix of
technical questions based on their resume skills and questions probing the gaps.
For each, give a short one-line tip on how to answer well.

Respond ONLY with valid JSON (no markdown) in this exact format:
{{
  "questions": [
    {{"question": "...", "tip": "..."}}
  ]
}}
"""

    try:
        raw_text = _ask(prompt)
    except AIBusyError:
        return []

    try:
        return _extract_json(raw_text).get("questions", [])
    except ValueError:
        print("[AI DEBUG] Interview JSON parse fail. Raw:", raw_text[:300])
        return []