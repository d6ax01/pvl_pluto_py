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

def RecoverySim():
    simmian = python_simmian_api.Simmian()
    test = simmian.Stop()
    simmian.Disconnect()

    # todo 심미안SW 다시 실행하기
    main.kill_nxsimmian()  # 일단 끄고,
    time.sleep(1)
    main.kill_nxsimmian()  # 일단 끄고,
    time.sleep(1)
    main.runNxsimmian()
    #time.sleep(4)
    #대략 키는데 3초? 정도. 한 5초 sleep 넣으면 될거같음
    sim_state=fc_vt.init_()
    fc_vt.msg_print(f'Sim State : {sim_state}')
    return sim_state


def get_temp(filePath):
    fid = open(filePath, "rb")

    Img = np.fromfile(fid,  dtype='>B')
    fid.close()

    data_paresr=embedded_data_parser.EmbeddedDataParser('63D','depth')
    my_data=data_paresr.parse_embedded_data(Img)
    print(my_data)
    print("TEST GET TEMP ")




def ProcSaveRaw(mode,MHz,Cm,result_saver):
    # RAW 저장 100MHz (위치 : 500 mm ) *********************************************************************************
    folder_name=(f'{MHz}M_{int(Cm/10)}cm')
    savePath = f'%s\%s\%s' % (fc_vt.gRootSavePath, fc_vt.gget_module_number, folder_name)
    #g100mhz50cm = f'%s\%s\%s' % (fc_vt.gRootSavePath, fc_vt.get_module_number, f'100M_50cm')


    fc_vt.msg_print(f'RAW 저장 {MHz}MHz (위치 : {10*Cm} mm ) **********************************************************************')

    fc_vt.msg_print(f'Capture Start : {MHz} MHz at {10*Cm} mm')

    #time.sleep(1)


    gOutputFilePrefix = (f'image{MHz}mhz')

    filePath = r'{0}\{1}_temp.raw'.format(savePath, gOutputFilePrefix)  # ++_ALL0_f1_nshfl_VC(2)_DT(Raw8).raw
    result = fc_vt.simmian.Capture(filePath, captureCount=1)
    if result:
        filePath = r'{0}\{1}_temp_ALL0_f1_nshfl.raw'.format(savePath, gOutputFilePrefix)  # ++_ALL0_f1_nshfl_VC(2)_DT(Raw8).raw
        get_temp(filePath)
    CaptureResult = fc_vt.validation(gOutputFilePrefix, savePath, MHz, mode, fc_vt.gCaptureCnt, 10*Cm,result_saver)
    # (gOutputFilePrefix)파일이름,   (savePath)저장경로, (freq)구동, (mode)옵셋찾기? 측정구간, (count)저장횟수, (pos)측정위치
    fc_vt.msg_print(f'Capture Done : {MHz} MHz at {10*Cm} mm')
    # if CaptureResult:
    #     filePath = r'{0}\{1}_{2}_ALL0_f1_nshfl.raw'.format(savePath, gOutputFilePrefix, 0)
    #     fid = open(filePath, "rb")
    #
    #     Img = np.fromfile(fid,dtype='int16', sep="")
    #     fid.close()
    #
    #
    #     data_paresr=embedded_data_parser.EmbeddedDataParser()
    #     data_paresr.parse_embedded_data(Img)
    #     print("TEST GET TEMP ")

    print(f' ')
    return CaptureResult

def init_setFile(MHz):
    # 셋파일 (100 MHz / 20 MHz ) 만들기 *******************************************************************************
    # ProcCreateSetFile100()
    time.sleep(0.010)
    if MHz==100:
        fc_vt.ProcCreateSetFile100()
    elif MHz==20:
        fc_vt.ProcCreateSetFile20()
    time.sleep(1)
    #time.sleep(0.010)

    # 심미안 리셋 *****************************************************************************************************
    fc_vt.ProcSimmianReset()

    # 셋파일 로딩 **********************************************************************************************
    if MHz==100:
        fc_vt.ProcLoadSetFile100mhz()
    elif MHz==20:
        fc_vt.ProcLoadSetFile20mhz()
    time.sleep(0.1)

    def get_temp_data(MHz,CM):
        folder_name = (f'{MHz}M_{int(CM / 10)}cm')
        savePath = f'%s\%s\%s' % (fc_vt.gRootSavePath, fc_vt.gget_module_number, folder_name)
        # g100mhz50cm = f'%s\%s\%s' % (fc_vt.gRootSavePath, fc_vt.get_module_number, f'100M_50cm')
        save_str = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S-')
        for i in range(fc_vt.gCaptureCnt):
            copyfile(f'{savePath}\image{MHz}mhz_{i}_ALL0_f1_nshfl.raw',
                     f'{savePath}\{save_str}image{MHz}mhz_{i}_ALL0_f1_nshfl.raw')


def image_save(MHz,Cm):
    folder_name = (f'{MHz}M_{int(Cm / 10)}cm')
    savePath = f'%s\%s\%s' % (fc_vt.gRootSavePath, fc_vt.gget_module_number, folder_name)
    # g100mhz50cm = f'%s\%s\%s' % (fc_vt.gRootSavePath, fc_vt.get_module_number, f'100M_50cm')
    save_str=datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S-')
    for i in range(fc_vt.gCaptureCnt):
        copyfile(f'{savePath}\image{MHz}mhz_{i}_ALL0_f1_nshfl.raw',f'{savePath}\{save_str}image{MHz}mhz_{i}_ALL0_f1_nshfl.raw')
