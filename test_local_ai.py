#!/usr/bin/env python3
"""
로컬 AI 기능 테스트 스크립트
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.file_processor import FileProcessor, preprocess_text
from src.core.regulation_checker import RegulationChecker
from src.core.local_ai_analyzer import LocalAIAnalyzer

def test_local_ai_functionality():
    """로컬 AI 기능 테스트"""
    print("=== 로컬 AI (Ollama) 기능 테스트 ===\n")
    
    # 초기화
    file_processor = FileProcessor()
    regulation_checker = RegulationChecker()
    local_ai_analyzer = LocalAIAnalyzer()
    
    print("1. 로컬 AI 환경 확인")
    print(f"   Ollama 라이브러리: {'✅ 설치됨' if local_ai_analyzer.ollama_available else '❌ 없음'}")
    print(f"   Ollama 서비스: {'✅ 실행중' if local_ai_analyzer.ollama_running else '❌ 중지'}")
    print(f"   사용 가능 여부: {'✅ 가능' if local_ai_analyzer.is_available() else '❌ 불가능'}")
    
    if local_ai_analyzer.available_models:
        print(f"   사용 가능한 모델: {', '.join(local_ai_analyzer.available_models)}")
        print(f"   선택된 모델: {local_ai_analyzer.get_best_model()}")
    else:
        print("   사용 가능한 모델: 없음")
    
    if not local_ai_analyzer.is_available():
        print("\n=== 설치 가이드 ===")
        guide = local_ai_analyzer.get_installation_guide()
        
        print("설치 단계:")
        for step in guide['installation_steps']:
            print(f"   {step}")
        
        print("\n권장 모델:")
        for model in guide['recommended_models']:
            print(f"   • {model}")
        
        print("\n시스템 요구사항:")
        for key, value in guide['system_requirements'].items():
            print(f"   {key}: {value}")
        
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
    
    print(f"   기본 검사 결과: {len(basic_violations)}건 위반사항")
    print(f"   위험도: {basic_report['risk_level']}")
    
    # 로컬 AI 분석 수행
    print("\n4. 로컬 AI 분석 수행 (시간이 많이 소요될 수 있습니다...)")
    try:
        local_ai_result = local_ai_analyzer.analyze_text(processed_text)
        
        if local_ai_result:
            print("✅ 로컬 AI 분석 완료")
            print(f"   사용된 모델: {local_ai_result.model_name}")
            print(f"   로컬 AI 위반사항: {len(local_ai_result.violations)}건")
            print(f"   신뢰도: {local_ai_result.confidence_score:.1%}")
            print(f"   처리 시간: {local_ai_result.processing_time:.1f}초")
            print(f"   모델 크기: {local_ai_result.resource_usage.get('model_size', 'Unknown')}")
            
            # 성능 비교
            print("\n5. 성능 비교 분석")
            print(f"   기본 검사: {len(basic_violations)}건")
            print(f"   로컬 AI: {len(local_ai_result.violations)}건")
            
            if len(local_ai_result.violations) > len(basic_violations):
                print("   🔍 로컬 AI가 더 많은 위반사항을 발견했습니다.")
            elif len(local_ai_result.violations) < len(basic_violations):
                print("   📊 기본 검사가 더 많은 위반사항을 발견했습니다.")
            else:
                print("   ⚖️ 두 방법의 위반사항 개수가 동일합니다.")
                
            # 처리 속도 비교
            basic_time = 0.1  # 기본 검사는 매우 빠름
            speedup = basic_time / local_ai_result.processing_time if local_ai_result.processing_time > 0 else float('inf')
            if speedup < 1:
                print(f"   ⏱️ 로컬 AI가 기본 검사보다 {1/speedup:.1f}배 느립니다.")
            else:
                print(f"   ⚡ 로컬 AI가 예상보다 빠릅니다!")
            
            # 로컬 AI 분석 결과 상세 표시
            print("\n6. 로컬 AI 분석 상세 결과")
            print("=" * 50)
            print("맥락 분석:")
            context_analysis = local_ai_result.contextual_analysis
            print(context_analysis[:200] + "..." if len(context_analysis) > 200 else context_analysis)
            
            print("\n법적 위험도 평가:")
            risk_assessment = local_ai_result.legal_risk_assessment
            print(risk_assessment[:200] + "..." if len(risk_assessment) > 200 else risk_assessment)
            
            print("\n주요 개선 제안:")
            for i, suggestion in enumerate(local_ai_result.improvement_suggestions[:3], 1):
                print(f"{i}. {suggestion}")
            
            # 로컬 AI 발견 위반사항 샘플
            print("\n로컬 AI가 발견한 위반사항 (처음 3개):")
            for i, violation in enumerate(local_ai_result.violations[:3], 1):
                print(f"\n[{i}] {violation.get('text', 'N/A')}")
                print(f"    유형: {violation.get('type', 'N/A')}")
                print(f"    심각도: {violation.get('severity', 'N/A')}")
                print(f"    제안: {violation.get('suggestion', 'N/A')[:100]}...")
        else:
            print("❌ 로컬 AI 분석 실패")
            
    except Exception as e:
        print(f"❌ 로컬 AI 분석 중 오류: {str(e)}")
    
    # 사용량 업데이트된 리포트
    print("\n7. 로컬 AI 사용량 정보")
    usage_report = local_ai_analyzer.get_usage_report()
    print(f"   오늘 사용량: {usage_report['today_requests']}회")
    print(f"   총 사용량: {usage_report['total_requests']}회")
    print(f"   평균 처리 시간: {usage_report['avg_processing_time']:.1f}초")
    print(f"   현재 모델: {usage_report.get('current_model', 'N/A')}")
    
    print("\n✅ 로컬 AI 기능 테스트 완료!")
    print("\n💡 로컬 AI의 장점:")
    print("   • 완전 오프라인 작동 (개인정보 보호)")
    print("   • 사용 후 추가 비용 없음")
    print("   • 네트워크 연결 불필요")
    print("   • 자체 서버에서 실행")

def test_installation_guide():
    """설치 가이드 테스트"""
    print("=== Ollama 설치 가이드 ===\n")
    
    local_ai_analyzer = LocalAIAnalyzer()
    guide = local_ai_analyzer.get_installation_guide()
    
    print("현재 상태:")
    print(f"   Ollama 설치됨: {'✅' if guide['ollama_installed'] else '❌'}")
    print(f"   Ollama 실행중: {'✅' if guide['ollama_running'] else '❌'}")
    print(f"   사용 가능한 모델: {len(guide['available_models'])}개")
    
    if guide['available_models']:
        for model in guide['available_models']:
            print(f"      - {model}")
    
    print("\n설치 단계:")
    for step in guide['installation_steps']:
        print(f"   {step}")
    
    print("\n권장 모델:")
    for model in guide['recommended_models']:
        print(f"   • {model}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--guide":
        test_installation_guide()
    else:
        test_local_ai_functionality()