"""
models.py
Database models - User accounts aur Match History store karne ke liye.
SQLite database use kar rahe hain (file-based, koi server install nahi karna).
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User account - login/signup ke liye."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Ek user ke multiple match history records ho sakte hain
    matches = db.relationship("MatchHistory", backref="user", lazy=True)


class MatchHistory(db.Model):
    """Har resume-JD match check ka record store karta hai."""
    __tablename__ = "match_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    resume_filename = db.Column(db.String(255), nullable=False)
    resume_text = db.Column(db.Text)  # chat feature ke liye resume ka poora text
    job_description = db.Column(db.Text, nullable=False)
    match_score = db.Column(db.Float, nullable=False)

    strengths = db.Column(db.Text)       # JSON string ke roop me store hoga
    missing_skills = db.Column(db.Text)  # JSON string ke roop me store hoga
    suggestions = db.Column(db.Text)     # JSON string ke roop me store hoga

    created_at = db.Column(db.DateTime, default=datetime.utcnow)