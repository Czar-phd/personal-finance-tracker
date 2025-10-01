from app import create_app
from app.db import db
from app.finance.models import Transaction, Category
from datetime import date

def make_app():
    app = create_app()
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI="sqlite:///:memory:")
    with app.app_context():
        db.create_all()
        c = Category(name="Coffee", type="expense")
        db.session.add(c); db.session.commit()
        db.session.add(Transaction(date=date(2025,9,1), amount=4.50, merchant="Starbucks", category_id=c.id))
        db.session.commit()
    return app

def test_csv_export_ok():
    app = make_app()
    client = app.test_client()
    r = client.get("/api/transactions.csv?month=2025-09")
    assert r.status_code == 200
    assert r.mimetype == "text/csv"
    body = r.data.decode()
    assert "date,merchant,category,amount,currency,notes" in body
    assert "2025-09-01" in body
    assert "Starbucks" in body

def test_delete_route_ok():
    app = make_app()
    client = app.test_client()
    with app.app_context():
        tx = db.session.query(Transaction).first()
        tx_id = tx.id
    r = client.post(f"/delete/{tx_id}", follow_redirects=False)
    assert r.status_code in (302, 303)
    with app.app_context():
        assert db.session.get(Transaction, tx_id) is None
