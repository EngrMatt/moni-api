from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.timeutil import taipei_today
from app.db import get_db
from app.models.user import User
from app.routers.deps import get_current_user
from app.schemas.ledger_schema import (
    BudgetResponse,
    BudgetUpdate,
    HomeResponse,
    TransactionCreate,
    TransactionItem,
    TransactionListResponse,
)
from app.services.ledger_service import (
    create_transaction,
    home_summary,
    list_transactions,
    upsert_current_budget,
    void_transaction,
)

router = APIRouter(tags=["ledger"])


@router.get("/home", response_model=HomeResponse)
def get_home(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return home_summary(db, current_user)


@router.get("/transactions", response_model=TransactionListResponse)
def get_transactions(
    on: date | None = Query(default=None),
    type: str = Query(default="expense"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_transactions(db, current_user, on or taipei_today(), type)


@router.post("/transactions", response_model=TransactionItem)
def post_transaction(
    payload: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_transaction(db, current_user, payload)


@router.delete("/transactions/{transaction_id}")
def delete_transaction(
    transaction_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    void_transaction(db, current_user, transaction_id)
    return {"message": "已刪除"}


@router.put("/budgets/current", response_model=BudgetResponse)
def put_current_budget(
    payload: BudgetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return upsert_current_budget(db, current_user, payload.amount)
