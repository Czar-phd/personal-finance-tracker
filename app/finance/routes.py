from __future__ import annotations
from dateutil.parser import parse as parse_date
from flask import Blueprint, request, jsonify
from sqlalchemy import extract
from ..db import db
from .models import Category, Transaction
from .services import guess_category_by_merchant

bp = Blueprint("finance", __name__)

# --------- categories ----------
@bp.get("/categories")
def list_categories():
    q = db.session.query(Category).filter_by(user_id=current_user.id).order_by(Category.name.asc()).all()
    return jsonify([{"id": c.id, "name": c.name, "type": c.type} for c in q])

@bp.post("/categories")
def create_category():
    payload = request.get_json() or {}
    name = payload.get("name")
    type_ = payload.get("type", "expense")
    if not name:
        return jsonify({"error": "name required"}), 400
    cat = Category(name=name, type=type_)
    db.session.add(cat)
    db.session.commit()
    return jsonify({"id": cat.id, "name": cat.name, "type": cat.type}), 201

@bp.put("/categories/<int:cat_id>")
def update_category(cat_id: int):
    payload = request.get_json() or {}
    cat = db.session.get(Category, cat_id)
    if not cat:
        return jsonify({"error": "not found"}), 404
    cat.name = payload.get("name", cat.name)
    cat.type = payload.get("type", cat.type)
    db.session.commit()
    return jsonify({"id": cat.id, "name": cat.name, "type": cat.type})

@bp.delete("/categories/<int:cat_id>")
def delete_category(cat_id: int):
    cat = db.session.get(Category, cat_id)
    if not cat:
        return jsonify({"error": "not found"}), 404
    db.session.delete(cat)
    db.session.commit()
    return "", 204

# --------- transactions ----------
@bp.get("/transactions")
def list_transactions():
    month = request.args.get("month")
    q = db.session.query(Transaction)
    if month:
        y, m = month.split("-")
        q = q.filter(
            extract("year", Transaction.date) == int(y)
        ).filter(
            extract("month", Transaction.date) == int(m)
        )
    q = q.order_by(Transaction.date.desc(), Transaction.id.desc())
    items = []
    for t in q.all():
        items.append({
            "id": t.id,
            "date": t.date.isoformat(),
            "amount": float(t.amount),
            "currency": t.currency,
            "merchant": t.merchant,
            "notes": t.notes,
            "category_id": t.category_id,
            "category_name": t.category.name if t.category else None,
        })
    return jsonify(items)

@bp.post("/transactions")
def create_transaction():
    payload = request.get_json() or {}
    try:
        dt = parse_date(payload["date"]).date()
        amount = float(payload["amount"])
    except Exception:
        return jsonify({"error": "date (YYYY-MM-DD) and amount required"}), 400

    category_id = payload.get("category_id")
    merchant = payload.get("merchant")
    if not category_id:
        cat = guess_category_by_merchant(merchant)
        if cat:
            category_id = cat.id

    t = Transaction(
        date=dt,
        amount=amount,
        currency=payload.get("currency", "USD"),
        merchant=merchant,
        notes=payload.get("notes"),
        category_id=category_id,
        source="manual",
    )
    db.session.add(t)
    db.session.commit()
    return jsonify({"id": t.id}), 201

@bp.put("/transactions/<int:tx_id>")
def update_transaction(tx_id: int):
    payload = request.get_json() or {}
    t = db.session.get(Transaction, tx_id)
    if not t:
        return jsonify({"error": "not found"}), 404
    if "date" in payload:
        t.date = parse_date(payload["date"]).date()
    if "amount" in payload:
        t.amount = float(payload["amount"])
    for field in ("currency", "merchant", "notes"):
        if field in payload:
            setattr(t, field, payload[field])
    if "category_id" in payload:
        t.category_id = payload["category_id"]
    db.session.commit()
    return jsonify({"id": t.id})

@bp.delete("/transactions/<int:tx_id>")
def delete_transaction(tx_id: int):
    t = db.session.get(Transaction, tx_id)
    if not t:
        return jsonify({"error": "not found"}), 404
    db.session.delete(t)
    db.session.commit()
    return "", 204

# --------- util: init + seed ----------
@bp.post("/admin/init-db")
def init_db():
    db.create_all()
    if db.session.query(Category).count() == 0:
        for n in ("Groceries", "Transport", "Coffee", "Shopping", "Income"):
            db.session.add(Category(name=n, type="income" if n == "Income" else "expense"))
        db.session.commit()
    return jsonify({"ok": True})

from flask import Response

@bp.get("/transactions.csv")
def export_transactions_csv():
    month = request.args.get("month")
    if not month:
        return jsonify({"error": "month required as YYYY-MM"}), 400
    try:
        y, m = map(int, month.split("-"))
    except Exception:
        return jsonify({"error": "bad month format"}), 400

    q = (
        db.session.query(Transaction)
        .filter(extract("year", Transaction.date) == y)
        .filter(extract("month", Transaction.date) == m)
        .order_by(Transaction.date.asc(), Transaction.id.asc())
    )

    def esc(s):
        if s is None:
            return ""
        s = str(s).replace('"', '""')
        return f'"{s}"'

    lines = ["date,merchant,category,amount,currency,notes"]
    for t in q.all():
        cat = t.category.name if t.category else ""
        line = ",".join([
            t.date.isoformat(),
            esc(t.merchant),
            esc(cat),
            f"{float(t.amount):.2f}",
            esc(t.currency or "USD"),
            esc(t.notes),
        ])
        lines.append(line)
    csv = "\n".join(lines) + "\n"
    return Response(csv, mimetype="text/csv")
