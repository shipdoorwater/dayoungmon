#!/usr/bin/env python3
"""
AI 기능 테스트 스크립트
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.file_processor import FileProcessor, preprocess_text
from src.core.regulation_checker import RegulationChecker
from src.core.ai_analyzer import AIAnalyzer

def test_ai_functionality():
    """AI 기능 테스트"""
    print("=== AI 기능 테스트 ===\n")
    
    # 초기화
    file_processor = FileProcessor()
    regulation_checker = RegulationChecker()
    ai_analyzer = AIAnalyzer()
    
    # AI 사용 가능 여부 확인
    print("1. AI 사용 가능 여부 확인")
    if ai_analyzer.is_available():
        print("✅ AI 분석 사용 가능")
        usage_report = ai_analyzer.get_usage_report()
        print(f"   오늘 사용량: {usage_report['today_requests']}/{usage_report['daily_limit']}회")
        print(f"   월간 비용: ${usage_report['month_cost']:.4f}/${usage_report['monthly_budget']:.2f}")
    else:
        print("❌ AI 분석 사용 불가")
        print("   API 키를 설정하려면:")
        print("   1. .env.example을 .env로 복사")
        print("   2. ANTHROPIC_API_KEY에 실제 API 키 입력")
        print("   3. 애플리케이션 재시작")
        return
    
    # 샘플 텍스트 로드
    sample_file = "assets/sample_text.txt"
    print(f"\n2. 샘플 텍스트 로드: {sample_file}")
    
    text = file_processor.extract_text(sample_file)
    if not text:
        print("❌ 텍스트 로드 실패")
        return
    
    processed_text = preprocess_text(text)
    print(f"✅ 텍스트 로드 성공 ({len(processed_text)}자)")
    
    # 기본 검사 수행
    print("\n3. 기본 키워드 검사 수행")
    basic_violations = regulation_checker.check_violations(processed_text)
    basic_report = regulation_checker.generate_report(basic_violations, processed_text)
    
    print(f"   기본 검사 결과: {len(basic_violations)}건 위반사항 발견")
    print(f"   위험도: {basic_report['risk_level']}")
    
    # AI 분석 수행
    print("\n4. AI 분석 수행 (시간이 소요될 수 있습니다...)")
    try:
        ai_result = ai_analyzer.analyze_text(processed_text)
        
        if ai_result:
            print("✅ AI 분석 완료")
            print(f"   AI 위반사항: {len(ai_result.violations)}건")
            print(f"   신뢰도: {ai_result.confidence_score:.1%}")
            print(f"   처리 시간: {ai_result.processing_time:.1f}초")
            print(f"   예상 비용: ${ai_result.cost_estimate:.4f}")
            
            # 성능 비교
            print("\n5. 성능 비교 분석")
            print(f"   기본 검사: {len(basic_violations)}건")
            print(f"   AI 분석: {len(ai_result.violations)}건")
            
            if len(ai_result.violations) > len(basic_violations):
                print("   🔍 AI가 더 많은 위반사항을 발견했습니다.")
            elif len(ai_result.violations) < len(basic_violations):
                print("   📊 기본 검사가 더 많은 위반사항을 발견했습니다.")
            else:
                print("   ⚖️ 두 방법의 위반사항 개수가 동일합니다.")
            
            # AI 분석 결과 상세 표시
            print("\n6. AI 분석 상세 결과")
            print("=" * 50)
            print("맥락 분석:")
            print(ai_result.contextual_analysis[:200] + "..." if len(ai_result.contextual_analysis) > 200 else ai_result.contextual_analysis)
            
            print("\n법적 위험도 평가:")
            print(ai_result.legal_risk_assessment[:200] + "..." if len(ai_result.legal_risk_assessment) > 200 else ai_result.legal_risk_assessment)
            
            print("\n주요 개선 제안:")
            for i, suggestion in enumerate(ai_result.improvement_suggestions[:3], 1):
                print(f"{i}. {suggestion}")
            
            # AI 발견 위반사항 샘플
            print("\nAI가 발견한 위반사항 (처음 3개):")
            for i, violation in enumerate(ai_result.violations[:3], 1):
                print(f"\n[{i}] {violation.get('text', 'N/A')}")
                print(f"    유형: {violation.get('type', 'N/A')}")
                print(f"    심각도: {violation.get('severity', 'N/A')}")
                print(f"    제안: {violation.get('suggestion', 'N/A')[:100]}...")
        else:
            print("❌ AI 분석 실패")
            
    except Exception as e:
        print(f"❌ AI 분석 중 오류: {str(e)}")
    
    # 사용량 업데이트된 리포트
    print("\n7. 업데이트된 사용량 정보")
    updated_usage = ai_analyzer.get_usage_report()
    print(f"   오늘 사용량: {updated_usage['today_requests']}/{updated_usage['daily_limit']}회")
    print(f"   남은 일일 한도: {updated_usage['remaining_daily']}회")
    print(f"   월간 누적 비용: ${updated_usage['month_cost']:.4f}")
    print(f"   남은 월간 예산: ${updated_usage['remaining_budget']:.4f}")
    
    print("\n✅ AI 기능 테스트 완료!")

def test_without_api():
    """API 키 없이 테스트"""
    print("=== API 키 없이 기본 기능 테스트 ===\n")
    
    ai_analyzer = AIAnalyzer()
    
    print("AI 사용 가능 여부:", "가능" if ai_analyzer.is_available() else "불가능")
    
    if not ai_analyzer.is_available():
        print("이는 정상적인 동작입니다. API 키가 설정되지 않았을 때의 처리를 확인했습니다.")
    
    print("\n기본 검사는 API 키 없이도 정상 작동합니다.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--no-api":
        test_without_api()
    else:
        test_ai_functionality()