"""
utils/matcher.py
Resume aur Job Description (JD) ke embeddings ke beech cosine similarity
nikal kar match score calculate karne ke liye.
"""

from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from utils.embeddings import get_embedding


def calculate_match_score(resume_text, jd_text):
    """
    Resume aur JD text ka embedding banata hai, phir unke beech
    cosine similarity nikal kar match percentage return karta hai.
    """
    resume_emb = get_embedding(resume_text)
    jd_emb = get_embedding(jd_text)

    # cosine_similarity ko 2D array chahiye, isliye reshape kar rahe hain
    resume_emb = np.array(resume_emb).reshape(1, -1)
    jd_emb = np.array(jd_emb).reshape(1, -1)

    similarity = cosine_similarity(resume_emb, jd_emb)[0][0]

    # similarity value 0 se 1 ke beech hoti hai, ise percentage me convert karte hain
    match_percentage = round(float(similarity) * 100, 2)

    return match_percentage


def extract_missing_keywords(resume_text, jd_text):
    """
    Simple keyword-based check: JD ke important words me se kaunse
    resume me missing hain (basic version, baad me improve kar sakte hain).
    """
    resume_words = set(resume_text.lower().split())
    jd_words = set(jd_text.lower().split())

    # Sirf lambe words (4+ letters) lo taaki 'the', 'and' jaise common words na aayein
    jd_keywords = {word.strip(".,()") for word in jd_words if len(word) > 3}
    resume_keywords = {word.strip(".,()") for word in resume_words if len(word) > 3}

    missing = jd_keywords - resume_keywords
    return list(missing)


# Quick test
if __name__ == "__main__":
    sample_resume_text = "Experienced Python developer skilled in Flask, SQL and Machine Learning."
    sample_jd_text = "Looking for a backend developer with Python, Flask, SQL and cloud deployment experience."

    score = calculate_match_score(sample_resume_text, sample_jd_text)
    missing = extract_missing_keywords(sample_resume_text, sample_jd_text)

    print(f"Match Score: {score}%")
    print(f"Missing Keywords (JD me hain, resume me nahi): {missing}")