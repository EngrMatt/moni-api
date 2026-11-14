from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.timeutil import as_taipei, day_bounds, month_bounds, taipei_now, taipei_today
from app.models.account import Account
from app.models.budget import Budget
from app.models.category import Category
from app.models.transaction import TransactionRecord
from app.models.user import User
from app.schemas.ledger_schema import TransactionCreate
from app.services.account_service import ensure_cash_account

PREFERRED_CATEGORIES = {"飲食": 0, "交通": 1, "娛樂": 2}


def display_name(user: User) -> str:
    if user.full_name and user.full_name.strip():
        return user.full_name.strip()
    return user.email.split("@")[0]


def _money(value) -> Decimal:
    return Decimal(value or 0).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _sum_between(db: Session, user_id, tx_type: str, start, end) -> Decimal:
    total = (
        db.query(func.coalesce(func.sum(TransactionRecord.amount), 0))
        .filter(
            TransactionRecord.user_id == user_id,
            TransactionRecord.type == tx_type,
            TransactionRecord.status == "confirmed",
            TransactionRecord.occurred_at >= start,
            TransactionRecord.occurred_at < end,
        )
        .scalar()
    )
    return _money(total)


def _category_type(tx_type: str) -> str:
    if tx_type == "expense":
        return "EXPENSE"
    if tx_type == "income":
        return "INCOME"
    raise HTTPException(status_code=400, detail="類型必須是 expense 或 income")


def _current_budget(db: Session, user: User, today: date) -> Budget | None:
    _, _, period_start, period_end = month_bounds(today)
    return (
        db.query(Budget)
        .filter(
            Budget.user_id == user.id,
            Budget.category_id.is_(None),
            Budget.period_start == period_start,
            Budget.period_end == period_end,
        )
        .first()
    )


def to_item(tx: TransactionRecord) -> dict:
    category = tx.category
    account = tx.account
    return {
        "id": tx.id,
        "category_id": tx.category_id,
        "category_name": category.name if category else "",
        "category_icon": category.icon_type if category else None,
        "category_color": category.color if category else None,
        "account_id": tx.account_id,
        "account_name": account.name if account else "現金",
        "type": tx.type,
        "amount": _money(tx.amount),
        "currency": tx.currency,
        "title": tx.title,
        "note": tx.note,
        "occurred_at": tx.occurred_at,
    }


def list_transactions(db: Session, user: User, day: date, tx_type: str) -> dict:
    _category_type(tx_type)
    start, end = day_bounds(day)
    month_start, month_end, _, _ = month_bounds(day)
    items = (
        db.query(TransactionRecord)
        .options(joinedload(TransactionRecord.category), joinedload(TransactionRecord.account))
        .filter(
            TransactionRecord.user_id == user.id,
            TransactionRecord.type == tx_type,
            TransactionRecord.status == "confirmed",
            TransactionRecord.occurred_at >= start,
            TransactionRecord.occurred_at < end,
        )
        .order_by(TransactionRecord.occurred_at.desc())
        .all()
    )
    return {
        "date": day.isoformat(),
        "type": tx_type,
        "day_total": _sum_between(db, user.id, tx_type, start, end),
        "month_total": _sum_between(db, user.id, tx_type, month_start, month_end),
        "items": [to_item(item) for item in items],
    }


def create_transaction(db: Session, user: User, payload: TransactionCreate) -> dict:
    tx_type = payload.type
    expected = _category_type(tx_type)
    category = (
        db.query(Category)
        .filter(Category.id == payload.category_id, Category.user_id == user.id, Category.is_active.is_(True))
        .first()
    )
    if not category:
        raise HTTPException(status_code=404, detail="找不到分類")
    if (category.type or "").upper() != expected:
        raise HTTPException(status_code=400, detail="分類與收支類型不符")

    if payload.account_id:
        account = (
            db.query(Account)
            .filter(Account.id == payload.account_id, Account.user_id == user.id, Account.is_archived.is_(False))
            .first()
        )
        if not account:
            raise HTTPException(status_code=404, detail="找不到帳戶")
    else:
        account = ensure_cash_account(db, user.id)

    occurred_at = as_taipei(payload.occurred_at) if payload.occurred_at else taipei_now()
    record = TransactionRecord(
        user_id=user.id,
        category_id=category.id,
        account_id=account.id,
        type=tx_type,
        amount=_money(payload.amount),
        currency="TWD",
        title=payload.title.strip(),
        note=payload.note,
        occurred_at=occurred_at,
        entry_source="manual",
        status="confirmed",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    record.category = category
    record.account = account
    return to_item(record)


def void_transaction(db: Session, user: User, transaction_id) -> None:
    record = (
        db.query(TransactionRecord)
        .filter(TransactionRecord.id == transaction_id, TransactionRecord.user_id == user.id)
        .first()
    )
    if not record or record.status != "confirmed":
        raise HTTPException(status_code=404, detail="找不到這筆記帳")
    record.status = "voided"
    db.commit()


def home_summary(db: Session, user: User) -> dict:
    today = taipei_today()
    day_start, day_end = day_bounds(today)
    month_start, month_end, _, _ = month_bounds(today)
    last_day = month_end.date() - timedelta(days=1)
    days_remaining = max((last_day - today).days + 1, 1)

    month_expense = _sum_between(db, user.id, "expense", month_start, month_end)
    month_income = _sum_between(db, user.id, "income", month_start, month_end)
    today_expense = _sum_between(db, user.id, "expense", day_start, day_end)

    budget = _current_budget(db, user, today)
    budget_amount = _money(budget.amount) if budget else None
    safe = None
    progress = None
    if budget_amount is not None:
        remaining = budget_amount - month_expense
        if remaining < 0:
            remaining = Decimal("0")
        safe = (remaining / Decimal(days_remaining)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if budget_amount > 0:
            progress = min(float(month_expense / budget_amount), 1)

    categories = (
        db.query(Category)
        .filter(Category.user_id == user.id, Category.is_active.is_(True), func.upper(Category.type) == "EXPENSE")
        .all()
    )
    by_id = {category.id: category for category in categories}
    grouped = (
        db.query(TransactionRecord.category_id, func.coalesce(func.sum(TransactionRecord.amount), 0))
        .filter(
            TransactionRecord.user_id == user.id,
            TransactionRecord.type == "expense",
            TransactionRecord.status == "confirmed",
            TransactionRecord.occurred_at >= month_start,
            TransactionRecord.occurred_at < month_end,
        )
        .group_by(TransactionRecord.category_id)
        .all()
    )
    rolled: dict = {}
    for category_id, amount in grouped:
        category = by_id.get(category_id)
        if category is None:
            continue
        top_id = category.parent_id if category.parent_id in by_id else category.id
        rolled[top_id] = rolled.get(top_id, Decimal("0")) + Decimal(amount)

    cards = []
    for category in categories:
        if category.parent_id:
            continue
        cards.append(
            {
                "id": category.id,
                "name": category.name,
                "icon_type": category.icon_type,
                "color": category.color,
                "amount": _money(rolled.get(category.id, 0)),
            }
        )
    cards.sort(key=lambda item: (-item["amount"], PREFERRED_CATEGORIES.get(item["name"], 9), item["name"]))

    return {
        "display_name": display_name(user),
        "email": user.email,
        "today": today.isoformat(),
        "month_expense": month_expense,
        "month_income": month_income,
        "today_expense": today_expense,
        "budget_amount": budget_amount,
        "safe_to_spend_today": safe,
        "days_remaining": days_remaining,
        "budget_progress": progress,
        "categories": cards[:3],
    }


def upsert_current_budget(db: Session, user: User, amount: Decimal) -> dict:
    today = taipei_today()
    _, _, period_start, period_end = month_bounds(today)
    budget = _current_budget(db, user, today)
    money = _money(amount)
    if budget:
        budget.amount = money
    else:
        budget = Budget(
            user_id=user.id,
            category_id=None,
            period_start=period_start,
            period_end=period_end,
            amount=money,
        )
        db.add(budget)
    db.commit()
    db.refresh(budget)
    return {
        "amount": _money(budget.amount),
        "period_start": budget.period_start.isoformat(),
        "period_end": budget.period_end.isoformat(),
    }
