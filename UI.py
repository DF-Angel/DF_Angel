import binascii
import sys
import struct
import datetime
import textwrap

from RootScan import RootScan
from PyQt5.QtWidgets import (QApplication, QMainWindow, QMenuBar, QAction, QTreeView, QTreeWidget, QTreeWidgetItem,
                             QTableWidget, QTableWidgetItem, QLabel, QTextEdit, QVBoxLayout, QHBoxLayout,
                             QWidget, QFileDialog, QMessageBox, QGridLayout, QHeaderView, QTextBrowser)
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
import sqlite3

class UI_main(QMainWindow):
    def __init__(self): # 생성자
        super().__init__() # QMainWindow 클래스의 초기화를 수행함. 즉 QMainWindow의 초기화를 호출

        self.files = {}  # 파일 경로와 트리 항목(ID)을 저장하는 딕셔너리. 현재 클래스의 인스턴스 변수로, 빈 딕셔너리로 초기화
        self.init_ui() # ui 실행 함수 호출

        # 생성자에서 itemSelectionChanged 시그널을 연결
        self.tree.itemSelectionChanged.connect(self.on_tree_select)

    def init_ui(self):
        self.setWindowTitle("IDIS DVR Analyzer by DF_Angel")
        self.setGeometry(100, 100, 1000, 600)  # x, y, 가로, 세로

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
        self.tree.setHeaderLabel('IDIS DVR Image List')
        treeLayout.addWidget(self.tree, 1)
        leftLayout.addLayout(treeLayout, 1)

        # 오른쪽 영역 - mainLayout
        self.blocktable = QTableWidget()
        self.blocktable.setColumnCount(9)  # 9개 컬럼
        self.blocktable.setHorizontalHeaderLabels(
            ["Index", "Name", "Channel", "Start Time", "End Time", "Total Time", "Start Offset", "End Offset", "Size"])
        self.blocktable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.blocktable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        mainLayout.addWidget(self.blocktable, 4)

        self.preview = QLabel("Preview")
        mainLayout.addWidget(self.preview, 1)

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
        self.hex_offset.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff) #
        hexoffsetLayout.addWidget(self.hex_offset, 8) #
        hexLayout.addLayout(hexoffsetLayout, 2)

        #====================================

        self.hex_display_header = QLabel("00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F")  # 새로운 QLabel 위젯 생성
        self.hex_display_header.setStyleSheet("background-color: white")
        hexdisplayLayout.addWidget(self.hex_display_header, 1)  #

        self.hex_display = QTextBrowser()
        self.hex_display.setStyleSheet("background-color: #CCCCCC")
        self.hex_display.setReadOnly(True) # 읽기 전용으로 설정 (편집 불가능)
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

        # Show the warning message after process_file
        # self.show_warning_message()


    def _create_menubar(self):
        menubar = self.menuBar() # 현재 윈도우에 대한 메뉴바 가져옴 / self: 현재 클래스의 인스턴스

        # File
        fileMenu = menubar.addMenu('File')
        loadAction = QAction('Load Image', self)
        loadAction.triggered.connect(self.open_image) # Load Image 액션의 트리거 시그널이 발생 시 self.open_image 메서드 호출
        fileMenu.addAction(loadAction) # "File" 메뉴에 방금 생성한 "Load Image" 액션을 추가

        # Search
        searchMenu = menubar.addMenu('Search')

        # Analysis
        analysisMenu = menubar.addMenu('Analysis')

        # Help
        helpMenu = menubar.addMenu('Help')

        # About
        aboutMenu = menubar.addMenu('About')

    def open_image(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Open file", "", "All Files (*)")  # 이미지 파일 선택, filepath에 경로 저장

        try:
            df = RootScan(filepath)  # RootScan()에 경로 넘기고 객체로 받기

            if df.check_G2FDb() == 0:  # 파일이 정상적으로 열렸는지 확인
                print("Invalid G2FDb image file. Exiting.")
                sys.exit()  # 프로그램 종료

            df.analyzer()  # RootScan 클래스의 analyzer 메소드 호출해 파일 분석, db 생성

            if filepath:
                filename = filepath.split("/")[-1]  # 경로에서 파일 이름만 추출
                item = QTreeWidgetItem(self.tree)
                item.setText(0, filename)  # 파일명을 트리에 추가
                self.files[filepath] = item  # self.files 딕셔너리에 선택된 파일의 경로와 해당 트리 뷰 항목을 연결하여 저장

            db_filepath = './IDIS_FS_sqlite.db'
            self.process_file(db_filepath)  # 파일 처리 메서드 호출
            self.show_warning_message()  # Show the warning message after process_file
            # self.update_preview(db_filepath) # 미리보기 메서드 호출

        except Exception as e:
            print(f"An error occurred: {e}")

    def process_file(self, db_filepath): # db에서 가져와서 보여주는
        self.blocktable.setRowCount(0)

        # Connect to the SQLite database
        connection = sqlite3.connect(db_filepath)
        cursor = connection.cursor()

        # Query to retrieve data from the allocation table
        query = "SELECT * FROM ROOTSCAN"
        cursor.execute(query)

        for row in cursor.fetchall():
            index = row[0]
            name = row[1]
            channel = row[2]
            start_time = row[3]
            end_time = row[4]
            start_offset = row[5]
            end_offset = row[6]
            size = row[7]

            rowPosition = self.blocktable.rowCount()
            self.blocktable.insertRow(rowPosition)
            self.blocktable.setItem(rowPosition, 0, QTableWidgetItem(str(index)))
            self.blocktable.setItem(rowPosition, 1, QTableWidgetItem(name))
            self.blocktable.setItem(rowPosition, 2, QTableWidgetItem(str(channel)))
            self.blocktable.setItem(rowPosition, 3, QTableWidgetItem(start_time))
            self.blocktable.setItem(rowPosition, 4, QTableWidgetItem(end_time))
            self.blocktable.setItem(rowPosition, 5, QTableWidgetItem(str(start_offset)))
            self.blocktable.setItem(rowPosition, 6, QTableWidgetItem(str(end_offset)))
            self.blocktable.setItem(rowPosition, 7, QTableWidgetItem(str(size)))

        # Close the database connection
        connection.close()

    def update_preview(self, image_path):
        # Image loading and updating preview...
        pass

    def on_tree_select(self):
        selected_items = self.tree.selectedItems() # 현재 선택된 항목의 목록 가져오기

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
                    break

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
            hex_offset_text += f'0x{offset:08X}\n' # offset 값을 16진수로 표현
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

    def show_warning_message(self):
        # Add a warning message
        warning_message = QMessageBox()
        warning_message.setIcon(QMessageBox.Warning)
        warning_message.setText("Warning: Performing a precise scan may take a long time.\nDo you want to proceed?")
        warning_message.setWindowTitle("Warning")
        warning_message.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        warning_message.setDefaultButton(QMessageBox.No)

        # Connect the warning message buttons to functions
        warning_message.buttonClicked.connect(self.on_warning_button_clicked)

        # Show the warning message
        result = warning_message.exec_()

        if result == QMessageBox.Yes:
            print("User clicked Yes. Proceeding with precise scan.")
            # Perform additional actions if needed after clicking Yes
        else:
            print("User clicked No. Cancelling precise scan.")
            # Perform additional actions if needed after clicking No

    def on_warning_button_clicked(self, button):
        if button.text() == "&Yes":
            print("Yes button clicked.")
        elif button.text() == "&No":
            print("No button clicked.")
        else:
            print("Unknown button clicked.")

if __name__ == '__main__':
    app = QApplication(sys.argv) # PyQt 애플리케이션 시작위해 PyQt의 QApplication 클래스를 인스턴스화
    ex = UI_main() # UI_main 클래스의 인스턴스를 생성합니다. 이것은 PyQt에서 사용자 인터페이스를 정의하는 클래스일 것으로 예상됩니다.
    ex.show() # 생성된 UI 화면 표시
    sys.exit(app.exec_())
