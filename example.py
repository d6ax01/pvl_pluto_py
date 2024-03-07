import os
from ctypes import *
# import python_analyzer_api
import python_simmian_api
import minimalmodbus
import serial
import time
import sys
import os.path

# Calibration
#####################################################
# reference motor control param
gCalRefMotorControlParam = 0	
# real distance (mm)
gCalRealDistanc = 120
#####################################################

# Configuration
#####################################################
gOutputFilePrefix = "Image"
gSavePath	= r"D:\lsi\save"
gOutputDirPrefix = ""
gCaptureCnt = 1
gMotorSettleTimeSec = 3
#####################################################

setfilePath = r'D:\lsi\set'
setfileName = '100M.set'
binfileName = '_ToF_cal_100MHz.bin'

gCurrPath = os.getcwd()
simmian = python_simmian_api.Simmian()	



def InitSimmian() :
	re = simmian.Play()
	if re : 
	    print("Connect")
	else : 
	    print("Error")


def DoCapture( prefix, path ) :

    simmian.SequentialCapture(prefix, path, gCaptureCnt) #시퀀셜캡처는 RAW저장 시간이 매우 느리다.
    print("Done")



if __name__ == "__main__" :

	# binfile = r'%s\%s' % (setfilePath, binfileName)
	# response_bin = simmian.LoadRegisterMap(binfile)

	InitSimmian()
	setfile = r'%s\%s' % (setfilePath, setfileName)
	isExist = os.path.isfile(setfile)

	response_set = simmian.LoadSetfile(setfile)
	print("simmian.LoadSetfile:", response_set);


	savePath = r"{}".format(gSavePath)
	print ("Capture Image Path", savePath)
		
	DoCapture(gOutputFilePrefix, savePath)
	print ("Capture Done")
    
    
	simmian.Disconnect()

	sys.exit()                 

