import uuid
from sqlalchemy import Column, ForeignKey, Numeric, Date
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    amount = Column(Numeric(precision=14, scale=2), nullable=False)
