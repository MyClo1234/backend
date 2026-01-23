# .env.example 파일 수정 가이드

## 수정 내용

`.env.example` 파일의 20-22번째 줄을 다음과 같이 수정하세요:

**변경 전:**
```env
# Weather
WEATHER_DATA_ENCODING_KEY=
WEATHER_DATA_DECODING_KEY=
```

**변경 후:**
```env
# Weather API Configuration (기상청 중기예보 조회서비스)
# 공공데이터포털(data.go.kr)에서 발급받은 서비스 키를 URL-encoded 형식으로 저장
# 주의: 이미 URL-encoded된 키를 그대로 저장 (추가 인코딩하지 않음)
KMA_SERVICE_KEY=
```

## 수정 방법

1. `backend/.env.example` 파일을 열기
2. 20-22번째 줄을 위의 내용으로 교체
3. 저장

또는 다음 명령어로 확인:

```bash
cd backend
cat .env.example
```
