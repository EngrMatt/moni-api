import uuid
from sqlalchemy import Column, String, ForeignKey, Boolean, Numeric, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    account_type = Column(String, nullable=False)  # cash, bank, ewallet, credit_card, other
    currency = Column(String(3), nullable=False, default="TWD", server_default="TWD")
    opening_balance = Column(Numeric(precision=14, scale=2), nullable=False, default=0, server_default="0")
    is_archived = Column(Boolean, nullable=False, default=False, server_default="false")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
