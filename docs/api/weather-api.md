# 기상청 날씨 데이터 API 가이드

이 문서는 기상청 API를 활용하여 날씨 데이터를 조회하는 방법을 정리한 가이드입니다.

## 목차

1. [단기예보](#단기예보)
2. [중기예보](#중기예보)
3. [기상특보](#기상특보)
4. [기상정보/속보](#기상정보속보)
5. [영향예보](#영향예보)
6. [API 기본 정보](#api-기본-정보)

---

## 단기예보

단기예보는 단기예보구역별 날씨 예보 정보를 제공합니다.

### 데이터베이스 테이블 구조

#### FCT_WID_DT (단기예보 데이터)
- **TM_FC**: 기준일시 (DATE, PK)
- **STN_ID**: 관서번호 (NUMBER(3), PK)
- **TM_IN**: 입력일시 (DATE)
- **DS**: 단기예보구역코드 (CHAR(1))
- **DL**: 단기예보구역코드 (CHAR(1))
- **DO**: 단기예보구역코드 (CHAR(1))

#### FCT_WID_DS (단기예보 단기)
- **TM_FC**: 기준일시 (DATE, PK)
- **STN_ID**: 기준관서 (NUMBER(5), PK)
- **TM_IN**: 입력일시 (DATE)
- **CNT**: 입력구분번호 (NUMBER(3))
  - 1: DB입력
  - 2: 파일전송
  - 5: 단기예보 입력프로그램 입력
- **MAN_FC**: 예보자명 (VARCHAR2(20))
- **MAN_IN**: 입력자명 (VARCHAR2(20))
- **MAN_IP**: 입력자IP (VARCHAR2(16))
- **WF_SV1**: 날씨(전날) (VARCHAR2(4000))
- **WF_SV2**: 날씨(당일) (VARCHAR2(4000))
- **WF_SV3**: 날씨(내일) (VARCHAR2(4000))
- **WN**: 특이사항 (VARCHAR2(2000))
- **WR**: 기상특보 (VARCHAR2(2000))
- **REM**: 비고 (VARCHAR2(500))
- **MAN_FC_ID**: 예보자ID (VARCHAR2(32))
- **MAN_IN_ID**: 입력자ID (VARCHAR2(32))

#### FCT_WID_DL (단기예보 단기)
- **TM_FC**: 기준일시 (DATE, PK)
- **REG_ID**: 예보구역코드 (CHAR(8), PK)
- **NUM_EF**: 유효번호 (NUMBER(2), PK)
  - 10: 당일, 11: 내일, 12: 모레
  - 0: 당일오전 or 당일오후
  - 1: 당일오후 or 내일오전
  - 2: 내일오후 or 모레오전
  - 3: 모레오후 or 모레오후
  - 4: 모레오후 or 모레오후
  - 5: 모레오후
- **STN_ID**: 기준관서 (NUMBER(5))
- **TM_IN**: 입력일시 (DATE)
- **CNT**: 입력구분번호 (NUMBER(3))
- **MAN_FC**: 예보자명 (VARCHAR2(20))
- **MAN_IN**: 입력자명 (VARCHAR2(20))
- **MAN_IP**: 입력자IP (VARCHAR2(16))
- **WD1**: 풍향1 (VARCHAR2(3))
  - E: 동, N: 북, NE: 북동, NW: 북서
  - S: 남, SE: 남동, SW: 남서, W: 서
- **WD_TND**: 풍향변화코드 (CHAR(1))
  - 1: -, 2: 시
- **WD2**: 풍향2 (VARCHAR2(3))
- **WS_TM**: 풍속 시간코드 (VARCHAR2(2))
- **WS_IT**: 풍속 강도코드 (VARCHAR2(2))
  - 1: 약한 바람, 2: 중간, 3: 강한 바람
- **TA**: 기온 (NUMBER(3))
- **TA2**: 기온 (NUMBER(3))
- **RN_ST**: 강수확률 (NUMBER(3))
- **RN_ST2**: 강수확률 (NUMBER(3))
- **RN1**: 강수량1(시간) (NUMBER(3))
- **RN2**: 강수량2(시간) (NUMBER(3))
- **SD1**: 적설1(시간) (NUMBER(3))
- **SD2**: 적설2(시간) (NUMBER(3))
- **WF**: 날씨 (VARCHAR2(100))
- **WF_CD**: 날씨코드 (VARCHAR2(4))
  - DB01: 맑음, DB02: 구름많음, DB03: 흐림, DB04: 흐리고비
- **RN_YN**: 강수형태 (VARCHAR2(2))
  - 0: 강수없음, 1: 비, 2: 비/눈, 4: 눈/비, 3: 눈
- **MAN_FC_ID**: 예보자ID (VARCHAR2(32))
- **MAN_IN_ID**: 입력자ID (VARCHAR2(32))

#### FCT_WID_DO (단기예보 오전)
- **TM_FC**: 기준일시 (DATE, PK)
- **REG_ID**: 예보구역코드 (CHAR(8), PK)
- **NUM_EF**: 유효번호 (NUMBER(2), PK)
- **STN_ID**: 기준관서 (NUMBER(5))
- **TM_IN**: 입력일시 (DATE)
- **CNT**: 입력구분번호 (NUMBER(3))
- **MAN_FC**: 예보자명 (VARCHAR2(20))
- **MAN_IN**: 입력자명 (VARCHAR2(20))
- **MAN_IP**: 입력자IP (VARCHAR2(16))
- **WD1**: 풍향1 (VARCHAR2(3))
- **WD_TND**: 풍향변화코드 (CHAR(1))
- **WD2**: 풍향2 (VARCHAR2(3))
- **WS1**: 풍속1 (NUMBER(3))
- **WS2**: 풍속2 (NUMBER(3))
- **WH1**: 파고1 (NUMBER(4,1))
- **WH2**: 파고2 (NUMBER(4,1))
- **WF**: 날씨 (VARCHAR2(100))
- **WF_CD**: 날씨코드 (VARCHAR2(4))
- **RN_YN**: 강수형태 (VARCHAR2(2))
- **MAN_FC_ID**: 예보자ID (VARCHAR2(32))
- **MAN_IN_ID**: 입력자ID (VARCHAR2(32))

#### FCT_WID_DH (단기예보 파일전송)
- **TM_FC**: 기준일시 (DATE, PK)
- **STN_ID**: 관서번호 (NUMBER(3), PK)
- **TM_IN**: 입력일시 (DATE, PK)
- **MAN_FC**: 예보자명 (VARCHAR2(20))
- **MAN_FC_ID**: 예보자ID (VARCHAR2(32))
- **MAN_IN**: 입력자명 (VARCHAR2(20))
- **MAN_IN_ID**: 입력자ID (VARCHAR2(32))
- **PDF_ID**: 파일ID (VARCHAR2(50))

### 파일 전송 형식

**경로**: `/C4N2_DATA/FCT/TXT`

**파일명 형식**:
- `FCT_DS2_{관서코드}_yyyymmddhh24mi.csv`
- `FCT_DL2_{예보구역코드}_yyyymmddhh24mi.csv`
- `FCT_DO2_{예보구역코드}_yyyymmddhh24mi.csv`

**구분자**: `#`

---

## 중기예보

중기예보는 중기예보구역별 날씨 예보 정보를 제공합니다.

### 데이터베이스 테이블 구조

#### FCT_AFS_WS (중기예보 단기)
- **TM_FC**: 기준일시 (DATE, PK)
- **STN_ID**: 관서번호 (NUMBER(5), PK)
- **CNT**: 입력구분번호 (NUMBER(3))
  - 1: DB입력, 2: 파일전송
- **WF_SV**: 날씨요약 (VARCHAR2(1000))
- **MAN_IP**: 입력자IP (VARCHAR2(16))
- **MAN_FC_ID**: 예보자ID (VARCHAR2(32))
- **MAN_IN_ID**: 입력자ID (VARCHAR2(32))
- **TM_IN**: 입력일시 (DATE)

#### FCT_AFS_WT (단기예보구역(단기,오전))
- **TM_FC**: 기준일시 (DATE, PK)
- **REG_ID**: 예보구역코드 (CHAR(8), PK)
- **MAN_IP**: 입력자IP (VARCHAR2(16))
- **MAN_FC_ID**: 예보자ID (VARCHAR2(32))
- **MAN_IN_ID**: 입력자ID (VARCHAR2(32))
- **TM_IN**: 입력일시 (DATE)
- **MAN_FC**: 예보자명 (VARCHAR2(20))

#### FCT_AFS_WL (중기단기)
- **TM_FC**: 기준일시 (DATE, PK)
- **REG_ID**: 예보구역코드 (CHAR(8), PK)
- **TM_EF**: 유효일시 (DATE, PK)
- **MODE_KEY**: 모드키 (VARCHAR2(3), PK)
  - A: 단기예보, B: 중기예보
  - 01: 24시간, 02: 12시간
  - A01: 24시간 단기(단기예보)
  - B01: 24시간 중기(중기예보)
  - A02: 12시간 단기(단기예보)
  - B02: 12시간 중기(중기예보)
- **STN_ID**: 관서번호 (NUMBER(5))
- **CNT**: 입력구분번호 (NUMBER(3))
- **WF_SKY_CD**: 날씨하늘상태코드 (VARCHAR2(4))
  - WB01: 맑음, WB02: 구름많음, WB03: 흐림, WB04: 흐리고비
- **WF_PRE_CD**: 날씨강수형태코드 (VARCHAR2(4))
  - WB00: 강수없음, WB09: 비, WB10: 비눈, WB11: 눈/비, WB13: 눈/비, WB12: 눈
- **TA_MIN**: 기온최저온도 (NUMBER(4))
- **TA_MAX**: 기온최고온도 (NUMBER(4))
- **CONF**: 신뢰도 (VARCHAR2(8))
- **WF**: 날씨요약 (VARCHAR2(100))

#### FCT_AFS_WO (중기오전)
- **TM_FC**: 기준일시 (DATE, PK)
- **REG_ID**: 예보구역코드 (CHAR(8), PK)
- **TM_EF**: 유효일시 (DATE, PK)
- **MODE_KEY**: 모드키 (VARCHAR2(3), PK)
- **STN_ID**: 관서번호 (NUMBER(5))
- **CNT**: 입력구분번호 (NUMBER(3))
- **WF_SKY_CD**: 날씨하늘상태코드 (VARCHAR2(4))
- **WF_PRE_CD**: 날씨강수형태코드 (VARCHAR2(4))
- **WH_A**: 파고파고1(m) (NUMBER(3,1))
- **WH_B**: 파고파고2(m) (NUMBER(3,1))
- **CONF**: 신뢰도 (VARCHAR2(8))
- **WF**: 날씨요약 (VARCHAR2(100))

#### FCT_AFS_WH (단기예보 파일전송)
- **TM_FC**: 기준일시 (DATE, PK)
- **STN_ID**: 관서번호 (NUMBER(5), PK)
- **TM_IN**: 입력일시 (DATE, PK)
- **PDF_ID**: 파일ID (VARCHAR2(50))
- **MAN_FC_ID**: 예보자ID (VARCHAR2(32))
- **MAN_IN_ID**: 입력자ID (VARCHAR2(32))

### 파일 전송 형식

**경로**: `/DATA/FCT/TXT`

**파일명 형식**:
- `FCT_WS1_{관서코드}_yyyymmddhh24mi.csv`
- `FCT_WL3_{예보구역코드}_yyyymmddhh24mi.csv` (중기단기)
- `FCT_WC3_{예보구역코드}_yyyymmddhh24mi.csv` (중기오전)
- `FCT_WO3_{예보구역코드}_yyyymmddhh24mi.csv`

**구분자**: `#`

---

## 기상특보

기상특보는 기상특보 발표 현황 및 상세 정보를 제공합니다.

### 데이터베이스 테이블 구조

#### WRN2_MET_DATA (특보자료)
- **TM_FC**: 기준일시 (DATE, PK)
- **REG_ID**: 특보구역 (VARCHAR2(8), PK)
- **WRN_TP**: 특보종류 (VARCHAR2(2), PK)
  - W: 강풍, R: 호우, C: 한파, D: 대설, O: 강풍대설
  - N: 풍랑특보, V: 폭풍, T: 태풍, S: 폭풍해일, Y: 황사, H: 건조, F: 폭염
- **WRN_LVL**: 특보단계 (VARCHAR2(2))
  - 1: 주의특보, 2: 경보, 3: 해제
- **WRN_CMD**: 특보명령 (VARCHAR2(2))
  - 1: 발표, 2: 변경, 3: 해제, 4: 변경해제, 5: 연장, 6: 정정, 7: 특보해제
- **WRN_GRD**: 특보등급(강풍) (VARCHAR2(2))
  - AB: A(1, 2, 3), B(1, 2, 3)
  - A: 육상특보, B: 해상 (등)

- **TM_EF**: 유효일시 (DATE)
- **TM_ED**: 발효종료일시 (DATE)
- **TM_IN**: 입력일시 (DATE)
- **STN_ID**: 특보관서 (NUMBER(3))
- **TYP**: 특보입력구분 (NUMBER(3))
  - 0: 자동, 1: 수동, 2: 전송
- **CNT**: 작업구분 (NUMBER(3))
  - 0: 발표, 1: 자동발표, 2: 정정, 3: 파일전송, 4: 파일전송완료
- **RPT**: 파일전송 (VARCHAR2(5))
- **MAN_IN**: 입력자명 (VARCHAR2(20))
- **MAN_IP**: 입력자IP (VARCHAR2(16))
- **T01~T18**: 내용01~18 (VARCHAR2(100))

#### WRN2_MET_LINK (특보 파일전송자료(링크))
- **TM_FC**: 기준일시 (DATE, PK)
- **STN_ID**: 기준관서 (NUMBER(3), PK)
- **TM_SEQ**: 기준번호 (VARCHAR2(8), PK)
- **REG_ID**: 특보구역 (VARCHAR2(8), PK)
- **WRN_TP**: 특보종류 (VARCHAR2(2), PK)
- **CNT**: 작업구분 (NUMBER(3))
- **RPT_TYPE**: 특보종류 (CHAR(2))

#### WRN2_MET_RPT (특보 파일전송)
- **TM_FC**: 기준일시 (DATE, PK)
- **STN_ID**: 기준관서 (NUMBER(3), PK)
- **TM_SEQ**: 기준번호 (VARCHAR2(8), PK)
- **TM_IN**: 입력일시 (DATE)
- **CNT**: 작업구분 (NUMBER(3))
  - 4: 파일전송(특보자료프로그램 입력)
- **MAN_FC**: 예보자명 (VARCHAR2(20))
- **MAN_IN**: 입력자명 (VARCHAR2(20))
- **MAN_IP**: 입력자IP (VARCHAR2(16))
- **WRN_FC**: 특보기준코드 (VARCHAR2(2))
  - 1: 발표, 2: 변경, 3: 해제, 4: 특보해제 해제
- **T1**: 내용 (VARCHAR2(500))
- **T2**: 상세내용 (VARCHAR2(2000))
- **T3**: 유효일시 (VARCHAR2(2000))
- **T4**: 내용 (VARCHAR2(2000))
- **T5**: 유효기상일시 (DATE)
- **T6**: 유효기상 (VARCHAR2(4000))
- **T7**: 기상특보상세 (VARCHAR2(2000))
- **OTHER**: 기타내용 (VARCHAR2(2000))

#### REG_WRN2 (특보구역)
- **REG_ID**: 특보구역 (VARCHAR2(8), PK)
- **TM_ED**: 종료일시 (DATE, PK)
- **TM_ST**: 시작일시 (DATE)
- **REG_KO**: 특보구역명(한국) (VARCHAR2(40))
- **REG_EN**: 특보구역명(영문) (VARCHAR2(40))
- **REG_SP**: 지역특보 (VARCHAR2(8))
- **SEQ**: 표시순서 (NUMBER(3))
- **REG_UP**: 상위특보구역 (VARCHAR2(8))
- **FCT_ID**: 예보관서코드 (VARCHAR2(8))
- **STN_ID**: 특보기준관서 (NUMBER(3))
- **REG_NAME**: 특보구역명(영문) (VARCHAR2(40))
- **ADM_ID**: 행정구역코드 (VARCHAR2(10))

---

## 기상정보/속보

기상정보/속보는 기상정보, 기상속보, 기상특보 관련 정보를 제공합니다.

### 데이터베이스 테이블 구조

#### WRN_INF (기상정보)
- **STN_ID**: 관서번호 (NUMBER(5), PK)
- **TM_FC**: 기준일시 (DATE, PK)
- **TM_SEQ**: 기준 순번 (NUMBER(4))
- **TM_IN**: 입력일시 (DATE, PK)
- **CNT**: 입력구분번호 (NUMBER(3))
  - 1: 실시간입력, 2: 파일전송 완료
- **MAN_FC**: 예보자명 (VARCHAR2(20))
- **MAN_IN**: 입력자명 (VARCHAR2(20))
- **MAN_IP**: 입력자IP (VARCHAR2(16))
- **T1**: 기상정보1 (VARCHAR2(4000))
- **T2**: 특보상황 (VARCHAR2(2000))
- **PW1~PW4**: 지역특보1~4:특보구역 (VARCHAR2(400))
- **PA1~PA4**: 지역특보1~4:상세내용 (VARCHAR2(1000))
- **PT1~PT4**: 지역특보1~4:유효일시 (VARCHAR2(800))
- **PR1~PR4**: 지역특보1~4:내용 (VARCHAR2(100))
- **SUB_TITLE_CD**: 부제목코드 (VARCHAR2(5))
- **SUB_TITLE_NAME**: 부제목이름 (VARCHAR2(50))
- **T3**: 기상정보2 (VARCHAR2(4000))

#### WTHR_CMT (기상속보)
- **STN_ID**: 관서번호 (NUMBER(5), PK)
- **TM_FC**: 기준일시 (DATE, PK)
- **TM_SEQ**: 기준 순번 (NUMBER(4))
- **TM_IN**: 입력일시 (DATE, PK)
- **CNT**: 입력구분번호 (NUMBER(3))
  - 1: 실시간입력, 2: 파일전송 완료
- **MAN_FC**: 예보자명 (VARCHAR2(20))
- **MAN_IN**: 입력자명 (VARCHAR2(20))
- **MAN_IP**: 입력자IP (VARCHAR2(16))
- **T1**: 기상속보1 (VARCHAR2(4000))
- **T2**: 특보상황 (VARCHAR2(2000))
- **PW1~PW4**: 지역특보1~4:특보구역 (VARCHAR2(400))
- **PA1~PA4**: 지역특보1~4:상세내용 (VARCHAR2(1000))
- **PT1~PT4**: 지역특보1~4:유효일시 (VARCHAR2(800))
- **PR1~PR4**: 지역특보1~4:내용 (VARCHAR2(100))
- **SUB_TITLE_CD**: 부제목코드 (VARCHAR2(5))
- **SUB_TITLE_NAME**: 부제목이름 (VARCHAR2(50))
- **T3**: 기상속보내용2 (VARCHAR2(4000))

#### WRN_ANN (기상특보)
- **STN_ID**: 관서번호 (NUMBER(3), PK)
- **TM_FC**: 기준일시 (DATE, PK)
- **TM_SEQ**: 기준번호(순번) (NUMBER(3))
- **TM_IN**: 입력일시 (DATE)
- **CNT**: 입력구분번호 (NUMBER(3))
  - 1: 실시간입력, 4: 파일전송 완료
- **MAN_FC**: 예보자명 (VARCHAR2(20))
- **MAN_IN**: 입력자명 (VARCHAR2(20))
- **MAN_IP**: 입력자IP (VARCHAR2(16))
- **ANN**: 내용 (VARCHAR2(2000))

#### WRN_FOG (폭염기상정보)
- **STN_ID**: 관서번호 (NUMBER(5), PK)
- **TM_FC**: 기준일시 (DATE, PK)
- **TM_SEQ**: 기준번호(순번) (NUMBER(4), PK)
- **TM_IN**: 입력일시 (DATE)
- **CNT**: 입력구분번호 (NUMBER(3))
  - 1: 실시간입력, 2: 파일전송 완료
- **MAN_FC**: 예보자명 (VARCHAR2(20))
- **MAN_IN**: 입력자명 (VARCHAR2(20))
- **MAN_IP**: 입력자IP (VARCHAR2(16))
- **FOG_SUM**: 요약 (VARCHAR2(2000))
- **FOG_AC**: 발생원인,전망 (VARCHAR2(2000))
- **FOG_SCT**: 폭염상세기상정보 (VARCHAR2(4000))
- **FOG_FF**: 폭염영향,대응 (VARCHAR2(2000))
- **OTHER**: 기타내용 (VARCHAR2(1000))

#### WRN_SEA (해상기상정보)
- **TM_FC**: 기준일시 (DATE, PK)
- **STN_ID**: 관서번호 (NUMBER(3), PK)
- **TM_SEQ**: 기준번호 (NUMBER(3))
- **TM_IN**: 입력일시 (DATE)
- **CNT**: 입력구분번호 (NUMBER(3))
  - 1: 실시간입력, 2: 파일전송 완료
- **MAN_FC**: 예보자명 (VARCHAR2(20))
- **MAN_IN**: 입력자명 (VARCHAR2(20))
- **MAN_IP**: 입력자IP (VARCHAR2(16))
- **SEA_CONTENT**: 해상기상정보내용 (VARCHAR2(4000))
- **FILE_NAME**: 파일명 (VARCHAR2(300))
- **ORG_FILE_NAME**: 원본파일명 (VARCHAR2(300))

---

## 영향예보

영향예보는 날씨 뿐만 아니라 시간과 장소에 따라 달라지는 날씨의 영향을 고려하여 기상 현상별 위험수준에 따른 분야별 상세 영향정보와 대응요령을 제공합니다.

### 개요

- **목적**: 유관기관에 실효적 정보를 제공하여 방재업무를 지원하고, 기상재해로부터 국민의 안전을 보호
- **요소**: 폭염, 한파(영향 전망, 피해 현황, 기상 전망, 분야별 위험수준 및 대응요령)
- **지점**: 전국 174개 시·군 단위 및 4개 산지(특보구역과 동일)
- **보유기간**: 2019년 6월 ~ 현재
- **생산주기**: 발표기준 부합시 일 1회 발표(11시 30분)

### API 엔드포인트

#### 1. 영향예보 발표 현황(발표구역별 위험수준) 조회

**1.1.1 폭염영향예보 기간 조회(발효시각 기준)**

```
GET https://apihub.kma.go.kr/api/typ01/url/ifs_fct_pstt.php
```

**요청 파라미터**:
- `tmef1` (string): 기준일 시작 (YYYYMMDD, KST)
- `tmef2` (string): 기준일 종료 (YYYYMMDD, KST)
- `ifpar` (string): 영향예보 요소 - `hw` (폭염)
- `help` (number, optional): 도움말 표시 여부 (1: 표시)
- `authKey` (string, required): API 인증키

**예시**:
```
https://apihub.kma.go.kr/api/typ01/url/ifs_fct_pstt.php?tmef1=20210701&tmef2=20210730&ifpar=hw&help=1&authKey=YOUR_AUTH_KEY
```

**1.1.2 한파영향예보 기간 조회(발표시각 기준)**

```
GET https://apihub.kma.go.kr/api/typ01/url/ifs_fct_pstt.php
```

**요청 파라미터**:
- `tmfc1` (string): 발표시간 시작 (YYYYMMDD, KST)
- `tmfc2` (string): 발표시간 종료 (YYYYMMDD, KST)
- `ifpar` (string): 영향예보 요소 - `cw` (한파)
- `help` (number, optional): 도움말 표시 여부 (1: 표시)
- `authKey` (string, required): API 인증키

**예시**:
```
https://apihub.kma.go.kr/api/typ01/url/ifs_fct_pstt.php?tmfc1=20210101&tmfc2=20210131&ifpar=cw&help=1&authKey=YOUR_AUTH_KEY
```

**1.1.3 기간, 특보구역 조회(발효시각 기준)**

```
GET https://apihub.kma.go.kr/api/typ01/url/ifs_fct_pstt.php
```

**요청 파라미터**:
- `tmef1` (string): 기준일 시작 (YYYYMMDD, KST)
- `tmef2` (string): 기준일 종료 (YYYYMMDD, KST)
- `ifarea` (number, optional): 영향분야
  - 폭염: 0(모든 분야), 1(보건 일반인), 2(보건 취약인), 3(산업), 4(축산업), 5(농업), 6(수산양식), 7(기타)
  - 한파: 0(모든 분야), 1(보건), 2(산업), 3(시설물), 4(농축산업), 5(수산양식), 6(기타)
  - 기본값: 1
- `regid` (string, optional): 특보구역 코드 (예: `L1050100`)
- `help` (number, optional): 도움말 표시 여부 (1: 표시)
- `authKey` (string, required): API 인증키

**예시**:
```
https://apihub.kma.go.kr/api/typ01/url/ifs_fct_pstt.php?tmef1=20210701&tmef2=20210730&ifarea=0&regid=L1050100&help=1&authKey=YOUR_AUTH_KEY
```

**공통 요청 파라미터**:
- `tmfc1`, `tmfc2`: 발표시간 기간 (YYYYMMDD, KST) - 생략 시 금일 발표시간으로 처리
- `tmef1`, `tmef2`: 기준일 기간 (YYYYMMDD, KST) - 기준일로부터 2일 유효, 매일갱신, 생략 시 금일로 처리
- `stn` (string, optional): 관서 코드 - 생략 시 전체 관서로 처리
- `regid` (string, optional): 특보구역 코드 - 생략 시 전체 구역으로 처리
- `ifpar` (string, optional): 영향예보 요소 - `hw` (폭염), `cw` (한파) - 생략 시 발효중인 요소 전체 처리
- `ifarea` (number, optional): 영향분야
- `ilvl` (number, optional): 위험수준 - 0(영향없음), 1(관심), 2(주의), 3(경고), 4(위험) - 생략 시 전체 처리
- `help` (number, optional): 도움말 표시 여부 (1: 표시)
- `authKey` (string, required): API 인증키

**응답 필드**:
- `TM_FC`: 발표시각 (KST)
- `TM_EF`: 기준일 (KST)
- `STN`: 관서 코드
- `REG_ID`: 특보구역 코드
- `IFPAR`: 영향예보 요소
- `IFAREA`: 영향분야
- `ILVL`: 위험 수준(영향 등급)

#### 2. 영향예보 위험수준별 발표지역 수 조회

```
GET https://apihub.kma.go.kr/api/typ01/url/ifs_ilvl_zone_cnt.php
```

**요청 파라미터**:
- `tmfc1`, `tmfc2` (string, optional): 발표시간 기간 (YYYYMMDD, KST)
- `tmef1`, `tmef2` (string, optional): 기준일 기간 (YYYYMMDD, KST)
- `stn` (string, optional): 관서 코드
- `ifpar` (string, optional): 영향예보 요소 - `hw` (폭염), `cw` (한파)
- `ifarea` (number, optional): 영향분야
- `ilvl` (number, optional): 위험수준
- `help` (number, optional): 도움말 표시 여부 (1: 표시)
- `authKey` (string, required): API 인증키

**예시**:
```
https://apihub.kma.go.kr/api/typ01/url/ifs_ilvl_zone_cnt.php?help=1&tmef1=20210701&tmef2=20210730&ifarea=0&stn=108&authKey=YOUR_AUTH_KEY
```

**응답 필드**:
- `TM_FC`: 발표시각 (KST)
- `TM_EF`: 기준일 (KST)
- `STN`: 관서 코드
- `IFPAR`: 영향예보 요소
- `IFAREA`: 영향분야
- `ILVL`: 위험 수준(영향 등급)
- `ILVL_NUM`: [출력전용] 위험 수준별 발표지역 수
- `ILVL_ID`: [출력전용] 위험 수준별 발표구역 코드

#### 3. 영향예보 위험수준 분포도

```
GET https://apihub.kma.go.kr/api/typ01/url/ifs_ilvl_dmap.php
```

**요청 파라미터**:
- `tmfc` (string, optional): 발표시간 (YYYYMMDD, KST) - 생략 시 금일 발표시간으로 처리
- `stn` (string, optional): 관서 코드 - 생략 시 108 관서로 처리
- `ifpar` (string, optional): 영향예보 요소 - `hw` (폭염), `cw` (한파) - 생략 시 폭염(hw) 요소 처리
- `ifarea` (number, optional): 영향분야 - 생략 시 1(보건 일반인/보건)로 처리
- `authKey` (string, required): API 인증키

**예시**:
```
https://apihub.kma.go.kr/api/typ01/url/ifs_ilvl_dmap.php?tmfc=20220601&ifpar=hw&ifarea=1&authKey=YOUR_AUTH_KEY
```

---

## API 기본 정보

### 인증

모든 API 요청에는 `authKey` 파라미터가 필요합니다. 기상청 API Hub에서 인증키를 발급받아야 합니다.

### 날짜 형식

- 모든 날짜는 `YYYYMMDD` 형식으로 전달합니다.
- 시간대는 KST(한국 표준시)를 사용합니다.

### 에러 처리

API 요청 시 오류가 발생하면 적절한 HTTP 상태 코드와 함께 오류 메시지가 반환됩니다.

### 요청 제한

API 사용 시 요청 제한이 있을 수 있으므로, 과도한 요청을 피하고 적절한 캐싱 전략을 사용하는 것이 좋습니다.

### 참고 자료

- [기상청 API Hub](https://apihub.kma.go.kr/)
- [단기예보 DB구조](https://apihub.kma.go.kr/static/html/attach/fct_shrt_table.html)
- [중기예보 DB구조](https://apihub.kma.go.kr/static/html/attach/fct_medm_table.html)
- [기상특보 DB구조](https://apihub.kma.go.kr/static/html/attach/wrn_table.html)
- [기상정보/속보 DB구조](https://apihub.kma.go.kr/static/html/attach/wrn_inf_table.html)

---

## 구현 예시

### Python 예시

```python
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

class WeatherAPIClient:
    """기상청 날씨 데이터 API 클라이언트"""
    
    BASE_URL = "https://apihub.kma.go.kr/api/typ01/url"
    
    def __init__(self, auth_key: str):
        self.auth_key = auth_key
    
    def get_impact_forecast_status(
        self,
        start_date: str,
        end_date: str,
        ifpar: str = "hw",  # hw: 폭염, cw: 한파
        ifarea: Optional[int] = None,
        regid: Optional[str] = None,
        ilvl: Optional[int] = None,
        use_effective_date: bool = True
    ) -> Dict[str, Any]:
        """
        영향예보 발표 현황 조회
        
        Args:
            start_date: 시작일 (YYYYMMDD)
            end_date: 종료일 (YYYYMMDD)
            ifpar: 영향예보 요소 (hw: 폭염, cw: 한파)
            ifarea: 영향분야
            regid: 특보구역 코드
            ilvl: 위험수준
            use_effective_date: True면 기준일(tmef), False면 발표시간(tmfc) 사용
        
        Returns:
            API 응답 데이터
        """
        url = f"{self.BASE_URL}/ifs_fct_pstt.php"
        params = {
            "authKey": self.auth_key,
            "ifpar": ifpar,
            "help": 1
        }
        
        if use_effective_date:
            params["tmef1"] = start_date
            params["tmef2"] = end_date
        else:
            params["tmfc1"] = start_date
            params["tmfc2"] = end_date
        
        if ifarea is not None:
            params["ifarea"] = ifarea
        if regid:
            params["regid"] = regid
        if ilvl is not None:
            params["ilvl"] = ilvl
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_impact_forecast_zone_count(
        self,
        start_date: str,
        end_date: str,
        ifpar: Optional[str] = None,
        ifarea: Optional[int] = None,
        stn: Optional[str] = None,
        ilvl: Optional[int] = None,
        use_effective_date: bool = True
    ) -> Dict[str, Any]:
        """
        영향예보 위험수준별 발표지역 수 조회
        
        Args:
            start_date: 시작일 (YYYYMMDD)
            end_date: 종료일 (YYYYMMDD)
            ifpar: 영향예보 요소
            ifarea: 영향분야
            stn: 관서 코드
            ilvl: 위험수준
            use_effective_date: True면 기준일(tmef), False면 발표시간(tmfc) 사용
        
        Returns:
            API 응답 데이터
        """
        url = f"{self.BASE_URL}/ifs_ilvl_zone_cnt.php"
        params = {
            "authKey": self.auth_key,
            "help": 1
        }
        
        if use_effective_date:
            params["tmef1"] = start_date
            params["tmef2"] = end_date
        else:
            params["tmfc1"] = start_date
            params["tmfc2"] = end_date
        
        if ifpar:
            params["ifpar"] = ifpar
        if ifarea is not None:
            params["ifarea"] = ifarea
        if stn:
            params["stn"] = stn
        if ilvl is not None:
            params["ilvl"] = ilvl
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_impact_forecast_distribution(
        self,
        date: str,
        ifpar: str = "hw",
        ifarea: int = 1,
        stn: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        영향예보 위험수준 분포도 조회
        
        Args:
            date: 발표시간 (YYYYMMDD)
            ifpar: 영향예보 요소
            ifarea: 영향분야
            stn: 관서 코드
        
        Returns:
            API 응답 데이터
        """
        url = f"{self.BASE_URL}/ifs_ilvl_dmap.php"
        params = {
            "authKey": self.auth_key,
            "tmfc": date,
            "ifpar": ifpar,
            "ifarea": ifarea
        }
        
        if stn:
            params["stn"] = stn
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()


# 사용 예시
if __name__ == "__main__":
    # 인증키 설정 (환경변수에서 가져오는 것을 권장)
    auth_key = "YOUR_AUTH_KEY"
    client = WeatherAPIClient(auth_key)
    
    # 오늘 날짜 기준으로 폭염 영향예보 조회
    today = datetime.now().strftime("%Y%m%d")
    result = client.get_impact_forecast_status(
        start_date=today,
        end_date=today,
        ifpar="hw",
        ifarea=1  # 보건 일반인
    )
    print(result)
```

### 환경변수 설정

```bash
# .env 파일
KMA_API_KEY=your_api_key_here
```

---

## 주의사항

1. **인증키 관리**: API 인증키는 환경변수나 보안 저장소에 저장하고 코드에 직접 하드코딩하지 마세요.

2. **요청 제한**: API 사용 시 요청 제한이 있을 수 있으므로, 적절한 재시도 로직과 캐싱을 구현하세요.

3. **날짜 형식**: 모든 날짜는 `YYYYMMDD` 형식으로 전달해야 합니다.

4. **에러 처리**: API 요청 실패 시 적절한 에러 처리를 구현하세요.

5. **데이터 파싱**: API 응답 데이터의 형식을 확인하고 적절히 파싱하세요.

---

## 추가 개발 가이드

### 캐싱 전략

날씨 데이터는 자주 변경되지 않으므로, 적절한 캐싱 전략을 사용하면 API 호출을 줄일 수 있습니다.

```python
from functools import lru_cache
from datetime import datetime, timedelta

@lru_cache(maxsize=128)
def get_cached_weather_data(date: str, region: str):
    """날씨 데이터 캐싱"""
    # 캐시된 데이터가 있으면 반환
    # 없으면 API 호출 후 캐시에 저장
    pass
```

### 비동기 처리

대량의 데이터를 조회할 경우 비동기 처리를 고려하세요.

```python
import asyncio
import aiohttp

async def fetch_weather_data_async(session, url, params):
    async with session.get(url, params=params) as response:
        return await response.json()
```

---

---

## 실전 예시: 서울시 마포구 내일 날씨 조회

### 1. 기상청 공개 API 사용 (권장)

기상청 공개 API는 공공데이터포털에서 제공하는 단기예보 조회 서비스를 사용합니다.

#### API 기본 정보

- **서비스명**: 기상청_단기예보 ((구)_동네예보) 조회서비스
- **API URL**: `http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst`
- **인증**: 공공데이터포털에서 발급받은 서비스 키 필요

#### 서울시 마포구 좌표 정보

- **위도**: 약 37.5665
- **경도**: 약 126.9019
- **기상청 격자 좌표**: 
  - **nx**: 55
  - **ny**: 126

> **참고**: 기상청 API는 위도/경도가 아닌 격자 좌표(nx, ny)를 사용합니다. 다른 지역의 좌표가 필요하면 기상청 홈페이지의 격자 위경도 파일을 참고하거나 좌표 변환 함수를 사용하세요.

#### API 요청 예시

**1. 단기예보 조회 (내일 날씨 포함)**

```python
import requests
from datetime import datetime, timedelta
from urllib.parse import urlencode, quote_plus

def get_tomorrow_weather_mapo():
    """
    서울시 마포구 내일 날씨 조회
    
    Returns:
        dict: 날씨 정보
    """
    # API 설정
    BASE_URL = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
    SERVICE_KEY = "YOUR_SERVICE_KEY"  # 공공데이터포털에서 발급받은 키
    
    # 서울시 마포구 좌표
    nx = 55
    ny = 126
    
    # 오늘 날짜와 시간 계산
    today = datetime.now()
    base_date = today.strftime("%Y%m%d")
    
    # base_time은 현재 시각으로부터 30분 이전의 정시 단위
    # 예: 현재가 14:35면 base_time은 1400 (14시)
    current_hour = today.hour
    current_minute = today.minute
    
    # 30분 이전 시각 계산
    if current_minute < 30:
        base_time_hour = current_hour - 1
    else:
        base_time_hour = current_hour
    
    # base_time은 0200, 0500, 0800, 1100, 1400, 1700, 2000, 2300 중 하나여야 함
    # 가장 가까운 발표 시각 찾기
    valid_times = [2, 5, 8, 11, 14, 17, 20, 23]
    base_time_hour = max([t for t in valid_times if t <= base_time_hour], default=23)
    base_time = f"{base_time_hour:02d}00"
    
    # 요청 파라미터
    params = {
        "serviceKey": SERVICE_KEY,
        "pageNo": "1",
        "numOfRows": "1000",
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": str(nx),
        "ny": str(ny)
    }
    
    # API 요청
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    data = response.json()
    
    # 응답 파싱
    if data.get("response", {}).get("header", {}).get("resultCode") == "00":
        items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        
        # 내일 날짜 계산
        tomorrow = today + timedelta(days=1)
        tomorrow_date = tomorrow.strftime("%Y%m%d")
        
        # 내일 날씨 정보 필터링
        tomorrow_weather = {}
        for item in items:
            fcst_date = item.get("fcstDate")
            fcst_time = item.get("fcstTime")
            category = item.get("category")
            fcst_value = item.get("fcstValue")
            
            if fcst_date == tomorrow_date:
                if fcst_time not in tomorrow_weather:
                    tomorrow_weather[fcst_time] = {}
                tomorrow_weather[fcst_time][category] = fcst_value
        
        return {
            "date": tomorrow_date,
            "weather": tomorrow_weather
        }
    else:
        error_msg = data.get("response", {}).get("header", {}).get("resultMsg", "알 수 없는 오류")
        raise Exception(f"API 오류: {error_msg}")


# 사용 예시
if __name__ == "__main__":
    try:
        weather_data = get_tomorrow_weather_mapo()
        print(f"내일 날씨 정보: {weather_data}")
    except Exception as e:
        print(f"오류 발생: {e}")
```

**2. 날씨 카테고리 설명**

API 응답의 `category` 필드 값과 의미:

- `TMP`: 기온 (℃)
- `TMN`: 최저기온 (℃)
- `TMX`: 최고기온 (℃)
- `SKY`: 하늘상태
  - 1: 맑음
  - 3: 구름많음
  - 4: 흐림
- `PTY`: 강수형태
  - 0: 없음
  - 1: 비
  - 2: 비/눈
  - 3: 눈
  - 4: 소나기
- `POP`: 강수확률 (%)
- `PCP`: 강수량 (mm)
- `REH`: 습도 (%)
- `WSD`: 풍속 (m/s)
- `VEC`: 풍향 (deg)
- `WAV`: 파고 (m)

**3. 간단한 사용 예시 (cURL)**

```bash
# 오늘 날짜와 적절한 base_time 설정 필요
curl "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst?\
serviceKey=YOUR_SERVICE_KEY&\
pageNo=1&\
numOfRows=1000&\
dataType=JSON&\
base_date=20250122&\
base_time=1100&\
nx=55&\
ny=126"
```

### 2. API 신청 절차

1. [공공데이터포털](https://www.data.go.kr) 회원가입 및 로그인
2. "기상청_단기예보 조회서비스" 검색
3. 활용신청 클릭
4. 발급받은 일반 인증키(Encoding) 저장
5. API 사용 시작

### 3. 주의사항

1. **base_time 제약**: 
   - base_time은 현재 시각으로부터 30분 이전의 정시 단위여야 합니다
   - 유효한 발표 시각: 0200, 0500, 0800, 1100, 1400, 1700, 2000, 2300

2. **데이터 제공 기간**:
   - 단기예보는 최근 1일간의 자료만 제공됩니다
   - 내일 날씨를 조회하려면 오늘 발표된 예보를 조회해야 합니다

3. **인증키 인코딩**:
   - 공공데이터포털에서 발급받은 키는 이미 인코딩되어 있으므로 추가 인코딩하지 마세요
   - URL에 직접 사용할 때는 `quote_plus()` 사용 주의

4. **요청 제한**:
   - 일일 요청 제한이 있을 수 있으므로 적절한 캐싱을 사용하세요

### 4. 완전한 예제 코드

```python
import requests
from datetime import datetime, timedelta
import json

class MapoWeatherClient:
    """서울시 마포구 날씨 조회 클라이언트"""
    
    BASE_URL = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
    NX = 55  # 마포구 격자 X 좌표
    NY = 126  # 마포구 격자 Y 좌표
    
    def __init__(self, service_key: str):
        self.service_key = service_key
    
    def _get_base_time(self) -> tuple:
        """현재 시각 기준으로 유효한 base_date와 base_time 계산"""
        now = datetime.now()
        base_date = now.strftime("%Y%m%d")
        
        # 유효한 발표 시각 목록
        valid_times = [2, 5, 8, 11, 14, 17, 20, 23]
        current_hour = now.hour
        current_minute = now.minute
        
        # 30분 이전 시각 계산
        if current_minute < 30:
            target_hour = current_hour - 1
        else:
            target_hour = current_hour
        
        # 가장 가까운 유효한 발표 시각 찾기
        base_time_hour = max([t for t in valid_times if t <= target_hour], default=23)
        
        # 만약 오늘 발표 시각이 없으면 어제 23시 사용
        if base_time_hour < valid_times[0]:
            base_date = (now - timedelta(days=1)).strftime("%Y%m%d")
            base_time_hour = 23
        
        base_time = f"{base_time_hour:02d}00"
        return base_date, base_time
    
    def get_tomorrow_weather(self) -> dict:
        """내일 날씨 조회"""
        base_date, base_time = self._get_base_time()
        
        params = {
            "serviceKey": self.service_key,
            "pageNo": "1",
            "numOfRows": "1000",
            "dataType": "JSON",
            "base_date": base_date,
            "base_time": base_time,
            "nx": str(self.NX),
            "ny": str(self.NY)
        }
        
        response = requests.get(self.BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        # 응답 검증
        header = data.get("response", {}).get("header", {})
        if header.get("resultCode") != "00":
            raise Exception(f"API 오류: {header.get('resultMsg', '알 수 없는 오류')}")
        
        items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        
        # 내일 날짜
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y%m%d")
        
        # 내일 날씨 정보 수집
        weather_info = {
            "date": tomorrow,
            "forecasts": {}
        }
        
        for item in items:
            fcst_date = item.get("fcstDate")
            fcst_time = item.get("fcstTime")
            category = item.get("category")
            fcst_value = item.get("fcstValue")
            
            if fcst_date == tomorrow:
                time_key = f"{fcst_time[:2]}:{fcst_time[2:]}"
                if time_key not in weather_info["forecasts"]:
                    weather_info["forecasts"][time_key] = {}
                weather_info["forecasts"][time_key][category] = fcst_value
        
        return weather_info
    
    def format_weather_summary(self, weather_data: dict) -> str:
        """날씨 정보를 읽기 쉬운 형식으로 변환"""
        tomorrow = datetime.now() + timedelta(days=1)
        date_str = tomorrow.strftime("%Y년 %m월 %d일")
        
        summary = f"서울시 마포구 {date_str} 날씨\n\n"
        
        # 주요 정보 추출
        forecasts = weather_data.get("forecasts", {})
        if not forecasts:
            return summary + "날씨 정보가 없습니다."
        
        # 최저/최고 기온 찾기
        min_temp = None
        max_temp = None
        sky_info = {}
        pop_info = {}
        
        for time, data in forecasts.items():
            if "TMN" in data:
                temp = int(data["TMN"])
                if min_temp is None or temp < min_temp:
                    min_temp = temp
            if "TMX" in data:
                temp = int(data["TMX"])
                if max_temp is None or temp > max_temp:
                    max_temp = temp
            if "SKY" in data:
                sky_code = int(data["SKY"])
                sky_map = {1: "맑음", 3: "구름많음", 4: "흐림"}
                sky_info[time] = sky_map.get(sky_code, "알 수 없음")
            if "POP" in data:
                pop_info[time] = int(data["POP"])
        
        if min_temp is not None:
            summary += f"최저기온: {min_temp}℃\n"
        if max_temp is not None:
            summary += f"최고기온: {max_temp}℃\n"
        
        if sky_info:
            summary += f"\n하늘상태: {list(sky_info.values())[0]}\n"
        if pop_info:
            max_pop = max(pop_info.values())
            summary += f"강수확률: 최대 {max_pop}%\n"
        
        return summary


# 사용 예시
if __name__ == "__main__":
    # 환경변수에서 서비스 키 가져오기 (권장)
    import os
    service_key = os.getenv("KMA_SERVICE_KEY", "YOUR_SERVICE_KEY")
    
    client = MapoWeatherClient(service_key)
    
    try:
        weather = client.get_tomorrow_weather()
        print(json.dumps(weather, indent=2, ensure_ascii=False))
        
        print("\n" + "="*50 + "\n")
        print(client.format_weather_summary(weather))
    except Exception as e:
        print(f"오류 발생: {e}")
```

### 5. 다른 지역 좌표 찾기

다른 지역의 nx, ny 좌표가 필요한 경우:

1. [기상청 격자 위경도 파일](https://www.data.go.kr) 다운로드
2. 위도/경도를 기상청 격자 좌표로 변환하는 함수 사용
3. 또는 공공데이터포털의 지역코드 조회 API 활용

---

**마지막 업데이트**: 2025-01-21
