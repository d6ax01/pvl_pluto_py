import os
from ctypes import *
# import python_analyzer_api
import python_simmian_api
# import minimalmodbus
# import serial
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
gSavePath	= r"E:\delete\lsi\Program\LsiLeo\python\save"
gOutputDirPrefix = ""
gCaptureCnt = 100
gMotorSettleTimeSec = 3
#####################################################

setfilePath = r'E:\delete\lsi\Program\LsiLeo\python\set'
setfileName = 'RQ4_EVT05_S24804_A05_MIPI_836M_VGA_D_60fps_R60FPS_0p4ms_DUAL_PH_FLOOD_.set'
binfileName = 'RQ4_EVT0_1.RegsMap.bin'

gCurrPath = os.getcwd()
simmian = python_simmian_api.Simmian()	



def InitSimmian() :
	re = simmian.Play()
	if re : 
		print("Connect")
	else : 
		print("Error")


def DoCapture( prefix, path ) :

	simmian.SequentialCapture(prefix, path, gCaptureCnt)
	print("Done")

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

def SetRegisterPD(register):
    # 000: Open, 001: 0.5kOhm, 010: 1.0kOhm, 011: 1.5kOhm
    # 100: 3.0kOhm, others : Open
    register_code = register << 4
    WriteCmd(0x20, 0x2000CF30, 0x0001) # number of write bytes
    WriteCmd(0x20, 0x2000CF32, 0x000E) # register address of VCSEL Driver
    WriteCmd(0x20, 0x2000CF34, register_code) # data for 0x08
    WriteCmd(0x20, 0x2000CF36, 0x00FF) # Delay command
    WriteCmd(0x20, 0x2000CF38, 0x000F) # Data for Delay, 13.3us
    WriteCmd(0x20, 0x2000CF3A, 0x0000) # Terminates command array
    WriteCmd(0x20, 0x2000CF70, 0x0001) # data at end address
    print("Setting done: ", hex(register_code), " code")

def SetVcselCurrent(current_mA):
	current_code = int(current_mA/12) # val = mA / 12
	WriteCmd(0x20, 0x2000CF30, 0x0001) # number of write bytes
	WriteCmd(0x20, 0x2000CF32, 0x0008) # register address of VCSEL Driver
	WriteCmd(0x20, 0x2000CF34, current_code) # data for 0x08
	WriteCmd(0x20, 0x2000CF36, 0x00FF) # Delay command
	WriteCmd(0x20, 0x2000CF38, 0x000F) # Data for Delay, 13.3us
	WriteCmd(0x20, 0x2000CF3A, 0x0000) # Terminates command array
	WriteCmd(0x20, 0x2000CF70, 0x0001) # data at end address
	print("Setting done: ", current_mA, "mA")

def ReadPdValue():
	WriteCmd(0x20, 0x2000CF9A, 0x0001)  # read operation_per_frame
	WriteCmd(0x20, 0x2000CF72, 0x0023)  # CHECK_APC_IMOD[9:8], PD value
	WriteCmd(0x20, 0x2000CF74, 0xFFFF)  # termination code
	WriteCmd(0x20, 0x2000CF9E, 0x0001)  #
	CHECK_APC_IMOD_B9_B8 = ReadCmd(0x20, 0x2000CF86, 2) # Read two bytes. (Return value, Use 2nd value)
	CHECK_APC_IMOD_B9_B8 = (CHECK_APC_IMOD_B9_B8 & 0xFF)

	WriteCmd(0x20, 0x2000CF9A, 0x0001)  # read operation_per_frame
	WriteCmd(0x20, 0x2000CF72, 0x0026)  # CHECK_APC_IMOD[7:0], PD value
	WriteCmd(0x20, 0x2000CF74, 0xFFFF)  # termination code
	WriteCmd(0x20, 0x2000CF9E, 0x0001)  #
	CHECK_APC_IMOD_B7_B0 = ReadCmd(0x20, 0x2000CF86, 2) # Read two bytes. (Return value, Use 2nd value)
	CHECK_APC_IMOD_B7_B0 = (CHECK_APC_IMOD_B7_B0 & 0xFF)

	pd_val = (((CHECK_APC_IMOD_B9_B8 & 0x20) >> 5) * (2**9)) + (((CHECK_APC_IMOD_B9_B8 & 0x10) >> 4) * (2**8)) + (CHECK_APC_IMOD_B7_B0)
	print("PD value[7:0] = ", hex(CHECK_APC_IMOD_B7_B0))
	print("PD value[9:8] = ", hex(CHECK_APC_IMOD_B9_B8 & 0x30))
	return pd_val

if __name__ == "__main__" :

	InitSimmian()
    
    SetRegisterPD(0)  # R_PD = 0b000:Open
    time.sleep(0.100)  # 100ms
    
	SetVcselCurrent(2700) # 1st current: 2700mA
	value = ReadPdValue()
	print("PD val = ", value, "(", hex(value), ")")
	
	SetVcselCurrent(1500) # 1st current: 1500mA
	value = ReadPdValue()
	print("PD val = ", value, "(", hex(value), ")")

	simmian.Disconnect()

	sys.exit()                 

