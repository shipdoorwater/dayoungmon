import logging
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

from .regulation_checker import RegulationChecker, Violation
from .ai_analyzer import AIAnalyzer, AIAnalysisResult
from .local_ai_analyzer import LocalAIAnalyzer, LocalAIResult

@dataclass
class HybridAnalysisResult:
    """하이브리드 분석 결과"""
    basic_violations: List[Violation]
    basic_report: Dict
    ai_result: Optional[AIAnalysisResult]
    local_ai_result: Optional[LocalAIResult]
    performance_comparison: Dict
    recommendation: str
    total_processing_time: float

class HybridAnalyzer:
    """여러 분석 방법을 통합한 하이브리드 분석 시스템"""
    
    def __init__(self):
        self.regulation_checker = RegulationChecker()
        self.ai_analyzer = AIAnalyzer()
        self.local_ai_analyzer = LocalAIAnalyzer()
        
        # 성능 통계
        self.performance_stats = {
            'basic': {'count': 0, 'total_time': 0.0, 'accuracy_score': 0.75},
            'ai': {'count': 0, 'total_time': 0.0, 'accuracy_score': 0.92},
            'local_ai': {'count': 0, 'total_time': 0.0, 'accuracy_score': 0.85}
        }
    
    def analyze_comprehensive(self, text: str, modes: List[str] = None) -> HybridAnalysisResult:
        """
        포괄적 분석 수행
        
        Args:
            text: 분석할 텍스트
            modes: 사용할 분석 모드 리스트 ['basic', 'ai', 'local_ai']
                  None이면 사용 가능한 모든 모드 사용
        """
        if modes is None:
            modes = ['basic']
            if self.ai_analyzer.is_available():
                modes.append('ai')
            if self.local_ai_analyzer.is_available():
                modes.append('local_ai')
        
        start_time = time.time()
        results = {}
        
        # 병렬 처리로 분석 수행
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_mode = {}
            
            for mode in modes:
                if mode == 'basic':
                    future = executor.submit(self._analyze_basic, text)
                elif mode == 'ai' and self.ai_analyzer.is_available():
                    future = executor.submit(self._analyze_ai, text)
                elif mode == 'local_ai' and self.local_ai_analyzer.is_available():
                    future = executor.submit(self._analyze_local_ai, text)
                else:
                    continue
                
                future_to_mode[future] = mode
            
            # 결과 수집
            for future in as_completed(future_to_mode):
                mode = future_to_mode[future]
                try:
                    results[mode] = future.result()
                except Exception as e:
                    logging.error(f"{mode} 분석 중 오류: {e}")
                    results[mode] = None
        
        total_time = time.time() - start_time
        
        # 기본 결과 (항상 존재)
        basic_result = results.get('basic')
        basic_violations = basic_result[0] if basic_result else []
        basic_report = basic_result[1] if basic_result else {}
        
        # AI 결과들
        ai_result = results.get('ai')
        local_ai_result = results.get('local_ai')
        
        # 성능 비교 수행
        performance_comparison = self._compare_performance(
            basic_violations, basic_report, ai_result, local_ai_result
        )
        
        # 추천사항 생성
        recommendation = self._generate_recommendation(
            modes, results, performance_comparison
        )
        
        return HybridAnalysisResult(
            basic_violations=basic_violations,
            basic_report=basic_report,
            ai_result=ai_result,
            local_ai_result=local_ai_result,
            performance_comparison=performance_comparison,
            recommendation=recommendation,
            total_processing_time=total_time
        )
    
    def _analyze_basic(self, text: str) -> Tuple[List[Violation], Dict]:
        """기본 키워드 분석"""
        start_time = time.time()
        violations = self.regulation_checker.check_violations(text)
        report = self.regulation_checker.generate_report(violations, text)
        
        processing_time = time.time() - start_time
        self.performance_stats['basic']['count'] += 1
        self.performance_stats['basic']['total_time'] += processing_time
        
        return violations, report
    
    def _analyze_ai(self, text: str) -> Optional[AIAnalysisResult]:
        """AI 분석"""
        start_time = time.time()
        result = self.ai_analyzer.analyze_text(text)
        
        processing_time = time.time() - start_time
        self.performance_stats['ai']['count'] += 1
        self.performance_stats['ai']['total_time'] += processing_time
        
        return result
    
    def _analyze_local_ai(self, text: str) -> Optional[LocalAIResult]:
        """로컬 AI 분석"""
        start_time = time.time()
        result = self.local_ai_analyzer.analyze_text(text)
        
        processing_time = time.time() - start_time
        self.performance_stats['local_ai']['count'] += 1
        self.performance_stats['local_ai']['total_time'] += processing_time
        
        return result
    
    def _compare_performance(self, basic_violations, basic_report, ai_result, local_ai_result) -> Dict:
        """성능 비교 분석"""
        comparison = {
            'violation_counts': {
                'basic': len(basic_violations),
                'ai': len(ai_result.violations) if ai_result else 0,
                'local_ai': len(local_ai_result.violations) if local_ai_result else 0
            },
            'processing_times': {
                'basic': 0.1,  # 기본 검사는 매우 빠름
                'ai': ai_result.processing_time if ai_result else 0,
                'local_ai': local_ai_result.processing_time if local_ai_result else 0
            },
            'confidence_scores': {
                'basic': 0.75,  # 기본 검사 고정 신뢰도
                'ai': ai_result.confidence_score if ai_result else 0,
                'local_ai': local_ai_result.confidence_score if local_ai_result else 0
            },
            'costs': {
                'basic': 0.0,  # 무료
                'ai': ai_result.cost_estimate if ai_result else 0,
                'local_ai': 0.0  # 초기 설정 후 무료
            }
        }
        
        # 상대적 성능 분석
        comparison['analysis'] = self._analyze_performance_differences(comparison)
        
        return comparison
    
    def _analyze_performance_differences(self, comparison: Dict) -> Dict:
        """성능 차이 분석"""
        analysis = {
            'best_coverage': 'basic',  # 가장 많은 위반사항 발견
            'fastest': 'basic',        # 가장 빠른 처리
            'most_confident': 'basic', # 가장 높은 신뢰도
            'most_cost_effective': 'basic',  # 가장 비용 효율적
            'insights': []
        }
        
        # 가장 많은 위반사항 발견한 방법
        violation_counts = comparison['violation_counts']
        max_violations = max(violation_counts.values())
        for method, count in violation_counts.items():
            if count == max_violations:
                analysis['best_coverage'] = method
                break
        
        # 가장 빠른 방법
        times = comparison['processing_times']
        min_time = min(t for t in times.values() if t > 0)
        for method, time_val in times.items():
            if time_val == min_time:
                analysis['fastest'] = method
                break
        
        # 가장 신뢰도 높은 방법
        confidence_scores = comparison['confidence_scores']
        max_confidence = max(confidence_scores.values())
        for method, score in confidence_scores.items():
            if score == max_confidence:
                analysis['most_confident'] = method
                break
        
        # 비용 효율성 (무료 > 저비용 > 고비용)
        costs = comparison['costs']
        free_methods = [m for m, c in costs.items() if c == 0.0]
        if free_methods:
            # 무료 방법 중 성능이 좋은 것
            best_free = max(free_methods, key=lambda m: confidence_scores.get(m, 0))
            analysis['most_cost_effective'] = best_free
        
        # 인사이트 생성
        insights = []
        
        if violation_counts['ai'] > violation_counts['basic']:
            insights.append("AI 분석이 기본 검사보다 더 많은 위반사항을 발견했습니다.")
        
        if violation_counts['local_ai'] > violation_counts['basic']:
            insights.append("로컬 AI가 기본 검사보다 더 정교한 분석을 제공했습니다.")
        
        if times.get('ai', 0) > 0 and times.get('local_ai', 0) > 0:
            if times['ai'] < times['local_ai']:
                insights.append("Claude API가 로컬 AI보다 빠른 처리 속도를 보였습니다.")
            else:
                insights.append("로컬 AI가 Claude API보다 빠른 처리를 완료했습니다.")
        
        if costs.get('ai', 0) > 0:
            cost_per_violation = costs['ai'] / max(violation_counts['ai'], 1)
            if cost_per_violation < 0.01:
                insights.append("AI 분석의 비용 대비 효과가 우수합니다.")
            else:
                insights.append("AI 분석 비용을 고려한 사용을 권장합니다.")
        
        analysis['insights'] = insights
        return analysis
    
    def _generate_recommendation(self, modes: List[str], results: Dict, comparison: Dict) -> str:
        """사용자 추천사항 생성"""
        available_modes = [mode for mode in modes if results.get(mode) is not None]
        
        if len(available_modes) == 1:
            return f"{available_modes[0]} 분석만 사용 가능합니다."
        
        analysis = comparison['analysis']
        recommendations = []
        
        # 상황별 추천
        if 'basic' in available_modes and 'ai' in available_modes:
            if comparison['violation_counts']['ai'] > comparison['violation_counts']['basic']:
                recommendations.append("중요한 문서는 AI 정밀 분석을 권장합니다.")
            else:
                recommendations.append("일반적인 검토는 빠른 기본 검사로 충분합니다.")
        
        if 'local_ai' in available_modes:
            recommendations.append("개인정보 보호가 중요한 경우 로컬 AI를 사용하세요.")
        
        if 'ai' in available_modes:
            ai_cost = comparison['costs'].get('ai', 0)
            if ai_cost > 0.01:
                recommendations.append("AI 분석 비용을 모니터링하며 사용하세요.")
        
        # 성능 기반 추천
        best_method = analysis['best_coverage']
        if best_method != 'basic':
            recommendations.append(f"가장 정확한 분석을 위해서는 {best_method} 모드를 사용하세요.")
        
        # 기본 추천사항
        if not recommendations:
            recommendations.append("모든 분석 방법이 유사한 결과를 보여줍니다. 상황에 맞게 선택하세요.")
        
        return " ".join(recommendations)
    
    def get_performance_summary(self) -> Dict:
        """성능 통계 요약"""
        summary = {}
        
        for mode, stats in self.performance_stats.items():
            if stats['count'] > 0:
                avg_time = stats['total_time'] / stats['count']
                summary[mode] = {
                    'usage_count': stats['count'],
                    'average_time': avg_time,
                    'accuracy_score': stats['accuracy_score'],
                    'total_time': stats['total_time']
                }
        
        return summary
    
    def suggest_optimal_mode(self, priority: str = 'balanced') -> str:
        """
        우선순위에 따른 최적 모드 제안
        
        Args:
            priority: 'speed', 'accuracy', 'cost', 'privacy', 'balanced'
        """
        available_modes = []
        
        if True:  # 기본 검사는 항상 사용 가능
            available_modes.append('basic')
        
        if self.ai_analyzer.is_available():
            available_modes.append('ai')
        
        if self.local_ai_analyzer.is_available():
            available_modes.append('local_ai')
        
        if priority == 'speed':
            return 'basic'
        elif priority == 'accuracy':
            if 'ai' in available_modes:
                return 'ai'
            elif 'local_ai' in available_modes:
                return 'local_ai'
            else:
                return 'basic'
        elif priority == 'cost':
            if 'local_ai' in available_modes:
                return 'local_ai'
            else:
                return 'basic'
        elif priority == 'privacy':
            if 'local_ai' in available_modes:
                return 'local_ai'
            else:
                return 'basic'
        else:  # balanced
            if len(available_modes) > 1:
                if 'ai' in available_modes and self.ai_analyzer.get_usage_report()['remaining_budget'] > 10:
                    return 'ai'
                elif 'local_ai' in available_modes:
                    return 'local_ai'
            return 'basic'