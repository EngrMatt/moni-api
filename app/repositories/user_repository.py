# app/repositories/user_repository.py
from sqlalchemy.orm import Session
from app.models.user import User
import uuid

class UserRepository:
    def get_by_id(self, db: Session, user_id: uuid.UUID):
        return db.query(User).filter(User.id == user_id).first()