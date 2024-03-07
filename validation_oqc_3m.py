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
# import python_vst_eepromparser_api 2023-04-13 기능 구현 필요함



# 심미안 ===============================================
SimmianLauncher = f'C:\\Program Files\\NxSimmian\\NxSimmian v1.3.7.0\\SimmianLauncher.exe'
# =====================================================


# motor ===============================================
gMotor = -1
motion_dist500 = 93
# 3m 실거리 -> 2023_03_15, DV1차 모듈바닥에서 차트까지 간격은 521.6mm 로 세팅 : 모터값 433
# isMedia -> 2023_04_19, DV1차 모듈바닥에서 차트까지 간격은 521.6mm 로 세팅 : 모터값 93

motion_dist300 = 308
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
gRootPath = f'%s\%s' % (f'C:\LSI_VST63D', f'4_Validation')
gOutputFilePrefix = f'Image'
gRootSavePath = f'%s\%s' % (f'C:\LSI_VST63D', f'4_Validation\save')
gOutputDirPrefix = f'image'
gCaptureCnt = 3
gMotorSettleTimeSec = 3
gWarmup = 3
#####################################################

# log
#####################################################
glogpath = f'%s\%s' % (gRootSavePath, f'validation.log')
#####################################################


# Configuration about Set File for Validation
#####################################################
gRootSetFilePath = f'%s\%s' % (f'C:\LSI_VST63D', f'4_Validation\save')
gSaveModulePath = f' '
g100MHzSetFileName = f'[val]63D_EVT0p1_QVGA_A_C02_M1_R300_D60_SINGLE_100M_FLOOD_DPHY960_AE_MIPI960_cal_maskoff_CalOff_3J.set'   # BtoC -> f'100M_1109.set'
g20MHzSetFileName = f'[val]63D_EVT0p1_QVGA_A_C02_M1_R300_D60_SINGLE_20M_FLOOD_DPHY960_AE_MIPI960_cal_maskoff_CalOff_3J.set'     # BtoC -> f'20M_1109.set'
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
gLSLGuardSpec = 495
gUSLGuardSpec = 505

JudgeResult_f1 = [0 for i in range(21)]
JudgeResult_f2 = [0 for i in range(21)]
JudgeResult = [0 for i in range(21)]
#####################################################


# Configuration about Create Set File
#####################################################
gRootPathOriginalSetFile = f'%s\%s' % (f'C:\LSI_VST63D', f'4_Validation\create_setfile')
gBatchPath100MHz = f'%s\%s' % (gRootPathOriginalSetFile, f'1.bat')
gBatchPath20MHz = f'%s\%s' % (gRootPathOriginalSetFile, f'2.bat')

#####################################################


# APC Check
#####################################################
setregvalue = 0 # 사전bring-up 투식스 '0' , 검증3차 루멘터 '4'
gApc_check_at_lsw_fix1_f1 = 0
gApc_check_at_lsw_fix2_f1 = 0
gApc_check_at_lsw_fix1_f2 = 0
gApc_check_at_lsw_fix2_f2 = 0
#####################################################


# Sensor ID
#####################################################
gSensor_id = f''
#####################################################


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
        return True
    else:
        msg_print(f'Failure, it can not turn on.')
        return False




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
        re = simmian.Reset()
        re = simmian.Play()

        if re == False:
            return 100

    except Exception as e:
        print(e)
        return 100


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
    msg_print('  save path : ', filePath)
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
    global gApc_check_at_lsw_fix1_f1, gApc_check_at_lsw_fix2_f1, gApc_check_at_lsw_fix1_f2, gApc_check_at_lsw_fix2_f2

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
    else:
        msg_print("Error!!! -> APC Check")

    SetRegisterPD(setregvalue)  # R_PD = 0b100:3.0kOhm

def judge_error_code(data):
    msg_print(f'')
    # 108 Z축 잡음 불량
    # 109 Z축 오차 불량
    # 110 픽셀 밝기 레벨 불량
    # 111 APC 체크 불량

    #data[0]            # Z축 오차 - 중심 - 300mm
    #data[1] ~ [5]      # Z축 오차 - 중심/주변 - 500mm
    if (data[0] and data[1] and data[2] and data[3] and data[4] and data[5] == True):
        msg_print(f'')
    else:
        return 109

    #data[6] ~ [10]     # Z축 잡음 - 중심/주변 - 500mm
    if (data[6] and data[7] and data[8] and data[9] and data[10] == True):
        msg_print(f'')
    else:
        return 108

    #data[11] ~ [15]    # 빅셀 광량 레벨 - 중심/주변 - 500mm
    if (data[11] and data[12] and data[13] and data[14] and data[15] == True):
        msg_print(f'')
    else:
        return 110

    #data[16] ~ [17]    # APC 체크 2700mA , 1500mA
    if (data[16] and data[17] == True):
        msg_print(f'')
    else:
        return 111



def find_judge(mode, freq, data, indexCount):
    # 2. 결과에 대한 양불 판정을 시작한다.
    # 2023-01-28 : B to B Validation(Depth 성능측정) ********************************************************************
    # Z축 잡음(Noise),    중심 QVGA,    촬영거리 500mm, 5.0 mm
    DepthNoiseAVG500_Spec_Center = 100#5.0

    # Z축 잡음(Noise),    주변 QVGA,    촬영거리 500mm, 5.0 mm
    DepthNoiseAVG500_Spec_06Field = 100#5.0

    # Z축 오차(Error),    중심 QVGA,    촬영거리 300mm, ± 24 mm
    DepthErrorAVG300_Spec_Center = 100#24.0

    # Z축 오차(Error),    중심 QVGA,    촬영거리 500mm, ± 15 mm
    DepthErrorAVG500_Spec_Center = 100#15.0

    # Z축 오차(Error),    주변 QVGA,    촬영거리 500mm, ± 40 mm
    DepthErrorAVG500_Spec_06Field = 100#40.0

    if freq == 100:
    # 픽셀 밝기 레벨 100MHz, 중심,       촬영거리 500mm, 938 ~ 1875
        ConfidenceAVG_Spec_CenterLower = 10#938
        ConfidenceAVG_Spec_CenterUpper = 90000#1875
    # 픽셀 밝기 레벨 100MHz, 주변,       촬영거리 500mm, 813 ~ 1625
        ConfidenceAVG_Spec_06FieldLower = 10#813
        ConfidenceAVG_Spec_06FieldUpper = 90000#1625
    else:
    # 픽셀 밝기 레벨 20MHz,  중심,       촬영거리 500mm, 1000 ~ 2000
        ConfidenceAVG_Spec_CenterLower = 10#1000
        ConfidenceAVG_Spec_CenterUpper = 90000#2000
    # 픽셀 밝기 레벨 20MHz,  주변,       촬영거리 500mm, 875 ~ 1750
        ConfidenceAVG_Spec_06FieldLower = 10#875
        ConfidenceAVG_Spec_06FieldUpper = 90000#1750

    # APC_CHECK 100MHz   2700mA,      촬영거리 500mm, 335 ~ 735
    lsl_lsw_fix1_f1 = 10#335
    usl_lsw_fix1_f1 = 1023#735

    # APC_CHECK 100MHz   1500mA,      촬영거리 500mm, 200 ~ 470
    lsl_lsw_fix2_f1 = 10#200
    usl_lsw_fix2_f1 = 1023#470

    # APC_CHECK 20MHz    2700mA,      촬영거리 500mm, 400 ~ 750
    lsl_lsw_fix1_f2 = 10#400
    usl_lsw_fix1_f2 = 1023#750

    # APC_CHECK 20MHz    1500mA,      촬영거리 500mm, 220 ~ 470
    lsl_lsw_fix2_f2 = 10#220
    usl_lsw_fix2_f2 = 1023#470

    # 2023-01-28 : B to B Validation(Depth 성능측정) ********************************************************************


    # // 2-3. 300mm Depth Validation Data_f1 ***************************************************************************
    # // 검사 사양 : 300mm Depth Validation Data_f1

    # // 판정 플래그 : 300mm Depth Validation Data_f1
    _b300mm_Depth_Validation_Data_f1_01F_CT_ROI = False

    # // 판정 비교
    f1_1 = data[0]  # 300 CT Error
    if (300 - DepthErrorAVG300_Spec_Center) <= f1_1 and (300 + DepthErrorAVG300_Spec_Center) >= f1_1:
        _b300mm_Depth_Validation_Data_f1_01F_CT_ROI = True
    else:
        _b300mm_Depth_Validation_Data_f1_01F_CT_ROI = False

    JudgeResult[0] = _b300mm_Depth_Validation_Data_f1_01F_CT_ROI
    str = f'{_b300mm_Depth_Validation_Data_f1_01F_CT_ROI} 300 CT Error '
    msg_print(str)

    # 2-1. 500mm Depth Validation Data_f1 (QVGA) ***********************************************************************
    # 2-1-1. Depth mean ************************************************************************************************

    # 검사 플래그 : 500mm Depth Validation Data_f1 (QVGA) -> Depth mean of ...
    _b500mm_Depth_Validation_Data_f1_Depth_mean_of_01F_CT_ROI = False
    _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_LT_ROI = False
    _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_RT_ROI = False
    _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_RB_ROI = False
    _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_LB_ROI = False

    # // 판정 비교 : 500mm Depth Validation Data_f1 (QVGA) -> Depth mean of center ROI
    f1_2 = data[1]
    if (500 - DepthErrorAVG500_Spec_Center) <= f1_2 and (500 + DepthErrorAVG500_Spec_Center) >= f1_2:
        _b500mm_Depth_Validation_Data_f1_Depth_mean_of_01F_CT_ROI = True
    else:
        _b500mm_Depth_Validation_Data_f1_Depth_mean_of_01F_CT_ROI = False

    JudgeResult[1] = _b500mm_Depth_Validation_Data_f1_Depth_mean_of_01F_CT_ROI
    str = f'{_b500mm_Depth_Validation_Data_f1_Depth_mean_of_01F_CT_ROI} 500 mm, Depth mean of center ROI '
    msg_print(str)

    # // 판정 비교 : 500mm Depth Validation Data_f1 (QVGA) -> Depth mean of 0.6F LT ROI
    f1_3 = data[2]
    if (500 - DepthErrorAVG500_Spec_06Field) <= f1_3 and (500 + DepthErrorAVG500_Spec_06Field) >= f1_3:
        _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_LT_ROI = True
    else:
        _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_LT_ROI = False

    JudgeResult[2] = _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_LT_ROI
    str = f'{_b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_LT_ROI} 500 mm, Depth mean of 0.6F LT ROI '
    msg_print(str)

    # // 판정 비교 : 500mm Depth Validation Data_f1 (QVGA) -> Depth mean of 0.6F RT ROI
    f1_4 = data[3]
    if (500 - DepthErrorAVG500_Spec_06Field) <= f1_4 and (500 + DepthErrorAVG500_Spec_06Field) >= f1_4:
        _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_RT_ROI = True
    else:
        _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_RT_ROI = False

    JudgeResult[3] = _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_RT_ROI
    str = f'{_b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_RT_ROI} 500 mm, Depth mean of 0.6F RT ROI '
    msg_print(str)

    # // 판정 비교 : 500mm Depth Validation Data_f1 (QVGA) -> Depth mean of 0.6F RB ROI
    f1_5 = data[4]
    if (500 - DepthErrorAVG500_Spec_06Field) <= f1_5 and (500 + DepthErrorAVG500_Spec_06Field) >= f1_5:
        _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_RB_ROI = True
    else:
        _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_RB_ROI = False

    JudgeResult[4] = _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_RB_ROI
    str = f'{_b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_RB_ROI} 500 mm, Depth mean of 0.6F RB ROI '
    msg_print(str)

    # // 판정 비교 : 500mm Depth Validation Data_f1 (QVGA) -> Depth mean of 0.6F LB ROI
    f1_6 = data[5]
    if (500 - DepthErrorAVG500_Spec_06Field) <= f1_6 and (500 + DepthErrorAVG500_Spec_06Field) >= f1_6:
        _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_LB_ROI = True
    else:
        _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_LB_ROI = False

    JudgeResult[5] = _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_LB_ROI
    str = f'{_b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_LB_ROI} 500 mm, Depth mean of 0.6F LB ROI '
    msg_print(str)

    # // ***************************************************************************************************************
    # // 2-1-2. Validation Noise ***************************************************************************************

    # // 검사 플래그 : 500mm Depth Validation Data_f1 (QVGA) - Validation Noise
    _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_01F_CT_ROI = False
    _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_LT_ROI = False
    _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_RT_ROI = False
    _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_RB_ROI = False
    _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_LB_ROI = False

    # // 판정 비교 : Validation Noise of center ROI
    f1_7 = data[6]
    if DepthNoiseAVG500_Spec_Center >= f1_7:
        _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_01F_CT_ROI = True
    else:
        _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_01F_CT_ROI = False

    JudgeResult[6] = _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_01F_CT_ROI
    str = f'{_b500mm_Depth_Validation_Data_f1_Validation_Noise_of_01F_CT_ROI} 500 mm, Validation Noise of center ROI '
    msg_print(str)

    # // 판정 비교 : Validation Noise of 0.6F ROI -> LT
    f1_8 = data[7]
    if DepthNoiseAVG500_Spec_06Field >= f1_8:
        _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_LT_ROI = True
    else:
        _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_LT_ROI = False

    JudgeResult[7] = _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_LT_ROI
    str = f'{_b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_LT_ROI} 500 mm, Validation Noise of 0.6F ROI -> LT '
    msg_print(str)

    # // 판정 비교 : Validation Noise of 0.6F ROI -> RT
    f1_9 = data[8]
    if DepthNoiseAVG500_Spec_06Field >= f1_9:
        _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_RT_ROI = True
    else:
        _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_RT_ROI = False

    JudgeResult[8] = _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_RT_ROI
    str = f'{_b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_RT_ROI} 500 mm, Validation Noise of 0.6F ROI -> RT '
    msg_print(str)

    # // 판정 비교 : Validation Noise of 0.6F ROI -> RB
    f1_10 = data[9]
    if DepthNoiseAVG500_Spec_06Field >= f1_10:
        _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_RB_ROI = True
    else:
        _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_RB_ROI = False

    JudgeResult[9] = _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_RB_ROI
    str = f'{_b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_RB_ROI} 500 mm, Validation Noise of 0.6F ROI -> RB '
    msg_print(str)

    # // 판정 비교 : Validation Noise of 0.6F ROI -> LB
    f1_11 = data[10]
    if DepthNoiseAVG500_Spec_06Field >= f1_11:
        _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_LB_ROI = True
    else:
        _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_LB_ROI = False

    JudgeResult[10] = _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_LB_ROI
    str = f'{_b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_LB_ROI} 500 mm, Validation Noise of 0.6F ROI -> LB '
    msg_print(str)

    # // ***************************************************************************************************************
    # // 2-2. 500mm VCSEL Optical Power Data_f1 (광량검사 데이터) *********************************************************
    # // 시작 ***********************************************************************************************************


    # // 검사 플래그 : 100MHz, 500mm VCSEL Optical Power Data (광량false이터)
    _b500mm_VCSEL_Optical_Power_Data_01F_CT_ROI = False
    _b500mm_VCSEL_Optical_Power_Data_06F_LT_ROI = False
    _b500mm_VCSEL_Optical_Power_Data_06F_RT_ROI = False
    _b500mm_VCSEL_Optical_Power_Data_06F_RB_ROI = False
    _b500mm_VCSEL_Optical_Power_Data_06F_LB_ROI = False

    # // 판정 비교
    f1_12 = data[11]
    if ConfidenceAVG_Spec_CenterLower <= f1_12 and ConfidenceAVG_Spec_CenterUpper >= f1_12:
        _b500mm_VCSEL_Optical_Power_Data_01F_CT_ROI = True
    else:
        _b500mm_VCSEL_Optical_Power_Data_01F_CT_ROI = False

    JudgeResult[11] = _b500mm_VCSEL_Optical_Power_Data_01F_CT_ROI
    str = f'{_b500mm_VCSEL_Optical_Power_Data_01F_CT_ROI} Optical Power Data CT '
    msg_print(str)

    f1_13 = data[12]
    if ConfidenceAVG_Spec_06FieldLower <= f1_13 and ConfidenceAVG_Spec_06FieldUpper >= f1_13:
        _b500mm_VCSEL_Optical_Power_Data_06F_LT_ROI = True
    else:
        _b500mm_VCSEL_Optical_Power_Data_06F_LT_ROI = False

    JudgeResult[12] = _b500mm_VCSEL_Optical_Power_Data_06F_LT_ROI
    str = f'{_b500mm_VCSEL_Optical_Power_Data_06F_LT_ROI} Optical Power Data LT '
    msg_print(str)

    f1_14 = data[13]
    if ConfidenceAVG_Spec_06FieldLower <= f1_14 and ConfidenceAVG_Spec_06FieldUpper >= f1_14:
        _b500mm_VCSEL_Optical_Power_Data_06F_RT_ROI = True
    else:
        _b500mm_VCSEL_Optical_Power_Data_06F_RT_ROI = False

    JudgeResult[13] = _b500mm_VCSEL_Optical_Power_Data_06F_RT_ROI
    str = f'{_b500mm_VCSEL_Optical_Power_Data_06F_RT_ROI} Optical Power Data RT '
    msg_print(str)

    f1_15 = data[14]
    if ConfidenceAVG_Spec_06FieldLower <= f1_15 and ConfidenceAVG_Spec_06FieldUpper >= f1_15:
        _b500mm_VCSEL_Optical_Power_Data_06F_RB_ROI = True
    else:
        _b500mm_VCSEL_Optical_Power_Data_06F_RB_ROI = False

    JudgeResult[14] = _b500mm_VCSEL_Optical_Power_Data_06F_RB_ROI
    str = f'{_b500mm_VCSEL_Optical_Power_Data_06F_RB_ROI} Optical Power Data RB '
    msg_print(str)

    f1_16 = data[15]
    if ConfidenceAVG_Spec_06FieldLower <= f1_16 and ConfidenceAVG_Spec_06FieldUpper >= f1_16:
        _b500mm_VCSEL_Optical_Power_Data_06F_LB_ROI = True
    else:
        _b500mm_VCSEL_Optical_Power_Data_06F_LB_ROI = False

    JudgeResult[15] = _b500mm_VCSEL_Optical_Power_Data_06F_LB_ROI
    str = f'{_b500mm_VCSEL_Optical_Power_Data_06F_LB_ROI} Optical Power Data LB '
    msg_print(str)

    # // ***************************************************************************************************************
    # // 2-4. 500mm APC PD VALUE 검사 ***********************************************************************************
    # // 시작 ***********************************************************************************************************

    b100mhz_apc_lsw_fix1_f1 = False
    b100mhz_apc_lsw_fix2_f1 = False
    b20mhz_apc_lsw_fix1_f2 = False
    b20mhz_apc_lsw_fix2_f2 = False
    apc_lsw_fix1 = False
    apc_lsw_fix2 = False


    if freq == 100:
        if gApc_check_at_lsw_fix1_f1 >= lsl_lsw_fix1_f1 and gApc_check_at_lsw_fix1_f1 <= usl_lsw_fix1_f1:
            apc_lsw_fix1 = True
        else:
            apc_lsw_fix1 = False

        JudgeResult[16] = apc_lsw_fix1 # 2700mA 의 결과
        str = f'{apc_lsw_fix1} 100 MHz, apc_lsw_fix1_f1'
        msg_print(str)

        if gApc_check_at_lsw_fix2_f1 >= lsl_lsw_fix2_f1 and gApc_check_at_lsw_fix2_f1 <= usl_lsw_fix2_f1:
            apc_lsw_fix2 = True
        else:
            apc_lsw_fix2 = False

        JudgeResult[17] = apc_lsw_fix2 # 1500mA 의 결과
        str = f'{apc_lsw_fix2} 100 MHz, apc_lsw_fix2_f1'
        msg_print(str)

    else:
        if gApc_check_at_lsw_fix1_f2 >= lsl_lsw_fix1_f2 and gApc_check_at_lsw_fix1_f2 <= usl_lsw_fix1_f2:
            apc_lsw_fix1 = True
        else:
            apc_lsw_fix1 = False

        JudgeResult[16] = apc_lsw_fix1 # 2700mA 의 결과
        str = f'{apc_lsw_fix1} 20 MHz, apc_lsw_fix1_f2'
        msg_print(str)

        if gApc_check_at_lsw_fix2_f2 >= lsl_lsw_fix2_f2 and gApc_check_at_lsw_fix2_f2 <= usl_lsw_fix2_f2:
            apc_lsw_fix2 = True
        else:
            apc_lsw_fix2 = False

        JudgeResult[17] = apc_lsw_fix2 # 1500mA 의 결과
        str = f'{apc_lsw_fix2} 20 MHz, apc_lsw_fix2_f2'
        msg_print(str)

    if mode == 0: # global_offset 검사 결과
        if (_b500mm_Depth_Validation_Data_f1_Depth_mean_of_01F_CT_ROI == True):
            if freq == 100:
                msg_print(f'global offset 100 Mhz Result -> PASS ')
            elif freq == 20:
                msg_print(f'global offset 20 Mhz Result -> PASS ')
            else:
                msg_print('ERROR -> find_judge()')
            return 'PASS'
        else:
            if freq == 100:
                msg_print(f'global offset 100 Mhz Result -> FAIL ')
            elif freq == 20:
                msg_print(f'global offset 20 Mhz Result -> FAIL ')
            else:
                msg_print('ERROR -> find_judge()')
            return 'FAIL'
    else:
        if (_b500mm_Depth_Validation_Data_f1_Depth_mean_of_01F_CT_ROI
                and _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_LT_ROI
                and _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_RT_ROI
                and _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_RB_ROI
                and _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_LB_ROI
                and _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_01F_CT_ROI
                and _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_LT_ROI
                and _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_RT_ROI
                and _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_RB_ROI
                and _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_LB_ROI
                and _b500mm_VCSEL_Optical_Power_Data_01F_CT_ROI
                and _b500mm_VCSEL_Optical_Power_Data_06F_LT_ROI
                and _b500mm_VCSEL_Optical_Power_Data_06F_RT_ROI
                and _b500mm_VCSEL_Optical_Power_Data_06F_RB_ROI
                and _b500mm_VCSEL_Optical_Power_Data_06F_LB_ROI
                and _b300mm_Depth_Validation_Data_f1_01F_CT_ROI
                and apc_lsw_fix1
                and apc_lsw_fix2 == True):
            if freq == 100:
                #print('              ' + '\033[42m' + 'PASS' + '\033[0m' + ' -> 100MHz 평가 결과')
                msg_print('PASS -> 100MHz Result')
            elif freq == 20:
                #print('              ' + '\033[42m' + 'PASS' + '\033[0m' + ' ->  20MHz 평가 결과')
                msg_print('PASS -> 20MHz Result')
            else:
                msg_print('ERROR -> find_judge()')
            return 0
        else:
            if freq == 100:
                #print('              ' + '\033[41m' + 'FAIL' + '\033[0m' + ' -> 100MHz 평가 결과')
                msg_print('FAIL -> 100MHz Result')
            elif freq == 20:
                #print('              ' + '\033[41m' + 'FAIL' + '\033[0m' + ' ->  20MHz 평가 결과')
                msg_print('FAIL -> 20MHz Result')
            else:
                msg_print('ERROR -> find_judge()')

            re = judge_error_code(JudgeResult)

            return re


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

    # 100 MHz
    for i in range(0, 16):
        JudgeResult_f1[i] = Result[0:(indexCount), i].mean()

    result_100mhz = find_judge(mode, 100, JudgeResult_f1, indexCount)  # 100 Mhz 검사항목을 모두 통과하면 PASS 아니면 FAIL
    if result_100mhz == 0:
        f1_0 = 'PASS'
    else:
        f1_0 = 'FAIL'

    # 20 MHz
    for i in range(0, 16):
        JudgeResult_f2[i] = Result[(indexCount): (indexCount + ((2 - 1) * indexCount)), i].mean()
        # print(JudgeResult_f2[i])

    result_20mhz = find_judge(mode, 20, JudgeResult_f2, indexCount)  # 20 Mhz 검사항목을 모두 통과하면 PASS 아니면 FAIL
    if result_20mhz == 0:
        f2_0 = 'PASS'
    else:
        f2_0 = 'FAIL'

    # report 엑셀 출력
    df1 = pd.DataFrame(
        [
            [f1_0,
             JudgeResult_f1[0],
             JudgeResult_f1[1], JudgeResult_f1[2], JudgeResult_f1[3], JudgeResult_f1[4], JudgeResult_f1[5],
             JudgeResult_f1[6], JudgeResult_f1[7], JudgeResult_f1[8], JudgeResult_f1[9], JudgeResult_f1[10],
             JudgeResult_f1[11], JudgeResult_f1[12], JudgeResult_f1[13], JudgeResult_f1[14],
             JudgeResult_f1[15],
             gBoard_offset_f1,  # gBoard_offset_f1 -> find offset( ) 에서 global offset 을 계산한다.
             gApc_check_at_lsw_fix1_f1,
             gApc_check_at_lsw_fix2_f1],
            [f2_0,
             JudgeResult_f2[0],
             JudgeResult_f2[1], JudgeResult_f2[2], JudgeResult_f2[3], JudgeResult_f2[4], JudgeResult_f2[5],
             JudgeResult_f2[6], JudgeResult_f2[7], JudgeResult_f2[8], JudgeResult_f2[9], JudgeResult_f2[10],
             JudgeResult_f2[11], JudgeResult_f2[12], JudgeResult_f2[13], JudgeResult_f2[14],
             JudgeResult_f2[15],
             gBoard_offset_f2,  # gBoard_offset_f2 -> find offset( ) 에서 global offset 을 계산한다.
             gApc_check_at_lsw_fix1_f2,
             gApc_check_at_lsw_fix2_f2]
        ],
        index=['100 MHz', '20 MHz'],
        columns=['Judge',
                 'Error_CT_300',
                 'Error_CT_500', 'Error_LT_500', 'Error_RT_500', 'Error_RB_500', 'Error_LB_500',
                 'Noise_CT_500', 'Noise_LT_500', 'Noise_RT_500', 'Noise_RB_500', 'Noise_LB_500',
                 'Intensity_CT_500', 'Intensity_LT_500', 'Intensity_RT_500', 'Intensity_RB_500',
                 'Intensity_LB_500',
                 'board_offset f1/f2',
                 'APC Check 2700mA',
                 'APC Check 1500mA'
                 ])

    file_path = r'{0}\{1}.csv'.format(Path, gSensor_id)  # file_path = r'{0}\{1}.csv'.format(Path, f'result')
    df1.to_csv(file_path, index=True, mode='w', header=True)
    # 하단코드는 처음이면 새로 생성 , 기존에 있으면 해당 파일에 누적해서 기록함
    # if not os.path.exists(file_path):
    #    df1.to_csv(file_path, index=True, mode='w', header=True)
    # else:
    #    df1.to_csv(file_path, index=True, mode='a', header=False)

    msg_print(df1)

    # 2023-02-22, 배중호 DB 쌓기
    create_DB(gSensor_id, f1_0, f2_0)

    if result_100mhz == 0 and result_20mhz == 0:
        return 0
    elif result_100mhz == 0 and result_20mhz != 0:
        return result_20mhz
    elif result_100mhz != 0 and result_20mhz == 0:
        return result_100mhz
    else:
        return 109



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


    # mode1 변환 코드 : depth image *************************************************************************************
    fullpath = os.path.join(path, depth_file)
    dump = np.fromfile(fullpath, dtype='>B').reshape(height + 4, width * 2)  # '>' big endian, 'B' unsigned byte
    dump = dump[4:, :]  # remove embedded lines
    image = np.zeros((height, width), dtype=np.ushort)
    for h in range(0, height):
        for w in range(0, width):
            image[h, w] = (dump[h, w * 2] << 8) + dump[h, w * 2 + 1]

    depth = np.bitwise_and(image, 0x1FFF).astype(np.float32) / 2 ** 13 * max_distance


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

    if position == 300:
        depth_data = 0
    else:
        depth_data = 1

    if frequency == 100:
        g100mhzDepthValue = gResult[(countIndex + ((cellLine - 1) * gCaptureCnt)), depth_data]
        log_message = f'100 MHz Center Measurement Depth mm -> {g100mhzDepthValue}'
    else:
        g20mhzDepthValue = gResult[(countIndex + ((cellLine - 1) * gCaptureCnt)), depth_data]
        log_message = f'20 MHz Center Measurement Depth mm -> {g20mhzDepthValue}'

    msg_print(log_message)

    return gResult


def validation(prefix, path, frequency, mode, count, pos):
    # prefix -> 100MHz이면 image100mhz , 20MHz이면 image20mhz
    # path -> 저장 경로
    # frequency -> 100 MHz 또는 20 MHz
    # mode -> 0 global offset 찾기 , 1 100mhz at 300 and 500 mm , 2 20mhz at 300 and 500 mm
    # count -> 저장 횟수
    global gResult, gBoard_offset_f1, gBoard_offset_f2

    # 영상을 캡쳐하고, CSV로 변환하는 구문 *********************************************************************************
    for i in range(0, count):
        filePath = r'{0}\{1}_{2}.raw'.format(path, prefix, i)  # ++_ALL0_f1_nshfl_VC(2)_DT(Raw8).raw
        simmian.Capture(filePath, captureCount=1)

        delayMicroseconds(100000)  # 0.5초

        if frequency == 100:
            Convert_RawToCSV(filePath, path, prefix, i, frequency, 1, pos) # RAW경로, 폴더경로, 파일이름, 파일이름순서, 동작주파수, , 측정위치 순이다.
        elif frequency == 20:
            Convert_RawToCSV(filePath, path, prefix, i, frequency, 2, pos) # RAW경로, 폴더경로, 파일이름, 파일이름순서, 동작주파수, , 측정위치 순이다.

    # global offset 을 구해야하는지 판단하는 구문 **************************************************************************
    if mode == 0:
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
        gBoard_offset_f1 = HEXLittleEndian(oldOffsetDEC)
    elif frequency == 20:
        oldOffsetDEC = simmian.ReadI2C(gDeviceID, gStartAddress_f2, 2)
        time.sleep(0.010)
        gBoard_offset_f2 = HEXLittleEndian(oldOffsetDEC)



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
        global gBoard_offset_f1, gBoard_offset_f2

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


def FindBoardoffset(freq, value, countIndex):  # (freq)(int)동작주파수 , (value)(float)측정값
    # 기준거리 500 mm 에서 옵셋을 어느범위안까지 조정을 할 것인가?
    lsl = gLSLGuardSpec  # at 500 mm
    usl = gUSLGuardSpec  # at 500 mm

    if value > lsl and value < usl:
        msg_print(f'Measurement Depth mm -> {value}')
        msg_print("No need to find global offsets.")
        return False
    else:
        msg_print(f'Measurement Depth mm -> {value}')
        msg_print("It need to find global offsets.")
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
    if init_() == False:
        return 100#sys.exit("It can not connect with simmian")
    else:
        return True


def ProcSimmianReset():
    re = ResetSimmian()

    return re


def ProcSimmianStop():
    simmian.Stop()
    time.sleep(0.010)
    simmian.Disconnect()


# 2023-02-17 ::: 배중호, 심미안툴에서 센서ID읽기
def get_sensor_id():
    list = [0 for i in range(13)]

    temp = simmian.ReadI2C(0xA0, "0x00B9", 1)
    list[0] = format(temp, '02X')
    # print(f'simmian readI2C 0x00B9 1 Byte  -> {temp} , hex -> {list[0]}')

    temp = simmian.ReadI2C(0xA0, "0x00BA", 1)
    list[1] = format(temp, '02X')
    # print(f'simmian readI2C 0x00BA 1 Byte  -> {temp} , hex -> {list[1]}')

    temp = simmian.ReadI2C(0xA0, "0x00BB", 1)
    list[2] = format(temp, '02X')
    # print(f'simmian readI2C 0x00BB 1 Byte  -> {temp} , hex -> {list[2]}')

    temp = simmian.ReadI2C(0xA0, "0x00BC", 1)
    list[3] = format(temp, '02X')
    # print(f'simmian readI2C 0x00BC 1 Byte  -> {temp} , hex -> {list[3]}')

    temp = simmian.ReadI2C(0xA0, "0x00BD", 1)
    list[4] = format(temp, '02X')
    # print(f'simmian readI2C 0x00BD 1 Byte  -> {temp} , hex -> {list[4]}')

    temp = simmian.ReadI2C(0xA0, "0x00BE", 1)
    list[5] = format(temp, '02X')
    # print(f'simmian readI2C 0x00BE 1 Byte  -> {temp} , hex -> {list[5]}')

    temp = simmian.ReadI2C(0xA0, "0x00BF", 1)
    list[6] = format(temp, '02X')
    # print(f'simmian readI2C 0x00BF 1 Byte  -> {temp} , hex -> {list[6]}')

    temp = simmian.ReadI2C(0xA0, "0x00C0", 1)
    list[7] = format(temp, '02X')
    # print(f'simmian readI2C 0x00C0 1 Byte  -> {temp} , hex -> {list[7]}')

    temp = simmian.ReadI2C(0xA0, "0x00C1", 1)
    list[8] = format(temp, '02X')
    # print(f'simmian readI2C 0x00C1 1 Byte  -> {temp} , hex -> {list[8]}')

    temp = simmian.ReadI2C(0xA0, "0x00C2", 1)
    list[9] = format(temp, '02X')
    # print(f'simmian readI2C 0x00C2 1 Byte  -> {temp} , hex -> {list[9]}')

    temp = simmian.ReadI2C(0xA0, "0x00C3", 1)
    list[10] = format(temp, '02X')
    # print(f'simmian readI2C 0x00C3 1 Byte  -> {temp} , hex -> {list[10]}')

    temp = simmian.ReadI2C(0xA0, "0x00C4", 1)
    list[11] = format(temp, '02X')
    # print(f'simmian readI2C 0x00C4 1 Byte  -> {temp} , hex -> {list[11]}')

    temp = simmian.ReadI2C(0xA0, "0x00C5", 1)
    list[12] = format(temp, '02X')
    # print(f'simmian readI2C 0x00C5 1 Byte  -> {temp} , hex -> {list[12]}')

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
            return 62
        else:
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


    except Exception as e:
        print(e)
        return 62


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
    msg_print(f'Create a 100MHz set-file for Validation ')

    global g100MHzSetFilePath

    # 100 MHz 만들기 단계
    cmd = [gBatchPath100MHz]  # CMD는 반드시 관리자 권한을 실행해야한다. cd /d d:\LSI_VST63D\4_Validation\create_setfile

    re = subprocess.call(cmd, shell=True) #re = subprocess.run(cmd, shell=True)
    if re == 0: # 정상 종료
        msg_print(f'')
    else:
        msg_print(f'  : Fail')
        for proc in psutil.process_iter():
            if proc.name() == "update_cal_data_to_setfile.exe":
                proc.kill()
        return 120

    src = f'%s\%s' % (gRootPath, g100MHzSetFileName)
    dst = f'%s\%s' % (gSaveModulePath, g100MHzSetFileName)
    shutil.move(src, dst)  # 전체경로 주소로 해줘야 이미 존재하는 파일명이면 덮어쓰기 한다
    g100MHzSetFilePath = dst

    # 검증 -> 셋파일 생성 유무
    bfile = os.path.isfile(g100MHzSetFilePath)
    if bfile == True:
        msg_print(f'  : Success')
        time.sleep(0.010)
        return True
    else:
        msg_print(f'  : Fail')
        return 120



def ProcCreateSetFile20():
    msg_print(f'Create a 20MHz set-file for Validation ')
    global g20MHzSetFilePath

    # 20 MHz 만들기 단계
    cmd = [gBatchPath20MHz]  # CMD는 반드시 관리자 권한을 실행해야한다. cd /d d:\LSI_VST63D\4_Validation\create_setfile

    re = subprocess.call(cmd, shell=True) # re = subprocess.run(cmd, shell=True)
    if re == 0: # 정상 종료
        msg_print(f'')
    else:
        msg_print(f'  : Fail')
        for proc in psutil.process_iter():
            if proc.name() == "update_cal_data_to_setfile.exe":
                proc.kill()
        return 120

    src = f'%s\%s' % (gRootPath, g20MHzSetFileName)
    dst = f'%s\%s' % (gSaveModulePath, g20MHzSetFileName)
    shutil.move(src, dst)  # 전체경로 주소로 해줘야 이미 존재하는 파일명이면 덮어쓰기 한다
    g20MHzSetFilePath = dst

    # 검증 -> 셋파일 생성 유무
    bfile = os.path.isfile(g20MHzSetFilePath)
    if bfile == True:
        msg_print(f'  : Success')
        time.sleep(0.010)
        return True
    else:
        msg_print(f'  : Fail')
        return 120



def ProcLoadSetFile100mhz():
    path = g100MHzSetFilePath

    if os.path.isfile(path):
        if simmian.LoadSetfile(path):
            msg_print(f'Success , it can load the setfile')
        else:
            msg_print(f'Failure. it can not load the setfile')
            return 121  # sys.exit('Error!!!!')
    else:
        msg_print("Failure, it find not a file ")
        return 120 #sys.exit('Error!!!!')

    time.sleep(0.1)


def ProcLoadSetFile20mhz():
    path = g20MHzSetFilePath

    if os.path.isfile(path):
        if simmian.LoadSetfile(path):
            msg_print(f'Success , it can load the setfile')
        else:
            msg_print(f'Failure , it can not load the setfile')
            return 121
    else:
        msg_print("Failure, it find not a file ")
        return 120 #sys.exit('Error!!!!')




def ProcFindGlobalOffset(freq, depthCTValue, countIndex):
    # depthCTValue 가 LSL-USL을 만족하는지 FindBoardoffset( ) 에서 검사한다.
    re = FindBoardoffset(freq, depthCTValue, countIndex)  # (freq)(int)주파수, (depthCTValue)(float)측정값

    if re == True:  # True -> 옵셋을 찾아야한다. , False -> 옵셋을 찾지 않아도 된다.
        find_offset(freq, depthCTValue, countIndex)  # (freq)(int)동작주파수 , (value)(float)측정값

        # 옵셋을 찾은 뒤 재검사
        if freq == 100:
            # 심미안 초기화
            ResetSimmian()
            # 셋파일 생성
            ProcCreateSetFile100()
            # 심미안 초기화
            ResetSimmian()
            # 100 MHz 셋파일 로딩
            ProcLoadSetFile100mhz()
            # 측정
            ProcSaveRaw100mhz50cm(0)  # 0 -> find global offset
        elif freq == 20:
            # 심미안 초기화
            ResetSimmian()
            # 셋파일 생성
            ProcCreateSetFile20()
            # 심미안 초기화
            ResetSimmian()
            # 100 MHz 셋파일 로딩
            ProcLoadSetFile20mhz()
            # 측정
            ProcSaveRaw20mhz50cm(0)  # 0 -> find global offset
        else:
            msg_print(f'ERROR!!! -> ProcFindGlobalOffset( )')
    else:
        msg_print(f' ')
        return True


def ProcSaveRaw100mhz50cm(mode):
    if mode == 0:
        msg_print(f'Start the 100MHz Global Offset process.')
    else:
        msg_print(f'Start the 100MHz Validation process.')

    time.sleep(1)

    savePath = g100mhz50cm
    gOutputFilePrefix = f'image100mhz'
    validation(gOutputFilePrefix, savePath, 100, mode, gCaptureCnt, 500)

    msg_print("Capture Done : 100 MHz at 500 mm")



def ProcSaveRaw100mhz30cm(mode):
    if mode == 0:
        msg_print(f'Start the 100MHz Global Offset process.')
    else:
        msg_print(f'Start the 100MHz Validation process.')

    time.sleep(1)

    savePath = g100mhz30cm
    gOutputFilePrefix = f'image100mhz'
    validation(gOutputFilePrefix, savePath, 100, mode, gCaptureCnt, 300)

    msg_print("Capture Done : 100 MHz at 300 mm")



def ProcSaveRaw20mhz50cm(mode):
    if mode == 0:
        msg_print(f'Start the 20MHz Global Offset process.')
    else:
        msg_print(f'Start the 20MHz Validation process.')

    time.sleep(1)

    savePath = g20mhz50cm
    gOutputFilePrefix = f'image20mhz'
    validation(gOutputFilePrefix, savePath, 20, mode, gCaptureCnt, 500)

    msg_print("Capture Done : 20 MHz at 500 mm")

    msg_print(f' ')



def ProcSaveRaw20mhz30cm(mode):
    if mode == 0:
        msg_print(f'Start the 20MHz Global Offset process.')
    else:
        msg_print(f'Start the 20MHz Validation process.')

    time.sleep(1)

    savePath = g20mhz30cm
    gOutputFilePrefix = f'image20mhz'
    validation(gOutputFilePrefix, savePath, 20, mode, gCaptureCnt, 300)

    msg_print("Capture Done : 20 MHz at 300 mm")



def ProcCreateReport(mode):
    re = create_report(mode, gSaveModulePath, gResult, gCaptureCnt)

    return re



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
        set_board_offset_f1 = 16931  # 계산한 옵셋이 0xabcd 이라면, WriteI2C 에 입력되는 값은 0xcdab 로 넣어야한다.
        set_board_offset_f1_ = HEXLittleEndian(set_board_offset_f1)
        simmian.WriteI2C(0xA0, "0x0108", set_board_offset_f1_)  # board offset f1 100MHz 0x0108 주소
        time.sleep(0.010)

        re = ResetSimmian()
        if re == 100:
            return 100

        re_read_board_offset_f1 = simmian.ReadI2C(0xA0, "0x0108", 2)

        msg_print(f'Write -> board offset f2(020 MHz), address : 0x010A ')
        set_board_offset_f2 = 16311  # 계산한 옵셋이 0xabcd 이라면, WriteI2C 에 입력되는 값은 0xcdab 로 넣어야한다.
        set_board_offset_f2_ = HEXLittleEndian(set_board_offset_f2)
        simmian.WriteI2C(0xA0, "0x010A", set_board_offset_f2_)  # board offset f2 20MHz 0x010A 주소
        time.sleep(0.010)

        re = ResetSimmian()
        if re == 100:
            return 100

        re_read_board_offset_f2 = simmian.ReadI2C(0xA0, "0x010A", 2)

        return True

    except Exception as e:
        print(e)
        return 103



def main_val():
    global gMotor, glogpath

    # 로그 생성
    #logging.basicConfig(filename=glogpath, level=logging.DEBUG)
    simmian = python_simmian_api.Simmian()


    # 관리자 권한으로 실행했는지 확인함*********************************************************************************
    if not winsys.is_admin():
        msg_print(f'You should run this program with administrator.')
        return 101 #sys.exit(-1)


    # 모터 초기화 *****************************************************************************************************
    #msg_print(f'Start motor initialization.')
    #want_home_position_at_start = True
    #motion_obj = motion.Motion()
    #gMotor = motor_open(want_home_position_at_start)
    #if (want_home_position_at_start):
    #    motor_move(distance=500, motion_abs=motion_dist500)  # 2023_01_13, 500mm(397.8)->506.6mm(402.2)
    #    time.sleep(0.5)


    # 심미안 플레이 ****************************************************************************************************
    #msg_print(f'심미안 뷰어의 재생을 시작합니다.')
    re = simmian.GetBoardCount()
    if re == 0:
        msg_print(f'Failure, it can not find Simmian.')
        return 100

    re = ProcSimmianPlay()
    if re == 100:
        msg_print(f'Failure, it can not turn on Simmian.')
        return re

    # board offset 넣기 ***********************************************************************************************
    re = True #InitGlobalOffsetWriteI2C()  # # write f1 0x7446 f2 0x7d40 비교
    if re == 100 and re == 103:
        return re


    # 모듈 번호 입력 ***************************************************************************************************
    re = ProcCreateModuleFolder()
    if 62 == re:
        return re


    # 셋파일 (100 MHz / 20 MHz ) 만들기 ********************************************************************************
    re = ProcCreateSetFile100()
    if 120 == re:
        return re

    re = ProcCreateSetFile20()
    if 120 == re:
        return re


    # 심미안 리셋 ******************************************************************************************************
    re = ProcSimmianReset()
    if re == 100:
        return re

    # 100 MHz 셋파일 로딩 **********************************************************************************************
    re = ProcLoadSetFile100mhz()
    if re == 120 and re == 121:
        return re


    # RAW 저장 100MHz (위치 : 500 mm ) *********************************************************************************
    time.sleep(gWarmup)  # 성능평가를 위한 뎁스 영상 취득 전에 워밍업 3초

    #ProcSaveRaw100mhz50cm(0)  # 0 -> find global offset

    ProcSaveRaw100mhz50cm(1)  # 1 -> only measurement

    # 심미안 리셋 ******************************************************************************************************
    re = ProcSimmianReset()
    if re == 100:
        return re

    # 모터 제어 : 위치 이동 300 mm *************************************************************************************
    #motor_move(distance=300, motion_abs=motion_dist300)  # 2023_01_13, 300mm(195.5)->306.6mm(199.5)
    #time.sleep(1)

    # 100 MHz 셋파일 로딩 **********************************************************************************************
    #re = ProcLoadSetFile100mhz()
    #if re == 120 and re == 121:
    #    return re

    #time.sleep(0.1)

    # RAW 저장 100 MHz (위치 : 300 mm ) ********************************************************************************
    #time.sleep(1)  # 성능평가를 위한 뎁스 영상 취득 전에 워밍업 3초
    #ProcSaveRaw100mhz30cm(1)  # 1 -> only measurement

    # 심미안 리셋 ******************************************************************************************************
    re = ProcSimmianReset()
    if re == 100:
        return re

    # 모터 제어 : 위치 이동 500 mm *************************************************************************************
    #motor_move(distance=500, motion_abs=motion_dist500)  # 2023_01_13, 500mm(397.8)->506.6mm(402.2)
    #time.sleep(1)

    #  20 MHz 셋파일 로딩 ***********************************************************************************************
    re = ProcLoadSetFile20mhz()
    if re == 120 and re == 121:
        return re

    time.sleep(0.1)

    # RAW 저장 20 MHz (위치 : 500 mm ) *********************************************************************************
    time.sleep(gWarmup)  # 성능평가를 위한 뎁스 영상 취득 전에 워밍업 3초

    #ProcSaveRaw20mhz50cm(0)  # 0 -> find global offset

    ProcSaveRaw20mhz50cm(1)  # 1 -> only measurement

    # 심미안 리셋 ******************************************************************************************************
    #re = ProcSimmianReset()
    #if re == 100:
    #    return re

    # 모터 제어 : 위치 이동 300 mm *************************************************************************************
    #motor_move(distance=300, motion_abs=motion_dist300)  # 2023_01_13, 300mm(195.5)->306.6mm(199.5)
    #time.sleep(1)

    #  20 MHz 셋파일 로딩 **********************************************************************************************
    #re = ProcLoadSetFile20mhz()
    #if re == 120 and re == 121:
    #    return re

    #time.sleep(0.1)

    # RAW 저장 20 MHz (위치 : 300 mm ) *********************************************************************************
    #time.sleep(1)  # 성능평가를 위한 뎁스 영상 취득 전에 워밍업 3초
    #ProcSaveRaw20mhz30cm(1)  # 1 -> only measurement

    # APC Check ::: 2023-01-27 ****************************************************************************************
    # APCCheck(100)
    # APCCheck(20)

    # 심미안 종료 ******************************************************************************************************
    ProcSimmianStop()

    # 모터 닫기 ********************************************************************************************************
    #motor_move(distance=500, motion_abs=motion_dist500)  # 2023_01_13, 500mm(397.8)->506.6mm(402.2)
    #ProcMotorClose()

    # 결과 출력 ********************************************************************************************************
    msg_print(f'Create a report of evaluation.')
    result = ProcCreateReport(1)  # 0 -> find global offset , 1 -> only measurement

    msg_print("done. please replace with next module")

    return result #sys.exit()


if __name__ == "__main__":
    main_val()
