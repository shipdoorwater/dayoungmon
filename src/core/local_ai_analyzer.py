import os
import logging
import json
import time
from typing import Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logging.warning("Ollama 라이브러리를 사용할 수 없습니다.")

import requests
from dotenv import load_dotenv

from .regulation_checker import Violation, ViolationType, SeverityLevel

# 환경 변수 로드
load_dotenv()

@dataclass
class LocalAIResult:
    """로컬 AI 분석 결과"""
    violations: List[Dict]
    contextual_analysis: str
    legal_risk_assessment: str
    improvement_suggestions: List[str]
    confidence_score: float
    processing_time: float
    model_name: str
    resource_usage: Dict

class LocalAIAnalyzer:
    """Ollama를 사용한 로컬 AI 기반 법규 분석"""
    
    def __init__(self):
        # 설정
        self.ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        self.model_name = os.getenv('LOCAL_AI_MODEL', 'llama3.2:3b')
        self.fallback_model = 'llama3.2:1b'  # 더 작은 모델로 대체
        
        # 사용량 추적
        self.usage_file = 'local_ai_usage.json'
        self.load_usage_stats()
        
        # 초기화
        self.available_models = []
        self.ollama_available = OLLAMA_AVAILABLE
        self.ollama_running = False
        
        if self.ollama_available:
            self._check_ollama_status()
    
    def load_usage_stats(self):
        """사용량 통계 로드"""
        try:
            if os.path.exists(self.usage_file):
                with open(self.usage_file, 'r') as f:
                    self.usage_stats = json.load(f)
            else:
                self.usage_stats = {
                    'total_requests': 0,
                    'total_processing_time': 0.0,
                    'model_usage': {},
                    'daily_usage': {}
                }
        except Exception as e:
            logging.error(f"로컬 AI 사용량 통계 로드 오류: {e}")
            self.usage_stats = {
                'total_requests': 0,
                'total_processing_time': 0.0,
                'model_usage': {},
                'daily_usage': {}
            }
    
    def save_usage_stats(self):
        """사용량 통계 저장"""
        try:
            with open(self.usage_file, 'w') as f:
                json.dump(self.usage_stats, f, indent=2)
        except Exception as e:
            logging.error(f"로컬 AI 사용량 통계 저장 오류: {e}")
    
    def _check_ollama_status(self):
        """Ollama 서비스 상태 확인"""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            if response.status_code == 200:
                self.ollama_running = True
                models_data = response.json()
                self.available_models = [model['name'] for model in models_data.get('models', [])]
                logging.info(f"Ollama 연결 성공. 사용 가능한 모델: {self.available_models}")
            else:
                self.ollama_running = False
                logging.warning("Ollama 서비스가 실행중이지만 API 응답이 올바르지 않습니다.")
        except requests.exceptions.ConnectionError:
            self.ollama_running = False
            logging.info("Ollama 서비스가 실행되지 않고 있습니다. 'ollama serve' 명령어로 시작하세요.")
        except requests.exceptions.RequestException as e:
            self.ollama_running = False
            logging.warning(f"Ollama 서비스에 연결할 수 없습니다: {e}")
        except Exception as e:
            self.ollama_running = False
            logging.error(f"Ollama 상태 확인 중 오류: {e}")
    
    def is_available(self) -> bool:
        """로컬 AI 사용 가능 여부 확인"""
        return self.ollama_available and self.ollama_running and len(self.available_models) > 0
    
    def get_best_model(self) -> Optional[str]:
        """사용 가능한 최적 모델 선택"""
        if not self.available_models:
            return None
        
        # 우선순위: 한국어 지원 모델 > 큰 모델 > 작은 모델
        preferred_models = [
            'solar-ko:10.7b',
            'kullm-polyglot:12.8b', 
            'llama3.2:3b',
            'llama3.2:1b',
            'llama3.1:8b',
            'llama3.1:7b',
            'gemma2:9b',
            'phi3:3.8b'
        ]
        
        for model in preferred_models:
            if model in self.available_models:
                return model
        
        # 우선순위 모델이 없으면 첫 번째 사용 가능한 모델 사용
        return self.available_models[0] if self.available_models else None
    
    def get_cosmetics_law_prompt(self, text: str) -> str:
        """화장품법 전문가 프롬프트 생성 (로컬 AI 최적화)"""
        return f"""당신은 화장품법과 광고표시법에 정통한 법무 전문가입니다. 
다음 텍스트를 분석하여 법규 위반사항을 찾아주세요.

분석할 텍스트:
{text}

다음 위반 유형을 확인해주세요:
1. 의약품적 표현: "치료", "완치", "의학적", "항균", "살균"
2. 효능 과장: "100% 효과", "즉시", "완벽한", "영구적"
3. 안전성 허위: "부작용 없음", "100% 안전", "알레르기 반응 없음"
4. 최상급 표현: "최고", "1위", "세계 최초", "유일한"
5. 비교광고 위반: "타제품보다", "경쟁사보다"

JSON 형식으로 응답해주세요:
{{
  "violations": [
    {{
      "text": "위반 문구",
      "type": "위반 유형",
      "severity": "높음/중간/낮음",
      "legal_basis": "관련 법령",
      "suggestion": "개선 제안"
    }}
  ],
  "contextual_analysis": "전체 맥락 분석",
  "legal_risk_assessment": "법적 위험도 평가",
  "improvement_suggestions": ["제안1", "제안2"],
  "confidence_score": 0.85
}}

한국 법규를 기준으로 정확히 분석해주세요."""
    
    def analyze_text(self, text: str) -> Optional[LocalAIResult]:
        """텍스트 로컬 AI 분석"""
        if not self.is_available():
            logging.error("로컬 AI 분석을 사용할 수 없습니다.")
            return None
        
        model_name = self.get_best_model()
        if not model_name:
            logging.error("사용 가능한 모델이 없습니다.")
            return None
        
        try:
            start_time = time.time()
            
            # Ollama API 호출
            if self.ollama_available:
                try:
                    response = ollama.chat(
                        model=model_name,
                        messages=[{
                            'role': 'user',
                            'content': self.get_cosmetics_law_prompt(text)
                        }],
                        options={
                            'temperature': 0.3,
                            'top_p': 0.9,
                            'num_predict': 2000
                        }
                    )
                    
                    response_text = response['message']['content']
                    
                except Exception as e:
                    logging.error(f"Ollama 호출 오류: {e}")
                    return None
            else:
                # Ollama가 없는 경우 더미 응답
                response_text = self._get_dummy_response(text)
            
            processing_time = time.time() - start_time
            
            # JSON 파싱
            try:
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
                
                analysis_data = json.loads(json_text)
            except json.JSONDecodeError:
                logging.warning("로컬 AI 응답의 JSON 파싱에 실패했습니다.")
                analysis_data = self._parse_text_response(response_text)
            
            # 리소스 사용량 계산 (추정)
            resource_usage = {
                'processing_time': processing_time,
                'model_size': self._estimate_model_size(model_name),
                'memory_usage': 'N/A',  # 실제 측정은 복잡함
                'cpu_usage': 'N/A'
            }
            
            # 사용량 통계 업데이트
            self._update_usage_stats(model_name, processing_time)
            
            # 결과 객체 생성
            result = LocalAIResult(
                violations=analysis_data.get('violations', []),
                contextual_analysis=analysis_data.get('contextual_analysis', ''),
                legal_risk_assessment=analysis_data.get('legal_risk_assessment', ''),
                improvement_suggestions=analysis_data.get('improvement_suggestions', []),
                confidence_score=analysis_data.get('confidence_score', 0.0),
                processing_time=processing_time,
                model_name=model_name,
                resource_usage=resource_usage
            )
            
            logging.info(f"로컬 AI 분석 완료: {len(result.violations)}건 위반사항, 모델: {model_name}, 시간: {processing_time:.1f}초")
            
            return result
            
        except Exception as e:
            logging.error(f"로컬 AI 분석 중 오류 발생: {str(e)}")
            return None
    
    def _get_dummy_response(self, text: str) -> str:
        """Ollama가 없을 때 더미 응답 생성"""
        return json.dumps({
            'violations': [
                {
                    'text': '로컬 AI 테스트',
                    'type': '기타',
                    'severity': '낮음',
                    'legal_basis': 'Ollama 설치 필요',
                    'suggestion': 'Ollama를 설치하고 적절한 모델을 다운로드하세요.'
                }
            ],
            'contextual_analysis': 'Ollama가 설치되지 않아 실제 분석을 수행할 수 없습니다.',
            'legal_risk_assessment': '로컬 AI 분석을 위해 Ollama 설치가 필요합니다.',
            'improvement_suggestions': [
                'Ollama를 설치하세요: https://ollama.ai/download',
                '한국어 지원 모델을 다운로드하세요: ollama pull solar-ko:10.7b'
            ],
            'confidence_score': 0.0
        })
    
    def _parse_text_response(self, response_text: str) -> Dict:
        """JSON 파싱 실패 시 텍스트 분석으로 대체"""
        return {
            'violations': [],
            'contextual_analysis': response_text[:300] + "..." if len(response_text) > 300 else response_text,
            'legal_risk_assessment': '로컬 AI 응답 파싱 오류로 정확한 분석을 할 수 없습니다.',
            'improvement_suggestions': ['로컬 AI 분석 결과를 수동으로 검토해주세요.'],
            'confidence_score': 0.0
        }
    
    def _estimate_model_size(self, model_name: str) -> str:
        """모델 크기 추정"""
        size_map = {
            'llama3.2:1b': '1.3GB',
            'llama3.2:3b': '2.0GB', 
            'llama3.1:7b': '4.7GB',
            'llama3.1:8b': '5.5GB',
            'solar-ko:10.7b': '7.5GB',
            'kullm-polyglot:12.8b': '8.9GB',
            'gemma2:9b': '6.2GB',
            'phi3:3.8b': '2.3GB'
        }
        return size_map.get(model_name, 'Unknown')
    
    def _update_usage_stats(self, model_name: str, processing_time: float):
        """사용량 통계 업데이트"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 전체 통계
        self.usage_stats['total_requests'] += 1
        self.usage_stats['total_processing_time'] += processing_time
        
        # 모델별 통계
        if model_name not in self.usage_stats['model_usage']:
            self.usage_stats['model_usage'][model_name] = {
                'requests': 0,
                'total_time': 0.0
            }
        self.usage_stats['model_usage'][model_name]['requests'] += 1
        self.usage_stats['model_usage'][model_name]['total_time'] += processing_time
        
        # 일별 통계
        if today not in self.usage_stats['daily_usage']:
            self.usage_stats['daily_usage'][today] = {
                'requests': 0,
                'total_time': 0.0
            }
        self.usage_stats['daily_usage'][today]['requests'] += 1
        self.usage_stats['daily_usage'][today]['total_time'] += processing_time
        
        self.save_usage_stats()
    
    def get_usage_report(self) -> Dict:
        """사용량 리포트 생성"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        today_usage = self.usage_stats['daily_usage'].get(today, {'requests': 0, 'total_time': 0.0})
        
        return {
            'today_requests': today_usage['requests'],
            'today_time': today_usage['total_time'],
            'total_requests': self.usage_stats['total_requests'],
            'total_time': self.usage_stats['total_processing_time'],
            'available_models': self.available_models,
            'current_model': self.get_best_model(),
            'ollama_running': self.ollama_running,
            'avg_processing_time': (
                self.usage_stats['total_processing_time'] / self.usage_stats['total_requests'] 
                if self.usage_stats['total_requests'] > 0 else 0
            )
        }
    
    def get_installation_guide(self) -> Dict:
        """설치 가이드 생성"""
        return {
            'ollama_installed': self.ollama_available,
            'ollama_running': self.ollama_running,
            'available_models': self.available_models,
            'installation_steps': [
                "1. Ollama 다운로드: https://ollama.ai/download",
                "2. macOS: .dmg 파일 실행 후 설치",
                "3. 터미널에서 'ollama serve' 실행",
                "4. 한국어 모델 다운로드: 'ollama pull solar-ko:10.7b'",
                "5. 애플리케이션 재시작"
            ],
            'recommended_models': [
                'solar-ko:10.7b (한국어 특화, 7.5GB)',
                'llama3.2:3b (일반용, 2.0GB)', 
                'llama3.2:1b (경량, 1.3GB)'
            ],
            'system_requirements': {
                'RAM': '최소 8GB, 권장 16GB+',
                'Storage': '모델당 1-8GB',
                'OS': 'macOS 10.15+, Windows 10+, Linux'
            }
        }