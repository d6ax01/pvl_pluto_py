from ctypes import *
import os
import platform
from site import getsitepackages
from pathlib import Path

class EziMotor:
    def __init__(self, port):
        self.dllname = 'EziServoMotor.dll'
        if platform.architecture()[0].find('64') != -1:
            self.dllname = 'EziServoMotor.dll'
        self.dllpath = Path(__file__).absolute().parent.joinpath(self.dllname)
        if not os.path.exists(self.dllpath):
            self.dllpath = '{}\\{}'.format(getsitepackages()[1], self.dllname)
        
        self.dll = CDLL(str(self.dllpath))
        result = self.dll.EX_Init(port)
        print('Motor Init : ' , result)
        
    def Close(self):
        result = self.dll.EX_Close()
        print('Motor Close : ' , result)
        return result
        
    def IsConnected(self):
        result = self.dll.EX_IsConnected()
        print('Motor IsConnected : ' , result)
        return result
        
    def IsSlaveConnected(self, axisNo):
        self.dll.EX_IsSlaveConnected.restype = c_bool
        self.dll.EX_IsSlaveConnected.argtypes = [c_int]
        result = self.dll.EX_IsSlaveConnected(axisNo)
        print('Motor IsSlaveConnected : ' , result)
        return result
        
    def SetIOSpace(self, startIn, endIn, startOut, endOut):
        self.dll.EX_SetIOSpace.argtypes = [c_int, c_int, c_int, c_int]
        self.dll.EX_SetIOSpace(startIn, endIn, startOut, endOut)
        print('Motor SetIOSpace : 1')        
    
    def SetAxisCount(self, count):
        self.dll.EX_SetAxisCount(count)
        print('Motor SetAxisCount : 1')
        
    def ServoOn(self, axisNo, bOnOff):
        self.dll.EX_ServoOn.restype = c_bool
        self.dll.EX_ServoOn.argtypes = [c_int, c_bool]
        result = self.dll.EX_ServoOn(axisNo, bOnOff)
        print('Motor ServoOn : ' , result)
        return result
        
    def IsServoOn(self, axisNo):
        self.dll.EX_IsServoOn.restype = c_bool
        self.dll.EX_IsServoOn.argtypes = [c_int]
        result = self.dll.EX_IsServoOn(axisNo)
        print('Motor IsServoOn : ' , result)
        return result
        
    def SetServoParam(self, nAxisNo, dMaxSpeed, dNegLimit, dPosLimit, nOriginType, dSpeedOrigin, nMotorType, dResolution):
        self.dll.EX_SetServoParam.restype = c_bool
        self.dll.EX_SetServoParam.argtypes = [c_int, c_double, c_double, c_double, c_int, c_double, c_int, c_double]
        result = self.dll.EX_SetServoParam(nAxisNo, dMaxSpeed, dNegLimit, dPosLimit, nOriginType, dSpeedOrigin, nMotorType, dResolution)
        print('Motor SetServoParam : ' , result)
        return result
    
    def SetMoveProfile(self, nAxisNo, speed, acceleration, deceleration):
        self.dll.EX_SetMoveProfile.restype = c_bool
        self.dll.EX_SetMoveProfile.argtypes = [c_int, c_double, c_double, c_double]
        result = self.dll.EX_SetMoveProfile(nAxisNo, speed, acceleration, deceleration)
        print('Motor SetMoveProfile : ' , result)
        return result
        
    def AlarmReset(self, nAxisNo):
        self.dll.EX_AlarmReset.restype = c_bool
        self.dll.EX_AlarmReset.argtypes = [c_int]
        result = self.dll.EX_AlarmReset(nAxisNo)        
        print('Motor AlarmReset : ' , result)
        return result

    def IsAlarm(self, nAxisNo):
        self.dll.EX_AlarmReset.restype = c_bool
        self.dll.EX_AlarmReset.argtypes = [c_int]
        result = self.dll.EX_IsAlarm(nAxisNo)        
        print('Motor IsAlarm : ' , result)
        return result
        
    def ServoHomeStart(self, nAxisNo):
        self.dll.EX_ServoHomeStart.restype = c_bool
        self.dll.EX_ServoHomeStart.argtypes = [c_int]
        result = self.dll.EX_ServoHomeStart(nAxisNo)        
        print('Motor ServoHomeStart : ' , result)
        return result
        
    def IsServoHomeSuccess(self, nAxisNo):
        self.dll.EX_IsServoHomeSuccess.restype = c_bool
        self.dll.EX_IsServoHomeSuccess.argtypes = [c_int]
        result = self.dll.EX_IsServoHomeSuccess(nAxisNo)        
        print('Motor IsServoHomeSuccess : ' , result)
        return result
        
    def GetPosition(self, nAxisNo):
        self.dll.EX_GetPosition.restype = c_double
        self.dll.EX_GetPosition.argtypes = [c_int]
        result = self.dll.EX_GetPosition(nAxisNo)        
        print('Motor GetPosition : ' , result)
        return result
        
    def GetServoCmdPos(self, nAxisNo):
        self.dll.EX_GetServoCmdPos.restype = c_double
        self.dll.EX_GetServoCmdPos.argtypes = [c_int]
        result = self.dll.EX_GetServoCmdPos(nAxisNo)        
        print('Motor GetServoCmdPos : ' , result)
        return result
        
    def GetServoActPos(self, nAxisNo):
        self.dll.EX_GetServoActPos.restype = c_double
        self.dll.EX_GetServoActPos.argtypes = [c_int]
        result = self.dll.EX_GetServoActPos(nAxisNo)        
        print('Motor GetServoActPos : ' , result)
        return result
        
    def GetVelocity(self, nAxisNo):
        self.dll.EX_GetVelocity.restype = c_double
        self.dll.EX_GetVelocity.argtypes = [c_int]
        result = self.dll.EX_GetVelocity(nAxisNo)        
        print('Motor GetVelocity : ' , result)
        return result
        
    def IsMotionDone(self, nAxisNo) -> bool:
        self.dll.EX_IsMotionDone.restype = c_bool
        self.dll.EX_IsMotionDone.argtypes = [c_int]
        result = self.dll.EX_IsMotionDone(nAxisNo)        
        return result
        
    def IsMotionDoneEx(self, nAxisNo, margin):
        self.dll.EX_IsMotionDoneEx.restype = c_bool
        self.dll.EX_IsMotionDoneEx.argtypes = [c_int, c_double]
        result = self.dll.EX_IsMotionDoneEx(nAxisNo, margin)        
        print('Motor IsMotionDoneEx : ' , result)
        return result
        
    def IsInPosition(self, nAxisNo, posIs, dbPosition, margin):
        self.dll.EX_IsInPosition.restype = c_bool
        self.dll.EX_IsInPosition.argtypes = [c_int]
        result = self.dll.EX_IsInPosition(nAxisNo)        
        print('Motor IsInPosition : ' , result)
        return result
        
    def IsPositionAt(self, nAxisNo, posIs, dbPosition, margin):
        self.dll.EX_IsPositionAt.restype = c_bool
        self.dll.EX_IsPositionAt.argtypes = [c_int, c_int, c_double, c_double]
        result = self.dll.EX_IsPositionAt(nAxisNo, posIs, dbPosition, margin)        
        print('Motor IsInPosition : ' , result)
        return result
        
    def IsHomeSensor(self, nAxisNo):
        self.dll.EX_IsHomeSensor.restype = c_bool
        self.dll.EX_IsHomeSensor.argtypes = [c_int]
        result = self.dll.EX_IsHomeSensor(nAxisNo)        
        print('Motor IsHomeSensor : ' , result)
        return result
        
    def IsNegLimitSensor(self, nAxisNo):
        self.dll.EX_IsNegLimitSensor.restype = c_bool
        self.dll.EX_IsNegLimitSensor.argtypes = [c_int]
        result = self.dll.EX_IsNegLimitSensor(nAxisNo)        
        print('Motor IsNegLimitSensor : ' , result)
        return result
        
    def IsPosLimitSensor(self, nAxisNo):
        self.dll.EX_IsPosLimitSensor.restype = c_bool
        self.dll.EX_IsPosLimitSensor.argtypes = [c_int]
        result = self.dll.EX_IsPosLimitSensor(nAxisNo)        
        print('Motor IsPosLimitSensor : ' , result)
        return result
        
    def JogMove(self, nAxisNo, dir):
        self.dll.EX_JogMove.restype = c_bool
        self.dll.EX_JogMove.argtypes = [c_int, c_int]
        result = self.dll.EX_JogMove(nAxisNo, dir)        
        print('Motor JogMove : ' , result)
        return result
        
    def JogStop(self, nAxisNo):
        self.dll.EX_JogStop.restype = c_bool
        self.dll.EX_JogStop.argtypes = [c_int]
        result = self.dll.EX_JogStop(nAxisNo)        
        print('Motor JogStop : ' , result)
        return result
        
    def MoveAbsolute(self, nAxisNo, dPos):
        self.dll.EX_MoveAbsolute.restype = c_bool
        self.dll.EX_MoveAbsolute.argtypes = [c_int, c_double]
        result = self.dll.EX_MoveAbsolute(nAxisNo, dPos)
        print('Motor MoveAbsolute : ' , result)
        return result

    def MoveRelative(self, nAxisNo, dPos):
        self.dll.EX_MoveRelative.restype = c_bool
        self.dll.EX_MoveRelative.argtypes = [c_int, c_double]
        result = self.dll.EX_MoveRelative(nAxisNo, dPos)
        print('Motor MoveAbsolute : ' , result)
        return result
                
    def MoveStop(self, nAxisNo):
        self.dll.EX_MoveStop.restype = c_bool
        self.dll.EX_MoveStop.argtypes = [c_int]
        result = self.dll.EX_MoveStop(nAxisNo)
        print('Motor MoveStop : ' , result)
        return result
        
    def MoveEStop(self, nAxisNo):
        self.dll.EX_MoveEStop.restype = c_bool
        self.dll.EX_MoveEStop.argtypes = [c_int]
        result = self.dll.EX_MoveEStop(nAxisNo)
        print('Motor MoveEStop : ' , result)
        return result
        
    def ABSMove_Chk(self, nAxisNo, dPos):
        self.dll.EX_ABSMove_Chk.restype = c_bool
        self.dll.EX_ABSMove_Chk.argtypes = [c_int, c_double]
        result = self.dll.EX_ABSMove_Chk(nAxisNo, dPos)
        print('Motor ABSMove_Chk : ' , result)
        return result
        
    def ROMMemoryRead(self, nAxisNo, ParamNum):
        self.dll.EX_ROMMemoryRead.restype = c_bool
        self.dll.EX_ROMMemoryRead.argtypes = [c_int, c_ubyte]
        result = self.dll.EX_ROMMemoryRead(nAxisNo, ParamNum)
        print('Motor ROMMemoryRead : ' , result)
        return result
        
    def RAMMemoryRead(self, nAxisNo, ParamNum):
        self.dll.EX_RAMMemoryRead.restype = c_bool
        self.dll.EX_RAMMemoryRead.argtypes = [c_int, c_ubyte]        
        result = self.dll.EX_RAMMemoryRead(nAxisNo, ParamNum)
        print('Motor RAMMemoryRead : ' , result)
        return result
        
    def RAMMemoryWrite(self, nAxisNo, ParamNum, nData):
        self.dll.EX_RAMMemoryWrite.restype = c_bool
        self.dll.EX_RAMMemoryWrite.argtypes = [c_int, c_ubyte, c_long]
        result = self.dll.EX_RAMMemoryWrite(nAxisNo, ParamNum, nData)
        print('Motor RAMMemoryWrite : ' , result)
        return result
        
    def RAMMemorySave(self, nAxisNo):
        self.dll.EX_RAMMemorySave.restype = c_bool
        self.dll.EX_RAMMemorySave.argtypes = [c_int]        
        result = self.dll.EX_RAMMemorySave(nAxisNo)
        print('Motor RAMMemorySave : ' , result)
        return result
        

#os.add_dll_directory('C://Users//Namuga//Desktop//VoyagerLDT_MotorVer//x64//Debug')
#hello_world_dll = ctypes.WinDLL('EziServoMotor.dll')
#hello_world_func = hello_world_dll['EX_Init']
#hello_world_func.argtypes = [ctypes.c_int]
#hello_world_func.restype = ctypes.c_bool
#result = hello_world_func(3)
#print(result)