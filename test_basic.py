#!/usr/bin/env python3
"""
기본 기능 테스트 스크립트
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.file_processor import FileProcessor, preprocess_text
from src.core.regulation_checker import RegulationChecker

def test_basic_functionality():
    """기본 기능 테스트"""
    print("=== 화장품 품질관리 법규 검토 툴 기본 기능 테스트 ===\n")
    
    # 파일 프로세서 초기화
    file_processor = FileProcessor()
    regulation_checker = RegulationChecker()
    
    # 샘플 텍스트 파일 테스트
    sample_file = "assets/sample_text.txt"
    
    print(f"1. 파일 처리 테스트: {sample_file}")
    text = file_processor.extract_text(sample_file)
    
    if text:
        print("✅ 텍스트 추출 성공")
        print(f"추출된 텍스트 길이: {len(text)}자")
        print(f"첫 100자: {text[:100]}...")
    else:
        print("❌ 텍스트 추출 실패")
        return
    
    print("\n2. 텍스트 전처리 테스트")
    processed_text = preprocess_text(text)
    print(f"전처리된 텍스트 길이: {len(processed_text)}자")
    
    print("\n3. 법규 위반사항 검사 테스트")
    violations = regulation_checker.check_violations(processed_text)
    print(f"발견된 위반사항: {len(violations)}건")
    
    if violations:
        print("\n발견된 위반사항들:")
        for i, violation in enumerate(violations, 1):
            print(f"\n[{i}] 위반 문구: '{violation.text}'")
            print(f"    위반 유형: {violation.violation_type.value}")
            print(f"    심각도: {violation.severity.value}")
            print(f"    법적 근거: {violation.legal_basis}")
            print(f"    개선 제안: {violation.suggestion}")
    
    print("\n4. 리포트 생성 테스트")
    report = regulation_checker.generate_report(violations, processed_text)
    
    print(f"상태: {report['status']}")
    print(f"총 위반사항: {report['total_violations']}건")
    print(f"위험도: {report['risk_level']}")
    print(f"요약: {report['summary']}")
    
    if 'severity_summary' in report:
        print(f"심각도별 분류:")
        print(f"  높음: {report['severity_summary']['high']}건")
        print(f"  중간: {report['severity_summary']['medium']}건")
        print(f"  낮음: {report['severity_summary']['low']}건")
    
    print(f"위반 유형: {', '.join(report.get('violation_types', []))}")
    
    print("\n✅ 모든 기본 기능 테스트 완료!")
    
    print("\n=== 지원 파일 형식 ===")
    supported_formats = file_processor.get_supported_formats()
    print(f"지원되는 파일 형식: {', '.join(supported_formats)}")
    
    print("\n=== 설치 안내 ===")
    print("이미지 파일 처리를 위해서는 Tesseract OCR 설치가 필요합니다.")
    print("macOS: brew install tesseract tesseract-lang")
    print("Ubuntu: sudo apt-get install tesseract-ocr tesseract-ocr-kor")
    print("Windows: https://github.com/UB-Mannheim/tesseract/wiki")

if __name__ == "__main__":
    test_basic_functionality()