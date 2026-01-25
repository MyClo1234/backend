from pydantic import BaseModel, field_validator
from app.domains.user.schema import UserResponse


class UserLogin(BaseModel):
    username: str
    password: str

    @field_validator("password")
    @classmethod
    def validate_password_length(cls, v):
        if len(v.encode("utf-8")) > 72:
            raise ValueError("비밀번호는 72바이트를 초과할 수 없습니다.")
        return v


class AuthResponse(BaseModel):
    success: bool
    token: str
    user: UserResponse
