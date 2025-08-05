#!/usr/bin/env python3
"""
화장품 품질관리 법규 검토 툴 - Streamlit 웹 인터페이스
"""

import streamlit as st
import sys
import os
from pathlib import Path
import datetime
import tempfile
import io

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 기존 모듈 import
from src.core.file_processor import FileProcessor, preprocess_text
from src.core.regulation_checker import RegulationChecker
from src.core.ai_analyzer import AIAnalyzer
from src.core.local_ai_analyzer import LocalAIAnalyzer

# 페이지 설정
st.set_page_config(
    page_title="화장품 품질관리 법규 검토 툴",
    page_icon="🧴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'current_text' not in st.session_state:
    st.session_state.current_text = ""
if 'current_file_name' not in st.session_state:
    st.session_state.current_file_name = ""

@st.cache_resource
def init_processors():
    """프로세서 초기화 (캐시로 한 번만 실행)"""
    file_processor = FileProcessor()
    regulation_checker = RegulationChecker()
    ai_analyzer = AIAnalyzer()
    local_ai_analyzer = LocalAIAnalyzer()
    
    return file_processor, regulation_checker, ai_analyzer, local_ai_analyzer

def main():
    """메인 앱"""
    # 제목
    st.title("🧴 화장품 품질관리 법규 검토 툴")
    st.markdown("---")
    
    # 프로세서 초기화
    file_processor, regulation_checker, ai_analyzer, local_ai_analyzer = init_processors()
    
    # 사이드바 - 분석 모드 선택
    with st.sidebar:
        st.header("🔧 분석 설정")
        
        # 분석 모드 선택
        analysis_mode = st.radio(
            "분석 모드 선택:",
            ["빠른 검사 (키워드)", "AI 정밀 분석 (Claude)", "로컬 AI 분석 (Ollama)"],
            help="분석 방식을 선택하세요"
        )
        
        # API 상태 표시
        st.subheader("📊 시스템 상태")
        
        # Claude API 상태
        if ai_analyzer.is_available():
            usage_report = ai_analyzer.get_usage_report()
            st.success(f"✅ Claude API: {usage_report['today_requests']}/{usage_report['daily_limit']}회")
        else:
            st.error("❌ Claude API 키 필요")
            
        # 로컬 AI 상태  
        if local_ai_analyzer.is_available():
            local_usage = local_ai_analyzer.get_usage_report()
            st.success(f"✅ 로컬 AI: {local_usage['today_requests']}회")
        else:
            st.warning("⚠️ Ollama 설치 필요")
            
        # 지원 파일 형식
        st.subheader("📁 지원 형식")
        supported_formats = file_processor.get_supported_formats()
        for fmt in supported_formats:
            st.text(f"• {fmt}")
    
    # 메인 영역
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.header("📤 파일 업로드")
        
        # 파일 업로드
        uploaded_file = st.file_uploader(
            "검토할 파일을 선택하세요",
            type=['pdf', 'docx', 'pptx', 'txt', 'png', 'jpg', 'jpeg', 'bmp', 'tiff'],
            help="PDF, Word, PowerPoint, 텍스트, 이미지 파일을 지원합니다"
        )
        
        if uploaded_file:
            st.success(f"✅ {uploaded_file.name} 업로드 완료")
            st.session_state.current_file_name = uploaded_file.name
            
            # 분석 시작 버튼
            if st.button("🔍 분석 시작", type="primary", use_container_width=True):
                analyze_file(uploaded_file, analysis_mode, file_processor, regulation_checker, ai_analyzer, local_ai_analyzer)
    
    with col2:
        st.header("📋 분석 결과")
        
        if st.session_state.analysis_result:
            display_results()
        else:
            st.info("📁 파일을 업로드하고 분석을 시작하세요")

def analyze_file(uploaded_file, analysis_mode, file_processor, regulation_checker, ai_analyzer, local_ai_analyzer):
    """파일 분석 실행"""
    
    # 임시 파일로 저장
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_file_path = tmp_file.name
    
    try:
        # 진행상황 표시
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 1. 텍스트 추출
        status_text.text("📄 텍스트 추출 중...")
        progress_bar.progress(20)
        
        extracted_text = file_processor.extract_text(tmp_file_path)
        if not extracted_text:
            st.error("❌ 텍스트를 추출할 수 없습니다.")
            return
            
        processed_text = preprocess_text(extracted_text)
        st.session_state.current_text = processed_text
        
        # 2. 분석 모드에 따른 처리
        progress_bar.progress(40)
        
        if analysis_mode == "빠른 검사 (키워드)":
            status_text.text("🔍 키워드 기반 검사 중...")
            progress_bar.progress(60)
            
            violations = regulation_checker.check_violations(processed_text)
            report = regulation_checker.generate_report(violations, processed_text)
            
            st.session_state.analysis_result = {
                'type': 'basic',
                'report': report,
                'violations': violations
            }
            
        elif analysis_mode == "AI 정밀 분석 (Claude)" and ai_analyzer.is_available():
            status_text.text("🤖 Claude AI 분석 중... (30초-1분 소요)")
            progress_bar.progress(60)
            
            ai_result = ai_analyzer.analyze_text(processed_text)
            if ai_result:
                # AI 결과와 기본 검사 비교
                status_text.text("📊 결과 비교 중...")
                progress_bar.progress(80)
                
                basic_violations = regulation_checker.check_violations(processed_text)
                basic_report = regulation_checker.generate_report(basic_violations, processed_text)
                
                st.session_state.analysis_result = {
                    'type': 'ai',
                    'ai_result': ai_result,
                    'basic_report': basic_report,
                    'basic_violations': basic_violations
                }
            else:
                st.error("❌ AI 분석 실패. 기본 검사로 대체합니다.")
                violations = regulation_checker.check_violations(processed_text)
                report = regulation_checker.generate_report(violations, processed_text)
                st.session_state.analysis_result = {
                    'type': 'basic',
                    'report': report,
                    'violations': violations
                }
                
        elif analysis_mode == "로컬 AI 분석 (Ollama)" and local_ai_analyzer.is_available():
            status_text.text("🏠 로컬 AI 분석 중... (1-3분 소요)")
            progress_bar.progress(60)
            
            local_ai_result = local_ai_analyzer.analyze_text(processed_text)
            if local_ai_result:
                # 로컬 AI 결과와 기본 검사 비교
                status_text.text("📊 결과 비교 중...")
                progress_bar.progress(80)
                
                basic_violations = regulation_checker.check_violations(processed_text)
                basic_report = regulation_checker.generate_report(basic_violations, processed_text)
                
                st.session_state.analysis_result = {
                    'type': 'local_ai',
                    'local_ai_result': local_ai_result,
                    'basic_report': basic_report,
                    'basic_violations': basic_violations
                }
            else:
                st.error("❌ 로컬 AI 분석 실패. 기본 검사로 대체합니다.")
                violations = regulation_checker.check_violations(processed_text)
                report = regulation_checker.generate_report(violations, processed_text)
                st.session_state.analysis_result = {
                    'type': 'basic',
                    'report': report,
                    'violations': violations
                }
        else:
            # 기본 검사 모드 또는 AI 사용 불가
            status_text.text("🔍 기본 키워드 검사 중...")
            progress_bar.progress(60)
            
            violations = regulation_checker.check_violations(processed_text)
            report = regulation_checker.generate_report(violations, processed_text)
            
            st.session_state.analysis_result = {
                'type': 'basic',
                'report': report,
                'violations': violations
            }
        
        # 완료
        progress_bar.progress(100)
        status_text.text("✅ 분석 완료!")
        
        # 잠시 후 진행바 제거
        import time
        time.sleep(1)
        progress_bar.empty()
        status_text.empty()
        
        st.success("🎉 분석이 완료되었습니다!")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ 분석 중 오류가 발생했습니다: {str(e)}")
    finally:
        # 임시 파일 삭제
        os.unlink(tmp_file_path)

def display_results():
    """결과 표시"""
    result = st.session_state.analysis_result
    
    if not result:
        return
    
    # 탭으로 결과 구성
    tab1, tab2, tab3 = st.tabs(["📊 요약", "🔍 상세 결과", "📄 원본 텍스트"])
    
    with tab1:
        display_summary(result)
    
    with tab2:
        display_details(result)
        
    with tab3:
        display_original_text()

def display_summary(result):
    """요약 탭 표시"""
    result_type = result['type']
    
    if result_type == 'basic':
        report = result['report']
        
        # 상태 표시
        if report['total_violations'] == 0:
            st.success(f"✅ {report['summary']}")
        elif report['risk_level'] == '높음':
            st.error(f"🚨 {report['summary']}")
        else:
            st.warning(f"⚠️ {report['summary']}")
        
        # 메트릭 표시
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("총 위반사항", f"{report['total_violations']}건")
        with col2:
            st.metric("위험도", report['risk_level'])
        with col3:
            severity_summary = report.get('severity_summary', {})
            st.metric("높은 심각도", f"{severity_summary.get('high', 0)}건")
        
        # 위반 유형
        if report.get('violation_types'):
            st.subheader("🏷️ 위반 유형")
            for vtype in report['violation_types']:
                st.write(f"• {vtype}")
        
        # 권장사항
        if report['total_violations'] > 0:
            st.subheader("💡 권장사항")
            st.write("• 위반 문구를 개선 제안에 따라 수정하세요")
            st.write("• 법적 근거를 참고하여 표현을 조정하세요") 
            st.write("• 개인차가 있을 수 있음을 명시하세요")
            
    elif result_type == 'ai':
        ai_result = result['ai_result']
        basic_report = result['basic_report']
        
        st.success("🤖 AI 정밀 분석 완료")
        
        # AI 분석 메트릭
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("AI 발견 위반", f"{len(ai_result.violations)}건")
        with col2:
            st.metric("신뢰도", f"{ai_result.confidence_score:.1%}")
        with col3:
            st.metric("처리 시간", f"{ai_result.processing_time:.1f}초")
        with col4:
            st.metric("예상 비용", f"${ai_result.cost_estimate:.4f}")
        
        # AI 분석 내용
        st.subheader("🧠 AI 맥락 분석")
        st.write(ai_result.contextual_analysis)
        
        st.subheader("⚖️ 법적 위험도 평가")
        st.write(ai_result.legal_risk_assessment)
        
        st.subheader("💡 AI 개선 제안")
        for i, suggestion in enumerate(ai_result.improvement_suggestions, 1):
            st.write(f"{i}. {suggestion}")
    
    elif result_type == 'local_ai':
        local_ai_result = result['local_ai_result']
        basic_report = result['basic_report']
        
        st.success("🏠 로컬 AI 분석 완료")
        
        # 로컬 AI 분석 메트릭
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("AI 발견 위반", f"{len(local_ai_result.violations)}건")
        with col2:
            st.metric("사용 모델", local_ai_result.model_name)
        with col3:
            st.metric("신뢰도", f"{local_ai_result.confidence_score:.1%}")
        with col4:
            st.metric("처리 시간", f"{local_ai_result.processing_time:.1f}초")
        
        # 로컬 AI 분석 내용
        st.subheader("🧠 AI 맥락 분석")
        st.write(local_ai_result.contextual_analysis)
        
        st.subheader("⚖️ 법적 위험도 평가") 
        st.write(local_ai_result.legal_risk_assessment)
        
        st.subheader("💡 AI 개선 제안")
        for i, suggestion in enumerate(local_ai_result.improvement_suggestions, 1):
            st.write(f"{i}. {suggestion}")
        
        st.info("💡 완전 오프라인 분석으로 개인정보 보호가 보장됩니다.")

def display_details(result):
    """상세 결과 탭 표시"""
    result_type = result['type']
    
    if result_type == 'basic':
        violations = result['violations']
    elif result_type == 'ai':
        # AI 결과를 기본 형식으로 변환
        violations = convert_ai_violations_to_basic(result['ai_result'].violations)
    elif result_type == 'local_ai':
        # 로컬 AI 결과를 기본 형식으로 변환
        violations = convert_ai_violations_to_basic(result['local_ai_result'].violations)
    else:
        violations = []
    
    if not violations:
        st.success("✅ 발견된 위반사항이 없습니다.")
        return
    
    st.subheader(f"🔍 위반사항 상세 ({len(violations)}건)")
    
    for i, violation in enumerate(violations, 1):
        with st.expander(f"위반 {i}: {violation.text[:50]}..."):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**위반 문구:** {violation.text}")
                st.write(f"**위반 유형:** {violation.violation_type.value}")
                st.write(f"**법적 근거:** {violation.legal_basis}")
                st.write(f"**개선 제안:** {violation.suggestion}")
            
            with col2:
                # 심각도에 따른 색상 표시
                if violation.severity.value == "높음":
                    st.error(f"⚠️ 심각도: {violation.severity.value}")
                elif violation.severity.value == "중간":
                    st.warning(f"⚠️ 심각도: {violation.severity.value}")
                else:
                    st.info(f"ℹ️ 심각도: {violation.severity.value}")

def convert_ai_violations_to_basic(ai_violations):
    """AI 위반사항을 기본 형식으로 변환"""
    from src.core.regulation_checker import Violation, ViolationType, SeverityLevel
    
    converted_violations = []
    
    # 위반 유형 매핑
    type_mapping = {
        "의약품적 표현": ViolationType.MEDICAL_CLAIM,
        "효능 과장": ViolationType.EXAGGERATED_EFFECT, 
        "안전성 허위": ViolationType.SAFETY_MISREPRESENTATION,
        "최상급 표현": ViolationType.SUPERLATIVE_EXPRESSION,
        "비교광고 위반": ViolationType.COMPARATIVE_AD_VIOLATION
    }
    
    # 심각도 매핑
    severity_mapping = {
        "높음": SeverityLevel.HIGH,
        "중간": SeverityLevel.MEDIUM,
        "낮음": SeverityLevel.LOW
    }
    
    for ai_violation in ai_violations:
        violation_type = type_mapping.get(ai_violation.get('type', ''), ViolationType.EXAGGERATED_EFFECT)
        severity = severity_mapping.get(ai_violation.get('severity', '중간'), SeverityLevel.MEDIUM)
        
        violation = Violation(
            text=ai_violation.get('text', ''),
            violation_type=violation_type,
            severity=severity,
            legal_basis=ai_violation.get('legal_basis', ''),
            suggestion=ai_violation.get('suggestion', ''),
            position=0
        )
        converted_violations.append(violation)
    
    return converted_violations

def display_original_text():
    """원본 텍스트 탭 표시"""
    if st.session_state.current_text:
        st.subheader("📄 추출된 텍스트")
        st.text_area(
            "원본 텍스트:",
            st.session_state.current_text,
            height=400,
            disabled=True
        )
        
        # 다운로드 버튼
        st.download_button(
            label="📥 텍스트 다운로드",
            data=st.session_state.current_text,
            file_name=f"{st.session_state.current_file_name}_extracted.txt",
            mime="text/plain"
        )
        
        # 결과 보고서 다운로드
        if st.session_state.analysis_result:
            report_content = generate_report_content()
            st.download_button(
                label="📊 분석 보고서 다운로드",
                data=report_content,
                file_name=f"{st.session_state.current_file_name}_analysis_report.txt",
                mime="text/plain"
            )
    else:
        st.info("📁 파일을 업로드하고 분석을 실행하면 텍스트가 표시됩니다.")

def generate_report_content():
    """분석 보고서 내용 생성"""
    result = st.session_state.analysis_result
    
    report_lines = [
        "=== 화장품 품질관리 법규 검토 결과 ===",
        "",
        f"검토 파일: {st.session_state.current_file_name}",
        f"검토 일시: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"분석 유형: {result['type']}",
        "",
        "=== 요약 ===",
    ]
    
    if result['type'] == 'basic':
        report = result['report']
        report_lines.extend([
            f"검토 결과: {report['status']}",
            f"위험도: {report['risk_level']}",
            f"총 위반사항: {report['total_violations']}건",
            "",
            "위반 유형:",
        ])
        for vtype in report.get('violation_types', []):
            report_lines.append(f"• {vtype}")
            
    elif result['type'] in ['ai', 'local_ai']:
        ai_key = 'ai_result' if result['type'] == 'ai' else 'local_ai_result'
        ai_result = result[ai_key]
        report_lines.extend([
            f"AI 분석 결과: {len(ai_result.violations)}건 위반사항 발견",
            f"신뢰도: {ai_result.confidence_score:.1%}",
            f"처리 시간: {ai_result.processing_time:.1f}초",
            "",
            "AI 맥락 분석:",
            ai_result.contextual_analysis,
            "",
            "법적 위험도 평가:",
            ai_result.legal_risk_assessment,
            "",
            "개선 제안:",
        ])
        for i, suggestion in enumerate(ai_result.improvement_suggestions, 1):
            report_lines.append(f"{i}. {suggestion}")
    
    report_lines.extend([
        "",
        "=== 원본 텍스트 ===",
        st.session_state.current_text
    ])
    
    return "\n".join(report_lines)

if __name__ == "__main__":
    main()