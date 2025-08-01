#!/usr/bin/env python3
"""
하이브리드 분석 시스템 테스트 스크립트
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.file_processor import FileProcessor, preprocess_text
from src.core.hybrid_analyzer import HybridAnalyzer

def test_hybrid_analysis():
    """하이브리드 분석 시스템 테스트"""
    print("=== 하이브리드 분석 시스템 테스트 ===\n")
    
    # 초기화
    file_processor = FileProcessor()
    hybrid_analyzer = HybridAnalyzer()
    
    print("1. 분석 시스템 가용성 확인")
    print(f"   기본 키워드 검사: ✅ 항상 사용 가능")
    print(f"   Claude AI 분석: {'✅ 사용 가능' if hybrid_analyzer.ai_analyzer.is_available() else '❌ 사용 불가 (API 키 필요)'}")
    print(f"   로컬 AI 분석: {'✅ 사용 가능' if hybrid_analyzer.local_ai_analyzer.is_available() else '❌ 사용 불가 (Ollama 설치 필요)'}")
    
    # 샘플 텍스트 로드
    sample_file = "assets/sample_text.txt"
    print(f"\n2. 샘플 텍스트 로드: {sample_file}")
    
    text = file_processor.extract_text(sample_file)
    if not text:
        print("❌ 텍스트 로드 실패")
        return
    
    processed_text = preprocess_text(text)
    print(f"✅ 텍스트 로드 성공 ({len(processed_text)}자)")
    
    # 사용 가능한 모드 결정
    available_modes = ['basic']
    if hybrid_analyzer.ai_analyzer.is_available():
        available_modes.append('ai')
    if hybrid_analyzer.local_ai_analyzer.is_available():
        available_modes.append('local_ai')
    
    print(f"\n3. 사용 가능한 분석 모드: {', '.join(available_modes)}")
    
    # 하이브리드 분석 수행
    print("\n4. 하이브리드 분석 수행 중...")
    try:
        result = hybrid_analyzer.analyze_comprehensive(processed_text, available_modes)
        
        print("✅ 하이브리드 분석 완료")
        print(f"   총 처리 시간: {result.total_processing_time:.1f}초")
        
        # 결과 비교
        print("\n5. 분석 결과 비교")
        comparison = result.performance_comparison
        
        print("   위반사항 개수:")
        for method, count in comparison['violation_counts'].items():
            if count > 0 or method == 'basic':
                print(f"      {method}: {count}건")
        
        print("   처리 시간:")
        for method, time_val in comparison['processing_times'].items():
            if time_val > 0:
                print(f"      {method}: {time_val:.1f}초")
        
        print("   신뢰도:")
        for method, score in comparison['confidence_scores'].items():
            if score > 0:
                print(f"      {method}: {score:.1%}")
        
        print("   비용:")
        for method, cost in comparison['costs'].items():
            if method in available_modes:
                if cost > 0:
                    print(f"      {method}: ${cost:.4f}")
                else:
                    print(f"      {method}: 무료")
        
        # 성능 분석
        print("\n6. 성능 분석")
        analysis = comparison['analysis']
        print(f"   최고 검출력: {analysis['best_coverage']}")
        print(f"   최고 속도: {analysis['fastest']}")
        print(f"   최고 신뢰도: {analysis['most_confident']}")
        print(f"   최고 비용효율: {analysis['most_cost_effective']}")
        
        if analysis['insights']:
            print("   주요 인사이트:")
            for insight in analysis['insights']:
                print(f"      • {insight}")
        
        # 추천사항
        print(f"\n7. 추천사항")
        print(f"   {result.recommendation}")
        
        # 우선순위별 모드 제안
        print("\n8. 상황별 최적 모드 제안")
        priorities = {
            'speed': '속도 우선',
            'accuracy': '정확도 우선', 
            'cost': '비용 절약',
            'privacy': '개인정보 보호',
            'balanced': '균형잡힌 사용'
        }
        
        for priority_key, priority_name in priorities.items():
            suggested_mode = hybrid_analyzer.suggest_optimal_mode(priority_key)
            print(f"   {priority_name}: {suggested_mode} 모드")
        
        # 상세 결과 (각 방법별)
        print("\n9. 상세 분석 결과")
        
        if result.basic_violations:
            print(f"\n   📊 기본 검사 결과 ({len(result.basic_violations)}건):")
            for i, violation in enumerate(result.basic_violations[:3], 1):
                print(f"      [{i}] {violation.text} ({violation.violation_type.value})")
        
        if result.ai_result and result.ai_result.violations:
            print(f"\n   🤖 Claude AI 결과 ({len(result.ai_result.violations)}건):")
            for i, violation in enumerate(result.ai_result.violations[:3], 1):
                print(f"      [{i}] {violation.get('text', 'N/A')} ({violation.get('type', 'N/A')})")
        
        if result.local_ai_result and result.local_ai_result.violations:
            print(f"\n   🏠 로컬 AI 결과 ({len(result.local_ai_result.violations)}건):")
            for i, violation in enumerate(result.local_ai_result.violations[:3], 1):
                print(f"      [{i}] {violation.get('text', 'N/A')} ({violation.get('type', 'N/A')})")
        
    except Exception as e:
        print(f"❌ 하이브리드 분석 중 오류: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # 성능 통계
    print("\n10. 성능 통계 요약")
    performance_summary = hybrid_analyzer.get_performance_summary()
    
    if performance_summary:
        for method, stats in performance_summary.items():
            print(f"   {method}:")
            print(f"      사용 횟수: {stats['usage_count']}회")
            print(f"      평균 시간: {stats['average_time']:.1f}초")
            print(f"      예상 정확도: {stats['accuracy_score']:.1%}")
    else:
        print("   아직 충분한 통계 데이터가 없습니다.")
    
    print("\n✅ 하이브리드 분석 시스템 테스트 완료!")
    
    print("\n🎯 하이브리드 시스템의 장점:")
    print("   • 상황에 맞는 최적 분석 방법 자동 선택")
    print("   • 여러 방법의 결과를 종합한 신뢰도 높은 분석")
    print("   • 비용과 성능의 균형잡힌 사용")
    print("   • 실시간 성능 비교 및 추천")

def test_mode_comparison():
    """분석 모드 비교 테스트"""
    print("=== 분석 모드 성능 비교 ===\n")
    
    hybrid_analyzer = HybridAnalyzer()
    
    modes_info = {
        'basic': {
            'name': '기본 키워드 검사',
            'pros': ['즉시 처리', '무료', '오프라인'],
            'cons': ['제한적 맥락 이해', '정규식 기반'],
            'best_for': '빠른 1차 스크리닝'
        },
        'ai': {
            'name': 'Claude AI 분석',
            'pros': ['높은 정확도', '맥락 이해', '상세한 분석'],
            'cons': ['비용 발생', '인터넷 필요', '처리 시간'],
            'best_for': '중요 문서 정밀 검토'
        },
        'local_ai': {
            'name': '로컬 AI 분석',
            'pros': ['개인정보 보호', '초기비용 후 무료', '커스터마이징'],
            'cons': ['설치 복잡', '높은 시스템 요구사항', '느린 처리'],
            'best_for': '보안이 중요한 내부 문서'
        }
    }
    
    for mode_key, info in modes_info.items():
        available = False
        if mode_key == 'basic':
            available = True
        elif mode_key == 'ai':
            available = hybrid_analyzer.ai_analyzer.is_available()
        elif mode_key == 'local_ai':
            available = hybrid_analyzer.local_ai_analyzer.is_available()
        
        status = "✅ 사용 가능" if available else "❌ 사용 불가"
        
        print(f"{info['name']} ({status})")
        print(f"   장점: {', '.join(info['pros'])}")
        print(f"   단점: {', '.join(info['cons'])}")
        print(f"   적합한 용도: {info['best_for']}")
        print()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--compare":
        test_mode_comparison()
    else:
        test_hybrid_analysis()