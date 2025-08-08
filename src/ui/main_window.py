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
from ..data.pattern_db import PatternDatabase, PatternRule
from ..core.types import ViolationType, SeverityLevel

class MainWindow:
    """메인 애플리케이션 윈도우"""
    
    def __init__(self):
        print("MainWindow 초기화 시작...")
        
        # macOS 호환성 향상
        self.root = tk.Tk()
        self.root.title("화장품 품질관리 법규 검토 툴")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # macOS 특화 설정
        try:
            # macOS에서 창이 숨겨지는 문제 방지
            self.root.withdraw()  # 일시적으로 숨기기
            self.root.update_idletasks()  # UI 업데이트 강제
            self.root.deiconify()  # 다시 표시
            
            # 포커스 강제 설정
            self.root.focus_force()
            self.root.tkraise()
            
            print(f"Tkinter 버전: {tk.TkVersion}")
            print(f"윈도우 상태: {self.root.state()}")
            print("Tkinter 윈도우 생성 완료")
        except Exception as e:
            print(f"macOS 호환성 설정 중 오류: {e}")
            print("기본 설정으로 진행합니다.")
        
        # 현재 파일 정보
        self.current_file = None
        self.current_text = ""
        
        # UI 먼저 설정
        try:
            self._setup_ui()
            print("UI 구성 완료")
        except Exception as e:
            print(f"UI 구성 중 오류: {e}")
            
        self._setup_logging()
        
        # 프로세서 초기화 (UI 구성 후)
        try:
            print("프로세서들 초기화 중...")
            self.file_processor = FileProcessor()
            print("FileProcessor 초기화 완료")
            
            self.regulation_checker = RegulationChecker()
            print("RegulationChecker 초기화 완료")
            
            self.ai_analyzer = AIAnalyzer()
            print("AIAnalyzer 초기화 완료")
            
            self.local_ai_analyzer = LocalAIAnalyzer()
            print("LocalAIAnalyzer 초기화 완료")
            
            self.pattern_db = PatternDatabase()
            print("PatternDatabase 초기화 완료")
            
            # 패턴 관리 탭의 초기 데이터 로딩
            if hasattr(self, 'pattern_tree'):
                self._refresh_patterns()
            
        except Exception as e:
            print(f"프로세서 초기화 중 오류: {e}")
            # 오류가 있어도 기본 UI는 표시되도록 함
    
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
        try:
            supported_formats = ", ".join(self.file_processor.get_supported_formats())
        except:
            supported_formats = "PDF, DOCX, PPTX, TXT, PNG, JPG 등"
        
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
        
        # 패턴 관리 탭
        self._create_pattern_management_tab()
    
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
        
        # AI 분석 옵션들을 안전하게 처리
        try:
            ai_available = hasattr(self, 'ai_analyzer') and self.ai_analyzer.is_available()
        except:
            ai_available = False
            
        try:
            local_ai_available = hasattr(self, 'local_ai_analyzer') and self.local_ai_analyzer.is_available()
        except:
            local_ai_available = False
        
        ai_radio = ttk.Radiobutton(
            mode_frame, 
            text="AI 정밀 분석 (Claude)", 
            variable=self.analysis_mode, 
            value="ai",
            state=tk.NORMAL if ai_available else tk.DISABLED
        )
        ai_radio.pack(anchor=tk.W)
        
        local_ai_radio = ttk.Radiobutton(
            mode_frame,
            text="로컬 AI 분석 (Ollama)",
            variable=self.analysis_mode,
            value="local_ai",
            state=tk.NORMAL if local_ai_available else tk.DISABLED
        )
        local_ai_radio.pack(anchor=tk.W)
        
        # AI 사용량 정보
        try:
            if ai_available:
                usage_report = self.ai_analyzer.get_usage_report()
                usage_text = f"Claude API: {usage_report['today_requests']}/{usage_report['daily_limit']}회"
                usage_label = ttk.Label(mode_frame, text=usage_text, font=("Arial", 8), foreground="gray")
                usage_label.pack(anchor=tk.W)
            else:
                no_api_label = ttk.Label(mode_frame, text="Claude API 키 필요", font=("Arial", 8), foreground="red")
                no_api_label.pack(anchor=tk.W)
        except:
            no_api_label = ttk.Label(mode_frame, text="Claude API 설정 확인 필요", font=("Arial", 8), foreground="red")
            no_api_label.pack(anchor=tk.W)
        
        # 로컬 AI 사용량 정보
        try:
            if local_ai_available:
                local_usage = self.local_ai_analyzer.get_usage_report()
                local_text = f"로컬 AI: {local_usage['today_requests']}회 ({local_usage.get('current_model', 'N/A')})"
                local_label = ttk.Label(mode_frame, text=local_text, font=("Arial", 8), foreground="gray")
                local_label.pack(anchor=tk.W)
            else:
                no_local_label = ttk.Label(mode_frame, text="Ollama 설치 필요", font=("Arial", 8), foreground="red")
                no_local_label.pack(anchor=tk.W)
        except:
            no_local_label = ttk.Label(mode_frame, text="로컬 AI 설정 확인 필요", font=("Arial", 8), foreground="red")
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
    
    def _create_pattern_management_tab(self):
        """패턴 관리 탭 생성"""
        pattern_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(pattern_frame, text="패턴 관리")
        
        pattern_frame.columnconfigure(0, weight=1)
        pattern_frame.rowconfigure(1, weight=1)
        
        # 상단 버튼 프레임
        button_frame = ttk.Frame(pattern_frame)
        button_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        button_frame.columnconfigure(4, weight=1)
        
        # 패턴 관리 버튼들
        add_pattern_btn = ttk.Button(button_frame, text="패턴 추가", command=self._add_pattern)
        add_pattern_btn.grid(row=0, column=0, padx=(0, 5))
        
        edit_pattern_btn = ttk.Button(button_frame, text="패턴 수정", command=self._edit_pattern)
        edit_pattern_btn.grid(row=0, column=1, padx=5)
        
        delete_pattern_btn = ttk.Button(button_frame, text="패턴 삭제", command=self._delete_pattern)
        delete_pattern_btn.grid(row=0, column=2, padx=5)
        
        refresh_pattern_btn = ttk.Button(button_frame, text="새로고침", command=self._refresh_patterns)
        refresh_pattern_btn.grid(row=0, column=3, padx=5)
        
        # 검색 프레임
        search_frame = ttk.Frame(button_frame)
        search_frame.grid(row=0, column=4, sticky=(tk.E))
        
        ttk.Label(search_frame, text="검색:").pack(side=tk.LEFT, padx=(10, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=(0, 5))
        search_entry.bind('<KeyRelease>', self._on_pattern_search)
        
        search_btn = ttk.Button(search_frame, text="검색", command=self._search_patterns)
        search_btn.pack(side=tk.LEFT)
        
        # 패턴 목록 트리뷰
        pattern_columns = ("ID", "패턴", "위반유형", "심각도", "활성화", "카테고리", "설명")
        self.pattern_tree = ttk.Treeview(pattern_frame, columns=pattern_columns, show="headings", height=20)
        
        # 컬럼 설정
        self.pattern_tree.heading("ID", text="ID")
        self.pattern_tree.heading("패턴", text="패턴")
        self.pattern_tree.heading("위반유형", text="위반유형")
        self.pattern_tree.heading("심각도", text="심각도")
        self.pattern_tree.heading("활성화", text="활성화")
        self.pattern_tree.heading("카테고리", text="카테고리")
        self.pattern_tree.heading("설명", text="설명")
        
        self.pattern_tree.column("ID", width=50)
        self.pattern_tree.column("패턴", width=200)
        self.pattern_tree.column("위반유형", width=120)
        self.pattern_tree.column("심각도", width=80)
        self.pattern_tree.column("활성화", width=80)
        self.pattern_tree.column("카테고리", width=100)
        self.pattern_tree.column("설명", width=150)
        
        # 스크롤바
        pattern_scrollbar = ttk.Scrollbar(pattern_frame, orient=tk.VERTICAL, command=self.pattern_tree.yview)
        self.pattern_tree.configure(yscrollcommand=pattern_scrollbar.set)
        
        self.pattern_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        pattern_scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        
        # 패턴 상세 정보 프레임
        detail_frame = ttk.LabelFrame(pattern_frame, text="패턴 상세 정보", padding="5")
        detail_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        detail_frame.columnconfigure(0, weight=1)
        
        self.pattern_detail_text = scrolledtext.ScrolledText(detail_frame, height=6, font=("Arial", 9))
        self.pattern_detail_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # 통계 정보 프레임
        stats_frame = ttk.LabelFrame(pattern_frame, text="통계", padding="5")
        stats_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.stats_label = ttk.Label(stats_frame, text="패턴 로딩 중...", font=("Arial", 9))
        self.stats_label.grid(row=0, column=0, sticky=tk.W)
        
        # 트리뷰 선택 이벤트
        self.pattern_tree.bind("<<TreeviewSelect>>", self._on_pattern_select)
        self.pattern_tree.bind("<Double-1>", self._edit_pattern)
        
        # 초기화 완료 후 패턴 로딩 (패턴 데이터베이스가 준비된 후)
    
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
    
    def _add_pattern(self):
        """새 패턴 추가"""
        self._show_pattern_dialog()
    
    def _edit_pattern(self, event=None):
        """선택된 패턴 수정"""
        selection = self.pattern_tree.selection()
        if not selection:
            messagebox.showwarning("알림", "수정할 패턴을 선택해주세요.")
            return
        
        item = selection[0]
        pattern_id = int(self.pattern_tree.item(item, "values")[0])
        pattern_rule = self.pattern_db.get_pattern(pattern_id)
        
        if pattern_rule:
            self._show_pattern_dialog(pattern_rule)
    
    def _delete_pattern(self):
        """선택된 패턴 삭제"""
        selection = self.pattern_tree.selection()
        if not selection:
            messagebox.showwarning("알림", "삭제할 패턴을 선택해주세요.")
            return
        
        item = selection[0]
        pattern_id = int(self.pattern_tree.item(item, "values")[0])
        pattern_text = self.pattern_tree.item(item, "values")[1]
        
        if messagebox.askyesno("확인", f"패턴 '{pattern_text}'을(를) 삭제하시겠습니까?"):
            if self.pattern_db.delete_pattern(pattern_id):
                messagebox.showinfo("완료", "패턴이 삭제되었습니다.")
                self._refresh_patterns()
            else:
                messagebox.showerror("오류", "패턴 삭제에 실패했습니다.")
    
    def _refresh_patterns(self):
        """패턴 목록 새로고침"""
        try:
            # 패턴 데이터베이스가 초기화되지 않은 경우 대기
            if not hasattr(self, 'pattern_db'):
                self.stats_label.config(text="패턴 데이터베이스 초기화 대기 중...")
                return
            
            # 기존 항목 삭제
            for item in self.pattern_tree.get_children():
                self.pattern_tree.delete(item)
            
            # 패턴 로딩
            patterns = self.pattern_db.get_all_patterns()
            
            for pattern in patterns:
                values = (
                    pattern.id,
                    pattern.pattern,
                    pattern.violation_type.value,
                    pattern.severity.value,
                    "활성" if pattern.is_active else "비활성",
                    pattern.category,
                    pattern.description
                )
                
                item = self.pattern_tree.insert("", tk.END, values=values)
                
                # 활성화 상태에 따른 색상 설정
                if not pattern.is_active:
                    self.pattern_tree.item(item, tags=("inactive",))
            
            # 비활성 패턴 스타일 설정
            self.pattern_tree.tag_configure("inactive", foreground="gray")
            
            # 통계 업데이트
            self._update_pattern_stats()
            
        except Exception as e:
            messagebox.showerror("오류", f"패턴 로딩 중 오류가 발생했습니다: {str(e)}")
    
    def _search_patterns(self):
        """패턴 검색"""
        if not hasattr(self, 'pattern_db'):
            messagebox.showwarning("알림", "패턴 데이터베이스가 아직 초기화되지 않았습니다.")
            return
            
        keyword = self.search_var.get().strip()
        if not keyword:
            self._refresh_patterns()
            return
        
        try:
            # 기존 항목 삭제
            for item in self.pattern_tree.get_children():
                self.pattern_tree.delete(item)
            
            # 검색 결과 표시
            patterns = self.pattern_db.search_patterns(keyword)
            
            for pattern in patterns:
                values = (
                    pattern.id,
                    pattern.pattern,
                    pattern.violation_type.value,
                    pattern.severity.value,
                    "활성" if pattern.is_active else "비활성",
                    pattern.category,
                    pattern.description
                )
                
                item = self.pattern_tree.insert("", tk.END, values=values)
                
                if not pattern.is_active:
                    self.pattern_tree.item(item, tags=("inactive",))
            
            self.pattern_tree.tag_configure("inactive", foreground="gray")
            
        except Exception as e:
            messagebox.showerror("오류", f"패턴 검색 중 오류가 발생했습니다: {str(e)}")
    
    def _on_pattern_search(self, event):
        """검색어 입력 시 실시간 검색"""
        # Enter 키를 누르면 검색 실행
        if event.keysym == 'Return':
            self._search_patterns()
    
    def _on_pattern_select(self, event):
        """패턴 선택 시 상세 정보 표시"""
        if not hasattr(self, 'pattern_db'):
            return
            
        selection = self.pattern_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        pattern_id = int(self.pattern_tree.item(item, "values")[0])
        pattern_rule = self.pattern_db.get_pattern(pattern_id)
        
        if pattern_rule:
            detail_text = f"패턴: {pattern_rule.pattern}\n\n"
            detail_text += f"위반 유형: {pattern_rule.violation_type.value}\n"
            detail_text += f"심각도: {pattern_rule.severity.value}\n"
            detail_text += f"카테고리: {pattern_rule.category}\n"
            detail_text += f"활성화: {'예' if pattern_rule.is_active else '아니오'}\n\n"
            detail_text += f"법적 근거:\n{pattern_rule.legal_basis}\n\n"
            detail_text += f"개선 제안:\n{pattern_rule.suggestion}\n\n"
            detail_text += f"설명: {pattern_rule.description}\n\n"
            detail_text += f"생성일: {pattern_rule.created_at}\n"
            detail_text += f"수정일: {pattern_rule.updated_at}"
            
            self.pattern_detail_text.delete(1.0, tk.END)
            self.pattern_detail_text.insert(1.0, detail_text)
    
    def _update_pattern_stats(self):
        """패턴 통계 업데이트"""
        try:
            if not hasattr(self, 'pattern_db'):
                self.stats_label.config(text="패턴 데이터베이스 초기화 대기 중...")
                return
                
            stats = self.pattern_db.get_statistics()
            
            stats_text = f"전체: {stats['total_patterns']}개 | "
            stats_text += f"활성: {stats['active_patterns']}개 | "
            stats_text += f"비활성: {stats['inactive_patterns']}개 | "
            
            # 위반 유형별 분포
            type_dist = stats.get('type_distribution', {})
            if type_dist:
                stats_text += "유형별: "
                for vtype, count in type_dist.items():
                    stats_text += f"{vtype}({count}) "
            
            self.stats_label.config(text=stats_text)
            
        except Exception as e:
            self.stats_label.config(text=f"통계 로딩 오류: {str(e)}")
    
    def _show_pattern_dialog(self, pattern_rule=None):
        """패턴 추가/수정 다이얼로그"""
        dialog = tk.Toplevel(self.root)
        dialog.title("패턴 수정" if pattern_rule else "패턴 추가")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 다이얼로그 중앙 배치
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 패턴 입력
        ttk.Label(main_frame, text="패턴:").grid(row=0, column=0, sticky=tk.W, pady=5)
        pattern_var = tk.StringVar(value=pattern_rule.pattern if pattern_rule else "")
        pattern_entry = ttk.Entry(main_frame, textvariable=pattern_var, width=50)
        pattern_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # 위반 유형
        ttk.Label(main_frame, text="위반 유형:").grid(row=1, column=0, sticky=tk.W, pady=5)
        violation_type_var = tk.StringVar(value=pattern_rule.violation_type.value if pattern_rule else ViolationType.MEDICAL_CLAIM.value)
        violation_type_combo = ttk.Combobox(main_frame, textvariable=violation_type_var, values=[vtype.value for vtype in ViolationType], state="readonly")
        violation_type_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # 심각도
        ttk.Label(main_frame, text="심각도:").grid(row=2, column=0, sticky=tk.W, pady=5)
        severity_var = tk.StringVar(value=pattern_rule.severity.value if pattern_rule else SeverityLevel.MEDIUM.value)
        severity_combo = ttk.Combobox(main_frame, textvariable=severity_var, values=[severity.value for severity in SeverityLevel], state="readonly")
        severity_combo.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # 카테고리
        ttk.Label(main_frame, text="카테고리:").grid(row=3, column=0, sticky=tk.W, pady=5)
        category_var = tk.StringVar(value=pattern_rule.category if pattern_rule else "")
        category_entry = ttk.Entry(main_frame, textvariable=category_var)
        category_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # 설명
        ttk.Label(main_frame, text="설명:").grid(row=4, column=0, sticky=(tk.W, tk.N), pady=5)
        description_text = tk.Text(main_frame, height=3, width=50, font=("Arial", 9))
        description_text.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5)
        if pattern_rule:
            description_text.insert(1.0, pattern_rule.description)
        
        # 법적 근거
        ttk.Label(main_frame, text="법적 근거:").grid(row=5, column=0, sticky=(tk.W, tk.N), pady=5)
        legal_basis_text = scrolledtext.ScrolledText(main_frame, height=4, width=50, font=("Arial", 9))
        legal_basis_text.grid(row=5, column=1, sticky=(tk.W, tk.E), pady=5)
        if pattern_rule:
            legal_basis_text.insert(1.0, pattern_rule.legal_basis)
        
        # 개선 제안
        ttk.Label(main_frame, text="개선 제안:").grid(row=6, column=0, sticky=(tk.W, tk.N), pady=5)
        suggestion_text = scrolledtext.ScrolledText(main_frame, height=4, width=50, font=("Arial", 9))
        suggestion_text.grid(row=6, column=1, sticky=(tk.W, tk.E), pady=5)
        if pattern_rule:
            suggestion_text.insert(1.0, pattern_rule.suggestion)
        
        # 활성화 상태
        is_active_var = tk.BooleanVar(value=pattern_rule.is_active if pattern_rule else True)
        active_check = ttk.Checkbutton(main_frame, text="활성화", variable=is_active_var)
        active_check.grid(row=7, column=1, sticky=tk.W, pady=10)
        
        # 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=8, column=0, columnspan=2, pady=20)
        
        def save_pattern():
            try:
                # 입력 검증
                pattern = pattern_var.get().strip()
                if not pattern:
                    messagebox.showerror("오류", "패턴을 입력해주세요.")
                    return
                
                legal_basis = legal_basis_text.get(1.0, tk.END).strip()
                if not legal_basis:
                    messagebox.showerror("오류", "법적 근거를 입력해주세요.")
                    return
                
                suggestion = suggestion_text.get(1.0, tk.END).strip()
                if not suggestion:
                    messagebox.showerror("오류", "개선 제안을 입력해주세요.")
                    return
                
                # 위반 유형과 심각도 매핑
                violation_type = next(vtype for vtype in ViolationType if vtype.value == violation_type_var.get())
                severity = next(sev for sev in SeverityLevel if sev.value == severity_var.get())
                
                # PatternRule 객체 생성
                new_pattern = PatternRule(
                    id=pattern_rule.id if pattern_rule else None,
                    pattern=pattern,
                    violation_type=violation_type,
                    severity=severity,
                    legal_basis=legal_basis,
                    suggestion=suggestion,
                    is_active=is_active_var.get(),
                    description=description_text.get(1.0, tk.END).strip(),
                    category=category_var.get().strip()
                )
                
                # 저장
                if pattern_rule:  # 수정
                    if self.pattern_db.update_pattern(new_pattern):
                        messagebox.showinfo("완료", "패턴이 수정되었습니다.")
                        dialog.destroy()
                        self._refresh_patterns()
                    else:
                        messagebox.showerror("오류", "패턴 수정에 실패했습니다.")
                else:  # 추가
                    pattern_id = self.pattern_db.add_pattern(new_pattern)
                    if pattern_id:
                        messagebox.showinfo("완료", "새 패턴이 추가되었습니다.")
                        dialog.destroy()
                        self._refresh_patterns()
                    else:
                        messagebox.showerror("오류", "패턴 추가에 실패했습니다.")
                
            except Exception as e:
                messagebox.showerror("오류", f"저장 중 오류가 발생했습니다: {str(e)}")
        
        # 저장 버튼
        save_btn = ttk.Button(button_frame, text="저장", command=save_pattern)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        # 취소 버튼
        cancel_btn = ttk.Button(button_frame, text="취소", command=dialog.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        # Enter 키로 저장
        dialog.bind('<Return>', lambda e: save_pattern())
        
        # 포커스 설정
        pattern_entry.focus_set()

    def run(self):
        """애플리케이션 실행"""
        # macOS에서 GUI 표시 강제
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after_idle(lambda: self.root.attributes('-topmost', False))
        
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\n프로그램이 사용자에 의해 종료되었습니다.")
        except Exception as e:
            print(f"GUI 실행 중 오류: {e}")
            logging.error(f"GUI 실행 중 오류: {e}")

if __name__ == "__main__":
    app = MainWindow()
    app.run()