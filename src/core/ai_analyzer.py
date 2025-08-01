import os
import logging
import json
from typing import Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime
import time

import anthropic
from dotenv import load_dotenv

from .regulation_checker import Violation, ViolationType, SeverityLevel

# 환경 변수 로드
load_dotenv()

@dataclass
class AIAnalysisResult:
    """AI 분석 결과"""
    violations: List[Dict]
    contextual_analysis: str
    legal_risk_assessment: str
    improvement_suggestions: List[str]
    confidence_score: float
    processing_time: float
    cost_estimate: float

class AIAnalyzer:
    """Claude API를 사용한 AI 기반 법규 분석"""
    
    def __init__(self):
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        self.model = os.getenv('AI_MODEL', 'claude-3-sonnet-20240229')
        self.max_tokens = int(os.getenv('AI_MAX_TOKENS', '4000'))
        self.temperature = float(os.getenv('AI_TEMPERATURE', '0.3'))
        
        # 비용 관리
        self.monthly_budget = float(os.getenv('MONTHLY_BUDGET_LIMIT', '50.0'))
        self.daily_limit = int(os.getenv('DAILY_REQUEST_LIMIT', '100'))
        
        # 사용량 추적
        self.usage_file = 'ai_usage.json'
        self.load_usage_stats()
        
        if not self.api_key:
            logging.warning("ANTHROPIC_API_KEY가 설정되지 않았습니다. AI 분석을 사용하려면 .env 파일에 API 키를 설정하세요.")
            self.client = None
        else:
            self.client = anthropic.Anthropic(api_key=self.api_key)
    
    def load_usage_stats(self):
        """사용량 통계 로드"""
        try:
            if os.path.exists(self.usage_file):
                with open(self.usage_file, 'r') as f:
                    self.usage_stats = json.load(f)
            else:
                self.usage_stats = {
                    'daily_requests': {},
                    'monthly_cost': {},
                    'total_requests': 0,
                    'total_cost': 0.0
                }
        except Exception as e:
            logging.error(f"사용량 통계 로드 오류: {e}")
            self.usage_stats = {
                'daily_requests': {},
                'monthly_cost': {},
                'total_requests': 0,
                'total_cost': 0.0
            }
    
    def save_usage_stats(self):
        """사용량 통계 저장"""
        try:
            with open(self.usage_file, 'w') as f:
                json.dump(self.usage_stats, f, indent=2)
        except Exception as e:
            logging.error(f"사용량 통계 저장 오류: {e}")
    
    def check_usage_limits(self) -> bool:
        """사용량 제한 확인"""
        today = datetime.now().strftime('%Y-%m-%d')
        current_month = datetime.now().strftime('%Y-%m')
        
        # 일일 요청 제한 확인
        daily_requests = self.usage_stats['daily_requests'].get(today, 0)
        if daily_requests >= self.daily_limit:
            logging.warning(f"일일 요청 제한({self.daily_limit})에 도달했습니다.")
            return False
        
        # 월간 예산 제한 확인
        monthly_cost = self.usage_stats['monthly_cost'].get(current_month, 0.0)
        if monthly_cost >= self.monthly_budget:
            logging.warning(f"월간 예산 제한({self.monthly_budget}$)에 도달했습니다.")
            return False
        
        return True
    
    def update_usage_stats(self, cost: float):
        """사용량 통계 업데이트"""
        today = datetime.now().strftime('%Y-%m-%d')
        current_month = datetime.now().strftime('%Y-%m')
        
        # 일일 요청 수 증가
        if today not in self.usage_stats['daily_requests']:
            self.usage_stats['daily_requests'][today] = 0
        self.usage_stats['daily_requests'][today] += 1
        
        # 월간 비용 증가
        if current_month not in self.usage_stats['monthly_cost']:
            self.usage_stats['monthly_cost'][current_month] = 0.0
        self.usage_stats['monthly_cost'][current_month] += cost
        
        # 전체 통계 업데이트
        self.usage_stats['total_requests'] += 1
        self.usage_stats['total_cost'] += cost
        
        self.save_usage_stats()
    
    def get_cosmetics_law_prompt(self, text: str) -> str:
        """화장품법 전문가 프롬프트 생성"""
        return f"""당신은 화장품법 및 광고표시법 전문가입니다. 주어진 텍스트를 분석하여 법규 위반사항을 찾아주세요.

분석할 텍스트:
{text}

다음 관점에서 분석해주세요:

1. 화장품법 위반사항:
   - 의약품적 표현 (치료, 완치, 의학적 효과 등)
   - 효능 과장 (100% 효과, 즉시, 완벽한 등)
   - 안전성 허위표시 (부작용 없음, 100% 안전 등)

2. 표시·광고의 공정화에 관한 법률 위반사항:
   - 최상급 표현 (최고, 1위, 세계 최초 등)
   - 비교광고 위반 (타제품보다, 경쟁사보다 등)

3. 맥락적 분석:
   - 문구의 전후 맥락 고려
   - 소비자 오인 가능성
   - 법적 위험도 평가

응답 형식 (JSON):
{{
  "violations": [
    {{
      "text": "위반 문구",
      "type": "위반 유형",
      "severity": "높음/중간/낮음",
      "legal_basis": "관련 법령",
      "context": "문맥 설명",
      "consumer_impact": "소비자 오인 가능성",
      "suggestion": "개선 제안"
    }}
  ],
  "contextual_analysis": "전체적인 맥락 분석",
  "legal_risk_assessment": "법적 위험도 종합 평가",
  "improvement_suggestions": [
    "구체적인 개선 제안 1",
    "구체적인 개선 제안 2"
  ],
  "confidence_score": 0.95
}}

한국 법규를 기준으로 정확하고 실용적인 분석을 제공해주세요."""

    def analyze_text(self, text: str) -> Optional[AIAnalysisResult]:
        """텍스트 AI 분석"""
        if not self.client:
            logging.error("Claude API 클라이언트가 초기화되지 않았습니다.")
            return None
        
        if not self.check_usage_limits():
            logging.error("사용량 제한에 도달하여 AI 분석을 수행할 수 없습니다.")
            return None
        
        try:
            start_time = time.time()
            
            # Claude API 호출
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": self.get_cosmetics_law_prompt(text)
                    }
                ]
            )
            
            processing_time = time.time() - start_time
            
            # 응답 파싱
            response_text = message.content[0].text
            
            # JSON 추출 (마크다운 코드 블록 제거)
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.rfind("```")
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text.strip()
            
            try:
                analysis_data = json.loads(json_text)
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 대체 처리
                logging.warning("AI 응답의 JSON 파싱에 실패했습니다. 텍스트 분석으로 대체합니다.")
                analysis_data = self._parse_text_response(response_text)
            
            # 비용 계산 (대략적인 추정)
            input_tokens = len(text.split()) * 1.3  # 대략적인 토큰 수 추정
            output_tokens = len(response_text.split()) * 1.3
            cost_estimate = self._calculate_cost(input_tokens, output_tokens)
            
            # 사용량 통계 업데이트
            self.update_usage_stats(cost_estimate)
            
            # 결과 객체 생성
            result = AIAnalysisResult(
                violations=analysis_data.get('violations', []),
                contextual_analysis=analysis_data.get('contextual_analysis', ''),
                legal_risk_assessment=analysis_data.get('legal_risk_assessment', ''),
                improvement_suggestions=analysis_data.get('improvement_suggestions', []),
                confidence_score=analysis_data.get('confidence_score', 0.0),
                processing_time=processing_time,
                cost_estimate=cost_estimate
            )
            
            logging.info(f"AI 분석 완료: {len(result.violations)}건 위반사항 발견, 처리시간: {processing_time:.2f}초, 예상비용: ${cost_estimate:.4f}")
            
            return result
            
        except Exception as e:
            logging.error(f"AI 분석 중 오류 발생: {str(e)}")
            return None
    
    def _parse_text_response(self, response_text: str) -> Dict:
        """JSON 파싱 실패 시 텍스트 분석으로 대체"""
        return {
            'violations': [],
            'contextual_analysis': response_text[:500] + "..." if len(response_text) > 500 else response_text,
            'legal_risk_assessment': 'AI 응답 파싱 오류로 정확한 위험도 평가를 할 수 없습니다.',
            'improvement_suggestions': ['AI 분석 결과를 수동으로 검토해주세요.'],
            'confidence_score': 0.0
        }
    
    def _calculate_cost(self, input_tokens: float, output_tokens: float) -> float:
        """비용 계산 (Claude-3 Sonnet 기준)"""
        # Claude-3 Sonnet 가격 (2024년 기준)
        input_cost_per_1k = 0.003   # $0.003 per 1K input tokens
        output_cost_per_1k = 0.015  # $0.015 per 1K output tokens
        
        input_cost = (input_tokens / 1000) * input_cost_per_1k
        output_cost = (output_tokens / 1000) * output_cost_per_1k
        
        return input_cost + output_cost
    
    def get_usage_report(self) -> Dict:
        """사용량 리포트 생성"""
        today = datetime.now().strftime('%Y-%m-%d')
        current_month = datetime.now().strftime('%Y-%m')
        
        return {
            'today_requests': self.usage_stats['daily_requests'].get(today, 0),
            'daily_limit': self.daily_limit,
            'month_cost': self.usage_stats['monthly_cost'].get(current_month, 0.0),
            'monthly_budget': self.monthly_budget,
            'total_requests': self.usage_stats['total_requests'],
            'total_cost': self.usage_stats['total_cost'],
            'remaining_daily': self.daily_limit - self.usage_stats['daily_requests'].get(today, 0),
            'remaining_budget': self.monthly_budget - self.usage_stats['monthly_cost'].get(current_month, 0.0)
        }
    
    def is_available(self) -> bool:
        """AI 분석 사용 가능 여부 확인"""
        return self.client is not None and self.check_usage_limits()