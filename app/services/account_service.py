from sqlalchemy.orm import Session
from uuid import UUID

from app.models.account import Account


def ensure_cash_account(db: Session, user_id: UUID) -> Account:
    account = (
        db.query(Account)
        .filter(Account.user_id == user_id, Account.account_type == "cash", Account.is_archived.is_(False))
        .order_by(Account.created_at.asc())
        .first()
    )
    if account:
        return account
    account = Account(user_id=user_id, name="現金", account_type="cash", currency="TWD", opening_balance=0)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account
