
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout,QTabWidget,QLabel ,QPushButton, QTextEdit, QLineEdit,QHBoxLayout,QSizePolicy,QMainWindow
from PyQt5.QtCore import QDateTime,pyqtSignal, QMutex, QObject,Qt
from PyQt5.QtGui import QTextCursor,QTextBlockFormat
from enum import Enum

import os
import main
import FactoryCode_verify_TemperatureVariation as fc_vt
import time  # sleep 함수 사용
import datetime
import python_simmian_api
import sys
import threading
from pyqt_ui.log_ui import *

from shutil import copyfile
from measurement import embedded_data_parser, measurement_items as mi
import numpy as np
import pvl_func.pvl_func as pvl_f
from pvl_func import TEC_Serial_Communication as serial_comm
from pvl_func import tec_Comm_Setting as tec_setting

class LogState(Enum):
    Fail=-1
    NoData=0
    GetData=1
    Recovery=2


class TestCase(Enum):
    NoData=0
    Aging=1
    ReliabilityTest=2
    DepthEvaluation=3

class LogEntry:
    def __init__(self, text, _logState=LogState.NoData, total_data=dict()):
        self.text = text
        self.log_state = _logState
        self.total_data=total_data
        self.timestamp = QDateTime.currentDateTime()


    def __str__(self):
        return f"[{self.timestamp.toString()}] {self.text} - {self.log_state.name }"


class LoggerUI(QMainWindow):
    change_large_text_signal=pyqtSignal(str,str)
    generate_log_signal=pyqtSignal(LogEntry)
    update_rcp_signal=pyqtSignal(list)

    def __init__(self,controller, test_case):
        super().__init__()
        self.test_case=test_case
        self.Capture_Start=False
        self.controller=controller
        self.initUI()
        self.mutex = QMutex()  # 뮤텍스 생성
        self.generate_log_signal.connect(self.generate_log_to)  # 시그널 연결
        self.change_large_text_signal.connect(self.change_large_text_to)  # 시그널 연결
        self.update_rcp_signal.connect(self.update_rcp_to)  # 시그널 연결
        self.tec_count=0
        self.my_comm=None


    def initUI(self):
        self.tabWidget = QTabWidget()
        self.setCentralWidget(self.tabWidget)

        self.main_tab = QWidget()
        self.log_tab = QWidget()

        self.tabWidget.addTab(self.main_tab, "main_tab")
        self.tabWidget.addTab(self.log_tab, "log_tab")

        self.main_tab_UI()
        self.log_tab_UI()

        if self.test_case==TestCase.TempTest:

            self.rcp_UI()



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

        self.data_line_text=""
        for key,val in log_entry.total_data.items():
            self.data_line_text+=key
            self.data_line_text+=str(round(val,2))
        self.data_line.setText(self.data_line_text)
        #self.data_line_min = log_entry.min
        #self.data_line_max = log_entry.max
        #self.data_line_avg = log_entry.avg
        #self.data_line_text = f"min= {self.data_line_min} , max= {self.data_line_max} , avg= {self.data_line_avg} , frame_count= {log_entry.frame_count} "


#&수정필요

    def start_aging_thread(self):
        self.input_module_name_text=self.input_module_name.text()
        self.work_thread = threading.Thread(target=self.start_aging_test)
        self.work_thread.start()
        self.start_button.setDisabled(True)


    def start_tec_thread(self):
        self.tec_thread = threading.Thread(target=self.start_tec_controller)
        self.tec_thread.start()
    def start_tec_controller(self):
        while True:
            if self.my_comm==None or self.my_comm.work_done==True:
                self.tec_count += 1
                self.del_comm_obj()
                self.read_rcp()
                self.my_comm.thread_on()
                self.my_comm.start_rcp()
            self.controller.update_rcp(self.my_comm.rcp_data)
            time.sleep(0.5)

    def start_tec_controller_forloop(self):
        while self.tec_count<=3:
            if self.my_comm==None or self.my_comm.work_done==True:
                self.tec_count += 1
                self.del_comm_obj()
                self.read_rcp()
                self.my_comm.thread_on()
                self.my_comm.start_rcp()
            self.controller.update_rcp(self.my_comm.rcp_data)
            time.sleep(0.5)
    def del_comm_obj(self):
        if self.my_comm!=None:
            self.my_comm.end_rcp()
            self.my_comm.is_thread_running=False

    def read_rcp(self):
        self.my_comm = serial_comm.TEC_SerialCommunication(tec_setting.TecCommSetting("config.ini"))
        self.my_comm.read_rcp("default.rcp")
        self.controller.update_rcp(self.my_comm.rcp_data)

        # try:
        #     self.my_comm = serial_comm.TEC_SerialCommunication(tec_setting.TecCommSetting("config.ini"))
        #     self.my_comm.read_rcp("default.rcp")
        #     self.rcp_list.setText("")
        #     for i in self.my_comm.rcp_data["workString"]:
        #         self.rcp_list.append(i)
        # except:
        #     print("read_RCP_ERR")


    def start_aging_thread(self):
        self.input_module_name_text=self.input_module_name.text()
        self.work_thread = threading.Thread(target=self.start_aging_test)
        self.work_thread.start()
        self.start_button.setDisabled(True)

    def start_aging_test(self,MHz):

        sim_state = False
        recovery_count = 0
        while sim_state is False:
            recovery_count += 1
            # add log
            self.controller.generate_log(f"recovery_count : {recovery_count}", LogState.Recovery)
            self.controller.change_large_text(f"SETTING : {recovery_count}", "lightcoral")

            sim_state = pvl_f.RecoverySim()

        # 모듈 번호 입력 ***************************************************************************************************
        fc_vt.ProcCreateModuleFolder(self.input_module_name_text)
        start_time = datetime.datetime.now()
        next_frame_time = 0
        test_during_time = 60 * 60 * 200
        image_save_time = 0
        pvl_f.init_setFile()
        total_data = {'total_count': 0, 'avg': 0, 'min': 0, 'max': 0}  # count, totalval,avg,min,max
        # total_data=[0,0,0,0,0]#count, totalval,avg,min,max
        recovery_count = 0
        cap_count = 0
        total_second = 0
        frame_item = list()

        mi_path = fc_vt.get_path()
        mi_obj = mi.MeasurementItems(mi_path)
        next_frame_time = start_time

        self.controller.change_large_text("RUNNING", "lightgreen")
        while total_second < test_during_time:
            # check 10s
            if (next_frame_time - datetime.datetime.now()).total_seconds() > 0:
                time.sleep(0.05)
                continue
            next_frame_time = next_frame_time + datetime.timedelta(seconds=10)
            result_saver = list()

            total_second = (datetime.datetime.now() - start_time).total_seconds()
            time.sleep(1)  # 성능평가를 위한 뎁스 영상 취득 전에 워밍업 3초
            # Measurement(100, 500, motion_dist500)  # 300 mm 에서 평가
            data_get_bool = pvl_f.ProcSaveRaw(1, 20, 500, result_saver)  # 500 mm 에서 평가

            if data_get_bool:
                if self.Capture_Start is False:
                    if self.test_case==TestCase.ReliabilityTest:
                        self.start_tec_thread()
                    self.Capture_Start = True
                # get easurement item from capture data
                frame_item = [0, 0, 0, 0, 0]# 0 : depth avg , 1 : intensity avg , 2 : tx temp , 3 : rx temp , 4 : time stamp
                frame_num = len(result_saver)
                for i in range(frame_num):
                    for j in range(4):  # j=  0 : depth avg , 1 : intensity avg , 2 : tx temp , 3 : rx temp
                        frame_item[j] += result_saver[i][j]
                for j in range(4):
                    frame_item[j] /= frame_num
                frame_item[4] = result_saver[0][4]  # input first frame time stamp

                mi_obj.input_measurement_item(frame_item)

                #mi_obj.result_table[0]-> depth data, 0:avg, 2:max, 4:min
                # add log
                cap_count += 1
                total_data = {' total_count : ': cap_count, ' , avg : ': mi_obj.result_table[0][0], ' , min : ': mi_obj.result_table[0][4], ' , max : ': mi_obj.result_table[0][2]}  # count, totalval,avg,min,max
                self.controller.generate_log(f"Data_get : {cap_count}", LogState.GetData, total_data)
                self.controller.change_large_text(f"RUNNING : {cap_count}", "lightgreen")

                #self.controller.generate_log(f"Data_get : {cap_count}", LogState.GetData)

                # img save per hour
                if total_second / 3600 > image_save_time:
                    image_save_time += 1
                    pvl_f.image_save(20, 500)
                recovery_count = 0

            else:
                sim_state = False
                while sim_state is False and recovery_count < 20:
                    recovery_count += 1
                    # add log
                    self.controller.generate_log(f"recovery_count : {recovery_count}", LogState.Recovery)
                    self.controller.change_large_text(f"RECOVERY : {recovery_count}", "lightcoral")
                    sim_state = pvl_f.RecoverySim()
                if recovery_count == 20:
                    # add log
                    self.controller.generate_log(f"recovery_count : {recovery_count}", LogState.Fail)
                    self.controller.change_large_text("FAIL", "red")
                    # 로그에 init count max를 입력하고 프로그램 종료
                    break
                else:
                    pvl_f.init_setFile()

            fc_vt.ProcCreateReport(1)  # 0 -> find global offset , 1 -> only measurement


        # 심미안 리셋 ******************************************************************************************************
        fc_vt.msg_print(f'심미안을 리셋합니다.')
        fc_vt.ProcSimmianReset()

        # 심미안 종료 ******************************************************************************************************
        fc_vt.msg_print(f'심미안을 종료합니다.')
        fc_vt.ProcSimmianStop()

        # 모터 닫기 ********************************************************************************************************
        fc_vt.msg_print(f'모터와 통신을 종료합니다.')
        fc_vt.ProcMotorClose()

        self.controller.generate_log(f"Done")
        self.controller.change_large_text(f"Done", "lightgreen")

        fc_vt.msg_print("done. please replace with next module")
        fc_vt.sys.exit()


    def generate_log_test(self):

         text = self.input_module_name.text()
         state_value = LogState.GetData  # 혹은 사용자 입력에 따라 결정
         # LogEntry 객체 생성
         log_entry = LogEntry(text, state_value)

         self.mutex.lock()
         self.controller.log_entries.append(log_entry)
         self.add_log(log_entry)
         self.mutex.unlock()

         self.input_module_name.clear()

    #def generate_log(self, log_entry, result_table):
    def generate_log_to(self, log_entry):
         self.mutex.lock()  # 뮤텍스로 데이터 접근을 보호
         self.add_log(log_entry)
         self.mutex.unlock()

    def change_large_text_to(self, text, color):

        self.large_text_box.setStyleSheet(f"background-color: {color}; color: black;")
        self.large_text_box.setPlainText(text)
        self.large_text_box.setAlignment(Qt.AlignCenter)  # Center-align text

        self.main_text_box.setStyleSheet(f"background-color: {color}; color: black;")
        self.main_text_box.setText(text)
        self.main_text_box.setAlignment(Qt.AlignCenter)  # Center-align text

    def update_rcp_to(self, rcp_dict):
        # Prepare a multi-line string to display multiple items
        multi_cstr = ""

        # Iterate over the workString items
        for index, work_string in enumerate(rcp_dict['workString']):
            cstr = work_string

            if index + 1 < rcp_dict['nCrrntIdx']:
                cstr += " : Done\r\n"
            elif index + 1 == rcp_dict['nCrrntIdx'] and rcp_dict['rcp'][index][0] == 1:
                if rcp_dict['TouchedTargetTemp']:
                    cstr += ", TouchedTargetTemp : True , time : {}\r\n".format(
                        int(time.time() - rcp_dict['CheckTime']))
                else:
                    cstr += ", TouchedTargetTemp : False\r\n"
            elif index + 1 == rcp_dict['nCrrntIdx'] and rcp_dict['rcp'][index][0] == 2:
                cstr += ", END RCP \r\n"
            else:
                cstr += "\r\n"

            multi_cstr += cstr

        self.rcp_list.setText(multi_cstr)


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
        self.data_line.setText(self.data_line_text)

    def log_tab_UI(self):
        # 레이아웃 설정
        layout = QVBoxLayout()

        # Create a horizontal layout for the text input field and "Add log" button
        input_layout = QHBoxLayout()

        # Text input field
        self.input_module_name = QLineEdit(self)
        input_layout.addWidget(self.input_module_name)

        # Add log button
        self.start_button = QPushButton('START TEST', self)
        #self.log_button.clicked.connect(self.generate_log_test)
        self.start_button.clicked.connect(self.start_aging_thread)


        input_layout.addWidget(self.start_button)

        data_layout = QVBoxLayout()
        self.data_line_text=""
        self.data_line_text_list = ["min= "," , max= "," , avg= "," , frame_count= "]
        self.data_line_data_list = [0]*4 #min max avg count
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


    def rcp_UI(self):
        self.rcp_tab = QWidget()
        self.tabWidget.addTab(self.rcp_tab, "rcp_tab")
        layout = QVBoxLayout()

        # Add log button
        self.read_rcp_button = QPushButton('READ RCP', self)
        #self.log_button.clicked.connect(self.generate_log_test)
        self.read_rcp_button.clicked.connect(self.start_tec_thread)

        set_layout = QVBoxLayout()

        # Create a horizontal layout for the large text box
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.read_rcp_button)
        top_layout.addWidget(self.large_text_box, alignment=Qt.AlignRight)
        # large_text_layout.addStretch(1)  # Add 1/3 spacing to the left

        # Add som

        layout.addLayout(top_layout)

        # 로그 창
        self.rcp_list = QTextEdit(self)
        self.rcp_list.setReadOnly(True)
        layout.addWidget(self.rcp_list)
        self.rcp_list.setTextInteractionFlags(Qt.NoTextInteraction)  # Prevent text selection

        # 레이아웃 적용
        self.rcp_tab.setLayout(layout)

