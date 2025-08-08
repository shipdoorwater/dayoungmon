#!/usr/bin/env python3
"""
화장품 품질관리 법규 검토 툴 메인 실행 파일
"""

import sys
import os
import warnings
from pathlib import Path

# 경고 메시지 억제
os.environ['TK_SILENCE_DEPRECATION'] = '1'
warnings.filterwarnings('ignore', category=UserWarning, module='urllib3')

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from src.ui.main_window import MainWindow
    
    def main():
        """메인 함수"""
        print("화장품 품질관리 법규 검토 툴을 시작합니다...")
        
        # GUI 애플리케이션 실행
        app = MainWindow()
        app.run()
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"모듈 가져오기 오류: {e}")
    print("가상환경이 활성화되어 있는지 확인하고 필요한 라이브러리가 설치되어 있는지 확인하세요.")
    print("다음 명령어로 라이브러리를 설치하세요:")
    print("pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"실행 중 오류가 발생했습니다: {e}")
    sys.exit(1)