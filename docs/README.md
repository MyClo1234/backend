# 문서 디렉토리 가이드

이 디렉토리는 AI Stylist Agent Backend 프로젝트의 모든 문서를 포함합니다.

## 📚 문서 구조

### 🎯 발표 및 개요
- **[presentation_content.md](presentation_content.md)** - 발표용 문서 (아키텍처, 워크플로우, 리팩토링 스토리)
- **[timeline.md](timeline.md)** - 프로젝트 개발 타임라인 (Git 커밋 기록 기반)
- **[index.md](index.md)** - 프로젝트 전체 가이드 및 시작하기

### 🗄️ 데이터베이스
- **[database_reference.md](database_reference.md)** - 데이터베이스 스키마 상세 문서 (ERD, 데이터 딕셔너리)

### 🏗️ 아키텍처
- **[architecture/langgraph-flows.md](architecture/langgraph-flows.md)** - LangGraph 워크플로우 상세 구조
- **[architecture/weather-batch.md](architecture/weather-batch.md)** - 날씨 배치 시스템 아키텍처

### 🔌 API 문서
- **[api/auth.md](api/auth.md)** - 인증 API (회원가입, 로그인)
- **[api/extraction.md](api/extraction.md)** - 이미지 분석 API (속성 추출)
- **[api/recommendation.md](api/recommendation.md)** - 코디 추천 API
- **[api/wardrobe.md](api/wardrobe.md)** - 옷장 관리 API
- **[api/weather-api.md](api/weather-api.md)** - 기상청 날씨 API 가이드

### 💻 개발 가이드
- **[development/rules.md](development/rules.md)** - 프로젝트 개발 규칙 및 코딩 스타일
- **[guides/vscode-debugging.md](guides/vscode-debugging.md)** - VS Code 디버깅 가이드

## 🚀 빠른 시작

### 발표 준비
1. **[presentation_content.md](presentation_content.md)** 확인 - 발표용 핵심 내용
2. **[timeline.md](timeline.md)** - 프로젝트 개발 과정 및 마일스톤
3. **[database_reference.md](database_reference.md)** - 데이터베이스 구조 설명
4. **[architecture/langgraph-flows.md](architecture/langgraph-flows.md)** - AI 워크플로우 상세

### 개발 시작
1. **[index.md](index.md)** - 프로젝트 설정 및 실행 방법
2. **[development/rules.md](development/rules.md)** - 코딩 규칙 및 컨벤션
3. **[api/](api/)** - API 엔드포인트 문서

### 아키텍처 이해
1. **[presentation_content.md](presentation_content.md)** - 전체 아키텍처 개요
2. **[architecture/langgraph-flows.md](architecture/langgraph-flows.md)** - AI 워크플로우 상세
3. **[architecture/weather-batch.md](architecture/weather-batch.md)** - 배치 시스템 구조

## 📋 문서 유지보수

### 문서 작성 규칙
- Markdown 형식 사용
- 코드 예제는 실제 동작하는 코드만 포함
- 다이어그램은 Mermaid 형식 사용
- 한글/영문 혼용 시 일관성 유지

### 문서 업데이트 시
1. 관련 문서도 함께 업데이트 확인
2. 링크가 깨지지 않도록 주의
3. 변경 사항을 문서 하단에 기록

---

**마지막 업데이트**: 2025-01-26
