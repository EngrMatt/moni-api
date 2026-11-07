from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, generate_refresh_token, hash_refresh_token
from app.core.settings import settings
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.user_schema import TokenResponse


def _refresh_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="無效的 refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )


def issue_tokens(db: Session, user: User) -> TokenResponse:
    raw_refresh = generate_refresh_token()
    access_token = create_access_token(str(user.id), user.token_version)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(raw_refresh),
            expires_at=expires_at,
        )
    )
    db.commit()
    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


def invalidate_user_sessions(db: Session, user: User, commit: bool = True) -> None:
    user.token_version = (user.token_version or 0) + 1
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user.id,
        RefreshToken.revoked_at.is_(None),
    ).update(
        {RefreshToken.revoked_at: datetime.now(timezone.utc)},
        synchronize_session=False,
    )
    if commit:
        db.commit()
        db.refresh(user)


def rotate_refresh_token(db: Session, raw_token: str) -> TokenResponse:
    record = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == hash_refresh_token(raw_token))
        .with_for_update()
        .first()
    )
    if record is None:
        raise _refresh_error()

    now = datetime.now(timezone.utc)
    if record.revoked_at is not None:
        user = db.query(User).filter(User.id == record.user_id).first()
        if user is not None:
            invalidate_user_sessions(db, user)
        raise _refresh_error()

    if record.expires_at <= now:
        raise _refresh_error()

    user = db.query(User).filter(User.id == record.user_id).first()
    if user is None or not user.is_active:
        record.revoked_at = now
        db.commit()
        raise _refresh_error()

    record.revoked_at = now
    db.flush()
    return issue_tokens(db, user)


def revoke_refresh_token(db: Session, raw_token: str) -> None:
    record = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == hash_refresh_token(raw_token))
        .first()
    )
    if record is None or record.revoked_at is not None:
        return
    record.revoked_at = datetime.now(timezone.utc)
    db.commit()
