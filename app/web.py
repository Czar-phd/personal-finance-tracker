from __future__ import annotations
from collections import defaultdict
from datetime import date, datetime
from calendar import monthrange

from flask import Blueprint, render_template, request
from sqlalchemy import extract

from .db import db
from .finance.models import Transaction

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

    # Aggregate: by category (name or 'Uncategorized') and by day
    category_totals = defaultdict(float)
    daily_totals = defaultdict(float)

    for t in txs:
        cat = t.category.name if t.category else "Uncategorized"
        category_totals[cat] += float(t.amount)
        day = t.date.day
        daily_totals[day] += float(t.amount)

    # Build arrays for charts
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
