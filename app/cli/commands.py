import click
from ..db import db
from ..finance.models import Category

def register_cli(app):
    @app.cli.command("init-db")
    def init_db_cmd():
        """Create tables and seed basic categories."""
        with app.app_context():
            db.create_all()
            if db.session.query(Category).count() == 0:
                for n in ("Groceries", "Transport", "Coffee", "Shopping", "Income"):
                    db.session.add(Category(name=n, type="income" if n == "Income" else "expense"))
                db.session.commit()
            click.echo("DB initialized and seeded.")

@register_cli
def _noop(_app=None):  # keeps flake quiet if imported directly
    pass

def _ensure_seed_categories():
    from ..finance.models import Category
    if db.session.query(Category).count() == 0:
        for n in ("Groceries", "Transport", "Coffee", "Shopping", "Income"):
            db.session.add(Category(name=n, type="income" if n=="Income" else "expense"))
        db.session.commit()

def _cat_by_name(name):
    from ..finance.models import Category
    return db.session.query(Category).filter_by(name=name).first()

def _add_tx(d, amt, merchant, catname):
    from ..finance.models import Transaction
    t = Transaction(date=d, amount=amt, merchant=merchant, category_id=_cat_by_name(catname).id)
    db.session.add(t)

def _seed_month(year, month):
    from datetime import date
    _ensure_seed_categories()
    samples = [
        (1,  4.75, "Starbucks Market", "Coffee"),
        (2,  62.90,"Safeway",          "Groceries"),
        (4,  18.20,"Uber Trip",        "Transport"),
        (7,  12.99,"Amazon",           "Shopping"),
        (10, 5.25, "Starbucks HQ",     "Coffee"),
        (15, 32.10,"Whole Foods",      "Groceries"),
        (20, 21.00,"Uber Trip",        "Transport"),
        (25, 7.10, "Starbucks Market", "Coffee"),
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
        from datetime import date as _date
        with app.app_context():
            if month:
                y, m = map(int, month.split("-"))
            else:
                today = _date.today()
                y, m = today.year, today.month
            _seed_month(y, m)
            click.echo(f"Seeded demo data for {y:04d}-{m:02d}.")
