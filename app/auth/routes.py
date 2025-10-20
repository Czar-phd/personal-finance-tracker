from __future__ import annotations
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from passlib.hash import bcrypt
from ..db import db
from .models import User

bp = Blueprint("auth", __name__)

@bp.get("/login")
def login_form():
    if current_user.is_authenticated:
        return redirect(url_for("web.dashboard"))
    return render_template("login.html")

@bp.post("/login")
def login_submit():
    email = request.form.get("email","").strip().lower()
    password = request.form.get("password","")
    user = db.session.query(User).filter_by(email=email).first()
    if not user or not bcrypt.verify(password, user.password_hash):
        flash("Invalid credentials", "error")
        return redirect(url_for("auth.login_form"))
    login_user(user, remember=True)
    return redirect(url_for("web.dashboard"))

@bp.post("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login_form"))
