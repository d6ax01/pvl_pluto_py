
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout,QTabWidget,QLabel ,QPushButton, QTextEdit, QLineEdit,QHBoxLayout,QSizePolicy,QMainWindow
from PyQt5.QtCore import QDateTime,pyqtSignal, QMutex, QObject,Qt
from PyQt5.QtGui import QTextCursor,QTextBlockFormat
from enum import Enum


class LogState(Enum):
    Fail=-1
    NoData=0
    GetData=1
    Recovery=2

class LogEntry:
    def __init__(self, text, _logState=LogState.NoData):
        self.text = text
        self.log_state = _logState
        self.timestamp = QDateTime.currentDateTime()


    def __str__(self):
        return f"[{self.timestamp.toString()}] {self.text} - {self.log_state.name }"


class LoggerUI(QMainWindow):
    change_large_text_signal=pyqtSignal(str,str)
    generate_log_signal=pyqtSignal(LogEntry)

    def __init__(self,controller):
        super().__init__()
        self.controller=controller
        self.initUI()
        self.mutex = QMutex()  # 뮤텍스 생성
        self.generate_log_signal.connect(self.generate_log)  # 시그널 연결
        self.change_large_text_signal.connect(self.change_large_text)  # 시그널 연결


    def initUI(self):
        self.tabWidget = QTabWidget()
        self.setCentralWidget(self.tabWidget)

        self.main_tab = QWidget()
        self.log_tab = QWidget()

        self.tabWidget.addTab(self.main_tab, "main_tab")
        self.tabWidget.addTab(self.log_tab, "log_tab")

        self.main_tab_UI()
        self.log_tab_UI()



        # 창 설정
        self.setGeometry(300, 100, 1200, 900)
        self.setWindowTitle('로그 창')

        # LogState에 따른 배경색 정의
        self.color_map = {
            LogState.Fail: "red",
            LogState.NoData: "lightgray",
            LogState.GetData: "lightgreen",
            LogState.Recovery: "lightcoral"
        }

        # Set initial text for the large text box and center it
        self.large_text_box.setLineWrapMode(QTextEdit.NoWrap)  # Prevent line breaks
        self.large_text_box.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Hide vertical scrollbar
        self.large_text_box.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Hide horizontal scrollbar
        self.large_text_box.setAlignment(Qt.AlignCenter)  # Center-align text
        # Center-align text both horizontally and vertically using HTML formatting


        text_box_height = 100
        self.large_text_box.setFixedHeight(text_box_height)
        self.large_text_box.setPlainText("INIT")
        self.main_text_box.setText("INIT")
        self.large_text_box.setViewportMargins(5,25,5,5)
        cursor = QTextCursor(self.large_text_box.document())
        block_format = QTextBlockFormat()
        block_format.setAlignment(Qt.AlignCenter)

        cursor.mergeBlockFormat(block_format)
        self.large_text_box.setTextCursor(cursor)


    def add_log(self, log_entry):
        # 로그 창에 표시
        color = self.color_map.get(log_entry.log_state, "white")  # 상태에 따른 색상 가져오기
        # HTML 스타일링을 사용하여 로그 메시지에 색상 적용
        log_message = f"<span style='background-color:{color};'>{str(log_entry)}</span>"
        self.log.insertHtml(log_message)
        # 스타일 초기화를 위해 빈 스타일 없는 div 추가
        self.log.insertHtml("<span style='background-color:none;'><br></span>")
        #self.log.insertHtml("<div style='background-color:white;'><br></div>")

        #min max 관련
        #self.data_line_min = log_entry.min
        #self.data_line_max = log_entry.max
        #self.data_line_avg = log_entry.avg
        #self.data_line_text = f"min= {self.data_line_min} , max= {self.data_line_max} , avg= {self.data_line_avg} , frame_count= {log_entry.frame_count} "

    def generate_log_test(self):

         text = self.entry.text()
         state_value = LogState.GetData  # 혹은 사용자 입력에 따라 결정
         # LogEntry 객체 생성
         log_entry = LogEntry(text, state_value)

         self.mutex.lock()
         self.controller.log_entries.append(log_entry)
         self.add_log(log_entry)
         self.mutex.unlock()

         self.entry.clear()

    def generate_log(self, log_entry):
         self.mutex.lock()  # 뮤텍스로 데이터 접근을 보호
         self.add_log(log_entry)
         self.mutex.unlock()

    def change_large_text(self, text, color):
        self.large_text_box.setStyleSheet(f"background-color: {color}; color: black;")
        self.large_text_box.setPlainText(text)
        self.large_text_box.setAlignment(Qt.AlignCenter)  # Center-align text


    def main_tab_UI(self):
        layout = QVBoxLayout()
        # label = QLabel('Content of Tab 2')
        # layout.addWidget(label)


        # Large text box
        self.main_text_box = QLabel('Sample Text',self)
       # self.main_text_box.setReadOnly(True)  # Make it non-editable

        #large_text_box_html = "<center><div style='line-height: 100px;'>Sample Text</div></center>"

        self.main_text_box.setAlignment(Qt.AlignCenter)  # Center alignment horizontally and vertically.

        # Optional: Set the style of the QLabel if needed.
        #self.main_text_box.setStyleSheet("QLabel { background-color : lightblue; color : black; font-size: 50px; }")

        font = self.main_text_box.font()
        font.setPointSize(50)  # Adjust font size as needed
        self.main_text_box.setFont(font)
        # Set background color of the entire large_text_box and text
        color = "lightgray"
        # self.large_text_box.setStyleSheet(f"background-color: {color}; color: {color};")
        self.main_text_box.setStyleSheet("background-color: lightblue; color: black;")

        # top_layout.addLayout(input_layout)
        #top_layout.addLayout(set_layout)
        #top_layout.addWidget(self.main_text_box, alignment=Qt.AlignRight)
        # large_text_layout.addStretch(1)  # Add 1/3 spacing to the left
        layout.addWidget(self.main_text_box)
        # Add som



        self.main_tab.setLayout(layout)

    def __make_data_line__(self):
        self.data_line_text = ""
        for i in range(4):
                self.data_line_text+=self.data_line_text_list[i]
                self.data_line_text+=str(self.data_line_data_list[i])

    def log_tab_UI(self):
        # 레이아웃 설정
        layout = QVBoxLayout()

        # Create a horizontal layout for the text input field and "Add log" button
        input_layout = QHBoxLayout()

        # Text input field
        self.entry = QLineEdit(self)
        input_layout.addWidget(self.entry)

        # Add log button
        self.log_button = QPushButton('Add log', self)
        self.log_button.clicked.connect(self.generate_log_test)
        input_layout.addWidget(self.log_button)

        data_layout = QVBoxLayout()
        self.data_line_text=""
        self.data_line_text_list = ["min= "," , max= "," , avg= "," , frame_count= "]
        self.data_line_data_list = [0]*4
        # self.data_line = QTextEdit(self)
        # self.data_line.setFixedHeight(40)  # Adjust height as needed
        # self.data_line.setReadOnly(True)
        # self.data_line.setPlainText(self.data_line_text)
        self.data_line = QLabel("",self)
        self.__make_data_line__()
        self.data_line.setText(self.data_line_text)
        data_layout.addWidget(self.data_line, alignment=Qt.AlignLeft)

        set_layout = QVBoxLayout()
        set_layout.addLayout(input_layout)
        set_layout.addLayout(data_layout)

        # Create a horizontal layout for the large text box
        top_layout = QHBoxLayout()

        # Large text box
        self.large_text_box = QTextEdit(self)
        self.large_text_box.setFixedHeight(100)  # Adjust height as needed
        self.large_text_box.setReadOnly(True)  # Make it non-editable

        large_text_box_html = "<center><div style='line-height: 100px;'>Sample Text</div></center>"
        self.large_text_box.setHtml(large_text_box_html)
        self.large_text_box.setTextInteractionFlags(Qt.NoTextInteraction)  # Prevent text selection
        font = self.large_text_box.font()
        font.setPointSize(25)  # Adjust font size as needed
        self.large_text_box.setFont(font)
        # Set background color of the entire large_text_box and text
        color = "lightgray"
        # self.large_text_box.setStyleSheet(f"background-color: {color}; color: {color};")
        self.large_text_box.setStyleSheet("background-color: lightblue; color: black;")

        # top_layout.addLayout(input_layout)
        top_layout.addLayout(set_layout)
        top_layout.addWidget(self.large_text_box, alignment=Qt.AlignRight)
        # large_text_layout.addStretch(1)  # Add 1/3 spacing to the left

        # Add som

        layout.addLayout(top_layout)

        # 로그 창
        self.log = QTextEdit(self)
        self.log.setReadOnly(True)
        layout.addWidget(self.log)
        self.log.setTextInteractionFlags(Qt.NoTextInteraction)  # Prevent text selection

        # 레이아웃 적용
        self.log_tab.setLayout(layout)

