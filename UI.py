import sys
import struct
import datetime
from Allocated import Allocated
from PyQt5.QtWidgets import (QApplication, QMainWindow, QMenuBar, QAction, QTreeView, QTreeWidget, QTreeWidgetItem,
                             QTableWidget, QTableWidgetItem, QLabel, QTextEdit, QVBoxLayout, QHBoxLayout,
                             QWidget, QFileDialog, QMessageBox, QGridLayout, QHeaderView)
from PyQt5.QtCore import Qt
import sqlite3


class UI_main(QMainWindow):
    def __init__(self):
        super().__init__() # QMainWindow 클래스의 초기화를 수행함. 즉 QMainWindow의 초기화를 호출

        self.files = {}  # 파일 경로와 트리 항목(ID)을 저장하는 딕셔너리. 현재 클래스의 인스턴스 변수로, 빈 딕셔너리로 초기화
        self.initUI()

    def initUI(self):
        self.setWindowTitle("IDIS DVR Analyzer")
        self.setGeometry(100, 100, 1000, 600) # x, y 좌표, 가로, 세로 크기

        # Main widget and layout
        mainWidget = QWidget(self)
        self.setCentralWidget(mainWidget)
        mainLayout = QHBoxLayout(mainWidget)

        # Left tree view
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel('DVR Images')
        # self.tree.itemSelectionChanged.connect(self.on_tree_select)
        mainLayout.addWidget(self.tree, 1)

        # Center table view
        self.listbox = QTableWidget()
        self.listbox.setColumnCount(9) # 9개 컬럼
        self.listbox.setHorizontalHeaderLabels(
            ["Index", "Name", "Channel", "Start Time", "End Time", "Total Time", "Start Offset", "End Offset", "Size"])
        self.listbox.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.listbox.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        mainLayout.addWidget(self.listbox, 4)

        # Right preview label
        self.preview = QLabel("Preview")
        mainLayout.addWidget(self.preview, 1)

        # Bottom hex display
        self.hex_display = QTextEdit()
        mainLayout.addWidget(self.hex_display, 1)

        # 메뉴바 생성 함수 불러오기
        self._create_menubar()

    def _create_menubar(self):
        menubar = self.menuBar()

        fileMenu = menubar.addMenu('File')
        loadAction = QAction('Load Image', self)
        loadAction.triggered.connect(self.open_image) # open_image 함수
        fileMenu.addAction(loadAction)

        # Other menu actions...
        # ...

    def open_image(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Open file", "", "All Files (*)")
        df = Allocated(filepath)  # 추가

        if df.check_G2FDb() == 0:
            print("Invalid G2FDb image file. Exiting.")
            sys.exit()  # 프로그램 종료

        if filepath:
            filename = filepath.split("/")[-1] # 경로에서 파일 이름만 추출
            item = QTreeWidgetItem(self.tree)
            item.setText(0, filename) # 파일명을 트리에 추가
            self.files[filepath] = item

            db_filepath = './IDIS_FS_sqlite.db'

            self.process_file(db_filepath) # 파일 처리 메서드 호출
            self.update_preview(db_filepath) # 미리보기 메서드 호출

        df.analyzer()

    def process_file(self, db_filepath):
        self.listbox.setRowCount(0)

        # Connect to the SQLite database
        connection = sqlite3.connect(db_filepath)
        cursor = connection.cursor()


        # Query to retrieve data from the allocation table
        query = "SELECT * FROM ALLOCATION"
        cursor.execute(query)


        for row in cursor.fetchall():
            print(row[0])
            index = row[0]  # Assuming the first column is the block number
            name = row[1]  # Assuming the second column is the channel number
            channel = row[2]  # Assuming the third column is the start time in hexadecimal format
            start_time = row[3]  # Assuming the fourth column is the end time in hexadecimal format
            end_time = row[4]  # Assuming the seventh column is the current offset
            total_time = row[5]
            start_offset = row[6]
            end_offset = row[7]
            size = row[8]

            rowPosition = self.listbox.rowCount()
            self.listbox.insertRow(rowPosition)
            self.listbox.setItem(rowPosition, 0, QTableWidgetItem(index))
            self.listbox.setItem(rowPosition, 1, QTableWidgetItem(name))
            self.listbox.setItem(rowPosition, 2, QTableWidgetItem(channel))
            self.listbox.setItem(rowPosition, 3, QTableWidgetItem(start_time))
            self.listbox.setItem(rowPosition, 4, QTableWidgetItem(end_time))
            self.listbox.setItem(rowPosition, 5, QTableWidgetItem(total_time))
            self.listbox.setItem(rowPosition, 6, QTableWidgetItem(start_offset))
            self.listbox.setItem(rowPosition, 7, QTableWidgetItem(end_offset))
            self.listbox.setItem(rowPosition, 8, QTableWidgetItem(size))

        # Close the database connection
        connection.close()

    def update_preview(self, image_path):
        # Image loading and updating preview...
        pass

    def on_tree_select(self):
        selected_items = self.tree.selectedItems()
        if selected_items:
            selected_item = selected_items[0]
            for filepath, item in self.files.items():
                if item == selected_item:
                    self.process_file(filepath)
                    break

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
        s_datetime = datetime.datetime.strptime(start, '%Y년 %m월 %d일 %H:%M:%S')
        e_datetime = datetime.datetime.strptime(end, '%Y년 %m월 %d일 %H:%M:%S')

        diff = e_datetime - s_datetime
        return str(diff)


if __name__ == '__main__':
    app = QApplication(sys.argv) # PyQt 애플리케이션을 시작하기 위해 PyQt의 QApplication 클래스를 인스턴스화합니다. sys.argv는 명령행 인수를 전달하는데 사용되며, PyQt 애플리케이션에서는 필수 요소입니다.
    ex = UI_main() # UI_main 클래스의 인스턴스를 생성합니다. 이것은 PyQt에서 사용자 인터페이스를 정의하는 클래스일 것으로 예상됩니다.
    ex.show() # 생성된 UI의 화면을 표시합니다. PyQt 애플리케이션에서는 이 메서드를 호출하여 UI를 사용자에게 보여줍니다.
    sys.exit(app.exec_()) # app.exec_() 메서드는 PyQt 애플리케이션의 메인 이벤트 루프를 시작합니다. 애플리케이션이 실행 중일 때는 사용자 입력 및 이벤트를 처리하고 윈도우를 업데이트합니다.sys.exit()는 app.exec_()가 종료되면 애플리케이션을 종료하는데 사용됩니다. 이 부분이 없으면 애플리케이션이 종료되지 않을 수 있습니다.
