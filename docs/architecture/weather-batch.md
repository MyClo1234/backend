# Weather Batch System

## 개요

전국 17개 지역의 기상 데이터를 매일 자동으로 수집하여 데이터베이스에 저장하는 배치 시스템입니다.

## 핵심 기능

- ✅ **자동 스케줄링**: 매일 02:16 KST에 자동 실행
- ✅ **병렬 처리**: 17개 지역 동시 API 호출 (aiohttp + asyncio)
- ✅ **자동 재시도**: 실패 시 자동으로 재시도 (2단계)
- ✅ **멱등성 보장**: 여러 번 실행해도 안전
- ✅ **All or Nothing**: 전체 성공해야만 저장

## 아키텍처

### 계층 구조

```
function_app.py (인프라 계층)
    ↓
app/batch/weather.py (애플리케이션 계층)
    ↓
app/domains/weather/service.py (도메인 계층)
    ↓
app/domains/weather/client.py (외부 API)
```

### 데이터 흐름

```
1. Time Trigger (02:16 KST)
   ↓
2. run_daily_weather_batch(db)
   ↓
3. weather_service.fetchAndLoadWeather(db)
   ↓
4. 오늘 날짜 데이터 삭제 (멱등성)
   ↓
5. 17개 지역 병렬 API 호출
   ↓
6. 데이터 파싱 (TMN, TMX, PTY)
   ↓
7. DB 저장 (전체 성공 시만)
```

## 스케줄 설정

### Time Trigger

```python
@app.schedule(
    schedule="0 16 17 * * *",  # 17:16 UTC = 02:16 KST
    arg_name="myTimer",
    run_on_startup=False,
    use_monitor=False,
)
```

### 시간 계산

- **KST = UTC + 9시간**
- 02:16 KST = 전날 17:16 UTC
- Cron: `0 16 17 * * *` = 매일 17시 16분 0초 (UTC)

### 타이밍 근거

```
02:00 - 기상청 데이터 생성 시작
02:10 - 기상청 데이터 생성 완료
02:16 - 배치 실행 (6분 안전 마진)
```

## 재시도 메커니즘

### 1단계: 배치 내부 재시도 (즉시)

```python
max_retries = 3
# 지수 백오프: 1초 → 3초 → 5초
wait_time = attempt * 2 - 1
```

**타임라인:**
```
02:16:00 - 1차 시도
02:16:01 - 2차 시도 (1초 후)
02:16:04 - 3차 시도 (3초 후)
02:16:09 - 4차 시도 (5초 후)
```

### 2단계: Azure Functions 자동 재시도 (5분 간격)

`host.json` 설정:
```json
{
  "retry": {
    "strategy": "fixedDelay",
    "maxRetryCount": 3,
    "delayInterval": "00:05:00"
  }
}
```

**타임라인:**
```
02:16:09 - 배치 실패 (Exception 발생)
02:21:09 - 1차 재시도
02:26:09 - 2차 재시도
02:31:09 - 3차 재시도 (최종)
```

### 실패 처리 로직

```python
if failed > 0:
    # 실패한 지역이 있으면 Exception 발생
    # → Azure Functions가 자동으로 재시도
    raise Exception(f"Failed to fetch {failed}/{total} regions")
```

## 멱등성 보장

### 핵심 원리

배치 실행 시 **오늘 날짜 데이터를 먼저 삭제**하여 중복 방지:

```python
# 멱등성 보장: 오늘 날짜 데이터 먼저 삭제
db.query(DailyWeather).filter_by(base_date=today_str).delete()
db.commit()
```

### 멱등성 시나리오

#### 시나리오 1: 정상 실행
```
02:16 배치 → 성공 → 17개 데이터 저장
```

#### 시나리오 2: 재시도 성공
```
02:16 배치 → 실패
02:21 자동 재시도 → 성공 → 17개 데이터 저장
```

#### 시나리오 3: 수동 재실행
```
02:16 배치 → 성공 → 17개 데이터 저장
10:00 실수로 수동 실행 → 기존 17개 삭제 → 새로 17개 저장 ✅
```

## 데이터 수집

### 대상 지역 (17개)

```python
KOREA_REGIONS = {
    "Seoul": {"nx": 60, "ny": 127},
    "Busan": {"nx": 98, "ny": 76},
    "Daegu": {"nx": 89, "ny": 90},
    # ... 14개 더
}
```

### 수집 데이터

| 항목 | 설명 | 출처 |
|------|------|------|
| `min_temp` | 일 최저기온 | TMN 카테고리 |
| `max_temp` | 일 최고기온 | TMX 카테고리 |
| `rain_type` | 강수 형태 | PTY 카테고리 (0:맑음, 1:비, 2:비/눈, 3:눈) |

### API 파라미터

```python
{
    "base_date": "20260126",  # YYYYMMDD
    "base_time": "0200",      # HHMM
    "nx": 60,                 # 격자 X
    "ny": 127,                # 격자 Y
    "numOfRows": 168          # 조회 행 수
}
```

## 에러 처리

### 에러 타입별 처리

1. **네트워크 오류** (`aiohttp.ClientError`)
   - 자동 재시도 (최대 3번)
   
2. **API 응답 오류** (`resultCode != "00"`)
   - 자동 재시도 (최대 3번)
   
3. **DB 저장 실패** (`Exception`)
   - 롤백 후 Exception 발생
   - Azure Functions 재시도

### 에러 로깅

```python
logging.error(f"❌ Batch failed: {str(e)}")
```

## 모니터링

### 성공 로그
```
☀️ [Batch] Daily weather update started
✅ Batch completed: {
  "status": "success",
  "total": 17,
  "success": 17,
  "failed": 0,
  "message": "All 17 regions saved successfully"
}
```

### 실패 로그
```
☀️ [Batch] Daily weather update started
❌ Batch failed: Failed to fetch 2/17 regions: ['Busan', 'Jeju-do']
```

### Azure Portal 확인

1. **Function App** > **Functions** > `daily_weather_update`
2. **Monitor** 탭
3. 실행 이력, 성공/실패, 재시도 횟수 확인

## 수동 실행

### API 엔드포인트

```http
POST /api/weather/batch/manual
```

### 사용 시점

- 배치 실패 시 즉시 재실행
- 데이터 갱신이 필요한 경우
- 테스트/디버깅

### 예시

```bash
curl -X POST http://localhost:7071/api/weather/batch/manual
```

## 데이터베이스 스키마

```python
class DailyWeather(Base):
    __tablename__ = "daily_weather"
    
    id = Column(Integer, primary_key=True)
    base_date = Column(String(8), nullable=False)  # "20260126"
    base_time = Column(String(4), nullable=False)  # "0200"
    nx = Column(Integer, nullable=False)
    ny = Column(Integer, nullable=False)
    region = Column(String(50), index=True)
    
    min_temp = Column(Float)     # 최저기온
    max_temp = Column(Float)     # 최고기온
    rain_type = Column(Integer)  # 강수형태
    
    created_at = Column(Date, server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint("base_date", "nx", "ny"),
    )
```

## 성능 최적화

### 병렬 처리

```python
# 17개 지역 동시 API 호출
tasks = [client.fetch_forecast(...) for region in KOREA_REGIONS]
results = await asyncio.gather(*tasks, return_exceptions=True)
```

### 타임아웃 설정

```python
timeout=aiohttp.ClientTimeout(total=10)
```

### DB 커넥션 풀

```python
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10
)
```

## 개발/테스트

### 로컬 실행

```bash
# Azure Functions 시작
func start

# 배치 즉시 실행 (테스트)
curl -X POST http://localhost:7071/api/weather/batch/manual
```

### 시간 변경 (테스트용)

```python
# function_app.py
schedule="*/5 * * * *"  # 5분마다 실행
```

### 로그 확인

```bash
# 터미널에서 실시간 로그 확인
func start
```

## 배포

### Azure 배포

```bash
func azure functionapp publish <YOUR_FUNCTION_APP_NAME>
```

### 환경 변수 설정

```
KMA_API_KEY=<기상청 API 키>
DATABASE_URL=<PostgreSQL 연결 문자열>
```

## 트러블슈팅

### 문제: 배치가 실행되지 않음

**원인:** Time Trigger 시간대 오류

**해결:**
```python
# UTC 시간으로 설정 필요 (KST - 9시간)
schedule="0 16 17 * * *"  # 17:16 UTC = 02:16 KST
```

### 문제: 일부 지역만 저장됨

**원인:** All or Nothing 정책 위반

**해결:** 정상 동작입니다. 전체 성공해야만 저장됩니다.

### 문제: 중복 데이터 발생

**원인:** 멱등성 로직 누락

**해결:**
```python
# 배치 시작 시 오늘 데이터 삭제
db.query(DailyWeather).filter_by(base_date=today_str).delete()
```

## 참고 자료

- [기상청 단기예보 API](https://www.data.go.kr/data/15084084/openapi.do)
- [Azure Functions Timer Trigger](https://learn.microsoft.com/en-us/azure/azure-functions/functions-bindings-timer)
- [Azure Functions Retry Policy](https://learn.microsoft.com/en-us/azure/azure-functions/functions-bindings-error-pages)
