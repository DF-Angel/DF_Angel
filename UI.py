import binascii
import sys
import struct
import datetime
import textwrap

from Root_Scan import Root_Scan
from PyQt5.QtWidgets import (QApplication, QMainWindow, QMenuBar, QAction, QTreeView, QTreeWidget, QTreeWidgetItem,
                             QTableWidget, QTableWidgetItem, QLabel, QTextEdit, QVBoxLayout, QHBoxLayout,
                             QWidget, QFileDialog, QMessageBox, QGridLayout, QHeaderView, QTextBrowser, QTableView)
from PyQt5.QtCore import Qt, QSortFilterProxyModel
from PyQt5.QtCore import pyqtSignal
import sqlite3
from PyQt5.QtGui import QStandardItemModel, QStandardItem

class UI_main(QMainWindow):
    def __init__(self):  # 생성자
        super().__init__()  # QMainWindow 초기화 호출

        # 정렬 기능 위한
        self.model = QStandardItemModel()
        self.proxy_model = QSortFilterProxyModel()
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

        # 오른쪽 영역 - mainLayout
        # self.blocktable = QTableWidget() # 정렬 기능하려고 일단 기존 QTableWidget 주석 처리
        self.model.setColumnCount(8)  # 모델에 컬럼 추가
        self.model.setHorizontalHeaderLabels(
            ["Index", "Block", "Channel", "Start Time", "End Time", "Start Offset", "End Offset", "Size"])
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
            index = row[0]
            name = row[1]
            channel = row[2]
            start_time = row[3]
            end_time = row[4]
            start_offset = row[5]
            end_offset = row[6]
            size = row[7]

            self.model.insertRow(self.model.rowCount())  # Insert a new row

            for col, value in enumerate([index, name, channel, start_time, end_time, start_offset, end_offset, size]):
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
