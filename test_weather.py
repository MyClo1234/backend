"""
날씨 기능 테스트 스크립트

사용법 (uv 사용):
1. 환경 변수 설정 (.env 파일에 KMA_SERVICE_KEY 추가)
2. uv run python test_weather.py

또는:
1. uv sync  # 의존성 설치
2. uv run python test_weather.py

테스트 항목:
- 지역 정규화 및 regId 매핑
- tmFc 선택
- 날씨 API 호출 (실제 API 키 필요)
- 워크플로우 통합 테스트
"""
import os
import sys
import json
from datetime import datetime, timedelta

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.weather.weather_resolver import WeatherResolver
from app.services.weather.weather_service import WeatherService
from app.ai.workflows.recommendation_workflow import get_recommendation_workflow
from app.ai.schemas.workflow_state import RecommendationState


def test_weather_resolver():
    """지역 정규화 및 regId 매핑 테스트"""
    print("\n=== 지역 정규화 테스트 ===")
    
    test_cases = [
        ("서울", "서울특별시", "11B10101", False),
        ("서울시", "서울특별시", "11B10101", False),
        ("수원", "경기도", "11B00000", False),
        ("강남구", "서울특별시", "11B10101", False),
        ("해운대구", "부산광역시", "11H20201", False),
        ("강원도", "강원도", None, True),  # disambiguation 필요
        ("전라도", "전라도", None, True),  # disambiguation 필요
    ]
    
    for region_text, expected_canonical, expected_regid, expected_disambiguation in test_cases:
        result = WeatherResolver.resolve_region(region_text)
        print(f"\n입력: '{region_text}'")
        print(f"  정규화: {result['region_canonical']} (예상: {expected_canonical})")
        print(f"  regId: {result['regId']} (예상: {expected_regid})")
        print(f"  disambiguation 필요: {result['needs_disambiguation']} (예상: {expected_disambiguation})")
        if result['clarifying_question']:
            print(f"  질문: {result['clarifying_question']}")
        
        assert result['region_canonical'] == expected_canonical, f"정규화 실패: {result['region_canonical']} != {expected_canonical}"
        assert result['regId'] == expected_regid, f"regId 실패: {result['regId']} != {expected_regid}"
        assert result['needs_disambiguation'] == expected_disambiguation, f"disambiguation 실패"
    
    print("\n✅ 지역 정규화 테스트 통과")


def test_tmfc_selection():
    """tmFc 선택 테스트"""
    print("\n=== tmFc 선택 테스트 ===")
    
    service = WeatherService()
    
    # 미래 날짜 (4일 후)
    future_date = (datetime.now() + timedelta(days=4)).strftime("%Y-%m-%d")
    print(f"\n목표 날짜: {future_date} (4일 후)")
    
    tmFc = service.select_tmfc(future_date)
    if tmFc:
        print(f"선택된 tmFc: {tmFc}")
        print("✅ tmFc 선택 성공")
    else:
        print("⚠️  tmFc를 찾을 수 없음 (예보 범위 밖일 수 있음)")
    
    # 범위 확인 테스트
    print("\n=== 날씨 범위 확인 테스트 ===")
    test_dates = [
        (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),  # 2일 후 (범위 밖)
        (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),  # 5일 후 (범위 내)
        (datetime.now() + timedelta(days=12)).strftime("%Y-%m-%d"),  # 12일 후 (범위 밖)
    ]
    
    for target_date in test_dates:
        range_check = service.check_weather_range(target_date)
        print(f"\n목표 날짜: {target_date}")
        print(f"  범위 내: {range_check['in_range']}")
        if range_check['reason']:
            print(f"  이유: {range_check['reason']}")


def test_weather_api():
    """날씨 API 호출 테스트 (실제 API 키 필요)"""
    print("\n=== 날씨 API 호출 테스트 ===")
    
    service = WeatherService()
    
    # API 키 확인
    from app.core.config import Config
    if not Config.KMA_SERVICE_KEY:
        print("⚠️  KMA_SERVICE_KEY가 설정되지 않았습니다. API 테스트를 건너뜁니다.")
        print("   .env 파일에 KMA_SERVICE_KEY를 추가하세요.")
        return
    
    # 테스트용 regId와 tmFc
    regId = "11B10101"  # 서울
    
    # 여러 날짜와 tmFc를 시도해보기
    now = datetime.now()
    kst_now = now + timedelta(hours=9)  # KST 기준
    
    # 여러 tmFc 후보 생성 (최근 48시간 내)
    tmFc_candidates = []
    for days_ago in [0, 1, 2]:
        for hour in [6, 18]:
            candidate = (kst_now - timedelta(days=days_ago)).replace(hour=hour, minute=0, second=0, microsecond=0)
            if candidate <= kst_now:
                tmFc_candidates.append(candidate.strftime("%Y%m%d%H%M"))
    
    # 여러 날짜 시도
    test_dates = [
        (now + timedelta(days=5)).strftime("%Y-%m-%d"),
        (now + timedelta(days=6)).strftime("%Y-%m-%d"),
        (now + timedelta(days=7)).strftime("%Y-%m-%d"),
        (now + timedelta(days=8)).strftime("%Y-%m-%d"),
    ]
    
    print(f"regId: {regId} (서울)")
    print(f"시도할 tmFc 후보: {tmFc_candidates[:5]}... (총 {len(tmFc_candidates)}개)")
    print(f"시도할 날짜: {test_dates}")
    
    # 각 조합을 시도
    success = False
    for test_date in test_dates:
        for tmFc in tmFc_candidates:
            try:
                print(f"\n시도: tmFc={tmFc}, target_date={test_date}")
                response = service.fetch_weather(regId=regId, tmFc=tmFc)
                
                # 응답 확인
                if "response" in response:
                    resp = response["response"]
                    if "header" in resp:
                        header = resp["header"]
                        result_code = header.get("resultCode", "00")
                        if result_code == "00" and "body" in resp:
                            # 성공! 데이터가 있음
                            print(f"\n✅ 데이터 발견: tmFc={tmFc}, target_date={test_date}")
                            print(f"응답 키: {list(response.keys())}")
                            
                            # 응답 원본 전체 출력
                            print("\n" + "=" * 60)
                            print("API 응답 원본 (전체):")
                            print("=" * 60)
                            print(json.dumps(response, ensure_ascii=False, indent=2))
                            print("=" * 60)
                            
                            # 파싱 테스트
                            weather_info = service.parse_weather_response(
                                response=response,
                                target_date=test_date,
                                region_canonical="서울특별시",
                                tmFc=tmFc
                            )
                            
                            if weather_info:
                                print("\n✅ 날씨 정보 파싱 성공")
                                print(f"  지역: {weather_info['region']}")
                                print(f"  날짜: {weather_info['date']}")
                                print(f"  기온: {weather_info['temperature']['min']}°C ~ {weather_info['temperature']['max']}°C")
                                print(f"  delta_days: {weather_info['delta_days']}")
                                print(f"  source: {weather_info['source']}")
                            else:
                                print("\n⚠️  날씨 정보 파싱 실패 (응답 구조 확인 필요)")
                            
                            success = True
                            break
                        else:
                            result_msg = header.get("resultMsg", "")
                            if result_code != "03":  # NO_DATA가 아닌 다른 에러만 출력
                                print(f"  ⚠️  resultCode={result_code}, resultMsg={result_msg}")
                
                if success:
                    break
                    
            except Exception as e:
                print(f"  ❌ 오류: {str(e)}")
                continue
        
        if success:
            break
    
    if not success:
        print("\n⚠️  모든 조합을 시도했지만 데이터를 찾을 수 없습니다.")
        print("   API가 현재 데이터를 제공하지 않을 수 있습니다.")
        print("   또는 API 키나 파라미터에 문제가 있을 수 있습니다.")
        print("\n   마지막 시도한 응답 구조:")
        # 마지막 시도한 응답 출력 (있다면)
        try:
            last_response = service.fetch_weather(regId=regId, tmFc=tmFc_candidates[0])
            print(json.dumps(last_response, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"   응답 확인 실패: {str(e)}")


def test_workflow_integration():
    """워크플로우 통합 테스트"""
    print("\n=== 워크플로우 통합 테스트 ===")
    
    # 테스트용 아이템 데이터 (최소한의 구조)
    test_tops = [
        {
            "id": "top1",
            "attributes": {
                "category": {"main": "top", "sub": "tshirt"},
                "color": {"primary": "blue"},
                "style_tags": ["casual"],
                "scores": {"formality": 0.3}
            }
        }
    ]
    
    test_bottoms = [
        {
            "id": "bottom1",
            "attributes": {
                "category": {"main": "bottom", "sub": "jeans"},
                "color": {"primary": "blue"},
                "style_tags": ["casual"],
                "scores": {"formality": 0.3}
            }
        }
    ]
    
    # 날씨 정보가 포함된 사용자 요청
    target_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    user_request = f"서울에서 {target_date}에 입을 옷 추천해줘"
    
    print(f"사용자 요청: {user_request}")
    
    initial_state: RecommendationState = {
        "tops": test_tops,
        "bottoms": test_bottoms,
        "candidates": [],
        "llm_recommendations": None,
        "final_outfits": [],
        "metadata": {},
        "user_request": user_request,
        "weather_info": None,
        "weather_query": None,
        "clarifying_question": None,
        "count": 1
    }
    
    try:
        workflow = get_recommendation_workflow()
        print("\n워크플로우 실행 중...")
        final_state = workflow.invoke(initial_state)
        
        print("\n✅ 워크플로우 실행 완료")
        print(f"  weather_query: {final_state.get('weather_query')}")
        print(f"  weather_info: {final_state.get('weather_info')}")
        print(f"  clarifying_question: {final_state.get('clarifying_question')}")
        print(f"  final_outfits 개수: {len(final_state.get('final_outfits', []))}")
        
        if final_state.get('metadata', {}).get('weather_unavailable_reason'):
            print(f"  날씨 불가 이유: {final_state['metadata']['weather_unavailable_reason']}")
        
    except Exception as e:
        print(f"\n❌ 워크플로우 실행 실패: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    """모든 테스트 실행"""
    print("=" * 60)
    print("날씨 기능 테스트 시작")
    print("=" * 60)
    
    try:
        # 1. 지역 정규화 테스트
        test_weather_resolver()
        
        # 2. tmFc 선택 테스트
        test_tmfc_selection()
        
        # 3. 날씨 API 호출 테스트 (API 키 필요)
        test_weather_api()
        
        # 4. 워크플로우 통합 테스트
        # 주의: 이 테스트는 실제 Azure OpenAI API를 호출하므로 비용이 발생할 수 있습니다
        # test_workflow_integration()
        
        print("\n" + "=" * 60)
        print("✅ 모든 테스트 완료")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
