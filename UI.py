import binascii
import sys
import struct
import datetime
import textwrap

from Root_Scan import Root_Scan
from PyQt5.QtWidgets import (QApplication, QMainWindow, QMenuBar, QAction, QTreeView, QTreeWidget, QTreeWidgetItem,
                             QTableWidget, QTableWidgetItem, QLabel, QTextEdit, QVBoxLayout, QHBoxLayout,
                             QWidget, QFileDialog, QMessageBox, QGridLayout, QHeaderView, QTextBrowser, QTableView, 
                             QCalendarWidget, QDialog, QPushButton, QInputDialog, QTimeEdit, QLineEdit, QFormLayout)             
from PyQt5.QtCore import Qt, QSortFilterProxyModel, QTime, QDateTime, QRegExp, pyqtSignal, QSortFilterProxyModel
import sqlite3
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QRegExpValidator

class CustomSortFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, *args, **kwargs):
        super(CustomSortFilterProxyModel, self).__init__(*args, **kwargs)
        self.start_datetime = None
        self.end_datetime = None
    
    def set_date_range(self, start_datetime, end_datetime):
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        if not self.start_datetime or not self.end_datetime:
            return True
        
        index = self.sourceModel().index(source_row, 3, source_parent)
        data = self.sourceModel().data(index)
        row_datetime = QDateTime.fromString(data, 'yyyy-MM-dd HH:mm:ss')

        return self.start_datetime <= row_datetime <= self.end_datetime

class UI_main(QMainWindow):
    def __init__(self):  # 생성자
        super().__init__()  # QMainWindow 초기화 호출

        # 정렬 기능 위한
        self.model = QStandardItemModel()
        self.proxy_model = CustomSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.blocktable = QTableView()  # QTableView로 수정
        self.blocktable.setModel(self.proxy_model)

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

        self.model = QStandardItemModel()  # 모델을 새로 생성합니다.
    
        # 'Index' 열 헤더를 설정합니다.
        index_header_item = QStandardItem("Index")
        index_header_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.model.setHorizontalHeaderItem(0, index_header_item)
    
        # 나머지 열 헤더를 설정합니다.
        for col, label in enumerate(["Block", "Channel", "Start Time", "End Time", "Start Offset", "End Offset", "Size"], start=1):
            header_item = QStandardItem(label)
            header_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.model.setHorizontalHeaderItem(col, header_item)   
        self.blocktable.setModel(self.model) # 테이블 뷰에 모델을 설정

        self.blocktable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.blocktable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.blocktable.verticalHeader().setVisible(False)  # Hide the vertical header
        mainLayout.addWidget(self.blocktable, 1)  # 일단 1로

        # 각 컬럼 헤더를 클릭했을 때 정렬 기능 추가
        self.blocktable.setSortingEnabled(True)

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

    def _create_menubar(self):
        menubar = self.menuBar()  # 현재 윈도우에 대한 메뉴바 가져옴 / self: 현재 클래스의 인스턴스

        # File
        fileMenu = menubar.addMenu('File')
        loadAction = QAction('Load Image', self)
        loadAction.triggered.connect(self.open_image)  # Load Image 액션의 트리거 시그널이 발생 시 self.open_image 메서드 호출
        fileMenu.addAction(loadAction)  # "File" 메뉴에 방금 생성한 "Load Image" 액션을 추가

        # Search
        searchMenu = menubar.addMenu('Search')

        # Analysis
        analysisMenu = menubar.addMenu('Analysis')
        filterAction = QAction('Filter', self) #필터 기능 추가
        filterAction.triggered.connect(self.open_calendar_to_filter)
        analysisMenu.addAction(filterAction)

        # Help
        helpMenu = menubar.addMenu('Help')

        # About
        aboutMenu = menubar.addMenu('About')

    def open_image(self):
        try:
            filepath, _ = QFileDialog.getOpenFileName(self, "Open file", "", "All Files (*)")  # filepath에 경로 저장

            self.filename = filepath.split("/")[-1]  # 경로에서 파일 이름만 추출해 전역변수 저장

            df = Root_Scan(filepath)  # Root_Scan()에 경로 넘기고 객체로 받기

            if df.check_G2FDb() == 0:  # 파일이 정상적으로 열렸는지 확인
                print("Invalid G2FDb image file. Exiting.")
                sys.exit()  # 프로그램 종료

            df.analyzer()  # Root_Scan 클래스의 analyzer 메소드 호출해 파일 분석, db 생성

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
            self.process_file(db_filepath)  # 파일 처리 메서드 호출
            self.show_warning_message(filepath)

            self.Root_Scan(filepath)

        except Exception as e:
            print(f"An error occurred in open_image: {e}")

    def open_calendar_to_filter(self): #필터링 하고 싶은 날짜 입력받기
        self.calendar_dialog = QDialog(self)
        self.calendar_dialog.setWindowTitle('Select Date Range')

        layout = QVBoxLayout(self.calendar_dialog)

        self.calendar = QCalendarWidget(self.calendar_dialog)
        self.calendar.setGridVisible(True)
        layout.addWidget(self.calendar)

        self.next_button = QPushButton('Next', self.calendar_dialog)
        layout.addWidget(self.next_button)

        self.next_button.clicked.connect(self.get_time_range)

        self.calendar_dialog.exec_()

    def get_time_range(self): #필터링 하고 싶은 시간대 입력받기
        self.calendar_dialog.accept() #캘린더 닫기

        self.time_range_dialog = QDialog(self)
        self.time_range_dialog.setWindowTitle('Enter Time Range')

        form_layout = QFormLayout(self.time_range_dialog)

        # 정규 표현식으로 시간, 분, 초의 범위를 제한합니다
        hour_regexp = QRegExp("([01]?[0-9]|2[0-3])")
        min_sec_regexp = QRegExp("[0-5]?[0-9]")

        # QLineEdit 위젯 생성 및 범위 제한을 위한 Validator 설정
        self.start_time_h_edit = QLineEdit()
        self.start_time_h_edit.setValidator(QRegExpValidator(hour_regexp))
        self.start_time_m_edit = QLineEdit()
        self.start_time_m_edit.setValidator(QRegExpValidator(min_sec_regexp))
        self.start_time_s_edit = QLineEdit()
        self.start_time_s_edit.setValidator(QRegExpValidator(min_sec_regexp))

        self.end_time_h_edit = QLineEdit()
        self.end_time_h_edit.setValidator(QRegExpValidator(hour_regexp))
        self.end_time_m_edit = QLineEdit()
        self.end_time_m_edit.setValidator(QRegExpValidator(min_sec_regexp))
        self.end_time_s_edit = QLineEdit()
        self.end_time_s_edit.setValidator(QRegExpValidator(min_sec_regexp))

        # 시간 입력을 위한 QHBoxLayout 생성
        start_time_layout = QHBoxLayout()
        start_time_layout.addWidget(self.start_time_h_edit)
        start_time_layout.addWidget(QLabel(":"))
        start_time_layout.addWidget(self.start_time_m_edit)
        start_time_layout.addWidget(QLabel(":"))
        start_time_layout.addWidget(self.start_time_s_edit)

        end_time_layout = QHBoxLayout()
        end_time_layout.addWidget(self.end_time_h_edit)
        end_time_layout.addWidget(QLabel(":"))
        end_time_layout.addWidget(self.end_time_m_edit)
        end_time_layout.addWidget(QLabel(":"))
        end_time_layout.addWidget(self.end_time_s_edit)

        # form_layout에 시간 입력 QHBoxLayout 추가
        form_layout.addRow('Start Time (HH:MM:SS):', start_time_layout)
        form_layout.addRow('End Time (HH:MM:SS):', end_time_layout)

        # 사용자가 시간 범위를 제출할 수 있는 버튼 생성
        submit_button = QPushButton('Submit', self.time_range_dialog)
        submit_button.clicked.connect(self.submit_time_range)
        form_layout.addWidget(submit_button)

        self.time_range_dialog.setLayout(form_layout)
        self.time_range_dialog.exec_()

    def submit_time_range(self):
        # QLineEdit 위젯에서 텍스트를 가져와서 시간 문자열을 만듭니다
        start_time = f"{self.start_time_h_edit.text()}:{self.start_time_m_edit.text()}:{self.start_time_s_edit.text()}"
        end_time = f"{self.end_time_h_edit.text()}:{self.end_time_m_edit.text()}:{self.end_time_s_edit.text()}"

        # 선택된 날짜와 시간 문자열로 QDateTime 객체를 만듭니다
        selected_date = self.calendar.selectedDate()
        filter_start_datetime = QDateTime(selected_date, QTime.fromString(start_time, 'HH:mm:ss'))
        filter_end_datetime = QDateTime(selected_date, QTime.fromString(end_time, 'HH:mm:ss'))

        # 생성된 QDateTime 객체의 유효성을 검사하고 필터링을 수행합니다
        if filter_start_datetime.isValid() and filter_end_datetime.isValid():
            self.filter_data_by_datetime(filter_start_datetime, filter_end_datetime)
            self.time_range_dialog.accept()
        else:
            # 유효하지 않은 입력에 대한 처리를 합니다
            # 여기에 에러 메시지를 표시하거나 사용자에게 다시 입력하도록 요청할 수 있습니다
            pass 


    def filter_data_by_datetime(self, filter_start_datetime, filter_end_datetime):
        self.proxy_model.set_date_range(filter_start_datetime, filter_end_datetime)
        # self.model이 데이터를 포함하고 있는 QStandardItemModel이라고 가정
        for row in range(self.model.rowCount()):
            row_start_time = self.model.item(row, 3).text()
            row_start_datetime = QDateTime.fromString(row_start_time, 'yyyy-MM-dd HH:mm:ss')

            if filter_start_datetime <= row_start_datetime <= filter_end_datetime:
                self.model.item(row).setVisible(True)
            else:
                self.model.item(row).setVisible(False)


    # 트리에서 파일명 클릭 시
    def Root_Scan(self, filepath):
        print("again Root_Scan")

        self.model.setColumnCount(8)  # 모델에 있는 컬럼 수 설정
        self.model.setHorizontalHeaderLabels(
            ["Index", "Block", "Channel", "Start Time", "End Time", "Start Offset", "End Offset", "Size"])
        self.blocktable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.blocktable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)

        db_filepath = './IDIS_FS_sqlite.db'
        self.process_file(db_filepath)  # 파일 처리 메서드 호출

    def process_file(self, db_filepath):
        # SQLite DB와 연결 생성
        connection = sqlite3.connect(db_filepath)
        cursor = connection.cursor()

        # ROOTSCAN 테이블에 쿼리 실행 및 결과 받기
        query = "SELECT * FROM ROOT_SCAN"
        cursor.execute(query)

        self.model.removeRows(0, self.model.rowCount())  # Clear existing data

        for row in cursor.fetchall():
            index = int(row[0]) # 문자열로 하면 정렬이 안돼서 정수로 변환
            name = row[1]
            channel = row[2]
            start_time = row[3]
            end_time = row[4]
            start_offset = row[5]
            end_offset = row[6]
            size = row[7]

            self.model.insertRow(self.model.rowCount())  # Insert a new row

            for col, value in enumerate([index, name, channel, start_time, end_time, start_offset, end_offset, size]):
                if col == 0:
                    item = QStandardItem()
                    item.setData(value, Qt.DisplayRole)
                else:
                    item = QStandardItem(str(value))
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                self.model.setItem(self.model.rowCount() - 1, col, item)  # Set data in the last row

        # Close the database connection
        connection.close()

    def update_preview(self, image_path):
        # Image loading and updating preview...
        pass

    def on_tree_select(self):
        selected_items = self.tree.selectedItems()  # 현재 선택된 항목의 목록 가져오기

        ''' 위랑 중복이라 일단 주석 / 트리 항목 선택하면 뭐 보여줄 지? 우클릭해서 정밀 검색하도록? 
        if selected_items:
            selected_item = selected_items[0]
            for filepath, item in self.files.items():
                if item == selected_item:
                    with open(filepath, 'rb') as file:
                        hex_value = file.read(5000).hex()
                        formatted_hex_lines = self.format_hex_lines(hex_value)  # 포맷된 라인 리스트로 받음

                        self.display_hex_value(formatted_hex_lines)
                        self.update_hex_offset(formatted_hex_lines)
                        self.display_ascii(formatted_hex_lines) #
                    break '''

        if selected_items:
            selected_item = selected_items[0]
            selected_name = selected_item.text(0)

            if selected_name == "Precise Scan":
                # "Precise Scan" 항목을 선택한 경우 오른쪽 측면을 업데이트하는 메서드 호출
                self.update_right_side_for_precise_scan()
                print(self.files)

            elif selected_name == self.filename:
                self.Root_Scan(list(self.files.keys())[0])
                print("filename selected: " + list(self.files.keys())[0])



        else:
            # 아무 항목도 선택하지 않은 경우 처리
            pass

    def update_right_side_for_precise_scan(self):
        # self.hex_display.clear() # 기존 내용 지우기
        # self.hex_offset.clear()
        # self.ascii_display.clear()

        # 오른쪽 영역 - mainLayout
        self.model.setColumnCount(14)  # 모델에 있는 컬럼 수 설정
        self.model.setHorizontalHeaderLabels(
            ["Index", "Name", "Block", "Channel", "Start Time", "End Time", "Duration", "Start Offset", "End Offset",
             "Size", "Del Type", "I-Frame", "P-Frame", "삭제 여부"])
        self.blocktable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.blocktable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)

        # 예제: "Precise Scan"을 위한 hex_display에 텍스트 설정
        # self.hex_display.setPlainText("이것은 Precise Scan 내용입니다.")

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
