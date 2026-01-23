feat: User ID를 UUID로 변경 및 이미지 저장 경로 개선

## 주요 변경 사항

### 1. User 테이블 UUID 마이그레이션
- User 모델의 id를 Integer에서 UUID로 변경
- 모든 관련 Foreign Key (ClosetItem, OutfitLog, ChatSession)의 user_id를 UUID로 변경
- Alembic 마이그레이션 파일 생성 및 실행 (a1b2c3d4e5f6_change_user_id_to_uuid.py)
- 기존 users 테이블 초기화 후 UUID 기반으로 재생성

### 2. 스키마 및 서비스 코드 업데이트
- 모든 스키마의 user_id/id 필드를 UUID 타입으로 변경
  - UserResponse, ClosetItemResponse, OutfitResponse, ChatSessionResponse
- 서비스 및 라우터 코드에서 user_id 타입을 UUID로 수정
  - user_service.py, wardrobe_manager.py, wardrobe_routes.py

### 3. JWT 토큰 개선
- JWT 토큰에 user_id (UUID 문자열) 추가
- 기존 username (sub) 유지로 호환성 보장
- 토큰에서 user_id를 직접 추출 가능하도록 개선

### 4. 인증 방식 개선
- OAuth2PasswordBearer를 HTTPBearer로 변경
- Swagger UI에서 Bearer 토큰 직접 입력 방식으로 개선

### 5. 이미지 GET API 추가
- GET /api/wardrobe/users/me/images: 토큰에서 자동으로 user_id 추출
- GET /api/wardrobe/users/{user_id}/images: 특정 사용자 옷장 이미지 조회
- Blob Storage에서 JSON 파일을 읽어 attributes 복원

### 6. 이미지 저장 경로 개선
- 기존: attributes_{timestamp}_{random}.jpg (컨테이너 루트)
- 변경: users/{user_id}/{YMD}/{uuid}.{ext} 형식으로 저장
- 예시: users/64580554-959b-4cb3-b7b1-e1a348de40e0/20260123/a1b2c3d4-e5f6-7890-abcd-ef1234567890.jpg

### 7. 데이터 처리 개선
- category 필드가 dict 형태일 때 main 값을 추출하여 String으로 저장
- sub_category도 dict에서 추출하도록 개선

## 마이그레이션
- 기존 데이터는 초기화됨 (users 테이블 및 모든 관련 테이블)
- 새로운 UUID 기반 스키마로 재생성

## Breaking Changes
- User.id가 Integer에서 UUID로 변경됨
- 모든 user_id 관련 필드가 UUID 타입으로 변경됨
- 기존 데이터는 마이그레이션 과정에서 삭제됨
