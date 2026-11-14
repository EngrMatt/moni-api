from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import uuid

from app.schemas.user_schema import UserResponse
from app.services.user_service import UserService
from app.db.session import get_db

router = APIRouter(prefix="/users", tags=["users"])
user_service = UserService()

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
    # 注意：資料庫用的是 UUID，所以參數型別要改
    user = user_service.get_user(db=db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user