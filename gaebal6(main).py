import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import struct

class DVRAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("IDIS DVR Analyzer")
        self.files = {} # 파일 경로와 트리뷰 아이템 ID를 저장할 딕셔너리
        
        # 메뉴바 생성
        self._create_menubar()

        # 메인 프레임 생성
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 왼쪽 트리뷰
        self.tree = ttk.Treeview(main_frame)
        self.tree.heading('#0', text='Tree')
        self.tree.grid(row=0, column=0, sticky='nswe', rowspan=2)
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)  # 선택 이벤트 바인딩
        
        # 중앙 리스트뷰
        self.listbox = ttk.Treeview(main_frame, columns=("Block No.", "Camera", "Start Time", "End Time", "Length"), show="headings")
        self.listbox.grid(row=0, column=1, sticky='nswe', padx=(0, 20))

        self.listbox.column("#1", anchor="center")
        self.listbox.column("#2", anchor="center")
        self.listbox.column("#3", anchor="center")
        self.listbox.column("#4", anchor="center")
        self.listbox.column("#5", anchor="center")
        
        self.listbox.heading("#1", text="Block No.", anchor="center")
        self.listbox.heading("#2", text="Channel No.", anchor="center")
        self.listbox.heading("#3", text="Start Time", anchor="center")
        self.listbox.heading("#4", text="End Time", anchor="center")
        self.listbox.heading("#5", text="Length", anchor="center")
        #self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True) -> pack에서 grid로 통일하는 과정에서 일단 주석처리했는데 실행은 됨

        # 리스트뷰 스크롤바 (scrollbar)
        self.scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=self.listbox.yview)
        self.scrollbar.grid(row=0, column=2, sticky='ns')
        self.listbox.configure(yscrollcommand=self.scrollbar.set)

        # 오른쪽 미리보기 (preview)
        self.preview = tk.Label(main_frame, text="Preview")
        self.preview.grid(row=0, column=3, sticky='nswe')

        # 하단 Hex 값들을 위한 공간 (hex_display)
        self.hex_display = tk.Text(main_frame, height=10)
        self.hex_display.grid(row=1, column=1, columnspan=3, sticky='we', pady=(0, 20))

        # 그리드 가중치 설정
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=3)
        main_frame.columnconfigure(2, weight=0)
        main_frame.columnconfigure(3, weight=2)

        main_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=0)



    def _create_menubar(self):
        menubar = tk.Menu(self.root)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Load Image", command=self.open_image)
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        search_menu = tk.Menu(menubar, tearoff=0)
        search_menu.add_command(label="Search Entry", command=self.search_entry)
        # 다른 search 메뉴 항목 추가 ...
        menubar.add_cascade(label="Search", menu=search_menu)

        analysis_menu = tk.Menu(menubar, tearoff=0)
        analysis_menu.add_command(label="Analyze Now", command=self.analyze_now)
        # 다른 analysis 메뉴 항목 추가 ...
        menubar.add_cascade(label="Analysis", menu=analysis_menu)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Help Contents", command=self.help_contents)
        help_menu.add_command(label="About", command=self.about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

        # 추가된 메뉴 커맨드 함수들
    def search_entry(self):
        messagebox.showinfo("Search", "Search functionality not implemented yet.")

    def analyze_now(self):
        messagebox.showinfo("Analysis", "Analysis functionality not implemented yet.")

    def help_contents(self):
        messagebox.showinfo("Help", "Help contents not available yet.")

    def about(self):
        messagebox.showinfo("About", "IDIS DVR Analyzer\nVersion 1.0")

    def hex_to_datetime_le(self, hex_value):
        le_hex = ''.join(reversed([hex_value[i:i+2] for i in range(0, len(hex_value), 2)]))
        
        int_value = int(le_hex, 16)
        
        second = int_value & 0x3F
        int_value >>= 6
        minute = int_value & 0x3F
        int_value >>= 6
        hour = int_value & 0x1F
        int_value >>= 5
        day = int_value & 0x1F
        int_value >>= 5
        month = int_value & 0xF
        int_value >>= 4
        year_offset = int_value & 0x3F

        year = 1970 + year_offset
        return f"{year}년 {month:02}월 {day:02}일 {hour:02}:{minute:02}:{second:02}"


    def calc_time_difference(self, start, end):
        s_year, s_month, s_day, s_hour, s_minute, s_second = map(int, start.split('년 ')[1].split('월 ')[1].split('일 ')[1].split(':'))
        e_year, e_month, e_day, e_hour, e_minute, e_second = map(int, end.split('년 ')[1].split('월 ')[1].split('일 ')[1].split(':'))

        s_total_seconds = s_hour*3600 + s_minute*60 + s_second
        e_total_seconds = e_hour*3600 + e_minute*60 + e_second

        diff = e_total_seconds - s_total_seconds
        minutes, seconds = divmod(diff, 60)

        return f"{minutes}분 {seconds}초"

    def update_preview(self, image_path):
        #이미지 로딩 및 미리보기 테이블 업데이트 로직 구현
        pass

    def open_image(self):
        filepath = filedialog.askopenfilename(filetypes=[("All files", "*.*")])
        if not filepath:
            return
        
        filename = filepath.split("/")[-1]
        item_id = self.tree.insert("", "end", text=filename)
        self.files[filepath] = item_id  # 파일 경로와 아이템 ID 저장
        self.process_file(filepath)
        self.update_preview(filepath)

    #프로퍼티 UI를 추가하는 부분
    def create_proterties_ui(self):
        #프로퍼티 섹션 UI 생성 코드
        pass
        
    def process_file(self, filepath):
        for item in self.listbox.get_children():
            self.listbox.delete(item)

    def on_tree_select(self, event):
        selected_item = self.tree.selection()[0]
        for filepath, item_id in self.files.items():
            if item_id == selected_item:
                self.process_file(filepath)
                break
        
        meta_offset = 0x80600080
        block_size = 64  

        with open(filepath, 'rb') as file:
            for block_no in range(1, 1024):  # 임의로 1024개 블록만 읽기
                file.seek(meta_offset)
                block_data = file.read(block_size)

                if len(block_data) < block_size:
                    break  # 블록 정보를 모두 읽었거나, 파일의 끝에 도달

                chn_no = struct.unpack_from('B', block_data, 0x22)[0] + 1
                start_time_hex = struct.unpack_from('4s', block_data, 0x6)[0].hex()
                end_time_hex = struct.unpack_from('4s', block_data, 0x12)[0].hex()

                start_time = self.hex_to_datetime_le(start_time_hex)
                end_time = self.hex_to_datetime_le(end_time_hex)

                self.listbox.insert("", "end", values=(f"Block {block_no}", f"Cam {chn_no}", start_time, end_time))

                meta_offset += block_size  # 다음 블록의 메타데이터 위치로 이동

        for item in self.tree.get_children():
            self.tree.delete(item)

        self.tree.insert("", "end", text=filepath.split("/")[-1])  # 트리뷰에 파일 이름 추가


if __name__ == "__main__":
    root = tk.Tk()
    app = DVRAnalyzer(root)
    root.geometry('1000x600')
    root.mainloop()
