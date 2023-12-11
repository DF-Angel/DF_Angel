import binascii
import os
import sys
import struct
from datetime import datetime
import textwrap
import traceback

from PyQt5.QtGui import QIcon
from Root_Scan import Root_Scan
from Scan import Scan
from PyQt5.QtWidgets import (QApplication, QMainWindow, QMenuBar, QAction, QTreeView, QTreeWidget, QTreeWidgetItem,
                             QTableWidget, QTableWidgetItem, QLabel, QTextEdit, QVBoxLayout, QHBoxLayout,
                             QWidget, QFileDialog, QMessageBox, QGridLayout, QHeaderView, QTextBrowser, QTableView,
                             QCalendarWidget, QDialog, QPushButton, QInputDialog, QTimeEdit, QLineEdit, QFormLayout,
                             QSizePolicy, QMenu, QGraphicsView, QGraphicsScene, QGraphicsGridLayout)
from PyQt5.QtCore import Qt, QSortFilterProxyModel, QTime, QDateTime, QRegExp, pyqtSignal, QSortFilterProxyModel, QDir, \
    QFile, QTextStream
import sqlite3
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QRegExpValidator, QPainter
from Extract_Video import main as extract_main
from Precise_Extract_Video import main as precise_extract_main
from LogParser import LogParser
from Log_Association import Association
from PyQt5.QtChart import QChart, QBarSet, QBarSeries, QChartView, QLineSeries, QDateTimeAxis, QValueAxis, \
    QBarCategoryAxis
from PyQt5.QtCore import QDate


class CustomSortFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, *args, **kwargs):
        super(CustomSortFilterProxyModel, self).__init__(*args, **kwargs)
        self.start_datetime = None
        self.end_datetime = None


class UI_main(QMainWindow):
    def __init__(self):  # 생성자
        super().__init__()  # QMainWindow 초기화 호출

        # Set window icon
        icon_path = "icon.png"
        original_icon = QIcon(icon_path)

        # Get the pixmap from the original icon and set the new size
        pixmap = original_icon.pixmap(100, 100)  # Set the desired width and height

        # Create a new QIcon with the adjusted pixmap
        adjusted_icon = QIcon(pixmap)
        self.setWindowIcon(adjusted_icon)

        # 정렬 기능 위한
        self.model = QStandardItemModel()
        self.proxy_model = CustomSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.blocktable = QTableView()  # QTableView로 수정
        self.blocktable.setModel(self.proxy_model)
        self.blocktable.setSortingEnabled(True)

        self.files = {}  # 파일 경로와 트리 항목(ID)을 저장하는 딕셔너리
        self.filename = ""  # 파일 이름을 담을 전역 변수
        self.filepath = ""

        # hex <-> decimal
        self.current_base = {}

        # 헤더에 컨텍스트 메뉴 연결
        self.blocktable.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.blocktable.horizontalHeader().customContextMenuRequested.connect(self.show_context_menu)

        # log
        self.rightLayout = QVBoxLayout()  # 수직
        self.hexLayout = QHBoxLayout()
        self.log_layout = QVBoxLayout()
        self.button_layout = QHBoxLayout()

        self.show_daily_button = QPushButton("Daily Graph")
        self.show_daily_button.clicked.connect(self.process_log_graph)

        self.show_monthly_button = QPushButton("Monthly Graph")
        self.show_monthly_button.clicked.connect(lambda: self.show_graph("monthly"))

        self.show_yearly_button = QPushButton("Yearly Graph")
        self.show_yearly_button.clicked.connect(lambda: self.show_graph("yearly"))

        self.init_ui()  # ui 실행 함수 호출

        self.logfile_opened = False
        self.graph_generated = False

        # 생성자에서 itemSelectionChanged 시그널을 연결
        self.tree.itemSelectionChanged.connect(self.on_tree_select)

    def init_ui(self):
        self.setWindowTitle("IDIS DVR Analyzer by DF_Angel")
        self.setGeometry(100, 100, 1500, 700)  # x, y, 가로, 세로

        # Main widget and layout
        mainWidget = QWidget(self)  # 창 생성
        self.setCentralWidget(mainWidget)  # 중앙 위젯으로 설정

        # layout -> left, right 두 영역으로 구분
        layout = QHBoxLayout(mainWidget)
        leftLayout = QVBoxLayout()  # 수직 (추가 요소 아래쪽에 추가)
        # rightLayout = QVBoxLayout()  # 수직

        layout.addLayout(leftLayout, 1)
        layout.addLayout(self.rightLayout, 5)

        treeLayout = QVBoxLayout()
        mainLayout = QHBoxLayout()
        # hexLayout = QHBoxLayout()

        # hexoffsetLayout = QVBoxLayout()
        # hexdisplayLayout = QVBoxLayout()
        # asciiLayout = QVBoxLayout()

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

        ''' 프리뷰 없앰
        self.preview = QLabel("Preview")
        mainLayout.addWidget(self.preview, 0) '''

        self.rightLayout.addLayout(mainLayout, 3)

        ''' hex 없앰
        # 오른쪽 영역 - hexLayout
        self.hex_offset_header = QLabel("Offset")  # 새로운 QLabel 위젯 생성
        self.hex_offset_header.setStyleSheet("background-color: white")
        self.hex_offset_header.setStyleSheet("color: blue")
        hexoffsetLayout.addWidget(self.hex_offset_header, 1)

        self.hex_offset = QTextEdit()
        self.hex_offset.setStyleSheet("background-color: white")
        self.hex_offset.setStyleSheet("color: blue")
        self.hex_offset.setReadOnly(True)  # 읽기 전용으로 설정 (편집 불가능)
        self.hex_offset.setLineWrapMode(QTextEdit.NoWrap)  # 자동 줄 바꿈 비활성화
        self.hex_offset.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        hexoffsetLayout.addWidget(self.hex_offset, 8)
        self.hexLayout.addLayout(hexoffsetLayout, 2)

        # ====================================

        self.hex_display_header = QLabel("00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F")  # 새로운 QLabel 위젯 생성
        self.hex_display_header.setStyleSheet("background-color: white")
        hexdisplayLayout.addWidget(self.hex_display_header, 1)  #

        self.hex_display = QTextBrowser()
        self.hex_display.setStyleSheet("background-color: #CCCCCC")
        self.hex_display.setReadOnly(True)  # 읽기 전용으로 설정 (편집 불가능)
        self.hex_display.setLineWrapMode(QTextBrowser.NoWrap)  # 자동 줄 바꿈 비활성화
        self.hex_display.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        hexdisplayLayout.addWidget(self.hex_display, 8)
        self.hexLayout.addLayout(hexdisplayLayout, 5)

        # ====================================

        self.ascii_display_header = QLabel("Decoded Text (ASCII)")  # 새로운 QLabel 위젯 생성
        self.ascii_display_header.setStyleSheet("background-color: white")
        asciiLayout.addWidget(self.ascii_display_header, 1)  #

        self.ascii_display = QTextBrowser()
        self.ascii_display.setStyleSheet("background-color: #CCCCCC")
        self.ascii_display.setReadOnly(True)  # 읽기 전용으로 설정 (편집 불가능)
        self.ascii_display.setLineWrapMode(QTextBrowser.NoWrap)  # 자동 줄 바꿈 비활성화
        asciiLayout.addWidget(self.ascii_display, 8)
        self.hexLayout.addLayout(asciiLayout, 5)

        rightLayout.addLayout(self.hexLayout, 1)

        # 스크롤 같이 동작하도록 시그널
        self.ascii_display.verticalScrollBar().valueChanged.connect(self.on_ascii_display_scroll)
        '''

        self._create_menubar()

    def _create_menubar(self):
        menubar = self.menuBar()  # 현재 윈도우에 대한 메뉴바 가져옴 / self: 현재 클래스의 인스턴스

        # File
        fileMenu = menubar.addMenu('File')
        caseAction = QAction('New Case', self)
        caseAction.triggered.connect(self.new_case)  # New Case 액션의 트리거 시그널이 발생 시 self.new_case 메서드 호출
        loadCAction = QAction('Load Case', self)
        loadCAction.triggered.connect(self.open_case)  # Load Case 액션의 트리거 시그널이 발생 시 self.open_case 메서드 호출
        fileMenu.addAction(caseAction)
        fileMenu.addAction(loadCAction)

        # Search
        searchMenu = menubar.addMenu('Search')

        # Analysis
        analysisMenu = menubar.addMenu('Analysis')
        psAction = QAction('Precise scan', self)  # 추가 정밀 분석 기능
        psAction.triggered.connect(self.re_update_precise_scan)
        analysisMenu.addAction(psAction)

        # Help
        helpMenu = menubar.addMenu('Help')

        # About
        aboutMenu = menubar.addMenu('About')

    # ======================= Extract =========================
    # 마우스 우클릭 Extract
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        extract_action = menu.addAction("Extract")
        # 현재 선택된 탭이 'Precise Scan'인지 확인
        if self.is_precise_scan_tab_selected():
            extract_action.triggered.connect(self.precise_extract_selected_rows)
        else:
            extract_action.triggered.connect(self.extract_selected_rows)

        # 메뉴 실행
        menu.exec_(event.globalPos())

    def is_precise_scan_tab_selected(self):
        selected_items = self.tree.selectedItems()
        if selected_items:
            # 현재 선택된 항목의 이름을 가져옵니다.
            selected_name = selected_items[0].text(0)
            # 'Precise Scan' 탭이 선택되었는지 확인합니다.
            return selected_name == "Precise Scan"
        return False  # 선택된 항목이 없으면 False를 반환합니다.

    # Extract 저장 경로 설정
    def select_output_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder_path:
            return folder_path
        else:
            return None

    # Extract 기능
    def extract_selected_rows(self):
        # 체크된 항목들의 인덱스를 가져옵니다.
        checked_indexes = [int(self.model.item(row, 1).text()) for row in range(self.model.rowCount())
                           if self.model.item(row, 0).checkState() == Qt.Checked]

        if not checked_indexes:
            QMessageBox.information(self, "Extract", "No rows selected for extraction.")
            return

        # 현재 스크립트와 동일한 경로에 추출된 비디오를 저장합니다.
        # current_dir = os.path.dirname(os.path.abspath(__file__))
        Extract_dir = os.path.join(case_directory, 'Extract')
        # current_dir = os.path.join()
        db_filepath = './IDIS_FS_sqlite.db'
        extract_main(db_filepath, filepath, checked_indexes, Extract_dir)

        QMessageBox.information(self, 'Success', f'Extract success {filepath}.')

    # Precise Extract 기능
    def precise_extract_selected_rows(self):
        # 선택된 정밀 스캔 데이터의 인덱스 가져오기
        checked_indexes = [int(self.model.item(row, 1).text()) for row in range(self.model.rowCount())
                           if self.model.item(row, 0).checkState() == Qt.Checked]

        if not checked_indexes:
            QMessageBox.information(self, "Precise Extract", "No rows selected for extraction.")
            return

        # Precise_Extract_Video 실행
        Extract_dir = os.path.join(case_directory, 'Extract')
        db_filepath = './IDIS_FS_sqlite.db'
        precise_extract_main(db_filepath, filepath, checked_indexes, Extract_dir)
        QMessageBox.information(self, 'Success', f'Precise Extract success {filepath}.')

    # ======================= Case =========================
    def new_case(self):
        # 사용자가 생성할 케이스명 입력
        case_name, ok = QInputDialog.getText(self, 'New Case',
                                             '<b>Enter case name</b>  <br>Next, select the path to the case file.')
        self.casename = case_name  # casename 전역변수 저장

        if not ok or not case_name:
            return

        # 사용자가 생성할 경로 선택
        selected_directory = QFileDialog.getExistingDirectory(self, 'Select Directory', os.getcwd())

        if not selected_directory:
            return

        # 케이스 경로 생성
        global case_directory
        case_directory = os.path.join(selected_directory, case_name)

        if not os.path.exists(case_directory):
            os.makedirs(case_directory)

            # DB, Export 디렉토리 생성
            db_directory = os.path.join(case_directory, 'DB')
            extract_directory = os.path.join(case_directory, 'Extract')

            os.makedirs(db_directory)
            os.makedirs(extract_directory)

            QMessageBox.information(self, 'Success',
                                    f'Case "{case_name}" created successfully at {case_directory}. <br><br><b>Select the image you want to analyze.</b> ')

        else:
            QMessageBox.warning(self, 'Error', f'Case "{case_name}" already exists at {case_directory}.')

        global filepath

        try:
            filepath, _ = QFileDialog.getOpenFileName(self, "Open file", "", "All Files (*)")  # filepath에 경로 저장
            if not filepath:
                return

            imgpath_file = os.path.join(case_directory, 'imgpath.case')
            with open(imgpath_file, 'w') as file:
                file.write(filepath)
            QMessageBox.information(self, 'Success', f"File '{case_directory}' created successfully.")
            self.filename = filepath.split("/")[-1]  # 경로에서 파일 이름만 추출해 전역변수 저장

            rs = Root_Scan(filepath)  # Root_Scan()에 경로 넘기고 객체로 받기

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

                '''
                # Hex View
                with open(filepath, 'rb') as file:
                    hex_value = file.read(5000).hex()
                    formatted_hex_lines = self.format_hex_lines(hex_value)  # 포맷된 라인 리스트로 받음

                    self.display_hex_value(formatted_hex_lines)
                    self.update_hex_offset(formatted_hex_lines)
                    self.display_ascii(formatted_hex_lines)
                '''

            db_filepath = './IDIS_FS_sqlite.db'

            self.update_root_scan(filepath)  # 파일 처리 메서드 호출
            self.show_warning_message(filepath)

        except Exception as e:
            print(f"An error occurred in new_case: {e}")

    def open_case(self):
        # 사용자에게 디렉토리를 선택하도록 요청
        selected_directory = QFileDialog.getExistingDirectory(self, 'Select Case Directory', os.getcwd())
        self.casename = selected_directory.split("/")[-1]  # 경로에서 파일 이름만 추출해 전역변수 저장
        print(selected_directory)
        if not selected_directory:
            return

        try:
            imgfile_path = QDir(selected_directory).filePath('imgpath.case')
            imgfile = QFile(imgfile_path)

            if not imgfile.open(QFile.ReadOnly | QFile.Text):
                print(f"파일을 열 수 없습니다: {imgfile.errorString()}")
            else:
                stream = QTextStream(imgfile)
                while not stream.atEnd():
                    imgpath = stream.readLine()
                    imgfile.close()

            self.filename = imgpath.split("/")[-1]  # 경로에서 파일 이름만 추출해 전역변수 저장

            rs = Root_Scan(imgpath)  # Root_Scan()에 경로 넘기고 객체로 받기

            if rs.check_file_validation() == 0:  # 파일이 정상적으로 열렸는지 확인
                print("Invalid G2FDb image file. Exiting.")
                sys.exit()  # 프로그램 종료

            # analyzer 메소드 호출해 파일 분석, db 생성
            rs.analyzer()

            if imgpath:
                item = QTreeWidgetItem(self.tree)  # 새로운 트리 항목(item) 생성
                item.setText(0, self.filename)  # 파일 이름을 트리에 추가
                self.files[imgpath] = item  # self.files 딕셔너리에 경로(키)와 해당 트리 뷰 항목(값) 저장
                # print(self.files.items())

                '''
                # Hex View
                with open(imgpath, 'rb') as file:
                    hex_value = file.read(5000).hex()
                    formatted_hex_lines = self.format_hex_lines(hex_value)  # 포맷된 라인 리스트로 받음

                    self.display_hex_value(formatted_hex_lines)
                    self.update_hex_offset(formatted_hex_lines)
                    self.display_ascii(formatted_hex_lines)
                '''

            db_filepath = './IDIS_FS_sqlite.db'

            self.update_root_scan(imgpath)  # 파일 처리 메서드 호출
            self.show_warning_message(imgpath)

        except Exception as e:
            print(f"An error occurred in open_case: {e}")

    # ======================= 1. Root scan =========================
    def update_root_scan(self, filepath):
        print("Root_Scan")

        self.model.setColumnCount(9)  # 모델에 있는 컬럼 수 설정
        self.model.setHorizontalHeaderLabels(
            ["Check", "Index", "Block", "Channel", "Start Time", "End Time", "Start Offset", "End Offset", "Size"])

        self.blocktable.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)  # 사용자 조절 가능
        self.blocktable.horizontalHeader().resizeSection(0, 60)
        self.blocktable.horizontalHeader().resizeSection(1, 60)
        self.blocktable.horizontalHeader().resizeSection(2, 60)
        self.blocktable.horizontalHeader().resizeSection(3, 60)
        self.blocktable.horizontalHeader().resizeSection(4, 140)
        self.blocktable.horizontalHeader().resizeSection(5, 140)

        db_filepath = './IDIS_FS_sqlite.db'
        self.process_root_scan(db_filepath)  # db 접근 메소드

    def process_root_scan(self, db_filepath):
        # SQLite DB와 연결 생성
        connection = sqlite3.connect(db_filepath)
        cursor = connection.cursor()

        # ROOT_SCAN 테이블 데이터 검색
        query = "SELECT * FROM ROOT_SCAN"
        cursor.execute(query)
        rows = cursor.fetchall()  # 각 행이 rows 리스트에 저장됨

        # 기존 데이터 제거
        self.model.removeRows(0, self.model.rowCount())

        # 테이블 상단에 필터링 행 추가
        for col in range(self.model.columnCount()):  # 모델 열 개수
            item = QStandardItem("")  # 각 열에 해당하는 새로운 아이템 생성
            item.setFlags(Qt.ItemIsEditable | Qt.ItemIsEnabled)  # 편집 가능하고 활성화
            self.model.setItem(0, col, item)  # 모델 첫번째 행에 해당하는 각 열에 아이템 설정

        # Filtering 버튼 추가
        check_button = QPushButton("Search")
        self.blocktable.setIndexWidget(self.model.index(0, 0), check_button)
        check_button.clicked.connect(self.onFilteringBtnClicked)

        for row in rows:
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
            checkbox_item.setCheckState(Qt.Unchecked)  # 체크 상태 설정
            checkbox_item.setTextAlignment(Qt.AlignCenter)  # 가운데 정렬 설정
            self.model.setItem(self.model.rowCount() - 1, 0, checkbox_item)  # 체크박스를 첫 번째 열에 추가

            for col, value in enumerate(row):
                item = QStandardItem()  # 항상 문자열이 들어가야
                if col == 0 or col == 1:  # index와 name에 대한 값들은 int로 설정
                    item.setData(int(value), Qt.DisplayRole)  # Qt.DisplayRole: 모델 데이터를 표시할 때 사용
                else:
                    item.setData(value, Qt.DisplayRole)
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)  # 편집 불가능 플래그 설정
                item.setTextAlignment(Qt.AlignCenter)
                self.model.setItem(self.model.rowCount() - 1, col + 1, item)  # 체크박스 추가 위해 col + 1

        connection.close()

    # ======================= Hex <-> Decimal =========================
    def show_context_menu(self, pos):
        # 우클릭한 위치의 열 인덱스 가져오기
        header = self.blocktable.horizontalHeader()
        index = header.logicalIndexAt(pos.x())

        # 컨텍스트 메뉴 생성
        menu = QMenu(self)
        hex_action = QAction("Convert to Hex", self)
        hex_action.triggered.connect(lambda: self.convert_to_base(index, 16))
        menu.addAction(hex_action)

        decimal_action = QAction("Convert to Decimal", self)
        decimal_action.triggered.connect(lambda: self.convert_to_base(index, 10))
        menu.addAction(decimal_action)

        # 메뉴 표시
        menu.exec_(header.mapToGlobal(pos))

    def convert_to_base(self, col_index, base):
        for row in range(self.model.rowCount()):
            item = self.model.item(row, col_index)
            if item is not None:
                try:
                    current_base = self.current_base.get((row, col_index), 10)  # 현재 기수 정보 가져오기 (기본값은 10진수)
                    if current_base != base:  # 이미 해당 기수로 표현되어 있지 않은 경우에만 변환
                        if base == 16:  # 10 -> 16
                            value = int(item.text())
                            hex_value = hex(value)[2:]  # 0x
                            item.setText(hex_value)
                            self.current_base[(row, col_index)] = base  # 현재 기수 정보 저장
                        elif base == 10:  # 16 -> 10
                            value = int(item.text(), 16)
                            item.setText(str(value))
                            self.current_base[(row, col_index)] = base  # 현재 기수 정보 저장

                except ValueError:
                    # 변환 실패 시에는 예외 처리
                    pass

    # ======================= Filtering =========================
    # 필터링 트리거
    def onFilteringBtnClicked(self):
        print("Filtering button clicked")
        self.filtering_method()

    # 필터링 데이터 전달
    def filtering_method(self):
        try:
            # 각 0행 1열 아이템 객체 추출
            index_item = self.model.item(0, 1)
            block_item = self.model.item(0, 2)
            channel_item = self.model.item(0, 3)
            start_time_item = self.model.item(0, 4)
            end_time_item = self.model.item(0, 5)
            start_offset_item = self.model.item(0, 6)
            end_offset_item = self.model.item(0, 7)
            size_item = self.model.item(0, 8)

            # 실제 데이터 추출
            filter_index = index_item.data(Qt.DisplayRole)
            filter_block = block_item.data(Qt.DisplayRole)
            filter_channel = channel_item.data(Qt.DisplayRole)
            filter_start_time = start_time_item.data(Qt.DisplayRole)
            filter_end_time = end_time_item.data(Qt.DisplayRole)
            filter_start_offset = start_offset_item.data(Qt.DisplayRole)
            filter_end_offset = end_offset_item.data(Qt.DisplayRole)
            filter_size = size_item.data(Qt.DisplayRole)

            if filter_block == '' and filter_channel == '' and filter_start_time == '' and filter_end_time == '':
                pass
            else:
                # if filter_start_time == '':
                # print("hi")
                print(
                    f"Block: {filter_block}, Filtered Channel: {filter_channel}, Start time: {filter_start_time}, End time: {filter_end_time}")

                self.filtered_data(filter_block, filter_channel, filter_start_time, filter_end_time)

        except Exception as e:
            print(f"filtering_method() exception occurred: {e}")

    # 필터링 결과 출력
    def filtered_data(self, filter_block, filter_channel, filter_start_time, filter_end_time):
        try:
            if filter_block == '' and filter_channel == '' and filter_start_time == '' and filter_end_time == '':
                pass
            else:
                # SQLite 데이터베이스 연결
                connection = sqlite3.connect('./IDIS_FS_sqlite.db')
                cursor = connection.cursor()

                # Channel 및 Block 열에서 filter_channel과 filter_block과 일치하는 행을 가져옴
                query = f"SELECT * FROM ROOT_SCAN WHERE"
                if filter_block != '':
                    query += f" NAME = '{filter_block}' OR"
                if filter_channel != '':
                    query += f" CH = '{filter_channel}' OR"
                if filter_start_time != '':
                    query += f" START_TIME LIKE '%{filter_start_time}%' OR"
                if filter_end_time != '':
                    query += f" END_TIME LIKE '%{filter_end_time}%' OR"
                query = query.rstrip(" OR")

                cursor.execute(query)
                result = cursor.fetchall()  # 각 행이 result 리스트에 저장됨

                # 결과를 모델에 추가하기 전에 기존 데이터 제거
                self.model.clear()

                self.model.setColumnCount(9)  # 모델에 있는 컬럼 수 설정
                self.model.setHorizontalHeaderLabels(
                    ["Check", "Index", "Block", "Channel", "Start Time", "End Time", "Start Offset", "End Offset",
                     "Size"])
                self.blocktable.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)  # 사용자 조절 가능
                self.blocktable.horizontalHeader().resizeSection(0, 60)
                self.blocktable.horizontalHeader().resizeSection(1, 60)
                self.blocktable.horizontalHeader().resizeSection(2, 60)
                self.blocktable.horizontalHeader().resizeSection(3, 60)
                self.blocktable.horizontalHeader().resizeSection(4, 140)
                self.blocktable.horizontalHeader().resizeSection(5, 140)

                # 테이블 상단에 필터링 행 추가
                for col in range(self.model.columnCount()):  # 모델 열 개수
                    item = QStandardItem("")  # 각 열에 해당하는 새로운 아이템 생성
                    item.setFlags(Qt.ItemIsEditable | Qt.ItemIsEnabled)  # 편집 가능하고 활성화
                    self.model.setItem(0, col, item)  # 모델 첫번째 행에 해당하는 각 열에 아이템 설정

                # Filtering 버튼 추가
                Filtering_btn = QPushButton("Search")
                self.blocktable.setIndexWidget(self.model.index(0, 0), Filtering_btn)
                Filtering_btn.clicked.connect(self.onFilteringBtnClicked)

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
                        item.setTextAlignment(Qt.AlignCenter)
                        self.model.setItem(self.model.rowCount() - 1, col + 1, item)  # 체크박스 추가 위해 col + 1

        except Exception as e:
            print(f"filtered_data() exception occurred: {e}")

    # ======================= 2. Precise scan =========================
    def update_precise_scan(self):
        print("update_precise scan()")

        self.model.clear()

        self.model.setColumnCount(15)  # 모델에 있는 컬럼 수 설정
        self.model.setHorizontalHeaderLabels(
            ["Check", "Index", "Name", "Block", "Channel", "Start Time", "End Time", "Duration", "Start Offset",
             "End Offset", "Size", "Del Type", "I-Frame", "P-Frame", "삭제 여부"])
        self.blocktable.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)  # 사용자 조절 가능
        self.blocktable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.blocktable.horizontalHeader().resizeSection(0, 60)
        self.blocktable.horizontalHeader().resizeSection(1, 60)
        self.blocktable.horizontalHeader().resizeSection(2, 60)
        self.blocktable.horizontalHeader().resizeSection(3, 60)
        self.blocktable.horizontalHeader().resizeSection(4, 60)
        self.blocktable.horizontalHeader().resizeSection(5, 140)
        self.blocktable.horizontalHeader().resizeSection(6, 140)

        db_filepath = './IDIS_FS_sqlite.db'
        self.process_precise_scan(db_filepath)  # db 접근 메소드

    def process_precise_scan(self, db_filepath):
        # SQLite DB와 연결 생성
        connection = sqlite3.connect(db_filepath)
        cursor = connection.cursor()

        # PRECISE_SCAN 테이블 데이터 검색
        query = "SELECT * FROM PRECISE_SCAN"
        cursor.execute(query)
        rows = cursor.fetchall()  # 각 행 rows 리스트에 저장

        # 테이블 상단에 필터링 행 추가
        for col in range(self.model.columnCount()):  # 모델 열 개수
            item = QStandardItem("")  # 각 열에 해당하는 새로운 아이템 생성
            item.setFlags(Qt.ItemIsEditable | Qt.ItemIsEnabled)  # 편집 가능하고 활성화
            self.model.setItem(0, col, item)  # 모델 첫번째 행에 해당하는 각 열에 아이템 설정

        # Filtering 버튼 추가
        check_button = QPushButton("Search")
        self.blocktable.setIndexWidget(self.model.index(0, 0), check_button)
        check_button.clicked.connect(self.onFilteringBtnClicked)

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
                elif col == 10:  # del_type 매칭
                    if value == 0:
                        output_text = '할당'
                    elif value == 1:
                        output_text = '부분 삭제'
                    elif value == 2:
                        output_text = '모든 데이터 삭제'  # 바꿔야 함
                    elif value == 3:
                        output_text = '포맷'
                    elif value == 4:
                        output_text = '슬랙'
                    else:
                        output_text = '알 수 없음'
                    item.setData(output_text, Qt.DisplayRole)
                else:
                    item.setData(value, Qt.DisplayRole)

                item.setFlags(item.flags() ^ Qt.ItemIsEditable)  # 편집 불가능 플래그 설정
                item.setTextAlignment(Qt.AlignCenter)
                self.model.setItem(self.model.rowCount() - 1, col + 1, item)  # 체크박스 추가 위해 col + 1

        connection.close()

    def re_update_precise_scan(self):
        # 트리에 파일 이름이 존재하는지 확인
        # filename = filepath.split("/")[-1]
        items_with_filename = self.tree.findItems(self.filename, Qt.MatchExactly, 0)

        selected_item = items_with_filename[0]

        print("Proceeding with precise scan.")
        ps = Scan(self.filepath)  # 정밀스캔
        ps.analyzer()  # db 생성

        for i in range(selected_item.childCount()):
            child_item = selected_item.child(i)
            child_item.setFlags(child_item.flags() | Qt.ItemIsEnabled)

    # ======================= 3. Allocated =========================
    def update_allocated(self):
        print("update_allocated")

        self.model.clear()
        self.model.setColumnCount(15)  # 모델에 있는 컬럼 수 설정
        self.model.setHorizontalHeaderLabels(
            ["Check", "Index", "Name", "Block", "Channel", "Start Time", "End Time", "Duration", "Start Offset",
             "End Offset", "Size", "Del Type", "I-Frame", "P-Frame", "삭제 여부"])
        self.blocktable.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)  # 사용자 조절 가능
        self.blocktable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.blocktable.horizontalHeader().resizeSection(1, 60)
        self.blocktable.horizontalHeader().resizeSection(2, 60)
        self.blocktable.horizontalHeader().resizeSection(3, 60)
        self.blocktable.horizontalHeader().resizeSection(4, 60)
        self.blocktable.horizontalHeader().resizeSection(5, 140)
        self.blocktable.horizontalHeader().resizeSection(6, 140)

        db_filepath = './IDIS_FS_sqlite.db'
        self.process_allocated(db_filepath)  # db 접근 메소드

    def process_allocated(self, db_filepath, filter_start_datetime=None, filter_end_datetime=None):
        try:
            # SQLite DB와 연결 생성
            connection = sqlite3.connect(db_filepath)
            cursor = connection.cursor()

            # PRECISE_SCAN - is_it_del이 0인 행만 추출
            query = f"SELECT * FROM PRECISE_SCAN WHERE IS_IT_DEL = 0"
            cursor.execute(query)
            rows = cursor.fetchall()  # 각 행이 rows 리스트에 저장됨

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
                    elif col == 10:  # del_type 매칭
                        if value == 0:
                            output_text = '할당'
                        elif value == 1:
                            output_text = '부분 삭제'
                        elif value == 2:
                            output_text = '모든 데이터 삭제'
                        elif value == 3:
                            output_text = '포맷'
                        elif value == 4:
                            output_text = '슬랙'
                        else:
                            output_text = '알 수 없음'
                        item.setData(output_text, Qt.DisplayRole)
                    else:
                        item.setData(value, Qt.DisplayRole)
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)  # 편집 불가능 플래그 설정
                    item.setTextAlignment(Qt.AlignCenter)
                    self.model.setItem(self.model.rowCount() - 1, col + 1, item)  # 체크박스 추가 위해 col + 1

            connection.close()

        except Exception as e:
            print(f"An error occurred: {e}")
            import traceback
            traceback.print_exc()

    # ======================= 4. Unallocated =========================
    def update_unallocated(self):
        print("update_allocated")

        self.model.clear()
        self.model.setColumnCount(15)  # 모델에 있는 컬럼 수 설정
        self.model.setHorizontalHeaderLabels(
            ["Check", "Index", "Name", "Block", "Channel", "Start Time", "End Time", "Duration", "Start Offset",
             "End Offset", "Size", "Del Type", "I-Frame", "P-Frame", "삭제 여부"])
        self.blocktable.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)  # 사용자 조절 가능
        self.blocktable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.blocktable.horizontalHeader().resizeSection(1, 60)
        self.blocktable.horizontalHeader().resizeSection(2, 60)
        self.blocktable.horizontalHeader().resizeSection(3, 60)
        self.blocktable.horizontalHeader().resizeSection(4, 60)
        self.blocktable.horizontalHeader().resizeSection(5, 140)
        self.blocktable.horizontalHeader().resizeSection(6, 140)

        db_filepath = './IDIS_FS_sqlite.db'
        self.process_unallocated(db_filepath)  # db 접근 메소드

    def process_unallocated(self, db_filepath):
        try:
            # SQLite DB와 연결 생성
            connection = sqlite3.connect(db_filepath)
            cursor = connection.cursor()

            # PRECISE_SCAN - is_it_del이 0인 행만 추출
            query = f"SELECT * FROM PRECISE_SCAN WHERE IS_IT_DEL = 1"
            cursor.execute(query)
            rows = cursor.fetchall()  # 각 행이 rows 리스트에 저장됨

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
                    elif col == 10:  # del_type 매칭
                        if value == 0:
                            output_text = '할당'
                        elif value == 1:
                            output_text = '부분 삭제'
                        elif value == 2:
                            output_text = '모든 데이터 삭제'
                        elif value == 3:
                            output_text = '포맷'
                        elif value == 4:
                            output_text = '슬랙'
                        else:
                            output_text = '알 수 없음'
                        item.setData(output_text, Qt.DisplayRole)
                    else:
                        item.setData(value, Qt.DisplayRole)
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)  # 편집 불가능 플래그 설정
                    item.setTextAlignment(Qt.AlignCenter)
                    self.model.setItem(self.model.rowCount() - 1, col + 1, item)  # 체크박스 추가 위해 col + 1

            connection.close()

        except Exception as e:
            print(f"An error occurred: {e}")
            import traceback
            traceback.print_exc()

    # ======================= 5. Log =========================
    def open_logfile(self):
        try:
            if not self.logfile_opened:
                logfilepath, _ = QFileDialog.getOpenFileName(self, "Open log file", "",
                                                             "All Files (*)")  # filepath에 경로 저장

                # self.logfilepath = logfilepath.split("/")[-1]  # 경로에서 파일 이름만 추출해 전역변수 저장

                if logfilepath:
                    # 화면이 처리 중임을 나타내는 메시지 창 표시
                    processing_msg = "로그 파일 처리 중입니다. 잠시만 기다려주세요..."
                    QMessageBox.information(self, "처리 중", processing_msg, QMessageBox.Ok)

                    log = LogParser(logfilepath)  # LogParser()에 경로 넘기고 객체로 받기

                    log.parse()  # DB 생성?

                    db_filepath = './IDIS_FS_sqlite.db'
                    self.update_log(db_filepath)  # 로그 처리 메서드 호출
                    self.show_warning_message_log(db_filepath)

                    self.logfile_opened = True




            else:
                db_filepath = './IDIS_FS_sqlite.db'
                self.update_log(db_filepath)

        except Exception as e:
            print(f"An error occurred in open_logfile: {e}")

    def update_log(self, db_filepath):
        try:
            print("update_log()")

            # 리스트
            self.model.clear()
            self.model.setColumnCount(3)  # 모델 컬럼 수 설정
            self.model.setHorizontalHeaderLabels(["Index", "Event", "Time"])
            self.blocktable.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)  # 사용자 조절 가능
            self.blocktable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
            self.blocktable.horizontalHeader().resizeSection(0, 60)
            self.blocktable.horizontalHeader().resizeSection(1, 250)
            self.blocktable.horizontalHeader().resizeSection(2, 140)
            self.process_log_list(db_filepath)  # db 리스트 생성

            # 그래프
            self.clear_hex_layout()  # hexLayout 초기화
            self.process_log_graph()  # db 그래프 생성

            '''
            if not self.graph_generated:
                self.process_log_graph() # db 그래프 생성
                self.graph_generated = True  # 최초 실행 후에는 상태를 변경
            else:
                pass
                '''

        except Exception as e:
            print(f"An error occurred in update_log(): {e}")

    def process_log_graph(self):
        try:
            self.clear_hex_layout()  # hexLayout 초기화

            print("process_log_graph()")
            db_filepath = './IDIS_FS_sqlite.db'

            connection = sqlite3.connect(db_filepath)
            cursor = connection.cursor()

            # Events to consider
            events_to_consider = ['부분 삭제 시작', '모든 데이터 삭제', '포맷', '자동 삭제']

            # Query to get distinct dates from the database
            date_query = "SELECT DISTINCT DATE(DATETIME) FROM LOG"
            cursor.execute(date_query)
            date_result = cursor.fetchall()

            # Extract distinct dates from the result
            date_range = [row[0] for row in date_result]

            # Dictionary to store date counts for each event
            date_event_counts = {formatted_date: {event: 0 for event in events_to_consider} for formatted_date in
                                 date_range}

            # Query to get count of events per date (considering only year-month-day)
            for event in events_to_consider:
                query = f"SELECT DATE(DATETIME), COUNT(EVENT) FROM LOG WHERE EVENT LIKE '%{event}%' GROUP BY DATE(DATETIME)"
                cursor.execute(query)

                # Traverse the query result and update the date_event_counts dictionary
                for row in cursor.fetchall():
                    datetime_str, event_count = row
                    date_obj = QDate.fromString(datetime_str, "yyyy-MM-dd")
                    formatted_date = date_obj.toString("yyyy-MM-dd")

                    # Update the dictionary with event count for the specific date and event
                    date_event_counts[formatted_date][event] = event_count

            connection.close()

            # Filter out dates with no occurrence for any event
            date_event_counts = {formatted_date: event_counts for formatted_date, event_counts in
                                 date_event_counts.items() if any(event_counts.values())}

            print(date_event_counts)

            if not date_event_counts:
                print("No data to display.")
                return

            # custom legend 매핑
            event_legend_mapping = {
                '부분 삭제 시작': '부분 삭제',
                '모든 데이터 삭제': '모든 데이터 삭제',
                '포맷': '포맷',
                '자동 삭제': '자동 삭제'
            }

            # 각 이벤트의 bar series 생성
            series_list = []
            for event in events_to_consider:
                bar_set = QBarSet(event_legend_mapping.get(event, event))  # 범례
                for formatted_date, event_counts in date_event_counts.items():
                    bar_set.append(event_counts[event])
                series = QBarSeries()
                series.append(bar_set)
                series_list.append(series)

            # Create a chart and set the series
            chart = QChart()
            for series in series_list:
                chart.addSeries(series)

            chart.setAnimationOptions(QChart.SeriesAnimations)
            chart.legend().setVisible(True)

            # 가로축 (날짜)
            datetime_axis = QBarCategoryAxis()
            datetime_axis.append(date_event_counts.keys())  # Use the keys (dates) directly
            chart.addAxis(datetime_axis, Qt.AlignBottom)

            # 세로축
            value_axis = QValueAxis()  # 세로축 객체
            value_axis.setTickCount(5)  # 세로축 눈금 개수
            chart.addAxis(value_axis, Qt.AlignLeft)

            # Set the range for the vertical axis
            min_value = 0
            max_value = max(max(event_counts.values()) for event_counts in
                            date_event_counts.values())  # Use the maximum value among all events
            value_axis.setRange(min_value, max_value)  # 세로축의 범위 설정

            # layout
            self.button_layout.addWidget(self.show_daily_button, 1)
            self.button_layout.addWidget(self.show_monthly_button, 1)
            self.button_layout.addWidget(self.show_yearly_button, 1)
            self.log_layout.addLayout(self.button_layout, 1)

            log_graph_widget = QChartView(chart)
            log_graph_widget.setStyleSheet("background-color: white")
            self.log_layout.addWidget(log_graph_widget, 10)

            self.hexLayout.addLayout(self.log_layout, 10)
            self.rightLayout.addLayout(self.hexLayout, 2)


        except Exception as e:
            print(f"An error occurred in process_log_graph(): {e}")

    def show_graph(self, hi):
        try:
            self.clear_hex_layout()  # hexLayout 초기화
            print("show_graph()")

            db_filepath = './IDIS_FS_sqlite.db'
            connection = sqlite3.connect(db_filepath)
            cursor = connection.cursor()

            # Events to consider
            events_to_consider = ['부분 삭제 시작', '모든 데이터 삭제', '포맷', '자동 삭제']

            # Query to get distinct dates from the database
            date_query = "SELECT DISTINCT DATE(DATETIME) FROM LOG"
            cursor.execute(date_query)
            date_result = cursor.fetchall()

            # Extract distinct dates from the result
            date_range = [row[0] for row in date_result]

            # 날짜별로 각 이벤트가 발생한 횟수를 저장하기 위한 딕셔너리
            date_event_counts = {formatted_date: {event: 0 for event in events_to_consider} for formatted_date in
                                 date_range}

            # Query to get count of events per date (considering only year-month-day)
            for event in events_to_consider:
                query = f"SELECT DATE(DATETIME), COUNT(EVENT) FROM LOG WHERE EVENT LIKE '%{event}%' GROUP BY DATE(DATETIME)"
                cursor.execute(query)

                # Traverse the query result and update the date_event_counts dictionary
                for row in cursor.fetchall():
                    datetime_str, event_count = row
                    date_obj = QDate.fromString(datetime_str, "yyyy-MM-dd")
                    formatted_date = date_obj.toString("yyyy-MM-dd")

                    # Update the dictionary with event count for the specific date and event
                    date_event_counts[formatted_date][event] = event_count

            connection.close()

            # Filter out dates with no occurrence for any event
            date_event_counts = {formatted_date: event_counts for formatted_date, event_counts in
                                 date_event_counts.items() if any(event_counts.values())}

            print(date_event_counts)

            if not date_event_counts:
                print("No data to display.")
                return

            # Monthly, Yearly
            result_dict = {}

            if hi == "monthly":
                for formatted_date, event_counts in date_event_counts.items():
                    year_month = formatted_date.rsplit('-', 1)[0]  # 연도와 월 추출
                    if year_month not in result_dict:
                        result_dict[year_month] = {event: 0 for event in events_to_consider}

                    for event, count in event_counts.items():
                        result_dict[year_month][event] += count
            elif hi == "yearly":
                for formatted_date, event_counts in date_event_counts.items():
                    year = formatted_date.split('-')[0]  # 연도
                    if year not in result_dict:
                        result_dict[year] = {event: 0 for event in events_to_consider}

                    for event, count in event_counts.items():
                        result_dict[year][event] += count

            # custom legend 매핑
            event_legend_mapping = {
                '부분 삭제 시작': '부분 삭제',
                '모든 데이터 삭제': '모든 데이터 삭제',
                '포맷': '포맷',
                '자동 삭제': '자동 삭제'
            }

            # 각 이벤트의 bar series 생성
            series_list = []
            for event in events_to_consider:
                bar_set = QBarSet(event_legend_mapping.get(event, event))  # 범례
                for formatted_date, event_counts in result_dict.items():
                    bar_set.append(event_counts[event])
                series = QBarSeries()
                series.append(bar_set)
                series_list.append(series)

            # Create a chart and set the series
            chart = QChart()
            for series in series_list:
                chart.addSeries(series)

            chart.setAnimationOptions(QChart.SeriesAnimations)
            chart.legend().setVisible(True)

            # 가로축 (날짜)
            datetime_axis = QBarCategoryAxis()
            datetime_axis.append(result_dict.keys())  # Use the keys (dates) directly
            chart.addAxis(datetime_axis, Qt.AlignBottom)

            # 세로축
            value_axis = QValueAxis()  # 세로축 객체
            value_axis.setTickCount(5)  # 세로축 눈금 개수
            chart.addAxis(value_axis, Qt.AlignLeft)

            # Set the range for the vertical axis
            min_value = 0
            max_value = max(max(event_counts.values()) for event_counts in
                            result_dict.values())  # Use the maximum value among all events
            value_axis.setRange(min_value, max_value)  # 세로축의 범위 설정

            # layout
            self.button_layout.addWidget(self.show_daily_button, 1)
            self.button_layout.addWidget(self.show_monthly_button, 1)
            self.button_layout.addWidget(self.show_yearly_button, 1)
            self.log_layout.addLayout(self.button_layout, 1)

            log_graph_widget = QChartView(chart)
            log_graph_widget.setStyleSheet("background-color: white")
            self.log_layout.addWidget(log_graph_widget, 10)

            self.hexLayout.addLayout(self.log_layout, 10)
            self.rightLayout.addLayout(self.hexLayout, 2)

        except Exception as e:
            print(f"An error occurred in show_graph(): {e}")

    def process_log_list(self, db_filepath):
        try:
            print("process_log()")
            # SQLite DB 연결 생성
            connection = sqlite3.connect(db_filepath)
            cursor = connection.cursor()

            # LOG 테이블 데이터 검색
            query = "SELECT * FROM LOG"
            cursor.execute(query)
            rows = cursor.fetchall()  # 각 행 rows 리스트에 저장

            # 기존 데이터 제거
            self.model.removeRows(0, self.model.rowCount())

            # 모든 데이터 처리
            for row_index, row in enumerate(rows):
                for col, value in enumerate(row):
                    # print(f"Processing column {col}: {value}")
                    item = QStandardItem()
                    if col == 0:  # index -> int
                        item.setData(int(value), Qt.DisplayRole)  # Qt.DisplayRole: 모델 데이터를 표시할 때 사용
                    else:
                        item.setData(value, Qt.DisplayRole)

                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)  # 편집 불가능 플래그 설정
                    item.setTextAlignment(Qt.AlignCenter)
                    self.model.setItem(row_index, col, item)

            connection.close()
        except Exception as e:
            print(f"An error occurred in process_log(): {e}")

    def clear_hex_layout(self):
        # hexLayout 내부의 모든 위젯을 제거
        while self.hexLayout.count():
            item = self.hexLayout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
            else:
                layout = item.layout()
                self.clear_layout(layout)
                layout.setParent(None)

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
            else:
                self.clear_layout(item.layout())

    # ======================= 6. Associated scan =========================
    def update_associated_scan(self):
        try:
            print("update_associated_scan()")

            self.model.clear()
            self.model.setColumnCount(15)  # 모델 컬럼 수 설정
            self.model.setHorizontalHeaderLabels(
                ["Index", "Event", "Block", "Channel", "Start time", "End time", "Duration", "Start offset",
                 "End offset", "Size", "Del type", "I-frame", "P-frame", "Is it del", "Association type"])
            self.blocktable.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)  # 사용자 조절 가능
            self.blocktable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
            self.blocktable.horizontalHeader().resizeSection(0, 60)
            self.blocktable.horizontalHeader().resizeSection(1, 250)
            self.blocktable.horizontalHeader().resizeSection(4, 140)
            self.blocktable.horizontalHeader().resizeSection(5, 140)

            db_filepath = './IDIS_FS_sqlite.db'
            self.process_associated_scan(db_filepath) # db 접근

        except Exception as e:
            print(f"An error occurred in update_associated_scan(): {e}")

    def process_associated_scan(self, db_filepath):
        try:
            print("process_associated_scan()")

            connection = sqlite3.connect(db_filepath)
            cursor = connection.cursor()

            query = "SELECT * FROM ASSOCIATION"
            cursor.execute(query)
            rows = cursor.fetchall()  # 각 행 rows 리스트에 저장

            # 필터링 행 추가
            for col in range(self.model.columnCount()):  # 모델 열 개수
                item = QStandardItem("")  # 각 열에 해당하는 새로운 아이템 생성
                item.setFlags(Qt.ItemIsEditable | Qt.ItemIsEnabled)  # 편집 가능하고 활성화
                self.model.setItem(0, col, item)  # 모델 첫번째 행에 해당하는 각 열에 아이템 설정

            # Filtering 버튼 추가
            search_button = QPushButton("Search")
            self.blocktable.setIndexWidget(self.model.index(0, 0), search_button)
            search_button.clicked.connect(self.as_onFilteringBtnClicked)

            # 모든 데이터 처리
            for row_index, row in enumerate(rows):
                self.model.insertRow(self.model.rowCount())  # 새로운 행 삽입
                search_item = QStandardItem()  # 아이템 생성
                search_item.setTextAlignment(Qt.AlignCenter)  # 가운데 정렬
                self.model.setItem(self.model.rowCount() - 1, 0, search_item)  # 첫 번째 열에 추가

                for col, value in enumerate(row):
                    item = QStandardItem()
                    if col == 0:  # index -> int
                        item.setData(int(value), Qt.DisplayRole)  # Qt.DisplayRole: 모델 데이터를 표시할 때 사용
                    elif col == 10:  # del_type 매칭
                        if value == 0:
                            output_text = '할당'
                        elif value == 1:
                            output_text = '부분 삭제'
                        elif value == 2:
                            output_text = '모든 데이터 삭제'  # 바꿔야 함
                        elif value == 3:
                            output_text = '포맷'
                        elif value == 4:
                            output_text = '슬랙'
                        else:
                            output_text = ''
                        item.setData(output_text, Qt.DisplayRole)
                    else:
                        item.setData(value, Qt.DisplayRole)

                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)  # 편집 불가능 플래그 설정
                    item.setTextAlignment(Qt.AlignCenter)

                    # Association type 값이 0인 경우 1번째부터 4번째 컬럼을 병합
                    if col == 14 and value == 0:
                        self.blocktable.setSpan(row_index, 1, 1, 4)

                    self.model.setItem(row_index, col, item)

            connection.close()
        except Exception as e:
            print(f"An error occurred in process_associated_scan(): {e}")

    def as_onFilteringBtnClicked(self):
        print("Filtering button clicked")
        self.as_filtering_method()

    # 필터링 데이터 전달
    def as_filtering_method(self):
        try:
            # 실제 데이터 추출
            filter_index = self.model.item(0, 0).data(Qt.DisplayRole)
            filter_event = self.model.item(0, 1).data(Qt.DisplayRole)
            filter_block = self.model.item(0, 2).data(Qt.DisplayRole)
            filter_channel = self.model.item(0, 3).data(Qt.DisplayRole)
            filter_start_time = self.model.item(0, 4).data(Qt.DisplayRole)
            filter_end_time = self.model.item(0, 5).data(Qt.DisplayRole)
            filter_duration = self.model.item(0, 6).data(Qt.DisplayRole)
            filter_start_offset = self.model.item(0, 7).data(Qt.DisplayRole)
            filter_end_offset = self.model.item(0, 8).data(Qt.DisplayRole)
            filter_size = self.model.item(0, 9).data(Qt.DisplayRole)
            filter_del_type = self.model.item(0, 10).data(Qt.DisplayRole)
            filter_iframe = self.model.item(0, 11).data(Qt.DisplayRole)
            filter_pframe = self.model.item(0, 12).data(Qt.DisplayRole)

            if filter_block == '' and filter_channel == '' and filter_start_time == '' and filter_end_time == '' and filter_del_type == '':
                pass
            else:
                print("hi")
                self.filtered_data(filter_block, filter_channel, filter_start_time, filter_end_time, filter_del_type)

        except Exception as e:
            print(f"filtering_method() exception occurred: {e}")

    # 필터링 결과 출력
    def as_filtered_data(self, filter_block, filter_channel, filter_start_time, filter_end_time, filter_del_type):
        try:
            connection = sqlite3.connect('./IDIS_FS_sqlite.db')
            cursor = connection.cursor()

            # Channel 및 Block 열에서 filter_channel과 filter_block과 일치하는 행을 가져옴
            query = f"SELECT * FROM ASSOCIATION WHERE"
            if filter_block != '':
                query += f" NAME = '{filter_block}' OR"
            if filter_channel != '':
                query += f" CH = '{filter_channel}' OR"
            if filter_start_time != '':
                query += f" START_TIME LIKE '%{filter_start_time}%' OR"
            if filter_end_time != '':
                query += f" END_TIME LIKE '%{filter_end_time}%' OR"
            if filter_del_type != '':
                query += f" DEL_TYPE LIKE '%{filter_del_type}%' OR"
            query = query.rstrip(" OR")

            cursor.execute(query)
            rows = cursor.fetchall()  # 각 행이 result 리스트에 저장됨

            connection.close()

            # 결과를 모델에 추가하기 전에 기존 데이터 제거
            self.model.clear()
            self.model.setColumnCount(15)  # 모델 컬럼 수 설정
            self.model.setHorizontalHeaderLabels(
                ["Index", "Event", "Block", "Channel", "Start time", "End time", "Duration", "Start offset",
                 "End offset", "Size", "Del type", "I-frame", "P-frame", "Is it del", "Association type"])
            self.blocktable.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)  # 사용자 조절 가능
            self.blocktable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
            self.blocktable.horizontalHeader().resizeSection(0, 60)
            self.blocktable.horizontalHeader().resizeSection(1, 250)
            self.blocktable.horizontalHeader().resizeSection(4, 140)
            self.blocktable.horizontalHeader().resizeSection(5, 140)

            # 테이블 상단에 필터링 행 추가
            for col in range(self.model.columnCount()):  # 모델 열 개수
                item = QStandardItem("")  # 각 열에 해당하는 새로운 아이템 생성
                item.setFlags(Qt.ItemIsEditable | Qt.ItemIsEnabled)  # 편집 가능하고 활성화
                self.model.setItem(0, col, item)  # 모델 첫번째 행에 해당하는 각 열에 아이템 설정

            # Filtering 버튼 추가
            Filtering_btn = QPushButton("Search")
            self.blocktable.setIndexWidget(self.model.index(0, 0), Filtering_btn)
            Filtering_btn.clicked.connect(self.onFilteringBtnClicked)

            # 결과를 모델에 추가
            for row_index, row in enumerate(rows):
                self.model.insertRow(self.model.rowCount())  # 새로운 행 삽입

                for col, value in enumerate(row):
                    item = QStandardItem()  # 항상 문자열이 들어가야
                    if col == 0:  # index와 name에 대한 값들은 int로 설정
                        item.setData(int(value), Qt.DisplayRole)  # Qt.DisplayRole: 모델 데이터를 표시할 때 사용
                    elif col == 10:  # del_type 매칭
                        if value == 0:
                            output_text = '할당'
                        elif value == 1:
                            output_text = '부분 삭제'
                        elif value == 2:
                            output_text = '모든 데이터 삭제'  # 바꿔야 함
                        elif value == 3:
                            output_text = '포맷'
                        elif value == 4:
                            output_text = '슬랙'
                        else:
                            output_text = ''
                        item.setData(output_text, Qt.DisplayRole)
                    else:
                        item.setData(value, Qt.DisplayRole)
                    item.setFlags(item.flags() ^ Qt.ItemIsEditable)  # 편집 불가능 플래그 설정
                    item.setTextAlignment(Qt.AlignCenter)

                    # Association type 값이 0인 경우 1번째부터 4번째 컬럼을 병합
                    if col == 14 and value == 0:
                        self.blocktable.setSpan(row_index, 1, 1, 4)

                    self.model.setItem(row_index, col, item)


        except Exception as e:
            print(f"filtered_data() exception occurred: {e}")

    # ======================= Tree =========================
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
                    self.update_precise_scan()

                elif selected_name == "Allocated":
                    self.update_allocated()

                elif selected_name == "Unallocated":
                    self.update_unallocated()

                elif selected_name == "Log":
                    self.open_logfile()  # 최초만 !

                elif selected_name == "Associated Scan":
                    self.update_associated_scan()

            except Exception as e:
                print(f"An error occurred in on_tree_select: {e}")

        else:
            # 아무 항목도 선택하지 않은 경우 처리
            pass

    '''
    # ======================= Hex Window =========================
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
    '''

    # ======================= Warning =========================
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
        self.filepath = filepath

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
            # 비활성화 처리
            for i in range(selected_item.childCount()):
                child_item = selected_item.child(i)
                child_item.setFlags(child_item.flags() & ~Qt.ItemIsEnabled)

        else:
            print("User clicked No. Cancelling precise scan.")

    def show_warning_message_log(self, db_filepath):
        # Add a warning message
        warning_message = QMessageBox()
        warning_message.setIcon(QMessageBox.Warning)
        warning_message.setText("연관 분석을 진행하시겠습니까? (시간이 오래 소요될 수 있습니다.)")
        warning_message.setWindowTitle("연관 분석")
        warning_message.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        warning_message.setDefaultButton(QMessageBox.Yes)

        # 버튼 클릭과 on_warning_button_clicked() 연결
        warning_message.buttonClicked.connect(self.on_warning_button_clicked)

        # 실행
        result = warning_message.exec_()

        # 트리에 파일 이름이 존재하는지 확인
        items_with_filename = self.tree.findItems(self.filename, Qt.MatchExactly, 0)
        selected_item = items_with_filename[0]

        # 트리 아이템 추가
        associated_item = QTreeWidgetItem()
        associated_item.setText(0, "Associated Scan")

        selected_item.addChild(associated_item)
        selected_item.setExpanded(True)

        QApplication.processEvents()  # Force UI to update instantly

        if result == QMessageBox.Yes:
            print("User clicked Yes. Proceeding with associated scan.")
            as_instance = Association(db_filepath)
            as_instance.parse()

        elif result == QMessageBox.No:
            pass

        else:
            print("User clicked No. Cancelling associated scan.")

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
