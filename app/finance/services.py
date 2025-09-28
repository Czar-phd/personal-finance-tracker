from __future__ import annotations
from typing import Optional
from .models import Category
from ..db import db

# very small keyword->category map (extend later)
DEFAULT_RULES = {
    "STARBUCKS": "Coffee",
    "UBER": "Transport",
    "AMAZON": "Shopping",
    "WHOLE FOODS": "Groceries",
    "SAFEWAY": "Groceries",
}

def get_or_create_category(name: str, type_: str = "expense") -> Category:
    existing = db.session.query(Category).filter(Category.name == name).first()
    if existing:
        return existing
    cat = Category(name=name, type=type_)
    db.session.add(cat)
    db.session.commit()
    return cat

def guess_category_by_merchant(merchant: Optional[str]) -> Optional[Category]:
    if not merchant:
        return None
    up = merchant.upper()
    for key, cat_name in DEFAULT_RULES.items():
        if key in up:
            return get_or_create_category(cat_name, "expense")
    return None
