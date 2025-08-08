#!/usr/bin/env python3
"""
패턴 마이그레이션 스크립트
기존 하드코딩된 패턴을 데이터베이스로 이동
"""

import sys
import os

# src 모듈을 import하기 위한 경로 설정
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data.pattern_manager import PatternManager

def main():
    """메인 함수"""
    print("🔄 패턴 마이그레이션 시작...")
    
    try:
        # PatternManager 인스턴스 생성
        pattern_manager = PatternManager()
        
        # 기존 패턴 수 확인
        stats_before = pattern_manager.get_pattern_statistics()
        print(f"📊 마이그레이션 전 패턴 수: {stats_before['total_patterns']}")
        
        # 마이그레이션 실행
        success = pattern_manager.migrate_hardcoded_patterns()
        
        if success:
            # 마이그레이션 후 통계
            stats_after = pattern_manager.get_pattern_statistics()
            print(f"📊 마이그레이션 후 패턴 수: {stats_after['total_patterns']}")
            print(f"✅ {stats_after['total_patterns'] - stats_before['total_patterns']}개 패턴 추가됨")
            
            # 위반 유형별 분포 출력
            print("\n📈 위반 유형별 패턴 분포:")
            for violation_type, count in stats_after['type_distribution'].items():
                print(f"  - {violation_type}: {count}개")
            
            # 심각도별 분포 출력
            print("\n⚠️ 심각도별 패턴 분포:")
            for severity, count in stats_after['severity_distribution'].items():
                print(f"  - {severity}: {count}개")
            
            print("\n🎉 패턴 마이그레이션이 성공적으로 완료되었습니다!")
            
            # 패턴 백업 생성
            backup_path = "data/patterns_backup.json"
            if pattern_manager.export_patterns(backup_path):
                print(f"💾 패턴 백업 파일 생성: {backup_path}")
            
        else:
            print("❌ 패턴 마이그레이션 실패")
            return 1
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())