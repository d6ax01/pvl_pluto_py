#import os
#from ctypes import *
# import python_analyzer_api
#import minimalmodbus
#import serial
import python_simmian_api
import time
import sys
import os.path
import subprocess
import shutil


# Calibration
#####################################################
# reference motor control param
# gCalRefMotorControlParam = 0
# real distance (mm)
# gCalRealDistanc = 120
#####################################################

gRootPath = f'%s\%s' % (f'D:\LSI_VST63D', f'4_Validation')

# Configuration about Image Capture
#####################################################
gOutputFilePrefix = f'Image'
gRootSavePath	= f'%s\%s' % (f'D:\LSI_VST63D', f'4_Validation\save')
gOutputDirPrefix = f'image'
gCaptureCnt = 10
gMotorSettleTimeSec = 3
#####################################################

# Configuration about Set File for Validation
#####################################################
gRootSetFilePath = f'%s\%s' % (f'D:\LSI_VST63D', f'4_Validation\save')
g100MHzSetFileName = f'100M_1109.set'
g20MHzSetFileName = f'20M_1109.set'
g100MHzSetFilePath = f''
g20MHzSetFilePath = f''
g20mhz30cm = f''
g20mhz50cm = f''
g100mhz30cm = f''
g100mhz50cm = f''
gDepth_U16 = f'DEPTH_U16'
gIntensity = f'INTENSITY'
gBinFileName = f'_ToF_cal_100MHz.bin'

#####################################################

# Configuration about Create Set File
#####################################################
gRootPathOriginalSetFile = f'%s\%s' % (f'D:\LSI_VST63D' , f'4_Validation\create_setfile')
gBatchPath100MHz = f'%s\%s' % (gRootPathOriginalSetFile, f'1.bat')
gBatchPath20MHz = f'%s\%s' % (gRootPathOriginalSetFile, f'2.bat')

#####################################################


gCurrPath = os.getcwd()
simmian = python_simmian_api.Simmian()


def InitSimmian() :
	re = simmian.Play()
	if re :
		print(f'Success, it can connect.')
	else :
		print(f'Failure, it can not connect.')



def StopSimmian() :
	re = simmian.Stop()
	if re :
		print(f'Success, it can stop.')
	else :
		print(f'Failure, it can not stop.')



def ResetSimmian() :
	re = simmian.Reset()
	if re :
		print(f'Success, it can reset.')
	else :
		print(f'Failure, it can not reset.')



def DisconnetSimmian() :
    re = simmian.Disconnect()
    if re :
        print(f'Success, it can disconnect.')
    else :
        print(f'Failure, it can not disconnect. ')



def DoCapture( prefix, path ) :
    simmian.SequentialCapture(prefix, path, gCaptureCnt) #시퀀셜캡처는 RAW저장 시간이 매우 느리다.
    print("Done")



def DoSingleCapture( prefix, path ) :
    #DepthfolderPath = f'%s\%s' % (path, f'DEPTH_U16')
    #IntensityfolderPath = f'%s\%s' % (path, f'INTENSITY')
    #create_folder(DepthfolderPath)
    #create_folder(IntensityfolderPath)
    filePath = r"%s\%s_.raw" % (path, prefix) #filePath = r"{0}\\{1}_{2}.raw".format(path, prefix, degree)
    print('save path : ', filePath)
    result = simmian.Capture(filePath, captureCount = 1)



def create_folder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print('Error: Creating directory. {0}'.format(directory))



if __name__ == "__main__" :

    # 모듈 번호 입력 ***************************************************************************************************
    print(f'모듈 번호 입력 ***************************************************************************************************')
    print('Please enter your module number : ')
    getModuleNumber = input() # (관리자모드)CMD 에서 키보드를 이용해서 모듈번호를 입력한다.


    if getModuleNumber == f'':
        print(f'Please enter your module number : ')
        getModuleNumber = input()
    else:
        print("Module Number : ", getModuleNumber)
        saveModulePath = f'%s\%s' % (gRootSavePath, getModuleNumber)                #모듈의 저장 경로
        g20mhz30cm = f'%s\%s\%s' % (gRootSavePath, getModuleNumber, f'20M_30cm')    #저장 경로 -> 20 MHz로 300 mm
        g20mhz50cm = f'%s\%s\%s' % (gRootSavePath, getModuleNumber, f'20M_50cm')    #저장 경로 -> 20 MHz로 500 mm
        g100mhz30cm = f'%s\%s\%s' % (gRootSavePath, getModuleNumber, f'100M_30cm')  #저장 경로 -> 100 MHz로 300 mm
        g100mhz50cm = f'%s\%s\%s' % (gRootSavePath, getModuleNumber, f'100M_50cm')  #저장 경로 -> 100 MHz로 500 mm

        # 폴더 생성
        create_folder(g20mhz30cm)
        create_folder(g20mhz50cm)
        create_folder(g100mhz30cm)
        create_folder(g100mhz50cm)
        print(f'%s -> %s' % (getModuleNumber, f'Folder creation with the name is complete.'))

    # 폴더 이름을 못 받으면 종료
    if getModuleNumber == f'':
        print(f'Can not folder creation')
        sys.exit('Error!!!!')



    # 모터 제어 : 로딩 위치 이동 (500 mm) ******************************************************************************
    print(f'모터 제어 : 로딩 위치 이동 (500 mm) ******************************************************************************')
    print("Move to Loading Pos : ", 500)
    print("Move to loading position completed")




    # 심미안 플레이 ****************************************************************************************************
    print(f'심미안 플레이 ****************************************************************************************************')
    InitSimmian()

    print(f'Read to board offset f1 : ', simmian.ReadI2C(0x0E, "0x0108", 2))    #board_offset_f1
    print(f'Read to board offset f2 : ', simmian.ReadI2C(0x0E, "0x010A", 2))    #board_offset_f2



    # 셋파일 만들기 ****************************************************************************************************
    print(f'셋파일 만들기 ****************************************************************************************************')
    # 100 MHz 만들기 단계
    cmd = [gBatchPath100MHz] # CMD는 반드시 관리자 권한을 실행해야한다. cd /d d:\LSI_VST63D\4_Validation\create_setfile
    #print(cmd)
    newSetFile_100M = subprocess.run(cmd, shell=True)

    src100 = f'%s\%s' % (gRootPath, g100MHzSetFileName)
    dst100 = f'%s\%s' % (saveModulePath, g100MHzSetFileName)
    shutil.move(src100, dst100) #전체경로 주소로 해줘야 이미 존재하는 파일명이면 덮어쓰기 한다
    g100MHzSetFilePath = dst100
    print(f'Create 100 MHz SetFile done : ', newSetFile_100M)

    time.sleep(1)



    # 20 MHz 만들기 단계
    cmd = [gBatchPath20MHz]  # CMD는 반드시 관리자 권한을 실행해야한다. cd /d d:\LSI_VST63D\4_Validation\create_setfile
    #print(cmd)
    newSetFile_20M = subprocess.run(cmd, shell=True)

    src20 = f'%s\%s' % (gRootPath, g20MHzSetFileName)
    dst20 = f'%s\%s' % (saveModulePath, g20MHzSetFileName)
    shutil.move(src20, dst20) #전체경로 주소로 해줘야 이미 존재하는 파일명이면 덮어쓰기 한다
    g20MHzSetFilePath =  dst20
    print(f'Create 20 MHz SetFile done : ', newSetFile_20M)

    time.sleep(1)



    # 모듈에 맞는 새로 생성한 셋파일 경로 불러오기 *********************************************************************
    print(f'모듈에 맞는 새로 생성한 셋파일 경로 불러오기 *********************************************************************')
    SetFile_f1 = g100MHzSetFilePath
    print("100Mhz SetFile path: ", SetFile_f1)

    SetFile_f2 = g20MHzSetFilePath
    print("20Mhz SetFile path: ", SetFile_f2)




    # 100 MHz 셋파일 로딩 **********************************************************************************************
    print(f'100 MHz 셋파일 로딩 **********************************************************************************************')
    if os.path.isfile(SetFile_f1):
        print("Success, it has a file")
    else:
        print("Failure, it has not a file ")
        sys.exit('Error!!!!')


    #response_set = simmian.LoadSetfile(SetFile_f1) # 셋파일 로드
    if simmian.LoadSetfile(SetFile_f1):
        print(f'Success , it can load the setfile')
    else :
        print(f'Failure. it can not load the setfile')
        sys.exit('Error!!!!')



    # 100 MHz at 500 mm 에서 global offset 찾기 ************************************************************************
    print(f'100 MHz at 500 mm 에서 global offset 찾기 ************************************************************************')
    print(f'Will......find global offset')



    # RAW 저장 100MHz (위치 : 500 mm ) *********************************************************************************
    #g20mhz30cm     #g20mhz50cm     #g100mhz30cm     #g100mhz50cm
    # 중요 MCLK 19.2 MHz 영상을 촬상해야 한다. 어떻게 해야하는가?

    print(f'RAW 저장 100MHz (위치 : 500 mm ) *********************************************************************************')

    print("Capture Start : 100 MHz at 500 mm")

    time.sleep(1)
    savePath = g100mhz50cm
    gOutputFilePrefix = f'image100mhz'
    DoSingleCapture(gOutputFilePrefix, savePath)

    print ("Capture Done : 100 MHz at 500 mm")



    # 심미안 스탑 ******************************************************************************************************
    print(f'심미안 스탑 ******************************************************************************************************')
    StopSimmian()



    # 심미안 리셋 ******************************************************************************************************
    print(f'심미안 리셋 ******************************************************************************************************')
    InitSimmian()#ResetSimmian()



    #  20 MHz 셋파일 로딩 ***********************************************************************************************
    print(f'20 MHz 셋파일 로딩 ***********************************************************************************************')
    if os.path.isfile(SetFile_f2):
        print("Success, it has a file")
    else:
        print("Failure, it has not a file ")
        sys.exit('Error!!!!')

    #response_set = simmian.LoadSetfile(SetFile_f2) # 셋파일 로드
    if simmian.LoadSetfile(SetFile_f2):
        print(f'Success , it can load the setfile')
    else :
        print(f'Success , it can not load the setfile')



    # 20 MHz at 500 mm 에서 global offset 찾기 ************************************************************************
    print(f'100 MHz at 500 mm 에서 global offset 찾기 ************************************************************************')
    print(f'Will......find global offset')



    # RAW 저장 20 MHz (위치 : 500 mm ) *********************************************************************************
    print(f'RAW 저장 20 MHz (위치 : 500 mm ) *********************************************************************************')

    print("Capture Start : 20 MHz at 500 mm")

    time.sleep(1)
    savePath = g20mhz50cm
    gOutputFilePrefix = f'image20mhz'
    DoSingleCapture(gOutputFilePrefix, savePath)

    print("Capture Done : 20 MHz at 500 mm")



    # 모터 제어 : 위치 이동 300 mm *************************************************************************************
    print(f'모터 제어 : 위치 이동 300 mm *************************************************************************************')
    print("Move to Loading Pos : ", 300)
    print("Move to 300 mm position completed")


    # RAW 저장 20 MHz (위치 : 300 mm ) *********************************************************************************
    print(f'RAW 저장 20 MHz (위치 : 300 mm ) *********************************************************************************')

    print("Capture Start : 20 MHz at 300 mm")

    time.sleep(1)
    savePath = g20mhz30cm
    gOutputFilePrefix = f'image20mhz'
    DoSingleCapture(gOutputFilePrefix, savePath)

    print("Capture Done : 20 MHz at 300 mm")



    # 심미안 스탑 ******************************************************************************************************
    print(f'심미안 스탑 ******************************************************************************************************')
    StopSimmian()



    # 심미안 리셋 ******************************************************************************************************
    print(f'심미안 리셋 ******************************************************************************************************')
    InitSimmian()#ResetSimmian()



    # 100 MHz 셋파일 로딩 **********************************************************************************************
    print(f'100 MHz 셋파일 로딩 **********************************************************************************************')
    if os.path.isfile(SetFile_f1):
        print("Success, it has a file")
    else:
        print("Failure, it has not a file ")
        sys.exit('Error!!!!')

    #response_set = simmian.LoadSetfile(SetFile_f1)  # 셋파일 로드
    if simmian.LoadSetfile(SetFile_f1):
        print(f'Success , it can load the setfile')
    else:
        print(f'Failure. it can not load the setfile')
        sys.exit('Error!!!!')



    # RAW 저장 100 MHz (위치 : 300 mm ) ********************************************************************************
    print(f'RAW 저장 100 MHz (위치 : 300 mm ) ********************************************************************************')
    print("Capture Start : 100 MHz at 300 mm")

    time.sleep(1)
    savePath = g100mhz30cm
    gOutputFilePrefix = f'image100mhz'
    DoSingleCapture(gOutputFilePrefix, savePath)

    print("Capture Done : 100 MHz at 300 mm")


    # 심미안 연결 끊기 *************************************************************************************************
    print(f'심미안 연결 끊기 *************************************************************************************************')
    DisconnetSimmian()#simmian.Disconnect()


    # 모터 제어 : 언로딩 위치 이동 (500 mm) ****************************************************************************
    print(f'모터 제어 : 언로딩 위치 이동 (500 mm) ****************************************************************************')
    print("Move to Unloading Pos : ", 500)
    print("Move to loading position completed")



    sys.exit('done')


