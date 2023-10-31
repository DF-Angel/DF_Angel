import tkinter as tk
from tkinter import ttk, filedialog
import struct


class DVRAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("IDIS DVR Analyzer")

        # 메뉴바 생성
        self._create_menubar()

        # 왼쪽 트리뷰
        self.tree = ttk.Treeview(root)
        self.tree.heading('#0', text='Tree')
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 중앙 리스트뷰
        self.listbox = ttk.Treeview(root, columns=("Block No.", "Camera", "Start Time", "End Time", "Length"))
        self.listbox.heading("#1", text="Block No.")
        self.listbox.heading("#2", text="Camera")
        self.listbox.heading("#3", text="Start Time")
        self.listbox.heading("#4", text="End Time")
        self.listbox.heading("#5", text="Length")
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 리스트뷰 스크롤바 추가
        self.scrollbar = ttk.Scrollbar(root, orient='vertical', command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.LEFT, fill=tk.Y)

        # 오른쪽 미리보기
        self.preview = tk.Label(root, text="Preview")
        self.preview.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    def _create_menubar(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="이미지 불러오기", command=self.open_image)
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        search_menu = tk.Menu(menubar, tearoff=0)
        # TODO: search 메뉴 항목 추가

        analysis_menu = tk.Menu(menubar, tearoff=0)
        # TODO: analysis 메뉴 항목 추가

        menubar.add_cascade(label="Search", menu=search_menu)
        menubar.add_cascade(label="Analysis", menu=analysis_menu)

        self.root.config(menu=menubar)

    def hex_to_datetime_le(self, hex_value):
        le_hex = ''.join(reversed([hex_value[i:i + 2] for i in range(0, len(hex_value), 2)]))

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
        s_year, s_month, s_day, s_hour, s_minute, s_second = map(int, start.split('년 ')[1].split('월 ')[1].split('일 ')[
            1].split(':'))
        e_year, e_month, e_day, e_hour, e_minute, e_second = map(int,
                                                                 end.split('년 ')[1].split('월 ')[1].split('일 ')[1].split(
                                                                     ':'))

        s_total_seconds = s_hour * 3600 + s_minute * 60 + s_second
        e_total_seconds = e_hour * 3600 + e_minute * 60 + e_second

        diff = e_total_seconds - s_total_seconds
        minutes, seconds = divmod(diff, 60)

        return f"{minutes}분 {seconds}초"

    def open_image(self):
        filepath = filedialog.askopenfilename(filetypes=[("Image files", "*.dd;*.img;*.iso"), ("All files", "*.*")])
        if not filepath:
            return

        meta_offset = 0x80600080
        block_size = 128  # 예시로 임의의 블록 크기 지정

        with open(filepath, 'rb') as file:
            for block_no in range(1, 1024):  # 임의로 1024개 블록만 읽기
                file.seek(meta_offset)
                block_data = file.read(block_size)

                if len(block_data) < block_size:
                    break  # 블록 정보를 모두 읽었거나, 파일의 끝에 도달

                cam_no = struct.unpack_from('B', block_data, 0x22)[0] + 1
                start_time_hex = struct.unpack_from('4s', block_data, 0x6)[0].hex()
                end_time_hex = struct.unpack_from('4s', block_data, 0x12)[0].hex()

                start_time = self.hex_to_datetime_le(start_time_hex)
                end_time = self.hex_to_datetime_le(end_time_hex)

                self.listbox.insert("", "end", values=(f"Block {block_no}", f"Cam {cam_no}", start_time, end_time))

                meta_offset += block_size  # 다음 블록의 메타데이터 위치로 이동

        self.tree.insert("", "end", text=filepath.split("/")[-1])  # 트리뷰에 파일 이름 추가


if __name__ == "__main__":
    root = tk.Tk()
    app = DVRAnalyzer(root)
    root.geometry('1000x600')
    root.mainloop()