import sqlite3
import os
import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

# enum들 import
from ..core.types import ViolationType, SeverityLevel

@dataclass
class PatternRule:
    """패턴 규칙 데이터 클래스"""
    id: Optional[int] = None
    pattern: str = ""
    violation_type: ViolationType = ViolationType.MEDICAL_CLAIM
    severity: SeverityLevel = SeverityLevel.MEDIUM
    legal_basis: str = ""
    suggestion: str = ""
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    description: str = ""
    category: str = ""

class PatternDatabase:
    """패턴 규칙 데이터베이스 관리 클래스"""
    
    def __init__(self, db_path: str = "data/patterns.db"):
        self.db_path = db_path
        self._ensure_data_directory()
        self._init_database()
    
    def _ensure_data_directory(self):
        """데이터 디렉터리 생성"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def _init_database(self):
        """데이터베이스 초기화"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS pattern_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern TEXT NOT NULL,
                    violation_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    legal_basis TEXT NOT NULL,
                    suggestion TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT,
                    category TEXT
                )
            ''')
            
            # 인덱스 생성
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_violation_type 
                ON pattern_rules(violation_type)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_is_active 
                ON pattern_rules(is_active)
            ''')
    
    def add_pattern(self, pattern_rule: PatternRule) -> int:
        """새 패턴 규칙 추가"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                INSERT INTO pattern_rules 
                (pattern, violation_type, severity, legal_basis, suggestion, 
                 is_active, description, category)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pattern_rule.pattern,
                pattern_rule.violation_type.name,
                pattern_rule.severity.name,
                pattern_rule.legal_basis,
                pattern_rule.suggestion,
                pattern_rule.is_active,
                pattern_rule.description,
                pattern_rule.category
            ))
            return cursor.lastrowid
    
    def get_pattern(self, pattern_id: int) -> Optional[PatternRule]:
        """ID로 패턴 규칙 조회"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM pattern_rules WHERE id = ?
            ''', (pattern_id,))
            
            row = cursor.fetchone()
            if row:
                return self._row_to_pattern_rule(row)
            return None
    
    def get_active_patterns(self, violation_type: Optional[ViolationType] = None) -> List[PatternRule]:
        """활성화된 패턴 규칙들 조회"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if violation_type:
                cursor = conn.execute('''
                    SELECT * FROM pattern_rules 
                    WHERE is_active = 1 AND violation_type = ?
                    ORDER BY severity DESC, id
                ''', (violation_type.name,))
            else:
                cursor = conn.execute('''
                    SELECT * FROM pattern_rules 
                    WHERE is_active = 1 
                    ORDER BY violation_type, severity DESC, id
                ''')
            
            return [self._row_to_pattern_rule(row) for row in cursor.fetchall()]
    
    def get_all_patterns(self) -> List[PatternRule]:
        """모든 패턴 규칙 조회"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM pattern_rules 
                ORDER BY violation_type, severity DESC, id
            ''')
            
            return [self._row_to_pattern_rule(row) for row in cursor.fetchall()]
    
    def update_pattern(self, pattern_rule: PatternRule) -> bool:
        """패턴 규칙 업데이트"""
        if not pattern_rule.id:
            return False
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                UPDATE pattern_rules 
                SET pattern = ?, violation_type = ?, severity = ?, 
                    legal_basis = ?, suggestion = ?, is_active = ?,
                    description = ?, category = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (
                pattern_rule.pattern,
                pattern_rule.violation_type.name,
                pattern_rule.severity.name,
                pattern_rule.legal_basis,
                pattern_rule.suggestion,
                pattern_rule.is_active,
                pattern_rule.description,
                pattern_rule.category,
                pattern_rule.id
            ))
            
            return cursor.rowcount > 0
    
    def delete_pattern(self, pattern_id: int) -> bool:
        """패턴 규칙 삭제"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                DELETE FROM pattern_rules WHERE id = ?
            ''', (pattern_id,))
            
            return cursor.rowcount > 0
    
    def deactivate_pattern(self, pattern_id: int) -> bool:
        """패턴 규칙 비활성화"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                UPDATE pattern_rules 
                SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (pattern_id,))
            
            return cursor.rowcount > 0
    
    def search_patterns(self, keyword: str) -> List[PatternRule]:
        """패턴 검색"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM pattern_rules 
                WHERE pattern LIKE ? OR description LIKE ? OR category LIKE ?
                ORDER BY violation_type, severity DESC
            ''', (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
            
            return [self._row_to_pattern_rule(row) for row in cursor.fetchall()]
    
    def get_patterns_by_category(self, category: str) -> List[PatternRule]:
        """카테고리별 패턴 조회"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM pattern_rules 
                WHERE category = ? AND is_active = 1
                ORDER BY severity DESC, id
            ''', (category,))
            
            return [self._row_to_pattern_rule(row) for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict:
        """패턴 통계 정보"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # 전체 패턴 수
            total_count = conn.execute('SELECT COUNT(*) as count FROM pattern_rules').fetchone()['count']
            
            # 활성화된 패턴 수
            active_count = conn.execute('SELECT COUNT(*) as count FROM pattern_rules WHERE is_active = 1').fetchone()['count']
            
            # 위반 유형별 분포
            type_distribution = {}
            cursor = conn.execute('''
                SELECT violation_type, COUNT(*) as count 
                FROM pattern_rules 
                WHERE is_active = 1 
                GROUP BY violation_type
            ''')
            
            for row in cursor.fetchall():
                type_distribution[row['violation_type']] = row['count']
            
            # 심각도별 분포
            severity_distribution = {}
            cursor = conn.execute('''
                SELECT severity, COUNT(*) as count 
                FROM pattern_rules 
                WHERE is_active = 1 
                GROUP BY severity
            ''')
            
            for row in cursor.fetchall():
                severity_distribution[row['severity']] = row['count']
            
            return {
                'total_patterns': total_count,
                'active_patterns': active_count,
                'inactive_patterns': total_count - active_count,
                'type_distribution': type_distribution,
                'severity_distribution': severity_distribution
            }
    
    def backup_to_json(self, backup_path: str) -> bool:
        """패턴을 JSON 파일로 백업"""
        try:
            patterns = self.get_all_patterns()
            backup_data = []
            
            for pattern in patterns:
                backup_data.append({
                    'pattern': pattern.pattern,
                    'violation_type': pattern.violation_type.name,
                    'severity': pattern.severity.name,
                    'legal_basis': pattern.legal_basis,
                    'suggestion': pattern.suggestion,
                    'is_active': pattern.is_active,
                    'description': pattern.description,
                    'category': pattern.category
                })
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            logging.error(f"백업 실패: {e}")
            return False
    
    def restore_from_json(self, backup_path: str, clear_existing: bool = False) -> bool:
        """JSON 파일에서 패턴 복원"""
        try:
            if clear_existing:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute('DELETE FROM pattern_rules')
            
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            for data in backup_data:
                pattern_rule = PatternRule(
                    pattern=data['pattern'],
                    violation_type=ViolationType[data['violation_type']],
                    severity=SeverityLevel[data['severity']],
                    legal_basis=data['legal_basis'],
                    suggestion=data['suggestion'],
                    is_active=data.get('is_active', True),
                    description=data.get('description', ''),
                    category=data.get('category', '')
                )
                self.add_pattern(pattern_rule)
            
            return True
        except Exception as e:
            logging.error(f"복원 실패: {e}")
            return False
    
    def _row_to_pattern_rule(self, row) -> PatternRule:
        """데이터베이스 행을 PatternRule 객체로 변환"""
        return PatternRule(
            id=row['id'],
            pattern=row['pattern'],
            violation_type=ViolationType[row['violation_type']],
            severity=SeverityLevel[row['severity']],
            legal_basis=row['legal_basis'],
            suggestion=row['suggestion'],
            is_active=bool(row['is_active']),
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            description=row.get('description', ''),
            category=row.get('category', '')
        )