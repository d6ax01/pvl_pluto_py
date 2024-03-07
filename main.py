import time
from tkinter import *
import subprocess # 외부 프로그램 호출
import ctypes # 알림창 띄우기
import sys # 시스템 종료
#import utils.winsys # 관리자 권한으로 실행했는지 확인
import winsys # 관리자 권한으로 실행했는지 확인

#from lib_wiggling import main_wigg # 파이썬 코드 -> 1_2_timedelay_hb_td8_3.py
#from lib_lensfppn import main_lensfppn # 파이썬 코드 -> 3_4_lens_fppn_namuga.py
from validation import main_val
from validation import database_uploader
from validation import check_sensor_id

import psutil # 이름으로 특정 프로세스 종료 시키기
# 실행파일 만들기 pyinstaller
# C:\Users\isMedia\AppData\Local\Programs\Python\Python311\Lib\site-packages\PyInstaller 에서
# out = out.decode(encoding, errors='ignore')

import python_simmian_api
import os
import python_vst_eepromparser_api as writeToeeprom

import argparse         # 프로그램을 실행 시에 커맨드 라인에 인수를 받아 처리

#******************************************************
# UI창 사이즈
uiconfig = f'380x785+1000+0'
root = Tk()
btnStart = Button(root)
listbox = Listbox(root)
labeljudge = Label(root)
cal_mode = 1
val_mode = 2
VALIDATION = 0
OQC = 1
DAILY_CHECK = 2
VALIDATION_SIMPLE = 3
gMode = VALIDATION # 0 : e2p 쓰기 포함 , 1 : OQC, e2p 쓰기 포함 안됨 , 2 : daily-check , 3 : 500mm만 평가
#******************************************************

#******************************************************
# 심미안 프로그램 경로
PATH_Nxsimmian = f'C:\\Program Files\\NxSimmian\\NxSimmian v1.3.7.0\\SimmianLauncher.exe'
#PATH_DBUploader = f'C:\\lsi\\NMG_DBUpload_Demo\\Release\\dbUploader.exe'
PATH_DBUploader = f'C:\\LSI_VST63D\\4_Validation\\NMG_DBUpload_Demo\\Release\\dbUploader.exe'
#******************************************************

#******************************************************
# 심미안 보드 USB 장치명
vendor_num = 4660 #usb Vendor ID 1234
product_num = 8197 #usb Product ID 2002
#******************************************************

#******************************************************
# 캘리브레이션 time-delay , bypass 교체 flag
WIGGLING = 1
LENSFPPN = 2
#******************************************************

#******************************************************
# 생산결과코드
is_code = f''

PASS = 0                # 0   PASS
FAIL = 1                # 1   FAIL
FAIL_SENSOR_ID = 62     # 62  SENSOR_ID 불량
FAIL_SIMMIAN_INIT = 100 # 100 INIT_SIMMIAN 불량
FAIL_IS_ADMIN = 101     # 101 IS_ADMIN
FAIL_IS_MOTOR = 102     # 102 IS_MOTOR
FAIL_OTP_WRITE = 103    # 103 OTP_WRITE 불량 -> e2p 쓰기 실패
FAIL_WIGG_LINEARITY_BROKEN = 104    # 104 [wigg] wiggling linearity is broken
FAIL_WIGG_GETCONFIDENCETHRE = 105   # 105 [WIGG] getWiggConfidenceThre is fail
FAIL_CALFILE_COUNT = 106            # 106 파일 갯수 부족
FAIL_IS_CONNECT_CHANGE = 107        # 107 IS_CONNECT_CHANGE
FAIL_Z_NOISE = 108      # 108 Z축 잡음 불량
FAIL_Z_ERROR = 109      # 109 Z축 오차 불량
FAIL_VCSEL_POWER = 110  # 110 픽셀 밝기 레벨 불량
FAIL_APC_CHECK = 111    # 111 APC 체크 불량
FAIL_Z_NOISE_100 = 112  # 112 100mhz, Z축 잡음 불량
FAIL_Z_ERROR_100 = 113  # 113 100mhz, Z축 오차 불량
FAIL_VCSEL_POWER_100 = 114  # 114 100mhz, 픽셀 밝기 레벨 불량
FAIL_APC_CHECK_100 = 115    # 115 100mhz, APC 체크 불량
FAIL_Z_NOISE_20 = 116   # 116 20mhz, Z축 잡음 불량
FAIL_Z_ERROR_20 = 117   # 117 20mhz, Z축 오차 불량
FAIL_VCSEL_POWER_20 = 118   # 118 20mhz, 픽셀 밝기 레벨 불량
FAIL_APC_CHECK_20 = 119     # 119 20mhz, APC 체크 불량
FAIL_MAKE_SETFILE = 120     # 120 MAKE_SETFILE, 셋파일 생성 실패
FAIL_LOAD_SETFILE = 121     # 121 LOAD_SETFILE

#******************************************************

#******************************************************
UNLOCK = 0
UNLOCK_VALUE = 160  # 0xA0
LOCK = 1
LOCK_VALUE = 161    # 0xA1
#******************************************************



def judgecode(code, msg):
    global btnStart

    is_code = code

    if is_code == PASS:
        messagebox(msg)
        btnStart.configure(text='PASS', font=("", 72), bg="Green", fg="Black", overrelief="solid")

    else:
        messagebox(msg)
        btnStart.configure(text='FAIL', font=("", 72), bg="Red", fg="White",overrelief="solid")


def exit():
    kill_nxsimmian() #심미안 프로그램 강제 종료
    sys.exit(1) # 0 -> 정상 종료 , 1 -> 강제 종료


def kill_nxsimmian():
    for proc in psutil.process_iter():
        if proc.name() == "SimmianApp.exe":
            proc.kill()
            #err psutil.NoSuchProcess: process no longer exists (pid=11532, name='SimmianApp.exe')
        elif proc.name() == "SimmianLauncher.exe":
            proc.kill()
        elif proc.name() =="MMF.exe":
            proc.kill()
        elif proc.name() =="SSkinServer.exe":
            proc.kill()



def changemode(mode):
    re = False

    if mode == 1:
        re = ctypes.windll.user32.MessageBoxW(0, f'Pls, After changing to WIGGLING, press Y ', " ", 52) # re -> 6 YES , 7 -> No
    elif mode == 2:
        re = ctypes.windll.user32.MessageBoxW(0, f'Pls, After changing to LENSFPPN, press Y', " ", 52) # re -> 6 YES , 7 -> No
    else :
        result = False

    if re == 6:
        result = 0
    else:
        result = 107

    return result


def runsimmianstatus():
    is_status = 99

    is_status = ctypes.windll.user32.MessageBoxW(0, f'Is it run NxSimmian Viewer?', " ", 52)

    if is_status == 6:  # Todo '6' -> YES , '7' -> NO
        return PASS
    else:
        # todo 심미안SW 다시 실행하기
        kill_nxsimmian()  # 일단 끄고,
        runNxsimmian()
        is_status = ctypes.windll.user32.MessageBoxW(0, f'Is it run NxSimmian Viewer?', " ", 52)
        if is_status == 6:  # Todo '6' -> YES , '7' -> NO
            return PASS
        else:
            # todo 심미안SW 다시 실행하기
            kill_nxsimmian()  # 일단 끄고,
            runNxsimmian()
            is_status = ctypes.windll.user32.MessageBoxW(0, f'Is it run NxSimmian Viewer?', " ", 52)
            if is_status == 6:  # Todo '6' -> YES , '7' -> NO
                return PASS
            else:
                # todo 심미안SW 다시 실행하기
                kill_nxsimmian()  # 일단 끄고,
                runNxsimmian()
                is_status = ctypes.windll.user32.MessageBoxW(0, f'Is it run NxSimmian Viewer?', " ", 52)
                if is_status == 6:  # Todo '6' -> YES , '7' -> NO
                    return PASS
                else:
                    return FAIL_SIMMIAN_INIT


def getDevice():
    status = False

    status = True # 나중에 구현하자

    return status


def messagebox(msg):
    listbox.insert(0, msg)


def runNxsimmian():
    global NxsimmianApp
    result = False

    #1 심미안 드라이버 인식
    re = getDevice()

    #2-1. 심미안 드라이버를 인식 못했으면 프로그램 종료
    if re == False :
        messagebox(f'Do not find Simmian Board!!')
        return 100
    # 2-2. 심미안 드라이버를 인식했으면 Nx심미안 프로그램을 실행
    else :
        #2 심미안 프로그램 실행
        #messagebox(f'Run the Nxsimmian Viewer.')
        cmd = [PATH_Nxsimmian]
        #messagebox("PATH = {}".format(cmd))
        NxsimmianApp = subprocess.Popen(cmd, shell=True)
        time.sleep(5)
        return 0

def _lib_wigg():
    re = False#main_wigg()

    return re


# def wigg():
#     result = False
#
#     path = ['C:\\lsi\\1.bat'] #1_2_timedelay_hb_td8_3.py
#
#     # 외부 프로그램 실행하기
#     #re = subprocess.run(path, capture_output=True)
#
#     with open('test.log', 'w') as f:
#         process = subprocess.run(path, capture_output=True, encoding='utf-8')#process = subprocess.run(path, stdout=subprocess.PIPE)
#
#         # for python3, use b''
#         for c in iter(lambda: process.stdout.read(1), b''):
#             sys.stdout.write(c)
#             f.write(c)
#
#             str1 = ''.join(str(s) for s in c)
#             strsurch = 'Run -> 2.bat'
#             if strsurch in str1:
#                 result = True
#             else:
#                 result = False
#
#     return result


def _lib_lensfppn():
    re = False#main_lensfppn()

    return re

def _lib_val():
    global gMode

    re = main_val(gMode)    # todo gMode = 0, VALIDATION    -> e2p 쓰기 포함
                            # todo gMode = 1, OQC           -> e2p 쓰기 안함
                            # todo gMode = 2, DAILY_CHECK   -> e2p 쓰기 안함

    return re


# def lensfppn():A
#     result = False
#
#     path = ['C:\\lsi\\2.bat'] #3_4_lens_fppn_namuga.py
#
#     # 외부 프로그램 실행하기
#     #re = subprocess.run(path, capture_output=True)
#
#     with open('test.log', 'w') as f:
#         process = subprocess.run(path, capture_output=True, encoding='utf-8')#process = subprocess.run(path, stdout=subprocess.PIPE)
#
#         # for python3, use b''
#         for c in iter(lambda: process.stdout.read(1), b''):
#             sys.stdout.write(c)
#             f.write(c)
#
#             str1 = ''.join(str(s) for s in c)
#             strsurch1 = 'PASS <- Write EEPROM Process'
#             strsurch2 = 'FAIL <- Write EEPROM Process'
#
#             if strsurch1 in str1:
#                 result = True
#             elif strsurch2 in str1:
#                 result = False
#             else:
#                 result = False
#
#     return result



def lensfppnproc(enable):

    # 심미안SW 실행 실패이면
    if enable == False:
        messagebox(f'Do not run Nxsimmian Viewer!!')
        return 100
    else:
        # lensfppn 영상 취득하기
        re = _lib_lensfppn()
        return re


def wigglingproc(enable):

    # 심미안SW 실행 실패이면
    if enable == False:
        messagebox(f'Do not run Nxsimmian Viewer!!')
        return 100
    else:
        # 위글링 영상 취득하기
        re = _lib_wigg()#wigg()
        return re


def validationproc(is_simmian_status):
    #path = ['C:\\LSI_VST63D\\4_Validation\\run.bat', '-u']  # validation.py

    # 외부 프로그램 실행하기
    #re = subprocess.run(path, shell=True, stdout=subprocess.PIPE, encoding='utf-8')

    #return re

    # 심미안SW 실행 실패이면
    if is_simmian_status != PASS:   # todo PASS 또는 FAIL_SIMMIAN_INIT 으로 받는다.
        messagebox(f'Do not run Nxsimmian Viewer!!')
        return FAIL_SIMMIAN_INIT #100
    else:
        # validation 공정 시작하기
        re = _lib_val()
        return re


def frontproc():
    simmian = python_simmian_api.Simmian()

    # TODO check -> 0x0000 == 0x00 , 0x0002 == 0x00
    readvaluep = simmian.ReadI2C(0xA0, "0x0000", 1)
    readvalueq = simmian.ReadI2C(0xA0, "0x0002", 1)

    if readvaluep != 0 or readvalueq != 0:  # 0xA1
        print(f'EEPROM address: 0x0000 -> value {hex(readvaluep)} . ')
        print(f'EEPROM address: 0x0002 -> value {hex(readvalueq)} . ')
        print(f'Failed, An incorrect value is recorded in the header area.')
        return FAIL_OTP_WRITE #103

    # 2023-05-25 : todo check -> sensor ID _603D
    is_check = check_sensor_id()
    if is_check != PASS:
        return FAIL_SENSOR_ID
    else:
        return PASS


def eepromlock(write_protection_mode):
    simmian = python_simmian_api.Simmian()

    if write_protection_mode == UNLOCK:  # Todo unlocking -> written and read
        print(f'Unlocking... Write protection.... ')
        is_write = simmian.WriteI2C(0xA0, "0xE000", '0xA0')  # Todo, 주소: 0xE000, 값: 0xA0 (int)160
        time.sleep(0.010)
        if not is_write:
            print(f'failed write to eeprom !!! ')
            return FAIL_OTP_WRITE

        # is_read = simmian.ReadI2C(0xA0, "0xE000", 1)
        # if is_read != UNLOCK_VALUE:  # Todo 0xA0 (int)160
        #     print(f'FAIL, Write protection unlocking. ')
        #     return FAIL_OTP_WRITE  # 103

        # Todo check to header_data -> 0x0000 == 0x00 , 0x0001 == 0x00
        is_header_data = writeToeeprom.header_data_check(UNLOCK)
        if is_header_data != PASS:
            return FAIL
        print(f'SUCCESS, Write protection unlocking. ')
        return PASS

    elif write_protection_mode == LOCK:  # 1-> lock # Todo locking -> only-read
        print(f'Locking... Write protection.... ')
        is_write = simmian.WriteI2C(0xA0, "0xE000", '0xA1')  # TODO, 주소: 0xE000, 값: 0xA1 (int)161
        time.sleep(0.010)
        if not is_write:
            print(f'failed write to eeprom !!! ')
            return FAIL_OTP_WRITE

        # is_read = simmian.ReadI2C(0xA0, "0xE000", 1)
        # if is_read != LOCK_VALUE:  # TODO 0xA1 (int)161
        #     print(f'FAIL, Write protection locking. ')
        #     return FAIL_OTP_WRITE

        # Todo check to header_data -> 0x0000 == 0x00 , 0x0001 == 0x00
        is_header_data = writeToeeprom.header_data_check(LOCK)
        if is_header_data != PASS:
            return FAIL_OTP_WRITE

        print(f'SUCCESS, Write protection locking. ')
        return PASS
    else:
        return FAIL


def update_to_database(result):
    re = database_uploader(PATH_DBUploader, result)

    return re


def btnStartCal() :
    btnStart.configure(text='Run', font=("", 72), bg="Cyan", fg="White", overrelief="solid")
    messagebox(f'Calibration is start.')

    # 심미안SW 실행하기
    re_sim = False
    kill_nxsimmian() # 실행 유무 확인하기
    re_sim = runNxsimmian() # 심미안SW 실행하기
    re_sim = runsimmianstatus() # 심미안SW 실행을 했는지 작업자가 확인한다

    # 이전 공정 '통과' 검사하기 ********************************************
    re_frontproc = frontproc() # 0 -> PASS
    if re_frontproc == 0:
        str = f'[{re_frontproc}] PASS -> re_frontproc'
        messagebox(str)
    else:
        str = f'[{re_frontproc}] FAIL -> re_frontproc'
        judgecode(re_frontproc, str)
        return re_frontproc

    # E2P 쓰기 잠금해제 unlock *******************************************
    re_romunlock = eepromlock(0)  # 0 -> unlock , 1 -> lock
    if re_romunlock == 0:
        str = f'[{re_romunlock}] PASS -> re_romunlock'
        messagebox(str)
    else:
        str = f'[{re_romunlock}] FAIL -> re_romunlock'
        judgecode(re_romunlock, str)
        return re_romunlock

    # 위글링 영상 취득 ***************************************************
    messagebox(f'Wiggling calibration is start.')
    re_wigg = wigglingproc(re_sim)
    if re_wigg == 0:  # 0 -> PASS
        str = f'[{re_wigg}] PASS -> Wiggling'
        messagebox(str)
    else:
        str = f'[{re_wigg}] FAIL -> Wiggling'
        judgecode(re_wigg, str)
        return re_wigg

    # 위치 변경 *********************************************************
    re_sim = False
    if re_wigg == 0:
        re = changemode(LENSFPPN)
        if re == '107': # 에러
            return re
        else:
            # 심미안SW 실행하기
            kill_nxsimmian()  # 실행 유무 확인하기
            re_sim = runNxsimmian()  # 심미안SW 실행하기
            re_sim = runsimmianstatus()  # 심미안SW 실행을 했는지 작업자가 확인한다

    # lensfppn 영상 취득 ***********************************************
    messagebox(f'LensFPPN calibration is start.')
    re_lensfppn = 1
    if re_wigg == 0:
        re_lensfppn = lensfppnproc(re_sim)
        if re_lensfppn == 0:  # 0 -> PASS
            str = f'[{re_lensfppn}] PASS -> LensFPPN'
            messagebox(re_lensfppn)
        else:
            str = f'[{re_lensfppn}] FAIL -> LensFPPN'
            judgecode(re_lensfppn, str)
            return re_lensfppn

    # E2P 쓰기 잠금 lock ***********************************************
    re_romlock = eepromlock(1)  # 0 -> unlock , 1 -> lock
    if re_romlock == 0:
        str = f'[{re_romlock}] PASS -> re_romlock'
        messagebox(str)
    else:
        str = f'[{re_romlock}] FAIL -> re_romlock'
        judgecode(re_romlock, str)
        return re_romlock

    # DB에 결과 올리기 **************************************************
    re_update = update_to_database()
    if re_update == 0:
        str = f'[{re_update}] PASS -> re_update'
        messagebox(str)
    else:
        str = f'[{re_update}] FAIL -> re_update'
        judgecode(re_update, str)
        return re_update

    # 위치 변경 안내 ****************************************************
    changemode(WIGGLING)

    # 결과 ************************************************************
    if re_wigg == 0 and re_lensfppn == 0:
        str = f'[{0}] PASS -> Calibration was done.'
        judgecode(0, str)
    else:
        str = f'[{1}] FAIL -> Calibration was not done.'
        judgecode(1, str)

def run_val() :
    global gMode

    # 심미안SW 실행하기
    re_sim = FAIL
    kill_nxsimmian()                    # 심미안SW 실행의 유무 확인하기
    runNxsimmian()                      # 심미안SW 실행을 하기
    is_simmian = runsimmianstatus()     # 심미안SW 실행을 했는지 작업자가 확인한다
    if is_simmian != PASS:
        return FAIL_SIMMIAN_INIT

    # 이전 공정 '통과' 검사하기 ********************************************
    is_fp = PASS #frontproc()  # 0 -> PASS
    if is_fp != PASS:
        judgecode(FAIL, f'[{is_fp}] FAIL -> fool proof !!!')
        return is_fp  # FAIL_OTP_WRITE or FAIL_SENSOR_ID

    # E2P 쓰기 잠금해제 unlock *******************************************
    # if gMode == VALIDATION:                 # todo VALIDATION 에서만 eeprom 을 '잠금'을 해제한다
    #     is_eeprom = eepromlock(UNLOCK)  # 0 -> unlock , 1 -> lock
    #     if is_eeprom != PASS:
    #         judgecode(FAIL, f'[{is_eeprom}] FAIL_OTP_WRITE')
    #         return FAIL_OTP_WRITE
    # else:
    #     print(f'unlock to eeprom -> skip !!!')
    #     pass

    # validation 평가 시작 ***********************************************
    is_val = validationproc(is_simmian)     # TODO is_simmian -> PASS or FAIL_SIMMIAN_INIT
    if is_val != PASS:
        judgecode(FAIL, f'[{is_val}] FAIL -> Validation')
        return is_val

    # E2P 쓰기 잠금 lock ***********************************************
    # if gMode == VALIDATION:                 # todo VALIDATION 에서만 eeprom 을 '잠금' 한다.
    #     is_eeprom = eepromlock(LOCK)  # 0 -> unlock , 1 -> lock
    #     if is_eeprom != PASS:
    #         judgecode(FAIL, f'[{is_eeprom}] FAIL -> re_romlock')
    #         return FAIL_OTP_WRITE
    # else:
    #     print(f'lock to eeprom -> skip !!!')
    #     pass

    return PASS


def btnStartVal() :
    btnStart.configure(text=' Run  ', font=("", 72), bg="Cyan", fg="White", overrelief="solid")
    messagebox(f'Validation is start.')

    # todo Val 시작 *****************************************************
    is_result = run_val()

    # todo 결과 표시 *****************************************************
    if is_result != PASS:
        judgecode(FAIL, f'[{is_result}] FAIL -> Validation was not done.')
    else:
        judgecode(PASS, f'[{is_result}] PASS -> Validation was done.')

    # todo DB 업로드 *****************************************************
    # if gMode == DAILY_CHECK: #TODO, 일상점검에서는 DB와 연동하지 않는다.
    #     return

    # is_database_update = update_to_database(is_result)
    # if is_database_update != PASS:
    #     messagebox(f'[{is_database_update}] FAIL -> update to database')
    # else:
    #     messagebox(f'[{is_database_update}] PASS -> update to database')


def checkAdministrator ():
    # 관리자 권한으로 실행했는지 확인함*********************************************************************************
    #if not utils.winsys.is_admin():
    if not winsys.is_admin():
        messagebox(f'You should run this program with administrator')
        exit()


def checktomode():
    global gMode
    # 1. create parser
    parser = argparse.ArgumentParser(description=f'This is a VALIDATION program in the PYTHON language.')

    # 2. add arguments to parser
    parser.add_argument('--mode', type=int, default=9,
                        help=f'(0)VALIDATION, (1)OQC, (2)DAILY_CHECK, (3)VALIDATION_SIMPLE')

    # 4. use arguments
    args = parser.parse_args()
    mode = args.mode
    # print(f'Mode value -> {gMode}')

    if mode == 0:
        print("Start in 'VALIDATION' mode. ")
        gMode = mode
    elif mode == 1:
        print(f"Start in 'VALIDATION: OQC' mode. ")
        gMode = mode
    elif mode == 2:
        print(f"Start in 'VALIDATION: DAILY_CHECK' mode. ")
        gMode = mode
    elif mode == 3:
        print(f"Start in 'VALIDATION: VALIDATION 2' mode. ")
        gMode = mode
    else:
        print("FAIL")
        gMode = 999

    return gMode


def init(mode) :
    global listbox, btnStart, gMode

    root.geometry(uiconfig)  # UI창 사이즈와 시작좌표 위치
    root.resizable(False, False)  # UI창 사이즈 변경 막기

    # create button ->
    if mode == cal_mode:
        root.title("VST Calibration")  # UI창 제목
        btnStart = Button(root, text='Ready', font=("", 72),overrelief="solid", command=btnStartCal)
        btnStart.place(x=10, y=10)  # 버튼 위치
    elif mode == val_mode:
        if gMode == OQC:
            root.title("VST Validation : OQC")  # UI창 제목
        elif gMode == DAILY_CHECK:
            root.title("VST Validation : Daily check")  # UI창 제목
        elif gMode == VALIDATION_SIMPLE:
            root.title("VST Validation 2")  # UI창 제목
        else :
            root.title("VST Validation")  # UI창 제목
        btnStart = Button(root, text='Ready', font=("", 72),overrelief="solid", command=btnStartVal)
        btnStart.place(x=10, y=10)  # 버튼 위치
    else:
        exit()


    # 리스트 박스 생성
    listbox = Listbox(root, width=59, height=35)
    listbox.place(x=10, y=210)

    root.mainloop()


if __name__ == "__main__" :

    # todo 1. 관리자 모드로 실행했는지 확인한다.
    checkAdministrator()

    # todo 2. 검사 모드를 확인한다.
    is_mode = checktomode()
    if is_mode == 999:
        print(f'Please, check to Validation mode.')
    gMode=0
    # todo 3. 검사 시작한다.
    init(val_mode)

    # todo 4. 종료 한다.
    # 창 우상단의 'X'버튼 클릭시 동작 함수
    root.protocol('WM_DELETE_WINDOW', exit())





