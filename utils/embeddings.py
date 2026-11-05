"""
utils/embeddings.py
Resume aur Job Description (JD) text ko embeddings (numeric vectors) me convert karta hai.

Do mode hain:
- Full mode (default): sentence-transformers (all-MiniLM-L6-v2) - semantic matching, torch chahiye.
- Lite mode (LITE_MODE=1): sklearn HashingVectorizer - keyword/phrase based, bahut halka,
  free hosting (512 MB RAM) par chal jata hai.
"""

import os

LITE_MODE = os.environ.get("LITE_MODE", "0") == "1"

if LITE_MODE:
    from sklearn.feature_extraction.text import HashingVectorizer

    _vectorizer = HashingVectorizer(
        n_features=4096,
        ngram_range=(1, 2),
        stop_words="english",
        alternate_sign=False,
        norm="l2",
    )

    def get_embedding(text):
        """Text ko ek fixed-size vector me badalta hai (lite mode)."""
        return _vectorizer.transform([text]).toarray()[0]

    def get_embeddings_batch(text_list):
        """Multiple texts ko ek saath vectors me badalta hai (lite mode)."""
        return _vectorizer.transform(text_list).toarray()

else:
    from sentence_transformers import SentenceTransformer

    # Model ek hi baar load hota hai (thoda time lagega pehli baar)
    model = SentenceTransformer("all-MiniLM-L6-v2")

    def get_embedding(text):
        """Text ko semantic embedding me badalta hai (full mode)."""
        return model.encode(text)

    def get_embeddings_batch(text_list):
        """Multiple texts ko ek saath embeddings me badalta hai (full mode)."""
        return model.encode(text_list)


# Quick test
if __name__ == "__main__":
    mode = "LITE" if LITE_MODE else "FULL"
    resume_emb = get_embedding("Experienced Python developer skilled in Flask, SQL and Machine Learning.")
    jd_emb = get_embedding("Looking for a backend developer with Python, Flask and database experience.")
    print("Mode:", mode)
    print("Resume embedding shape:", resume_emb.shape)
    print("JD embedding shape:", jd_emb.shape)