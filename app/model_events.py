from datetime import datetime
from sqlalchemy import event
from .finance.models import Category, Transaction

@event.listens_for(Category, "before_update", propagate=True)
def _cat_touch(mapper, connection, target):
    target.updated_at = datetime.utcnow()

@event.listens_for(Transaction, "before_update", propagate=True)
def _tx_touch(mapper, connection, target):
    target.updated_at = datetime.utcnow()
