
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QLineEdit,QHBoxLayout
from PyQt5.QtCore import QDateTime,pyqtSignal, QMutex, QObject,Qt
from PyQt5.QtGui import QTextCursor,QTextBlockFormat
from enum import Enum
from pyqt_ui.log_ui_aging import *

class LoggerController(QObject):
    change_large_text_signal=pyqtSignal(str,str)
    generate_log_signal = pyqtSignal(LogEntry)
    def __init__(self):
        super().__init__()
        self.log_entries=[]

    def generate_log(self, text, log_state, total_data=dict()):
        log_entry = LogEntry(text, log_state,total_data)
        self.log_entries.append(log_entry)
        self.generate_log_signal.emit(log_entry)

    def change_large_text(self,text,color):
        self.change_large_text_signal.emit(text,color)