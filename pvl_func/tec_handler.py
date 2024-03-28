import threading
import queue
import time
from serial import Serial # pip install pySerial


class TecHandler:
    def __init__(self, tec_setting):
        self.serial_comm = Serial(tec_setting.port, tec_setting.baudrate, timeout=1)
        self.data_to_send = bytearray([0x53, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x45])
        self.set_queue = queue.Queue()
        self.comm_lock = threading.Lock()
        self.condition = threading.Condition()
        self.work_done=False
        self.is_thread_running = False
        self.schedule_thread = None
        self.work_thread = None
        self.current_temp = 0
        self.state = False
        self.sended_target_temp = 0

    def process_queue(self):
        while self.is_thread_running:
            if not self.is_thread_running:
                break
            if not self.work_queue.empty():
                self.comm_lock.acquire()
                work = self.work_queue.get()
                self.comm_lock.release()
                if work[0] == 1:
                    self.on_tec(work[1])
                elif work[0] == 2:
                    self.off_tec()
                elif work[0] == 5:
                    self.get_temp()
            if self.work_queue.empty():
                with self.condition:
                    if self.condition.wait_for(lambda: not self.work_queue.empty(), 2) is False:
                        self.tec_command_in_queue(5, 0)


    def check_schedule_state(self):
        if not self.rcp_data['TouchedTargetTemp']:
            if abs(self.current_temp - self.rcp_data['TargetTemp']) <= 5:
                self.rcp_data['TouchedTargetTemp'] = True
                self.rcp_data['CheckTime'] = time.time()
            else:
                if self.rcp_data['mode'] == 1 and self.rcp_data['SendedTime'] + 10 < time.time():
                    self.tec_command_in_queue(1, self.rcp_data['TargetTemp'])
                    self.rcp_data['SendedTime'] = time.time()

        if self.rcp_data['TouchedTargetTemp'] and self.rcp_data['CheckTime'] + self.rcp_data[
            'TargetTime'] < time.time():
            self.rcp_data['DoNextWork'] = True

    def thread_on(self):
        if self.is_thread_running is False:
            self.is_thread_running = True
            self.work_thread = threading.Thread(target=self.process_queue)
            self.work_thread.start()

    def on_tec(self, temp):
        print(f"Send ON Protocol, set Temp: {temp}")
        self.data_to_send[2] = 0x01
        self.data_to_send[3] = (int)(temp >> 8)
        self.data_to_send[4] = temp & 0xFF
        self.send_message(self.data_to_send)
        # Simplified, assumes success
        self.sended_target_temp = temp
        self.state = True

    def off_tec(self):
        print("Send Off Protocol")
        self.data_to_send[2] = 0x02
        self.send_message(self.data_to_send)
        # Simplified, assumes success
        self.state = False

    def get_temp(self):
        self.data_to_send[2] = 0x05
        result = self.send_message(self.data_to_send)
        # Simplified, assumes reception of temperature
        if len(result) == 8:
            self.current_temp = (result[5] << 8) + result[6]
            print(f"Get Protocol, Current Temp: {self.current_temp}")
        else:
            print("result len : ", len(result))

    def send_message(self, input_order):
        # Simplified placeholder for sending and receiving message
        # Assumes serial communication is properly configured and open
        try:
            self.serial_comm.write(input_order)
            response = self.serial_comm.read(8)  # Assuming fixed response size for simplicity
            return response
        except Exception as e:
            print(f"Error in communication: {e}")
            return bytearray([0] * 8)  # Return a default response