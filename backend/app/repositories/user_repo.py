from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User, RefreshToken

class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_id(self, user_id: str) -> User | None:
        stmt = select(User).where(User.id == user_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def create(self, email: str, password_hash: str, full_name: str | None) -> User:
        user = User(email=email, password_hash=password_hash, full_name=full_name)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def create_refresh_token(self, user_id: str, jti: str, expires_at: datetime) -> RefreshToken:
        refresh_token = RefreshToken(user_id=user_id, jti=jti, expires_at=expires_at)
        self.session.add(refresh_token)
        self.session.commit()
        self.session.refresh(refresh_token)
        return refresh_token

    def get_refresh_token(self, jti: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.jti == jti)
        return self.session.execute(stmt).scalar_one_or_none()

    def revoke_refresh_token(self, jti: str) -> None:
        stmt = select(RefreshToken).where(RefreshToken.jti == jti)
        refresh_token = self.session.execute(stmt).scalar_one_or_none()
        if refresh_token:
            refresh_token.revoked = True
            self.session.commit()
