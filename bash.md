📝 Phase 1에서 사용한 Bash 명령어 정리

  1. 환경 설정 단계

  # Python 버전 확인
  python3 --version
  역할: 시스템에 설치된 Python 버전 확인이유: 프로젝트 요구사항(Python 3.9+) 충족 여부 확인

  # 가상환경 생성
  python3 -m venv cosmetics_checker_env
  역할: 독립적인 Python 가상환경 생성이유: 시스템 Python과 분리하여 라이브러리 의존성 충돌 방지

  # 가상환경 활성화 및 pip 업그레이드
  source cosmetics_checker_env/bin/activate && pip install --upgrade pip
  역할: 가상환경 활성화 후 최신 pip으로 업그레이드이유: 최신 패키지 관리 도구로 안정적인 라이브러리 설치 보장

  # 필요한 라이브러리 설치
  source cosmetics_checker_env/bin/activate && pip install -r requirements.txt
  역할: requirements.txt에 정의된 모든 의존성 라이브러리 설치이유: 프로젝트 실행에 필요한 모든 패키지를 한 번에 설치

  2. Tesseract OCR 설치 시도

  # Homebrew 설치 확인
  which brew
  역할: Homebrew 패키지 관리자 설치 여부 확인이유: macOS에서 Tesseract OCR 설치를 위한 준비 단계

  # Homebrew 설치 시도 (실패)
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  역할: Homebrew 패키지 관리자 설치이유: Tesseract OCR 설치를 위해 필요했지만 관리자 권한 부족으로 실패

  3. 프로젝트 구조 생성

  # 디렉터리 구조 생성
  mkdir -p src/{core,ui,data} tests docs assets
  역할: 프로젝트의 기본 디렉터리 구조를 한 번에 생성이유: 체계적인 코드 구조로 유지보수성과 확장성 확보

  4. 애플리케이션 테스트

  # GUI 애플리케이션 실행 테스트 (타임아웃)
  source cosmetics_checker_env/bin/activate && python main.py
  역할: GUI 애플리케이션 정상 실행 여부 확인이유: 사용자 인터페이스가 올바르게 작동하는지 검증 (정상적으로 실행되어 타임아웃됨)

  # 기본 기능 테스트 실행
  source cosmetics_checker_env/bin/activate && python test_basic.py
  역할: 핵심 기능들의 동작 상태를 커맨드라인에서 확인이유: GUI 없이도 파일 처리, 위반사항 검출, 리포트 생성 등 핵심 로직 검증

  5. 명령어 사용 패턴 분석

  가상환경 활성화 패턴:
  - 모든 Python 관련 명령어 앞에 source cosmetics_checker_env/bin/activate && 사용
  - 이유: 격리된 환경에서 일관된 실행 보장

  병렬 처리:
  - && 연산자로 명령어 연결하여 순차 실행
  - 이유: 이전 명령어 성공 시에만 다음 명령어 실행하여 안전성 확보

---

## 📝 Phase 2에서 사용한 Bash 명령어 정리

### 1. AI API 라이브러리 설치

```bash
# AI API 연동을 위한 라이브러리 설치
source cosmetics_checker_env/bin/activate && pip install anthropic python-dotenv
```
**역할**: AI 분석을 위한 Anthropic Claude API 클라이언트와 환경변수 관리 라이브러리 설치  
**이유**: Claude API를 통한 맥락적 법규 분석 기능 구현을 위해 필요

### 2. AI 기능 테스트

```bash
# API 키 없이 AI 기능 테스트
source cosmetics_checker_env/bin/activate && python test_ai_features.py --no-api
```
**역할**: API 키 설정 없이도 AI 모듈의 기본 동작 및 오류 처리 확인  
**이유**: 환경 설정 오류 시 적절한 안내 메시지와 대체 동작 검증

```bash
# 전체 AI 기능 테스트 (API 키 필요)
source cosmetics_checker_env/bin/activate && python test_ai_features.py
```
**역할**: Claude API를 실제로 호출하여 AI 분석 기능 전체 테스트  
**이유**: AI 분석, 비용 계산, 사용량 추적 등 모든 AI 관련 기능 검증

### 3. GUI 애플리케이션 테스트

```bash
# GUI 애플리케이션 AI 모드 포함 실행 확인
source cosmetics_checker_env/bin/activate && gtimeout 5 python main.py 2>/dev/null || python main.py &
```
**역할**: AI 분석 모드가 포함된 GUI 애플리케이션의 정상 실행 확인  
**이유**: 새로 추가된 AI 분석 모드 선택 UI와 기능들이 제대로 통합되었는지 검증

### 4. Phase 2 명령어 사용 패턴 분석

**라이브러리 추가 설치 패턴**:
- 기존 requirements.txt 업데이트 후 새로운 라이브러리만 개별 설치
- 이유: 전체 재설치 없이 필요한 패키지만 효율적으로 추가

**테스트 전략**:
- API 키 없는 상황과 있는 상황을 모두 테스트
- 이유: 실제 사용 환경에서 발생할 수 있는 다양한 시나리오 검증

**통합 테스트**:
- 기본 기능 테스트 + AI 기능 테스트 분리 실행
- 이유: 기능별로 독립적인 테스트로 문제 발생 지점 명확히 파악

### 5. Phase 2에서 추가된 새로운 도구들

- **anthropic**: Claude API 클라이언트 라이브러리
- **python-dotenv**: 환경변수 관리를 위한 .env 파일 지원
- **AI 사용량 추적**: JSON 파일 기반 로컬 사용량 통계 관리
- **비용 계산**: 토큰 사용량 기반 실시간 비용 추정

---

## 📝 Phase 3에서 사용한 Bash 명령어 정리

### 1. 로컬 AI 라이브러리 설치

```bash
# Ollama Python 클라이언트 및 HTTP 요청 라이브러리 설치
source cosmetics_checker_env/bin/activate && pip install ollama requests
```
**역할**: 로컬 AI 연동을 위한 Ollama Python 클라이언트와 HTTP 요청 라이브러리 설치  
**이유**: Ollama 서비스와 통신하여 로컬 AI 모델 실행 및 관리를 위해 필요

### 2. Ollama 설치 시도

```bash
# Linux용 Ollama 설치 시도 (macOS에서 실패)
curl -fsSL https://ollama.ai/install.sh | sh
```
**역할**: 자동 설치 스크립트를 통한 Ollama 설치 시도  
**이유**: macOS에서는 지원되지 않아 실패, 사용자가 직접 .dmg 파일로 설치 필요함을 확인

```bash
# 기존 Ollama 설치 확인
which ollama
```
**역할**: 시스템에 Ollama가 이미 설치되어 있는지 확인  
**이유**: 중복 설치를 방지하고 기존 설치 상태를 파악하기 위해

### 3. 로컬 AI 기능 테스트

```bash
# 로컬 AI 기능 및 Ollama 연결 상태 테스트
source cosmetics_checker_env/bin/activate && python test_local_ai.py
```
**역할**: Ollama 설치 상태 확인 및 로컬 AI 분석 기능 테스트  
**이유**: 로컬 AI 모듈의 동작 상태, 사용 가능한 모델, 설치 가이드 제공 기능 검증

```bash
# 로컬 AI 설치 가이드만 확인
source cosmetics_checker_env/bin/activate && python test_local_ai.py --guide
```
**역할**: Ollama 설치 가이드 및 권장 모델 정보만 표시  
**이유**: 사용자에게 설치 방법과 시스템 요구사항을 명확히 안내하기 위해

### 4. 하이브리드 분석 시스템 테스트

```bash
# 하이브리드 분석 시스템 종합 테스트
source cosmetics_checker_env/bin/activate && python test_hybrid_analysis.py
```
**역할**: 세 가지 분석 모드의 성능 비교 및 최적 모드 추천 시스템 테스트  
**이유**: 하이브리드 시스템의 병렬 처리, 성능 분석, 추천 알고리즘 기능 검증

```bash
# 분석 모드 비교 정보만 확인
source cosmetics_checker_env/bin/activate && python test_hybrid_analysis.py --compare
```
**역할**: 세 가지 분석 모드의 특징과 장단점 비교 표시  
**이용**: 사용자가 상황에 맞는 최적 모드를 선택할 수 있도록 정보 제공

### 5. Phase 3 명령어 사용 패턴 분석

**점진적 기능 확장**:
- 기존 라이브러리에 새로운 패키지만 추가 설치
- 이유: 기존 환경을 보존하면서 필요한 기능만 점진적으로 확장

**설치 실패 대응**:
- 자동 설치 실패 시 수동 설치 가이드 제공
- 이유: 플랫폼별 차이점을 고려한 유연한 설치 옵션 제공

**다층적 테스트 전략**:
- 개별 모듈 테스트 → 통합 시스템 테스트 → 성능 비교 테스트
- 이유: 단계별 검증으로 문제 발생 지점을 명확히 파악

**옵션 기반 테스트**:
- 명령행 인자로 다양한 테스트 시나리오 지원 (--guide, --compare)
- 이유: 사용자 목적에 따른 맞춤형 정보 제공

### 6. Phase 3에서 추가된 새로운 도구들

- **ollama**: 로컬 AI 모델 실행을 위한 Python 클라이언트
- **requests**: HTTP 통신을 위한 라이브러리 (Ollama API 호출)
- **ThreadPoolExecutor**: 병렬 처리를 위한 멀티스레딩 (하이브리드 분석)
- **JSON 기반 로컬 사용량 추적**: 로컬 AI 사용 통계 관리
- **성능 벤치마킹**: 실시간 처리 시간 및 정확도 비교
- **상황별 모드 추천 시스템**: 우선순위 기반 최적 분석 모드 제안

---

## 📝 Streamlit 웹 애플리케이션 실행

```bash
# Streamlit 애플리케이션 실행
source cosmetics_checker_env/bin/activate && streamlit run streamlit_app.py
```
**역할**: 웹 브라우저 기반 화장품 성분 검사 애플리케이션 실행  
**이유**: GUI 대신 웹 인터페이스를 통해 더 직관적이고 접근하기 쉬운 사용자 경험 제공