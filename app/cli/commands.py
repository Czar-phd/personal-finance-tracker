import click
from datetime import date as _date
from ..db import db
from ..finance.models import Category, Transaction

def _get_or_create_category(name: str, type_: str = "expense") -> Category:
    cat = db.session.query(Category).filter_by(name=name).first()
    if cat:
        return cat
    cat = Category(name=name, type=type_)
    db.session.add(cat)
    db.session.commit()
    return cat

def _ensure_seed_categories():
    for n in ("Groceries", "Transport", "Coffee", "Shopping", "Income"):
        _get_or_create_category(n, "income" if n == "Income" else "expense")

def _add_tx(d, amt, merchant, catname):
    cat = _get_or_create_category(catname)
    t = Transaction(date=d, amount=amt, merchant=merchant, category_id=cat.id)
    db.session.add(t)

def _seed_month(year: int, month: int):
    from datetime import date
    _ensure_seed_categories()
    samples = [
        (1,  4.75, "Starbucks Market", "Coffee"),
        (2,  62.90, "Safeway",          "Groceries"),
        (4,  18.20, "Uber Trip",        "Transport"),
        (7,  12.99, "Amazon",           "Shopping"),
        (10, 5.25,  "Starbucks HQ",     "Coffee"),
        (15, 32.10, "Whole Foods",      "Groceries"),
        (20, 21.00, "Uber Trip",        "Transport"),
        (25, 7.10,  "Starbucks Market", "Coffee"),
    ]
    for day, amt, merchant, cat in samples:
        _add_tx(date(year, month, min(day, 28)), amt, merchant, cat)
    db.session.commit()

def register_cli(app):
    @app.cli.command("init-db")
    def init_db_cmd():
        """Create tables and seed basic categories."""
        with app.app_context():
            db.create_all()
            _ensure_seed_categories()
            click.echo("DB initialized and seeded.")

    @app.cli.command("seed-demo")
    @click.option("--month", help="YYYY-MM (defaults to current month)")
    def seed_demo(month: str | None):
        """Insert sample transactions for charts."""
        with app.app_context():
            if month:
                y, m = map(int, month.split("-"))
            else:
                today = _date.today()
                y, m = today.year, today.month
            _seed_month(y, m)
            click.echo(f"Seeded demo data for {y:04d}-{m:02d}.")
