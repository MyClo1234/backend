from pydantic import BaseModel, field_validator, Field, ConfigDict
from uuid import UUID


# 회원가입 시 받을 데이터 규격
class UserCreate(BaseModel):
    username: str
    password: str
    age: int | None = None
    height: float | None = None
    weight: float | None = None
    gender: str | None = None
    body_shape: str | None = None

    @field_validator("password")
    @classmethod
    def validate_password_length(cls, v):
        if len(v.encode("utf-8")) > 72:
            raise ValueError("비밀번호는 72바이트를 초과할 수 없습니다.")
        return v


# 사용자 정보 수정 시 받을 데이터 규격 (Optional)
class UserUpdate(BaseModel):
    height: float | None = None
    weight: float | None = None
    gender: str | None = None
    body_shape: str | None = None


# API 응답으로 보낼 데이터 규격
class UserResponse(BaseModel):
    id: UUID
    username: str = Field(validation_alias="user_name")
    age: int | None = None
    height: float | None = None
    weight: float | None = None
    gender: str | None = None
    body_shape: str | None = None

    model_config = ConfigDict(from_attributes=True)
