from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.db import get_db
from app.models.user import User
from app.schemas.user_schema import RefreshTokenRequest, TokenResponse, UserCreate, UserResponse
from app.routers.deps import get_current_user
from app.services.account_service import ensure_cash_account
from app.services.auth_service import invalidate_user_sessions, issue_tokens, revoke_refresh_token, rotate_refresh_token
from app.services.category_service import init_user_categories

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/check-email")
def check_email(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email, User.is_active == True).first()
    return {"available": user is None}


@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email, User.is_active == True).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email 已被註冊")

    pending = db.query(User).filter(User.email == user.email, User.is_active == False).first()
    if pending:
        pending.hashed_password = hash_password(user.password)
        pending.is_active = True
        invalidate_user_sessions(db, pending, commit=False)
        db.add(pending)
        db.commit()
        db.refresh(pending)
        new_user = pending
    else:
        new_user = User(email=user.email, hashed_password=hash_password(user.password), full_name=user.full_name, is_active=True)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    init_user_categories(db, new_user.id)
    ensure_cash_account(db, new_user.id)
    return new_user


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """username 填註冊用的 email。"""
    db_user = db.query(User).filter(User.email == form.username, User.is_active == True).first()
    if not db_user or not verify_password(form.password, db_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="信箱或密碼錯誤")
    return issue_tokens(db, db_user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshTokenRequest, db: Session = Depends(get_db)):
    return rotate_refresh_token(db, body.refresh_token)


@router.post("/logout")
def logout(body: RefreshTokenRequest, db: Session = Depends(get_db)):
    revoke_refresh_token(db, body.refresh_token)
    return {"message": "Logged out"}


@router.post("/admin/activate/{user_id}")
def activate_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = True
    db.commit()
    return {"message": "User activated"}
