from app import create_app
from app.db import db
from app.auth.models import User
from app.finance.models import Category, Transaction
from passlib.hash import bcrypt
from datetime import date

def _login(client, email, password):
    return client.post("/login", data={"email": email, "password": password}, follow_redirects=False)

def test_user_scoping_isolated():
    app = create_app()
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI="sqlite:///:memory:")
    with app.app_context():
        db.create_all()
        a = User(email="a@example.com", password_hash=bcrypt.hash("a"))
        b = User(email="b@example.com", password_hash=bcrypt.hash("b"))
        db.session.add_all([a,b]); db.session.commit()

        # Seed A data
        ca = Category(name="A-Cat", type="expense", user_id=a.id)
        db.session.add(ca); db.session.flush()
        db.session.add(Transaction(user_id=a.id, category_id=ca.id, amount=1, currency="USD", date=date(2024,1,1)))
        db.session.commit()

        # Seed B data
        cb = Category(name="B-Cat", type="expense", user_id=b.id)
        db.session.add(cb); db.session.flush()
        db.session.add(Transaction(user_id=b.id, category_id=cb.id, amount=2, currency="USD", date=date(2024,1,2)))
        db.session.commit()

    client = app.test_client()

    # Login as A, see only A
    _login(client, "a@example.com", "a")
    ra = client.get("/api/transactions")
    assert ra.status_code == 200
    assert b"B-Cat" not in ra.data
    assert b"A-Cat" in ra.data

    # Login as B, see only B
    _login(client, "b@example.com", "b")
    rb = client.get("/api/transactions")
    assert rb.status_code == 200
    assert b"A-Cat" not in rb.data
    assert b"B-Cat" in rb.data
