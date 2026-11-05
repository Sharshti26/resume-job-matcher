"""
utils/embeddings.py
Resume aur Job Description (JD) text ko embeddings (numeric vectors) me
convert karne ke liye utility functions.
"""

from sentence_transformers import SentenceTransformer

# Model ek hi baar load hota hai (thoda time lagega pehli baar)
model = SentenceTransformer('all-MiniLM-L6-v2')


def get_embedding(text):
    """
    Diye gaye text ko ek numeric vector (embedding) me convert karta hai.
    Ye vector resume/JD ke 'meaning' ko represent karta hai.
    """
    embedding = model.encode(text)
    return embedding


def get_embeddings_batch(text_list):
    """
    Multiple texts (jaise resume ke chunks ya multiple JDs) ko
    ek saath embeddings me convert karta hai - single texts se zyada fast hai.
    """
    embeddings = model.encode(text_list)
    return embeddings


# Quick test
if __name__ == "__main__":
    sample_resume_text = "Experienced Python developer skilled in Flask, SQL and Machine Learning."
    sample_jd_text = "Looking for a backend developer with Python, Flask and database experience."

    resume_emb = get_embedding(sample_resume_text)
    jd_emb = get_embedding(sample_jd_text)

    print("Resume embedding shape:", resume_emb.shape)
    print("JD embedding shape:", jd_emb.shape)
    print("\nPehle 5 numbers (resume embedding ka):", resume_emb[:5])