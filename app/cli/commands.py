import click
from flask import current_app
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
                    db.session.add(Category(name=n, type="income" if n=="Income" else "expense"))
                db.session.commit()
            click.echo("DB initialized and seeded.")
