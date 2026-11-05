"""
app.py
Main Flask application - resume upload, matching, feedback, login/signup,
match history, chat, scorecard, roadmap aur comparison - sab yahan se control hota hai.
"""

import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from flask_login import LoginManager, login_required, current_user
from dotenv import load_dotenv

from models import db, User, MatchHistory
from auth import auth_bp
from utils.extract_text import extract_resume_text
from utils.matcher import calculate_match_score, extract_missing_keywords
from utils.pdf_report import generate_pdf_report
from utils.feedback import generate_feedback, chat_about_resume, generate_roadmap, generate_interview_questions

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-this")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///resume_matcher.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


app.register_blueprint(auth_bp)


@app.route("/", methods=["GET"])
@login_required
def index():
    return render_template("index.html")


@app.route("/match", methods=["POST"])
@login_required
def match():
    resume_file = request.files.get("resume")
    jd_text = request.form.get("job_description", "").strip()

    if not resume_file or resume_file.filename == "":
        return render_template("index.html", error="Please resume file upload karo.")

    if not jd_text:
        return render_template("index.html", error="Please job description daalo.")

    resume_path = os.path.join(app.config["UPLOAD_FOLDER"], resume_file.filename)
    resume_file.save(resume_path)

    resume_text = extract_resume_text(resume_path)

    match_score = calculate_match_score(resume_text, jd_text)
    missing_keywords = extract_missing_keywords(resume_text, jd_text)

    feedback = generate_feedback(resume_text, jd_text, match_score, missing_keywords)

    history_entry = MatchHistory(
        user_id=current_user.id,
        resume_filename=resume_file.filename,
        resume_text=resume_text,
        job_description=jd_text,
        match_score=match_score,
        strengths=json.dumps(feedback.get("strengths", [])),
        missing_skills=json.dumps(feedback.get("missing_skills", [])),
        suggestions=json.dumps(feedback.get("suggestions", [])),
    )
    db.session.add(history_entry)
    db.session.commit()

    return render_template(
        "result.html",
        match_score=match_score,
        feedback=feedback,
        missing_keywords=missing_keywords,
        match_id=history_entry.id,
        resume_filename=resume_file.filename,
    )


@app.route("/dashboard")
@login_required
def dashboard():
    history = (
        MatchHistory.query.filter_by(user_id=current_user.id)
        .order_by(MatchHistory.created_at.desc())
        .all()
    )
    total_checks = len(history)
    avg_score = round(sum(h.match_score for h in history) / total_checks, 2) if total_checks else 0

    return render_template(
        "dashboard.html",
        history=history,
        total_checks=total_checks,
        avg_score=avg_score,
    )


@app.route("/batch", methods=["GET", "POST"])
@login_required
def batch():
    if request.method == "GET":
        return render_template("batch.html")

    resume_files = request.files.getlist("resumes")
    jd_text = request.form.get("job_description", "").strip()

    if not resume_files or resume_files[0].filename == "":
        return render_template("batch.html", error="Please kam se kam ek resume upload karo.")

    if not jd_text:
        return render_template("batch.html", error="Please job description daalo.")

    results = []
    for resume_file in resume_files:
        resume_path = os.path.join(app.config["UPLOAD_FOLDER"], resume_file.filename)
        resume_file.save(resume_path)

        resume_text = extract_resume_text(resume_path)
        match_score = calculate_match_score(resume_text, jd_text)
        missing_keywords = extract_missing_keywords(resume_text, jd_text)

        results.append({
            "filename": resume_file.filename,
            "score": match_score,
            "missing_keywords": missing_keywords[:8],
        })

        history_entry = MatchHistory(
            user_id=current_user.id,
            resume_filename=resume_file.filename,
            resume_text=resume_text,
            job_description=jd_text,
            match_score=match_score,
            strengths=json.dumps([]),
            missing_skills=json.dumps(missing_keywords[:8]),
            suggestions=json.dumps([]),
        )
        db.session.add(history_entry)

    db.session.commit()
    results.sort(key=lambda r: r["score"], reverse=True)

    return render_template("batch.html", results=results)


# ---------------- Chat With Your Resume ----------------

@app.route("/chat/<int:match_id>", methods=["GET", "POST"])
@login_required
def chat(match_id):
    entry = MatchHistory.query.filter_by(id=match_id, user_id=current_user.id).first_or_404()

    session_key = f"chat_{match_id}"
    chat_history = session.get(session_key, [])

    if request.method == "POST":
        user_message = request.form.get("message", "").strip()
        if user_message:
            reply = chat_about_resume(entry.resume_text or "", entry.job_description, chat_history, user_message)
            chat_history.append({"role": "user", "text": user_message})
            chat_history.append({"role": "assistant", "text": reply})
            session[session_key] = chat_history

    return render_template("chat.html", entry=entry, chat_history=chat_history)


# ---------------- Shareable Score Card ----------------

@app.route("/scorecard/<int:match_id>")
@login_required
def scorecard(match_id):
    entry = MatchHistory.query.filter_by(id=match_id, user_id=current_user.id).first_or_404()
    return render_template("scorecard.html", entry=entry)


# ---------------- Skill Gap Roadmap ----------------

@app.route("/roadmap/<int:match_id>")
@login_required
def roadmap(match_id):
    entry = MatchHistory.query.filter_by(id=match_id, user_id=current_user.id).first_or_404()
    missing_skills = json.loads(entry.missing_skills) if entry.missing_skills else []
    roadmap_items = generate_roadmap(missing_skills, entry.job_description)
    return render_template("roadmap.html", entry=entry, roadmap=roadmap_items)


# ---------------- Interview Questions ----------------

@app.route("/interview/<int:match_id>")
@login_required
def interview(match_id):
    entry = MatchHistory.query.filter_by(id=match_id, user_id=current_user.id).first_or_404()
    missing_skills = json.loads(entry.missing_skills) if entry.missing_skills else []
    questions = generate_interview_questions(entry.resume_text or "", entry.job_description, missing_skills)
    return render_template("interview.html", entry=entry, questions=questions)


# ---------------- PDF Report Download ----------------

@app.route("/download-pdf/<int:match_id>")
@login_required
def download_pdf(match_id):
    entry = MatchHistory.query.filter_by(id=match_id, user_id=current_user.id).first_or_404()
    pdf_file = generate_pdf_report(entry)
    return send_file(
        pdf_file,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="resume-match-report.pdf",
    )


# ---------------- Before/After Comparison ----------------

@app.route("/compare", methods=["GET", "POST"])
@login_required
def compare():
    history = (
        MatchHistory.query.filter_by(user_id=current_user.id)
        .order_by(MatchHistory.created_at.desc())
        .all()
    )

    entry_a = entry_b = None
    if request.method == "POST":
        id_a = request.form.get("entry_a")
        id_b = request.form.get("entry_b")
        entry_a = MatchHistory.query.filter_by(id=id_a, user_id=current_user.id).first()
        entry_b = MatchHistory.query.filter_by(id=id_b, user_id=current_user.id).first()

    return render_template("compare.html", history=history, entry_a=entry_a, entry_b=entry_b)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, use_reloader=False)