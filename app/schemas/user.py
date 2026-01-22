from pydantic import BaseModel


# 회원가입 시 받을 데이터 규격
class UserCreate(BaseModel):
    username: str
    password: str


# API 응답으로 보낼 데이터 규격
class UserResponse(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True
