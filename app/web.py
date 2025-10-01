from __future__ import annotations
from collections import defaultdict
from datetime import date
from calendar import monthrange

from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy import extract

from .db import db
from .finance.models import Transaction, Category
from .finance.services import guess_category_by_merchant
from dateutil.parser import parse as parse_date

bp = Blueprint("web", __name__, template_folder="templates")

def _month_year():
    qs = request.args.get("month")  # YYYY-MM
    if qs:
        y, m = qs.split("-")
        return int(y), int(m)
    today = date.today()
    return today.year, today.month

@bp.get("/dashboard")
def dashboard():
    year, month = _month_year()
    q = (
        db.session.query(Transaction)
        .filter(extract("year", Transaction.date) == year)
        .filter(extract("month", Transaction.date) == month)
        .order_by(Transaction.date.desc(), Transaction.id.desc())
    )
    txs = q.all()

    # Aggregate totals
    category_totals = defaultdict(float)
    daily_totals = defaultdict(float)
    for t in txs:
        cat = t.category.name if t.category else "Uncategorized"
        category_totals[cat] += float(t.amount)
        daily_totals[t.date.day] += float(t.amount)

    # Chart data
    labels_cat = list(category_totals.keys())
    data_cat = [round(category_totals[k], 2) for k in labels_cat]

    days_in_month = monthrange(year, month)[1]
    labels_days = list(range(1, days_in_month + 1))
    data_days = [round(daily_totals.get(d, 0.0), 2) for d in labels_days]

    total = round(sum(data_cat), 2)

    return render_template(
        "dashboard.html",
        year=year,
        month=month,
        txs=txs,
        labels_cat=labels_cat,
        data_cat=data_cat,
        labels_days=labels_days,
        data_days=data_days,
        total=total,
    )

@bp.route("/add", methods=["GET", "POST"])
def add_transaction():
    if request.method == "POST":
        f = request.form
        date_str = (f.get("date") or "").strip()
        amount_str = (f.get("amount") or "").strip()
        merchant = (f.get("merchant") or "").strip() or None
        notes = (f.get("notes") or "").strip() or None
        category_id = f.get("category_id") or None
        try:
            dt = parse_date(date_str).date()
            amount = float(amount_str)
        except Exception:
            flash("Please provide a valid date (YYYY-MM-DD) and amount.", "error")
            return redirect(url_for("web.add_transaction"))

        if not category_id:
            cat = guess_category_by_merchant(merchant)
            if cat:
                category_id = cat.id

        t = Transaction(
            date=dt,
            amount=amount,
            merchant=merchant,
            notes=notes,
            category_id=int(category_id) if category_id else None,
            currency="USD",
            source="manual",
        )
        db.session.add(t)
        db.session.commit()
        flash("Transaction added.", "ok")
        return redirect(url_for("web.dashboard", month=f"{dt.year:04d}-{dt.month:02d}"))

    # GET
    y, m = _month_year()
    categories = db.session.query(Category).order_by(Category.type.asc(), Category.name.asc()).all()
    return render_template("add.html", categories=categories, year=y, month=m)
