import os
import main
import FactoryCode_verify_TemperatureVariation as fc_vt
import time  # sleep 함수 사용
import datetime
import python_simmian_api
import sys
import threading
from pyqt_ui.log_ui import *
from pyqt_ui import log_controll

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

    time.sleep(1)


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

def init_setFile():
    # 셋파일 (100 MHz / 20 MHz ) 만들기 *******************************************************************************
    # ProcCreateSetFile100()
    time.sleep(0.010)
    fc_vt.ProcCreateSetFile20()
    time.sleep(1)
    #time.sleep(0.010)

    # 심미안 리셋 *****************************************************************************************************
    fc_vt.ProcSimmianReset()

    # 셋파일 로딩 **********************************************************************************************
    # ProcLoadSetFile100mhz()
    # time.sleep(0.1)

    fc_vt.ProcLoadSetFile20mhz()
    time.sleep(0.1)

    def get_temp_data(MHz,CM):
        folder_name = (f'{MHz}M_{int(CM / 10)}cm')
        savePath = f'%s\%s\%s' % (fc_vt.gRootSavePath, fc_vt.gget_module_number, folder_name)
        # g100mhz50cm = f'%s\%s\%s' % (fc_vt.gRootSavePath, fc_vt.get_module_number, f'100M_50cm')
        save_str = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S-')
        for i in range(3):
            copyfile(f'{savePath}\image{MHz}mhz_{i}_ALL0_f1_nshfl.raw',
                     f'{savePath}\{save_str}image{MHz}mhz_{i}_ALL0_f1_nshfl.raw')


def image_save(MHz,Cm):
    folder_name = (f'{MHz}M_{int(Cm / 10)}cm')
    savePath = f'%s\%s\%s' % (fc_vt.gRootSavePath, fc_vt.gget_module_number, folder_name)
    # g100mhz50cm = f'%s\%s\%s' % (fc_vt.gRootSavePath, fc_vt.get_module_number, f'100M_50cm')
    save_str=datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S-')
    for i in range(3):
        copyfile(f'{savePath}\image{MHz}mhz_{i}_ALL0_f1_nshfl.raw',f'{savePath}\{save_str}image{MHz}mhz_{i}_ALL0_f1_nshfl.raw')


def run_ui(controller):
    app = QApplication(sys.argv)
    logger_ui = LoggerUI(controller)
    controller.generate_log_signal.connect(logger_ui.generate_log)
    controller.change_large_text_signal.connect(logger_ui.change_large_text)
    logger_ui.show()
    app.exec_()




if __name__ == "__main2__" :
    logger_controller = log_controll.LoggerController()
    ui_thread = threading.Thread(target=run_ui, args=(logger_controller,))
    ui_thread.start()

    path = os.path.dirname(os.path.abspath(__file__))
    print(path)

if __name__ == '__main__':
    logger_controller = log_controll.LoggerController()
    ui_thread = threading.Thread(target=run_ui, args=(logger_controller,))
    ui_thread.start()



    sim_state=False
    recovery_count = 0
    while sim_state is False:
        recovery_count+=1
        #add log
        logger_controller.generate_log(f"recovery_count : {recovery_count}", LogState.Recovery)
        logger_controller.change_large_text("SETTING","cadetblue")

        sim_state=RecoverySim()



    # 모듈 번호 입력 ***************************************************************************************************
    fc_vt.ProcCreateModuleFolder()
    start_time=datetime.datetime.now()
    next_frame_time=0
    test_during_time=60*60*200
    image_save_time=0
    #init_setFile()
    total_data= {'total_count':0, 'total_val':0,'avg':0,'min':0,'max':0}#count, totalval,avg,min,max
    #total_data=[0,0,0,0,0]#count, totalval,avg,min,max
    recovery_count=0
    cap_count=0
    total_second=0
    frame_item=list()

    mi_path = fc_vt.get_path()
    mi_obj= mi.MeasurementItems(mi_path)
    next_frame_time=start_time
    while total_second < test_during_time:
        #check 10s
        if (next_frame_time - datetime.datetime.now()).total_seconds()> 0:
            time.sleep(0.05)
            continue
        next_frame_time= next_frame_time+datetime.timedelta(seconds=10)
        result_saver = list()

        total_second = (datetime.datetime.now() - start_time).total_seconds()
        logger_controller.change_large_text("RUNNING", "lightgreen")
        time.sleep(1)  # 성능평가를 위한 뎁스 영상 취득 전에 워밍업 3초
        # Measurement(100, 500, motion_dist500)  # 300 mm 에서 평가
        data_get_bool = ProcSaveRaw(1, 20, 500,result_saver)  #  500 mm 에서 평가

        if data_get_bool:
            # add log
            cap_count+=1
            logger_controller.generate_log(f"Data_get : {cap_count}", LogState.GetData)

            if total_second/3600>image_save_time:
                image_save_time+=1
                image_save(20, 500)
            recovery_count = 0

            #get easurement item from capture data
            frame_item = [0, 0, 0, 0, 0]
            frame_num = len(result_saver)
            for i in range(frame_num):
                for j in range(4):  # j=  0 : depth avg , 1 : intensity avg , 2 : tx temp , 3 : rx temp
                    frame_item[j] += result_saver[i][j]
            for j in range(4):
                frame_item[j] /= frame_num
            frame_item[4] = result_saver[0][4]  # input first frame time stamp

            mi_obj.input_measurement_item(frame_item)


        else:
            sim_state=False
            logger_controller.change_large_text("RECOVERY", "lightcoral")
            while sim_state is False and recovery_count<20:
                recovery_count +=1
                # add log
                logger_controller.generate_log(f"recovery_count : {recovery_count}", LogState.Recovery)
                sim_state = RecoverySim()
            if recovery_count==20:
                # add log
                logger_controller.generate_log(f"recovery_count : {recovery_count}", LogState.Fail)
                logger_controller.change_large_text("FAIL", "red")
                #로그에 init count max를 입력하고 프로그램 종료
                break
            else:
                init_setFile()

        fc_vt.ProcCreateReport(1)  # 0 -> find global offset , 1 -> only measurement



    # RAW 저장 (위치 : 500 mm ) *********************************************************************************
    # while time.time()<start_time+test_during_time:
    #     try:
    #         time.sleep(1)  # 성능평가를 위한 뎁스 영상 취득 전에 워밍업 3초
    #         # Measurement(100, 500, motion_dist500)  # 300 mm 에서 평가
    #         data_get_bool=ProcSaveRaw(1, 20, 500)  # 500 mm 에서 평가
    #         if data_get_bool:
    #             fc_vt.ProcCreateReport(1)  # 0 -> find global offset , 1 -> only measurement
    #             init_count = 0
    #         else:
    #
    #             raise Exception
    #     except:
    #         init_count+=1
    #         init()
    #         if init_count==10:
    #             break

    # 심미안 리셋 ******************************************************************************************************
    fc_vt.msg_print(f'심미안을 리셋합니다.')
    fc_vt.ProcSimmianReset()

    # 심미안 종료 ******************************************************************************************************
    fc_vt.msg_print(f'심미안을 종료합니다.')
    fc_vt.ProcSimmianStop()

    # 모터 닫기 ********************************************************************************************************
    fc_vt.msg_print(f'모터와 통신을 종료합니다.')
    fc_vt.ProcMotorClose()
    fc_vt.msg_print("done. please replace with next module")
    fc_vt.sys.exit()



