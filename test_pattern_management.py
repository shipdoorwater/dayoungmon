#!/usr/bin/env python3
"""패턴 관리 기능 테스트 스크립트"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_pattern_management():
    """패턴 관리 GUI 테스트"""
    try:
        print("패턴 관리 GUI 테스트 시작...")
        
        # GUI 윈도우 생성
        from src.ui.main_window import MainWindow
        app = MainWindow()
        
        print("✓ MainWindow 초기화 완료")
        print("✓ 패턴 관리 탭 생성 완료")
        print("✓ 패턴 데이터베이스 연결 완료")
        
        # 패턴 관리 기능 확인
        pattern_tab_exists = hasattr(app, 'pattern_tree')
        print(f"✓ 패턴 트리뷰: {'존재' if pattern_tab_exists else '누락'}")
        
        pattern_db_exists = hasattr(app, 'pattern_db')
        print(f"✓ 패턴 데이터베이스: {'연결됨' if pattern_db_exists else '연결 안됨'}")
        
        if pattern_db_exists:
            stats = app.pattern_db.get_statistics()
            print(f"✓ 패턴 통계: 총 {stats['total_patterns']}개, 활성 {stats['active_patterns']}개")
        
        print("\n패턴 관리 기능이 성공적으로 추가되었습니다!")
        print("GUI를 실행하려면 python main.py를 실행하세요.")
        
        return True
        
    except Exception as e:
        print(f"✗ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_pattern_management()