import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import List, Optional
import logging
from ..data.pattern_manager import PatternManager
from ..core.regulation_checker import ViolationType, SeverityLevel

class PatternManagementWindow:
    """패턴 관리 UI"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.pattern_manager = PatternManager()
        self.window = None
        self.patterns_tree = None
        self.selected_pattern_id = None
        
    def show(self):
        """패턴 관리 창 표시"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
        
        self.window = tk.Toplevel(self.parent) if self.parent else tk.Tk()
        self.window.title("패턴 관리")
        self.window.geometry("1200x800")
        
        self._create_widgets()
        self._load_patterns()
        
    def _create_widgets(self):
        """UI 구성요소 생성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 툴바
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill='x', pady=(0, 10))
        
        ttk.Button(toolbar, text="새 패턴", command=self._add_pattern).pack(side='left', padx=(0, 5))
        ttk.Button(toolbar, text="편집", command=self._edit_pattern).pack(side='left', padx=(0, 5))
        ttk.Button(toolbar, text="삭제", command=self._delete_pattern).pack(side='left', padx=(0, 5))
        ttk.Button(toolbar, text="활성화/비활성화", command=self._toggle_pattern).pack(side='left', padx=(0, 5))
        
        ttk.Separator(toolbar, orient='vertical').pack(side='left', fill='y', padx=10)
        
        ttk.Button(toolbar, text="내보내기", command=self._export_patterns).pack(side='left', padx=(0, 5))
        ttk.Button(toolbar, text="가져오기", command=self._import_patterns).pack(side='left', padx=(0, 5))
        ttk.Button(toolbar, text="새로고침", command=self._load_patterns).pack(side='left', padx=(0, 5))
        
        # 검색 프레임
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(search_frame, text="검색:").pack(side='left')
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side='left', padx=(5, 0))
        search_entry.bind('<KeyRelease>', self._on_search)
        
        # 필터 프레임
        filter_frame = ttk.Frame(main_frame)
        filter_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(filter_frame, text="위반 유형:").pack(side='left')
        self.violation_type_var = tk.StringVar(value="전체")
        violation_combo = ttk.Combobox(filter_frame, textvariable=self.violation_type_var, 
                                     values=["전체"] + [vt.value for vt in ViolationType],
                                     state='readonly', width=20)
        violation_combo.pack(side='left', padx=(5, 20))
        violation_combo.bind('<<ComboboxSelected>>', self._on_filter_change)
        
        ttk.Label(filter_frame, text="심각도:").pack(side='left')
        self.severity_var = tk.StringVar(value="전체")
        severity_combo = ttk.Combobox(filter_frame, textvariable=self.severity_var,
                                    values=["전체"] + [sl.value for sl in SeverityLevel],
                                    state='readonly', width=15)
        severity_combo.pack(side='left', padx=(5, 20))
        severity_combo.bind('<<ComboboxSelected>>', self._on_filter_change)
        
        ttk.Label(filter_frame, text="상태:").pack(side='left')
        self.status_var = tk.StringVar(value="전체")
        status_combo = ttk.Combobox(filter_frame, textvariable=self.status_var,
                                  values=["전체", "활성", "비활성"],
                                  state='readonly', width=10)
        status_combo.pack(side='left', padx=(5, 0))
        status_combo.bind('<<ComboboxSelected>>', self._on_filter_change)
        
        # 패턴 목록 트리뷰
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill='both', expand=True)
        
        columns = ('ID', 'Pattern', 'Type', 'Severity', 'Status', 'Category', 'Description')
        self.patterns_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        
        # 컬럼 설정
        self.patterns_tree.heading('ID', text='ID')
        self.patterns_tree.column('ID', width=50)
        
        self.patterns_tree.heading('Pattern', text='패턴')
        self.patterns_tree.column('Pattern', width=300)
        
        self.patterns_tree.heading('Type', text='위반 유형')
        self.patterns_tree.column('Type', width=120)
        
        self.patterns_tree.heading('Severity', text='심각도')
        self.patterns_tree.column('Severity', width=80)
        
        self.patterns_tree.heading('Status', text='상태')
        self.patterns_tree.column('Status', width=60)
        
        self.patterns_tree.heading('Category', text='카테고리')
        self.patterns_tree.column('Category', width=100)
        
        self.patterns_tree.heading('Description', text='설명')
        self.patterns_tree.column('Description', width=200)
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.patterns_tree.yview)
        self.patterns_tree.configure(yscrollcommand=scrollbar.set)
        
        self.patterns_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 이벤트 바인딩
        self.patterns_tree.bind('<<TreeviewSelect>>', self._on_pattern_select)
        self.patterns_tree.bind('<Double-1>', self._edit_pattern)
        
        # 통계 정보 프레임
        stats_frame = ttk.LabelFrame(main_frame, text="통계 정보")
        stats_frame.pack(fill='x', pady=(10, 0))
        
        self.stats_label = ttk.Label(stats_frame, text="")
        self.stats_label.pack(pady=5)
        
    def _load_patterns(self):
        """패턴 목록 로드"""
        try:
            # 기존 항목 삭제
            for item in self.patterns_tree.get_children():
                self.patterns_tree.delete(item)
            
            # 패턴 로드
            patterns = self.pattern_manager.db.get_all_patterns()
            
            for pattern in patterns:
                status = "활성" if pattern.is_active else "비활성"
                
                self.patterns_tree.insert('', 'end', values=(
                    pattern.id,
                    pattern.pattern[:50] + "..." if len(pattern.pattern) > 50 else pattern.pattern,
                    pattern.violation_type.value,
                    pattern.severity.value,
                    status,
                    pattern.category,
                    pattern.description[:30] + "..." if len(pattern.description) > 30 else pattern.description
                ))
            
            # 통계 업데이트
            self._update_statistics()
            
        except Exception as e:
            messagebox.showerror("오류", f"패턴 로드 실패: {e}")
            logging.error(f"패턴 로드 실패: {e}")
    
    def _update_statistics(self):
        """통계 정보 업데이트"""
        try:
            stats = self.pattern_manager.get_pattern_statistics()
            stats_text = f"전체: {stats['total_patterns']}개 | " \
                        f"활성: {stats['active_patterns']}개 | " \
                        f"비활성: {stats['inactive_patterns']}개"
            self.stats_label.config(text=stats_text)
        except Exception as e:
            self.stats_label.config(text="통계 로드 실패")
            logging.error(f"통계 업데이트 실패: {e}")
    
    def _on_pattern_select(self, event):
        """패턴 선택 이벤트"""
        selection = self.patterns_tree.selection()
        if selection:
            item = self.patterns_tree.item(selection[0])
            self.selected_pattern_id = item['values'][0]
    
    def _on_search(self, event):
        """검색 이벤트"""
        search_term = self.search_var.get()
        if search_term:
            try:
                patterns = self.pattern_manager.search_similar_patterns(search_term)
                self._display_filtered_patterns(patterns)
            except Exception as e:
                messagebox.showerror("오류", f"검색 실패: {e}")
        else:
            self._load_patterns()
    
    def _on_filter_change(self, event):
        """필터 변경 이벤트"""
        self._apply_filters()
    
    def _apply_filters(self):
        """필터 적용"""
        try:
            patterns = self.pattern_manager.db.get_all_patterns()
            
            # 위반 유형 필터
            if self.violation_type_var.get() != "전체":
                violation_type = next(vt for vt in ViolationType if vt.value == self.violation_type_var.get())
                patterns = [p for p in patterns if p.violation_type == violation_type]
            
            # 심각도 필터
            if self.severity_var.get() != "전체":
                severity = next(sl for sl in SeverityLevel if sl.value == self.severity_var.get())
                patterns = [p for p in patterns if p.severity == severity]
            
            # 상태 필터
            if self.status_var.get() == "활성":
                patterns = [p for p in patterns if p.is_active]
            elif self.status_var.get() == "비활성":
                patterns = [p for p in patterns if not p.is_active]
            
            self._display_filtered_patterns(patterns)
            
        except Exception as e:
            messagebox.showerror("오류", f"필터 적용 실패: {e}")
    
    def _display_filtered_patterns(self, patterns):
        """필터된 패턴 표시"""
        # 기존 항목 삭제
        for item in self.patterns_tree.get_children():
            self.patterns_tree.delete(item)
        
        # 필터된 패턴 표시
        for pattern in patterns:
            status = "활성" if pattern.is_active else "비활성"
            
            self.patterns_tree.insert('', 'end', values=(
                pattern.id,
                pattern.pattern[:50] + "..." if len(pattern.pattern) > 50 else pattern.pattern,
                pattern.violation_type.value,
                pattern.severity.value,
                status,
                pattern.category,
                pattern.description[:30] + "..." if len(pattern.description) > 30 else pattern.description
            ))
    
    def _add_pattern(self):
        """새 패턴 추가"""
        dialog = PatternEditDialog(self.window, "새 패턴 추가")
        if dialog.show():
            pattern_data = dialog.get_data()
            try:
                self.pattern_manager.add_custom_pattern(
                    pattern_data['pattern'],
                    pattern_data['violation_type'],
                    pattern_data['severity'],
                    pattern_data['legal_basis'],
                    pattern_data['suggestion'],
                    pattern_data['description'],
                    pattern_data['category']
                )
                self._load_patterns()
                messagebox.showinfo("성공", "패턴이 추가되었습니다.")
            except Exception as e:
                messagebox.showerror("오류", f"패턴 추가 실패: {e}")
    
    def _edit_pattern(self):
        """패턴 편집"""
        if not self.selected_pattern_id:
            messagebox.showwarning("경고", "편집할 패턴을 선택하세요.")
            return
        
        try:
            pattern = self.pattern_manager.db.get_pattern(self.selected_pattern_id)
            if pattern:
                dialog = PatternEditDialog(self.window, "패턴 편집", pattern)
                if dialog.show():
                    pattern_data = dialog.get_data()
                    
                    # 패턴 업데이트
                    pattern.pattern = pattern_data['pattern']
                    pattern.violation_type = pattern_data['violation_type']
                    pattern.severity = pattern_data['severity']
                    pattern.legal_basis = pattern_data['legal_basis']
                    pattern.suggestion = pattern_data['suggestion']
                    pattern.description = pattern_data['description']
                    pattern.category = pattern_data['category']
                    
                    self.pattern_manager.db.update_pattern(pattern)
                    self._load_patterns()
                    messagebox.showinfo("성공", "패턴이 수정되었습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"패턴 편집 실패: {e}")
    
    def _delete_pattern(self):
        """패턴 삭제"""
        if not self.selected_pattern_id:
            messagebox.showwarning("경고", "삭제할 패턴을 선택하세요.")
            return
        
        if messagebox.askyesno("확인", "선택한 패턴을 삭제하시겠습니까?"):
            try:
                self.pattern_manager.db.delete_pattern(self.selected_pattern_id)
                self._load_patterns()
                messagebox.showinfo("성공", "패턴이 삭제되었습니다.")
            except Exception as e:
                messagebox.showerror("오류", f"패턴 삭제 실패: {e}")
    
    def _toggle_pattern(self):
        """패턴 활성화/비활성화"""
        if not self.selected_pattern_id:
            messagebox.showwarning("경고", "상태를 변경할 패턴을 선택하세요.")
            return
        
        try:
            pattern = self.pattern_manager.db.get_pattern(self.selected_pattern_id)
            if pattern:
                pattern.is_active = not pattern.is_active
                self.pattern_manager.db.update_pattern(pattern)
                self._load_patterns()
                status = "활성화" if pattern.is_active else "비활성화"
                messagebox.showinfo("성공", f"패턴이 {status}되었습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"패턴 상태 변경 실패: {e}")
    
    def _export_patterns(self):
        """패턴 내보내기"""
        file_path = filedialog.asksaveasfilename(
            title="패턴 내보내기",
            filetypes=[("JSON files", "*.json")],
            defaultextension=".json"
        )
        
        if file_path:
            try:
                if self.pattern_manager.export_patterns(file_path):
                    messagebox.showinfo("성공", f"패턴이 {file_path}로 내보내졌습니다.")
                else:
                    messagebox.showerror("오류", "패턴 내보내기 실패")
            except Exception as e:
                messagebox.showerror("오류", f"내보내기 실패: {e}")
    
    def _import_patterns(self):
        """패턴 가져오기"""
        file_path = filedialog.askopenfilename(
            title="패턴 가져오기",
            filetypes=[("JSON files", "*.json")]
        )
        
        if file_path:
            clear_existing = messagebox.askyesno(
                "확인", 
                "기존 패턴을 모두 삭제하고 가져오시겠습니까?\n"
                "'아니오'를 선택하면 기존 패턴에 추가됩니다."
            )
            
            try:
                if self.pattern_manager.import_patterns(file_path, clear_existing):
                    self._load_patterns()
                    messagebox.showinfo("성공", "패턴 가져오기가 완료되었습니다.")
                else:
                    messagebox.showerror("오류", "패턴 가져오기 실패")
            except Exception as e:
                messagebox.showerror("오류", f"가져오기 실패: {e}")


class PatternEditDialog:
    """패턴 편집 대화상자"""
    
    def __init__(self, parent, title, pattern=None):
        self.parent = parent
        self.title = title
        self.pattern = pattern
        self.result = None
        self.dialog = None
        
    def show(self):
        """대화상자 표시"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(self.title)
        self.dialog.geometry("600x500")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        self._create_widgets()
        
        if self.pattern:
            self._load_pattern_data()
        
        # 창 중앙 배치
        self.dialog.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + 50,
            self.parent.winfo_rooty() + 50
        ))
        
        self.dialog.wait_window()
        return self.result is not None
    
    def _create_widgets(self):
        """위젯 생성"""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # 패턴
        ttk.Label(main_frame, text="패턴 (정규식):").pack(anchor='w')
        self.pattern_text = tk.Text(main_frame, height=3, width=70)
        self.pattern_text.pack(fill='x', pady=(0, 10))
        
        # 위반 유형
        ttk.Label(main_frame, text="위반 유형:").pack(anchor='w')
        self.violation_type_var = tk.StringVar()
        violation_combo = ttk.Combobox(main_frame, textvariable=self.violation_type_var,
                                     values=[vt.value for vt in ViolationType], 
                                     state='readonly')
        violation_combo.pack(fill='x', pady=(0, 10))
        
        # 심각도
        ttk.Label(main_frame, text="심각도:").pack(anchor='w')
        self.severity_var = tk.StringVar()
        severity_combo = ttk.Combobox(main_frame, textvariable=self.severity_var,
                                    values=[sl.value for sl in SeverityLevel],
                                    state='readonly')
        severity_combo.pack(fill='x', pady=(0, 10))
        
        # 법적 근거
        ttk.Label(main_frame, text="법적 근거:").pack(anchor='w')
        self.legal_basis_text = tk.Text(main_frame, height=2, width=70)
        self.legal_basis_text.pack(fill='x', pady=(0, 10))
        
        # 개선 제안
        ttk.Label(main_frame, text="개선 제안:").pack(anchor='w')
        self.suggestion_text = tk.Text(main_frame, height=2, width=70)
        self.suggestion_text.pack(fill='x', pady=(0, 10))
        
        # 설명
        ttk.Label(main_frame, text="설명:").pack(anchor='w')
        self.description_entry = ttk.Entry(main_frame, width=70)
        self.description_entry.pack(fill='x', pady=(0, 10))
        
        # 카테고리
        ttk.Label(main_frame, text="카테고리:").pack(anchor='w')
        self.category_entry = ttk.Entry(main_frame, width=70)
        self.category_entry.pack(fill='x', pady=(0, 10))
        
        # 버튼
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Button(button_frame, text="확인", command=self._ok_clicked).pack(side='right', padx=(5, 0))
        ttk.Button(button_frame, text="취소", command=self._cancel_clicked).pack(side='right')
        
        # 패턴 검증 버튼
        ttk.Button(button_frame, text="패턴 검증", command=self._validate_pattern).pack(side='left')
    
    def _load_pattern_data(self):
        """기존 패턴 데이터 로드"""
        self.pattern_text.insert('1.0', self.pattern.pattern)
        self.violation_type_var.set(self.pattern.violation_type.value)
        self.severity_var.set(self.pattern.severity.value)
        self.legal_basis_text.insert('1.0', self.pattern.legal_basis)
        self.suggestion_text.insert('1.0', self.pattern.suggestion)
        self.description_entry.insert(0, self.pattern.description)
        self.category_entry.insert(0, self.pattern.category)
    
    def _validate_pattern(self):
        """패턴 유효성 검사"""
        pattern = self.pattern_text.get('1.0', 'end-1c')
        if pattern:
            pattern_manager = PatternManager()
            result = pattern_manager.validate_pattern(pattern)
            if result['valid']:
                messagebox.showinfo("검증 결과", result['message'])
            else:
                messagebox.showerror("검증 실패", result['message'])
        else:
            messagebox.showwarning("경고", "패턴을 입력하세요.")
    
    def _ok_clicked(self):
        """확인 버튼 클릭"""
        # 데이터 검증
        if not self._validate_input():
            return
        
        # 결과 저장
        self.result = {
            'pattern': self.pattern_text.get('1.0', 'end-1c'),
            'violation_type': next(vt for vt in ViolationType if vt.value == self.violation_type_var.get()),
            'severity': next(sl for sl in SeverityLevel if sl.value == self.severity_var.get()),
            'legal_basis': self.legal_basis_text.get('1.0', 'end-1c'),
            'suggestion': self.suggestion_text.get('1.0', 'end-1c'),
            'description': self.description_entry.get(),
            'category': self.category_entry.get()
        }
        
        self.dialog.destroy()
    
    def _cancel_clicked(self):
        """취소 버튼 클릭"""
        self.dialog.destroy()
    
    def _validate_input(self):
        """입력 데이터 검증"""
        if not self.pattern_text.get('1.0', 'end-1c').strip():
            messagebox.showerror("오류", "패턴을 입력하세요.")
            return False
        
        if not self.violation_type_var.get():
            messagebox.showerror("오류", "위반 유형을 선택하세요.")
            return False
        
        if not self.severity_var.get():
            messagebox.showerror("오류", "심각도를 선택하세요.")
            return False
        
        if not self.legal_basis_text.get('1.0', 'end-1c').strip():
            messagebox.showerror("오류", "법적 근거를 입력하세요.")
            return False
        
        if not self.suggestion_text.get('1.0', 'end-1c').strip():
            messagebox.showerror("오류", "개선 제안을 입력하세요.")
            return False
        
        return True
    
    def get_data(self):
        """입력된 데이터 반환"""
        return self.result