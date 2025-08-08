"""
Streamlit 패턴 관리 페이지 모듈
"""

import streamlit as st
import pandas as pd
from src.data.pattern_manager import PatternManager
from src.core.types import ViolationType, SeverityLevel
from src.data.pattern_db import PatternRule
import json
from datetime import datetime

def show_pattern_management_page(pattern_manager: PatternManager):
    """패턴 관리 페이지 표시"""
    
    st.header("⚙️ 패턴 관리")
    st.markdown("---")
    
    # 탭 구성
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 패턴 목록", 
        "➕ 패턴 추가", 
        "📊 통계", 
        "🔄 백업/복원"
    ])
    
    with tab1:
        show_pattern_list(pattern_manager)
    
    with tab2:
        show_add_pattern(pattern_manager)
    
    with tab3:
        show_pattern_statistics(pattern_manager)
    
    with tab4:
        show_backup_restore(pattern_manager)

def show_pattern_list(pattern_manager: PatternManager):
    """패턴 목록 표시"""
    
    st.subheader("📋 패턴 목록")
    
    # 필터 옵션
    col1, col2, col3 = st.columns(3)
    
    with col1:
        violation_type_filter = st.selectbox(
            "위반 유형 필터:",
            ["전체"] + [vt.value for vt in ViolationType],
            key="list_violation_type"
        )
    
    with col2:
        severity_filter = st.selectbox(
            "심각도 필터:",
            ["전체"] + [sl.value for sl in SeverityLevel],
            key="list_severity"
        )
    
    with col3:
        status_filter = st.selectbox(
            "상태 필터:",
            ["전체", "활성", "비활성"],
            key="list_status"
        )
    
    # 검색
    search_term = st.text_input(
        "🔍 패턴 검색:",
        placeholder="패턴, 설명, 카테고리로 검색...",
        key="pattern_search"
    )
    
    try:
        # 패턴 조회
        if search_term:
            patterns = pattern_manager.search_similar_patterns(search_term)
        else:
            patterns = pattern_manager.db.get_all_patterns()
        
        # 필터 적용
        filtered_patterns = apply_filters(patterns, violation_type_filter, severity_filter, status_filter)
        
        if not filtered_patterns:
            st.info("조건에 맞는 패턴이 없습니다.")
            return
        
        # 패턴 데이터프레임 생성
        pattern_data = []
        for pattern in filtered_patterns:
            pattern_data.append({
                "ID": pattern.id,
                "패턴": pattern.pattern[:50] + "..." if len(pattern.pattern) > 50 else pattern.pattern,
                "위반 유형": pattern.violation_type.value,
                "심각도": pattern.severity.value,
                "상태": "활성" if pattern.is_active else "비활성",
                "카테고리": pattern.category,
                "설명": pattern.description[:30] + "..." if len(pattern.description) > 30 else pattern.description,
                "생성일": pattern.created_at[:10] if pattern.created_at else "",
                "수정일": pattern.updated_at[:10] if pattern.updated_at else ""
            })
        
        df = pd.DataFrame(pattern_data)
        
        # 패턴 표시 및 선택
        st.markdown(f"**총 {len(filtered_patterns)}개 패턴**")
        
        # 데이터프레임 표시
        selected_indices = st.data_editor(
            df,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "ID": st.column_config.NumberColumn("ID", width="small"),
                "패턴": st.column_config.TextColumn("패턴", width="large"),
                "위반 유형": st.column_config.TextColumn("위반 유형", width="medium"),
                "심각도": st.column_config.TextColumn("심각도", width="small"),
                "상태": st.column_config.TextColumn("상태", width="small"),
                "카테고리": st.column_config.TextColumn("카테고리", width="medium"),
                "설명": st.column_config.TextColumn("설명", width="large"),
                "생성일": st.column_config.TextColumn("생성일", width="small"),
                "수정일": st.column_config.TextColumn("수정일", width="small")
            },
            disabled=["ID", "생성일", "수정일"]
        )
        
        # 패턴 관리 버튼들
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🔄 새로고침", use_container_width=True):
                st.rerun()
        
        with col2:
            selected_pattern_id = st.number_input(
                "패턴 ID 입력:",
                min_value=1,
                value=1,
                key="selected_pattern_id"
            )
        
        with col3:
            if st.button("✏️ 편집", use_container_width=True):
                edit_pattern(pattern_manager, selected_pattern_id)
        
        with col4:
            if st.button("🗑️ 삭제", use_container_width=True, type="secondary"):
                delete_pattern(pattern_manager, selected_pattern_id)
        
        # 일괄 작업
        st.markdown("---")
        st.subheader("🔧 일괄 작업")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📤 모든 패턴 활성화", use_container_width=True):
                activate_all_patterns(pattern_manager, filtered_patterns)
        
        with col2:
            if st.button("📥 모든 패턴 비활성화", use_container_width=True):
                deactivate_all_patterns(pattern_manager, filtered_patterns)
                
    except Exception as e:
        st.error(f"패턴 목록 로드 실패: {e}")

def apply_filters(patterns, violation_type_filter, severity_filter, status_filter):
    """필터 적용"""
    filtered = patterns
    
    # 위반 유형 필터
    if violation_type_filter != "전체":
        violation_type = next(vt for vt in ViolationType if vt.value == violation_type_filter)
        filtered = [p for p in filtered if p.violation_type == violation_type]
    
    # 심각도 필터
    if severity_filter != "전체":
        severity = next(sl for sl in SeverityLevel if sl.value == severity_filter)
        filtered = [p for p in filtered if p.severity == severity]
    
    # 상태 필터
    if status_filter == "활성":
        filtered = [p for p in filtered if p.is_active]
    elif status_filter == "비활성":
        filtered = [p for p in filtered if not p.is_active]
    
    return filtered

def show_add_pattern(pattern_manager: PatternManager):
    """패턴 추가 페이지"""
    
    st.subheader("➕ 새 패턴 추가")
    
    with st.form("add_pattern_form"):
        # 패턴 입력
        pattern = st.text_area(
            "패턴 (정규식) *:",
            placeholder="예: (치료|완치|의학적\\s*효과)",
            help="정규식 패턴을 입력하세요. 백슬래시는 두 번 입력해야 합니다."
        )
        
        # 위반 유형
        violation_type = st.selectbox(
            "위반 유형 *:",
            [vt.value for vt in ViolationType]
        )
        
        # 심각도
        severity = st.selectbox(
            "심각도 *:",
            [sl.value for sl in SeverityLevel]
        )
        
        # 법적 근거
        legal_basis = st.text_area(
            "법적 근거 *:",
            placeholder="화장품법 제2조(정의), 약사법 제85조"
        )
        
        # 개선 제안
        suggestion = st.text_area(
            "개선 제안 *:",
            placeholder="화장품의 기능적 효과로 표현을 변경하세요"
        )
        
        # 설명
        description = st.text_input(
            "설명:",
            placeholder="패턴에 대한 간단한 설명"
        )
        
        # 카테고리
        category = st.text_input(
            "카테고리:",
            placeholder="사용자정의",
            value="사용자정의"
        )
        
        # 패턴 검증 버튼
        col1, col2 = st.columns(2)
        with col1:
            validate_clicked = st.form_submit_button("🔍 패턴 검증", use_container_width=True)
        
        with col2:
            submit_clicked = st.form_submit_button("✅ 패턴 추가", type="primary", use_container_width=True)
        
        # 패턴 검증
        if validate_clicked and pattern:
            result = pattern_manager.validate_pattern(pattern)
            if result['valid']:
                st.success(f"✅ {result['message']}")
            else:
                st.error(f"❌ {result['message']}")
        
        # 패턴 추가
        if submit_clicked:
            if not all([pattern, violation_type, severity, legal_basis, suggestion]):
                st.error("❌ 필수 항목을 모두 입력하세요.")
            else:
                try:
                    # 패턴 검증
                    validation_result = pattern_manager.validate_pattern(pattern)
                    if not validation_result['valid']:
                        st.error(f"❌ 패턴 오류: {validation_result['message']}")
                        return
                    
                    # 위반 유형과 심각도 변환
                    vt = next(vt for vt in ViolationType if vt.value == violation_type)
                    sl = next(sl for sl in SeverityLevel if sl.value == severity)
                    
                    # 패턴 추가
                    pattern_id = pattern_manager.add_custom_pattern(
                        pattern=pattern,
                        violation_type=vt,
                        severity=sl,
                        legal_basis=legal_basis,
                        suggestion=suggestion,
                        description=description,
                        category=category
                    )
                    
                    st.success(f"✅ 패턴이 추가되었습니다! (ID: {pattern_id})")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ 패턴 추가 실패: {e}")

def edit_pattern(pattern_manager: PatternManager, pattern_id: int):
    """패턴 편집"""
    try:
        pattern = pattern_manager.db.get_pattern(pattern_id)
        if not pattern:
            st.error(f"❌ ID {pattern_id}인 패턴을 찾을 수 없습니다.")
            return
        
        st.info(f"📝 패턴 편집 (ID: {pattern_id})")
        
        with st.form(f"edit_pattern_{pattern_id}"):
            # 기존 값으로 초기화
            new_pattern = st.text_area("패턴:", value=pattern.pattern)
            new_violation_type = st.selectbox(
                "위반 유형:",
                [vt.value for vt in ViolationType],
                index=list(ViolationType).index(pattern.violation_type)
            )
            new_severity = st.selectbox(
                "심각도:",
                [sl.value for sl in SeverityLevel],
                index=list(SeverityLevel).index(pattern.severity)
            )
            new_legal_basis = st.text_area("법적 근거:", value=pattern.legal_basis)
            new_suggestion = st.text_area("개선 제안:", value=pattern.suggestion)
            new_description = st.text_input("설명:", value=pattern.description)
            new_category = st.text_input("카테고리:", value=pattern.category)
            new_is_active = st.checkbox("활성화", value=pattern.is_active)
            
            if st.form_submit_button("💾 저장", type="primary"):
                # 패턴 업데이트
                pattern.pattern = new_pattern
                pattern.violation_type = next(vt for vt in ViolationType if vt.value == new_violation_type)
                pattern.severity = next(sl for sl in SeverityLevel if sl.value == new_severity)
                pattern.legal_basis = new_legal_basis
                pattern.suggestion = new_suggestion
                pattern.description = new_description
                pattern.category = new_category
                pattern.is_active = new_is_active
                
                if pattern_manager.db.update_pattern(pattern):
                    st.success("✅ 패턴이 수정되었습니다!")
                    st.rerun()
                else:
                    st.error("❌ 패턴 수정 실패")
                    
    except Exception as e:
        st.error(f"❌ 패턴 편집 실패: {e}")

def delete_pattern(pattern_manager: PatternManager, pattern_id: int):
    """패턴 삭제"""
    try:
        pattern = pattern_manager.db.get_pattern(pattern_id)
        if not pattern:
            st.error(f"❌ ID {pattern_id}인 패턴을 찾을 수 없습니다.")
            return
        
        if st.confirm(f"패턴 '{pattern.pattern[:50]}...'을 삭제하시겠습니까?"):
            if pattern_manager.db.delete_pattern(pattern_id):
                st.success("✅ 패턴이 삭제되었습니다!")
                st.rerun()
            else:
                st.error("❌ 패턴 삭제 실패")
                
    except Exception as e:
        st.error(f"❌ 패턴 삭제 실패: {e}")

def activate_all_patterns(pattern_manager: PatternManager, patterns):
    """모든 패턴 활성화"""
    try:
        count = 0
        for pattern in patterns:
            if not pattern.is_active:
                pattern.is_active = True
                if pattern_manager.db.update_pattern(pattern):
                    count += 1
        
        st.success(f"✅ {count}개 패턴이 활성화되었습니다!")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ 일괄 활성화 실패: {e}")

def deactivate_all_patterns(pattern_manager: PatternManager, patterns):
    """모든 패턴 비활성화"""
    try:
        count = 0
        for pattern in patterns:
            if pattern.is_active:
                pattern.is_active = False
                if pattern_manager.db.update_pattern(pattern):
                    count += 1
        
        st.success(f"✅ {count}개 패턴이 비활성화되었습니다!")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ 일괄 비활성화 실패: {e}")

def show_pattern_statistics(pattern_manager: PatternManager):
    """패턴 통계 표시"""
    
    st.subheader("📊 패턴 통계")
    
    try:
        stats = pattern_manager.get_pattern_statistics()
        
        # 전체 통계
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("전체 패턴", f"{stats['total_patterns']}개")
        
        with col2:
            st.metric("활성 패턴", f"{stats['active_patterns']}개")
        
        with col3:
            st.metric("비활성 패턴", f"{stats['inactive_patterns']}개")
        
        # 위반 유형별 분포
        st.markdown("---")
        st.subheader("📈 위반 유형별 분포")
        
        if stats['type_distribution']:
            type_data = []
            for vtype, count in stats['type_distribution'].items():
                type_data.append({"위반 유형": vtype, "패턴 수": count})
            
            df_type = pd.DataFrame(type_data)
            st.bar_chart(df_type.set_index("위반 유형"))
            st.dataframe(df_type, use_container_width=True)
        else:
            st.info("위반 유형별 데이터가 없습니다.")
        
        # 심각도별 분포
        st.markdown("---")
        st.subheader("⚠️ 심각도별 분포")
        
        if stats['severity_distribution']:
            severity_data = []
            for severity, count in stats['severity_distribution'].items():
                severity_data.append({"심각도": severity, "패턴 수": count})
            
            df_severity = pd.DataFrame(severity_data)
            st.bar_chart(df_severity.set_index("심각도"))
            st.dataframe(df_severity, use_container_width=True)
        else:
            st.info("심각도별 데이터가 없습니다.")
            
    except Exception as e:
        st.error(f"❌ 통계 로드 실패: {e}")

def show_backup_restore(pattern_manager: PatternManager):
    """백업/복원 페이지"""
    
    st.subheader("🔄 백업 및 복원")
    
    # 백업
    st.markdown("### 📤 패턴 백업")
    
    if st.button("💾 패턴 백업 생성", use_container_width=True, type="primary"):
        try:
            backup_filename = f"patterns_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            if pattern_manager.export_patterns(backup_filename):
                st.success(f"✅ 백업 파일이 생성되었습니다: {backup_filename}")
                
                # 백업 파일 다운로드
                with open(backup_filename, 'r', encoding='utf-8') as f:
                    backup_content = f.read()
                
                st.download_button(
                    label="📥 백업 파일 다운로드",
                    data=backup_content,
                    file_name=backup_filename,
                    mime="application/json"
                )
            else:
                st.error("❌ 백업 실패")
                
        except Exception as e:
            st.error(f"❌ 백업 실패: {e}")
    
    # 복원
    st.markdown("---")
    st.markdown("### 📥 패턴 복원")
    
    uploaded_file = st.file_uploader(
        "복원할 백업 파일을 선택하세요",
        type=['json'],
        help="JSON 형식의 패턴 백업 파일을 업로드하세요"
    )
    
    if uploaded_file:
        clear_existing = st.checkbox(
            "기존 패턴 삭제",
            help="체크하면 기존 모든 패턴을 삭제하고 백업 파일의 패턴으로 교체합니다"
        )
        
        if st.button("🔄 복원 실행", use_container_width=True, type="secondary"):
            try:
                # 임시 파일로 저장
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp_file:
                    content = uploaded_file.getvalue().decode('utf-8')
                    tmp_file.write(content)
                    tmp_file_path = tmp_file.name
                
                if pattern_manager.import_patterns(tmp_file_path, clear_existing):
                    if clear_existing:
                        st.success("✅ 기존 패턴을 삭제하고 백업에서 복원했습니다!")
                    else:
                        st.success("✅ 백업 패턴을 기존 패턴에 추가했습니다!")
                    st.rerun()
                else:
                    st.error("❌ 복원 실패")
                
                # 임시 파일 삭제
                import os
                os.unlink(tmp_file_path)
                
            except Exception as e:
                st.error(f"❌ 복원 실패: {e}")
    
    # 초기화
    st.markdown("---")
    st.markdown("### ⚠️ 위험한 작업")
    
    if st.button("🔄 기본 패턴으로 초기화", use_container_width=True, type="secondary"):
        if st.confirm("모든 패턴을 삭제하고 기본 패턴으로 초기화하시겠습니까?"):
            try:
                # 모든 패턴 삭제
                patterns = pattern_manager.db.get_all_patterns()
                for pattern in patterns:
                    pattern_manager.db.delete_pattern(pattern.id)
                
                # 기본 패턴 마이그레이션
                if pattern_manager.migrate_hardcoded_patterns():
                    st.success("✅ 기본 패턴으로 초기화되었습니다!")
                    st.rerun()
                else:
                    st.error("❌ 초기화 실패")
                    
            except Exception as e:
                st.error(f"❌ 초기화 실패: {e}")