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
import pvl_func.pvl_func as pvl_f

def run_ui(controller):
    app = QApplication(sys.argv)
    logger_ui = LoggerUI(controller)
    controller.generate_log_signal.connect(logger_ui.generate_log)
    controller.change_large_text_signal.connect(logger_ui.change_large_text)
    logger_ui.show()
    app.exec_()




if __name__ == "__main__" :
    logger_controller = log_controll.LoggerController()
    ui_thread = threading.Thread(target=run_ui, args=(logger_controller,))
    ui_thread.start()

if __name__ == '__main2__':
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

        sim_state=pvl_f.RecoverySim()



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
        data_get_bool = pvl_f.ProcSaveRaw(1, 20, 500,result_saver)  #  500 mm 에서 평가

        if data_get_bool:
            # add log
            cap_count+=1
            logger_controller.generate_log(f"Data_get : {cap_count}", LogState.GetData)

            if total_second/3600>image_save_time:
                image_save_time+=1
                pvl_f.image_save(20, 500)
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
                sim_state = pvl_f.RecoverySim()
            if recovery_count==20:
                # add log
                logger_controller.generate_log(f"recovery_count : {recovery_count}", LogState.Fail)
                logger_controller.change_large_text("FAIL", "red")
                #로그에 init count max를 입력하고 프로그램 종료
                break
            else:
                pvl_f.init_setFile()

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



