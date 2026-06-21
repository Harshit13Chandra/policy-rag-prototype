import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError

from app.config import get_settings
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.models.user import User
from app.repositories.user_repo import UserRepository

class EmailAlreadyExistsError(Exception):
    pass

class InvalidCredentialsError(Exception):
    pass

class InvalidTokenError(Exception):
    pass

class AuthService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    def register(self, email: str, password: str, full_name: str | None) -> User:
        if self.repo.get_by_email(email) is not None:
            raise EmailAlreadyExistsError("Email is already registered")
        
        hashed = hash_password(password)
        return self.repo.create(email=email, password_hash=hashed, full_name=full_name)

    def login(self, email: str, password: str) -> tuple[str, str, User]:
        user = self.repo.get_by_email(email)
        if user is None:
            raise InvalidCredentialsError("Invalid email or password")
            
        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")
            
        access_token = create_access_token(user.id)
        
        jti = str(uuid.uuid4())
        refresh_token = create_refresh_token(user.id, jti)
        
        settings = get_settings()
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
        self.repo.create_refresh_token(user_id=user.id, jti=jti, expires_at=expires_at)
        
        return access_token, refresh_token, user

    def refresh(self, refresh_token: str) -> str:
        try:
            payload = decode_token(refresh_token)
        except JWTError:
            raise InvalidTokenError("Invalid or expired refresh token")
            
        if payload.get("type") != "refresh":
            raise InvalidTokenError("Invalid token type")
            
        jti = payload.get("jti")
        if not jti:
            raise InvalidTokenError("Invalid token format")
            
        token_record = self.repo.get_refresh_token(jti)
        if token_record is None or token_record.revoked:
            raise InvalidTokenError("Refresh token is invalid or has been revoked")
            
        user_id = payload.get("sub")
        if not user_id:
            raise InvalidTokenError("Invalid token format")
            
        new_access_token = create_access_token(user_id)
        return new_access_token
