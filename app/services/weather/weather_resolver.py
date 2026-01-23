"""
지역명 정규화 및 regId 매핑
"""
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class WeatherResolver:
    """지역명을 정규화하고 regId로 매핑하는 클래스"""
    
    # 지역 alias 매핑 (정규화용)
    REGION_ALIASES = {
        "서울": "서울특별시",
        "서울시": "서울특별시",
        "서울특별시": "서울특별시",
        "인천": "인천광역시",
        "인천시": "인천광역시",
        "인천광역시": "인천광역시",
        "경기": "경기도",
        "경기도": "경기도",
        "충북": "충청북도",
        "충청북도": "충청북도",
        "충남": "충청남도",
        "충청남도": "충청남도",
        "대전": "대전광역시",
        "대전시": "대전광역시",
        "대전광역시": "대전광역시",
        "세종": "세종특별자치시",
        "세종시": "세종특별자치시",
        "세종특별자치시": "세종특별자치시",
        "강원": "강원도",
        "강원도": "강원도",
        "전북": "전북특별자치도",
        "전라북도": "전북특별자치도",
        "전북특별자치도": "전북특별자치도",
        "전남": "전라남도",
        "전라남도": "전라남도",
        "광주": "광주광역시",
        "광주시": "광주광역시",
        "광주광역시": "광주광역시",
        "경북": "경상북도",
        "경상북도": "경상북도",
        "경남": "경상남도",
        "경상남도": "경상남도",
        "대구": "대구광역시",
        "대구시": "대구광역시",
        "대구광역시": "대구광역시",
        "부산": "부산광역시",
        "부산시": "부산광역시",
        "부산광역시": "부산광역시",
        "울산": "울산광역시",
        "울산시": "울산광역시",
        "울산광역시": "울산광역시",
        "제주": "제주특별자치도",
        "제주도": "제주특별자치도",
        "제주특별자치도": "제주특별자치도",
    }
    
    # 시군구 → 상위 광역 매핑
    CITY_TO_PROVINCE = {
        # 경기도 시군구
        "수원": "경기도",
        "성남": "경기도",
        "용인": "경기도",
        "고양": "경기도",
        "부천": "경기도",
        "안산": "경기도",
        "안양": "경기도",
        "평택": "경기도",
        "시흥": "경기도",
        "김포": "경기도",
        "광명": "경기도",
        "광주": "경기도",  # 경기도 광주시 (광주광역시와 구분)
        "이천": "경기도",
        "오산": "경기도",
        "의정부": "경기도",
        "하남": "경기도",
        "구리": "경기도",
        "안성": "경기도",
        "포천": "경기도",
        "의왕": "경기도",
        "양주": "경기도",
        "여주": "경기도",
        "양평": "경기도",
        "동두천": "경기도",
        "과천": "경기도",
        "가평": "경기도",
        "연천": "경기도",
        # 서울특별시 구
        "강남구": "서울특별시",
        "서초구": "서울특별시",
        "강동구": "서울특별시",
        "송파구": "서울특별시",
        "강서구": "서울특별시",
        "양천구": "서울특별시",
        "영등포구": "서울특별시",
        "마포구": "서울특별시",
        "은평구": "서울특별시",
        "종로구": "서울특별시",
        "중구": "서울특별시",
        "용산구": "서울특별시",
        "성동구": "서울특별시",
        "광진구": "서울특별시",
        "동대문구": "서울특별시",
        "중랑구": "서울특별시",
        "성북구": "서울특별시",
        "강북구": "서울특별시",
        "도봉구": "서울특별시",
        "노원구": "서울특별시",
        # 부산광역시 구
        "해운대구": "부산광역시",
        "수영구": "부산광역시",
        "남구": "부산광역시",
        "중구": "부산광역시",
        "서구": "부산광역시",
        "동구": "부산광역시",
        "영도구": "부산광역시",
        "부산진구": "부산광역시",
        "동래구": "부산광역시",
        "사상구": "부산광역시",
        "사하구": "부산광역시",
        "금정구": "부산광역시",
        "강서구": "부산광역시",
        "연제구": "부산광역시",
        "기장군": "부산광역시",
        # 기타 주요 시군구
        "강릉": "강원도",
        "춘천": "강원도",
        "원주": "강원도",
        "속초": "강원도",
        "전주": "전북특별자치도",
        "익산": "전북특별자치도",
        "군산": "전북특별자치도",
        "목포": "전라남도",
        "여수": "전라남도",
        "순천": "전라남도",
        "포항": "경상북도",
        "구미": "경상북도",
        "경주": "경상북도",
        "창원": "경상남도",
        "진해": "경상남도",
        "김해": "경상남도",
        "거제": "경상남도",
    }
    
    # regId 매핑 (도/광역시 단위)
    REGION_TO_REGID = {
        "서울특별시": "11B10101",
        "인천광역시": "11B20201",
        "경기도": "11B00000",  # 서울·인천·경기 묶음
        "충청북도": "11C10000",
        "충청남도": "11C20000",
        "대전광역시": "11C20401",
        "세종특별자치시": "11C20404",
        "강원도": None,  # 영서/영동으로 분기 필요
        "강원도영서": "11D10000",
        "강원도영동": "11D20000",
        "전북특별자치도": "11F10000",
        "전라남도": "11F20000",
        "광주광역시": "11F20501",
        "경상북도": "11H10000",
        "경상남도": "11H20000",
        "대구광역시": "11H10701",
        "부산광역시": "11H20201",
        "울산광역시": "11H20101",
        "제주특별자치도": "11G00000",
    }
    
    # 애매한 케이스 (disambiguation 필요)
    AMBIGUOUS_REGIONS = {
        "강원도": "강원도는 영서/영동 중 어디야?",
        "전라도": "전북/전남 중 어디야?",
        "경상도": "경북/경남 중 어디야?",
    }
    
    @classmethod
    def resolve_region(cls, region_text: str) -> Dict[str, Any]:
        """
        지역명을 정규화하고 regId로 매핑
        
        Args:
            region_text: 사용자가 입력한 지역명 (예: "서울", "수원", "강원도")
        
        Returns:
            {
                "region_canonical": str,  # 정규화된 지역명
                "regId": Optional[str],  # regId (None이면 disambiguation 필요)
                "needs_disambiguation": bool,  # disambiguation 필요 여부
                "clarifying_question": Optional[str]  # 되묻기 질문
            }
        """
        if not region_text:
            return {
                "region_canonical": None,
                "regId": None,
                "needs_disambiguation": False,
                "clarifying_question": None
            }
        
        region_text = region_text.strip()
        
        # 1. 시군구 → 상위 광역으로 올리기
        if region_text in cls.CITY_TO_PROVINCE:
            region_text = cls.CITY_TO_PROVINCE[region_text]
            logger.info(f"City mapped to province: {region_text}")
        
        # 2. alias 정규화
        canonical = cls.REGION_ALIASES.get(region_text, region_text)
        
        # 3. 애매한 케이스 확인
        if canonical in cls.AMBIGUOUS_REGIONS:
            return {
                "region_canonical": canonical,
                "regId": None,
                "needs_disambiguation": True,
                "clarifying_question": cls.AMBIGUOUS_REGIONS[canonical]
            }
        
        # 4. regId 매핑
        regId = cls.REGION_TO_REGID.get(canonical)
        
        if regId is None:
            # 매핑되지 않은 경우
            logger.warning(f"Region not found in mapping: {canonical}")
            return {
                "region_canonical": canonical,
                "regId": None,
                "needs_disambiguation": False,
                "clarifying_question": f"'{canonical}' 지역은 지원하지 않습니다. 도/시 단위로 입력해주세요."
            }
        
        return {
            "region_canonical": canonical,
            "regId": regId,
            "needs_disambiguation": False,
            "clarifying_question": None
        }
    
    @classmethod
    def resolve_with_disambiguation(cls, region_text: str, disambiguation: str) -> Dict[str, Any]:
        """
        disambiguation 정보를 포함하여 지역명 해결
        
        Args:
            region_text: 지역명
            disambiguation: "영서"/"영동", "전북"/"전남", "경북"/"경남" 등
        
        Returns:
            resolve_region과 동일한 형식
        """
        base_result = cls.resolve_region(region_text)
        
        if not base_result["needs_disambiguation"]:
            return base_result
        
        canonical = base_result["region_canonical"]
        
        # disambiguation 적용
        if canonical == "강원도":
            if "영서" in disambiguation or "서" in disambiguation:
                return {
                    "region_canonical": "강원도영서",
                    "regId": cls.REGION_TO_REGID["강원도영서"],
                    "needs_disambiguation": False,
                    "clarifying_question": None
                }
            elif "영동" in disambiguation or "동" in disambiguation:
                return {
                    "region_canonical": "강원도영동",
                    "regId": cls.REGION_TO_REGID["강원도영동"],
                    "needs_disambiguation": False,
                    "clarifying_question": None
                }
        elif canonical == "전라도":
            if "전북" in disambiguation or "북" in disambiguation:
                return {
                    "region_canonical": "전북특별자치도",
                    "regId": cls.REGION_TO_REGID["전북특별자치도"],
                    "needs_disambiguation": False,
                    "clarifying_question": None
                }
            elif "전남" in disambiguation or "남" in disambiguation:
                return {
                    "region_canonical": "전라남도",
                    "regId": cls.REGION_TO_REGID["전라남도"],
                    "needs_disambiguation": False,
                    "clarifying_question": None
                }
        elif canonical == "경상도":
            if "경북" in disambiguation or "북" in disambiguation:
                return {
                    "region_canonical": "경상북도",
                    "regId": cls.REGION_TO_REGID["경상북도"],
                    "needs_disambiguation": False,
                    "clarifying_question": None
                }
            elif "경남" in disambiguation or "남" in disambiguation:
                return {
                    "region_canonical": "경상남도",
                    "regId": cls.REGION_TO_REGID["경상남도"],
                    "needs_disambiguation": False,
                    "clarifying_question": None
                }
        
        # disambiguation이 명확하지 않은 경우 원래 결과 반환
        return base_result
