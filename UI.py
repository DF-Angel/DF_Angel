import binascii
import sys
import struct
import datetime
import textwrap
import traceback

from Root_Scan import Root_Scan
from Scan import Scan
from PyQt5.QtWidgets import (QApplication, QMainWindow, QMenuBar, QAction, QTreeView, QTreeWidget, QTreeWidgetItem,
                             QTableWidget, QTableWidgetItem, QLabel, QTextEdit, QVBoxLayout, QHBoxLayout,
                             QWidget, QFileDialog, QMessageBox, QGridLayout, QHeaderView, QTextBrowser, QTableView,
                             QCalendarWidget, QDialog, QPushButton, QInputDialog, QTimeEdit, QLineEdit, QFormLayout,
                             QSizePolicy, QMenu)
from PyQt5.QtCore import Qt, QSortFilterProxyModel, QTime, QDateTime, QRegExp, pyqtSignal, QSortFilterProxyModel
import sqlite3
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QRegExpValidator
#from Extract import Extractor


class CustomSortFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, *args, **kwargs):
        super(CustomSortFilterProxyModel, self).__init__(*args, **kwargs)
        self.start_datetime = None
        self.end_datetime = None


class UI_main(QMainWindow):
    def __init__(self):  # 생성자
        super().__init__()  # QMainWindow 초기화 호출

        # 정렬 기능 위한
        self.model = QStandardItemModel()
        self.proxy_model = CustomSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.blocktable = QTableView()  # QTableView로 수정
        self.blocktable.setModel(self.proxy_model)
        self.blocktable.setSortingEnabled(True)  # 체크박스 위해 추가했으나 없어도 정상동작

        self.files = {}  # 파일 경로와 트리 항목(ID)을 저장하는 딕셔너리
        self.filename = ""  # 파일 이름을 담을 전역 변수

        self.init_ui()  # ui 실행 함수 호출

        # 생성자에서 itemSelectionChanged 시그널을 연결
        self.tree.itemSelectionChanged.connect(self.on_tree_select)

    def init_ui(self):
        self.setWindowTitle("IDIS DVR Analyzer by DF_Angel")
        self.setGeometry(100, 100, 1200, 600)  # x, y, 가로, 세로

        # Main widget and layout
        mainWidget = QWidget(self)  # 창 생성
        self.setCentralWidget(mainWidget)  # 중앙 위젯으로 설정

        # layout -> left, right 두 영역으로 구분
        layout = QHBoxLayout(mainWidget)
        leftLayout = QVBoxLayout()  # 수직 (추가 요소 아래쪽에 추가)
        rightLayout = QVBoxLayout()  # 수직

        layout.addLayout(leftLayout, 1)
        layout.addLayout(rightLayout, 5)

        treeLayout = QVBoxLayout()
        mainLayout = QHBoxLayout()
        hexLayout = QHBoxLayout()

        hexoffsetLayout = QVBoxLayout()
        hexdisplayLayout = QVBoxLayout()
        asciiLayout = QVBoxLayout()

        # 왼쪽 영역
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel('Add IDIS DVR Image')
        treeLayout.addWidget(self.tree, 1)
        leftLayout.addLayout(treeLayout, 1)

        # 모델을 새로 생성
        self.model = QStandardItemModel()

        # 테이블 뷰의 수평 헤더를 설정
        for col, label in enumerate(
                ["Index", "Block", "Channel", "Start Time", "End Time", "Start Offset", "End Offset", "Size"], start=0):
            header_item = QStandardItem(label)
            header_item.setTextAlignment(Qt.AlignCenter)
            self.model.setHorizontalHeaderItem(col, header_item)

        self.blocktable.setModel(self.model)  # 테이블 뷰에 모델을 설정

        self.blocktable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.blocktable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.blocktable.verticalHeader().setVisible(False)  # Hide the vertical header
        mainLayout.addWidget(self.blocktable, 1)  # 일단 1로

        ''' 일단 프리뷰 없앰
        self.preview = QLabel("Preview")
        mainLayout.addWidget(self.preview, 0) '''

        rightLayout.addLayout(mainLayout, 2)

        # 오른쪽 영역 - hexLayout
        self.hex_offset_header = QLabel("Offset")  # 새로운 QLabel 위젯 생성
        self.hex_offset_header.setStyleSheet("background-color: white")
        self.hex_offset_header.setStyleSheet("color: blue")
        hexoffsetLayout.addWidget(self.hex_offset_header, 1)  #

        self.hex_offset = QTextEdit()
        self.hex_offset.setStyleSheet("background-color: white")
        self.hex_offset.setStyleSheet("color: blue")
        self.hex_offset.setReadOnly(True)  # 읽기 전용으로 설정 (편집 불가능)
        self.hex_offset.setLineWrapMode(QTextEdit.NoWrap)  # 자동 줄 바꿈 비활성화
        self.hex_offset.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  #
        hexoffsetLayout.addWidget(self.hex_offset, 8)  #
        hexLayout.addLayout(hexoffsetLayout, 2)

        # ====================================

        self.hex_display_header = QLabel("00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F")  # 새로운 QLabel 위젯 생성
        self.hex_display_header.setStyleSheet("background-color: white")
        hexdisplayLayout.addWidget(self.hex_display_header, 1)  #

        self.hex_display = QTextBrowser()
        self.hex_display.setStyleSheet("background-color: #CCCCCC")
        self.hex_display.setReadOnly(True)  # 읽기 전용으로 설정 (편집 불가능)
        self.hex_display.setLineWrapMode(QTextBrowser.NoWrap)  # 자동 줄 바꿈 비활성화
        self.hex_display.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  #
        hexdisplayLayout.addWidget(self.hex_display, 8)  #
        hexLayout.addLayout(hexdisplayLayout, 5)

        # ====================================

        self.ascii_display_header = QLabel("Decoded Text (ASCII)")  # 새로운 QLabel 위젯 생성
        self.ascii_display_header.setStyleSheet("background-color: white")
        asciiLayout.addWidget(self.ascii_display_header, 1)  #

        self.ascii_display = QTextBrowser()
        self.ascii_display.setStyleSheet("background-color: #CCCCCC")
        self.ascii_display.setReadOnly(True)  # 읽기 전용으로 설정 (편집 불가능)
        self.ascii_display.setLineWrapMode(QTextBrowser.NoWrap)  # 자동 줄 바꿈 비활성화
        asciiLayout.addWidget(self.ascii_display, 8)  #
        hexLayout.addLayout(asciiLayout, 5)

        rightLayout.addLayout(hexLayout, 1)

        # ====================================

        # 스크롤 같이 동작하도록 시그널, 메뉴바 생성
        self.ascii_display.verticalScrollBar().valueChanged.connect(self.on_ascii_display_scroll)
        self._create_menubar()

    # 마우스 우클릭 Extract 기능
    def context_menu(self, position):
        menu = QMenu()

        extract_action = menu.addAction("Extract")
        extract_action.triggered.connect(self.extract_selected_rows)

        # 메뉴 실행
        menu.exec_(self.blocktable.viewport().mapToGlobal(position))

    # Extract 저장경로 설정
    def select_output_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder_path:
            return folder_path
        else:
            return None

    # Extract 기능
    def extract_selected_rows(self):
        # 체크된 항목들을 가져옵니다.
        checked_indexes = [self.model.item(row, 1).text() for row in range(self.model.rowCount()) if
                           self.model.item(row, 0).checkState() == Qt.Checked]

        if not checked_indexes:
            # 체크된 항목이 없으면 메시지를 표시하고 리턴
            QMessageBox.information(self, "Extract", "No rows selected for extraction.")
            return

        # 데이터베이스 연결 생성
        connection = sqlite3.connect('IDIS_FS_sqlite.db')
        cursor = connection.cursor()

        # 추출할 파일들을 저장할 경로 설정
        extracted_folder_path = self.select_output_folder()
        if not extracted_folder_path:
            return

        #extractor = Extractor(self.filepath, extracted_folder_path)

        # 각 체크된 항목에 대해 처리
        for index_value in checked_indexes:
            # 데이터베이스에서 START_OFFSET 및 END_OFFSET 검색
            query = "SELECT START_OFFSET, END_OFFSET FROM ROOT_SCAN WHERE idx = ?"
            cursor.execute(query, (index_value,))
            result = cursor.fetchone()

            if result:
                start_offset, end_offset = result
                #extractor.read_at_offset(int(start_offset), int(end_offset))

        # 데이터베이스 연결 종료
        connection.close()

    def _create_menubar(self):
        menubar = self.menuBar()  # 현재 윈도우에 대한 메뉴바 가져옴 / self: 현재 클래스의 인스턴스

        # File
        fileMenu = menubar.addMenu('File')
        loadAction = QAction('Load Image', self)
        loadAction.triggered.connect(self.open_image)  # Load Image 액션의 트리거 시그널 발생 시 self.open_image 메서드 호출
        fileMenu.addAction(loadAction)  # "File" 메뉴에 방금 생성한 "Load Image" 액션을 추가

        # Search
        searchMenu = menubar.addMenu('Search')

        # Analysis
        analysisMenu = menubar.addMenu('Analysis')
        filterAction = QAction('Filter', self)  # 필터 기능 추가
        #filterAction.triggered.connect(self.open_calendar_to_filter)
        analysisMenu.addAction(filterAction)

        # Help
        helpMenu = menubar.addMenu('Help')

        # About
        aboutMenu = menubar.addMenu('About')

    def open_image(self):
        try:
            filepath, _ = QFileDialog.getOpenFileName(self, "Open file", "", "All Files (*)")  # filepath에 경로 저장

            self.filename = filepath.split("/")[-1]  # 경로에서 파일 이름만 추출해 전역변수 저장

            # 경로 넘기고 객체로 받기
            rs = Root_Scan(filepath)

            if rs.check_file_validation() == 0:  # 파일이 정상적으로 열렸는지 확인
                print("Invalid G2FDb image file. Exiting.")
                sys.exit()  # 프로그램 종료

            # analyzer 메소드 호출해 파일 분석, db 생성
            rs.analyzer()

            if filepath:
                item = QTreeWidgetItem(self.tree)  # 새로운 트리 항목(item) 생성
                item.setText(0, self.filename)  # 파일 이름을 트리에 추가
                self.files[filepath] = item  # self.files 딕셔너리에 경로(키)와 해당 트리 뷰 항목(값) 저장
                # print(self.files.items())

                # Hex View
                with open(filepath, 'rb') as file:
                    hex_value = file.read(5000).hex()
                    formatted_hex_lines = self.format_hex_lines(hex_value)  # 포맷된 라인 리스트로 받음

                    self.display_hex_value(formatted_hex_lines)
                    self.update_hex_offset(formatted_hex_lines)
                    self.display_ascii(formatted_hex_lines)

            db_filepath = './IDIS_FS_sqlite.db'

            self.update_root_scan(filepath)
            self.show_warning_message(filepath)

        except Exception as e:
            print(f"An error occurred in open_image: {e}")

    def update_root_scan(self, filepath):
        print("again Root_Scan")

        self.model.setColumnCount(9)  # 모델에 있는 컬럼 수 설정
        self.model.setHorizontalHeaderLabels(
            ["Check", "Index", "Block", "Channel", "Start Time", "End Time", "Start Offset", "End Offset", "Size"])
        self.blocktable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.blocktable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)

        db_filepath = './IDIS_FS_sqlite.db'
        self.process_root_scan(db_filepath)  # db 접근 메소드

        # 테이블 상단에 필터링 행 추가
        for col in range(self.model.columnCount()):  # 모델 열 개수
            item = QStandardItem("")  # 각 열에 해당하는 새로운 아이템 생성
            item.setFlags(Qt.ItemIsEditable | Qt.ItemIsEnabled)  # 편집 가능하고 활성화
            self.model.setItem(0, col, item)  # 모델 첫번째 행에 해당하는 각 열에 아이템 설정

        # 아이템 변경 시 필터링 메소드 호출  사용자가 필터링 행에 값을 입력할 때마다 filtering_method 메소드가 호출되어 필터링이 업데이트
        self.model.itemChanged.connect(self.filtering_method)  # 모델 내의 아이템이 변경될 때 발생하는 신호입니다. 이 신호는 모델 내의 아이템이 편집되면 발생
        ###### 이 부분을 엔터키로 바꿔야 할 것 같음. 바뀌자마자 신호가 가서 한 번에 바뀌도록 해야 할 것 같다

    def filtering_method(self):  # 필터링 데이터 전달
        try:
            # 필터링 조건을 확인하고 적용합니다.
            channel_item = self.model.item(0, 3)
            block_item = self.model.item(0, 2)

            if channel_item is not None and block_item is not None:
                filter_channel = channel_item.data(Qt.DisplayRole)  # Channel 열의 필터링 조건
                filter_block = block_item.data(Qt.DisplayRole)  # Block 열의 필터링 조건

                print(f"Filter Channel: {filter_channel}, Filter Block: {filter_block}")

                # 필터링된 데이터를 가져옵니다.
                self.filtered_data(filter_channel, filter_block)
            else:
                print("No item found at (0, 3) or (0, 2) in the model.")
        except Exception as e:
            print(f"An exception1 occurred: {e}")

    def filtered_data(self, filter_channel=None, filter_block=None):  # 필터링 데이터 화면에 보여주는
        try:
            # SQLite 데이터베이스 연결
            connection = sqlite3.connect('./IDIS_FS_sqlite.db')
            cursor = connection.cursor()

            # Channel 및 Block 열에서 filter_channel과 filter_block과 일치하는 행을 가져옴
            query = f"SELECT * FROM ROOT_SCAN WHERE CH = '{filter_channel}' OR NAME = '{filter_block}'"
            cursor.execute(query)
            result = cursor.fetchall()  # 각 행이 result 리스트에 저장됨

            # 시그널 연결 해제
            self.model.itemChanged.disconnect(self.filtering_method)

            # 결과를 모델에 추가하기 전에 기존 데이터 제거
            self.model.clear()  # 모델 전체를 비우는 메소드 사용

            self.model.setColumnCount(9)  # 모델에 있는 컬럼 수 설정
            self.model.setHorizontalHeaderLabels(
                ["Check", "Index", "Block", "Channel", "Start Time", "End Time", "Start Offset", "End Offset", "Size"])
            self.blocktable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.blocktable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)

            # 결과를 모델에 추가
            for row in result:
                self.model.insertRow(self.model.rowCount())  # 새로운 행 삽입
                checkbox_item = QStandardItem()  # 체크박스 아이템 생성
                checkbox_item.setCheckable(True)  # 체크 가능하도록 설정
                self.model.setItem(self.model.rowCount() - 1, 0, checkbox_item)  # 체크박스를 첫 번째 열에 추가

                for col, value in enumerate(row):
                    item = QStandardItem()  # 항상 문자열이 들어가야
                    if col == 0 or col == 1:  # index와 name에 대한 값들은 int로 설정
                        item.setData(int(value), Qt.DisplayRole)  # Qt.DisplayRole: 모델 데이터를 표시할 때 사용
                    else:
                        item.setData(value, Qt.DisplayRole)
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)  # 편집 불가능 플래그 설정
                    self.model.setItem(self.model.rowCount() - 1, col + 1, item)  # 체크박스 추가 위해 col + 1

            # 시그널 재연결
            #self.model.itemChanged.connect(self.filtering_method)

            # 연결 종료
            connection.close()

        except Exception as e:
            print(f"An exception2 occurred: {e}")

    def process_root_scan(self, db_filepath, filter_start_datetime=None, filter_end_datetime=None):
        # SQLite DB와 연결 생성
        connection = sqlite3.connect(db_filepath)
        cursor = connection.cursor()

        # ROOT_SCAN 테이블 데이터 검색
        query = "SELECT * FROM ROOT_SCAN"
        cursor.execute(query)
        rows = cursor.fetchall()  # 각 행이 rows 리스트에 저장됨

        # 기존 데이터 제거
        self.model.removeRows(0, self.model.rowCount())

        for row in rows:
            row_start_time = QDateTime.fromString(row[3], 'yyyy-MM-dd HH:mm:ss')

            # 필터링 조건을 확인하여 데이터를 모델에 추가
            if not filter_start_datetime or not filter_end_datetime or (
                    filter_start_datetime <= row_start_time <= filter_end_datetime):
                index = row[0]
                name = row[1]
                channel = row[2]
                start_time = row[3]
                end_time = row[4]
                start_offset = row[5]
                end_offset = row[6]
                size = row[7]

                self.model.insertRow(self.model.rowCount())  # 새로운 행 삽입
                checkbox_item = QStandardItem()  # 체크박스 아이템 생성
                checkbox_item.setCheckable(True)  # 체크 가능하도록 설정
                self.model.setItem(self.model.rowCount() - 1, 0, checkbox_item)  # 체크박스를 첫 번째 열에 추가

                for col, value in enumerate(row):
                    item = QStandardItem()  # 항상 문자열이 들어가야
                    if col == 0 or col == 1:  # index와 name에 대한 값들은 int로 설정
                        item.setData(int(value), Qt.DisplayRole)  # Qt.DisplayRole: 모델 데이터를 표시할 때 사용
                    else:
                        item.setData(value, Qt.DisplayRole)
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)  # 편집 불가능 플래그 설정
                    self.model.setItem(self.model.rowCount() - 1, col + 1, item)  # 체크박스 추가 위해 col + 1

        connection.close()

    def update_precise_scan(self):
        print("update_precise scan")

        self.model.clear()
        self.model.setColumnCount(15)  # 모델에 있는 컬럼 수 설정
        self.model.setHorizontalHeaderLabels(
            ["Check", "Index", "Name", "Block", "Channel", "Start Time", "End Time", "Duration", "Start Offset",
             "End Offset", "Size", "Del Type", "I-Frame", "P-Frame", "삭제 여부"])
        self.blocktable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.blocktable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)

        db_filepath = './IDIS_FS_sqlite.db'
        self.process_precise_scan(db_filepath)  # db 접근 메소드

    def process_precise_scan(self, db_filepath, filter_start_datetime=None, filter_end_datetime=None):
        # SQLite DB와 연결 생성
        connection = sqlite3.connect(db_filepath)
        cursor = connection.cursor()

        # PRECISE_SCAN 테이블 데이터 검색
        query = "SELECT * FROM PRECISE_SCAN"
        cursor.execute(query)
        rows = cursor.fetchall()  # 각 행이 rows 리스트에 저장됨

        # 기존 데이터 제거
        self.model.removeRows(0, self.model.rowCount())

        for row in rows:
            index = row[0]
            name = row[1]
            block = row[2]
            channel = row[3]
            start_time = row[4]
            end_time = row[5]
            duration = row[6]
            start_offset = row[7]
            end_offset = row[8]
            size = row[9]
            del_type = row[10]
            i_frame = row[11]
            p_frame = row[12]
            is_it_del = row[13]

            self.model.insertRow(self.model.rowCount())  # 새로운 행 삽입
            checkbox_item = QStandardItem()  # 체크박스 아이템 생성
            checkbox_item.setCheckable(True)  # 체크 가능하도록 설정
            self.model.setItem(self.model.rowCount() - 1, 0, checkbox_item)  # 체크박스를 첫 번째 열에 추가

            for col, value in enumerate(row):
                item = QStandardItem()
                if col == 0 or col == 2:  # index와 name에 대한 값들은 int로 설정
                    item.setData(int(value), Qt.DisplayRole)  # Qt.DisplayRole: 모델 데이터를 표시할 때 사용
                else:
                    item.setData(value, Qt.DisplayRole)
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)  # 편집 불가능 플래그 설정
                self.model.setItem(self.model.rowCount() - 1, col + 1, item)  # 체크박스 추가 위해 col + 1

        connection.close()

    def update_allocated(self):
        pass

    def update_unallocated(self):
        pass

    def update_log(self):
        pass

    def update_preview(self, image_path):
        # Image loading and updating preview...
        pass

    def on_tree_select(self):
        selected_items = self.tree.selectedItems()

        if selected_items:
            selected_item = selected_items[0]
            selected_name = selected_item.text(0)

            try:
                if selected_name == self.filename:
                    self.update_root_scan(list(self.files.keys())[0])
                    print("filename selected: " + list(self.files.keys())[0])

                elif selected_name == "Precise Scan":
                    # itemChanged 시그널을 차단
                    self.model.itemChanged.disconnect()
                    self.update_precise_scan()

                elif selected_name == "Allocated":
                    self.update_allocated()

                elif selected_name == "Unallocated":
                    self.update_unallocated()

                elif selected_name == "Log":
                    self.update_log()

            except Exception as e:
                print(f"An error occurred in on_tree_select: {e}")

        else:
            # 아무 항목도 선택하지 않은 경우 처리
            pass

    def format_hex_lines(self, hex_value):
        hex_lines = textwrap.wrap(hex_value, 32)  # textwrap.wrap을 사용하여 hex 문자열을 32자씩 분할하여 리스트 생성
        formatted_hex_lines = [' '.join(line[i:i + 2] for i in range(0, len(line), 2)) for line in hex_lines]
        return formatted_hex_lines

    def display_hex_value(self, formatted_hex_lines):
        formatted_hex = '\n'.join(line for line in formatted_hex_lines)
        self.hex_display.setPlainText(formatted_hex)

    def update_hex_offset(self, formatted_hex_lines):
        offset = 0
        hex_offset_text = ""

        for line in formatted_hex_lines:
            hex_offset_text += f'0x{offset:08X}\n'  # offset 값을 16진수로 표현
            offset += 16

        self.hex_offset.setText(hex_offset_text)

    def display_ascii(self, formatted_hex_lines):
        ascii_lines = []

        for line in formatted_hex_lines:
            ascii_line = binascii.unhexlify(line.replace(" ", "")).decode('ascii', 'ignore')
            ascii_lines.append(ascii_line)

        # 리스트를 개행 문자를 이용하여 문자열로 결합
        formatted_ascii = '\n'.join(ascii_lines)

        self.ascii_display.setPlainText(formatted_ascii)

    def on_ascii_display_scroll(self):
        # Get the value of the ascii_display scrollbar
        ascii_display_scroll_value = self.ascii_display.verticalScrollBar().value()

        # Set the value of the hex_display scrollbar to match ascii_display
        self.hex_display.verticalScrollBar().setValue(ascii_display_scroll_value)

        # Set the value of the hex_offset scrollbar to match ascii_display
        self.hex_offset.verticalScrollBar().setValue(ascii_display_scroll_value)

    def show_warning_message(self, filepath):
        # Add a warning message
        warning_message = QMessageBox()
        warning_message.setIcon(QMessageBox.Warning)
        warning_message.setText("정밀 스캔을 진행하시겠습니까? (시간이 오래 소요될 수 있습니다.)")
        warning_message.setWindowTitle("정밀 스캔")
        warning_message.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        warning_message.setDefaultButton(QMessageBox.Yes)

        # 버튼 클릭과 on_warning_button_clicked() 연결
        warning_message.buttonClicked.connect(self.on_warning_button_clicked)

        # 실행
        result = warning_message.exec_()

        # 실행 후 일단 트리에 추가 이후 활성화 or 비활성화
        # 트리에 파일 이름이 존재하는지 확인
        filename = filepath.split("/")[-1]
        items_with_filename = self.tree.findItems(filename, Qt.MatchExactly, 0)
        print(items_with_filename)

        selected_item = items_with_filename[0]

        # Create Allocated and Unallocated items
        allocated_item = QTreeWidgetItem()
        unallocated_item = QTreeWidgetItem()
        precise_item = QTreeWidgetItem()
        log_item = QTreeWidgetItem()

        # Set text for Allocated and Unallocated items
        precise_item.setText(0, "Precise Scan")
        allocated_item.setText(0, "Allocated")
        unallocated_item.setText(0, "Unallocated")
        log_item.setText(0, "Log")

        # Add Allocated and Unallocated items to the tree
        selected_item.addChild(precise_item)
        selected_item.addChild(allocated_item)
        selected_item.addChild(unallocated_item)
        selected_item.addChild(log_item)

        # Expand the selected item to show the new children
        selected_item.setExpanded(True)

        QApplication.processEvents()  # Force UI to update instantly

        if result == QMessageBox.Yes:
            print("User clicked Yes. Proceeding with precise scan.")
            ps = Scan(filepath)  # 정밀스캔
            ps.analyzer()  # db 생성

        elif result == QMessageBox.No:
            print("트리에 비활성화 시켜야")

            # 비활성화 처리
            for i in range(selected_item.childCount()):
                child_item = selected_item.child(i)
                child_item.setFlags(child_item.flags() & ~Qt.ItemIsEnabled)

        else:
            print("User clicked No. Cancelling precise scan.")

    def on_warning_button_clicked(self, button):
        if button.text() == "&Yes":
            print("Yes button clicked.")
        elif button.text() == "&No":
            print("No button clicked.")
        else:
            print("Unknown button clicked.")


if __name__ == '__main__':
    app = QApplication(sys.argv)  # PyQt 애플리케이션 시작위해 PyQt의 QApplication 클래스를 인스턴스화
    ex = UI_main()  # UI_main 클래스의 인스턴스를 생성합니다. 이것은 PyQt에서 사용자 인터페이스를 정의하는 클래스일 것으로 예상됩니다.
    ex.show()  # 생성된 UI 화면 표시
    sys.exit(app.exec_())
