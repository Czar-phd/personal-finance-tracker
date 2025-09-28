from app import create_app
from app.db import db
from app.finance.models import Category
from sqlalchemy.pool import StaticPool

def setup_app():
    app = create_app()
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite://",
        SQLALCHEMY_ENGINE_OPTIONS={
            "poolclass": StaticPool,
            "connect_args": {"check_same_thread": False},
        },
    )
    with app.app_context():
        db.drop_all()
        db.create_all()
        db.session.add(Category(name="Groceries", type="expense"))
        db.session.add(Category(name="Income", type="income"))
        db.session.commit()
    return app

def test_create_and_list_transactions_autocat():
    app = setup_app()
    client = app.test_client()

    # count before
    before = client.get("/api/transactions?month=2025-09").get_json()
    before_len = len(before)

    # create one
    r = client.post("/api/transactions", json={
        "date": "2025-09-01",
        "amount": 5.75,
        "merchant": "Starbucks Market",
        "notes": "latte"
    })
    assert r.status_code == 201

    # count after
    after = client.get("/api/transactions?month=2025-09").get_json()
    assert len(after) == before_len + 1

    # newest item should be Starbucks + category resolved
    tx = after[0]  # list is sorted desc by date/id
    assert tx["merchant"].upper().startswith("STARBUCKS")
    assert tx["category_name"] is not None

def test_categories_crud():
    app = setup_app()
    client = app.test_client()

    r = client.post("/api/categories", json={"name": "Pets", "type": "expense"})
    assert r.status_code == 201
    cat_id = r.get_json()["id"]

    r = client.put(f"/api/categories/{cat_id}", json={"name": "Pet Care"})
    assert r.status_code == 200
    assert r.get_json()["name"] == "Pet Care"

    r = client.get("/api/categories")
    assert r.status_code == 200
    assert any(c["name"] == "Pet Care" for c in r.get_json())

    r = client.delete(f"/api/categories/{cat_id}")
    assert r.status_code == 204
