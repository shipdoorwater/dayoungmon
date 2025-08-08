from enum import Enum

class ViolationType(Enum):
    """위반 유형"""
    MEDICAL_CLAIM = "의약품적 표현"
    EXAGGERATED_EFFECT = "효능 과장"
    SAFETY_MISREPRESENTATION = "안전성 허위"
    SUPERLATIVE_EXPRESSION = "최상급 표현"
    COMPARATIVE_AD_VIOLATION = "비교광고 위반"

class SeverityLevel(Enum):
    """위반 심각도"""
    HIGH = "높음"
    MEDIUM = "중간"
    LOW = "낮음"