import re
import logging
from typing import List, Dict, Tuple
from dataclasses import dataclass
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

@dataclass
class Violation:
    """위반사항 정보"""
    text: str  # 위반 문구
    violation_type: ViolationType  # 위반 유형
    severity: SeverityLevel  # 심각도
    legal_basis: str  # 법적 근거
    suggestion: str  # 개선 제안
    position: int = -1  # 텍스트 내 위치

class RegulationChecker:
    """화장품법 및 광고표시법 위반사항 검출 클래스"""
    
    def __init__(self):
        self.violation_patterns = self._load_violation_patterns()
    
    def _load_violation_patterns(self) -> Dict[ViolationType, List[Dict]]:
        """위반 패턴들을 로드"""
        patterns = {
            ViolationType.MEDICAL_CLAIM: [
                {
                    'pattern': r'(치료|완치|의학적\s*효과|병원|의사|처방|진료|임상|약효)',
                    'severity': SeverityLevel.HIGH,
                    'legal_basis': '화장품법 제2조(정의), 약사법 제85조',
                    'suggestion': '화장품의 기능적 효과로 표현을 변경하세요'
                },
                {
                    'pattern': r'(항균|살균|세균\s*제거|바이러스\s*차단)',
                    'severity': SeverityLevel.HIGH,
                    'legal_basis': '화장품법 제2조, 의료기기법',
                    'suggestion': '청결 유지나 세정 효과로 표현을 변경하세요'
                }
            ],
            ViolationType.EXAGGERATED_EFFECT: [
                {
                    'pattern': r'(100%\s*효과|완벽한|즉시|바로|하루\s*만에|기적|마법)',
                    'severity': SeverityLevel.HIGH,
                    'legal_basis': '화장품법 제10조(표시·광고의 금지 등)',
                    'suggestion': '점진적 개선이나 도움을 줄 수 있다는 표현으로 변경하세요'
                },
                {
                    'pattern': r'(영구적|평생|절대|무조건|확실히)',
                    'severity': SeverityLevel.MEDIUM,
                    'legal_basis': '표시·광고의 공정화에 관한 법률',
                    'suggestion': '개인차가 있을 수 있음을 명시하세요'
                }
            ],
            ViolationType.SAFETY_MISREPRESENTATION: [
                {
                    'pattern': r'(부작용\s*없음|무해한|100%\s*안전|완전히\s*안전)',
                    'severity': SeverityLevel.HIGH,
                    'legal_basis': '화장품법 제10조, 소비자기본법',
                    'suggestion': '테스트를 거쳤다거나 안전성을 고려했다는 표현으로 변경하세요'
                },
                {
                    'pattern': r'(알레르기\s*반응\s*없음|자극\s*없음)',
                    'severity': SeverityLevel.MEDIUM,
                    'legal_basis': '화장품법 제10조',
                    'suggestion': '개인에 따라 반응이 다를 수 있음을 명시하세요'
                }
            ],
            ViolationType.SUPERLATIVE_EXPRESSION: [
                {
                    'pattern': r'(최고|최상|최적|1위|넘버원|NO\.1|으뜸)',
                    'severity': SeverityLevel.MEDIUM,
                    'legal_basis': '표시·광고의 공정화에 관한 법률 제3조',
                    'suggestion': '객관적 근거가 있는 경우에만 사용하거나 삭제하세요'
                },
                {
                    'pattern': r'(유일한|독보적|독창적|세계\s*최초)',
                    'severity': SeverityLevel.HIGH,
                    'legal_basis': '표시·광고의 공정화에 관한 법률',
                    'suggestion': '검증 가능한 사실이 아닌 경우 삭제하세요'
                }
            ],
            ViolationType.COMPARATIVE_AD_VIOLATION: [
                {
                    'pattern': r'(타제품보다|경쟁사보다|다른\s*브랜드보다|비교\s*불가)',
                    'severity': SeverityLevel.MEDIUM,
                    'legal_basis': '표시·광고의 공정화에 관한 법률 제6조',
                    'suggestion': '객관적 근거 자료와 함께 제시하거나 삭제하세요'
                }
            ]
        }
        return patterns
    
    def check_violations(self, text: str) -> List[Violation]:
        """텍스트에서 위반사항 검출"""
        violations = []
        
        if not text:
            return violations
        
        for violation_type, pattern_list in self.violation_patterns.items():
            for pattern_info in pattern_list:
                pattern = pattern_info['pattern']
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    violation = Violation(
                        text=match.group(),
                        violation_type=violation_type,
                        severity=pattern_info['severity'],
                        legal_basis=pattern_info['legal_basis'],
                        suggestion=pattern_info['suggestion'],
                        position=match.start()
                    )
                    violations.append(violation)
        
        # 중복된 위반사항 제거 (같은 텍스트, 같은 위치)
        unique_violations = []
        seen = set()
        for violation in violations:
            key = (violation.text, violation.position, violation.violation_type)
            if key not in seen:
                seen.add(key)
                unique_violations.append(violation)
        
        # 위치순으로 정렬
        unique_violations.sort(key=lambda x: x.position)
        
        return unique_violations
    
    def generate_report(self, violations: List[Violation], original_text: str) -> Dict:
        """위반사항 리포트 생성"""
        if not violations:
            return {
                'status': 'PASS',
                'total_violations': 0,
                'violations': [],
                'summary': '법규 위반사항이 발견되지 않았습니다.',
                'risk_level': 'LOW'
            }
        
        # 심각도별 분류
        severity_count = {
            SeverityLevel.HIGH: 0,
            SeverityLevel.MEDIUM: 0,
            SeverityLevel.LOW: 0
        }
        
        violation_types = set()
        violation_details = []
        
        for violation in violations:
            severity_count[violation.severity] += 1
            violation_types.add(violation.violation_type)
            
            # 문맥 정보 추가 (앞뒤 20자)
            start = max(0, violation.position - 20)
            end = min(len(original_text), violation.position + len(violation.text) + 20)
            context = original_text[start:end]
            
            violation_details.append({
                'text': violation.text,
                'type': violation.violation_type.value,
                'severity': violation.severity.value,
                'legal_basis': violation.legal_basis,
                'suggestion': violation.suggestion,
                'context': context,
                'position': violation.position
            })
        
        # 전체 위험도 평가
        if severity_count[SeverityLevel.HIGH] > 0:
            risk_level = 'HIGH'
        elif severity_count[SeverityLevel.MEDIUM] > 2:
            risk_level = 'HIGH'
        elif severity_count[SeverityLevel.MEDIUM] > 0:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        return {
            'status': 'VIOLATION_FOUND',
            'total_violations': len(violations),
            'violations': violation_details,
            'severity_summary': {
                'high': severity_count[SeverityLevel.HIGH],
                'medium': severity_count[SeverityLevel.MEDIUM],
                'low': severity_count[SeverityLevel.LOW]
            },
            'violation_types': [vt.value for vt in violation_types],
            'risk_level': risk_level,
            'summary': f'총 {len(violations)}건의 위반사항이 발견되었습니다. 위험도: {risk_level}'
        }