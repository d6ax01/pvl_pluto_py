import threading
import queue
import time
import tec_handler


class TecScheduler:
    def __init__(self, tec_setting):
        self.tec_handler= tec_handler.TecHandler(tec_setting)
        self.work_queue = queue.Queue()
        self.comm_lock = threading.Lock()
        self.condition = threading.Condition()
        self.work_done=False
        self.is_thread_running = False
        self.schedule_thread = None
        self.work_thread = None
        self.rcp_data = {
            'rcp': [],
            'workString': [],
            'DoSchedule': False,
            'nCrrntIdx': 0,
            'TouchedTargetTemp': False,
            'DoNextWork': True,
            'TargetTemp': 0,
            'TargetTime': 0,
            'SendedTime': 0,
            'mode': 0,
            'CheckTime': 0,
        }
        self.current_temp = 0
        self.state = False
        self.sended_target_temp = 0

    def thread_on(self):
        if not self.rcp_data['DoSchedule']:
            self.rcp_data['DoSchedule'] = True
            self.schedule_thread = threading.Thread(target=self.work_scheduler)
            self.schedule_thread.start()

    def read_rcp(self, filename):
        # Simplified placeholder for reading from a file
        with open(filename, 'r') as file:
            lines = file.readlines()
            for line in lines:
                parts = line.strip().split(',')
                if parts[0] == '1':
                    temp = int(parts[1])
                    time_sec = int(parts[2])
                    self.rcp_data['rcp'].append([1, temp, time_sec])
                    self.rcp_data['workString'].append(f"SET : 설정온도 = {temp / 10:.1f}, 유지시간(s) : {time_sec}")
                elif parts[0] == '2':
                    self.rcp_data['rcp'].append([2])
                    self.rcp_data['workString'].append("TEC OFF")
        # self.start_rcp()

    def end_rcp(self):
        self.rcp_data['DoSchedule'] = False
        with self.comm_lock:
            while not self.work_queue.empty():
                self.work_queue.get()

    def tec_command_in_queue(self, command, temp):
        with self.comm_lock:
            self.work_queue.put((command, temp))

    def work_scheduler(self):
        self.rcp_data['nCrrntIdx'] = 0
        self.rcp_data['TouchedTargetTemp'] = False
        self.rcp_data['DoNextWork'] = True

        while self.rcp_data['nCrrntIdx'] < len(self.rcp_data['rcp']) and self.rcp_data['DoSchedule']:
            if self.rcp_data['DoNextWork']:
                with self.comm_lock:
                    work = self.rcp_data['rcp'][self.rcp_data['nCrrntIdx']]
                    self.work_queue.put((work[0], work[1] if len(work) > 1 else 0))
                    print(self.rcp_data['workString'][self.rcp_data['nCrrntIdx']])
                    self.rcp_data['DoNextWork'] = False
                    if work[0] == 1:
                        self.rcp_data['mode'] = 1
                        self.rcp_data['TargetTemp'] = work[1]
                        self.rcp_data['TargetTime'] = work[2]
                        self.rcp_data['SendedTime'] = time.time()
                        self.rcp_data['TouchedTargetTemp'] = False
                        self.rcp_data['nCrrntIdx'] += 1
                    else:
                        self.rcp_data['mode'] = 0
                        self.rcp_data['nCrrntIdx'] += 1
                        break
            time.sleep(0.2)
        self.work_done = True
