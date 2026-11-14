from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    category_id: UUID
    amount: Decimal = Field(gt=0)
    type: str = "expense"
    title: str = Field(min_length=1, max_length=80)
    note: str | None = None
    occurred_at: datetime | None = None
    account_id: UUID | None = None


class TransactionItem(BaseModel):
    id: UUID
    category_id: UUID
    category_name: str
    category_icon: str | None = None
    category_color: str | None = None
    account_id: UUID | None = None
    account_name: str
    type: str
    amount: Decimal
    currency: str
    title: str | None = None
    note: str | None = None
    occurred_at: datetime


class TransactionListResponse(BaseModel):
    date: str
    type: str
    day_total: Decimal
    month_total: Decimal
    items: list[TransactionItem]


class HomeCategory(BaseModel):
    id: UUID
    name: str
    icon_type: str | None = None
    color: str | None = None
    amount: Decimal


class HomeResponse(BaseModel):
    display_name: str
    email: str
    today: str
    month_expense: Decimal
    month_income: Decimal
    today_expense: Decimal
    budget_amount: Decimal | None = None
    safe_to_spend_today: Decimal | None = None
    days_remaining: int
    budget_progress: float | None = None
    categories: list[HomeCategory]


class BudgetUpdate(BaseModel):
    amount: Decimal = Field(gt=0)


class BudgetResponse(BaseModel):
    amount: Decimal
    period_start: str
    period_end: str
