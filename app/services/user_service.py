# app/services/user_service.py
from sqlalchemy.orm import Session
import uuid
from app.repositories.user_repository import UserRepository

class UserService:
    def __init__(self):
        self.user_repo = UserRepository()

    def get_user(self, db: Session, user_id: uuid.UUID):
        return self.user_repo.get_by_id(db, user_id)