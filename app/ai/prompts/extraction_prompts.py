"""
이미지 속성 추출 프롬프트 템플릿
"""

from typing import Dict, List

# ENUMS
ENUMS = {
    "category_main": ["outer", "top", "bottom", "onepiece", "shoes", "accessory"],
    "category_sub": [
        "coat",
        "puffer",
        "jacket",
        "blazer",
        "cardigan",
        "hoodie",
        "sweatshirt",
        "blouses",
        "shirt",
        "tshirt",
        "knit",
        "sweater",
        "slacks",
        "jeans",
        "shorts",
        "skirt",
        "dress",
        "sneakers",
        "loafers",
        "heels",
        "boots",
        "camisoles",
        "bag",
        "cap",
        "hat",
        "scarf",
        "belt",
        "other",
        "unknown",
    ],
    "color": [
        "black",
        "white",
        "gray",
        "navy",
        "blue",
        "skyblue",
        "beige",
        "brown",
        "khaki",
        "green",
        "red",
        "pink",
        "purple",
        "yellow",
        "orange",
        "cream",
        "charcoal",
        "ivory",
        "camel",
        "olive",
        "wine",
        "mint",
        "silver",
        "gold",
        "lavender",
        "mustard",
        "denim",
        "indigo",
        "other",
        "unknown",
    ],
    "tone": [
        "light",
        "dark",
        "muted",
        "vivid",
        "pastel",
        "deep",
        "neon",
        "neutral",
        "other",
        "unknown",
    ],
    "pattern": [
        "solid",
        "stripe",
        "check",
        "houndstooth",
        "dot",
        "floral",
        "animal",
        "argyle",
        "graphic",
        "camo",
        "other",
        "unknown",
    ],
    "material": [
        "cotton",
        "denim",
        "knit",
        "wool",
        "leather",
        "suede",
        "poly",
        "linen",
        "silk",
        "corduroy",
        "fleece",
        "velvet",
        "chiffon",
        "other",
        "unknown",
    ],
    "fit": [
        "tight",
        "slim",
        "regular",
        "loose",
        "oversized",
        "a-line",
        "flare",
        "wide",
        "other",
        "unknown",
    ],
    "neckline": [
        "crew",
        "vneck",
        "u-neck",
        "collar",
        "turtleneck",
        "mock-neck",
        "square",
        "off-shoulder",
        "boat-neck",
        "hood",
        "other",
        "unknown",
    ],
    "sleeve": ["sleeveless", "cap", "short", "half", "long", "other", "unknown"],
    "length": [
        "cropped",
        "waist",
        "hip",
        "thigh",
        "knee",
        "long",
        "maxi",
        "other",
        "unknown",
    ],
    "closure": ["zipper", "button", "wrap", "hook", "open", "none", "other", "unknown"],
    "style_tags": [
        "minimal",
        "classic",
        "street",
        "sporty",
        "gorpcore",
        "preppy",
        "amekaji",
        "feminine",
        "chic",
        "vintage",
        "business",
        "formal",
        "casual",
        "other",
    ],
    "season": ["spring", "summer", "fall", "winter", "all-season", "transitional"],
}

ALIASES = {
    "category_main": {
        "clothing": "top",
        "top": "top",
        "sweater": "top",
        "knitwear": "top",
        "blouses": "top",
        "cardigan": "outer",
        "jacket": "outer",
        "coat": "outer",
        "puffer": "outer",
        "pants": "bottom",
        "trousers": "bottom",
        "jeans": "bottom",
        "skirt": "bottom",
        "dress": "onepiece",
        "gown": "onepiece",
        "sneakers": "shoes",
        "boots": "shoes",
        "heels": "shoes",
        "handbag": "accessory",
        "cap": "accessory",
        "hat": "accessory",
        "belt": "accessory",
    },
    "category_sub": {
        "round-neck": "tshirt",
        "tee": "tshirt",
        "knitted-sweater": "knit",
        "pullover": "sweater",
        "slacks": "slacks",
        "suit-pants": "slacks",
        "chinos": "slacks",
        "denim-pants": "jeans",
        "blue-jeans": "jeans",
        "mini-skirt": "skirt",
        "maxi-skirt": "skirt",
        "running-shoes": "sneakers",
        "trainers": "sneakers",
        "camisole": "camisoles",
        "tank-top": "camisoles",
        "beanie": "cap",
        "beret": "hat",
        "muffler": "scarf",
    },
    "color": {
        "dark blue": "indigo",
        "navy blue": "indigo",  # 진청/남색은 indigo로 통일
        "light blue": "skyblue",
        "baby blue": "skyblue",
        "wine red": "wine",
        "burgundy": "wine",
        "dark green": "olive",
        "forest green": "olive",
        "gold metal": "gold",
        "silver metal": "silver",
        "off white": "ivory",
        "bone": "ivory",
    },
    "tone": {
        "navy": "dark",
        "darkest": "dark",
        "pale": "pastel",
        "soft": "pastel",
        "dusty": "muted",
        "ashy": "muted",  # Muted 톤 매핑 추가
        "bright": "vivid",
        "electric": "neon",
        "rich": "deep",
        "strong": "deep",  # Deep 톤 매핑 추가
    },
    "neckline": {
        "round": "crew",
        "crew neck": "crew",
        "crewneck": "crew",
        "polo": "collar",
        "shirt neck": "collar",
        "half-turtleneck": "mock-neck",
        "semi-turtleneck": "mock-neck",  # 모크넥 매핑
        "low cut": "u-neck",
        "scoop": "u-neck",
    },
    "material": {
        "polyester": "poly",
        "nylon": "poly",
        "synthetic": "poly",
        "jeans": "denim",
        "jean": "denim",
        "cashmere": "wool",
        "angora": "wool",  # 울/모 계열 통합
        "satin": "silk",
        "shiny": "silk",
    },
    "fit": {
        "baggy": "wide",
        "relaxed": "loose",
        "skinny": "tight",
        "bodycon": "tight",
        "comfy": "regular",
        "standard": "regular",
    },
    "length": {
        "short": "cropped",
        "mini": "thigh",  # 기장 세분화 매핑
        "midi": "knee",
        "maxi": "long",
        "full-length": "maxi",
    },
    "closure": {
        "no closure": "none",
        "invisible": "none",
        "buttons": "button",
        "zip": "zipper",
        "tie": "wrap",
        "ribbon": "wrap",  # 랩/끈 형태 매핑
    },
}

# REQUIRED_TOP_KEYS
REQUIRED_TOP_KEYS = {
    "category",
    "color",
    "pattern",
    "material",
    "fit",
    "neckline",
    "sleeve",
    "length",
    "closure",
    "style_tags",
    "scores",
    "meta",
    "confidence",
}

# DEFAULT_OBJ
DEFAULT_OBJ = {
    "category": {"main": "unknown", "sub": "unknown", "confidence": 0.2},
    "color": {
        "primary": "unknown",
        "secondary": [],
        "tone": "unknown",
        "confidence": 0.2,
    },
    "pattern": {"type": "unknown", "confidence": 0.2},
    "material": {"guess": "unknown", "confidence": 0.2},
    "fit": {"type": "unknown", "confidence": 0.2},
    "neckline": "unknown",
    "sleeve": "unknown",
    "length": "unknown",
    "closure": ["none"],
    "details": {
        "neckline": "unknown",
        "sleeve": "unknown",
        "length": "unknown",
        "closure": ["none"],
        "print_or_logo": False,
    },
    "style_tags": [],
    "scores": {
        "formality": 0.3,
        "warmth": 0.3,
        "thickness": 0.3,
        "season": [],
        "versatility": 0.5,
    },
    "meta": {
        "is_layering_piece": False,
        "layering_rank": 2,
        "print_or_logo": False,
        "notes": None,
    },
    "confidence": 0.2,
}

# Azure OpenAI에 최적화된 시스템 프롬프트
SYSTEM_PROMPT = (
    "You are a clothing-attribute extractor. "
    "You MUST output ONLY a valid JSON object. No extra text, no markdown, no code blocks. "
    "Follow the schema EXACTLY. "
    "If uncertain, use 'unknown' or null and lower confidence."
)

# USER_PROMPT - 테스트로 검증된 버전
USER_PROMPT = """당신은 패션 아이템 분석 전문가입니다.
주어진 옷 사진을 보고 다음 정보를 JSON 형식으로 정확하게 추출해주세요.

반드시 다음 JSON 형식으로 응답하세요 (JSON만 출력, 마크다운 코드블록 사용 금지):
{
  "category": {
    "main": "상위 카테고리 (outer/top/bottom/onepiece/shoes/accessory 중 하나)",
    "sub": "하위 카테고리 (coat/jacket/hoodie/tshirt/shirt/sweater/jeans/slacks/skirt/dress 등)",
    "confidence": 0.0~1.0
  },
  "color": {
    "primary": "주요 색상 (black/white/gray/navy/blue/beige/brown/khaki/green/red/pink 등)",
    "secondary": ["보조 색상들"],
    "tone": "톤 (light/dark/muted/vivid/pastel/neutral 등)",
    "confidence": 0.0~1.0
  },
  "material": {
    "guess": "소재 (cotton/denim/knit/wool/leather/poly/linen 등)",
    "confidence": 0.0~1.0
  },
  "pattern": {
    "type": "패턴 (solid/stripe/check/dot/floral/graphic 등)",
    "confidence": 0.0~1.0
  },
  "fit": {
    "type": "핏 (tight/slim/regular/loose/oversized/wide 등)",
    "confidence": 0.0~1.0
  },
  "neckline": "넥라인 (crew/vneck/collar/turtleneck/hood 등, 해당 시)",
  "sleeve": "소매 (sleeveless/short/long 등, 해당 시)",
  "length": "기장 (cropped/waist/hip/knee/long 등)",
  "closure": ["여밈 방식 (zipper/button/none 등)"],
  "style_tags": ["스타일 태그 (minimal/classic/street/sporty/casual/business/formal 등)"],
  "scores": {
    "formality": 0.0~1.0 (캐주얼 0 ~ 포멀 1),
    "warmth": 0.0~1.0 (시원함 0 ~ 따뜻함 1),
    "thickness": 0.0~1.0 (얇음 0.1 ~ 두꺼움 1.0),
    "season": ["적합한 계절들 (spring/summer/fall/winter/all-season)"],
    "versatility": 0.0~1.0 (활용도)
  },
  "meta": {
    "is_layering_piece": true/false,
    "layering_rank": 1~3 (1:inner, 2:mid, 3:outer),
    "print_or_logo": true/false,
    "notes": "기타 특이사항 또는 null"
  },
  "confidence": 전체 분석 신뢰도 0.0~1.0
}

중요 규칙:
- JSON만 출력하세요. 마크다운(```), 주석, 다른 텍스트 절대 사용 금지
- 모든 필드를 채워주세요. 확실하지 않으면 'unknown'을 사용하고 confidence를 낮게 설정
- 영어 소문자로 작성하세요
- season과 closure, style_tags는 반드시 배열로 제공
- neckline, sleeve, length, closure는 반드시 최상위 키로 포함
"""


# build_retry_prompt
def build_retry_prompt(errors: List[str]) -> str:
    """재시도용 프롬프트 생성: 여태까지의 첨삭 사항 및 스키마 변경 반영"""

    # AI가 반드시 지켜야 할 Top-level 키 리스트 (알파벳 순 정렬)
    expected_keys = sorted(list(REQUIRED_TOP_KEYS))

    return f"""Fix your output to be VALID JSON and match the schema EXACTLY.

Errors detected in your previous response:
- {chr(10).join(errors[:10])}

MUST FOLLOW THESE CRITICAL RULES:
1. Return ONLY ONE JSON object. No extra text, no markdown (no ```json), no code blocks.
2. Top-level keys must be EXACTLY: {expected_keys}
3. 'neckline', 'sleeve', and 'length' MUST be top-level keys (NOT nested under details).
4. 'closure' and 'scores.season' MUST be an ARRAY of strings (e.g., ["button"], ["spring", "fall"]).
5. All confidence and score fields must be between 0.0 and 1.0.
6. 'meta.layering_rank' must be an integer (1, 2, or 3).

STRICT ENUM VALIDATION:
- category.main: {ENUMS["category_main"]}
- color.tone: {ENUMS["tone"]}
- material.guess: {ENUMS["material"]}
- fit.type: {ENUMS["fit"]}
- pattern.type: {ENUMS["pattern"]}
- neckline: {ENUMS["neckline"]}
- sleeve: {ENUMS["sleeve"]}
- length: {ENUMS["length"]}
- season: {ENUMS["season"]}

Use "unknown" for any field if you are unsure or the attribute is not visible.
Return corrected JSON ONLY.
"""
