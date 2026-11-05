"""
utils/extract_text.py
Resume (PDF/DOCX) se clean text nikalne ke liye utility functions.
"""

import os
import re
import pdfplumber
import docx


def extract_text_from_pdf(file_path):
    """PDF file se saara text nikalta hai."""
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def extract_text_from_docx(file_path):
    """DOCX file se saara text nikalta hai."""
    doc = docx.Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text


def clean_text(text):
    """
    Extra spaces, extra newlines, aur special characters clean karta hai
    taaki embeddings/matching ke liye text ready ho jaye.
    """
    text = text.replace("\r", " ")
    text = re.sub(r"\n+", "\n", text)          # multiple newlines -> single
    text = re.sub(r"[ \t]+", " ", text)        # multiple spaces/tabs -> single
    text = re.sub(r"[^\x00-\x7F]+", " ", text) # non-ascii chars hatao (icons/bullets)
    return text.strip()


def extract_resume_text(file_path):
    """
    File extension ke hisaab se sahi extractor call karta hai
    aur clean text return karta hai.
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        raw_text = extract_text_from_pdf(file_path)
    elif ext == ".docx":
        raw_text = extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}. Sirf .pdf aur .docx supported hain.")

    return clean_text(raw_text)


# Quick test (isse run karke check kar sakte ho ki function kaam kar raha hai ya nahi)
if __name__ == "__main__":
    sample_path = "../sample_resume.pdf" # apni test file ka path yaha do
    if os.path.exists(sample_path):
        print(extract_resume_text(sample_path))
    else:
        print("Test ke liye sample_resume.pdf ya .docx file yaha rakh do.")