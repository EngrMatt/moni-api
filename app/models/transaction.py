from sqlalchemy import Column, String, ForeignKey, Numeric, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.db.base import Base

class TransactionRecord(Base):
    __tablename__ = "transaction_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False)
    
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=True)
    type = Column(String, nullable=False, default="expense", server_default="expense")
    amount = Column(Numeric(precision=18, scale=2), nullable=False)
    currency = Column(String(3), nullable=False, default="TWD", server_default="TWD")
    title = Column(String, nullable=True)
    note = Column(Text, nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    entry_source = Column(String, nullable=False, default="manual", server_default="manual")
    status = Column(String, nullable=False, default="confirmed", server_default="confirmed")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User")
    category = relationship("Category", back_populates="transactions")
    account = relationship("Account")
