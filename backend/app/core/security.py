from datetime import datetime, timedelta, timezone
import uuid

import argon2
from jose import jwt
import jose.exceptions

from app.config import get_settings

ph = argon2.PasswordHasher()

def hash_password(plain_password: str) -> str:
    return ph.hash(plain_password)

def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        ph.verify(password_hash, plain_password)
        return True
    except argon2.exceptions.VerifyMismatchError:
        return False
    except Exception:
        return False

def create_access_token(user_id: str) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "iat": now,
        "type": "access"
    }
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt

def create_refresh_token(user_id: str, jti: str) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.refresh_token_expire_days)
    
    to_encode = {
        "sub": str(user_id),
        "jti": str(jti),
        "exp": expire,
        "iat": now,
        "type": "refresh"
    }
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt

def decode_token(token: str) -> dict:
    settings = get_settings()
    # If the token is invalid or expired, jose.exceptions.JWTError will be raised and propagate.
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
