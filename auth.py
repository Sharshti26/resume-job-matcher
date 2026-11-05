"""
auth.py
Signup, Login, aur Logout routes - Flask Blueprint ke roop me.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("Saari fields bharna zaroori hai.")
            return redirect(url_for("auth.signup"))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Is email se account pehle se bana hua hai. Login karo.")
            return redirect(url_for("auth.login"))

        new_user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
        )
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for("index"))

    return render_template("signup.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash("Email ya password galat hai.")
            return redirect(url_for("auth.login"))

        login_user(user)
        return redirect(url_for("index"))

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))