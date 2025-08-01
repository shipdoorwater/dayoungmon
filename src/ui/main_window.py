import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import logging
import datetime
from pathlib import Path

from ..core.file_processor import FileProcessor, preprocess_text
from ..core.regulation_checker import RegulationChecker
from ..core.ai_analyzer import AIAnalyzer
from ..core.local_ai_analyzer import LocalAIAnalyzer

class MainWindow:
    """메인 애플리케이션 윈도우"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("화장품 품질관리 법규 검토 툴")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # 프로세서 초기화
        self.file_processor = FileProcessor()
        self.regulation_checker = RegulationChecker()
        self.ai_analyzer = AIAnalyzer()
        self.local_ai_analyzer = LocalAIAnalyzer()
        
        # 현재 파일 정보
        self.current_file = None
        self.current_text = ""
        
        self._setup_ui()
        self._setup_logging()
    
    def _setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def _setup_ui(self):
        """UI 구성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 그리드 가중치 설정
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # 제목
        title_label = ttk.Label(
            main_frame, 
            text="화장품 품질관리 법규 검토 툴", 
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # 파일 선택 섹션
        self._create_file_section(main_frame)
        
        # 결과 표시 섹션
        self._create_results_section(main_frame)
        
        # 버튼 섹션
        self._create_button_section(main_frame)
    
    def _create_file_section(self, parent):
        """파일 선택 섹션 생성"""
        file_frame = ttk.LabelFrame(parent, text="파일 선택", padding="10")
        file_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(0, weight=1)
        
        # 파일 경로 표시
        self.file_path_var = tk.StringVar(value="파일을 선택해주세요...")
        file_path_label = ttk.Label(file_frame, textvariable=self.file_path_var)
        file_path_label.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # 파일 선택 버튼
        select_button = ttk.Button(
            file_frame, 
            text="파일 선택", 
            command=self._select_file
        )
        select_button.grid(row=0, column=1)
        
        # 지원 파일 형식 안내
        supported_formats = ", ".join(self.file_processor.get_supported_formats())
        format_label = ttk.Label(
            file_frame, 
            text=f"지원 형식: {supported_formats}",
            font=("Arial", 8),
            foreground="gray"
        )
        format_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
    
    def _create_results_section(self, parent):
        """결과 표시 섹션 생성"""
        results_frame = ttk.LabelFrame(parent, text="검토 결과", padding="10")
        results_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # 노트북 위젯 (탭)
        self.notebook = ttk.Notebook(results_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 요약 탭
        self._create_summary_tab()
        
        # 상세 탭
        self._create_details_tab()
        
        # 원본 텍스트 탭
        self._create_text_tab()
    
    def _create_summary_tab(self):
        """요약 탭 생성"""
        summary_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(summary_frame, text="요약")
        
        summary_frame.columnconfigure(0, weight=1)
        summary_frame.rowconfigure(1, weight=1)
        
        # 상태 표시
        self.status_var = tk.StringVar(value="파일을 선택하고 검토를 시작하세요.")
        status_label = ttk.Label(summary_frame, textvariable=self.status_var, font=("Arial", 12, "bold"))
        status_label.grid(row=0, column=0, pady=(0, 10))
        
        # 요약 정보 표시
        self.summary_text = scrolledtext.ScrolledText(
            summary_frame, 
            height=15, 
            font=("Arial", 10)
        )
        self.summary_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def _create_details_tab(self):
        """상세 탭 생성"""
        details_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(details_frame, text="상세 결과")
        
        details_frame.columnconfigure(0, weight=1)
        details_frame.rowconfigure(0, weight=1)
        
        # 트리뷰로 위반사항 표시
        columns = ("위반 문구", "유형", "심각도", "법적 근거")
        self.violations_tree = ttk.Treeview(details_frame, columns=columns, show="headings", height=15)
        
        # 컬럼 설정
        self.violations_tree.heading("위반 문구", text="위반 문구")
        self.violations_tree.heading("유형", text="위반 유형")
        self.violations_tree.heading("심각도", text="심각도")
        self.violations_tree.heading("법적 근거", text="법적 근거")
        
        self.violations_tree.column("위반 문구", width=150)
        self.violations_tree.column("유형", width=120)
        self.violations_tree.column("심각도", width=80)
        self.violations_tree.column("법적 근거", width=200)
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(details_frame, orient=tk.VERTICAL, command=self.violations_tree.yview)
        self.violations_tree.configure(yscrollcommand=scrollbar.set)
        
        self.violations_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 선택된 위반사항 상세 정보
        detail_info_frame = ttk.LabelFrame(details_frame, text="개선 제안", padding="5")
        detail_info_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        detail_info_frame.columnconfigure(0, weight=1)
        
        self.detail_info_text = tk.Text(detail_info_frame, height=4, font=("Arial", 9))
        self.detail_info_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # 트리뷰 선택 이벤트
        self.violations_tree.bind("<<TreeviewSelect>>", self._on_violation_select)
    
    def _create_text_tab(self):
        """원본 텍스트 탭 생성"""
        text_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(text_frame, text="원본 텍스트")
        
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        self.original_text = scrolledtext.ScrolledText(
            text_frame, 
            height=20, 
            font=("Arial", 10),
            state=tk.DISABLED
        )
        self.original_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def _create_button_section(self, parent):
        """버튼 섹션 생성"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=3, column=0, pady=(10, 0))
        
        # 분석 모드 선택
        mode_frame = ttk.LabelFrame(button_frame, text="분석 모드", padding="5")
        mode_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        self.analysis_mode = tk.StringVar(value="basic")
        
        basic_radio = ttk.Radiobutton(
            mode_frame, 
            text="빠른 검사 (키워드)", 
            variable=self.analysis_mode, 
            value="basic"
        )
        basic_radio.pack(anchor=tk.W)
        
        ai_radio = ttk.Radiobutton(
            mode_frame, 
            text="AI 정밀 분석 (Claude)", 
            variable=self.analysis_mode, 
            value="ai",
            state=tk.NORMAL if self.ai_analyzer.is_available() else tk.DISABLED
        )
        ai_radio.pack(anchor=tk.W)
        
        local_ai_radio = ttk.Radiobutton(
            mode_frame,
            text="로컬 AI 분석 (Ollama)",
            variable=self.analysis_mode,
            value="local_ai",
            state=tk.NORMAL if self.local_ai_analyzer.is_available() else tk.DISABLED
        )
        local_ai_radio.pack(anchor=tk.W)
        
        # AI 사용량 정보
        if self.ai_analyzer.is_available():
            usage_report = self.ai_analyzer.get_usage_report()
            usage_text = f"Claude API: {usage_report['today_requests']}/{usage_report['daily_limit']}회"
            usage_label = ttk.Label(mode_frame, text=usage_text, font=("Arial", 8), foreground="gray")
            usage_label.pack(anchor=tk.W)
        else:
            no_api_label = ttk.Label(mode_frame, text="Claude API 키 필요", font=("Arial", 8), foreground="red")
            no_api_label.pack(anchor=tk.W)
        
        # 로컬 AI 사용량 정보
        if self.local_ai_analyzer.is_available():
            local_usage = self.local_ai_analyzer.get_usage_report()
            local_text = f"로컬 AI: {local_usage['today_requests']}회 ({local_usage.get('current_model', 'N/A')})"
            local_label = ttk.Label(mode_frame, text=local_text, font=("Arial", 8), foreground="gray")
            local_label.pack(anchor=tk.W)
        else:
            no_local_label = ttk.Label(mode_frame, text="Ollama 설치 필요", font=("Arial", 8), foreground="red")
            no_local_label.pack(anchor=tk.W)
        
        # 검토 시작 버튼
        self.check_button = ttk.Button(
            button_frame, 
            text="검토 시작", 
            command=self._start_check,
            state=tk.DISABLED
        )
        self.check_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 결과 저장 버튼
        self.save_button = ttk.Button(
            button_frame, 
            text="결과 저장", 
            command=self._save_results,
            state=tk.DISABLED
        )
        self.save_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 진행 상황 표시
        self.progress = ttk.Progressbar(button_frame, mode='indeterminate')
        self.progress.pack(side=tk.LEFT, padx=(10, 0))
    
    def _select_file(self):
        """파일 선택"""
        file_types = [
            ("모든 지원 파일", "*.pdf;*.docx;*.pptx;*.txt;*.png;*.jpg;*.jpeg;*.bmp;*.tiff"),
            ("PDF 파일", "*.pdf"),
            ("Word 문서", "*.docx"),
            ("PowerPoint 파일", "*.pptx"),
            ("텍스트 파일", "*.txt"),
            ("이미지 파일", "*.png;*.jpg;*.jpeg;*.bmp;*.tiff"),
            ("모든 파일", "*.*")
        ]
        
        file_path = filedialog.askopenfilename(
            title="검토할 파일을 선택하세요",
            filetypes=file_types
        )
        
        if file_path:
            self.current_file = file_path
            self.file_path_var.set(Path(file_path).name)
            self.check_button.config(state=tk.NORMAL)
            self._clear_results()
    
    def _start_check(self):
        """검토 시작"""
        if not self.current_file:
            messagebox.showerror("오류", "파일을 먼저 선택해주세요.")
            return
        
        # UI 비활성화
        self.check_button.config(state=tk.DISABLED)
        self.progress.start()
        self.status_var.set("파일을 처리 중입니다...")
        
        # 백그라운드에서 처리
        thread = threading.Thread(target=self._process_file)
        thread.daemon = True
        thread.start()
    
    def _process_file(self):
        """파일 처리 (백그라운드)"""
        try:
            # 텍스트 추출
            self.root.after(0, lambda: self.status_var.set("텍스트를 추출하는 중..."))
            text = self.file_processor.extract_text(self.current_file)
            
            if not text:
                self.root.after(0, lambda: self._show_error("텍스트를 추출할 수 없습니다."))
                return
            
            # 텍스트 전처리
            self.current_text = preprocess_text(text)
            
            # 분석 모드에 따른 처리
            analysis_mode = self.analysis_mode.get()
            
            if analysis_mode == "ai" and self.ai_analyzer.is_available():
                # Claude AI 분석 모드
                self.root.after(0, lambda: self.status_var.set("Claude AI가 법규 위반사항을 분석하는 중... (30초-1분 소요)"))
                ai_result = self.ai_analyzer.analyze_text(self.current_text)
                
                if ai_result:
                    # AI 결과와 기본 검사 결과 비교
                    self.root.after(0, lambda: self.status_var.set("기본 검사와 결과를 비교하는 중..."))
                    basic_violations = self.regulation_checker.check_violations(self.current_text)
                    basic_report = self.regulation_checker.generate_report(basic_violations, self.current_text)
                    
                    # AI 결과 표시
                    self.root.after(0, lambda: self._display_ai_results(ai_result, basic_report, basic_violations))
                else:
                    # AI 분석 실패 시 기본 분석으로 대체
                    self.root.after(0, lambda: self.status_var.set("Claude AI 분석 실패. 기본 검사로 진행합니다..."))
                    violations = self.regulation_checker.check_violations(self.current_text)
                    report = self.regulation_checker.generate_report(violations, self.current_text)
                    self.root.after(0, lambda: self._display_results(report, violations))
            elif analysis_mode == "local_ai" and self.local_ai_analyzer.is_available():
                # 로컬 AI 분석 모드
                self.root.after(0, lambda: self.status_var.set("로컬 AI가 법규 위반사항을 분석하는 중... (1-3분 소요)"))
                local_ai_result = self.local_ai_analyzer.analyze_text(self.current_text)
                
                if local_ai_result:
                    # 로컬 AI 결과와 기본 검사 결과 비교
                    self.root.after(0, lambda: self.status_var.set("기본 검사와 결과를 비교하는 중..."))
                    basic_violations = self.regulation_checker.check_violations(self.current_text)
                    basic_report = self.regulation_checker.generate_report(basic_violations, self.current_text)
                    
                    # 로컬 AI 결과 표시
                    self.root.after(0, lambda: self._display_local_ai_results(local_ai_result, basic_report, basic_violations))
                else:
                    # 로컬 AI 분석 실패 시 기본 분석으로 대체
                    self.root.after(0, lambda: self.status_var.set("로컬 AI 분석 실패. 기본 검사로 진행합니다..."))
                    violations = self.regulation_checker.check_violations(self.current_text)
                    report = self.regulation_checker.generate_report(violations, self.current_text)
                    self.root.after(0, lambda: self._display_results(report, violations))
            else:
                # 기본 키워드 검사 모드
                self.root.after(0, lambda: self.status_var.set("법규 위반사항을 검사하는 중..."))
                violations = self.regulation_checker.check_violations(self.current_text)
                report = self.regulation_checker.generate_report(violations, self.current_text)
                self.root.after(0, lambda: self._display_results(report, violations))
            
        except Exception as e:
            logging.error(f"파일 처리 중 오류: {str(e)}")
            self.root.after(0, lambda: self._show_error(f"파일 처리 중 오류가 발생했습니다: {str(e)}"))
        finally:
            # UI 복원
            self.root.after(0, self._finish_processing)
    
    def _display_results(self, report, violations):
        """결과 표시"""
        # 요약 탭 업데이트
        self.status_var.set(report['summary'])
        
        summary_text = f"""
검토 결과: {report['status']}
위험도: {report['risk_level']}
총 위반사항: {report['total_violations']}건

심각도별 분류:
• 높음: {report.get('severity_summary', {}).get('high', 0)}건
• 중간: {report.get('severity_summary', {}).get('medium', 0)}건
• 낮음: {report.get('severity_summary', {}).get('low', 0)}건

위반 유형:
"""
        for vtype in report.get('violation_types', []):
            summary_text += f"• {vtype}\n"
        
        if report['total_violations'] > 0:
            summary_text += "\n권장사항:\n"
            summary_text += "• 위반 문구를 개선 제안에 따라 수정하세요\n"
            summary_text += "• 법적 근거를 참고하여 표현을 조정하세요\n"
            summary_text += "• 개인차가 있을 수 있음을 명시하세요\n"
        
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(1.0, summary_text)
        
        # 상세 탭 업데이트
        self._update_details_tab(violations)
        
        # 원본 텍스트 탭 업데이트
        self._update_text_tab()
        
        # 저장 버튼 활성화
        if report['total_violations'] > 0:
            self.save_button.config(state=tk.NORMAL)
    
    def _update_details_tab(self, violations):
        """상세 탭 업데이트"""
        # 기존 항목 삭제
        for item in self.violations_tree.get_children():
            self.violations_tree.delete(item)
        
        # 위반사항 추가
        for violation in violations:
            severity_color = {
                "높음": "red",
                "중간": "orange", 
                "낮음": "blue"
            }.get(violation.severity.value, "black")
            
            item = self.violations_tree.insert("", tk.END, values=(
                violation.text,
                violation.violation_type.value,
                violation.severity.value,
                violation.legal_basis
            ))
            
            # 심각도에 따른 색상 설정
            self.violations_tree.set(item, "심각도", violation.severity.value)
    
    def _update_text_tab(self):
        """원본 텍스트 탭 업데이트"""
        self.original_text.config(state=tk.NORMAL)
        self.original_text.delete(1.0, tk.END)
        self.original_text.insert(1.0, self.current_text)
        self.original_text.config(state=tk.DISABLED)
    
    def _display_ai_results(self, ai_result, basic_report, basic_violations):
        """AI 분석 결과 표시"""
        # 요약 탭 업데이트 (AI 특화)
        summary_text = f"""
🤖 AI 정밀 분석 결과

AI 분석:
• 발견된 위반사항: {len(ai_result.violations)}건
• 신뢰도: {ai_result.confidence_score:.1%}
• 처리 시간: {ai_result.processing_time:.1f}초
• 예상 비용: ${ai_result.cost_estimate:.4f}

기본 검사 비교:
• 기본 검사 위반사항: {basic_report['total_violations']}건
• 위험도: {basic_report['risk_level']}

AI 맥락 분석:
{ai_result.contextual_analysis}

법적 위험도 평가:
{ai_result.legal_risk_assessment}

개선 제안:
"""
        for i, suggestion in enumerate(ai_result.improvement_suggestions, 1):
            summary_text += f"{i}. {suggestion}\n"
        
        self.status_var.set(f"AI 분석 완료: {len(ai_result.violations)}건 위반사항 발견 (신뢰도: {ai_result.confidence_score:.1%})")
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(1.0, summary_text)
        
        # AI 위반사항을 기본 형식으로 변환하여 상세 탭에 표시
        converted_violations = []
        for ai_violation in ai_result.violations:
            # AI 결과를 기본 Violation 객체로 변환
            from ..core.regulation_checker import Violation, ViolationType, SeverityLevel
            
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
            
            violation_type = type_mapping.get(ai_violation.get('type', ''), ViolationType.EXAGGERATED_EFFECT)
            severity = severity_mapping.get(ai_violation.get('severity', '중간'), SeverityLevel.MEDIUM)
            
            violation = Violation(
                text=ai_violation.get('text', ''),
                violation_type=violation_type,
                severity=severity,
                legal_basis=ai_violation.get('legal_basis', ''),
                suggestion=ai_violation.get('suggestion', ''),
                position=0  # AI는 위치 정보가 없을 수 있음
            )
            converted_violations.append(violation)
        
        # 상세 탭 업데이트
        self._update_details_tab(converted_violations)
        
        # 원본 텍스트 탭 업데이트
        self._update_text_tab()
        
        # 저장 버튼 활성화
        if len(ai_result.violations) > 0:
            self.save_button.config(state=tk.NORMAL)
    
    def _display_local_ai_results(self, local_ai_result, basic_report, basic_violations):
        """로컬 AI 분석 결과 표시"""
        # 요약 탭 업데이트 (로컬 AI 특화)
        summary_text = f"""
🏠 로컬 AI 분석 결과

로컬 AI 분석:
• 발견된 위반사항: {len(local_ai_result.violations)}건
• 사용된 모델: {local_ai_result.model_name}
• 신뢰도: {local_ai_result.confidence_score:.1%}
• 처리 시간: {local_ai_result.processing_time:.1f}초
• 모델 크기: {local_ai_result.resource_usage.get('model_size', 'Unknown')}

기본 검사 비교:
• 기본 검사 위반사항: {basic_report['total_violations']}건
• 위험도: {basic_report['risk_level']}

AI 맥락 분석:
{local_ai_result.contextual_analysis}

법적 위험도 평가:
{local_ai_result.legal_risk_assessment}

개선 제안:
"""
        for i, suggestion in enumerate(local_ai_result.improvement_suggestions, 1):
            summary_text += f"{i}. {suggestion}\n"
        
        summary_text += f"\n💡 완전 오프라인 분석으로 개인정보 보호가 보장됩니다."
        
        self.status_var.set(f"로컬 AI 분석 완료: {len(local_ai_result.violations)}건 위반사항 발견 (모델: {local_ai_result.model_name})")
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(1.0, summary_text)
        
        # 로컬 AI 위반사항을 기본 형식으로 변환하여 상세 탭에 표시
        converted_violations = []
        for ai_violation in local_ai_result.violations:
            # AI 결과를 기본 Violation 객체로 변환
            from ..core.regulation_checker import Violation, ViolationType, SeverityLevel
            
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
            
            violation_type = type_mapping.get(ai_violation.get('type', ''), ViolationType.EXAGGERATED_EFFECT)
            severity = severity_mapping.get(ai_violation.get('severity', '중간'), SeverityLevel.MEDIUM)
            
            violation = Violation(
                text=ai_violation.get('text', ''),
                violation_type=violation_type,
                severity=severity,
                legal_basis=ai_violation.get('legal_basis', ''),
                suggestion=ai_violation.get('suggestion', ''),
                position=0  # 로컬 AI는 위치 정보가 없을 수 있음
            )
            converted_violations.append(violation)
        
        # 상세 탭 업데이트
        self._update_details_tab(converted_violations)
        
        # 원본 텍스트 탭 업데이트
        self._update_text_tab()
        
        # 저장 버튼 활성화
        if len(local_ai_result.violations) > 0:
            self.save_button.config(state=tk.NORMAL)
    
    def _on_violation_select(self, event):
        """위반사항 선택 시 상세 정보 표시"""
        selection = self.violations_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.violations_tree.item(item, "values")
        
        if len(values) >= 4:
            # 해당 위반사항의 개선 제안 찾기
            violation_text = values[0]
            violations = self.regulation_checker.check_violations(self.current_text)
            
            for violation in violations:
                if violation.text == violation_text:
                    suggestion_text = f"개선 제안:\n{violation.suggestion}\n\n"
                    suggestion_text += f"법적 근거:\n{violation.legal_basis}"
                    
                    self.detail_info_text.delete(1.0, tk.END)
                    self.detail_info_text.insert(1.0, suggestion_text)
                    break
    
    def _save_results(self):
        """결과 저장"""
        if not hasattr(self, 'current_text') or not self.current_text:
            messagebox.showerror("오류", "저장할 결과가 없습니다.")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="결과 저장",
            defaultextension=".txt",
            filetypes=[("텍스트 파일", "*.txt"), ("모든 파일", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("=== 화장품 품질관리 법규 검토 결과 ===\n\n")
                    f.write(f"검토 파일: {Path(self.current_file).name}\n")
                    f.write(f"검토 일시: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write("=== 요약 ===\n")
                    f.write(self.summary_text.get(1.0, tk.END))
                    f.write("\n=== 원본 텍스트 ===\n")
                    f.write(self.current_text)
                
                messagebox.showinfo("저장 완료", f"결과가 저장되었습니다.\n{file_path}")
            except Exception as e:
                messagebox.showerror("저장 오류", f"저장 중 오류가 발생했습니다: {str(e)}")
    
    def _clear_results(self):
        """결과 초기화"""
        self.status_var.set("파일을 선택하고 검토를 시작하세요.")
        self.summary_text.delete(1.0, tk.END)
        
        for item in self.violations_tree.get_children():
            self.violations_tree.delete(item)
        
        self.detail_info_text.delete(1.0, tk.END)
        
        self.original_text.config(state=tk.NORMAL)
        self.original_text.delete(1.0, tk.END)
        self.original_text.config(state=tk.DISABLED)
        
        self.save_button.config(state=tk.DISABLED)
    
    def _show_error(self, message):
        """오류 메시지 표시"""
        messagebox.showerror("오류", message)
        self.status_var.set("오류가 발생했습니다.")
    
    def _finish_processing(self):
        """처리 완료 후 UI 복원"""
        self.progress.stop()
        self.check_button.config(state=tk.NORMAL)
    
    def run(self):
        """애플리케이션 실행"""
        self.root.mainloop()

if __name__ == "__main__":
    app = MainWindow()
    app.run()