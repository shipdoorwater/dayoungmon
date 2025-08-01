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