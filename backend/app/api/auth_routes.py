from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from jose import JWTError

from app.schemas.auth_schema import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    UserPublic,
    RefreshResponse
)
from app.dependencies import get_db, get_current_user
from app.repositories.user_repo import UserRepository
from app.services.auth_service import (
    AuthService,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    InvalidTokenError
)
from app.core.security import decode_token
from app.config import get_settings
from app.models.user import User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(request_data: RegisterRequest, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    service = AuthService(repo)
    
    try:
        user = service.register(
            email=request_data.email,
            password=request_data.password,
            full_name=request_data.full_name
        )
    except EmailAlreadyExistsError:
        raise HTTPException(status_code=409, detail="Email already registered")
        
    return RegisterResponse(id=str(user.id), email=user.email)

@router.post("/login", response_model=LoginResponse)
def login(request_data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    service = AuthService(repo)
    
    try:
        access_token, refresh_token, user = service.login(
            email=request_data.email,
            password=request_data.password
        )
    except InvalidCredentialsError:
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    settings = get_settings()
    
    # IMPORTANT: samesite="lax" and secure=False are for local prototype only.
    # This must change to secure=True and samesite="strict" before any real deployment.
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=settings.refresh_token_expire_days * 86400
    )
    
    user_public = UserPublic(id=str(user.id), email=user.email, full_name=user.full_name)
    return LoginResponse(access_token=access_token, user=user_public)

@router.post("/refresh", response_model=RefreshResponse)
def refresh(request: Request, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token provided")
        
    repo = UserRepository(db)
    service = AuthService(repo)
    
    try:
        new_access_token = service.refresh(refresh_token)
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
        
    return RefreshResponse(access_token=new_access_token)

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        repo = UserRepository(db)
        try:
            payload = decode_token(refresh_token)
            jti = payload.get("jti")
            if jti:
                repo.revoke_refresh_token(jti)
        except JWTError:
            pass  # Even if decoding fails, we still clear the cookie
            
    response.delete_cookie("refresh_token")

@router.get("/me", response_model=UserPublic)
def get_me(current_user: User = Depends(get_current_user)):
    return UserPublic(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name
    )
