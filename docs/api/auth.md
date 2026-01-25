# 인증 API (Auth)

사용자 인증 및 회원가입 관련 API입니다.

## Base URL

```
/api/auth
```

## 엔드포인트

### 회원가입

새로운 사용자를 등록합니다.

**Endpoint**
```http
POST /auth/signup
```

**Request Body**
```json
{
  "username": "user@example.com",
  "password": "password123",
  "age": 25,
  "height": 170.5,
  "weight": 65.0,
  "gender": "male",
  "body_shape": "normal"
}
```

**Response**
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "user@example.com",
    "age": 25,
    "height": 170.5,
    "weight": 65.0,
    "gender": "male",
    "body_shape": "normal"
  }
}
```

**예제**
```bash
curl -X POST http://localhost:7071/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test@example.com",
    "password": "mypassword",
    "age": 25,
    "height": 175,
    "weight": 70
  }'
```

---

### 로그인

사용자 인증 후 JWT 토큰을 발급합니다.

**Endpoint**
```http
POST /auth/login
```

**Request Body**
```json
{
  "username": "user@example.com",
  "password": "password123"
}
```

**Response**
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "user@example.com",
    "age": 25,
    "height": 170.5,
    "weight": 65.0,
    "gender": "male",
    "body_shape": "normal"
  }
}
```

**예제**
```bash
curl -X POST http://localhost:7071/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test@example.com",
    "password": "mypassword"
  }'
```

---

### 로그아웃

사용자를 로그아웃 처리합니다.

!!! info "클라이언트 측 처리"
    서버에서는 특별한 작업을 하지 않습니다. 클라이언트에서 저장된 토큰을 삭제하면 됩니다.

**Endpoint**
```http
POST /auth/logout
```

**Response**
```json
{
  "success": true,
  "message": "Successfully logged out"
}
```

## 인증 토큰 사용

로그인 후 받은 JWT 토큰은 이후 모든 인증이 필요한 요청에 포함해야 합니다.

**헤더 형식**
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**예제**
```bash
curl -X GET http://localhost:7071/api/users/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## 에러 응답

### 401 Unauthorized
```json
{
  "detail": "아이디 또는 비밀번호가 잘못되었습니다."
}
```

### 400 Bad Request
```json
{
  "detail": "Username already registered"
}
```

## 비밀번호 규칙

!!! warning "비밀번호 제한"
    비밀번호는 UTF-8 인코딩 기준 **72바이트를 초과할 수 없습니다**.

## 보안

- 비밀번호는 **bcrypt**로 해싱되어 저장됩니다
- JWT 토큰은 **HS256** 알고리즘으로 서명됩니다
- 토큰 유효기간은 설정에 따라 다릅니다

## 관련 API

- [사용자 API](../user.md) - 프로필 관리
- [옷장 API](wardrobe.md) - 옷장 아이템 관리
