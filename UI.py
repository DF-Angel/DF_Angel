import sys
import struct
import datetime
from Allocated import Allocated
from PyQt5.QtWidgets import (QApplication, QMainWindow, QMenuBar, QAction, QTreeView, QTreeWidget, QTreeWidgetItem,
                             QTableWidget, QTableWidgetItem, QLabel, QTextEdit, QVBoxLayout, QHBoxLayout,
                             QWidget, QFileDialog, QMessageBox, QGridLayout, QHeaderView)
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
import sqlite3

class UI_main(QMainWindow):
    def __init__(self):
        super().__init__() # QMainWindow 클래스의 초기화를 수행함. 즉 QMainWindow의 초기화를 호출

        self.files = {}  # 파일 경로와 트리 항목(ID)을 저장하는 딕셔너리. 현재 클래스의 인스턴스 변수로, 빈 딕셔너리로 초기화
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("IDIS DVR Analyzer")
        self.setGeometry(100, 100, 1000, 600) # x, y 좌표, 가로, 세로 크기

        # Main widget and layout
        mainWidget = QWidget(self)
        self.setCentralWidget(mainWidget)
        mainLayout = QHBoxLayout(mainWidget)

        # Left tree view
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel('IDIS DVR Images')
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

        # 메뉴바 생성 함수 호출
        self._create_menubar()

    def _create_menubar(self):
        menubar = self.menuBar() # 현재 윈도우에 대한 메뉴바 가져옴 / self: 현재 클래스의 인스턴스

        fileMenu = menubar.addMenu('File')
        loadAction = QAction('Load Image', self)
        loadAction.triggered.connect(self.open_image) # Load Image 액션의 트리거 시그널이 발생 시 self.open_image 메서드 호출
        fileMenu.addAction(loadAction) # "File" 메뉴에 방금 생성한 "Load Image" 액션을 추가

        # Other menu actions...

    def open_image(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Open file", "", "All Files (*)")  # 이미지 파일 선택, filepath에 경로 저장

        try:
            df = Allocated(filepath)  # Allocated()에 경로 넘기고 객체로 받기

            if df.check_G2FDb() == 0:  # 파일이 정상적으로 열렸는지 확인
                print("Invalid G2FDb image file. Exiting.")
                sys.exit()  # 프로그램 종료

            df.analyzer()  # Allocated 클래스의 analyzer 메소드 호출해 파일 분석, db 생성

            if filepath:
                filename = filepath.split("/")[-1]  # 경로에서 파일 이름만 추출
                item = QTreeWidgetItem(self.tree)
                item.setText(0, filename)  # 파일명을 트리에 추가
                self.files[filepath] = item  # self.files 딕셔너리에 선택된 파일의 경로와 해당 트리 뷰 항목을 연결하여 저장

            db_filepath = './IDIS_FS_sqlite.db'
            self.process_file(db_filepath)  # 파일 처리 메서드 호출
            # self.update_preview(db_filepath) # 미리보기 메서드 호출

        except Exception as e:
            print(f"An error occurred: {e}")

    def process_file(self, db_filepath):
        self.listbox.setRowCount(0)

        # Connect to the SQLite database
        connection = sqlite3.connect(db_filepath)
        cursor = connection.cursor()

        # Query to retrieve data from the allocation table
        query = "SELECT * FROM ALLOCATION"
        cursor.execute(query)

        for row in cursor.fetchall():
            index = row[0]
            name = row[1]
            channel = row[2]
            # print(channel)
            start_time = row[3]
            end_time = row[4]
            total_time = row[5]
            start_offset = row[6]
            end_offset = row[7]
            size = row[8]

            rowPosition = self.listbox.rowCount()
            self.listbox.insertRow(rowPosition)
            self.listbox.setItem(rowPosition, 0, QTableWidgetItem(str(index)))
            self.listbox.setItem(rowPosition, 1, QTableWidgetItem(name))
            self.listbox.setItem(rowPosition, 2, QTableWidgetItem(str(channel)))
            self.listbox.setItem(rowPosition, 3, QTableWidgetItem(start_time))
            self.listbox.setItem(rowPosition, 4, QTableWidgetItem(end_time))
            self.listbox.setItem(rowPosition, 5, QTableWidgetItem(total_time))
            self.listbox.setItem(rowPosition, 6, QTableWidgetItem(str(start_offset)))
            self.listbox.setItem(rowPosition, 7, QTableWidgetItem(str(end_offset)))
            self.listbox.setItem(rowPosition, 8, QTableWidgetItem(str(size)))

        # Close the database connection
        connection.close()

    # 미리보기
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

if __name__ == '__main__':
    app = QApplication(sys.argv) # PyQt 애플리케이션 시작위해 PyQt의 QApplication 클래스를 인스턴스화
    ex = UI_main() # UI_main 클래스의 인스턴스를 생성합니다. 이것은 PyQt에서 사용자 인터페이스를 정의하는 클래스일 것으로 예상됩니다.
    ex.show() # 생성된 UI의 화면을 표시합니다. PyQt 애플리케이션에서는 이 메서드를 호출하여 UI를 사용자에게 보여줍니다.
    sys.exit(app.exec_())
