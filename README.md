

# ResumeMatch AI - AI Resume-to-Job Matcher with Auto-Feedback
**Live demo:** https://resume-job-matcher-1-dmag.onrender.com
A Flask web app that compares a resume with a job description, gives a match score, and uses a generative AI model (Google Gemini) to produce personalised feedback, a skill-gap roadmap, likely interview questions and an interactive resume chat.

## Features

- **Resume parsing** - extracts text from PDF and DOCX resumes
- **Semantic matching** - sentence embeddings (`all-MiniLM-L6-v2`) + cosine similarity give a match score (0-100%)
- **AI feedback** - strengths, missing skills and suggestions generated from the resume and job description
- **Chat about your resume** - ask follow-up questions in the context of your resume and the job
- **Skill-gap roadmap** - prioritised learning path with free resources
- **Interview question generator** - likely questions with answering tips
- **PDF report and shareable score card** - download results as PDF or image
- **User accounts** - signup/login, with a private history per user
- **Dashboard** - total checks, average score and score-trend chart
- **Batch mode** - compare many resumes against one job description
- **Before/after comparison** - see how a revised resume improved the score
- Graceful handling of AI rate limits (friendly message instead of a crash)

## Tech Stack

| Area | Tools |
|------|-------|
| Backend | Python, Flask, Flask-Login, Flask-SQLAlchemy |
| Database | SQLite |
| NLP / ML | sentence-transformers, scikit-learn (cosine similarity) |
| Generative AI | Google Gemini API |
| Parsing / Reports | pdfplumber, python-docx, ReportLab |
| Frontend | HTML, CSS, Jinja2, Chart.js |

## How It Works

1. The user uploads a resume and pastes a job description.
2. Text is extracted and cleaned.
3. Both texts are converted to embeddings and compared with cosine similarity to get the match score.
4. The resume, job description and score are sent to the Gemini model, which returns structured feedback (JSON).
5. Results are saved in the database and shown on the result page, with links to chat, roadmap, interview questions, PDF and score card.

## Project Structure

```
app.py              Flask app and routes
auth.py             Signup / login / logout
models.py           Database models (User, MatchHistory)
utils/
  extract_text.py   PDF/DOCX text extraction
  embeddings.py     Sentence embeddings
  matcher.py        Match score and missing keywords
  feedback.py       Gemini calls (feedback, chat, roadmap, interview questions)
  pdf_report.py     PDF report generation
templates/          HTML pages
static/style.css    Styling
```

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your keys
copy .env.example .env        # then edit .env and add your Gemini API key
```

Get a free Gemini API key from https://aistudio.google.com/app/apikey

```bash
# 4. Run
python app.py
```

Open http://127.0.0.1:5000, sign up, and upload a resume.

## Notes

- The free Gemini tier has request limits. If the AI is busy, the app still shows the match score and a friendly message.
- Never commit your `.env` file.
- The live demo runs in lite mode (keyword-based matching) to fit free hosting; the full version uses sentence-transformers.
## Screenshots

_Add screenshots here (result page, dashboard, roadmap, score card)._

## Future Improvements

- FAISS vector database for chunk-level retrieval from resumes
- Cloud deployment
- Unit tests

## Author

Sharshti Singhai