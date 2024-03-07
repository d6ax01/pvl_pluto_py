#
# Python Simmian API
# ------------------
# 2014-10-21, heegeun.park
# Control Simmian by python script via C Simmian API.
# This python class is wrapping the C Simmian API functions for easy to use.
#

from ctypes import *
from time import sleep
import os
import platform
from site import getsitepackages
#from pea_util_functions import Util
from pathlib import Path
#from pea_return_types import *
from functools import reduce

VIRTUAL_CHANNEL_COUNT = 4
INFO_STRING_LEN = 50

class Simmian:
    
    # Load a c_simmian_api.dll from existing python file directory.
    # And automatically initializing to connect to Simmian COM Server.
    def __init__(self, af_I2C_id=0x18, af_address = 0x02, af_OIS_address = 0x48):
        self.dllname = 'c_simmian_api.dll'
        if platform.architecture()[0].find('64') != -1:
            self.dllname = 'c_simmian_api_x64.dll'
        self.dllpath = Path(__file__).absolute().parent.joinpath(self.dllname)
        if not os.path.exists(self.dllpath):
            self.dllpath = '{}\\{}'.format(getsitepackages()[1], self.dllname)

        self.dll = CDLL(str(self.dllpath))
        self.dll.Connect()

        self.af_I2C_id = af_I2C_id
        self.af_address = af_address
        self.af_OIS_address = af_OIS_address
        self.selectedTitleName = ''
    
    # Get version of PEA
    def GetVersion(self, opt=''):
        v = {'version': '2.23.0-rev1', 'date': 20220412}
        if opt == '': return v
        else: return v[opt]

    # User should call this method after connection.
    def Disconnect(self):
        self.dll.Disconnect()

    # Play / Stop / Reset
    def Play(self):
        self.dll.Play.restype = c_bool
        self.dll.Play.argtype = [c_wchar_p]
        return self.dll.Play(c_wchar_p(self.selectedTitleName))

    def Stop(self): 
        self.dll.Stop.restype = c_bool
        self.dll.Stop.argtype = [c_wchar_p]
        return self.dll.Stop(c_wchar_p(self.selectedTitleName))

    def Reset(self): 
        self.dll.Reset.argtype = [c_wchar_p]
        self.dll.Reset(c_wchar_p(self.selectedTitleName))

    # Register read methods are here.
    # Generally, using "RegisterRead(...)" method is comfortable.
    # length is... 0x1234 -> [input]byte length: 2, buffer length: 4
    def RegisterReadBySymbol(self, symbol, length):
        self.dll.RegisterReadBySymbol.restype = c_int
        self.dll.RegisterReadBySymbol.argtypes = [c_wchar_p, c_wchar_p, c_int]
        return self.dll.RegisterReadBySymbol(c_wchar_p(self.selectedTitleName), c_wchar_p(symbol), length)
    
    # Normal register read
    def RegisterRead(self, page, address, length):
        self.dll.RegisterRead.argtypes = [c_wchar_p, c_uint, c_uint, c_int, c_wchar_p]

        buff = (c_wchar * 50)()
        self.dll.RegisterRead(c_wchar_p(self.selectedTitleName), page, address, length, buff)        
        return int(buff.value, 16)

    # Register write methods are here.
    # Generally, using "Write(...)" method is comfortable.
    # Note: byteLength is below symbol register size (byte), default: 2
    def RegisterWriteBySymbol(self, symbol, value, length, byteLength=2):
        self.dll.RegisterWriteBySymbol.restype = c_bool
        self.dll.RegisterWriteBySymbol.argtypes = [c_wchar_p, c_wchar_p, c_uint, c_int, c_int]
        s = c_wchar_p(symbol)        
        return self.dll.RegisterWriteBySymbol(c_wchar_p(self.selectedTitleName), s, value, length, byteLength)

    # Normal register write
    # Note: byteLength will no longer needed
    def RegisterWrite(self, page, address, value, length):
        self.dll.RegisterWrite.restype = c_bool
        self.dll.RegisterWrite.argtypes = [c_wchar_p, c_uint, c_uint, c_uint, c_int]
        return self.dll.RegisterWrite(c_wchar_p(self.selectedTitleName),page, address, value, length)

    # Load register map
    def LoadRegisterMap(self, regpath):
        self.dll.LoadRegisterMap.restype = c_bool
        self.dll.LoadRegisterMap.argtypes = [c_wchar_p, c_wchar_p]
        s = c_wchar_p(regpath)
        return self.dll.LoadRegisterMap(c_wchar_p(self.selectedTitleName),s)

        # SPI Read
    # input length is byte length. Not buffer length. 
    # (0x1234 -> byte length is 2, buffer length is 4)
    def SPIRead(self, address, addrLength, dataLength):
        c_ubyte_p = POINTER(c_ubyte)
        self.dll.SPIRead.restype = c_bool
        self.dll.SPIRead.argtypes = [c_wchar_p, c_ubyte_p, c_int, c_ubyte_p, c_int]
        
        pAddr = (c_ubyte * addrLength)()
        for i in range(addrLength):
            pAddr[addrLength - i - 1] = ((address >> (i * 8)) & 0xFF)
        pAddrValue = cast(pAddr, c_ubyte_p)

        pData = (c_ubyte * dataLength)()
        pDataValue = cast(pData, c_ubyte_p)
        
        if self.dll.SPIRead(c_wchar_p(self.selectedTitleName),pAddrValue, addrLength, pDataValue, dataLength) == False:
            print("Fail to SPI read.")
            return False

        result = 0x0
        for i in range(dataLength):
            result <<= 8
            result |= pDataValue[i]
        
        return result

    def ReadSPI(self, address, dataLength):
        if type(address) is not str:
            print("Type error: address must be string type like '02020000' or '0x0202ABCD' (Hex)")
            return False

        if len(address) % 2 != 0:
            print("Length error: address must be even length like '02020000' or '0x0202ABCD'")
            return False
                    
        addrLength = int(len(address.replace('0x','')) / 2)
        address = int(address, 16)
        return self.SPIRead(address, addrLength, dataLength)
        
    # SPI Write
    # input length is byte length. Not buffer length. 
    # (0x1234 -> byte length is 2, buffer length is 4)
    def SPIWrite(self, address, addrLength, data, dataLength):
        c_ubyte_p = POINTER(c_ubyte)
        self.dll.SPIWrite.restype = c_bool
        self.dll.SPIWrite.argtypes = [c_wchar_p, c_ubyte_p, c_int, c_ubyte_p, c_int]
   
        pAddr = (c_ubyte * addrLength)()
        for i in range(addrLength):
            pAddr[addrLength - i - 1] = ((address >> (i * 8)) & 0xFF)
        pAddrValue = cast(pAddr, c_ubyte_p)
               
        pData = (c_ubyte * dataLength)()
        for i in range(dataLength):
            pData[dataLength - i - 1] = ((data >> (i * 8)) & 0xFF)
        pDataValue = cast(pData, c_ubyte_p)        
        return self.dll.SPIWrite(c_wchar_p(self.selectedTitleName), pAddrValue, addrLength, pDataValue, dataLength)

    # IIC Write wrapper method
    # address and data must be string type.
    def WriteSPI(self, address, data):
        if type(address) is not str:
            print("Type error: address must be string type like '02020000' or '0x0202ABCD' (Hex)")
            return False

        if type(data) is not str:
            print("Type error: data must be string type like '1F9A' or '0x1F9A' (Hex)")
            return False

        if len(address) % 2 != 0:
            print("Length error: address must have even length like '02020000' or '0x0202ABCD' (Hex)")
            return False

        if len(data) % 2 != 0:
            print("Length error: data must have even length like '1F9A' or '0x1F9A' (Hex)")
            return False

        addrLength = int(len(address.replace('0x','')) / 2)
        dataLength = int(len(data.replace('0x','')) / 2)
        address = int(address, 16)
        data = int(data, 16)
        return self.SPIWrite(address, addrLength, data, dataLength)

    # IIC Read
    # input length is byte length. Not buffer length. 
    # (0x1234 -> byte length is 2, buffer length is 4)
    def I2CRead(self, id, address, addrLength, dataLength):
        c_ubyte_p = POINTER(c_ubyte)
        self.dll.I2CRead.restype = c_bool
        self.dll.I2CRead.argtypes = [c_wchar_p, c_ubyte, c_ubyte_p, c_int, c_ubyte_p, c_int]

        if (addrLength > 4) or (addrLength < 1) :
           print("The length of address should be 1 ~ 4. yours :" + str(addrLength))
           return False

        pAddr = (c_ubyte * addrLength)()
        for i in range(addrLength):
            pAddr[addrLength - i - 1] = ((address >> (i * 8)) & 0xFF)
        pAddrValue = cast(pAddr, c_ubyte_p)

        pData = (c_ubyte * dataLength)()
        pDataValue = cast(pData, c_ubyte_p)
        
        self.dll.I2CRead(c_wchar_p(self.selectedTitleName),id, pAddrValue, addrLength, pDataValue, dataLength)
        
        result = 0x0
        for i in range(dataLength):
            result <<= 8
            result |= pDataValue[i]
        
        return result

    def ReadI2C(self, id, address, dataLength):
        if type(address) is not str:
            print("Type error: address must be string type like '0028' or '0x0028'")
            return False

        if len(address) % 2 != 0:
            print("Length error: address must be even length like '0028' or '0x0028'")
            return False

        addrLength = int(len(address.replace('0x','')) / 2)
        if (addrLength > 4) or (addrLength < 1) :
           print("The length of address should be 1 ~ 4. yours :" + str(addrLength))
           return False

        address = int(address, 16)
        return self.I2CRead(id, address, addrLength, dataLength)

    # IIC Write
    # input length is byte length. Not buffer length. 
    # (0x1234 -> byte length is 2, buffer length is 4)
    def I2CWrite(self, id, address, addrLength, data, dataLength):
        c_ubyte_p = POINTER(c_ubyte)
        self.dll.I2CWrite.restype = c_bool
        self.dll.I2CWrite.argtypes = [c_wchar_p, c_ubyte, c_ubyte_p, c_int, c_ubyte_p, c_int]

        if (addrLength > 4) or (addrLength < 1) :
            print("The length of address should be 1 ~ 4. yours :" + str(addrLength))
            return False
   
        pAddr = (c_byte * addrLength)()
        for i in range(addrLength):
            pAddr[addrLength - i - 1] = ((address >> (i * 8)) & 0xFF)
        pAddrValue = cast(pAddr, c_ubyte_p)
               
        pData = (c_byte * dataLength)()
        for i in range(dataLength):
            pData[dataLength - i - 1] = ((data >> (i * 8)) & 0xFF)
        pDataValue = cast(pData, c_ubyte_p)        
        return self.dll.I2CWrite(c_wchar_p(self.selectedTitleName), id, pAddrValue, addrLength, pDataValue, dataLength)

    def I2CWrites(self, id, address, addrLength, data, dataLength):
        c_ubyte_p = POINTER(c_ubyte)
        self.dll.I2CWrite.restype = c_bool
        self.dll.I2CWrite.argtypes = [c_wchar_p, c_ubyte, c_ubyte_p, c_uint, c_ubyte_p, c_uint]

        if (len(data) > dataLength) :
            print("dataLength value can not be bigger than size of data")
            return False

        if (addrLength > 4) or (addrLength < 1) :
            print("The length of address should be 1 ~ 4. yours :" + str(addrLength))
            return False

        pAddr = (c_ubyte * addrLength)()
        for i in range(addrLength):
            pAddr[addrLength - i - 1] = ((address >> (i * 8)) & 0xFF)

        pData = (c_ubyte * dataLength)()
        for i in range(dataLength):
            pData[i] = data[i] & 0xFF

        return self.dll.I2CWrite(c_wchar_p(self.selectedTitleName), id, pAddr, addrLength, pData, dataLength)

    # IIC Write wrapper method
    # address and data must be string type.
    def WriteI2C(self, id, address, data):
        if type(address) is not str:
            print("Type error: address must be string type like '0028' or '0x0028' (Hex)")
            return False

        if type(data) is not str:
            print("Type error: data must be string type like '1F9A' or '0x1F9A' (Hex)")
            return False

        if len(address) % 2 != 0:
            print("Length error: address must have even length like '0028' or '0x0028' (Hex)")
            return False

        if len(data) % 2 != 0:
            print("Length error: data must have even length like '1F9A' or '0x1F9A' (Hex)")
            return False

        addrLength = int(len(address.replace('0x','')) / 2)

        if (addrLength > 4) or (addrLength < 1) :
           print("The length of address should be 1 ~ 4. yours :" + str(addrLength))
           return False

        dataLength = int(len(data.replace('0x','')) / 2)
        address = int(address, 16)
        data = int(data, 16)
        return self.I2CWrite(id, address, addrLength, data, dataLength)

    # Capture frame(s) - normal purpose
    def Capture(self, savePath, skipFrameCount=0, captureCount=1, givenRoi=[]):
        self.dll.Capture.restype = c_bool
        self.dll.Capture.argtypes = [c_wchar_p, c_wchar_p, c_int, c_int, POINTER(c_int)]

        roi = (c_int * 4)()
        if len(givenRoi) > 3:
            for i in range(4): 
                roi[i] = givenRoi[i]
        
        arr = savePath.split('\\')
        dirPath = savePath.replace(arr[-1], '')
        if not os.path.isdir(dirPath):
            os.makedirs(dirPath)

        s = c_wchar_p(savePath)
        result = self.dll.Capture(c_wchar_p(self.selectedTitleName), s, skipFrameCount, captureCount, roi)
        #if captureCount == 1: return savePath
        #else:
        return result

    # Quick method for easy to use. Real work: call Capture() method
    def MultiCapture(self, savePath, captureCount=1, skipEachFrame=1, sizeOfIndexField=3, isCheckFinish=1):
        return self.dll.MultiCapture(c_wchar_p(self.selectedTitleName), savePath, captureCount, skipEachFrame, sizeOfIndexField, isCheckFinish)

    def GridROIMultiCapture(self, savePath, rawType, captureCnt=1, gridM=5, gridN=3, centerW=100, centerH=100, isCheckFinish=1):
        self.dll.GridROIMultiCapture.restype = c_int
        self.dll.GridROIMultiCapture.argtypes = [c_wchar_p, c_wchar_p, c_wchar_p, c_int, c_int, c_int, c_int, c_int,c_int]
        ret = self.dll.GridROIMultiCapture(c_wchar_p(self.selectedTitleName), savePath, rawType, captureCnt, gridM, gridN, centerW, centerH, isCheckFinish)
        if(ret == 1):
            print(r"Grid ROI Capture : Received parameters are not available \r\n- board name or save path or capture count.")
        elif(ret == 2):
            print(r"Grid ROI Capture : Fail to get frame info - width, height.")
        elif(ret == 3):
            print(r"Grid ROI Capture : Each grid size should be bigger than crop center size.")
        elif(ret == 4):
            print(r"Grid ROI Capture : Valid raw types are - Bayer, Tetra, Nona, Hexadeca, RGBW_FULL and RGBW_2SUM.")
        elif(ret == 5):
            print(r"Grid ROI Capture : the center crop size should be below - \r\n Bayer: multiple of two, Tetra: multiple of four, Nona: multiple of six, Hexadeca : multiple of eight.")
        elif(ret == 6):
            print(r"Grid ROI Capture : Fail to Grid ROI Capture.")

        return ret

    def AverageCapture(self, savePath, captureCount, replaceName='average_frame', removeTemporalFiles=True, skipEachFrame=1, givenRoi=[]):
        self.dll.AverageCapture.restype = c_bool
        self.dll.AverageCapture.argtypes = [c_wchar_p, c_wchar_p, c_int, c_wchar_p, c_bool, c_int, POINTER(c_int)]

        roi = (c_int * 4)()
        if len(givenRoi) > 3:
            for i in range(4): 
                roi[i] = givenRoi[i]

        arr = savePath.split('\\')
        dirPath = savePath.replace(arr[-1], '')
        if not os.path.isdir(dirPath):
            Util.MakeDirTree(dirPath)

        outPath = savePath.replace('.raw', '_{}.raw'.format(replaceName))
        result = self.dll.AverageCapture(c_wchar_p(self.selectedTitleName), c_wchar_p(savePath), captureCount, c_wchar_p(outPath), removeTemporalFiles, skipEachFrame, roi)
        return outPath if result else False

    # Sequential Cpature
    def SequentialCapture(self, filename, path, cnt=30, isCheckFinished = 1, ext='raw'):
        os.makedirs(path, exist_ok=True)
        self.dll.SequentialCapture.restype = c_bool
        self.dll.SequentialCapture.argtypes = [c_wchar_p, c_wchar_p, c_wchar_p, c_int, c_wchar_p, c_bool]
        return self.dll.SequentialCapture(c_wchar_p(self.selectedTitleName), c_wchar_p(filename), c_wchar_p(path), cnt, ext, isCheckFinished)

    # Load a setfile via file path
    def LoadSetfile(self, path):
        self.dll.LoadSetfile.restype = c_bool
        self.dll.LoadSetfile.argtypes = [c_wchar_p, c_wchar_p]

        s = c_wchar_p(path)
        return self.dll.LoadSetfile(c_wchar_p(self.selectedTitleName),s)

    # Get render frame information
    def GetRenderFrameInfo(self):
        self.dll.GetRenderImageInfo.restype = c_bool
        #self.dll.GetRenderImageInfo.argtypes = [c_wchar_p, c_wchar_p, c_wchar_p, c_wchar_p]
        self.dll.GetRenderImageInfo.argtypes = [c_wchar_p, c_wchar_p, c_wchar_p, c_wchar_p]
        width = (c_wchar * 20)()
        height = (c_wchar * 20)()
        format = (c_wchar * 20)()
        #avgY = (c_wchar * 20)()

        #result = self.dll.GetRenderImageInfo(width, height, format, avgY)
        result = self.dll.GetRenderImageInfo(c_wchar_p(self.selectedTitleName), width, height, format)
        if not result: return False
        else:
            #pyresult = {'width': int(width.value), 'height': int(height.value), 'format': format.value, 'avgY': float(avgY.value)}
            pyresult = {'width': int(width.value), 'height': int(height.value), 'format': format.value}
            return pyresult

    # Get raw frame information
    def GetRawFrameInfo(self):
        self.dll.GetRawFrameInfo.restype = c_bool
        # self.dll.GetRawFrameInfo.argtypes = [c_wchar_p, c_wchar_p, c_wchar_p, c_wchar_p]
        self.dll.GetRawFrameInfo.argtypes = [c_wchar_p, c_wchar_p, c_wchar_p, c_wchar_p]

        width = (c_wchar * 20)()
        height = (c_wchar * 20)()
        size = (c_wchar * 20)()
        # decoder = (c_wchar * 20)()

        # result = self.dll.GetRawFrameInfo(width, height, size, decoder)
        result = self.dll.GetRawFrameInfo(c_wchar_p(self.selectedTitleName),width, height, size)
        if not result: return False
        else:
            # pyresult = {'width': int(width.value), 'height': int(height.value), 'size': int(size.value), 'decoder': int(decoder.value)}
            pyresult = {'width': int(width.value), 'height': int(height.value), 'size': int(size.value)}
            return pyresult

    # Get sensor frame rate
    def GetFPS(self):
        self.dll.GetSensorFPS.restype = c_double
        self.dll.GetSensorFPS.argtypes = [c_wchar_p]        
        fps = self.dll.GetSensorFPS(c_wchar_p(self.selectedTitleName))
        return fps

    # Get board PLL clock
    def GetBoardPLLClock(self):
        self.dll.GetBoardPLLClock.restype = c_double
        self.dll.GetBoardPLLClock.argtypes = [c_wchar_p]
        pll = self.dll.GetBoardPLLClock(c_wchar_p(self.selectedTitleName))
        return pll

    # Get a selected decoder name
    def GetDecoder(self):
        self.dll.GetSelectedDecoder.restype = c_bool
        self.dll.GetSelectedDecoder.argtypes = [c_wchar_p, c_wchar_p]
        name = (c_wchar * 100)()
        result = self.dll.GetSelectedDecoder(c_wchar_p(self.selectedTitleName), name)
        return name.value if result else False

    # Set Decoder by given name
    def SetDecoder(self, decoderName):
        if len(decoderName) < 1:
            print('[!] Method needs a valid decoder name like \'PackedRAW\'')
            return False
        if decoderName.lower() == 'twopd': decoderName = '2PD'
        self.dll.SetDecoder.restype = c_bool
        self.dll.SetDecoder.argtypes = [c_wchar_p, c_wchar_p]
        return self.dll.SetDecoder(c_wchar_p(self.selectedTitleName), c_wchar_p(decoderName))

    # Get bayer order
    def GetBayerOrder(self, decoderName):
        if len(decoderName) < 1:
            print('[!] Method needs a valid decoder name like \'PackedRAW\'')
            return False

        self.dll.GetBayerOrder.restype = c_bool
        self.dll.GetBayerOrder.argtypes = [c_wchar_p, c_wchar_p, c_wchar_p]

        order = (c_wchar * 20)()
        result = self.dll.GetBayerOrder(c_wchar_p(self.selectedTitleName), c_wchar_p(decoderName), order)
       
        if result: 
            bayers = {'GRBG': 'gr', 'RGGB': 'r', 'BGGR': 'b', 'GBRG': 'gb'}
            return bayers[order.value]
        else: return False

    # Set bayer order (newBayerOrder = gr / r / b / gb)
    def SetBayerOrder(self, decoderName, newBayerOrder):
        if len(decoderName) < 1 or len(newBayerOrder) < 1:
            print('[!] Method needs a valid decoder name like \'PackedRAW\' and bayer order like \'gr\'')
            return False

        self.dll.SetBayerOrder.restype = c_bool
        self.dll.SetBayerOrder.argtypes = [c_wchar_p, c_wchar_p, c_wchar_p]

        bayers = {'gr':'GRBG', 'r':'RGGB', 'b':'BGGR', 'gb':'GBRG'}
        bayer = bayers[newBayerOrder]
        return self.dll.SetBayerOrder(c_wchar_p(self.selectedTitleName), c_wchar_p(decoderName), c_wchar_p(bayer))

    # Set Clip ROI
    def SetClipROI(self, isCenter=False, givenRoi=[]):

        self.dll.SetClipROI.restype = c_bool
        self.dll.SetClipROI.argtypes = [c_wchar_p, POINTER(c_int), c_bool]

        roi = (c_int * 4)()
        if len(givenRoi) > 3:
            for i in range(4): 
                roi[i] = givenRoi[i]
        return self.dll.SetClipROI(c_wchar_p(self.selectedTitleName), roi, isCenter)

    # Calculate shutter from F#number (default: 125ms, F2.2)
    def GetShutterByF(self, fnumber):
        return ((fnumber ** 2) / (2.2 ** 2) * 125)
        
    # Get integration time by target LSB
    # Warning: Be carefully using this method. Sometimes work not perfectly.
    # Notice: width, height 0 means auto-detect size, recommand using GetROIRect()
    def SetEITbyLSB(self, targetLSB, targetBayer='gr', 
                    isCenter=False, givenRoi=[], 
                    page=0x4000, eitAddr=0x0202, minEIT=0x5, 
                    maxTry=20, eitAddrShort=0, selPD='', delayMSec=500):
        if targetLSB < 0 or targetLSB > 1023:
            print('[!] Method needs a valid target LSB (0 ~ 1023)')
            return False

        roi = (c_int * 4)()
        if len(givenRoi) > 3: 
            for i in range(4): 
                roi[i] = givenRoi[i]

        self.dll.SetEITbyLSB.restype = c_int
        self.dll.SetEITbyLSB.argtypes = [c_wchar_p, c_int, c_wchar_p, c_bool, POINTER(c_int),
                                         c_uint, c_uint, c_uint, c_int, c_uint, c_wchar_p, c_int]
        eit = self.dll.SetEITbyLSB(c_wchar_p(self.selectedTitleName), targetLSB, c_wchar_p(targetBayer), isCenter, 
                                   roi, page, eitAddr, minEIT, maxTry, 
                                   eitAddrShort, c_wchar_p(selPD), delayMSec)
        return eit if eit > 0 and eit < 0x10000 else False

    # Initialize AF-Actuator and OIS centering
    def InitAF(self, id=0x18, addr=0x02, ois=0x48):
        if id != 0x18: self.af_I2C_id = id
        if addr != 0x02: self.af_address = addr
        if ois != 0x48: self.af_OIS_address = ois

        self.I2CWrite(self.af_I2C_id, self.af_address, 1, 0x00, 1)
        sleep(1)

        self.I2CWrite(self.af_OIS_address, 0x0000, 2, 0x01, 1)
        self.I2CWrite(self.af_OIS_address, 0x0002, 2, 0x05, 1)
        
    # Move lens position for auto-focus
    def MoveAFPos(self, pos):
        self.I2CWrite(self.af_I2C_id, 0x00, 1, pos * 128, 2)

    # Get ROI Rect @dong.shin
    def GetROIRect(self):
        self.dll.GetROIRect.argtypes = [c_wchar_p, POINTER(c_int)]
        pRoi = (c_int * 4)()
        self.dll.GetROIRect(c_wchar_p(self.selectedTitleName), pRoi)
        return {'left': pRoi[0], 'top': pRoi[1], 'right': pRoi[2], 'bottom': pRoi[3]}

    # Set ROI Rect @dong.shin
    def SetROIRect(self, left, top, right, bottom):
        self.dll.SetROIRect.argtypes = [c_wchar_p, c_int, c_int, c_int, c_int]
        return self.dll.SetROIRect(c_wchar_p(self.selectedTitleName), left, top, right, bottom)

    # Change Raw Decoder Bit-depth @dong.shin
    # This function only works SimmianMV.
    def SetRawBitDepth(self, bits): # bits = 10 or 12 or 14 ... (integer type)
        if bits < 8 or bits > 16:
            print('[!] Method needs a valid parameter (bits)')
            return False
        self.dll.SetRawBitDepth.restype = c_bool
        self.dll.SetRawBitDepth.argtypes = [c_wchar_p, c_int]
        return self.dll.SetRawBitDepth(c_wchar_p(self.selectedTitleName), bits)

    # Change 2PD Decoder Type (displayType = 0 or 1) @dong.shin
    def Set2PDMode(self, value, mode):
        if len(mode) < 1:
            print('[!] Method needs a valid parameter (mode)')
            return False
        if type(value) == bool:
            if value == True: value = 1
            else: value = 0
        var = '{}'.format(value)
        self.dll.Set2PDMode.restype = c_bool
        self.dll.Set2PDMode.argtypes = [c_wchar_p, c_wchar_p, c_wchar_p]
        return self.dll.Set2PDMode(c_wchar_p(self.selectedTitleName), c_wchar_p(var), c_wchar_p(mode))

    # Selecting L or R PD (displayType = 0 or 1) @dong.shin
    def Select2PD(self, isTrue, pd):
        if pd not in ('L', 'R'):
            print('[!] Method needs a valid parameter (pd)')
            return False
        if type(isTrue) == bool: 
            if isTrue == True: isTrue = 1
            else: isTrue = 0
        self.dll.Set2PD.restype = c_bool
        self.dll.Set2PD.argtypes = [c_wchar_p, c_int, c_wchar]
        return self.dll.Set2PD(c_wchar_p(self.selectedTitleName), isTrue, c_wchar(pd))

    # 2PD Quick methods (displayType = 0 or 1) @dong.shin
    def SetDecoder2PD(self, displayType): return self.Set2PDMode(displayType, 'ConvertMethod')
    def Set2PD_L(self, isTrue): return self.Select2PD(isTrue, 'L')
    def Set2PD_R(self, isTrue): return self.Select2PD(isTrue, 'R')
    def Set2PD_MultiCapture(self, isTrue): return self.Set2PDMode(isTrue, 'SaveSplitFrames')
    def Set2PD_CaptureValidate(self, isTrue): return self.Set2PDMode(isTrue, 'CaptureValidate')
    def Set2PD_SubtractPedestal(self, isTrue): return self.Set2PDMode(isTrue, 'SubtractPedestal')

    # Get result from user command in directly (for debug only)
    def GetCmdResult(self, tagName=''):
        resultStr = (c_wchar * 512)()
        if len(tagName) > 0:
            self.dll.GetResultByTag.argtypes = [c_wchar_p, c_wchar_p, c_uint]
            self.dll.GetResultByTag(c_wchar_p(tagName), resultStr, 512)
        else:
            self.dll.GetResult.argtypes = [c_wchar_p, c_uint]
            self.dll.GetResult(resultStr, 512)
        return resultStr

    def UserCommand(self, command):
        self.dll.UserCommand.restype = c_bool
        self.dll.UserCommand.argtypes = [c_wchar_p]
        return self.dll.UserCommand(command)

    def SetDecoderSubOption(self, decoderName, subOption, isOn):
        if decoderName.lower() == 'twopd' : decoderName = '2PD'

        if(decoderName == "2PD"):
            if subOption.lower() == 'l': subOption = 'L'
            if subOption.lower() == 'r': subOption = 'R'
            if(subOption == "PhaseDetection" or subOption == "PD") : subOption = "ConvertMethod"
            self.dll.Set2PDDecoderSubOption.restype = c_bool
            self.dll.Set2PDDecoderSubOption.argtypes = [c_wchar_p, c_wchar_p, c_wchar_p]
            ret = self.dll.Set2PDDecoderSubOption(c_wchar_p(self.selectedTitleName), c_wchar_p(subOption), c_wchar_p(isOn))
            if ret == 0: print("[!] Method needs a valid parameter\n[2PD SubOption] : Packed, ConvertMethod(PD), L(Selected PD), R(Selected PD), SaveSplitFrames")
            return ret

        support_decoder_dict = dict(Raw="Packed, Format, Color, Order",
                       Tetra="Packed, BayerRearrangement, Format, Color, Order",
                       Nona="Packed, Frame, Rearrangement, Format, Color, Order",
                       RGBW="FrameOutputMode, FullMode_Direction, Format, Color, Order, BayerType, PatternType",
                       Hexadeca="Packed, Rearrangement, Format, Color, Order",
                       TwoPD="Packed, ConvertMethod(PD), L(Selected PD), R(Selected PD), SaveSplitFrames")

        if decoderName not in support_decoder_dict:
            print("[!] Invalid decoderName: {0}".format(decoderName))
            print("Supported decoders and sub options are")
            for key, value in support_decoder_dict.items():
                print(key, ":", value)
            return False
        elif subOption not in support_decoder_dict[decoderName]:
            print("[!] Method needs a valid parameter [{0} SubOption] : {1}".format(decoderName, support_decoder_dict[decoderName]))
            return False

        self.dll.SetDecoderSubOption.restype = c_bool
        self.dll.SetDecoderSubOption.argtypes = [c_wchar_p, c_wchar_p, c_wchar_p, c_wchar_p]
        ret = self.dll.SetDecoderSubOption(c_wchar_p(self.selectedTitleName), c_wchar_p(decoderName), c_wchar_p(subOption), c_wchar_p(isOn))
        if(ret == 0):
            print("[!] Method needs a valid parameter [{0} SubOption] : {1}".format(decoderName, support_decoder_dict[decoderName]))
        return ret

    def SetRawDecoderFrameDecompress(self, methodName, firstOption='', firstOptionValue='', secondOption='', secondOptionValue=''):
        self.dll.SetRawDecoderFrameFrameDecompress.restype = c_bool
        self.dll.SetRawDecoderFrameFrameDecompress.argtypes = [c_wchar_p, c_wchar_p, c_wchar_p, c_wchar_p, c_wchar_p, c_wchar_p]
        ret = self.dll.SetRawDecoderFrameFrameDecompress(c_wchar_p(self.selectedTitleName), c_wchar_p(methodName), c_wchar_p(firstOption), c_wchar_p(firstOptionValue), c_wchar_p(secondOption), c_wchar_p(secondOptionValue))
        if ret == 0: print("[!] Method needs a valid parameter\n[RawDecoderFrameDecompress]")
        return ret

    def GetBoardCount(self):
        self.dll.GetBoardCount.restype = c_int
        return self.dll.GetBoardCount()

    def GetTitleNamefromSimmian(self, idx):
        self.dll.GetTitleName.restype = c_bool;
        self.dll.GetTitleName.argtypes = [c_uint, c_wchar_p, c_uint]

        board_name = (c_wchar * INFO_STRING_LEN)()
        ret = self.dll.GetTitleName(c_uint(idx), board_name, INFO_STRING_LEN)
        if ret == False:
            print("[!] Fail to get valid board names")
            return None
        return board_name.value

    def SetTitleName(self, titleName):
        validCnt = self.GetBoardCount()
        validTitleNames = []

        i = 0
        flag = 0
        for i in range(0, validCnt):
            validTitleNames.append(self.GetTitleNamefromSimmian(i))
            if validTitleNames[i].find(titleName) != -1:
                flag =1
                break;

        if flag == 0:
            print('[!] Method needs valid BoardName :' , validTitleNames)
        else:
            self.selectedTitleName = titleName
            print('Success to set a title name : ', self.selectedTitleName)

    def GetBoardFWVersion(self):
        self.dll.GetBoardFWVersion.restype = c_bool
        self.dll.GetBoardFWVersion.argtypes = [c_wchar_p, c_wchar_p, c_uint]

        fw_ver = (c_wchar * INFO_STRING_LEN)()
        ret = self.dll.GetBoardFWVersion(c_wchar_p(self.selectedTitleName), fw_ver, INFO_STRING_LEN)
        if ret == False:
            print("[!] Fail to get FW version")
            return None
        return fw_ver.value

    def GetNxSimmianSWVersion(self) :
        self.dll.GetNxSimmianSWVersion.restype = c_bool
        self.dll.GetNxSimmianSWVersion.argtypes = [c_wchar_p, c_wchar_p, c_uint]

        sw_ver = (c_wchar * INFO_STRING_LEN)()
        ret = self.dll.GetNxSimmianSWVersion(c_wchar_p(self.selectedTitleName), sw_ver, INFO_STRING_LEN)
        if ret == False:
            print("[!] Fail to get SW version")
            return None
        return sw_ver.value

    def GetSensorName(self):
        self.dll.GetSensorName.restype = c_bool
        self.dll.GetSensorName.argtypes = [c_wchar_p, c_wchar_p, c_uint]

        sensor_name = (c_wchar * INFO_STRING_LEN)()
        ret = self.dll.GetSensorName(c_wchar_p(self.selectedTitleName), sensor_name, INFO_STRING_LEN)
        if ret == False:
            print("[!] Fail to get sensor name")
            return None
        return sensor_name.value

    def GetBoardName(self):
        self.dll.GetBoardName.restype = c_bool
        self.dll.GetBoardName.argtypes = [c_wchar_p, c_wchar_p, c_uint]

        board_name = (c_wchar * INFO_STRING_LEN)()
        ret = self.dll.GetBoardName(c_wchar_p(self.selectedTitleName), board_name, INFO_STRING_LEN)
        if ret == False:
            print("[!] Fail to get board name")
            return None
        return board_name.value

    def GetDecoderSubOption(self, decoderName, subOption):
        decoder_sub_option = (c_wchar * INFO_STRING_LEN)()

        if decoderName.lower() == 'twopd' : decoderName = '2PD'
        if(decoderName == "2PD"):
            if subOption.lower() == 'l': subOption = 'L'
            if subOption.lower() == 'r': subOption = 'R'
            if( subOption == "PhaseDetection" or subOption == "PD") : subOption = "ConvertMethod"
            self.dll.Get2PDDecoderSubOption.restype = c_bool
            self.dll.Get2PDDecoderSubOption.argtypes = [c_wchar_p, c_wchar_p, c_wchar_p, c_uint]
            ret = self.dll.Get2PDDecoderSubOption(c_wchar_p(self.selectedTitleName), c_wchar_p(subOption), decoder_sub_option, INFO_STRING_LEN)
            if ret == False:
                print("[!] Fail to get sub option")
                return None
            if decoder_sub_option.value == '':
                print("[!] Method needs a valid parameter\n[2PD SubOption] : Packed, ConvertMethod(PD), L(Selected PD), R(Selected PD), SaveSplitFrames")
                return None

            return decoder_sub_option.value

        support_decoder_dict = dict(Raw="Packed, Format, Color, Order",
                       Tetra="Packed, BayerRearrangement, Format, Color, Order",
                       Nona="Frame, Rearrangement, Format, Color, Order",
                       RGBW="FrameOutputMode, FullMode_Direction, Format, Color, Order, BayerType, PatternType",
                       Hexadeca="Packed, Rearrangement, Format, Color, Order", 
                       TwoPD="Packed, ConvertMethod(PD), L(Selected PD), R(Selected PD), SaveSplitFrames")
        if decoderName not in support_decoder_dict:
            print("[!] Invalid decoderName: {0}".format(decoderName))
            print("Supported decoders and sub options are")
            for key, value in support_decoder_dict.items():
                print(key, ":", value)
            return False
        elif subOption not in support_decoder_dict[decoderName]:
            print("[!] Method needs a valid parameter [{0} SubOption] : {1}".format(decoderName, support_decoder_dict[decoderName]))
            return False

        self.dll.GetDecoderSubOption.restype = c_bool
        self.dll.GetDecoderSubOption.argtypes = [c_wchar_p, c_wchar_p, c_wchar_p, c_wchar_p, c_uint]
        ret = self.dll.GetDecoderSubOption(c_wchar_p(self.selectedTitleName), c_wchar_p(decoderName), c_wchar_p(subOption), decoder_sub_option, INFO_STRING_LEN)
        if ret == False:
            print("[!] Fail to get sub option")
            return None
        if decoder_sub_option.value == '':
            print("[!] Method needs a valid parameter [{0} SubOption] : {1}".format(decoderName, support_decoder_dict[decoderName]))
            return None

        return decoder_sub_option.value

    def GetFrameData(self, pFrame, width, height):
        self.dll.GetFrameData.restype = c_bool
        self.dll.GetFrameData.argtypes = [POINTER(c_ushort), c_int, c_int, c_wchar_p(self.selectedTitleName)]
        ret = self.dll.GetFrameData(pFrame, width, height, c_wchar_p(self.selectedTitleName))
        return ret

    def GetRenderFrameData(self, pRGBFrame, width, height):
        self.dll.GetRenderFrameData.restype = c_bool
        self.dll.GetRenderFrameData.argtypes = [POINTER(c_ubyte), c_int, c_int, c_wchar_p(self.selectedTitleName)]
        ret = self.dll.GetRenderFrameData(pRGBFrame, width, height, c_wchar_p(self.selectedTitleName))
        return ret

    def GetInterleavedDataSizeArray(self, array_vc_size, array_vc_idx):
        if array_vc_idx is None:
            print('[!] Method needs valid virtual channel index information')
            return False

        checked_vc_idx = 0
        for vc_idx in array_vc_idx:
            if vc_idx >= VIRTUAL_CHANNEL_COUNT:
                print('[!] invalid virtual channel idx :',vc_idx)
                continue
            checked_vc_idx |= 1 << vc_idx

        self.dll.GetInterleavedDataSizeArray.restype = c_bool
        self.dll.GetInterleavedDataSizeArray.argtypes = [type(array_vc_size), c_uint32, c_wchar_p(self.selectedTitleName)]
        ret = self.dll.GetInterleavedDataSizeArray(array_vc_size, c_uint32(checked_vc_idx), c_wchar_p(self.selectedTitleName))
        return ret

    def GetFrameWithInterleavedData(self, pMainFrame, array_interleaved_data, array_vc_size, array_vc_idx):
        if array_vc_idx is None:
            print('[!] Method needs valid virtual channel index information')
            return False

        checked_vc_idx = 0
        for vc_idx in array_vc_idx:
            if vc_idx >= VIRTUAL_CHANNEL_COUNT or array_vc_size[vc_idx] == 0:
                print('[!] invalid virtual channel idx :',vc_idx)
                continue
            checked_vc_idx |= 1 << vc_idx

        if checked_vc_idx == 0:
            return False

        self.dll.GetFrameWithInterleavedData.restype = c_bool
        self.dll.GetFrameWithInterleavedData.argtypes = [POINTER(frame_data), type(array_interleaved_data), c_uint32, c_wchar_p(self.selectedTitleName)]
        ret = self.dll.GetFrameWithInterleavedData(pMainFrame, array_interleaved_data, c_uint32(checked_vc_idx), c_wchar_p(self.selectedTitleName))
        return ret

    def SetDeviceAddress(self, address):
        self.dll.SetDeviceAddress.restype = c_bool
        self.dll.SetDeviceAddress.argtypes = [c_wchar_p, c_int]
        ret = self.dll.SetDeviceAddress(c_wchar_p(self.selectedTitleName), address)
        return ret
