from typing import List, Dict, Optional
import logging
from .pattern_db import PatternDatabase, PatternRule
from ..core.types import ViolationType, SeverityLevel

class PatternManager:
    """패턴 관리 클래스"""
    
    def __init__(self, db_path: str = "data/patterns.db"):
        self.db = PatternDatabase(db_path)
        self.logger = logging.getLogger(__name__)
    
    def migrate_hardcoded_patterns(self) -> bool:
        """기존 하드코딩된 패턴을 DB로 마이그레이션"""
        try:
            hardcoded_patterns = self._get_hardcoded_patterns()
            
            for violation_type, pattern_list in hardcoded_patterns.items():
                for pattern_info in pattern_list:
                    pattern_rule = PatternRule(
                        pattern=pattern_info['pattern'],
                        violation_type=violation_type,
                        severity=pattern_info['severity'],
                        legal_basis=pattern_info['legal_basis'],
                        suggestion=pattern_info['suggestion'],
                        is_active=True,
                        description=f"{violation_type.value} 관련 패턴",
                        category="기본"
                    )
                    self.db.add_pattern(pattern_rule)
            
            self.logger.info("하드코딩된 패턴 마이그레이션 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"패턴 마이그레이션 실패: {e}")
            return False
    
    def _get_hardcoded_patterns(self) -> Dict[ViolationType, List[Dict]]:
        """기존 하드코딩된 패턴 반환"""
        return {
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
    
    def add_custom_pattern(self, pattern: str, violation_type: ViolationType, 
                          severity: SeverityLevel, legal_basis: str, 
                          suggestion: str, description: str = "", 
                          category: str = "사용자정의") -> int:
        """사용자 정의 패턴 추가"""
        pattern_rule = PatternRule(
            pattern=pattern,
            violation_type=violation_type,
            severity=severity,
            legal_basis=legal_basis,
            suggestion=suggestion,
            is_active=True,
            description=description,
            category=category
        )
        return self.db.add_pattern(pattern_rule)
    
    def get_patterns_for_checking(self) -> Dict[ViolationType, List[Dict]]:
        """검사용 패턴을 기존 형태로 반환"""
        patterns = {}
        
        for violation_type in ViolationType:
            db_patterns = self.db.get_active_patterns(violation_type)
            pattern_list = []
            
            for db_pattern in db_patterns:
                pattern_list.append({
                    'pattern': db_pattern.pattern,
                    'severity': db_pattern.severity,
                    'legal_basis': db_pattern.legal_basis,
                    'suggestion': db_pattern.suggestion
                })
            
            if pattern_list:
                patterns[violation_type] = pattern_list
        
        return patterns
    
    def update_pattern_status(self, pattern_id: int, is_active: bool) -> bool:
        """패턴 활성화/비활성화"""
        pattern = self.db.get_pattern(pattern_id)
        if pattern:
            pattern.is_active = is_active
            return self.db.update_pattern(pattern)
        return False
    
    def search_similar_patterns(self, text: str) -> List[PatternRule]:
        """유사한 패턴 검색"""
        return self.db.search_patterns(text)
    
    def get_pattern_statistics(self) -> Dict:
        """패턴 통계 반환"""
        return self.db.get_statistics()
    
    def export_patterns(self, file_path: str) -> bool:
        """패턴을 파일로 내보내기"""
        return self.db.backup_to_json(file_path)
    
    def import_patterns(self, file_path: str, clear_existing: bool = False) -> bool:
        """파일에서 패턴 가져오기"""
        return self.db.restore_from_json(file_path, clear_existing)
    
    def validate_pattern(self, pattern: str) -> Dict:
        """패턴 유효성 검사"""
        try:
            import re
            re.compile(pattern)
            return {'valid': True, 'message': '유효한 정규식 패턴입니다.'}
        except re.error as e:
            return {'valid': False, 'message': f'정규식 오류: {str(e)}'}
    
    def get_pattern_usage_stats(self, days: int = 30) -> Dict:
        """패턴 사용 통계 (향후 구현)"""
        # TODO: 패턴별 매칭 횟수, 사용 빈도 등 통계 기능 추가
        return {
            'total_checks': 0,
            'pattern_usage': {},
            'period_days': days
        }