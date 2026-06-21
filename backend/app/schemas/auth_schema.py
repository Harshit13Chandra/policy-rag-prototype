from pydantic import BaseModel, EmailStr, field_validator

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None

    @field_validator("password")
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        if len(v) < 10:
            raise ValueError("Password must be at least 10 characters long")
        return v

class RegisterResponse(BaseModel):
    id: str
    email: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserPublic(BaseModel):
    id: str
    email: str
    full_name: str | None = None

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic

class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
