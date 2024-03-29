from __future__ import with_statement
import datetime  # 현재 시간 출력용
import os
import os.path
import subprocess
# import thread
import shutil
import psutil
import sys
import time  # sleep 함수 사용
import numpy as np
import motion  # 모터
import python_ezimotor_api  # 모터
import python_simmian_api
import pandas as pd  # pip install pandas
import struct
import logging
from waiting import wait
import winsys  # pip install winsys
import python_vst_eepromparser_api as writeToeeprom


# 심미안 ===============================================
SimmianLauncher = f'C:\\Program Files\\NxSimmian\\NxSimmian v1.3.7.0\\SimmianLauncher.exe'
# =====================================================


# motor ===============================================
gMotor = -1
# motion_dist500 = 397.8
motion_dist500 = 399.7
# 3m 실거리 -> 2023_03_15, DV1차 모듈바닥에서 차트까지 간격은 521.6mm 로 세팅 : 모터값 433
# isMedia -> 2023_04_19, DV1차 모듈바닥에서 차트까지 간격은 521.6mm 로 세팅 : 모터값 93

motion_dist300 = 195.5
# 3m 실거리 -> 2023_03_15, DV1차 모듈바닥에서 차트까지 간격은 321.6mm 로 세팅 : 모터값 228
# isMedia -> 2023_04_19, DV1차 모듈바닥에서 차트까지 간격은 321.6mm 로 세팅 : 모터값 308
# =====================================================


# cal_data
#####################################################
gBoard_offset_f1 = f''
gBoard_offset_f2 = f''
gDeviceID = 0xA0
gStartAddress_f1 = f'0x0108'    # cal_data영역에서 f1(100Mhz)board_offset 주소
gEndAddress_f1 = f'0x0109'      # cal_data영역에서 f1(100Mhz)board_offset 주소
gStartAddress_f2 = f'0x010A'    # cal_data영역에서 f2(20Mhz)board_offset 주소
gEndAddress_f2 = f'0x010B'      # cal_data영역에서 f2(20Mhz)board_offset 주소
#####################################################


# Configuration about Image Capture
#####################################################
gRootPath = os.path.dirname(os.path.abspath(__file__))
gOutputFilePrefix = f'Image'
gRootSavePath = f'%s\%s' % (f'C:\LSI_VST63D', f'save')
gOutputDirPrefix = f'image'
gCaptureCnt = 3
gMotorSettleTimeSec = 3
g_find_offset_cycle = 0
#####################################################

# log
#####################################################
glogpath = f'%s\%s' % (gRootSavePath, f'validation.log')
#####################################################


# Configuration about Set File for Validation
#####################################################
GLOBAL_OFFSET = 0
EVALUATION = 1
ERROR = 2

VALIDATION = 0
OQC = 1
DAILY_CHECK = 2
VALIDATION_SIMPLE = 3

gRootSetFilePath = f'%s\%s' % (f'C:\LSI_VST63D', f'save')
gSaveModulePath = f' '
mode_type = 1
g100MHzSetFileName = f'[val]63D_EVT0p1_QVGA_A_C02_M1_R300_D60_SINGLE_100M_FLOOD_DPHY960_AE_MIPI960_cal_maskoff_CalOff_2J.set'
g20MHzSetFileName = f'[val]63D_EVT0p1_QVGA_A_C02_M1_R300_D60_SINGLE_20M_FLOOD_DPHY960_AE_MIPI960_cal_maskoff_CalOff_2J.set'
g100MHzSetFilePath = f' '
g20MHzSetFilePath = f' '
g20mhz30cm = f' '
g20mhz50cm = f' '
g100mhz30cm = f' '
g100mhz50cm = f' '
gDepth_U16 = f'DEPTH_U16'
gIntensity = f'INTENSITY'
gBinFileName = f'_ToF_cal_100MHz.bin'
gResult = np.zeros((100, 21))  # dtypr 설정 안해주면 기본값 float64
g100mhzDepthValue = 0
g20mhzDepthValue = 0
gLSLGuardSpec = 497
gUSLGuardSpec = 503

JudgeResult_f1 = [0 for i in range(21)]
JudgeResult_f2 = [0 for i in range(21)]
JudgeResult = [0 for i in range(21)]
#####################################################


# Configuration about Create Set File
#####################################################
gRootPathOriginalSetFile = f'%s\%s' % (os.path.dirname(os.path.abspath(__file__)), f'create_setfile')
gBatchPath100MHz = f'%s\%s' % (gRootPathOriginalSetFile, f'1.bat')
gBatchPath20MHz = f'%s\%s' % (gRootPathOriginalSetFile, f'2.bat')

#####################################################


# APC Check
#####################################################
setregvalue = 0 # 검증3차 루멘터 '4' , 사전bring-up 투식스 '0'
gApc_check_at_lsw_fix1_f1 = 0
gApc_check_at_lsw_fix2_f1 = 0
gApc_check_at_lsw_fix1_f2 = 0
gApc_check_at_lsw_fix2_f2 = 0
#####################################################


# Sensor ID
#####################################################
gSensor_id = f''
gSensor_id_dec = [0 for i in range(16)]
#####################################################

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

gCurrPath = os.getcwd()
simmian = python_simmian_api.Simmian()


def os_system(path):
    os.system(path)


def init_():
    re = simmian.Play()
    time.sleep(0.010)  # 10ms
    if re:
        msg_print(f'Success, it can turn on.')
        simmian.SetDecoder('ToF')
        return PASS
    else:
        msg_print(f'Failure, it can not turn on.')
        return FAIL_SIMMIAN_INIT




def StopSimmian():
    re = simmian.Stop()
    time.sleep(0.010)  # 10ms
    if re:
        msg_print(f'Success, it can stop.')
    else:
        msg_print(f'Failure, it can not stop.')
        return False


def ResetSimmian():
    try:
        re = simmian.Stop()
        time.sleep(0.1)  # 100ms
        re = simmian.Reset()
        time.sleep(0.1)  # 100ms
        re = simmian.Play()
        time.sleep(0.1)  # 100ms
        if re == False:
            return FAIL_SIMMIAN_INIT

        return PASS

    except Exception as e:
        print(e)
        return FAIL_SIMMIAN_INIT


def DisconnetSimmian():
    re = simmian.Disconnect()
    if re:
        msg_print(f'Success, it can disconnect.')
    else:
        msg_print(f'Failure, it can not disconnect. ')
        return False


def DoCapture(prefix, path):
    simmian.SequentialCapture(prefix, path, gCaptureCnt)  # 시퀀셜캡처는 RAW저장 시간이 매우 느리다.
    msg_print("  Done")


def DoSingleCapture(prefix, path):
    filePath = r"%s\%s_.raw" % (path, prefix)
    msg_print(f'  save path : {filePath}' )
    result = simmian.Capture(filePath, captureCount=1)


def create_folder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        msg_print('  Error: Creating directory. {0}'.format(directory))


def delayMicroseconds(usec):
    start = time.time()
    end = start + (usec * 0.000001)
    while time.time() < end:
        pass
    return


def WriteCmd(id, addr, val):
    page_str = '0x' + format(addr, '08X')[0:4]
    addr_str = '0x' + format(addr, '08X')[4:8]
    val_str = '0x' + format(val, '04X')
    simmian.WriteI2C(id, '0x6028', page_str)
    time.sleep(0.010)  # 10ms
    simmian.WriteI2C(id, '0x602A', addr_str)
    time.sleep(0.010)  # 10ms
    simmian.WriteI2C(id, '0x6F12', val_str)
    time.sleep(0.010)  # 10ms
    return


def ReadCmd(id, addr, num):
    page_str = '0x' + format(addr, '08X')[0:4]
    addr_str = '0x' + format(addr, '08X')[4:8]
    simmian.WriteI2C(id, '0x602C', page_str)
    time.sleep(0.010)  # 10ms
    simmian.WriteI2C(id, '0x602E', addr_str)
    time.sleep(0.010)  # 10ms
    val = simmian.ReadI2C(id, '0x6F12', num)
    time.sleep(0.010)  # 10ms
    return val


def SetVcselCurrent(current_mA):
    current_code = int(current_mA / 12)  # val = mA / 12
    WriteCmd(0x20, 0x2000CF30, 0x0001)  # number of write bytes
    WriteCmd(0x20, 0x2000CF32, 0x0008)  # register address of VCSEL Driver
    WriteCmd(0x20, 0x2000CF34, current_code)  # data for 0x08
    WriteCmd(0x20, 0x2000CF36, 0x00FF)  # Delay command
    WriteCmd(0x20, 0x2000CF38, 0x000F)  # Data for Delay, 13.3us
    WriteCmd(0x20, 0x2000CF3A, 0x0000)  # Terminates command array
    WriteCmd(0x20, 0x2000CF70, 0x0001)  # data at end address
    #str = ("Setting done: ", current_mA, "mA")
    #msg_print(str)


def ReadPdValue():
    WriteCmd(0x20, 0x2000CF9A, 0x0001)  # read operation_per_frame
    WriteCmd(0x20, 0x2000CF72, 0x0023)  # CHECK_APC_IMOD[9:8], PD value
    WriteCmd(0x20, 0x2000CF74, 0xFFFF)  # termination code
    WriteCmd(0x20, 0x2000CF9E, 0x0001)  #
    CHECK_APC_IMOD_B9_B8 = ReadCmd(0x20, 0x2000CF86, 2)  # Read two bytes. (Return value, Use 2nd value)
    CHECK_APC_IMOD_B9_B8 = (CHECK_APC_IMOD_B9_B8 & 0xFF)

    WriteCmd(0x20, 0x2000CF9A, 0x0001)  # read operation_per_frame
    WriteCmd(0x20, 0x2000CF72, 0x0026)  # CHECK_APC_IMOD[7:0], PD value
    WriteCmd(0x20, 0x2000CF74, 0xFFFF)  # termination code
    WriteCmd(0x20, 0x2000CF9E, 0x0001)  #
    CHECK_APC_IMOD_B7_B0 = ReadCmd(0x20, 0x2000CF86, 2)  # Read two bytes. (Return value, Use 2nd value)
    CHECK_APC_IMOD_B7_B0 = (CHECK_APC_IMOD_B7_B0 & 0xFF)

    pd_val = (((CHECK_APC_IMOD_B9_B8 & 0x20) >> 5) * (2 ** 9)) + (((CHECK_APC_IMOD_B9_B8 & 0x10) >> 4) * (2 ** 8)) + (
        CHECK_APC_IMOD_B7_B0)
    #str1 = ("PD value[7:0] = ", hex(CHECK_APC_IMOD_B7_B0))
    #str2 = ("PD value[9:8] = ", hex(CHECK_APC_IMOD_B9_B8 & 0x30))
    #msg_print(str1)
    #msg_print(str2)

    return pd_val


def SetRegisterPD(register):
    # 000: Open, 001: 0.5kOhm, 010: 1.0kOhm, 011: 1.5kOhm
    # 100: 3.0kOhm, others : Open
    register_code = register << 4
    WriteCmd(0x20, 0x2000CF30, 0x0001)  # number of write bytes
    WriteCmd(0x20, 0x2000CF32, 0x000E)  # register address of VCSEL Driver
    WriteCmd(0x20, 0x2000CF34, register_code)  # data for 0x08
    WriteCmd(0x20, 0x2000CF36, 0x00FF)  # Delay command
    WriteCmd(0x20, 0x2000CF38, 0x000F)  # Data for Delay, 13.3us
    WriteCmd(0x20, 0x2000CF3A, 0x0000)  # Terminates command array
    WriteCmd(0x20, 0x2000CF70, 0x0001)  # data at end address
    # print("Setting done: ", hex(register_code), " code")


def APCCheck(freq):
    # APC 변수 초기화
    global gApc_check_at_lsw_fix1_f1, gApc_check_at_lsw_fix2_f1, gApc_check_at_lsw_fix1_f2, gApc_check_at_lsw_fix2_f2, JudgeResult_f1,JudgeResult_f2

    SetRegisterPD(setregvalue)  # 투식스 TX -> setregvalue = 0
    time.sleep(0.100)  # 100ms

    if freq == 100:
        gApc_check_at_lsw_fix1_f1 = 0   # 2700 mA
        gApc_check_at_lsw_fix2_f1 = 0   # 1500 mA

        # 100Mhz(f1), 2700mA(fix1), fix1_f1 ****************************************************************************
        SetVcselCurrent(2700)  # 1st current: 2700mA
        gApc_check_at_lsw_fix1_f1 = ReadPdValue()  # value = ReadPdValue()

        # TX의 PD값이 100 이하이면 올바르게 읽히지 않은 것으로 판단하고 다시 읽어본다.
        if gApc_check_at_lsw_fix1_f1 < 100:
            gApc_check_at_lsw_fix1_f1 = ReadPdValue()  # value = ReadPdValue()

        littleEndian_gApc_check_at_lsw_fix1_f1 = HEXLittleEndian(gApc_check_at_lsw_fix1_f1)

        simmian.WriteI2C(0xA0, "0x00d2", littleEndian_gApc_check_at_lsw_fix1_f1)
        time.sleep(0.010)  # 10ms
        new_gApc_check_at_lsw_fix1_f1 = simmian.ReadI2C(0xA0, "0x00d2", 2)
        time.sleep(0.010)  # 10ms
        msg_print(f'PD val 100MHz at 2700mA = [measure] {gApc_check_at_lsw_fix1_f1}, {hex(gApc_check_at_lsw_fix1_f1)} , [e2p] {hex(new_gApc_check_at_lsw_fix1_f1)}')

        # 100Mhz(f1), 1500mA(fix2), fix2_f1 ****************************************************************************
        SetVcselCurrent(1500)  # 1st current: 1500mA
        gApc_check_at_lsw_fix2_f1 = ReadPdValue()  # value = ReadPdValue()

        # TX의 PD값이 100 이하이면 올바르게 읽히지 않은 것으로 판단하고 다시 읽어본다.
        if gApc_check_at_lsw_fix2_f1 < 100:
            gApc_check_at_lsw_fix2_f1 = ReadPdValue()  # value = ReadPdValue()

        littleEndian_gApc_check_at_lsw_fix2_f1 = HEXLittleEndian(gApc_check_at_lsw_fix2_f1)

        simmian.WriteI2C(0xA0, "0x00d4", littleEndian_gApc_check_at_lsw_fix2_f1)
        time.sleep(0.010)  # 10ms
        new_gApc_check_at_lsw_fix2_f1 = simmian.ReadI2C(0xA0, "0x00d4", 2)
        time.sleep(0.010)  # 10ms
        msg_print(f'PD val 100MHz at 1500mA = [measure] {gApc_check_at_lsw_fix2_f1}, {hex(gApc_check_at_lsw_fix2_f1)}, [e2p] {hex(new_gApc_check_at_lsw_fix2_f1)} ')

        JudgeResult_f1[18] = gApc_check_at_lsw_fix1_f1
        JudgeResult_f1[19] = gApc_check_at_lsw_fix2_f1

    elif freq == 20:
        gApc_check_at_lsw_fix1_f2 = 0   # 2700 mA
        gApc_check_at_lsw_fix2_f2 = 0   # 1500 mA

        # 20Mhz(f2), 2700mA(fix1), fix1_f2 *****************************************************************************
        SetVcselCurrent(2700)  # 1st current: 2700mA
        gApc_check_at_lsw_fix1_f2 = ReadPdValue()  # value = ReadPdValue()

        # TX의 PD값이 100 이하이면 올바르게 읽히지 않은 것으로 판단하고 다시 읽어본다.
        if gApc_check_at_lsw_fix1_f2 < 100:
            gApc_check_at_lsw_fix1_f2 = ReadPdValue()  # value = ReadPdValue()

        littleEndian_gApc_check_at_lsw_fix1_f2 = HEXLittleEndian(gApc_check_at_lsw_fix1_f2)

        simmian.WriteI2C(0xA0, "0x00d6", littleEndian_gApc_check_at_lsw_fix1_f2)
        time.sleep(0.010)  # 10ms
        new_gApc_check_at_lsw_fix1_f2 = simmian.ReadI2C(0xA0, "0x00d6", 2)
        time.sleep(0.010)  # 10ms
        msg_print(f'PD val 020MHz at 2700mA = [measure] {gApc_check_at_lsw_fix1_f2}, {hex(gApc_check_at_lsw_fix1_f2)}, [e2p] {hex(new_gApc_check_at_lsw_fix1_f2)} ')

        # 20Mhz(f2), 1500mA(fix2), fix2_f2 *****************************************************************************
        SetVcselCurrent(1500)  # 1st current: 1500mA

        gApc_check_at_lsw_fix2_f2 = ReadPdValue()  # value = ReadPdValue()

        # TX의 PD값이 100 이하이면 올바르게 읽히지 않은 것으로 판단하고 다시 읽어본다.
        if gApc_check_at_lsw_fix2_f2 < 100:
            gApc_check_at_lsw_fix2_f2 = ReadPdValue()  # value = ReadPdValue()

        littleEndian_gApc_check_at_lsw_fix2_f2 = HEXLittleEndian(gApc_check_at_lsw_fix2_f2)

        simmian.WriteI2C(0xA0, "0x00d8", littleEndian_gApc_check_at_lsw_fix2_f2)
        time.sleep(0.010)  # 10ms
        new_gApc_check_at_lsw_fix2_f2 = simmian.ReadI2C(0xA0, "0x00d8", 2)
        time.sleep(0.010)  # 10ms
        msg_print(f'PD val 020MHz at 1500mA = [measure] {gApc_check_at_lsw_fix2_f2} , {hex(gApc_check_at_lsw_fix2_f2)}, [e2p] {hex(new_gApc_check_at_lsw_fix2_f2)}')

        JudgeResult_f2[18] = gApc_check_at_lsw_fix1_f2
        JudgeResult_f2[19] = gApc_check_at_lsw_fix2_f2

    else:
        msg_print("Error!!! -> APC Check")

    # SetRegisterPD(setregvalue)


def judge_error_code(freq, data):

    if freq == 100:
        # Todo Z축 오차(error)
        if data[0]!= True or data[1]!= True or data[2]!= True or data[3]!= True or data[4]!= True or data[5]!= True:
            msg_print(f'FAIL, -> FAIL_Z_ERROR_100')
            return FAIL_Z_ERROR_100
        # Todo Z축 잡음(noise)
        elif data[6]!= True or data[7]!= True or data[8]!= True or data[9]!= True or data[10]!= True:
            msg_print(f'FAIL, -> FAIL_Z_NOISE_100')
            return FAIL_Z_NOISE_100
        # Todo VCSEL 광량 레벨
        elif data[11]!= True or data[12]!= True or data[13]!= True or data[14]!= True or data[15]!= True:
            msg_print(f'FAIL, -> FAIL_VCSEL_POWER_100')
            return FAIL_VCSEL_POWER_100
        # Todo APC_CHECK
        elif data[16]!= True or data[17]!= True:
            msg_print(f'FAIL, -> FAIL_APC_CHECK_100')
            return FAIL_APC_CHECK_100
        else:
            return PASS
    elif freq == 20:
        # Todo Z축 오차(error)
        if data[0]!= True or data[1]!= True or data[2]!= True or data[3]!= True or data[4]!= True or data[5]!= True:
            msg_print(f'FAIL, -> FAIL_Z_ERROR_20')
            return FAIL_Z_ERROR_20
        # Todo Z축 잡음(noise)
        elif data[6]!= True or data[7]!= True or data[8]!= True or data[9]!= True or data[10]!= True:
            msg_print(f'FAIL, -> FAIL_Z_NOISE_20')
            return FAIL_Z_NOISE_20
        # Todo VCSEL 광량 레벨
        elif data[11]!= True or data[12]!= True or data[13]!= True or data[14]!= True or data[15]!= True:
            msg_print(f'FAIL, -> FAIL_VCSEL_POWER_20')
            return FAIL_VCSEL_POWER_20
        # Todo APC_CHECK
        elif data[16]!= True or data[17]!= True:
            msg_print(f'FAIL, -> FAIL_APC_CHECK_20')
            return FAIL_APC_CHECK_20
        else:
            return PASS
    else:
        # Todo Z축 오차(error)
        if data[0]!= True or data[1]!= True or data[2]!= True or data[3]!= True or data[4]!= True or data[5] != True:
            msg_print(f'FAIL, -> FAIL_Z_ERROR')
            return FAIL_Z_ERROR
        # Todo Z축 잡음(noise)
        elif data[6]!= True or data[7]!= True or data[8]!= True or data[9]!= True or data[10] != True:
            msg_print(f'FAIL, -> FAIL_Z_NOISE')
            return FAIL_Z_NOISE
        # Todo VCSEL 광량 레벨
        elif data[11]!= True or data[12]!= True or data[13]!= True or data[14]!= True or data[15] != True:
            msg_print(f'FAIL, -> FAIL_VCSEL_POWER')
            return FAIL_VCSEL_POWER
        # Todo APC_CHECK
        elif data[16]!= True or data[17] != True:
            msg_print(f'FAIL, -> FAIL_APC_CHECK')
            return FAIL_APC_CHECK
        else:
            return PASS


def find_judge(mode, freq, data, indexCount):
    global GLOBAL_OFFSET

    # Todo 2023-06-13 : Gen2 DV1-5 Validation (Depth 성능측정)
    if freq == 100:
        # ■ 500mm Depth Validation Data_f1 (QVGA)
        DepthErrorAVG500_Spec_Center    = 15      # Todo Z축 오차(Error) - Depth mean of Center ROI : 15 mm
        DepthErrorAVG500_Spec_06Field   = 40      # Todo Z축 오차(Error) - Depth mean of 0.6F ROI (LT,RT,RB,LB) : 40 mm
        DepthNoiseAVG500_Spec_Center    = 7       # Todo Z축 잡음(Noise) - Depth Noise of Center ROI : 7 mm
        DepthNoiseAVG500_Spec_06Field   = 7       # Todo Z축 잡음(Noise) - Depth Noise of 0.6F ROI (LT,RT,RB,LB) : 7 mm

        # ■ 500mm VCSEL Optical Power Data_f1 (광량검사 데이터)
        ConfidenceAVG_Spec_CenterLower  = 2700    # Todo 픽셀 밝기 레벨 - Center ROI : 2700 ~ 5700
        ConfidenceAVG_Spec_CenterUpper  = 5700    # Todo 픽셀 밝기 레벨 - Center ROI : 2700 ~ 5700
        ConfidenceAVG_Spec_06FieldLower = 2600    # Todo 픽셀 밝기 레벨 - 0.6F ROI (LT, RT, RB, LB) : 2600 ~ 5600
        ConfidenceAVG_Spec_06FieldUpper = 5600    # Todo 픽셀 밝기 레벨 - 0.6F ROI (LT, RT, RB, LB) : 2600 ~ 5600

        # ■ 300mm Depth Validation Data_f1
        DepthErrorAVG300_Spec_Center = 24         # Todo Z축 오차(Error) - Depth mean of center ROI

    else:
        # ■ 500mm Depth Validation Data_f2 (QVGA)
        DepthErrorAVG500_Spec_Center    = 15      # Todo Z축 오차(Error) - Depth mean of Center ROI : 15 mm
        DepthErrorAVG500_Spec_06Field   = 50      # Todo Z축 오차(Error) - Depth mean of 0.4F ROI (LT,RT,RB,LB) : 50 mm
        DepthNoiseAVG500_Spec_Center    = 10      # Todo Z축 잡음(Noise) - Depth Noise of Center ROI : 10 mm
        DepthNoiseAVG500_Spec_06Field   = 10      # Todo Z축 잡음(Noise) - Depth Noise of 0.4F ROI (LT,RT,RB,LB) : 10 mm

        # ■ 500mm VCSEL Optical Power Data_f2 (광량검사 데이터)
        ConfidenceAVG_Spec_CenterLower  = 17000   # Todo 픽셀 밝기 레벨 - Center ROI : 17000 ~ 22000
        ConfidenceAVG_Spec_CenterUpper  = 22000   # Todo 픽셀 밝기 레벨 - Center ROI : 17000 ~ 22000
        ConfidenceAVG_Spec_06FieldLower = 11000   # Todo 픽셀 밝기 레벨 - 0.6F ROI (LT, RT, RB, LB) : 11000 ~ 20000
        ConfidenceAVG_Spec_06FieldUpper = 20000   # Todo 픽셀 밝기 레벨 - 0.6F ROI (LT, RT, RB, LB) : 11000 ~ 20000

        # ■ 300mm Depth Validation Data_f2
        DepthErrorAVG300_Spec_Center = 30         # Todo Z축 오차(Error) - Depth mean of center ROI

    # ■ APC_CHECK, Todo Single Frequency -> 100 MHz
    lsl_lsw_fix1_f1 = 600                         # Todo APC_CHECK - 100 MHz - 2700 mA - LSL
    usl_lsw_fix1_f1 = 850                         # Todo APC_CHECK - 100 MHz - 2700 mA - USL
    lsl_lsw_fix2_f1 = 320                         # Todo APC_CHECK - 100 MHz - 1500 mA - LSL
    usl_lsw_fix2_f1 = 520                         # Todo APC_CHECK - 100 MHz - 1500 mA - USL

    # ■ APC_CHECK, Todo Single Frequency -> 20 MHz
    lsl_lsw_fix1_f2 = 600                         # Todo APC_CHECK -  20 MHz - 2700 mA - LSL
    usl_lsw_fix1_f2 = 850                         # Todo APC_CHECK -  20 MHz - 2700 mA - USL
    lsl_lsw_fix2_f2 = 320                         # Todo APC_CHECK -  20 MHz - 1500 mA - LSL
    usl_lsw_fix2_f2 = 520                         # Todo APC_CHECK -  20 MHz - 1500 mA - USL


    # Todo Z축 오차(Error) - 중심 - 300mm *****************************************************************
    _b300mm_Depth_Validation_Data_f1_01F_CT_ROI = False

    f1_1 = data[0]  # 300 CT Error
    if (300 - DepthErrorAVG300_Spec_Center) <= f1_1 and (300 + DepthErrorAVG300_Spec_Center) >= f1_1:
        _b300mm_Depth_Validation_Data_f1_01F_CT_ROI = True

    JudgeResult[0] = _b300mm_Depth_Validation_Data_f1_01F_CT_ROI
    msg_print(f'{_b300mm_Depth_Validation_Data_f1_01F_CT_ROI} 300 CT Error ')

    # Todo Z축 오차(Error) *******************************************************************************
    _b500mm_Depth_Validation_Data_f1_Depth_mean_of_01F_CT_ROI = False
    _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_LT_ROI = False
    _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_RT_ROI = False
    _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_RB_ROI = False
    _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_LB_ROI = False

    # Todo Z축 오차(Error) - 중심
    # // 판정 비교 : 500mm Depth Validation Data_f1 (QVGA) -> Depth mean of center ROI
    f1_2 = data[1]
    if (500 - DepthErrorAVG500_Spec_Center) <= f1_2 and (500 + DepthErrorAVG500_Spec_Center) >= f1_2:
        _b500mm_Depth_Validation_Data_f1_Depth_mean_of_01F_CT_ROI = True

    JudgeResult[1] = _b500mm_Depth_Validation_Data_f1_Depth_mean_of_01F_CT_ROI
    msg_print(f'{_b500mm_Depth_Validation_Data_f1_Depth_mean_of_01F_CT_ROI} 500 mm, Depth mean of center ROI ')

    # Todo Z축 오차(Error) - 주변(0.6f) - LT
    # // 판정 비교 : 500mm Depth Validation Data_f1 (QVGA) -> Depth mean of 0.6F LT ROI
    f1_3 = data[2]
    if (500 - DepthErrorAVG500_Spec_06Field) <= f1_3 and (500 + DepthErrorAVG500_Spec_06Field) >= f1_3:
        _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_LT_ROI = True

    JudgeResult[2] = _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_LT_ROI
    msg_print(f'{_b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_LT_ROI} 500 mm, Depth mean of 0.6F LT ROI ')

    # Todo Z축 오차(Error) - 주변(0.6f) - RT
    f1_4 = data[3]
    if (500 - DepthErrorAVG500_Spec_06Field) <= f1_4 and (500 + DepthErrorAVG500_Spec_06Field) >= f1_4:
        _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_RT_ROI = True

    JudgeResult[3] = _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_RT_ROI
    msg_print(f'{_b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_RT_ROI} 500 mm, Depth mean of 0.6F RT ROI ')

    # Todo Z축 오차(Error) - 주변(0.6f) - RB
    f1_5 = data[4]
    if (500 - DepthErrorAVG500_Spec_06Field) <= f1_5 and (500 + DepthErrorAVG500_Spec_06Field) >= f1_5:
        _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_RB_ROI = True

    JudgeResult[4] = _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_RB_ROI
    msg_print(f'{_b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_RB_ROI} 500 mm, Depth mean of 0.6F RB ROI ')

    # Todo Z축 오차(Error) - 주변(0.6f) - LB
    f1_6 = data[5]
    if (500 - DepthErrorAVG500_Spec_06Field) <= f1_6 and (500 + DepthErrorAVG500_Spec_06Field) >= f1_6:
        _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_LB_ROI = True

    JudgeResult[5] = _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_LB_ROI
    msg_print(f'{_b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_LB_ROI} 500 mm, Depth mean of 0.6F LB ROI ')

    # Todo Z축 잡음(Noise) *****************************************************************************
    _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_01F_CT_ROI = False
    _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_LT_ROI = False
    _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_RT_ROI = False
    _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_RB_ROI = False
    _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_LB_ROI = False

    # Todo Z축 잡음(Noise) - 중심
    f1_7 = data[6]
    if DepthNoiseAVG500_Spec_Center >= f1_7:
        _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_01F_CT_ROI = True

    JudgeResult[6] = _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_01F_CT_ROI
    msg_print(f'{_b500mm_Depth_Validation_Data_f1_Validation_Noise_of_01F_CT_ROI} 500 mm, Validation Noise of center ROI ')

    # Todo Z축 잡음(Noise) - 주변(0.6f) - LT
    f1_8 = data[7]
    if DepthNoiseAVG500_Spec_06Field >= f1_8:
        _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_LT_ROI = True

    JudgeResult[7] = _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_LT_ROI
    msg_print(f'{_b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_LT_ROI} 500 mm, Validation Noise of 0.6F ROI -> LT ')

    # Todo Z축 잡음(Noise) - 주변(0.6f) - RT
    f1_9 = data[8]
    if DepthNoiseAVG500_Spec_06Field >= f1_9:
        _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_RT_ROI = True

    JudgeResult[8] = _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_RT_ROI
    msg_print(f'{_b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_RT_ROI} 500 mm, Validation Noise of 0.6F ROI -> RT ')

    # Todo Z축 잡음(Noise) - 주변(0.6f) - RB
    f1_10 = data[9]
    if DepthNoiseAVG500_Spec_06Field >= f1_10:
        _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_RB_ROI = True

    JudgeResult[9] = _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_RB_ROI
    msg_print(f'{_b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_RB_ROI} 500 mm, Validation Noise of 0.6F ROI -> RB ')

    # Todo Z축 잡음(Noise) - 주변(0.6f) - LB
    f1_11 = data[10]
    if DepthNoiseAVG500_Spec_06Field >= f1_11:
        _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_LB_ROI = True

    JudgeResult[10] = _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_LB_ROI
    msg_print(f'{_b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_LB_ROI} 500 mm, Validation Noise of 0.6F ROI -> LB ')

    # Todo 픽셀 밝기 레벨 **********************************************************************************
    _b500mm_VCSEL_Optical_Power_Data_01F_CT_ROI = False
    _b500mm_VCSEL_Optical_Power_Data_06F_LT_ROI = False
    _b500mm_VCSEL_Optical_Power_Data_06F_RT_ROI = False
    _b500mm_VCSEL_Optical_Power_Data_06F_RB_ROI = False
    _b500mm_VCSEL_Optical_Power_Data_06F_LB_ROI = False

    # Todo 픽셀 밝기 레벨 - 중심
    f1_12 = data[11]
    if ConfidenceAVG_Spec_CenterLower <= f1_12 and ConfidenceAVG_Spec_CenterUpper >= f1_12:
        _b500mm_VCSEL_Optical_Power_Data_01F_CT_ROI = True

    JudgeResult[11] = _b500mm_VCSEL_Optical_Power_Data_01F_CT_ROI
    msg_print(f'{_b500mm_VCSEL_Optical_Power_Data_01F_CT_ROI} Optical Power Data CT ')

    # Todo 픽셀 밝기 레벨 - 주변(0.6f) - LT
    f1_13 = data[12]
    if ConfidenceAVG_Spec_06FieldLower <= f1_13 and ConfidenceAVG_Spec_06FieldUpper >= f1_13:
        _b500mm_VCSEL_Optical_Power_Data_06F_LT_ROI = True

    JudgeResult[12] = _b500mm_VCSEL_Optical_Power_Data_06F_LT_ROI
    msg_print(f'{_b500mm_VCSEL_Optical_Power_Data_06F_LT_ROI} Optical Power Data LT ')

    # Todo 픽셀 밝기 레벨 - 주변(0.6f) - RT
    f1_14 = data[13]
    if ConfidenceAVG_Spec_06FieldLower <= f1_14 and ConfidenceAVG_Spec_06FieldUpper >= f1_14:
        _b500mm_VCSEL_Optical_Power_Data_06F_RT_ROI = True

    JudgeResult[13] = _b500mm_VCSEL_Optical_Power_Data_06F_RT_ROI
    msg_print(f'{_b500mm_VCSEL_Optical_Power_Data_06F_RT_ROI} Optical Power Data RT ')

    # Todo 픽셀 밝기 레벨 - 주변(0.6f) - RB
    f1_15 = data[14]
    if ConfidenceAVG_Spec_06FieldLower <= f1_15 and ConfidenceAVG_Spec_06FieldUpper >= f1_15:
        _b500mm_VCSEL_Optical_Power_Data_06F_RB_ROI = True

    JudgeResult[14] = _b500mm_VCSEL_Optical_Power_Data_06F_RB_ROI
    msg_print(f'{_b500mm_VCSEL_Optical_Power_Data_06F_RB_ROI} Optical Power Data RB ')

    # Todo 픽셀 밝기 레벨 - 주변(0.6f) - LB
    f1_16 = data[15]
    if ConfidenceAVG_Spec_06FieldLower <= f1_16 and ConfidenceAVG_Spec_06FieldUpper >= f1_16:
        _b500mm_VCSEL_Optical_Power_Data_06F_LB_ROI = True

    JudgeResult[15] = _b500mm_VCSEL_Optical_Power_Data_06F_LB_ROI
    msg_print(f'{_b500mm_VCSEL_Optical_Power_Data_06F_LB_ROI} Optical Power Data LB ')

    # Todo APC_CHECK 2700mA / 1500mA
    b100mhz_apc_lsw_fix1_f1 = False
    b100mhz_apc_lsw_fix2_f1 = False
    b20mhz_apc_lsw_fix1_f2 = False
    b20mhz_apc_lsw_fix2_f2 = False
    apc_lsw_fix1 = False # Todo 2700 mA
    apc_lsw_fix2 = False # Todo 1500 mA


    if freq == 100: # Todo APC_CHECK -> 100MHz
        # Todo 100MHz -> 2700mA 판정 :
        if gApc_check_at_lsw_fix1_f1 >= lsl_lsw_fix1_f1 and gApc_check_at_lsw_fix1_f1 <= usl_lsw_fix1_f1:
            apc_lsw_fix1 = True

        JudgeResult[16] = apc_lsw_fix1 # Todo 결과
        msg_print(f'{apc_lsw_fix1} 100 MHz, apc_lsw_fix1_f1')

        # Todo 100MHz -> 1500mA 판정 :
        if gApc_check_at_lsw_fix2_f1 >= lsl_lsw_fix2_f1 and gApc_check_at_lsw_fix2_f1 <= usl_lsw_fix2_f1:
            apc_lsw_fix2 = True

        JudgeResult[17] = apc_lsw_fix2 # Todo 결과
        msg_print(f'{apc_lsw_fix2} 100 MHz, apc_lsw_fix2_f1')

    else: # Todo APC_CHECK -> 20MHz
        # Todo 20MHz -> 2700mA 판정 :
        if gApc_check_at_lsw_fix1_f2 >= lsl_lsw_fix1_f2 and gApc_check_at_lsw_fix1_f2 <= usl_lsw_fix1_f2:
            apc_lsw_fix1 = True

        JudgeResult[16] = apc_lsw_fix1 # Todo 결과
        msg_print(f'{apc_lsw_fix1} 20 MHz, apc_lsw_fix1_f2')

        # Todo 20MHz -> 1500mA 판정 :
        if gApc_check_at_lsw_fix2_f2 >= lsl_lsw_fix2_f2 and gApc_check_at_lsw_fix2_f2 <= usl_lsw_fix2_f2:
            apc_lsw_fix2 = True

        JudgeResult[17] = apc_lsw_fix2 # Todo 결과
        msg_print(f'{apc_lsw_fix2} 20 MHz, apc_lsw_fix2_f2')

    if mode == GLOBAL_OFFSET:   # Todo global_offset 검사 결과 -> (0.1f)중심 평가만 한다
        if _b500mm_Depth_Validation_Data_f1_Depth_mean_of_01F_CT_ROI != True:
            msg_print(f'global offset {freq} Mhz Result -> FAIL ')
            return FAIL_Z_ERROR

        msg_print(f'global offset {freq} Mhz Result -> PASS ')
        return PASS

    else:                       # Todo EVALUATION 검사 결과
        result_judge = judge_error_code(freq, JudgeResult)
        if result_judge != PASS :
            msg_print(f'FAIL -> {freq}MHz Result')
            return result_judge

        msg_print(f'PASS -> {freq} MHz Result')
        return PASS


def create_DB(sensorid, result100, result20):
    file_path = r'{0}\validation.csv'.format(gRootSavePath)
    f = open(file_path, 'a')
    f.write(sensorid + ',' + 'validation' + ',' + result100 + ',' + result20 + ',' + time.strftime('%Y-%m-%d', time.localtime(
        time.time()))+',\n')
    f.close()


def create_report(mode, Path, Result, indexCount):
    global gSensor_id
    # summary 엑셀 출력
    df = pd.DataFrame(Result)
    file_path = r'{0}\{1}_{2}.csv'.format(Path, gSensor_id, f'summary')

    if not os.path.exists(file_path):
        df.to_csv(file_path, index=False, mode='w', header=False)
    else:
        df.to_csv(file_path, index=False, mode='a', header=False)

    # 100 MHz : 검사 항목에 대한 양불 판정 ********************************************************************************
    for i in range(0, 16):
        JudgeResult_f1[i] = Result[0:(indexCount), i].mean()

    result_100mhz = find_judge(mode, 100, JudgeResult_f1, indexCount)  # 100 Mhz 검사항목을 모두 통과하면 PASS 아니면 FAIL

    # 20 MHz : 검사 항목에 대한 양불 판정 *********************************************************************************
    for i in range(0, 16):
        JudgeResult_f2[i] = Result[(indexCount): (indexCount + ((2 - 1) * indexCount)), i].mean()

    result_20mhz = find_judge(mode, 20, JudgeResult_f2, indexCount)  # 20 Mhz 검사항목을 모두 통과하면 PASS 아니면 FAIL

    # 100 / 20 MHz 의 Pass, Fail 을 각각 판단하고, 최종 양불을 판정한다 *****************************************************
    if result_100mhz == PASS and result_20mhz == PASS:
        JudgeResult_f1[16] = PASS
        JudgeResult_f2[16] = PASS
        JudgeResult = PASS
    else:
        JudgeResult_f1[16] = result_100mhz
        JudgeResult_f2[16] = result_20mhz
        JudgeResult = FAIL

    # report 엑셀 출력
    df1 = pd.DataFrame(
        [
            [JudgeResult_f1[16],
             JudgeResult_f1[0],
             JudgeResult_f1[1], JudgeResult_f1[2], JudgeResult_f1[3], JudgeResult_f1[4], JudgeResult_f1[5],
             JudgeResult_f1[6], JudgeResult_f1[7], JudgeResult_f1[8], JudgeResult_f1[9], JudgeResult_f1[10],
             JudgeResult_f1[11], JudgeResult_f1[12], JudgeResult_f1[13], JudgeResult_f1[14],
             JudgeResult_f1[15],
             JudgeResult_f1[17],  # gBoard_offset_f1 -> find offset( ) 에서 global offset 을 계산한다.
             JudgeResult_f1[18],
             JudgeResult_f1[19],
             ''],
            [JudgeResult_f2[16],
             JudgeResult_f2[0],
             JudgeResult_f2[1], JudgeResult_f2[2], JudgeResult_f2[3], JudgeResult_f2[4], JudgeResult_f2[5],
             JudgeResult_f2[6], JudgeResult_f2[7], JudgeResult_f2[8], JudgeResult_f2[9], JudgeResult_f2[10],
             JudgeResult_f2[11], JudgeResult_f2[12], JudgeResult_f2[13], JudgeResult_f2[14],
             JudgeResult_f2[15],
             JudgeResult_f2[17],  # gBoard_offset_f2 -> find offset( ) 에서 global offset 을 계산한다.
             JudgeResult_f2[18],
             JudgeResult_f2[19],
             ''],
            [JudgeResult,
             ''],
            [gSensor_id,
             gSensor_id_dec[0], gSensor_id_dec[1], gSensor_id_dec[2], gSensor_id_dec[3], gSensor_id_dec[4],
             gSensor_id_dec[5], gSensor_id_dec[6], gSensor_id_dec[7], gSensor_id_dec[8], gSensor_id_dec[9],
             gSensor_id_dec[10], gSensor_id_dec[11], gSensor_id_dec[12], gSensor_id_dec[13], gSensor_id_dec[14],
             gSensor_id_dec[15], '']
        ],
        index=['100', '20', 'Result', 'SensorID'],
        columns=['Judge',
                 'Error_CT_300',
                 'Error_CT_500', 'Error_LT_500', 'Error_RT_500', 'Error_RB_500', 'Error_LB_500',
                 'Noise_CT_500', 'Noise_LT_500', 'Noise_RT_500', 'Noise_RB_500', 'Noise_LB_500',
                 'Intensity_CT_500', 'Intensity_LT_500', 'Intensity_RT_500', 'Intensity_RB_500',
                 'Intensity_LB_500',
                 'board_offset f1/f2',
                 'APC Check 2700mA',
                 'APC Check 1500mA',
                 ''
                 ])


    file_path = r'{0}\{1}.csv'.format(Path, gSensor_id)  # file_path = r'{0}\{1}.csv'.format(Path, f'result')
    df1.to_csv(file_path, index=True, mode='w', header=True)
    # 하단코드는 처음이면 새로 생성 , 기존에 있으면 해당 파일에 누적해서 기록함
    # if not os.path.exists(file_path):
    #    df1.to_csv(file_path, index=True, mode='w', header=True)
    # else:
    #    df1.to_csv(file_path, index=True, mode='a', header=False)

    msg_print(df1)

    if not os.path.exists(file_path):
        msg_print(f'Failed, could not find report')

    return JudgeResult  # todo evalutaion judge -> result : 100/20 MHz PASS or FAIL

    # if os.path.isfile(file):
    #     print("Yes. it is a file")



def calc(data, mode):
    # 2023-02-16 ::: 실거리 평가 시, 뎁스영상 중심ROI에서 '0'을 제외하고 (평균)대표 값을 추출한다.

    CTValueRavel = np.ravel(data, order='C')
    remove_set = {0}
    CTValueSort = [i for i in CTValueRavel if i not in remove_set]

    if mode == f'mean':
        return np.mean(CTValueSort)
    elif mode == f'std':
        return np.std(CTValueSort)



def Convert_RawToCSV(filePath, folderPath, prefix, countIndex, frequency, cellLine, position):
    global mode_type
    try:
        #filePath RAW경로, path폴더경로, prefix파일이름, i파일이름순서, 측정위치
        global gResult, g100mhzDepthValue, g20mhzDepthValue

        path = folderPath
        depth_file = f'%s_%s%s' % (prefix, countIndex, f'_ALL0_f1_nshfl.raw')  # 심미안 뷰어에서 'Decode' - 'ToF' 가 선택이 되어야한다.
        intensity_file = f'%s_%s%s' % (prefix, countIndex, f'_ALL0_f1_nshfl_VC(2)_DT(Raw8).raw')
        width = 320
        height = 240

        if frequency == 100:
            max_distance = 1500  # 100M = 1500(mm)
        else:
            max_distance = 7500  # 20M = 7500(mm)


        if mode_type == 1:
            # mode1 변환 코드 : depth image *****************************************************************************
            fullpath = os.path.join(path, depth_file)
            dump = np.fromfile(fullpath, dtype='>B').reshape(height + 4, width * 2)  # '>' big endian, 'B' unsigned byte
            dump = dump[4:, :]  # remove embedded lines
            image = np.zeros((height, width), dtype=np.ushort)
            for h in range(0, height):
                for w in range(0, width):
                    image[h, w] = (dump[h, w * 2] << 8) + dump[h, w * 2 + 1]

            depth = np.bitwise_and(image, 0x1FFF).astype(np.float32) / 2 ** 13 * max_distance
        elif mode_type == 3:
            # mode3 변환 코드 : depth image *****************************************************************************
            fullpath = os.path.join(path, depth_file)
            dump = np.fromfile(fullpath, dtype='>H').reshape(height + 4, width * 3)  # '>' big endian, 'H' unsigned short
            dump = dump[4:, :]  # remove embedded lines
            Z = np.zeros((height, width), dtype=np.ushort)
            for h in range(0, height):
                for w in range(0, width):
                    Z[h, w] = dump[h, w * 3 + 2]

            depth = Z / (2 ** 16) * max_distance
        else:
            pass

        # mode1 변환 코드 : intensity image *********************************************************************************
        fullpath = os.path.join(path, intensity_file)
        dump = np.fromfile(fullpath, dtype='B').reshape(height + 0, width * 2)  # '>' big endian, 'H' unsigned short
        image = np.zeros((height, width), dtype=np.ushort)
        for h in range(0, height):
            for w in range(0, width):
                image[h, w] = (dump[h, w * 2] << 8) + dump[h, w * 2 + 1]

        intensity = image  # 2023-03-21, MX와 출력값 동기화 from 이정현 프로 # old code : intensity = image / 2 ** 4


        # CSV 파일로 저장 ***************************************************************************************************
        DepthCSV = f'%s%s.csv' % (f'depth', countIndex)
        np.savetxt(os.path.join(folderPath, DepthCSV), depth, delimiter=',')

        IntensityCSV = f'%s%s.csv' % (f'intensity', countIndex)
        np.savetxt(os.path.join(folderPath, IntensityCSV), intensity, delimiter=',')


        # 대표 값 계산 ******************************************************************************************************
        if position == 300:  # 측정 위치 300 mm
            # Depth Error
            gResult[(countIndex + ((cellLine - 1) * gCaptureCnt)), 0] = depth[114:124, 154:164].mean()  # CT
        else:  # 측정 위치 500 mm
            if frequency == 100:  # 2023-06-12, todo DV1-5에서 20MHz Wide모드는 TX화각이 70도로 줄어듬 -> ROI 별도 관리
                pass
                # Depth Error
                gResult[(countIndex + ((cellLine - 1) * gCaptureCnt)), 1] = depth[114:124, 154:164].mean()  # CT
                gResult[(countIndex + ((cellLine - 1) * gCaptureCnt)), 2] = depth[43:53, 59:69].mean()  # LT
                gResult[(countIndex + ((cellLine - 1) * gCaptureCnt)), 3] = depth[43:53, 250:260].mean()  # RT
                gResult[(countIndex + ((cellLine - 1) * gCaptureCnt)), 4] = depth[186:196, 250:260].mean()  # RB
                gResult[(countIndex + ((cellLine - 1) * gCaptureCnt)), 5] = depth[186:196, 59:69].mean()  # LB
                # Depth Noise
                gResult[(countIndex + ((cellLine - 1) * gCaptureCnt)), 6] = depth[114:124, 154:164].std()  # CT
                gResult[(countIndex + ((cellLine - 1) * gCaptureCnt)), 7] = depth[43:53, 59:69].std()  # LT
                gResult[(countIndex + ((cellLine - 1) * gCaptureCnt)), 8] = depth[43:53, 250:260].std()  # RT
                gResult[(countIndex + ((cellLine - 1) * gCaptureCnt)), 9] = depth[186:196, 250:260].std()  # RB
                gResult[(countIndex + ((cellLine - 1) * gCaptureCnt)), 10] = depth[186:196, 59:69].std()  # LB
                # Depth Intensity
                gResult[(countIndex + ((cellLine - 1) * gCaptureCnt)), 11] = intensity[114:124, 154:164].mean()  # CT
                gResult[(countIndex + ((cellLine - 1) * gCaptureCnt)), 12] = intensity[43:53, 59:69].mean()  # LT
                gResult[(countIndex + ((cellLine - 1) * gCaptureCnt)), 13] = intensity[43:53, 250:260].mean()  # RT
                gResult[(countIndex + ((cellLine - 1) * gCaptureCnt)), 14] = intensity[186:196, 250:260].mean()  # RB
                gResult[(countIndex + ((cellLine - 1) * gCaptureCnt)), 15] = intensity[186:196, 59:69].mean()  # LB

            else:  # 2023-06-12, todo DV1-5에서 20MHz Wide모드는 TX화각이 70도로 줄어듬 -> ROI 별도 관리
                pass
                # Depth Error
                gResult[(countIndex + ((cellLine - 1) * gCaptureCnt)), 1] = depth[114:124, 154:164].mean()  # CT
                gResult[(countIndex + ((cellLine - 1) * gCaptureCnt)), 2] = depth[66:76, 91:101].mean()  # LT
                gResult[(countIndex + ((cellLine - 1) * gCaptureCnt)), 3] = depth[66:76, 219:229].mean()  # RT
                gResult[(countIndex + ((cellLine - 1) * gCaptureCnt)), 4] = depth[163:173, 219:229].mean()  # RB
                gResult[(countIndex + ((cellLine - 1) * gCaptureCnt)), 5] = depth[163:173, 91:101].mean()  # LB
                # Depth Noise
                gResult[(countIndex + ((cellLine - 1) * gCaptureCnt)), 6] = depth[114:124, 154:164].std()  # CT
                gResult[(countIndex + ((cellLine - 1) * gCaptureCnt)), 7] = depth[66:76, 91:101].std()  # LT
                gResult[(countIndex + ((cellLine - 1) * gCaptureCnt)), 8] = depth[66:76, 219:229].std()  # RT
                gResult[(countIndex + ((cellLine - 1) * gCaptureCnt)), 9] = depth[163:173, 219:229].std()  # RB
                gResult[(countIndex + ((cellLine - 1) * gCaptureCnt)), 10] = depth[163:173, 91:101].std()  # LB
                # Depth Intensity
                gResult[(countIndex + ((cellLine - 1) * gCaptureCnt)), 11] = intensity[114:124, 154:164].mean()  # CT
                gResult[(countIndex + ((cellLine - 1) * gCaptureCnt)), 12] = intensity[66:76, 91:101].mean()  # LT
                gResult[(countIndex + ((cellLine - 1) * gCaptureCnt)), 13] = intensity[66:76, 219:229].mean()  # RT
                gResult[(countIndex + ((cellLine - 1) * gCaptureCnt)), 14] = intensity[163:173, 219:229].mean()  # RB
                gResult[(countIndex + ((cellLine - 1) * gCaptureCnt)), 15] = intensity[163:173, 91:101].mean()  # LB

        if position == 300:
            depth_data = 0
        else:
            depth_data = 1

        if frequency == 100:
            g100mhzDepthValue = gResult[(countIndex + ((cellLine - 1) * gCaptureCnt)), depth_data]
            log_message = f'100 MHz Center Measurement Depth mm -> {g100mhzDepthValue}'
            if g100mhzDepthValue == 0:
                log_message = f'100 MHz Center Measurement Depth Failed.'
                return FAIL_Z_ERROR
        else:
            g20mhzDepthValue = gResult[(countIndex + ((cellLine - 1) * gCaptureCnt)), depth_data]
            log_message = f'20 MHz Center Measurement Depth mm -> {g20mhzDepthValue}'
            if g20mhzDepthValue == 0:
                log_message = f'20 MHz Center Measurement Depth Failed.'
                return FAIL_Z_ERROR

        msg_print(log_message)

        return PASS

    except Exception as e:
        print(e)
        return FAIL_Z_ERROR


def validation(prefix, path, frequency, mode, count, pos):
    # prefix -> 100MHz이면 image100mhz , 20MHz이면 image20mhz
    # path -> 저장 경로
    # frequency -> 100 MHz 또는 20 MHz
    # mode -> 0 global offset 찾기 , 1 100mhz at 300 and 500 mm , 2 20mhz at 300 and 500 mm
    # count -> 저장 횟수
    global gResult, gBoard_offset_f1, gBoard_offset_f2, JudgeResult_f1, JudgeResult_f2, g_find_offset_cycle

    # 영상을 캡쳐하고, CSV로 변환하는 구문 *********************************************************************************
    for i in range(0, count):
        filePath = r'{0}\{1}_{2}.raw'.format(path, prefix, i)  # ++_ALL0_f1_nshfl_VC(2)_DT(Raw8).raw
        simmian.Capture(filePath, captureCount=1)

        delayMicroseconds(100000)  # 0.5초

        if frequency == 100:
            is_data = Convert_RawToCSV(filePath, path, prefix, i, frequency, 1, pos) # RAW경로, 폴더경로, 파일이름, 파일이름순서, 동작주파수, , 측정위치 순이다.
            if is_data == FAIL_Z_ERROR : # 뎁스 획득이 안되거나 '0' 이면 'NG'처리해야한다.
                return FAIL_Z_ERROR
        elif frequency == 20:
            is_data = Convert_RawToCSV(filePath, path, prefix, i, frequency, 2, pos) # RAW경로, 폴더경로, 파일이름, 파일이름순서, 동작주파수, , 측정위치 순이다.
            if is_data == FAIL_Z_ERROR:  # 뎁스 획득이 안되거나 '0' 이면 'NG'처리해야한다.
                return FAIL_Z_ERROR
        else:
            pass

    # global offset 을 구해야하는지 판단하는 구문 **************************************************************************
    if mode == GLOBAL_OFFSET:
        if g_find_offset_cycle == 4: #global offset 을 찾을려고 4번째 들어오면 'NG'로 처리한다
            return FAIL_Z_ERROR
        else:
            if frequency == 100 and pos == 500:
                #ctDepth100 = gResult[0:(count), 1].mean()  # 100MHz 500 CT Error
                CTValue = gResult[0:(count), 1]
                CTValueRavel = np.ravel(CTValue, order='C')
                remove_set = {0}
                CTValueSort = [i for i in CTValueRavel if i not in remove_set]
                ctDepth100 = np.mean(CTValueSort)
                msg_print(f'CT depth at 500 mm at 100 MHz is = {ctDepth100}')
                ProcFindGlobalOffset(frequency, ctDepth100, count)
            elif frequency == 20 and pos == 500:
                #ctDepth20 = gResult[(count): (count + ((2 - 1) * count)), 1].mean()
                CTValue = gResult[(count): (count + ((2 - 1) * count)), 1]
                CTValueRavel = np.ravel(CTValue, order='C')
                remove_set = {0}
                CTValueSort = [i for i in CTValueRavel if i not in remove_set]
                ctDepth20 = np.mean(CTValueSort)
                msg_print(f'CT depth at 500 mm at 20 MHz is = {ctDepth20}')
                ProcFindGlobalOffset(frequency, ctDepth20, count)
            else:
                msg_print(f'There is no need to calibrate the global-offset.')

    # e2p로부터 최종 적용한 global offset 값을 읽어오고, 리포트에 기록한다. ***************************************************
    if frequency == 100:
        oldOffsetDEC = simmian.ReadI2C(gDeviceID, gStartAddress_f1, 2)
        time.sleep(0.010)
        JudgeResult_f1[17] = HEXLittleEndian(oldOffsetDEC) #gBoard_offset_f1 = HEXLittleEndian(oldOffsetDEC)
    elif frequency == 20:
        oldOffsetDEC = simmian.ReadI2C(gDeviceID, gStartAddress_f2, 2)
        time.sleep(0.010)
        JudgeResult_f2[17] = HEXLittleEndian(oldOffsetDEC) #gBoard_offset_f2 = HEXLittleEndian(oldOffsetDEC)

    return PASS



def calc_offset(freq, oldOffsetDEC, MeasureDepthValue):  # (freq)(int)동작주파수, (oldOffsetDEC)(int)현재옵셋값,
    if freq == 100:
        DepthCTValue = MeasureDepthValue  # 500 mm 에서 뎁스 센터 초기치
        Modulation = 1500  # 100 MHz 동작에서 계산 가능한 최대 거리 mm
        if oldOffsetDEC == 32768:
            oldDepthOffset = 0
        else:
            oldDepthOffset = ((oldOffsetDEC - 32768) / 32768) * Modulation
        DepthOffset = oldDepthOffset + (500 - DepthCTValue)  # 기준거리(500) - 측정값
        calcDEC = int(((DepthOffset / Modulation) * 32768) + 32768)
    elif freq == 20:
        DepthCTValue = MeasureDepthValue  # 500 mm 에서 뎁스 센터 초기치
        Modulation = 7500  # 20 MHz 동작에서 계산 가능한 최대 거리 mm
        if oldOffsetDEC == 32768:
            oldDepthOffset = 0
        else:
            oldDepthOffset = ((oldOffsetDEC - 32768) / 32768) * Modulation
        DepthOffset = oldDepthOffset + (500 - DepthCTValue)  # 기준거리(500) - 측정값
        calcDEC = int(((DepthOffset / Modulation) * 32768) + 32768)
    else:
        msg_print(f'ERROR !!! -> calc_offset( ) ')
        calcDEC = 32768  # global offset 이 (HEX)8000 으로 들어간다.

    return calcDEC


def HEXLittleEndian(input):
    value = input  # input 은 DEC 타입이여야한다.

    # print(f'     * global offset 입력 값 -> ', value, hex(value))

    b_ = struct.pack('<i', value)[0]
    c1_ = format(b_, '02x')

    b_ = struct.pack('<i', value)[1]
    c2_ = format(b_, '02x')

    d = f'0x%s%s' % (c1_, c2_)

    return d  # HEX 로 리턴한다


def find_offset(freq, value, countIndex):  # (freq)(int)동작주파수 , (value)(float)측정값
    try :
        global gBoard_offset_f1, gBoard_offset_f2, JudgeResult_f1, JudgeResult_f2

        MeasureDepthValue = value

        if freq == 100:
            # 1 현재 보드 옵셋 값을 읽어한다. *********************************************************************************
            valueDEC = simmian.ReadI2C(0xA0, "0x0108", 2)
            time.sleep(0.010)  # 10ms
            ValueHEX = HEXLittleEndian(valueDEC)
            oldOffsetDEC = int(ValueHEX, 16)

            # 2 새로 적용해야하는 옵셋 값을 계산한다. **************************************************************************
            newOffsetDEC = calc_offset(freq, oldOffsetDEC, MeasureDepthValue)
            gBoard_offset_f1 = hex(newOffsetDEC)

            # 4 새로 적용해야하는 옵셋 값을 E2P에 쓰기 한다. *******************************************************************
            # 계산한 옵셋이 0x ab cd 이라면, WriteI2C 에 입력되는 값은 0x cd ab 로 넣어야한다.
            littleEndian_newOffsetHEX = HEXLittleEndian(newOffsetDEC)
            msg_print(f'offset : [old] {hex(oldOffsetDEC)} [new] {hex(newOffsetDEC)} [endian] {littleEndian_newOffsetHEX}')
            simmian.WriteI2C(0xA0, "0x0108", littleEndian_newOffsetHEX)
            time.sleep(0.010)  # 10ms

            # 6 현재 보드 옵셋 값을 읽어온다 **********************************************************************************
            read_board_offset_f1 = simmian.ReadI2C(0xA0, "0x0108", 2)
            time.sleep(0.010)  # 10ms
            msg_print(f'[endian] {littleEndian_newOffsetHEX} , [e2p] {hex(read_board_offset_f1)}')
        elif freq == 20:
            # 1 현재 보드 옵셋 값을 읽어한다. *********************************************************************************
            valueDEC = simmian.ReadI2C(0xA0, "0x010A", 2)
            time.sleep(0.010)  # 10ms
            ValueHEX = HEXLittleEndian(valueDEC)
            oldOffsetDEC = int(ValueHEX, 16)

            # 2 새로 적용해야하는 옵셋 값을 계산한다. ***************************************************************************
            newOffsetDEC = calc_offset(freq, oldOffsetDEC, MeasureDepthValue)
            gBoard_offset_f2 = hex(newOffsetDEC)

            # 4 새로 적용해야하는 옵셋 값을 E2P에 쓰기 한다. ********************************************************************
            # 계산한 옵셋이 0x ab cd 이라면, WriteI2C 에 입력되는 값은 0x cd ab 로 넣어야한다.
            littleEndian_newOffsetHEX = HEXLittleEndian(newOffsetDEC)
            msg_print(f'offset : [old] {hex(oldOffsetDEC)} [new] {hex(newOffsetDEC)} [endian] {littleEndian_newOffsetHEX}')
            simmian.WriteI2C(0xA0, "0x010A", littleEndian_newOffsetHEX)  # newOffsetHEX)
            time.sleep(0.010)  # 10ms

            # 6 현재 보드 옵셋 값을 읽어온다 **********************************************************************************
            read_board_offset_f2 = simmian.ReadI2C(0xA0, "0x010A", 2)
            time.sleep(0.010)  # 10ms
            msg_print(f'[endian] {littleEndian_newOffsetHEX} , [e2p] {hex(read_board_offset_f2)}')

    except Exception as e:
        print(e)
        return FAIL


def FindBoardoffset(freq, value, countIndex):  # (freq)(int)동작주파수 , (value)(float)측정값
    # 기준거리 500 mm 에서 옵셋을 어느범위안까지 조정을 할 것인가?
    lsl = gLSLGuardSpec  # at 500 mm
    usl = gUSLGuardSpec  # at 500 mm

    if value > lsl and value < usl: # Todo -> 옵셋을 찾았다
        msg_print(f'Measurement Depth mm -> {value}')
        return False
    else: # Todo -> 옵셋을 찾지 못했다
        msg_print(f'Measurement Depth mm -> {value}')
        return True



def motor_open(want_home_position_at_start):
    motor = python_ezimotor_api.EziMotor(motion.com_port)
    if motor.IsConnected() == False:
        sys.exit('Motor is not connected')
    motor.SetServoParam(motion.axis_no, motion.max_speed, motion.neg_limit, motion.pos_limit, motion.origin_type,
                        motion.speed_origin, motion.motor_type, motion.resolution)
    motor.SetMoveProfile(motion.axis_no, 200, motion.acceleration, motion.deceleration)

    # Alarm Reset
    if motor.IsAlarm(motion.axis_no) == True:
        motor.AlarmReset(motion.axis_no)
        time.sleep(0.5)

    # Servo On
    if motor.ServoOn(motion.axis_no, True) == False:
        sys.exit('Motor is not ServoOn. Please contact s/w engineer.')

    time.sleep(0.5)

    if motor.IsServoOn(motion.axis_no) == False:
        motor.ServoOn(motion.axis_no, True)
        time.sleep(0.5)

    return motor


def motor_close(motor):
    # Close motor
    ##motor.MoveAbsolute(motion.axis_no, 50)
    motor.ServoOn(motion.axis_no, False)
    motor.Close()


def is_motor_ready(motor, axis_no):
    if motor.IsMotionDone(axis_no) == False:
        return True
    return False


def _init_motor():
    if not winsys.is_admin():
        msg_print('[ERROR] You should run this program with administrator')
        sys.exit(-1)

    # motor create
    want_home_position_at_start = True
    motion_obj = motion.Motion()
    gMotor = motor_open(want_home_position_at_start)


def msg_print(msg):
    try:
        now = datetime.datetime.now()
        str_now = now.strftime('%H:%M:%S')
        str = f'  [%s] %s' % (str_now, msg)
        print(str)  # 현재 시간 출력
        logging.info(str)


    except Exception as e:
        print(e)


def ProcSimmianPlay():
    if init_() != PASS:
        return FAIL_SIMMIAN_INIT #sys.exit("It can not connect with simmian")

    return PASS


def ProcSimmianReset():
    re = ResetSimmian()

    return re


def ProcSimmianStop():
    simmian.Stop()
    time.sleep(0.010)
    simmian.Disconnect()


def check_sensor_id():
    global gSensor_id_dec

    sensor_id = get_sensor_id()

    if gSensor_id_dec[12] != 96 or gSensor_id_dec[13] != 61:    # 0x60 -> (int)96 , 0x3D -> (int)61
        return FAIL_SENSOR_ID
    else:
        return PASS


# 2023-02-17 ::: 배중호, 심미안툴에서 센서ID읽기
def get_sensor_id():
    global gSensor_id_dec

    list = [0 for i in range(16)]

    gSensor_id_dec[0] = simmian.ReadI2C(0xA0, "0x00B8", 1)
    list[0] = format(gSensor_id_dec[0], '02X')

    gSensor_id_dec[1] = simmian.ReadI2C(0xA0, "0x00B9", 1)
    list[1] = format(gSensor_id_dec[1], '02X')
    # print(f'simmian readI2C 0x00B9 1 Byte  -> {temp} , hex -> {list[0]}')

    gSensor_id_dec[2] = simmian.ReadI2C(0xA0, "0x00BA", 1)
    list[2] = format(gSensor_id_dec[2], '02X')
    # print(f'simmian readI2C 0x00BA 1 Byte  -> {temp} , hex -> {list[1]}')

    gSensor_id_dec[3] = simmian.ReadI2C(0xA0, "0x00BB", 1)
    list[3] = format(gSensor_id_dec[3], '02X')
    # print(f'simmian readI2C 0x00BB 1 Byte  -> {temp} , hex -> {list[2]}')

    gSensor_id_dec[4] = simmian.ReadI2C(0xA0, "0x00BC", 1)
    list[4] = format(gSensor_id_dec[4], '02X')
    # print(f'simmian readI2C 0x00BC 1 Byte  -> {temp} , hex -> {list[3]}')

    gSensor_id_dec[5] = simmian.ReadI2C(0xA0, "0x00BD", 1)
    list[5] = format(gSensor_id_dec[5], '02X')
    # print(f'simmian readI2C 0x00BD 1 Byte  -> {temp} , hex -> {list[4]}')

    gSensor_id_dec[6] = simmian.ReadI2C(0xA0, "0x00BE", 1)
    list[6] = format(gSensor_id_dec[6], '02X')
    # print(f'simmian readI2C 0x00BE 1 Byte  -> {temp} , hex -> {list[5]}')

    gSensor_id_dec[7] = simmian.ReadI2C(0xA0, "0x00BF", 1)
    list[7] = format(gSensor_id_dec[7], '02X')
    # print(f'simmian readI2C 0x00BF 1 Byte  -> {temp} , hex -> {list[6]}')

    gSensor_id_dec[8] = simmian.ReadI2C(0xA0, "0x00C0", 1)
    list[8] = format(gSensor_id_dec[8], '02X')
    # print(f'simmian readI2C 0x00C0 1 Byte  -> {temp} , hex -> {list[7]}')

    gSensor_id_dec[9] = simmian.ReadI2C(0xA0, "0x00C1", 1)
    list[9] = format(gSensor_id_dec[9], '02X')
    # print(f'simmian readI2C 0x00C1 1 Byte  -> {temp} , hex -> {list[8]}')

    gSensor_id_dec[10] = simmian.ReadI2C(0xA0, "0x00C2", 1)
    list[10] = format(gSensor_id_dec[10], '02X')
    # print(f'simmian readI2C 0x00C2 1 Byte  -> {temp} , hex -> {list[9]}')

    gSensor_id_dec[11] = simmian.ReadI2C(0xA0, "0x00C3", 1)
    list[11] = format(gSensor_id_dec[11], '02X')
    # print(f'simmian readI2C 0x00C3 1 Byte  -> {temp} , hex -> {list[10]}')

    gSensor_id_dec[12] = simmian.ReadI2C(0xA0, "0x00C4", 1)
    list[12] = format(gSensor_id_dec[12], '02X')
    # print(f'simmian readI2C 0x00C4 1 Byte  -> {temp} , hex -> {list[11]}')

    gSensor_id_dec[13] = simmian.ReadI2C(0xA0, "0x00C5", 1)
    list[13] = format(gSensor_id_dec[13], '02X')
    # print(f'simmian readI2C 0x00C5 1 Byte  -> {temp} , hex -> {list[12]}')

    gSensor_id_dec[14] = simmian.ReadI2C(0xA0, "0x00C6", 1)
    list[14] = format(gSensor_id_dec[14], '02X')

    gSensor_id_dec[15] = simmian.ReadI2C(0xA0, "0x00C7", 1)
    list[15] = format(gSensor_id_dec[15], '02X')

    str_sensorid = "".join(list)

    return str_sensorid


def ProcCreateModuleFolder():
    try:
        global gSaveModulePath, g20mhz30cm, g20mhz50cm, g100mhz30cm, g100mhz50cm, gSensor_id

        # 2023-02-17 ::: 배중호, 심미안툴에서 센서ID 읽어오기
        gSensor_id = get_sensor_id()
        get_module_number = gSensor_id

        if get_module_number == f'00000000000000000000000000' and f'':
            msg_print(f'Module Number : {get_module_number}')
            return FAIL_SENSOR_ID

        # if get_module_number == f'FFFFFFFFFFFFFFFFFFFFFFFFFF':
        #     f= open(gRootSavePath+"\\name.txt",'r')
        #     lines= f.reandlines()
        #     get_module_number=lines[0]
        #     int(f)


        msg_print(f'Module Number : {get_module_number}')

        # 폴더 생성
        gSaveModulePath = f'%s\%s' % (gRootSavePath, get_module_number)  # 모듈의 저장 경로
        create_folder(gSaveModulePath)

        g20mhz30cm = f'%s\%s\%s' % (gRootSavePath, get_module_number, f'20M_30cm')  # 저장 경로 -> 20 MHz로 300 mm
        create_folder(g20mhz30cm)

        g20mhz50cm = f'%s\%s\%s' % (gRootSavePath, get_module_number, f'20M_50cm')  # 저장 경로 -> 20 MHz로 500 mm
        create_folder(g20mhz50cm)

        g100mhz30cm = f'%s\%s\%s' % (gRootSavePath, get_module_number, f'100M_30cm')  # 저장 경로 -> 100 MHz로 300 mm
        create_folder(g100mhz30cm)

        g100mhz50cm = f'%s\%s\%s' % (gRootSavePath, get_module_number, f'100M_50cm')  # 저장 경로 -> 100 MHz로 500 mm
        create_folder(g100mhz50cm)

        return PASS


    except Exception as e:
        print(e)
        return FAIL_SENSOR_ID


def ProcMoveTo500():
    msg_print(f'모터 제어 : 위치 이동 (500 mm) ************************************************************************')
    msg_print("Move to Loading Pos : 500 mm")
    msg_print("Move to loading position completed")

    # move_to_pos(500)

    msg_print(f' ')


def ProcMoveto300():
    msg_print(f'모터 제어 : 위치 이동 300 mm **************************************************************************')

    # move_to_pos(300)

    msg_print("Move to Loading Pos : ", 300)
    msg_print("Move to 300 mm position completed")
    msg_print(f' ')


def ProcMotorClose():
    msg_print("Close motor communication")
    motor_close(gMotor)
    msg_print(f' ')


def ProcCreateSetFile100():
    global g100MHzSetFilePath

    msg_print(f'Create a 100MHz set-file for Validation ')

    # 100 MHz 만들기 단계
    cmd = [gBatchPath100MHz]  # CMD는 반드시 관리자 권한을 실행해야한다. cd /d d:\LSI_VST63D\4_Validation\create_setfile

    re = subprocess.call(cmd, shell=True)
    if re == PASS:  # subprocess.call = '0' -> 정상 종료
        msg_print(f'')
    else:
        msg_print(f'  : Fail')
        for proc in psutil.process_iter():
            if proc.name() == "update_cal_data_to_setfile.exe":
                proc.kill()
        msg_print(f'  FAIL, could not create set file !!!')
        return FAIL_MAKE_SETFILE

    src = f'%s\%s' % (gRootPath, g100MHzSetFileName)
    dst = f'%s\%s' % (gSaveModulePath, g100MHzSetFileName)
    shutil.move(src, dst)  # 전체경로 주소로 해줘야 이미 존재하는 파일명이면 덮어쓰기 한다
    g100MHzSetFilePath = dst

    # 검증 -> 셋파일 생성 유무
    bfile = os.path.isfile(g100MHzSetFilePath)
    if bfile == True:
        msg_print(f'  : Success')
        time.sleep(0.010)
        return PASS
    else:
        msg_print(f'  FAIL, could not create set file !!!')
        return FAIL_MAKE_SETFILE



def ProcCreateSetFile20():
    msg_print(f'Create a 20MHz set-file for Validation ')
    global g20MHzSetFilePath

    # 20 MHz 만들기 단계
    cmd = [gBatchPath20MHz]  # CMD는 반드시 관리자 권한을 실행해야한다. cd /d d:\LSI_VST63D\4_Validation\create_setfile

    re = subprocess.call(cmd, shell=True) # re = subprocess.run(cmd, shell=True)
    if re == PASS:  # subprocess.call = '0' ->정상 종료
        msg_print(f'')
    else:
        msg_print(f'  : Fail')
        for proc in psutil.process_iter():
            if proc.name() == "update_cal_data_to_setfile.exe":
                proc.kill()

        msg_print(f'  FAIL, could not create set file !!!')
        return FAIL_MAKE_SETFILE

    src = f'%s\%s' % (gRootPath, g20MHzSetFileName)
    dst = f'%s\%s' % (gSaveModulePath, g20MHzSetFileName)
    shutil.move(src, dst)  # 전체경로 주소로 해줘야 이미 존재하는 파일명이면 덮어쓰기 한다
    g20MHzSetFilePath = dst

    # 검증 -> 셋파일 생성 유무
    bfile = os.path.isfile(g20MHzSetFilePath)
    if bfile == True:
        msg_print(f'  : Success')
        time.sleep(0.010)
        return PASS
    else:
        msg_print(f'  FAIL, could not create set file !!!')
        return FAIL_MAKE_SETFILE



def ProcLoadSetFile100mhz():
    global g100MHzSetFilePath

    if os.path.isfile(g100MHzSetFilePath):
        if simmian.LoadSetfile(g100MHzSetFilePath):
            time.sleep(0.1)
            msg_print(f'Success , it can load the setfile')
            return PASS
        else:
            msg_print(f'Failure. it can not load the setfile')
            return FAIL_LOAD_SETFILE  # sys.exit('Error!!!!')


def ProcLoadSetFile20mhz():
    global g20MHzSetFilePath

    if os.path.isfile(g20MHzSetFilePath):
        if simmian.LoadSetfile(g20MHzSetFilePath):
            time.sleep(0.1)
            msg_print(f'Success , it can load the setfile')
            return PASS
        else:
            msg_print(f'Failure , it can not load the setfile')
            return FAIL_LOAD_SETFILE
        return FAIL_LOAD_SETFILE #sys.exit('Error!!!!')


def ProcFindGlobalOffset(freq, depthCTValue, countIndex):
    global g_find_offset_cycle

    g_find_offset_cycle += 1 # Todo 옵셋 찾는 횟수를 모니터링 한다

    # depthCTValue 가 LSL-USL을 만족하는지 FindBoardoffset( ) 에서 검사한다.
    is_find_offset = FindBoardoffset(freq, depthCTValue, countIndex)  # (freq)(int)주파수, (depthCTValue)(float)측정값

    if is_find_offset == True: #-> 옵셋을 찾아야한다. , PASSFalse -> 옵셋을 찾지 않아도 된다.
        msg_print("It need to find global offsets.")
        # Todo 옵셋을 찾는다.
        find_offset(freq, depthCTValue, countIndex)  # (freq)(int)동작주파수 , (value)(float)측정값
        # Todo 재 검사
        if freq == 100:
            ResetSimmian()                          # 심미안 초기화
            ProcCreateSetFile100()                  # 셋파일 생성
            ResetSimmian()                          # 심미안 초기화
            ProcLoadSetFile100mhz()                 # 100 MHz 셋파일 로딩
            ProcSaveRaw100mhz50cm(GLOBAL_OFFSET)    # 뎁스 측정
        elif freq == 20:
            ResetSimmian()                          # 심미안 초기화
            ProcCreateSetFile20()                   # 셋파일 생성
            ResetSimmian()                          # 심미안 초기화
            ProcLoadSetFile20mhz()                  # 100 MHz 셋파일 로딩
            ProcSaveRaw20mhz50cm(GLOBAL_OFFSET)     # 뎁스 측정
        else:
            msg_print(f'ERROR!!! -> ProcFindGlobalOffset( )')
            return FAIL
    else:
        msg_print("No need to find global offsets.")
        return PASS     # True


def ProcSaveRaw100mhz50cm(mode): # Todo Single Frequency 100 MHz at 500 mm
    time.sleep(1)

    is_validation = validation(f'image100mhz', g100mhz50cm, 100, mode, gCaptureCnt, 500)
    if is_validation != PASS:
        return FAIL_Z_ERROR

    msg_print("Capture Done : 100 MHz at 500 mm")
    return PASS


def ProcSaveRaw100mhz30cm(mode): # Todo Single Frequency 100 MHz at 300 mm
    time.sleep(1)

    is_validation = validation(f'image100mhz', g100mhz30cm, 100, mode, gCaptureCnt, 300)
    if is_validation != PASS:
        return FAIL_Z_ERROR

    msg_print("Capture Done : 100 MHz at 300 mm")
    return PASS

def ProcSaveRaw20mhz50cm(mode): # Todo Single Frequency 20 MHz at 500 mm
    time.sleep(1)

    is_validation = validation(f'image20mhz', g20mhz50cm, 20, mode, gCaptureCnt, 500)
    if is_validation != PASS:
        return FAIL_Z_ERROR

    msg_print("Capture Done : 20 MHz at 500 mm")
    return PASS


def ProcSaveRaw20mhz30cm(mode): # Todo Single Frequency 20 MHz at 300 mm
    time.sleep(1)

    is_validation = validation(f'image20mhz', g20mhz30cm, 20, mode, gCaptureCnt, 300)
    if is_validation != PASS:
        return FAIL_Z_ERROR

    msg_print("Capture Done : 20 MHz at 300 mm")
    return PASS


def ProcCreateReport(mode, errorcode):
    global gSensor_id, gSaveModulePath

    is_create_report = FAIL

    if errorcode == PASS:   # todo '평가'가 '정상'으로 진행되었음.
        is_create_report = create_report(mode, gSaveModulePath, gResult, gCaptureCnt)
        # if is_create_report != PASS:
        #     print(f'Failed, could not create report !!!')
        #     return FAIL
        return is_create_report     # todo create_report -> judge result : 100/20 Mhz

    # todo '평가'가 '정상'으로 진행되지않았거나, 리포트를 '정상'으로 생성 못했으면,
    if errorcode != PASS:
        gSaveModulePath = f'%s\%s' % (gRootSavePath, gSensor_id)  # 모듈의 저장 경로
        create_folder(gSaveModulePath)
        df1 = pd.DataFrame([
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ''],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ''],
            [errorcode, ''],
            [gSensor_id,
             gSensor_id_dec[0], gSensor_id_dec[1], gSensor_id_dec[2], gSensor_id_dec[3], gSensor_id_dec[4],
             gSensor_id_dec[5], gSensor_id_dec[6], gSensor_id_dec[7], gSensor_id_dec[8], gSensor_id_dec[9],
             gSensor_id_dec[10], gSensor_id_dec[11], gSensor_id_dec[12], gSensor_id_dec[13], gSensor_id_dec[14],
             gSensor_id_dec[15],'']],
            index=['100', '20', 'Result', 'SensorID'],
            columns=['Judge', 'Error_CT_300',
                     'Error_CT_500', 'Error_LT_500', 'Error_RT_500', 'Error_RB_500', 'Error_LB_500',
                     'Noise_CT_500', 'Noise_LT_500', 'Noise_RT_500', 'Noise_RB_500', 'Noise_LB_500',
                     'Intensity_CT_500', 'Intensity_LT_500', 'Intensity_RT_500', 'Intensity_RB_500',
                     'Intensity_LB_500', 'board_offset f1/f2', 'APC Check 2700mA', 'APC Check 1500mA', ''])

        file_path = f'%s\%s\%s.csv' % (gRootSavePath, gSensor_id, gSensor_id)
        df1.to_csv(file_path, index=True, mode='w', header=True)

        if not os.path.exists(file_path):
            msg_print(f'Failed, could not create report !!!')
            return FAIL
        else:
            msg_print(f'Succeed, create report')
            return FAIL_Z_ERROR


def TestReversed(input):
    value = input

    # print(f'입력값 -> ', value, hex(value))

    # b_ = struct.pack('<L', value)
    # print(f'리틀엔디안 변환 -> ', b_)

    b_ = struct.pack('<i', value)[0]
    # print(f'리틀엔디안 변환 -> ', hex(b_))
    c1 = '%x' % b_
    if c1 == '0':
        c1 = '00'
    # print(f'리틀엔디안 변환 0x 제거 -> ', c1)

    b_ = struct.pack('<i', value)[1]
    # print(f'리틀엔디안 변환 -> ', hex(b_))
    c2 = '%x' % b_
    if c2 == '0':
        c2 = '00'
    # print(f'리틀엔디안 변환 0x 제거 -> ', c2)

    d = f'0x%s%s' % (c1, c2)
    # print(f'입력값 리틀엔디안 변환 : ', d)

    return d


def TestWriteI2C():
    set_board_offset_f1 = 32768  # 계산한 옵셋이 0xabcd 이라면, WriteI2C 에 입력되는 값은 0xcdab 로 넣어야한다.
    msg_print(f'입력 값 -> ', set_board_offset_f1, hex(set_board_offset_f1))

    set_board_offset_f1_ = TestReversed(set_board_offset_f1)
    msg_print(f'리틀엔디안 ->', set_board_offset_f1_)

    simmian.WriteI2C(0xA0, "0x0108", set_board_offset_f1_)
    time.sleep(1)

    ResetSimmian()
    re_read_board_offset_f1 = simmian.ReadI2C(gDeviceID, gStartAddress_f1, 2)
    msg_print(f'리틀엔디안 , E2P 값 : ', set_board_offset_f1_, hex(re_read_board_offset_f1))

    msg_print(f'################################################################################')

    set_board_offset_f2 = 32768  # 계산한 옵셋이 0xabcd 이라면, WriteI2C 에 입력되는 값은 0xcdab 로 넣어야한다.
    msg_print(f'입력 값 -> ', set_board_offset_f2, hex(set_board_offset_f2))

    set_board_offset_f2_ = TestReversed(set_board_offset_f2)
    msg_print(f'리틀엔디안 ->', set_board_offset_f2_)

    simmian.WriteI2C(0xA0, "0x0108", set_board_offset_f2_)
    time.sleep(1)

    ResetSimmian()
    re_read_board_offset_f2 = simmian.ReadI2C(gDeviceID, gStartAddress_f1, 2)
    msg_print(f'리틀엔디안 , E2P 값 : ', set_board_offset_f2_, hex(re_read_board_offset_f2))

    sys.exit()


def motor_clear():
    global gMotor
    gMotor.ServoOn(motion.axis_no, False)
    gMotor.Close()
    want_home_position_at_start = True
    gMotor = motor_open(want_home_position_at_start)


def motor_move(distance, motion_abs):
    if gMotor == -1:
        raise SystemError

    msg_print(f'Motor move {distance}mm')
    if gMotor.ABSMove_Chk(motion.axis_no, motion_abs) == False:
        msg_print(f' => Oops: Motor could not move {distance}')
        motor_clear()

    gMotor.MoveAbsolute(motion.axis_no, motion_abs)
    wait(lambda: is_motor_ready(gMotor, motion.axis_no), timeout_seconds=120, waiting_for="Motor move to be ready")
    time.sleep(1)
    # input("Press Enter to continue...")


def InitGlobalOffsetWriteI2C():
    try:
        msg_print(f'Write -> board offset f1(100 MHz), address : 0x0108 ')
        set_board_offset_f1 = 17000  # 계산한 옵셋이 0xabcd 이라면, WriteI2C 에 입력되는 값은 0xcdab 로 넣어야한다.
        set_board_offset_f1_ = HEXLittleEndian(set_board_offset_f1)
        simmian.WriteI2C(0xA0, "0x0108", set_board_offset_f1_)  # board offset f1 100MHz 0x0108 주소
        time.sleep(0.100)

        is_simmian = ResetSimmian()
        if is_simmian == FAIL_SIMMIAN_INIT:
            return FAIL_SIMMIAN_INIT

        re_read_board_offset_f1 = simmian.ReadI2C(0xA0, "0x0108", 2)

        msg_print(f'Write -> board offset f2(020 MHz), address : 0x010A ')
        set_board_offset_f2 = 16600  # 계산한 옵셋이 0xabcd 이라면, WriteI2C 에 입력되는 값은 0xcdab 로 넣어야한다.
        set_board_offset_f2_ = HEXLittleEndian(set_board_offset_f2)
        simmian.WriteI2C(0xA0, "0x010A", set_board_offset_f2_)  # board offset f2 20MHz 0x010A 주소
        time.sleep(0.100)

        is_simmian = ResetSimmian()
        if is_simmian == FAIL_SIMMIAN_INIT:
            return FAIL_SIMMIAN_INIT

        re_read_board_offset_f2 = simmian.ReadI2C(0xA0, "0x010A", 2)

        return PASS

    except Exception as e:
        print(e)
        return FAIL_OTP_WRITE


def check_dbuploader(msg):
    str_msg = ''.join(str(s) for s in msg)
    str_done = 'done'

    if str_done in str_msg:
        return PASS
    else:
        return FAIL


def database_uploader(path, result):
    # todo 밸리데이션 SW의 데이터베이스 코드이다.

    global gRootSavePath, gSensor_id_dec

    simmian = python_simmian_api.Simmian()

    # 심미안 플레이 ****************************************************************************************************
    re = simmian.GetBoardCount()
    if re == 0:
        msg_print(f'Failure, it can not find Simmian.')
        return FAIL_SIMMIAN_INIT

    is_simmian = ProcSimmianPlay()
    if is_simmian == FAIL_SIMMIAN_INIT:
        msg_print(f'Failure, it can not turn on Simmian.')
        return FAIL_SIMMIAN_INIT

    sensor_id = get_sensor_id()
    gSaveModulePath = f'%s\%s' % (gRootSavePath, sensor_id)  # 모듈의 저장 경로 C:\LSI_VST63D\save\sensor_id
    file_path = r'{0}\{1}.csv'.format(gSaveModulePath, sensor_id) #{C:\LSI_VST63D\save\sensor_id}\{sensor_id.csv}

    if not os.path.exists(file_path): # todo DB에 올릴 리포트를 찾지 못했다면, '비정상'으로 끝났으니까 'FAIL'리포트 생성
        msg_print(f'Failed, could not find report')
        create_folder(gSaveModulePath)
        df1 = pd.DataFrame( [
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ''],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ''],
                [result, ''],
                [sensor_id,
                 gSensor_id_dec[0], gSensor_id_dec[1], gSensor_id_dec[2], gSensor_id_dec[3], gSensor_id_dec[4],
                 gSensor_id_dec[5], gSensor_id_dec[6], gSensor_id_dec[7], gSensor_id_dec[8], gSensor_id_dec[9],
                 gSensor_id_dec[10], gSensor_id_dec[11], gSensor_id_dec[12], gSensor_id_dec[13], gSensor_id_dec[14],
                 gSensor_id_dec[15], ''] ],
            index=['100', '20', 'Result', 'SensorID'],
            columns=['Judge', 'Error_CT_300',
                     'Error_CT_500', 'Error_LT_500', 'Error_RT_500', 'Error_RB_500', 'Error_LB_500',
                     'Noise_CT_500', 'Noise_LT_500', 'Noise_RT_500', 'Noise_RB_500', 'Noise_LB_500',
                     'Intensity_CT_500', 'Intensity_LT_500', 'Intensity_RT_500', 'Intensity_RB_500',
                     'Intensity_LB_500', 'board_offset f1/f2', 'APC Check 2700mA', 'APC Check 1500mA', '' ])

        # file_path = f'%s\%s\%s.csv' % (gRootSavePath, Sensor_id, Sensor_id)
        df1.to_csv(file_path, index=True, mode='w', header=True)
        if not os.path.exists(file_path):
            msg_print(f'Failed, could not find report')
            return FAIL

    cmd = f'%s -%s\%s\%s.csv' % (path, gRootSavePath, sensor_id, sensor_id)
    # {C:\\lsi\\NMG_DBUpload_Demo\\Release\\dbUploader.exe} -{C:\LSI_VST63D\save}\{sensor_id}\{sensor_id.csv}

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    msg = f''
    is_status = FAIL

    with process.stdout:
        for line in iter(process.stdout.readline, b''):
            msg = line.decode("utf-8").strip()
            is_status = check_dbuploader(msg)

    simmian.Stop()
    simmian.Disconnect()

    return is_status


def main_val(mode):
    global gMotor, glogpath, JudgeResult_f1, JudgeResult_f2, gSaveModulePath, g_find_offset_cycle

    # Todo 심미안 라이브러리 초기화
    simmian = python_simmian_api.Simmian()

    # Todo 관리자 권한으로 실행했는지 확인함
    if not winsys.is_admin():
        msg_print(f'You should run this program with administrator.')
        return FAIL_IS_ADMIN #sys.exit(-1)

    # Todo 모터 초기화
    is_status = False
    if is_status is True:
        msg_print(f'Start motor initialization.')
        want_home_position_at_start = True
        motion_obj = motion.Motion()
        gMotor = motor_open(want_home_position_at_start)
        if (want_home_position_at_start):
            motor_move(distance=500, motion_abs=motion_dist500)
            time.sleep(0.5)

    # Todo 심미안 장치 찾기 및 플레이
    #msg_print(f'심미안 뷰어의 재생을 시작합니다.')
    re = simmian.GetBoardCount()
    if re == 0:     # 인식된 보드가 없을 때 '0' 으로 리턴된다.
        msg_print(f'Failure, it can not find Simmian.')
        ProcCreateReport(ERROR, FAIL_SIMMIAN_INIT)
        return FAIL_SIMMIAN_INIT

    is_simmian = ProcSimmianPlay()
    if is_simmian != PASS:
        msg_print(f'Failure, it can not turn on Simmian.')
        ProcCreateReport(ERROR, FAIL_SIMMIAN_INIT)
        return FAIL_SIMMIAN_INIT

    # Todo 모듈 번호 입력
    is_create_folder = ProcCreateModuleFolder()
    if is_create_folder != PASS:
        ProcCreateReport(ERROR, is_create_folder)
        return FAIL_SENSOR_ID # 센서ID 읽기 실패 또는 폴더를 생성 실패이다.

    # Todo 디폴트 global-offset 넣기 -> (0)VALIDATION 에서만 '디폴트 옵셋'을 넣어준다.
    if mode == VALIDATION:  # todo mode -> (0)VALIDATION, (1)OQC, (2)DAILY_CHECK, (3)VALIDATION_SIMPLE
        is_default_offset = InitGlobalOffsetWriteI2C()  # # write f1 0x7446 f2 0x7d40 비교
        if is_default_offset != PASS:
            ProcCreateReport(ERROR, is_default_offset)
            return is_default_offset

    ## Todo 셋파일 100 MHz 만들기
    is_status = True
    if is_status:
       is_create_setfile = ProcCreateSetFile100()
       if is_create_setfile != PASS:
           ProcCreateReport(ERROR, FAIL_MAKE_SETFILE)
           return FAIL_MAKE_SETFILE

    # Todo 셋파일 20 MHz 만들기
    is_status = True
    if is_status:
        is_create_setfile = ProcCreateSetFile20()
        if is_create_setfile != PASS:
            ProcCreateReport(ERROR, FAIL_MAKE_SETFILE)
            return FAIL_MAKE_SETFILE


    # Todo 심미안 리셋
    is_simmian = ProcSimmianReset()
    if is_simmian != PASS:
        ProcCreateReport(ERROR, FAIL_SIMMIAN_INIT)
        return FAIL_SIMMIAN_INIT

    ## Todo 100 MHz 셋파일 로딩
    is_status = True
    if is_status:
       is_load_setfile = ProcLoadSetFile100mhz()
       if is_load_setfile != PASS:
           ProcCreateReport(ERROR, FAIL_LOAD_SETFILE)
           return FAIL_LOAD_SETFILE

    # Todo 100MHz 평가 (위치 : 500 mm )
    time.sleep(1)  # 성능평가를 위한 뎁스 영상 취득 전에 워밍업 3초

    # todo 100MHz at 500mm 뎁스 global-offset 찾기 -> (0)VALIDATION 에서만 한다.
    is_status = True
    if is_status:
        if mode == VALIDATION:  # todo (0)VALIDATION, (1)OQC, (2)DAILY_CHECK, (3)VALIDATION_SIMPLE
            g_find_offset_cycle = 0
            is_measure = ProcSaveRaw100mhz50cm(GLOBAL_OFFSET)  # todo (0)GLOBAL_OFFSET , (1)EVALUATION
            if is_measure != PASS:
                return FAIL_Z_ERROR
        else:
            msg_print(f'Find to global offset for 100 MHz : skip !!! ')


    # todo 100MHz at 500mm 뎁스 측정
    is_status = True
    if is_status:
        is_measure = ProcSaveRaw100mhz50cm(EVALUATION)  # todo (0)GLOBAL_OFFSET , (1)EVALUATION
        if is_measure != PASS:
            return FAIL_Z_ERROR

    # Todo 심미안 리셋
    is_simmian = ProcSimmianReset()
    if is_simmian != PASS:
        ProcCreateReport(ERROR, FAIL_SIMMIAN_INIT)
        return FAIL_SIMMIAN_INIT

    # # Todo 모터 제어 : 위치 이동 300 mm
    is_status = False
    if is_status:
        motor_move(distance=300, motion_abs=motion_dist300)
        time.sleep(1)
    #
    # # Todo 100 MHz 셋파일 로딩
    is_status = False
    if is_status:
        is_load_setfile = ProcLoadSetFile100mhz()
        if is_load_setfile != PASS:
            ProcCreateReport(ERROR, FAIL_LOAD_SETFILE)
            return FAIL_LOAD_SETFILE
    #
    # # todo 100MHz at 300mm 뎁스 측정
    is_status = False
    if is_status:
        time.sleep(1)  # 성능평가를 위한 뎁스 영상 취득 전에 워밍업 3초
        is_measure = ProcSaveRaw100mhz30cm(EVALUATION)          # todo (0)GLOBAL_OFFSET , (1)EVALUATION
        if is_measure != PASS:
            return FAIL_Z_ERROR

    # Todo 심미안 리셋
    is_simmian = ProcSimmianReset()
    if is_simmian != PASS:
        ProcCreateReport(ERROR, FAIL_SIMMIAN_INIT)
        return FAIL_SIMMIAN_INIT

    # Todo 모터 제어 : 위치 이동 500 mm
    is_status = False
    if is_status:
        motor_move(distance=500, motion_abs=motion_dist500)
        time.sleep(1)

    # Todo 20 MHz 셋파일 로딩
    is_status = True
    if is_status:
        is_load_setfile = ProcLoadSetFile20mhz()
        if is_load_setfile != PASS:
            ProcCreateReport(ERROR, FAIL_LOAD_SETFILE)
            return FAIL_LOAD_SETFILE

    # Todo 20MHz 평가 (위치 : 500 mm )
    time.sleep(1)  # 성능평가를 위한 뎁스 영상 취득 전에 워밍업 3초

    # todo 20MHz at 500mm 뎁스 global-offset 찾기 -> (0)VALIDATION 에서만 수행한다.
    is_status = True
    if is_status:
        if mode == VALIDATION:  # todo (0)VALIDATION, (1)OQC, (2)DAILY_CHECK, (3)VALIDATION_SIMPLE
            g_find_offset_cycle = 0
            is_measure = ProcSaveRaw20mhz50cm(GLOBAL_OFFSET)  # todo (0)GLOBAL_OFFSET , (1)EVALUATION
            if is_measure != PASS:
                return FAIL_Z_ERROR
        else:
            msg_print(f'Find to global offset for 20 MHz : skip !!! ')

    # todo 20MHz at 500mm 뎁스 측정
    is_status = True
    if is_status:
        is_measure = ProcSaveRaw20mhz50cm(EVALUATION)  # todo (0)GLOBAL_OFFSET , (1)EVALUATION
        if is_measure != PASS:
            return FAIL_Z_ERROR

    # Todo 심미안 리셋
    is_simmian = ProcSimmianReset()
    if is_simmian != PASS:
        ProcCreateReport(ERROR, FAIL_SIMMIAN_INIT)
        return FAIL_SIMMIAN_INIT

    # # Todo 모터 제어 : 위치 이동 300 mm
    is_status = False
    if is_status:
        motor_move(distance=300, motion_abs=motion_dist300)
        time.sleep(1)

    # # Todo 20 MHz 셋파일 로딩
    is_status = False
    if is_status:
        is_load_setfile = ProcLoadSetFile20mhz()
        if is_load_setfile != PASS:
            ProcCreateReport(ERROR, FAIL_LOAD_SETFILE)
            return FAIL_LOAD_SETFILE

    # # todo 20MHz at 300mm 뎁스 측정
    is_status = False
    if is_status:
        time.sleep(1)  # 성능평가를 위한 뎁스 영상 취득 전에 워밍업 3초
        is_measure = ProcSaveRaw20mhz30cm(EVALUATION)           # todo (0)GLOBAL_OFFSET , (1)EVALUATION
        if is_measure != PASS:
            return FAIL_Z_ERROR

    # Todo 모터 닫기
    is_status = False
    if is_status:
        motor_move(distance=500, motion_abs=motion_dist500)
        ProcMotorClose()

    # 2023-01-27 Todo APC Check 투식스 레이저 DV1-5 'T1-> T2' , DV2 'T2-> T3'
    is_status = False
    if is_status:
        APCCheck(100)
        APCCheck(20)

    # Todo 심미안 종료
    ProcSimmianStop()

    # Todo 결과 출력
    msg_print(f'Create a report of evaluation.')
    is_create_report = ProcCreateReport(EVALUATION, PASS)   # todo (0)GLOBAL_OFFSET , (1)EVALUATION
    # is_create_report -> PASS or FAIL

    is_status = False
    if not is_status:
        simmian.Stop()
        simmian.Disconnect()
        msg_print(f'please replace with next module')
        return PASS
    else:
        # Todo 'VALIDATION' 일 경우, E2P Factory 영역 쓰기
        if mode == VALIDATION:  # todo (0)VALIDATION, (1)OQC, (2)DAILY_CHECK
            msg_print(f'The checksum of the header area is recalculated... ')
            is_header_checksum = writeToeeprom.header_checksum()
            if is_header_checksum != PASS:
                msg_print(f'failed write to Header area checksum !!! ')
                return FAIL_OTP_WRITE

            is_tof_data_common_checksum = writeToeeprom.tofcal_common_checksum()  # todo ToF DATA 의 Common의 체크썸
            if is_tof_data_common_checksum != PASS:
                msg_print(f'failed write to ToF Data(-> Common) area checksum !!! ')
                return FAIL_OTP_WRITE

            is_tof_data_checksum = writeToeeprom.tofcal_checksum()  # todo 체크썸 계산이 올바르지 않음.
            if is_tof_data_checksum != PASS:
                msg_print(f'failed write to ToF Data area checksum !!! ')
                return FAIL_OTP_WRITE

            is_factory_checksum = writeToeeprom.factory_checksum(JudgeResult_f1, JudgeResult_f2, gSaveModulePath)
            if is_factory_checksum != PASS:
                msg_print(f'failed write to Factory area checksum !!! ')
                return FAIL_OTP_WRITE
        else:
            msg_print(f'Write to eeprom of factory and calculate checksum. -> skip !!!')
            pass

        simmian.Stop()
        simmian.Disconnect()
        msg_print(f'done. -> {gSaveModulePath}')
        msg_print(f'please replace with next module')
        return is_create_report  # todo 'is_create_report' -> 100/20 MHz PASS or FAIL


if __name__ == "__main__":

    main_val(0)     # todo (0)VALIDATION, (1)OQC, (2)DAILY_CHECK

    sys.exit(-1)
