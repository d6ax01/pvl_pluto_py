from __future__ import with_statement
import datetime  # 현재 시간 출력용
import os
import os.path
import shutil
import subprocess
import sys
import time  # sleep 함수 사용
import numpy as np
import motion  # 모터
import python_ezimotor_api  # 모터
import python_simmian_api
import pandas as pd  # pip install pandas
import struct

from waiting import wait
import winsys #pip install winsys


# motor ===============================================
gMotor = -1
# =====================================================

# cal_data
#####################################################
gBoard_offset_f1 = f''
gBoard_offset_f2 = f''
gDeviceID = 0xA0
gStartAddress_f1 = f'0x0108'
gEndAddress_f1 = f'0x0109'
gStartAddress_f2 = f'0x010A'
gEndAddress_f2 = f'0x010B'
#####################################################

gRootPath = f'%s\%s' % (f'D:\LSI_VST63D', f'4_Validation')

# Configuration about Image Capture
#####################################################
gOutputFilePrefix = f'Image'
gRootSavePath = f'%s\%s' % (f'D:\LSI_VST63D', f'4_Validation\save')
gOutputDirPrefix = f'image'
gCaptureCnt = 5
gMotorSettleTimeSec = 3
#####################################################

# Configuration about Set File for Validation
#####################################################
gRootSetFilePath = f'%s\%s' % (f'D:\LSI_VST63D', f'4_Validation\save')
gSaveModulePath = f' '
g100MHzSetFileName = f'100M_1109.set'
g20MHzSetFileName = f'20M_1109.set'
g100MHzSetFilePath = f' '
g20MHzSetFilePath = f' '
g20mhz30cm = f' '
g20mhz50cm = f' '
g100mhz30cm = f' '
g100mhz50cm = f' '
gDepth_U16 = f'DEPTH_U16'
gIntensity = f'INTENSITY'
gBinFileName = f'_ToF_cal_100MHz.bin'
gResult = np.zeros((100, 20))  # dtypr 설정 안해주면 기본값 float64
g100mhzDepthValue = 0
g20mhzDepthValue = 0
gLSLGuardSpec = 490
gUSLGuardSpec = 510

JudgeResult_f1 = [0 for i in range(20)]
JudgeResult_f2 = [0 for i in range(20)]

#####################################################

# Configuration about Create Set File
#####################################################
gRootPathOriginalSetFile = f'%s\%s' % (f'D:\LSI_VST63D', f'4_Validation\create_setfile')
gBatchPath100MHz = f'%s\%s' % (gRootPathOriginalSetFile, f'1.bat')
gBatchPath20MHz = f'%s\%s' % (gRootPathOriginalSetFile, f'2.bat')

#####################################################

# APC Check
#####################################################
gApc_check_at_lsw_fix1_f1 = 0   
gApc_check_at_lsw_fix2_f1 = 0   
gApc_check_at_lsw_fix1_f2 = 0   
gApc_check_at_lsw_fix2_f2 = 0
#####################################################


gCurrPath = os.getcwd()
simmian = python_simmian_api.Simmian()


def init_():
    re = simmian.Play()
    if re:
        msg_print(f'Success, it can connect.')
    else:
        msg_print(f'Failure, it can not connect.')
        return False


def StopSimmian():
    re = simmian.Stop()
    if re:
        msg_print(f'Success, it can stop.')
    else:
        msg_print(f'Failure, it can not stop.')
        return False


def ResetSimmian():
    simmian.Reset()
    return True
    re = simmian.Stop()
    if re:
        msg_print(f'Success, it can stop.')
        time.sleep(0.5)
    else:
        msg_print(f'Failure, it can not stop.')
        return False

    re = simmian.Play()
    if re:
        msg_print(f'Success, it can connect.')
        time.sleep(0.5)
    else:
        msg_print(f'Failure, it can not connect.')
        return False


def DisconnetSimmian():
    re = simmian.Disconnect()
    if re:
        msg_print(f'Success, it can disconnect.')
    else:
        msg_print(f'Failure, it can not disconnect. ')
        return False


def DoCapture(prefix, path):
    simmian.SequentialCapture(prefix, path, gCaptureCnt)  # 시퀀셜캡처는 RAW저장 시간이 매우 느리다.
    print("  Done")


def DoSingleCapture(prefix, path):
    filePath = r"%s\%s_.raw" % (path, prefix)
    print('  save path : ', filePath)
    result = simmian.Capture(filePath, captureCount=1)


def create_folder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print('  Error: Creating directory. {0}'.format(directory))



def WriteCmd(id, addr, val):
	page_str = '0x' + format(addr, '08X')[0:4]
	addr_str = '0x' + format(addr, '08X')[4:8]
	val_str = '0x' + format(val, '04X')
	simmian.WriteI2C(id, '0x6028', page_str)
	time.sleep(0.010)	# 10ms
	simmian.WriteI2C(id, '0x602A', addr_str)
	time.sleep(0.010)	# 10ms
	simmian.WriteI2C(id, '0x6F12', val_str)
	time.sleep(0.010)	# 10ms
	return

def ReadCmd(id, addr, num):
	page_str = '0x' + format(addr, '08X')[0:4]
	addr_str = '0x' + format(addr, '08X')[4:8]
	simmian.WriteI2C(id, '0x602C', page_str)
	time.sleep(0.010)	# 10ms
	simmian.WriteI2C(id, '0x602E', addr_str)
	time.sleep(0.010)	# 10ms
	val = simmian.ReadI2C(id, '0x6F12', num)
	time.sleep(0.010)	# 10ms
	return val

def SetVcselCurrent(current_mA):
    current_code = int(current_mA/12) # val = mA / 12
    WriteCmd(0x20, 0x2000E3A0, 0x0001) # number of write bytes
    WriteCmd(0x20, 0x2000E3A2, 0x0008) # register address of VCSEL Driver
    WriteCmd(0x20, 0x2000E3A4, current_code) # data for 0x08
    WriteCmd(0x20, 0x2000E3A6, 0x00FF) # Delay command
    WriteCmd(0x20, 0x2000E3A8, 0x000F) # Data for Delay, 13.3us
    WriteCmd(0x20, 0x2000E3AA, 0x0000) # Terminates command array
    WriteCmd(0x20, 0x2000E3E0, 0x0001) # data at end address
    print("Setting done: ", current_mA, "mA")

def ReadPdValue():
    WriteCmd(0x20, 0x2000E40A, 0x0001)  # read operation_per_frame
    WriteCmd(0x20, 0x2000E3E2, 0x0023)  # CHECK_APC_IMOD[9:8], PD value
    WriteCmd(0x20, 0x2000E3E4, 0xFFFF)  # termination code
    WriteCmd(0x20, 0x2000E40E, 0x0001)  #
    CHECK_APC_IMOD_B9_B8 = ReadCmd(0x20, 0x2000E3F6, 2) # Read two bytes. (Return value, Use 2nd value)
    CHECK_APC_IMOD_B9_B8 = (CHECK_APC_IMOD_B9_B8 & 0xFF)

    WriteCmd(0x20, 0x2000E40A, 0x0001)  # read operation_per_frame
    WriteCmd(0x20, 0x2000E3E2, 0x0026)  # CHECK_APC_IMOD[7:0], PD value
    WriteCmd(0x20, 0x2000E3E4, 0xFFFF)  # termination code
    WriteCmd(0x20, 0x2000E40E, 0x0001)  #
    CHECK_APC_IMOD_B7_B0 = ReadCmd(0x20, 0x2000E3F6, 2) # Read two bytes. (Return value, Use 2nd value)
    CHECK_APC_IMOD_B7_B0 = (CHECK_APC_IMOD_B7_B0 & 0xFF)

    pd_val = (((CHECK_APC_IMOD_B9_B8 & 0x20) >> 5) * (2**9)) + (((CHECK_APC_IMOD_B9_B8 & 0x10) >> 4) * (2**8)) + (CHECK_APC_IMOD_B7_B0)
    print("PD value[7:0] = ", hex(CHECK_APC_IMOD_B7_B0))
    print("PD value[9:8] = ", hex(CHECK_APC_IMOD_B9_B8 & 0x30))
    
    return pd_val

    
def APCCheck(freq):
    global gApc_check_at_lsw_fix1_f1, gApc_check_at_lsw_fix2_f1, gApc_check_at_lsw_fix1_f2, gApc_check_at_lsw_fix2_f2

    if freq == 100:
        SetVcselCurrent(2700) # 1st current: 2700mA
        gApc_check_at_lsw_fix1_f1 = ReadPdValue() #value = ReadPdValue()
        print("PD val 100MHz 2700mA = ", gApc_check_at_lsw_fix1_f1, "(", hex(gApc_check_at_lsw_fix1_f1), ")")
        SetVcselCurrent(1500) # 1st current: 1500mA
        gApc_check_at_lsw_fix2_f1 = ReadPdValue()#value = ReadPdValue()
        print("PD val 100MHz 1500mA = ", gApc_check_at_lsw_fix2_f1, "(", hex(gApc_check_at_lsw_fix2_f1), ")")
    elif freq == 20:
        SetVcselCurrent(2700) # 1st current: 2700mA
        gApc_check_at_lsw_fix1_f2 = ReadPdValue() #value = ReadPdValue()
        print("PD val 20MHz 2700mA = ", gApc_check_at_lsw_fix1_f2, "(", hex(gApc_check_at_lsw_fix1_f2), ")")
        SetVcselCurrent(1500) # 1st current: 1500mA
        gApc_check_at_lsw_fix2_f2 = ReadPdValue() #value = ReadPdValue()
        print("PD val 20MHz 1500mA = ", gApc_check_at_lsw_fix2_f2, "(", hex(gApc_check_at_lsw_fix2_f2), ")")
    else:
        print("Error!!! -> APC Check")


def find_judge(freq, data, indexCount):
    # 2. 결과에 대한 양불 판정을 시작한다.
    # 다빈치 후면 ToF 모듈 검사 항목(나무가)를 임시 사양으로 한다.
    # Z축 잡음(Noise),    중심 QVGA,    촬영거리 500mm, 02.5 mm ( 00.5 % ) 이하
    # Z축 오차(Error),    중심 QVGA,    촬영거리 300mm, 30.0 mm ( 10.0 % ) 이하
    # Z축 오차(Error),    중심 QVGA,    촬영거리 500mm, 15.0 mm ( 03.0 % ) 이하
    # Z축 오차(Error),    주변 QVGA,    촬영거리 500mm, 25.0 mm ( 05.0 % ) 이하
    # 픽셀 밝기 레벨,     중심,         촬영거리 500mm, 480 ~ 1900
    # 픽셀 밝기 레벨,     주변,         촬영거리 500mm, 340 ~ 1500

    # // 2-3. 300mm Depth Validation Data_f1 ****************************************************************************************************
    # // 검사 사양 : 300mm Depth Validation Data_f1
    DepthErrorAVG300_Spec_Center = 30.0  # //300mm Depth Validation Data_f1 -> Depth mean of center ROI

    # // 판정 플래그 : 300mm Depth Validation Data_f1
    _b300mm_Depth_Validation_Data_f1_01F_CT_ROI = False
    #
    # // 판정 비교
    f1_1 = data[0]  # 300 CT Error
    if (300 - DepthErrorAVG300_Spec_Center) <= f1_1 and (300 + DepthErrorAVG300_Spec_Center) >= f1_1:
        _b300mm_Depth_Validation_Data_f1_01F_CT_ROI = True
    else:
        _b300mm_Depth_Validation_Data_f1_01F_CT_ROI = False

    # 2-1. 500mm Depth Validation Data_f1 (QVGA) ****************************************************************************************
    # 2-1-1. Depth mean *****************************************************************************************************************
    # 시작 ******************************************************************************************************************************
    #
    # 검사 사양 : 500mm Depth Validation Data_f1 (QVGA) -> Depth mean of ...
    DepthErrorAVG500_Spec_Center = 15.0;  # 500mm Depth Validation Data_f1 (QVGA) -> Depth mean of center ROI
    DepthErrorAVG500_Spec_06Field = 25.0;  # 500mm Depth Validation Data_f1 (QVGA) -> Depth mean of 0.6F ROI

    # 검사 플래그 : 500mm Depth Validation Data_f1 (QVGA) -> Depth mean of ...
    _b500mm_Depth_Validation_Data_f1_Depth_mean_of_01F_CT_ROI = False
    _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_LT_ROI = False
    _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_RT_ROI = False
    _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_RB_ROI = False
    _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_LB_ROI = False

    # // 판정 비교 : 500mm Depth Validation Data_f1 (QVGA) -> Depth mean of center ROI
    f1_2 = data[0]
    if (500 - DepthErrorAVG500_Spec_Center) <= f1_2 and (500 + DepthErrorAVG500_Spec_Center) >= f1_2:
        _b500mm_Depth_Validation_Data_f1_Depth_mean_of_01F_CT_ROI = True
    else:
        _b500mm_Depth_Validation_Data_f1_Depth_mean_of_01F_CT_ROI = False

    # // 판정 비교 : 500mm Depth Validation Data_f1 (QVGA) -> Depth mean of 0.6F LT ROI
    f1_3 = data[1]
    if (500 - DepthErrorAVG500_Spec_06Field) <= f1_3 and (500 + DepthErrorAVG500_Spec_06Field) >= f1_3:
        _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_LT_ROI = True
    else:
        _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_LT_ROI = False

    # // 판정 비교 : 500mm Depth Validation Data_f1 (QVGA) -> Depth mean of 0.6F RT ROI
    f1_4 = data[2]
    if (500 - DepthErrorAVG500_Spec_06Field) <= f1_4 and (500 + DepthErrorAVG500_Spec_06Field) >= f1_4:
        _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_RT_ROI = True
    else:
        _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_RT_ROI = False

    # // 판정 비교 : 500mm Depth Validation Data_f1 (QVGA) -> Depth mean of 0.6F RB ROI
    f1_5 = data[3]
    if (500 - DepthErrorAVG500_Spec_06Field) <= f1_5 and (500 + DepthErrorAVG500_Spec_06Field) >= f1_5:
        _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_RB_ROI = True
    else:
        _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_RB_ROI = False

    # // 판정 비교 : 500mm Depth Validation Data_f1 (QVGA) -> Depth mean of 0.6F LB ROI
    f1_6 = data[4]
    if (500 - DepthErrorAVG500_Spec_06Field) <= f1_6 and (500 + DepthErrorAVG500_Spec_06Field) >= f1_6:
        _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_LB_ROI = True
    else:
        _b500mm_Depth_Validation_Data_f1_Depth_mean_of_06F_LB_ROI = False

    # // ***********************************************************************************************************************************
    # // 2-1-2. Validation Noise ***********************************************************************************************************
    # // 시작 ******************************************************************************************************************************
    # // Z축 잡음(Noise),    중심 QVGA,    촬영거리 500mm, 02.5 mm ( 0.5 % ) 이하
    #
    # // 검사 사양 : 500mm Depth Validation Data_f1 (QVGA) - Validation Noise
    DepthNoiseAVG500_Spec_Center = 2.5;  # 500mm Depth Validation Data_f1 (QVGA) -> Validation Noise of center ROI
    DepthNoiseAVG500_Spec_06Field = 5.0;  # 500mm Depth Validation Data_f1 (QVGA) -> Validation Noise of 0.6F ROI

    # // 검사 플래그 : 500mm Depth Validation Data_f1 (QVGA) - Validation Noise
    _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_01F_CT_ROI = False
    _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_LT_ROI = False
    _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_RT_ROI = False
    _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_RB_ROI = False
    _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_LB_ROI = False

    # // 판정 비교 : Validation Noise of center ROI
    f1_7 = data[5]
    if DepthNoiseAVG500_Spec_Center >= f1_7:
        _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_01F_CT_ROI = True
    else:
        _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_01F_CT_ROI = False

    # // 판정 비교 : Validation Noise of 0.6F ROI -> LT
    f1_8 = data[6]
    if DepthNoiseAVG500_Spec_06Field >= f1_8:
        _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_LT_ROI = True
    else:
        _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_LT_ROI = False

    # // 판정 비교 : Validation Noise of 0.6F ROI -> RT
    f1_9 = data[7]
    if DepthNoiseAVG500_Spec_06Field >= f1_9:
        _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_RT_ROI = True
    else:
        _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_RT_ROI = False

    # // 판정 비교 : Validation Noise of 0.6F ROI -> RB
    f1_10 = data[8]
    if DepthNoiseAVG500_Spec_06Field >= f1_10:
        _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_RB_ROI = True
    else:
        _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_RB_ROI = False

    # // 판정 비교 : Validation Noise of 0.6F ROI -> LB
    f1_11 = data[9]
    if DepthNoiseAVG500_Spec_06Field >= f1_11:
        _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_LB_ROI = True
    else:
        _b500mm_Depth_Validation_Data_f1_Validation_Noise_of_06F_LB_ROI = False

    # // ***********************************************************************************************************************************
    # // 2-2. 500mm VCSEL Optical Power Data_f1 (광량검사 데이터) *******************************************************************************
    # // 시작 ******************************************************************************************************************************
    # // 픽셀 밝기 레벨,     중심,         촬영거리 500mm, 480 ~ 1900
    # // 픽셀 밝기 레벨,     주변,         촬영거리 500mm, 340 ~ 1500
    #
    # // 검사 사양 : 500mm VCSEL Optical Power Data_f1 (광량검사 데이터)
    ConfidenceAVG_Spec_CenterLower = 480;  # //500mm VCSEL Optical Power Data_f1 (광량검사 데이터) -> Center ROI (하한선)
    ConfidenceAVG_Spec_CenterUpper = 1900;  # //500mm VCSEL Optical Power Data_f1 (광량검사 데이터) -> Center ROI (상한선)
    ConfidenceAVG_Spec_06FieldLower = 340;  # //500mm VCSEL Optical Power Data_f1 (광량검사 데이터) -> 0.6F ROI (하한선)
    ConfidenceAVG_Spec_06FieldUpper = 1500;  # //500mm VCSEL Optical Power Data_f1 (광량검사 데이터) -> 0.6F ROI (상한선)
    #
    # // 검사 플래그 : 500mm VCSEL Optical Power Data_f1 (광량false이터)
    _b500mm_VCSEL_Optical_Power_Data_f1_01F_CT_ROI = False
    _b500mm_VCSEL_Optical_Power_Data_f1_06F_LT_ROI = False
    _b500mm_VCSEL_Optical_Power_Data_f1_06F_RT_ROI = False
    _b500mm_VCSEL_Optical_Power_Data_f1_06F_RB_ROI = False
    _b500mm_VCSEL_Optical_Power_Data_f1_06F_LB_ROI = False
    #
    # // 판정 비교
    f1_12 = data[10]
    if ConfidenceAVG_Spec_CenterLower <= f1_12 and ConfidenceAVG_Spec_CenterUpper >= f1_12:
        _b500mm_VCSEL_Optical_Power_Data_f1_01F_CT_ROI = True
    else:
        _b500mm_VCSEL_Optical_Power_Data_f1_01F_CT_ROI = False

    f1_13 = data[11]
    if ConfidenceAVG_Spec_06FieldLower <= f1_13 and ConfidenceAVG_Spec_06FieldUpper >= f1_13:
        _b500mm_VCSEL_Optical_Power_Data_f1_06F_LT_ROI = True
    else:
        _b500mm_VCSEL_Optical_Power_Data_f1_06F_LT_ROI = False

    f1_14 = data[12]
    if ConfidenceAVG_Spec_06FieldLower <= f1_14 and ConfidenceAVG_Spec_06FieldUpper >= f1_14:
        _b500mm_VCSEL_Optical_Power_Data_f1_06F_RT_ROI = True
    else:
        _b500mm_VCSEL_Optical_Power_Data_f1_06F_RT_ROI = False

    f1_15 = data[13]
    if ConfidenceAVG_Spec_06FieldLower <= f1_15 and ConfidenceAVG_Spec_06FieldUpper >= f1_15:
        _b500mm_VCSEL_Optical_Power_Data_f1_06F_RB_ROI = True
    else:
        _b500mm_VCSEL_Optical_Power_Data_f1_06F_RB_ROI = False

    f1_16 = data[14]
    if ConfidenceAVG_Spec_06FieldLower <= f1_16 and ConfidenceAVG_Spec_06FieldUpper >= f1_16:
        _b500mm_VCSEL_Optical_Power_Data_f1_06F_LB_ROI = True
    else:
        _b500mm_VCSEL_Optical_Power_Data_f1_06F_LB_ROI = False

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
        and _b500mm_VCSEL_Optical_Power_Data_f1_01F_CT_ROI
        and _b500mm_VCSEL_Optical_Power_Data_f1_06F_LT_ROI
        and _b500mm_VCSEL_Optical_Power_Data_f1_06F_RT_ROI
        and _b500mm_VCSEL_Optical_Power_Data_f1_06F_RB_ROI
        and _b500mm_VCSEL_Optical_Power_Data_f1_06F_LB_ROI
        and _b300mm_Depth_Validation_Data_f1_01F_CT_ROI == True):
        print(f'모든 조건을 PASS 한다')
        return True
    else:
        print(f'모든 조건을 PASS 하지 못한다')
        return False


def create_report(Path, Result, indexCount):
    # APC 변수 초기화
    global gApc_check_at_lsw_fix1_f1, gApc_check_at_lsw_fix2_f1, gApc_check_at_lsw_fix1_f2, gApc_check_at_lsw_fix2_f2

    gApc_check_at_lsw_fix1_f1 = 0
    gApc_check_at_lsw_fix2_f1 = 0  
    gApc_check_at_lsw_fix1_f2 = 0   
    gApc_check_at_lsw_fix2_f2 = 0


    # summary 엑셀 출력
    df = pd.DataFrame(Result)
    file_path = r'{0}\{1}.xlsx'.format(Path, f'summary')
    df.to_excel(file_path, sheet_name='sheet1', index=False, header=False)
    print(df)

    # 100 MHz
    for i in range(0, 16):
        JudgeResult_f1[i] = Result[0:(indexCount), i].mean()
        print(JudgeResult_f1[i])

    f1_0 = find_judge(100, JudgeResult_f1, indexCount)  # 100 Mhz 검사항목을 모두 통과하면 PASS 아니면 FAIL
    msg_print(f1_0)

    APCCheck(100)

    # 20 MHz
    for i in range(0, 16):
        JudgeResult_f2[i] = Result[(indexCount): (indexCount + ((2 - 1) * indexCount)), i].mean()
        print(JudgeResult_f2[i])

    f2_0 = find_judge(20, JudgeResult_f2, indexCount)  # 20 Mhz 검사항목을 모두 통과하면 PASS 아니면 FAIL
    msg_print(f2_0)

    APCCheck(20)

    # report 엑셀 출력
    df1 = pd.DataFrame(
        [
        [f1_0,
         JudgeResult_f1[0],
         JudgeResult_f1[1], JudgeResult_f1[2], JudgeResult_f1[3], JudgeResult_f1[4], JudgeResult_f1[5],
         JudgeResult_f1[6], JudgeResult_f1[7], JudgeResult_f1[8], JudgeResult_f1[9], JudgeResult_f1[10],
         JudgeResult_f1[11], JudgeResult_f1[12], JudgeResult_f1[13], JudgeResult_f1[14],
         JudgeResult_f1[15],
         gBoard_offset_f1],  # gBoard_offset_f1 -> find offset( ) 에서 global offset 을 계산한다.
         gApc_check_at_lsw_fix1_f1,
         gApc_check_at_lsw_fix2_f1,
        [f2_0,
         JudgeResult_f2[0],
         JudgeResult_f2[1], JudgeResult_f2[2], JudgeResult_f2[3], JudgeResult_f2[4], JudgeResult_f2[5],
         JudgeResult_f2[6], JudgeResult_f2[7], JudgeResult_f2[8], JudgeResult_f2[9], JudgeResult_f2[10],
         JudgeResult_f2[11], JudgeResult_f2[12], JudgeResult_f2[13], JudgeResult_f2[14],
         JudgeResult_f2[15],
         gBoard_offset_f2],  # gBoard_offset_f2 -> find offset( ) 에서 global offset 을 계산한다.
         gApc_check_at_lsw_fix1_f2,
         gApc_check_at_lsw_fix2_f2
         ],
        index=['100 MHz', '20 MHz'],
        columns=['Judge',
                 'Error_CT_300',
                 'Error_CT_500', 'Error_LT_500', 'Error_RT_500', 'Error_RB_500', 'Error_LB_500',
                 'Noise_CT_500', 'Noise_LT_500', 'Noise_RT_500', 'Noise_RB_500', 'Noise_LB_500',
                 'Intensity_CT_500', 'Intensity_LT_500', 'Intensity_RT_500', 'Intensity_RB_500',
                 'Intensity_LB_500',
                 'board_offset f1/f2'
                 'APC Check 2700mA'
                 'APC Check 1500mA'
                 ])

    file_path = r'{0}\{1}.xlsx'.format(Path, f'result')
    df1.to_excel(file_path, sheet_name='sheet1', index=True, header=True)

    print(df1)


def Convert_RawToCSV(filePath, folderPath, prefix, countIndex, frequency, mode,
                     position):  # Convert_RawToCSV(filePath, path, prefix, i) #filePath RAW경로, path폴더경로, prefix파일이름, i파일이름순서, 측정위치
    global gResult, g100mhzDepthValue, g20mhzDepthValue

    path = folderPath
    depth_file = f'%s_%s%s' % (prefix, countIndex, f'.raw')  # 심미안 뷰어에서 'Decode' - 'ToF' 가 선택이 되어야한다.
    intensity_file = f'%s_%s%s' % (prefix, countIndex, f'_VC(2)_DT(Raw8).raw')
    width = 320
    height = 240

    # max_distance = 1500  # 100M = 1500(mm), 20M=7500(mm)
    if frequency == 100:
        max_distance = 1500  # 100M = 1500(mm)
    else:
        max_distance = 7500  # 20M = 7500(mm)

    # depth image
    fullpath = os.path.join(path, depth_file)
    dump = np.fromfile(fullpath, dtype='>B').reshape(height + 4, width * 2)  # '>' big endian, 'B' unsigned byte
    dump = dump[4:, :]  # remove embedded lines
    image = np.zeros((height, width), dtype=np.ushort)
    for h in range(0, height):
        for w in range(0, width):
            image[h, w] = (dump[h, w * 2] << 8) + dump[h, w * 2 + 1]

    depth = np.bitwise_and(image, 0x1FFF).astype(np.float32) / 2 ** 13 * max_distance

    # intensity image
    fullpath = os.path.join(path, intensity_file)
    dump = np.fromfile(fullpath, dtype='B').reshape(height + 0, width * 2)  # '>' big endian, 'H' unsigned short
    image = np.zeros((height, width), dtype=np.ushort)
    for h in range(0, height):
        for w in range(0, width):
            image[h, w] = (dump[h, w * 2] << 8) + dump[h, w * 2 + 1]

    intensity = image / 2 ** 4  # DEPS tool 설정과 동일하게 맞추기 위해 2**4를 함

    # save csv file
    DepthCSV = f'%s%s.csv' % (f'depth', countIndex)
    np.savetxt(os.path.join(folderPath, DepthCSV), depth, delimiter=',')
    # print(f'   Save : %s\%s', folderPath, DepthCSV)

    IntensityCSV = f'%s%s.csv' % (f'intensity', countIndex)
    np.savetxt(os.path.join(folderPath, IntensityCSV), intensity, delimiter=',')
    # print(f'   Save : %s\%s', folderPath, IntensityCSV)

    # 뎁스 오차, 노이즈, 세기 대표 값 계산
    if position == 300:  # 측정 위치 300 mm
        # Depth Error
        gResult[(countIndex + ((mode - 1) * gCaptureCnt)), 0] = depth[114:124, 154:164].mean()  # CT
    else:  # 측정 위치 500 mm
        # Depth Error
        gResult[(countIndex + ((mode - 1) * gCaptureCnt)), 1] = depth[114:124, 154:164].mean()  # CT
        gResult[(countIndex + ((mode - 1) * gCaptureCnt)), 2] = depth[43:53, 59:69].mean()  # LT
        gResult[(countIndex + ((mode - 1) * gCaptureCnt)), 3] = depth[43:53, 250:260].mean()  # RT
        gResult[(countIndex + ((mode - 1) * gCaptureCnt)), 4] = depth[186:196, 250:260].mean()  # RB
        gResult[(countIndex + ((mode - 1) * gCaptureCnt)), 5] = depth[186:196, 59:69].mean()  # LB
        # Depth Noise
        gResult[(countIndex + ((mode - 1) * gCaptureCnt)), 6] = depth[114:124, 154:164].std()  # CT
        gResult[(countIndex + ((mode - 1) * gCaptureCnt)), 7] = depth[43:53, 59:69].std()  # LT
        gResult[(countIndex + ((mode - 1) * gCaptureCnt)), 8] = depth[43:53, 250:260].std()  # RT
        gResult[(countIndex + ((mode - 1) * gCaptureCnt)), 9] = depth[186:196, 250:260].std()  # RB
        gResult[(countIndex + ((mode - 1) * gCaptureCnt)), 10] = depth[186:196, 59:69].std()  # LB
        # Depth Intensity
        gResult[(countIndex + ((mode - 1) * gCaptureCnt)), 11] = intensity[114:124, 154:164].mean()  # CT
        gResult[(countIndex + ((mode - 1) * gCaptureCnt)), 12] = intensity[43:53, 59:69].mean()  # LT
        gResult[(countIndex + ((mode - 1) * gCaptureCnt)), 13] = intensity[43:53, 250:260].mean()  # RT
        gResult[(countIndex + ((mode - 1) * gCaptureCnt)), 14] = intensity[186:196, 250:260].mean()  # RB
        gResult[(countIndex + ((mode - 1) * gCaptureCnt)), 15] = intensity[186:196, 59:69].mean()  # LB

    if frequency == 100:
        g100mhzDepthValue = gResult[(countIndex + ((mode - 1) * gCaptureCnt)), 1]
        print(f'     * 100 MHz Center Measurement Depth mm -> ', g100mhzDepthValue)
    else:
        g20mhzDepthValue = gResult[(countIndex + ((mode - 1) * gCaptureCnt)), 1]
        print(f'     *  20 MHz Center Measurement Depth mm -> ', g20mhzDepthValue)

    return gResult


def validation(prefix, path, frequency, mode, count, pos):
    # prefix -> 100MHz이면 image100mhz , 20MHz이면 image20mhz
    # path -> 저장 경로
    # frequency -> 100 MHz 또는 20 MHz
    # mode -> 0 global offset 찾기 , 1 100mhz at 300 and 500 mm , 2 20mhz at 300 and 500 mm
    # count -> 저장 횟수

    for i in range(0, count):
        filePath = r'{0}\{1}_{2}.raw'.format(path, prefix, i)  # ++_ALL0_f1_nshfl_VC(2)_DT(Raw8).raw
        result = simmian.Capture(filePath, captureCount=1)
        # msg_print(filePath)
        Convert_RawToCSV(filePath, path, prefix, i, frequency, mode, pos)
        # RAW경로, 폴더경로, 파일이름, 파일이름순서, 동작주파수, , 측정위치 순이다.

    # global offset 을 구해야하는지 판단하자. pos = 500(mm) 일 경우에만
    if frequency == 100 and pos == 500:
        ctDepth100 = gResult[0:(count), 1].mean()  # 100MHz 500 CT Error
        print(f'  100 MHz at 500 mm 에서 CT depth = ', ctDepth100)
        ProcFindGlobalOffset(frequency, ctDepth100, count)
    elif frequency == 20 and pos == 500:
        ctDepth20 = gResult[(gCaptureCnt): (gCaptureCnt + ((2 - 1) * gCaptureCnt)), 1].mean()
        print(f'  20 MHz at 500 mm 에서 CT depth = ', ctDepth20)
        ProcFindGlobalOffset(frequency, ctDepth20, count)
    else:
        print(f'')


def calc_offset_f1(oldvalue, measureValue):
    if oldvalue == 32768:
        oldDepthOffset = 0
    else:
        oldDepthOffset = (oldvalue - 32768) / 32768

    DepthCTValue = measureValue  # 500 mm 에서 뎁스 센터 초기치
    Modulation = 1500  # 100 MHz 동작에서 계산 가능한 최대 거리 mm
    DepthOffset = oldDepthOffset + 500 - DepthCTValue  # 기준거리(500) - 측정값
    calcDEC = int(((DepthOffset / Modulation) * 32768) + 32768)

    return calcDEC


def calc_offset_f2(oldvalue, measureValue):
    if oldvalue == 32768:
        oldDepthOffset = 0
    else:
        oldDepthOffset = (oldvalue - 32768) / 32768

    DepthCTValue = measureValue  # 500 mm 에서 뎁스 센터 초기치
    Modulation = 7500  # 20 MHz 동작에서 계산 가능한 최대 거리 mm
    DepthOffset = oldDepthOffset + 500 - DepthCTValue  # 기준거리(500) - 측정값
    calcDEC = int(((DepthOffset / Modulation) * 32768) + 32768)

    return calcDEC


def calc_offset(freq, oldOffsetDEC, MeasureDepthValue):  # (freq)(int)동작주파수, (oldOffsetDEC)(int)현재옵셋값,
    if oldOffsetDEC == 32768:
        oldDepthOffset = 0

    else:
        oldDepthOffset = (oldOffsetDEC - 32768) / 32768

    if freq == 100:
        DepthCTValue = MeasureDepthValue  # 500 mm 에서 뎁스 센터 초기치
        Modulation = 1500  # 100 MHz 동작에서 계산 가능한 최대 거리 mm
        DepthOffset = oldDepthOffset + 500 - DepthCTValue  # 기준거리(500) - 측정값
        calcDEC = int(((DepthOffset / Modulation) * 32768) + 32768)
    elif freq == 20:
        DepthCTValue = MeasureDepthValue  # 500 mm 에서 뎁스 센터 초기치
        Modulation = 7500  # 20 MHz 동작에서 계산 가능한 최대 거리 mm
        DepthOffset = oldDepthOffset + 500 - DepthCTValue  # 기준거리(500) - 측정값
        calcDEC = int(((DepthOffset / Modulation) * 32768) + 32768)
    else:
        msg_print(f'ERROR !!! -> calc_offset(freq, oldOffsetDEC, MeasureDepthValue) ')
        calcDEC = 32768  # global offset 이 (HEX)8000 으로 들어간다.

    return calcDEC


def HEXLittleEndian(input):
    value = input  # input 은 DEC 타입이여야한다.

    # print(f'     * global offset 입력 값 -> ', value, hex(value))

    b_ = struct.pack('<i', value)[0]
    c1 = '%x' % b_
    if c1 == '0':  # 0x00 으로 나올경우 0x0 으로 표현이 되는게 나온다
        c1 = '00'
    elif c1 == '':
        c1 = '00'
    else:
        print('')

    b_ = struct.pack('<i', value)[1]
    c2 = '%x' % b_
    if c2 == '0':  # 0x00 으로 나올경우 0x0 으로 표현이 되는게 나온다
        c2 = '00'
    elif c2 == '':
        c2 = '00'
    else:
        print('')

    d = f'0x%s%s' % (c1, c2)
    # print(f'     * global offset 입력 값 -> ', d)

    return d  # HEX 로 리턴한다


def find_offset(freq, value, countIndex):  # (freq)(int)동작주파수 , (value)(float)측정값
    global gBoard_offset_f1, gBoard_offset_f2

    MeasureDepthValue = value

    if freq == 100:
        # 1 현재 보드 옵셋 값을 읽어한다.
        oldOffsetDEC = simmian.ReadI2C(gDeviceID, gStartAddress_f1, 2)

        # 2 새로 적용해야하는 옵셋 값을 계산한다.
        newOffsetDEC = calc_offset(freq, oldOffsetDEC, MeasureDepthValue)
        gBoard_offset_f1 = hex(newOffsetDEC)

        # 3 심미안 리셋
        re = StopSimmian()
        if re == False:
            sys.exit('FAIL, StopSimmian()')

        # 4 새로 적용해야하는 옵셋 값을 E2P에 쓰기 한다.
        # 계산한 옵셋이 0x ab cd 이라면, WriteI2C 에 입력되는 값은 0x cd ab 로 넣어야한다.
        littleEndian_newOffsetHEX = HEXLittleEndian(newOffsetDEC)
        print(f'  board_offset f1 [현재값] [변경값] [변환] ->', hex(oldOffsetDEC), hex(newOffsetDEC), littleEndian_newOffsetHEX)
        simmian.WriteI2C(0xA0, "0x0108", littleEndian_newOffsetHEX)

        # 5 심미안 리셋
        re = ResetSimmian()
        if re == False:
            sys.exit('FAIL, ResetSimmian()')

        # 6 현재 보드 옵셋 값을 읽어온다
        read_board_offset_f1 = simmian.ReadI2C(0xA0, "0x0108", 2)
        print(f'  대상 값 , E2P 값 비교  -> ', littleEndian_newOffsetHEX, hex(read_board_offset_f1))

        # 7 일치하는지 검사

        # 8 셋파일 생성 단계부터 다시 시작한다.
        #ProcReValidationOffset(freq, '500mm')
        #ProcLoadSetFile100mhz()

    elif freq == 20:
        # 1 현재 보드 옵셋 값을 읽어한다.
        oldOffsetDEC = simmian.ReadI2C(gDeviceID, gStartAddress_f2, 2)

        # 2 새로 적용해야하는 옵셋 값을 계산한다.
        newOffsetDEC = calc_offset(freq, oldOffsetDEC, MeasureDepthValue)
        gBoard_offset_f2 = hex(newOffsetDEC)

        # 3 심미안 리셋
        re = StopSimmian()
        if re == False:
            sys.exit('FAIL, StopSimmian()')

        # 4 새로 적용해야하는 옵셋 값을 E2P에 쓰기 한다.
        # 계산한 옵셋이 0x ab cd 이라면, WriteI2C 에 입력되는 값은 0x cd ab 로 넣어야한다.
        littleEndian_newOffsetHEX = HEXLittleEndian(newOffsetDEC)
        print(f'  board_offset f2 [현재값] [변경값] [변환] ->', hex(oldOffsetDEC), hex(newOffsetDEC), littleEndian_newOffsetHEX)
        simmian.WriteI2C(0xA0, "0x010A", littleEndian_newOffsetHEX)  # newOffsetHEX)


        # 5 심미안 리셋
        re = ResetSimmian()
        if re == False:
            sys.exit('FAIL, ResetSimmian()')

        # 6 현재 보드 옵셋 값을 읽어온다
        read_board_offset_f2 = simmian.ReadI2C(0xA0, "0x010A", 2)
        print(f'  대상 값 , E2P 값 비교  -> ', littleEndian_newOffsetHEX, hex(read_board_offset_f2))

        # 7 일치하는지 검사

        # 8 셋파일 생성 단계부터 다시 시작한다.
        # ProcReValidationOffset(freq, '500mm')
        #ProcLoadSetFile20mhz()
    else:
        msg_print(f'ERROR !!! -> find_offset(freq, value, countIndex)')


def FindBoardoffset(freq, value, countIndex):  # (freq)(int)동작주파수 , (value)(float)측정값

    print(f'  FindBoardoffset( ) 함수 입니다.')
    # 기준거리 500 mm 에서 옵셋을 어느범위안까지 조정을 할 것인가?
    lsl = gLSLGuardSpec  # at 500 mm
    usl = gUSLGuardSpec  # at 500 mm
    FindNeedOffset = False  # True -> 옵셋을 찾아야한다. , False -> 옵셋을 찾지 않아도 된다.

    if value > lsl and value < usl:
        FindNeedOffset = False
        print(f'        * LSL Spec -> ', lsl)
        print(f'        * USL Spec -> ', usl)
        print(f'        * Modulation Frequency MHz -> ', freq)
        print(f'        * Measurement Depth mm -> ', value)
        msg_print("No need to find global offsets.")
    else:
        FindNeedOffset = True
        print(f'        * LSL Spec -> ', lsl)
        print(f'        * USL Spec -> ', usl)
        print(f'        * Modulation Frequency MHz -> ', freq)
        print(f'        * Measurement Depth mm -> ', value)
        msg_print("It need to find global offsets.")

    return FindNeedOffset


def motor_open(want_home_position_at_start):
    motor = python_ezimotor_api.EziMotor(motion.com_port)
    if motor.IsConnected() == False:
        sys.exit('Motor is not connected')
    motor.SetServoParam(motion.axis_no, motion.max_speed, motion.neg_limit, motion.pos_limit, motion.origin_type,
                        motion.speed_origin, motion.motor_type, motion.resolution)
    motor.SetMoveProfile(motion.axis_no, 50, motion.acceleration, motion.deceleration)

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

    if (want_home_position_at_start):
        # Move motor at home position
        motor.ServoHomeStart(motion.axis_no)
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
        print('[ERROR] You should run this program with administrator')
        sys.exit(-1)

    # motor create
    want_home_position_at_start = True
    motion_obj = motion.Motion()
    gMotor = motor_open(want_home_position_at_start)

def move_to_pos(pos):
    if pos == 500:
        motor_position_list = [
            {"distance": pos, "motion_abs": 356},
        ]

        for p in motor_position_list:
            print(f'Motor move {p["distance"]}mm')
            if gMotor.ABSMove_Chk(motion.axis_no, p["motion_abs"]) == False:
                print(f' => Oops: Motor could not move {p["distance"]}')

            gMotor.MoveAbsolute(motion.axis_no, p["motion_abs"])
            wait(lambda: is_motor_ready(gMotor, motion.axis_no), timeout_seconds=120,
                 waiting_for="Motor move to be ready")
            time.sleep(0.5)
    elif pos == 300:
        motor_position_list = [
            {"distance": pos, "motion_abs": 153},
        ]

        for p in motor_position_list:
            print(f'Motor move {p["distance"]}mm')
            if gMotor.ABSMove_Chk(motion.axis_no, p["motion_abs"]) == False:
                print(f' => Oops: Motor could not move {p["distance"]}')

            gMotor.MoveAbsolute(motion.axis_no, p["motion_abs"])
            wait(lambda: is_motor_ready(gMotor, motion.axis_no), timeout_seconds=120,
                 waiting_for="Motor move to be ready")
            time.sleep(0.5)





def msg_print(msg):
    now = datetime.datetime.now()
    str_now = now.strftime('%H:%M:%S')
    print(f'  [%s] %s' % (str_now, msg))  # 현재 시간 출력


def ProcSimmianPlay():
    msg_print(f'심미안 플레이 *****************************************************************************************')
    if init_() == False:
        sys.exit("It can not connect with simmian")


def ProcSimmianReset():
    msg_print(f'심미안 리셋 *******************************************************************************************')
    if ResetSimmian() == False:
        sys.exit("It can not reset with simmian")


def ProcSimmianStop():
    msg_print(f'심미안 종료 *******************************************************************************************')
    if StopSimmian() == False:
        sys.exit("It can not stop with simmian")


def ProcCreateModuleFolder():
    global gSaveModulePath, g20mhz30cm, g20mhz50cm, g100mhz30cm, g100mhz50cm

    msg_print(f'모듈 번호 입력 ****************************************************************************************')
    msg_print('Please enter your module number : ')

    get_module_number = input()  # (관리자모드)CMD 에서 키보드를 이용해서 모듈번호를 입력한다.

    if get_module_number == f'':
        msg_print(f'Please enter your module number : ')
        get_module_number = input()

    # 폴더 이름을 못 받으면 종료
    if get_module_number == f'':
        msg_print(f'Can not folder creation')
        sys.exit('Error!!!!')

    print("  Module Number : ", get_module_number)
    gSaveModulePath = f'%s\%s' % (gRootSavePath, get_module_number)  # 모듈의 저장 경로
    g20mhz30cm = f'%s\%s\%s' % (gRootSavePath, get_module_number, f'20M_30cm')  # 저장 경로 -> 20 MHz로 300 mm
    g20mhz50cm = f'%s\%s\%s' % (gRootSavePath, get_module_number, f'20M_50cm')  # 저장 경로 -> 20 MHz로 500 mm
    g100mhz30cm = f'%s\%s\%s' % (gRootSavePath, get_module_number, f'100M_30cm')  # 저장 경로 -> 100 MHz로 300 mm
    g100mhz50cm = f'%s\%s\%s' % (gRootSavePath, get_module_number, f'100M_50cm')  # 저장 경로 -> 100 MHz로 500 mm

    # 폴더 생성
    create_folder(gSaveModulePath)
    create_folder(g20mhz30cm)
    create_folder(g20mhz50cm)
    create_folder(g100mhz30cm)
    create_folder(g100mhz50cm)
    print(f'  %s -> %s' % (get_module_number, gSaveModulePath))

    print(f' ')

    return gSaveModulePath


def ProcMoveTo500():
    msg_print(f'모터 제어 : 위치 이동 (500 mm) ************************************************************************')
    msg_print("Move to Loading Pos : 500 mm")
    msg_print("Move to loading position completed")

    move_to_pos(500)

    print(f' ')


def ProcMoveto300():
    msg_print(f'모터 제어 : 위치 이동 300 mm **************************************************************************')

    move_to_pos(300)

    print("Move to Loading Pos : ", 300)
    msg_print("Move to 300 mm position completed")
    print(f' ')


def ProcMotorClose():
    msg_print("Close motor communication")
    motor_close(gMotor)
    print(f' ')


def ProcCreateSetFile100():
    global g100MHzSetFilePath

    print(f' ')
    msg_print(f'셋파일 만들기 *****************************************************************************************')
    # 100 MHz 만들기 단계
    cmd = [gBatchPath100MHz]  # CMD는 반드시 관리자 권한을 실행해야한다. cd /d d:\LSI_VST63D\4_Validation\create_setfile
    # print(cmd)
    newSetFile_100M = subprocess.run(cmd, shell=True)

    src100 = f'%s\%s' % (gRootPath, g100MHzSetFileName)
    dst100 = f'%s\%s' % (gSaveModulePath, g100MHzSetFileName)
    shutil.move(src100, dst100)  # 전체경로 주소로 해줘야 이미 존재하는 파일명이면 덮어쓰기 한다
    g100MHzSetFilePath = dst100
    print(f'  Create 100 MHz SetFile done : ', g100MHzSetFilePath)

    time.sleep(0.5)
    print(f' ')


def ProcCreateSetFile20():
    global g20MHzSetFilePath

    msg_print(f'셋파일 만들기 *****************************************************************************************')

    # 20 MHz 만들기 단계
    cmd = [gBatchPath20MHz]  # CMD는 반드시 관리자 권한을 실행해야한다. cd /d d:\LSI_VST63D\4_Validation\create_setfile
    # print(cmd)
    newSetFile_20M = subprocess.run(cmd, shell=True)

    src20 = f'%s\%s' % (gRootPath, g20MHzSetFileName)
    dst20 = f'%s\%s' % (gSaveModulePath, g20MHzSetFileName)
    shutil.move(src20, dst20)  # 전체경로 주소로 해줘야 이미 존재하는 파일명이면 덮어쓰기 한다
    g20MHzSetFilePath = dst20
    print(f'  Create 20 MHz SetFile done : ', g20MHzSetFilePath)

    time.sleep(0.5)
    print(f' ')


def ProcLoadSetFile100mhz():
    msg_print(f'모듈에 맞는 새로 생성한 셋파일 경로 불러오기 **********************************************************')
    path = g100MHzSetFilePath
    print("  100Mhz SetFile path: ", path)

    # 100 MHz 셋파일 로딩 **********************************************************************************************
    print(f' ')
    msg_print(f'100 MHz 셋파일 로딩 ***********************************************************************************')
    if os.path.isfile(path):
        msg_print("Success, it find a file")
    else:
        msg_print("Failure, it find not a file ")
        sys.exit('Error!!!!')

    if simmian.LoadSetfile(path):
        msg_print(f'Success , it can load the setfile')
    else:
        msg_print(f'Failure. it can not load the setfile')
        sys.exit('Error!!!!')
    print(f' ')


def ProcLoadSetFile20mhz():
    msg_print(f'모듈에 맞는 새로 생성한 셋파일 경로 불러오기 **********************************************************')

    path = g20MHzSetFilePath
    print("  20Mhz SetFile path: ", path)

    print(f' ')
    msg_print(f'20 MHz 셋파일 로딩 ************************************************************************************')
    if os.path.isfile(path):
        msg_print("Success, it find a file")
    else:
        msg_print("Failure, it find not a file ")
        sys.exit('Error!!!!')

    if simmian.LoadSetfile(path):
        msg_print(f'Success , it can load the setfile')
    else:
        msg_print(f'Success , it can not load the setfile')
    print(f' ')


def ProcFindGlobalOffset(freq, depthCTValue, countIndex):
    # depthCTValue 가 LSL-USL을 만족하는지 FindBoardoffset( ) 에서 검사한다.
    _result = FindBoardoffset(freq, depthCTValue, countIndex)  # (freq)(int)주파수, (depthCTValue)(float)측정값

    if _result == True:  # True -> 옵셋을 찾아야한다. , False -> 옵셋을 찾지 않아도 된다.
        msg_print(f'global offset 보정이 필요하다. ')
        msg_print(f'Find Offset () 프로세스로 넘어간다.')
        find_offset(freq, depthCTValue, countIndex)  # (freq)(int)동작주파수 , (value)(float)측정값

    else:
        msg_print(f'global offset 보정이 필요없다.')
        #스펙을 만족하지만, fatcory 영역을 쓸때에 리포트의 global offset 값을 활용한다.
        global gBoard_offset_f1, gBoard_offset_f2

        if freq == 100:
            oldOffsetDEC = simmian.ReadI2C(gDeviceID, gStartAddress_f1, 2)
            gBoard_offset_f1 = hex(oldOffsetDEC)
        elif freq == 20:
            oldOffsetDEC = simmian.ReadI2C(gDeviceID, gStartAddress_f2, 2)
            gBoard_offset_f2 = hex(oldOffsetDEC)
    print(f' ')


def ProcSaveRaw100mhz50cm():
    # RAW 저장 100MHz (위치 : 500 mm ) *********************************************************************************

    msg_print(f'RAW 저장 100MHz (위치 : 500 mm ) **********************************************************************')

    msg_print("Capture Start : 100 MHz at 500 mm")

    time.sleep(1)

    savePath = g100mhz50cm
    gOutputFilePrefix = f'image100mhz'
    validation(gOutputFilePrefix, savePath, 100, 1, gCaptureCnt, 500)
    # (gOutputFilePrefix)파일이름, (savePath)저장경로, (freq)구동, (mode)옵셋찾기? 측정구간, (count)저장횟수, (pos)측정위치

    msg_print("Capture Done : 100 MHz at 500 mm")

    print(f' ')


def ProcSaveRaw100mhz30cm():
    msg_print(
        f'RAW 저장 100 MHz (위치 : 300 mm ) ********************************************************************************')
    msg_print("Capture Start : 100 MHz at 300 mm")

    time.sleep(1)

    savePath = g100mhz30cm
    gOutputFilePrefix = f'image100mhz'
    validation(gOutputFilePrefix, savePath, 100, 1, gCaptureCnt, 300)

    msg_print("Capture Done : 100 MHz at 300 mm")

    print(f' ')


def ProcSaveRaw20mhz50cm():
    msg_print(f'RAW 저장 20 MHz (위치 : 500 mm ) **********************************************************************')

    msg_print("Capture Start : 20 MHz at 500 mm")

    time.sleep(1)

    savePath = g20mhz50cm
    gOutputFilePrefix = f'image20mhz'
    validation(gOutputFilePrefix, savePath, 20, 2, gCaptureCnt, 500)

    msg_print("Capture Done : 20 MHz at 500 mm")

    print(f' ')


def ProcSaveRaw20mhz30cm():
    msg_print(f'RAW 저장 20 MHz (위치 : 300 mm ) **********************************************************************')

    msg_print("Capture Start : 20 MHz at 300 mm")

    time.sleep(1)

    savePath = g20mhz30cm
    gOutputFilePrefix = f'image20mhz'
    validation(gOutputFilePrefix, savePath, 20, 2, gCaptureCnt, 300)

    msg_print("Capture Done : 20 MHz at 300 mm")

    print(f' ')


def ProcCreateReport():
    create_report(gSaveModulePath, gResult, gCaptureCnt)


def ProcReValidationOffset(freq, pos):
    re = simmian.Reset()
    if re == False:
        msg_print('심미안 리셋을 실패하였습니다.')

    if freq == 100:
        # 셋파일 (100 MHz ) 만들기 *************************************************************************************
        ProcCreateSetFile100()
        # 모터 제어 : 로딩 위치 이동 (500 mm) **************************************************************************
        ProcMoveTo500()
        # 심미안 플레이 ****************************************************************************************************
        # ProcSimmianPlay()
        # 100 MHz 셋파일 로딩 ******************************************************************************************
        ProcLoadSetFile100mhz()
        # RAW 저장 100MHz (위치 : 500 mm ) *****************************************************************************
        ProcSaveRaw100mhz50cm()
    elif freq == 20:
        # 셋파일 (20 MHz ) 만들기 **************************************************************************************
        ProcCreateSetFile20()
        # 모터 제어 : 로딩 위치 이동 (500 mm) **************************************************************************
        ProcMoveTo500()
        #  20 MHz 셋파일 로딩 ******************************************************************************************
        ProcLoadSetFile20mhz()
        # RAW 저장 20 MHz (위치 : 500 mm ) *****************************************************************************
        ProcSaveRaw20mhz50cm()
    else:
        print(f'')


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
    print(f'입력 값 -> ', set_board_offset_f1, hex(set_board_offset_f1))

    set_board_offset_f1_ = TestReversed(set_board_offset_f1)
    print(f'리틀엔디안 ->', set_board_offset_f1_)

    simmian.WriteI2C(0xA0, "0x0108", set_board_offset_f1_)
    time.sleep(1)

    ResetSimmian()
    re_read_board_offset_f1 = simmian.ReadI2C(gDeviceID, gStartAddress_f1, 2)
    print(f'리틀엔디안 , E2P 값 : ', set_board_offset_f1_, hex(re_read_board_offset_f1))

    print(f'################################################################################')

    set_board_offset_f2 = 32768  # 계산한 옵셋이 0xabcd 이라면, WriteI2C 에 입력되는 값은 0xcdab 로 넣어야한다.
    print(f'입력 값 -> ', set_board_offset_f2, hex(set_board_offset_f2))

    set_board_offset_f2_ = TestReversed(set_board_offset_f2)
    print(f'리틀엔디안 ->', set_board_offset_f2_)

    simmian.WriteI2C(0xA0, "0x0108", set_board_offset_f2_)
    time.sleep(1)

    ResetSimmian()
    re_read_board_offset_f2 = simmian.ReadI2C(gDeviceID, gStartAddress_f1, 2)
    print(f'리틀엔디안 , E2P 값 : ', set_board_offset_f2_, hex(re_read_board_offset_f2))

    sys.exit()




if __name__ == "__main__":
    # 심미안 플레이 ****************************************************************************************************
    ProcSimmianPlay()
    #TestWriteI2C()


    # 모듈 번호 입력 ***************************************************************************************************
    ProcCreateModuleFolder()

    # 모터 제어 : 로딩 위치 이동 (500 mm) ******************************************************************************
    _init_motor()
    ProcMoveTo500()

    # 셋파일 (100 MHz / 20 MHz ) 만들기 ********************************************************************************
    ProcCreateSetFile100()
    ProcCreateSetFile20()

    # 100 MHz 셋파일 로딩 **********************************************************************************************
    ProcLoadSetFile100mhz()

    # RAW 저장 100MHz (위치 : 500 mm ) *********************************************************************************
    ProcSaveRaw100mhz50cm()

    # 모터 제어 : 위치 이동 300 mm *************************************************************************************
    ProcMoveto300()

    # RAW 저장 100 MHz (위치 : 300 mm ) ********************************************************************************
    ProcSaveRaw100mhz30cm()

    # 모터 제어 : 위치 이동 500 mm *************************************************************************************
    ProcMoveTo500()

    # 심미안 리셋 ******************************************************************************************************
    ProcSimmianReset()

    #  20 MHz 셋파일 로딩 ***********************************************************************************************
    ProcLoadSetFile20mhz()

    # RAW 저장 20 MHz (위치 : 500 mm ) *********************************************************************************
    ProcSaveRaw20mhz50cm()

    # 모터 제어 : 위치 이동 300 mm *************************************************************************************
    ProcMoveto300()

    # RAW 저장 20 MHz (위치 : 300 mm ) *********************************************************************************
    ProcSaveRaw20mhz30cm()

    # 심미안 종료 ******************************************************************************************************
    ProcSimmianStop()

    # 모터 닫기 ********************************************************************************************************
    ProcMotorClose()

    # 결과 출력 ********************************************************************************************************
    ProcCreateReport()

    msg_print("done. please replace with next module")

    sys.exit()
