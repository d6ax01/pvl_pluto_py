import ctypes
from ctypes import *
from pathlib import Path
from site import getsitepackages
import os
import platform
import python_simmian_api
import sys
import struct
import time
import zlib

#******************************************************
# 생산결과코드
is_code = f''

PASS = 0                # 0   PASS
FAIL = 1                # 1   FAIL
FAIL_SENSOR_ID = 62     # 62  SENSOR_ID 불량
FAIL_SIMMIAN_INIT = 100 # 100 INIT_SIMMIAN 불량
FAIL_IS_ADMIN = 101     # 101 IS_ADMIN
FAIL_IS_MOTOR = 102     # 102 IS_MOTOR
FAIL_OTP_WRITE = 103    # 103 OTP_WRITE 불량 -> e2p 쓰기 실패
FAIL_WIGG_LINEARITY_BROKEN = 104    # 104 [wigg] wiggling linearity is broken
FAIL_WIGG_GETCONFIDENCETHRE = 105   # 105 [WIGG] getWiggConfidenceThre is fail
FAIL_CALFILE_COUNT = 106            # 106 파일 갯수 부족
FAIL_IS_CONNECT_CHANGE = 107        # 107 IS_CONNECT_CHANGE
FAIL_Z_NOISE = 108      # 108 Z축 잡음 불량
FAIL_Z_ERROR = 109      # 109 Z축 오차 불량
FAIL_VCSEL_POWER = 110  # 110 픽셀 밝기 레벨 불량
FAIL_APC_CHECK = 111    # 111 APC 체크 불량
FAIL_Z_NOISE_100 = 112  # 112 100mhz, Z축 잡음 불량
FAIL_Z_ERROR_100 = 113  # 113 100mhz, Z축 오차 불량
FAIL_VCSEL_POWER_100 = 114  # 114 100mhz, 픽셀 밝기 레벨 불량
FAIL_APC_CHECK_100 = 115    # 115 100mhz, APC 체크 불량
FAIL_Z_NOISE_20 = 116   # 116 20mhz, Z축 잡음 불량
FAIL_Z_ERROR_20 = 117   # 117 20mhz, Z축 오차 불량
FAIL_VCSEL_POWER_20 = 118   # 118 20mhz, 픽셀 밝기 레벨 불량
FAIL_APC_CHECK_20 = 119     # 119 20mhz, APC 체크 불량
FAIL_MAKE_SETFILE = 120     # 120 MAKE_SETFILE, 셋파일 생성 실패
FAIL_LOAD_SETFILE = 121     # 121 LOAD_SETFILE

#******************************************************

class DepthValidationData500mm(ctypes.Structure):
    _fields_ = [("Depth_mean_of_center_ROI", c_float),
                ("Depth_mean_of_0dot6F_ROI_LT", c_float),
                ("Depth_mean_of_0dot6F_ROI_RT", c_float),
                ("Depth_mean_of_0dot6F_ROI_RB", c_float),
                ("Depth_mean_of_0dot6F_ROI_LB", c_float),
                ("Validation_Noise_of_Center_ROI", c_float),
                ("Validation_Noise_of_0dot6F_ROI_LT", c_float),
                ("Validation_Noise_of_0dot6F_ROI_RT", c_float),
                ("Validation_Noise_of_0dot6F_ROI_RB", c_float),
                ("Validation_Noise_of_0dot6F_ROI_LB", c_float)]


class VcselOpticalPowerData(ctypes.Structure):
    _fields_ = [("Center_ROI", c_float),
                ("Side_0dot6F_LT", c_float),
                ("Side_0dot6F_RT", c_float),
                ("Side_0dot6F_RB", c_float),
                ("Side_0dot6F_LB", c_float)]


class DepthValidationData300mm(ctypes.Structure):
    _fields_ = [("Depth_mean_of_center_ROI", c_float),
                ("Reserve", c_ubyte * 16)]


class EepromOffsetInfo(ctypes.Structure):
    _fields_ = [("EEPROM_HEADER_START_ADDRESS", c_int),
                ("EEPROM_HEADER_END_ADDRESS", c_int),
                ("EEPROM_CALIBRATIONDATA_START_ADDRESS", c_int),
                ("EEPROM_CALIBRATIONDATA_END_ADDRESS", c_int),
                ("EEPROM_FACTORY_START_ADDRESS", c_int),
                ("EEPROM_FACTORY_END_ADDRESS", c_int)
                ]


class VstEepromParser:

    EEPROM_HEADER_START_ADDRESS = 0x00000000
    EEPROM_HEADER_END_ADDRESS = 0x000000FF
    EEPROM_CALIBRATIONDATA_START_ADDRESS = 0x00000100
    EEPROM_CALIBRATIONDATA_END_ADDRESS = 0x000018FF
    EEPROM_FACTORY_START_ADDRESS = 0x00001900
    EEPROM_FACTORY_END_ADDRESS = 0x00001FFF

    EEPROM_START_ADDRESS = EEPROM_HEADER_START_ADDRESS
    EEPROM_END_ADDRESS = EEPROM_FACTORY_END_ADDRESS
    EEPROM_CAL_MAP_SIZE = EEPROM_END_ADDRESS + 0x00000001    # EEPROM 시작 주소가 0이므로 +1

    eeprom_offset_info = EepromOffsetInfo()
    eeprom_offset_info.EEPROM_HEADER_START_ADDRESS = EEPROM_HEADER_START_ADDRESS
    eeprom_offset_info.EEPROM_HEADER_END_ADDRESS = EEPROM_HEADER_END_ADDRESS
    eeprom_offset_info.EEPROM_CALIBRATIONDATA_START_ADDRESS = EEPROM_CALIBRATIONDATA_START_ADDRESS
    eeprom_offset_info.EEPROM_CALIBRATIONDATA_END_ADDRESS = EEPROM_CALIBRATIONDATA_END_ADDRESS
    eeprom_offset_info.EEPROM_FACTORY_START_ADDRESS = EEPROM_FACTORY_START_ADDRESS
    eeprom_offset_info.EEPROM_FACTORY_END_ADDRESS = EEPROM_FACTORY_END_ADDRESS

    def __init__(self):
        self.dllname = 'VstEepromParser.dll'
        if platform.architecture()[0].find('64') != -1:
            self.dllname = 'VstEepromParser.dll'
        self.dllpath = Path(__file__).absolute().parent.joinpath(self.dllname)
        if not os.path.exists(self.dllpath):
            self.dllpath = '{}\\{}'.format(getsitepackages()[1], self.dllname)

        self.dll = CDLL(str(self.dllpath))

        # EEPROM 영역 사이즈 정보를 전달합니다.
        self.dll.EX_EepromInit(self.eeprom_offset_info)
        print(f'[VST EEPROM PARSER] Init')

    def EX_GetLastErrorMessage(self):
        self.dll.EX_GetLastErrorMessage.restype = c_wchar_p
        self.dll.EX_GetLastErrorMessage.argtypes = None

        message = self.dll.EX_GetLastErrorMessage()

        return message

    def EX_GetLastErrorCode(self):
        self.dll.EX_GetLastErrorCode.restype = c_int
        self.dll.EX_GetLastErrorCode.argtypes = None

        code = self.dll.EX_GetLastErrorCode()

        return code

    def EX_EepromCreateFinalDumpUsingHeaderAndCalibrationDumpMemory(self,
                                                                    header_and_calibration_dump,
                                                                    header_and_calibration_dump_length,
                                                                    board_offset_f1,
                                                                    board_offset_f2,
                                                                    Depth_Validation_Data_f1_QVGA_500mm,
                                                                    VCSEL_Optical_Power_Data_f1,
                                                                    Depth_Validation_Data_f1_300mm,
                                                                    Depth_Validation_Data_f2_QVGA_500mm,
                                                                    VCSEL_Optical_Power_Data_f2,
                                                                    Depth_Validation_Data_f2_300mm,
                                                                    out_final_dump,
                                                                    out_final_dump_length,
                                                                    out_modify_lens_calibration_checksum,
                                                                    update_lens_calibration_checksum2,
                                                                    update_board_offset) -> bool:

        self.dll.EX_EepromCreateFinalDumpUsingHeaderAndCalibrationDumpMemory.restype = c_bool
        self.dll.EX_EepromCreateFinalDumpUsingHeaderAndCalibrationDumpMemory.argtype = \
            [POINTER(c_byte),
             c_uint32,
             c_ushort,
             c_ushort,
             POINTER(DepthValidationData500mm),
             POINTER(VcselOpticalPowerData),
             POINTER(DepthValidationData300mm),
             POINTER(DepthValidationData500mm),
             POINTER(VcselOpticalPowerData),
             POINTER(DepthValidationData300mm),
             POINTER(c_byte),
             POINTER(c_uint32),
             POINTER(c_bool),
             c_bool,
             c_bool
             ]

        ref_out_final_dump_length = c_uint32(out_final_dump_length[0])
        ref_out_modify_lens_calibration_checksum = c_bool(out_modify_lens_calibration_checksum[0])

        result = self.dll.EX_EepromCreateFinalDumpUsingHeaderAndCalibrationDumpMemory(header_and_calibration_dump,
                                                                                      header_and_calibration_dump_length,
                                                                                      board_offset_f1,
                                                                                      board_offset_f2,
                                                                                      Depth_Validation_Data_f1_QVGA_500mm,
                                                                                      VCSEL_Optical_Power_Data_f1,
                                                                                      Depth_Validation_Data_f1_300mm,
                                                                                      Depth_Validation_Data_f2_QVGA_500mm,
                                                                                      VCSEL_Optical_Power_Data_f2,
                                                                                      Depth_Validation_Data_f2_300mm,
                                                                                      out_final_dump,
                                                                                      byref(ref_out_final_dump_length),
                                                                                      byref(
                                                                                          ref_out_modify_lens_calibration_checksum),
                                                                                      update_lens_calibration_checksum2,
                                                                                      update_board_offset)

        out_final_dump_length[0] = ref_out_final_dump_length
        out_modify_lens_calibration_checksum[0] = ref_out_modify_lens_calibration_checksum

        print(f'EX_EepromCreateFinalDumpUsingHeaderAndCalibrationDumpMemory : {result}')

        return result


VST_EEPROM_PARSER = VstEepromParser()


def example_create_final_dump_file_using_header_and_calibration_dump_file():
    # header 영역과 calibration 영역이 쓰여진 덤프파일을 읽어서 바이트 버퍼에 담습니다. -> byte_buffer
    header_and_calibration_dump_filename = 'S219_231C1D0705CAACA0004003603D.dump'
    header_and_calibration_dump_fullpath = Path(__file__).absolute().parent.joinpath(
        header_and_calibration_dump_filename)

    file = open(header_and_calibration_dump_fullpath, 'rb')
    byte_buffer = bytearray(file.read())
    byte_buffer_size = len(byte_buffer)
    byte_buffer_ctype = ctypes.c_byte * len(byte_buffer)

    # board_offset을 수정할지 여부 (현재 사용안됨) -> 밸리데이션 설비에서 직접 board offset값을 수정해서 현재 사용 안하므로 무조건 False값 집어넣음
    update_board_offset = False

    # board offset f1 (update_board_offset 변수가 True일때만 수정)
    board_offset_f1 = 0x4470

    # board_offset f2 (update_board_offset 변수가 True일때만 수정)
    board_offset_f2 = 0xc042

    # Depth_Validation_Data_f1_QVGA_500mm
    Depth_Validation_Data_f1_QVGA_500mm = DepthValidationData500mm()
    Depth_Validation_Data_f1_QVGA_500mm.Depth_mean_of_center_ROI = 498.3032
    Depth_Validation_Data_f1_QVGA_500mm.Depth_mean_of_0dot6F_ROI_LT = 507.7704
    Depth_Validation_Data_f1_QVGA_500mm.Depth_mean_of_0dot6F_ROI_RT = 506.088867
    Depth_Validation_Data_f1_QVGA_500mm.Depth_mean_of_0dot6F_ROI_RB = 504.874268
    Depth_Validation_Data_f1_QVGA_500mm.Depth_mean_of_0dot6F_ROI_LB = 509.3713
    Depth_Validation_Data_f1_QVGA_500mm.Validation_Noise_of_Center_ROI = 0.6531719
    Depth_Validation_Data_f1_QVGA_500mm.Validation_Noise_of_0dot6F_ROI_LT = 1.47108459
    Depth_Validation_Data_f1_QVGA_500mm.Validation_Noise_of_0dot6F_ROI_RT = 1.29283249
    Depth_Validation_Data_f1_QVGA_500mm.Validation_Noise_of_0dot6F_ROI_RB = 1.6128937
    Depth_Validation_Data_f1_QVGA_500mm.Validation_Noise_of_0dot6F_ROI_LB = 0.9812971

    # VCSEL_Optical_Power_Data_f1
    VCSEL_Optical_Power_Data_f1 = VcselOpticalPowerData()
    VCSEL_Optical_Power_Data_f1.Center_ROI = 5291.36
    VCSEL_Optical_Power_Data_f1.Side_0dot6F_LB = 4128.8335
    VCSEL_Optical_Power_Data_f1.Side_0dot6F_LT = 3618.66
    VCSEL_Optical_Power_Data_f1.Side_0dot6F_RB = 4043.48
    VCSEL_Optical_Power_Data_f1.Side_0dot6F_RT = 3530.26

    # Depth_Validation_Data_f1_300mm
    Depth_Validation_Data_f1_300mm = DepthValidationData300mm()
    Depth_Validation_Data_f1_300mm.Depth_mean_of_center_ROI = 308.504028

    # Depth_Validation_Data_f2_QVGA_500mm
    Depth_Validation_Data_f2_QVGA_500mm = DepthValidationData500mm()
    Depth_Validation_Data_f2_QVGA_500mm.Depth_mean_of_center_ROI = 498.2147
    Depth_Validation_Data_f2_QVGA_500mm.Depth_mean_of_0dot6F_ROI_LT = 490.3748
    Depth_Validation_Data_f2_QVGA_500mm.Depth_mean_of_0dot6F_ROI_RT = 491.818268
    Depth_Validation_Data_f2_QVGA_500mm.Depth_mean_of_0dot6F_ROI_RB = 503.436279
    Depth_Validation_Data_f2_QVGA_500mm.Depth_mean_of_0dot6F_ROI_LB = 503.353882
    Depth_Validation_Data_f2_QVGA_500mm.Validation_Noise_of_Center_ROI = 2.43254113
    Depth_Validation_Data_f2_QVGA_500mm.Validation_Noise_of_0dot6F_ROI_LT = 2.84860063
    Depth_Validation_Data_f2_QVGA_500mm.Validation_Noise_of_0dot6F_ROI_RT = 2.1853807
    Depth_Validation_Data_f2_QVGA_500mm.Validation_Noise_of_0dot6F_ROI_RB = 3.39943862
    Depth_Validation_Data_f2_QVGA_500mm.Validation_Noise_of_0dot6F_ROI_LB = 1.59196615

    # VCSEL_Optical_Power_Data_f2
    VCSEL_Optical_Power_Data_f2 = VcselOpticalPowerData()
    VCSEL_Optical_Power_Data_f2.Center_ROI = 17915.5742
    VCSEL_Optical_Power_Data_f2.Side_0dot6F_LB = 15732.7734
    VCSEL_Optical_Power_Data_f2.Side_0dot6F_LT = 11666.2129
    VCSEL_Optical_Power_Data_f2.Side_0dot6F_RB = 14840.2129
    VCSEL_Optical_Power_Data_f2.Side_0dot6F_RT = 11050

    # Depth_Validation_Data_f2_300mm
    Depth_Validation_Data_f2_300mm = DepthValidationData300mm()
    Depth_Validation_Data_f2_300mm.Depth_mean_of_center_ROI = 303.356964

    # (출력) 최종 덤프가 저장될 메모리영역을 생성합니다. -> out_final_dump
    out_final_dump = bytearray(byte_buffer_size)
    out_final_dump_ctype = ctypes.c_byte * len(out_final_dump)

    # (출력) 최종 덤프 파일의 사이즈를 리턴합니다
    out_file_dump_size = [0]

    # (출력) lens_calibration_checksum 수정 여부를 리턴합니다.
    #         - Tof_Calibration.exe 프로그램의 버그로 인해 우회하려고 만든 변수입니다. -> 버그 내용 : Lens Calibration checksum(0x1662)이 잘못된 값으로 쓰여지던 버그 -> 현재 버그 수정돼서 사용안됨
    ref_out_modify_lens_calibration_checksum2 = [False]

    # lens_calibration_checksum2 값이 잘못돼있으면 수정할지 여부. (현재 사용안됨)
    update_lens_calibration_checksum2 = False

    result = VST_EEPROM_PARSER.EX_EepromCreateFinalDumpUsingHeaderAndCalibrationDumpMemory(
        byte_buffer_ctype.from_buffer(byte_buffer),
        byte_buffer_size,
        board_offset_f1,
        board_offset_f2,
        Depth_Validation_Data_f1_QVGA_500mm,
        VCSEL_Optical_Power_Data_f1,
        Depth_Validation_Data_f1_300mm,
        Depth_Validation_Data_f2_QVGA_500mm,
        VCSEL_Optical_Power_Data_f2,
        Depth_Validation_Data_f2_300mm,
        out_final_dump_ctype.from_buffer(out_final_dump),
        out_file_dump_size,
        ref_out_modify_lens_calibration_checksum2,
        update_lens_calibration_checksum2,
        update_board_offset)

    # result = True 성공, False 실패
    if result == False:
        # final dump 생성에 실패했을때 error code와 error message 출력
        error_code = VST_EEPROM_PARSER.EX_GetLastErrorCode()
        error_message = VST_EEPROM_PARSER.EX_GetLastErrorMessage()
        print(f"error 발생!\n  -> Error_code = {error_code}, error_message = {error_message}")
        sys.exit(-1)

    # (출력) 덤프 내용 파일에 쓰기
    final_dump_path = 'final_dump_test.dump'
    with open(final_dump_path, 'wb') as f:
        write_size = f.write(out_final_dump)
        if write_size == byte_buffer_size:
            print(f'최종 덤프 파일 쓰기 성공 : {final_dump_path}')
        else:
            print(f'최종 덤프 파일 쓰기 실패')



def get_header_and_calibration_buffer_from_eeprom() -> bytearray:
    simmian = python_simmian_api.Simmian()
    list = [0x0000 for i in range(VST_EEPROM_PARSER.EEPROM_CAL_MAP_SIZE)]

    ncount = 0

    for i in range(VST_EEPROM_PARSER.EEPROM_START_ADDRESS, VST_EEPROM_PARSER.EEPROM_CALIBRATIONDATA_END_ADDRESS+1):
        str_hex = "0x%0.4X" % i
        temp = simmian.ReadI2C(0xA0, str_hex, 1)
        list[i] = temp
        # list[i] = format(temp, '02X')
        print(f'[{ncount}] EEPROM 번지 : {str_hex} -> 값 {hex(temp)} 읽기 성공!')
        ncount += 1

    to_byte_array = bytearray(list)
    return to_byte_array


def convert_full_eeprom_size_header_and_calibration(original_data: bytearray) -> bytearray:
    original_data.extend([0 for i in range(0x0700)])
    return original_data


def read_eeprom_data_from_eeprom_memory():
    eeprom_dump_size = 0x2000
    sim = python_simmian_api.Simmian()
    list = [0x0000 for i in range(eeprom_dump_size)]
    # list = range(1899)

    for i in range(0x0000, eeprom_dump_size):
        str_hex = "0x%0.4X" % i
        temp = sim.ReadI2C(0xA0, str_hex, 1)
        list[i] = temp
        # list[i] = format(temp, '02X')

    to_byte_array = bytearray(list)
    return to_byte_array


def example_create_full_eeprom_dump_file():
    eeprom_dump = read_eeprom_data_from_eeprom_memory()

   # Bytearray can be cast to bytes
    immutable_bytes = bytes(eeprom_dump)

    # Write bytes to file
    with open("full_eeprom_test.dump", "wb") as binary_file:
        binary_file.write(immutable_bytes)


def format_bytes_as_hex(b: bytes, split = ' ') -> str:
    h = b.hex()
    return split.join(f'{a}{b}'.upper() for a, b in zip(h[0::2], h[1::2]))


def example_write_to_eeprom(eeprom_dump_path):
    file = open(eeprom_dump_path, 'rb')
    byte_buffer = bytearray(file.read())
    byte_buffer_size = len(byte_buffer)
    file.close()

    if byte_buffer_size != VST_EEPROM_PARSER.EEPROM_CAL_MAP_SIZE:
        raise Exception("invalid file")

    simmian = python_simmian_api.Simmian()
    for i in range(0x0000, VST_EEPROM_PARSER.EEPROM_CAL_MAP_SIZE, 2):
        str_address = "0x%0.4X" % i
        str_value = bytes([byte_buffer[i], byte_buffer[i + 1]])
        str_value_hex_format = f'0x{format_bytes_as_hex(str_value, split="")}'
        print(f'{i} = {str_value_hex_format}')

        result = simmian.WriteI2C(0xA0, str_address, str_value_hex_format)
        if result:
            print(f'EEPROM 번지: {str_address} -> 값 {str_value_hex_format} 쓰기 성공!')
        else:
            print(f'EEPROM 번지: {str_address} -> 값 {str_value_hex_format} 쓰기 실패!')


    for i in range(0, byte_buffer_size):
        print(i)


def factory_checksum(factorydata_f1, factorydata_f2, save_path_module):
    header_and_calibration_buffer = get_header_and_calibration_buffer_from_eeprom()

    # Bytearray can be cast to bytes
    immutable_bytes = bytes(header_and_calibration_buffer)

    # # Write bytes to file
    # with open("testtesttest.dump", "wb") as binary_file:
    #     binary_file.write(immutable_bytes)

    # header 영역과 calibration 영역이 쓰여진 덤프파일을 읽어서 바이트 버퍼에 담습니다. -> byte_buffer
    byte_buffer_size = len(header_and_calibration_buffer)
    byte_buffer_ctype = ctypes.c_byte * byte_buffer_size

    # Modulation Frequency F1 : START *********************************************************************************

    # Depth_Validation_Data_f1_300mm
    Depth_Validation_Data_f1_300mm = DepthValidationData300mm()
    Depth_Validation_Data_f1_300mm.Depth_mean_of_center_ROI = factorydata_f1[0]

    # Depth_Validation_Data_f1_QVGA_500mm
    Depth_Validation_Data_f1_QVGA_500mm = DepthValidationData500mm()
    Depth_Validation_Data_f1_QVGA_500mm.Depth_mean_of_center_ROI = factorydata_f1[1]
    Depth_Validation_Data_f1_QVGA_500mm.Depth_mean_of_0dot6F_ROI_LT = factorydata_f1[2]
    Depth_Validation_Data_f1_QVGA_500mm.Depth_mean_of_0dot6F_ROI_RT = factorydata_f1[3]
    Depth_Validation_Data_f1_QVGA_500mm.Depth_mean_of_0dot6F_ROI_RB = factorydata_f1[4]
    Depth_Validation_Data_f1_QVGA_500mm.Depth_mean_of_0dot6F_ROI_LB = factorydata_f1[5]
    Depth_Validation_Data_f1_QVGA_500mm.Validation_Noise_of_Center_ROI = factorydata_f1[6]
    Depth_Validation_Data_f1_QVGA_500mm.Validation_Noise_of_0dot6F_ROI_LT = factorydata_f1[7]
    Depth_Validation_Data_f1_QVGA_500mm.Validation_Noise_of_0dot6F_ROI_RT = factorydata_f1[8]
    Depth_Validation_Data_f1_QVGA_500mm.Validation_Noise_of_0dot6F_ROI_RB = factorydata_f1[9]
    Depth_Validation_Data_f1_QVGA_500mm.Validation_Noise_of_0dot6F_ROI_LB = factorydata_f1[10]

    # VCSEL_Optical_Power_Data_f1
    VCSEL_Optical_Power_Data_f1 = VcselOpticalPowerData()
    VCSEL_Optical_Power_Data_f1.Center_ROI = factorydata_f1[11]
    VCSEL_Optical_Power_Data_f1.Side_0dot6F_LT = factorydata_f1[12]
    VCSEL_Optical_Power_Data_f1.Side_0dot6F_RT = factorydata_f1[13]
    VCSEL_Optical_Power_Data_f1.Side_0dot6F_RB = factorydata_f1[14]
    VCSEL_Optical_Power_Data_f1.Side_0dot6F_LB = factorydata_f1[15]

    # 사용하지 않은 변수입니다. False 입력해주세요.
    # board_offset 수정 여부 -> 밸리데이션 설비에서 직접 board offset값을 수정해서 현재 사용 안하므로 무조건 False값 집어넣음
    update_board_offset = False
    # board offset f1 (update_board_offset 변수가 True일때만 수정됨)
    board_offset_f1 = factorydata_f1[17]

    # Modulation Frequency F1 : END ***********************************************************************************

    # Modulation Frequency F2 : START *********************************************************************************

    # Depth_Validation_Data_f2_300mm
    Depth_Validation_Data_f2_300mm = DepthValidationData300mm()
    Depth_Validation_Data_f2_300mm.Depth_mean_of_center_ROI = factorydata_f2[0]

    # Depth_Validation_Data_f2_QVGA_500mm
    Depth_Validation_Data_f2_QVGA_500mm = DepthValidationData500mm()
    Depth_Validation_Data_f2_QVGA_500mm.Depth_mean_of_center_ROI = factorydata_f2[1]
    Depth_Validation_Data_f2_QVGA_500mm.Depth_mean_of_0dot6F_ROI_LT = factorydata_f2[2]
    Depth_Validation_Data_f2_QVGA_500mm.Depth_mean_of_0dot6F_ROI_RT = factorydata_f2[3]
    Depth_Validation_Data_f2_QVGA_500mm.Depth_mean_of_0dot6F_ROI_RB = factorydata_f2[4]
    Depth_Validation_Data_f2_QVGA_500mm.Depth_mean_of_0dot6F_ROI_LB = factorydata_f2[5]
    Depth_Validation_Data_f2_QVGA_500mm.Validation_Noise_of_Center_ROI = factorydata_f2[6]
    Depth_Validation_Data_f2_QVGA_500mm.Validation_Noise_of_0dot6F_ROI_LT = factorydata_f2[7]
    Depth_Validation_Data_f2_QVGA_500mm.Validation_Noise_of_0dot6F_ROI_RT = factorydata_f2[8]
    Depth_Validation_Data_f2_QVGA_500mm.Validation_Noise_of_0dot6F_ROI_RB = factorydata_f2[9]
    Depth_Validation_Data_f2_QVGA_500mm.Validation_Noise_of_0dot6F_ROI_LB = factorydata_f2[10]

    # VCSEL_Optical_Power_Data_f2
    VCSEL_Optical_Power_Data_f2 = VcselOpticalPowerData()
    VCSEL_Optical_Power_Data_f2.Center_ROI = factorydata_f2[11]
    VCSEL_Optical_Power_Data_f2.Side_0dot6F_LT = factorydata_f2[12]
    VCSEL_Optical_Power_Data_f2.Side_0dot6F_RT = factorydata_f2[13]
    VCSEL_Optical_Power_Data_f2.Side_0dot6F_RB = factorydata_f2[14]
    VCSEL_Optical_Power_Data_f2.Side_0dot6F_LB = factorydata_f2[15]

    # 사용하지 않은 변수입니다. False 입력해주세요.
    # board_offset 수정 여부 -> 밸리데이션 설비에서 직접 board offset값을 수정해서 현재 사용 안하므로 무조건 False값 집어넣음
    update_board_offset = False
    # board_offset f2 (update_board_offset 변수가 True일때만 수정됨)
    board_offset_f2 = factorydata_f2[17]

    # Modulation Frequency F2 : END ***********************************************************************************

    # (출력) 최종 덤프가 저장될 메모리영역을 생성합니다. -> out_final_dump
    out_final_dump = bytearray(byte_buffer_size)
    out_final_dump_ctype = ctypes.c_byte * len(out_final_dump)

    # (출력) 최종 덤프 파일의 사이즈를 리턴합니다
    out_file_dump_size = [0]

    # 사용하지 않는 변수입니다. False로 입력해주세요.
    # (출력) lens_calibration_checksum 수정 여부를 리턴합니다.
    # Tof_Calibration.exe 프로그램의 버그로 인해 우회하려고 만든 변수입니다. -> 버그 내용 : Lens Calibration checksum(0x1662)이 잘못된 값으로 쓰여지던 버그
    ref_out_modify_lens_calibration_checksum2 = [False]

    # 사용하지 않는 변수입니다. False로 입력해주세요.
    # lens_calibration_checksum2 값이 잘못돼있으면 수정할지 여부.
    update_lens_calibration_checksum2 = False

    result = VST_EEPROM_PARSER.EX_EepromCreateFinalDumpUsingHeaderAndCalibrationDumpMemory(
        byte_buffer_ctype.from_buffer(header_and_calibration_buffer),
        byte_buffer_size,
        board_offset_f1,
        board_offset_f2,
        Depth_Validation_Data_f1_QVGA_500mm,
        VCSEL_Optical_Power_Data_f1,
        Depth_Validation_Data_f1_300mm,
        Depth_Validation_Data_f2_QVGA_500mm,
        VCSEL_Optical_Power_Data_f2,
        Depth_Validation_Data_f2_300mm,
        out_final_dump_ctype.from_buffer(out_final_dump),
        out_file_dump_size,
        ref_out_modify_lens_calibration_checksum2,
        update_lens_calibration_checksum2,
        update_board_offset)

    # result = True 성공, False 실패
    if result == False:
        # final dump 생성에 실패했을때 error code와 error message 출력
        error_code = VST_EEPROM_PARSER.EX_GetLastErrorCode()
        error_message = VST_EEPROM_PARSER.EX_GetLastErrorMessage()
        print(f"error 발생!\n  -> Error_code = {error_code}, error_message = {error_message}")
        return FAIL_OTP_WRITE #sys.exit(-1)

    # EEPROM에 데이터 쓰기
    bresult = 1
    simmian = python_simmian_api.Simmian()

    # todo ToF Data 영역 체크썸이 올바르지 않아서 다시 한다. 나중에 수정 꼭 !!!!
    str_address_a = 0x18FC
    str_address_b = 0x18FD
    str_address_c = 0x18FE
    str_address_d = 0x18FF

    str_value_a = bytes([out_final_dump[str_address_a]])
    str_value_a_hex_format = f'0x{format_bytes_as_hex(str_value_a, split="")}'
    is_write = simmian.WriteI2C(0xA0, "0x18FC", str_value_a_hex_format)
    time.sleep(0.010)  # 10ms
    if not is_write:
        print(f'EEPROM 번지: "0x18FC" -> 값 {str_value_a_hex_format} 쓰기 실패!')
        return FAIL_OTP_WRITE

    str_value_b = bytes([out_final_dump[str_address_b]])
    str_value_b_hex_format = f'0x{format_bytes_as_hex(str_value_b, split="")}'
    is_write = simmian.WriteI2C(0xA0, "0x18FD", str_value_b_hex_format)
    time.sleep(0.010)  # 10ms
    if not is_write:
        print(f'EEPROM 번지: "0x18FD" -> 값 {str_value_b_hex_format} 쓰기 실패!')
        return FAIL_OTP_WRITE

    str_value_c = bytes([out_final_dump[str_address_c]])
    str_value_c_hex_format = f'0x{format_bytes_as_hex(str_value_c, split="")}'
    is_write = simmian.WriteI2C(0xA0, "0x18FE", str_value_c_hex_format)
    time.sleep(0.010)  # 10ms
    if not is_write:
        print(f'EEPROM 번지: "0x18FE" -> 값 {str_value_c_hex_format} 쓰기 실패!')
        return FAIL_OTP_WRITE

    str_value_d = bytes([out_final_dump[str_address_d]])
    str_value_d_hex_format = f'0x{format_bytes_as_hex(str_value_d, split="")}'
    is_write = simmian.WriteI2C(0xA0, "0x18FF", str_value_d_hex_format)
    time.sleep(0.010)  # 10ms
    if not is_write:
        print(f'EEPROM 번지: "0x18FF" -> 값 {str_value_d_hex_format} 쓰기 실패!')
        return FAIL_OTP_WRITE

    # Factory 영역 쓰기
    for i in range(VST_EEPROM_PARSER.EEPROM_FACTORY_START_ADDRESS, VST_EEPROM_PARSER.EEPROM_CAL_MAP_SIZE, 2):
        str_address = "0x%0.4X" % i
        str_value = bytes([out_final_dump[i], out_final_dump[i + 1]])
        str_value_hex_format = f'0x{format_bytes_as_hex(str_value, split="")}'

        is_write = simmian.WriteI2C(0xA0, str_address, str_value_hex_format)
        time.sleep(0.010)  # 10ms
        if not is_write:
            print(f'Factory, Fail to write to EEPROM : {str_address} -> value {str_value_hex_format} ')
            return FAIL_OTP_WRITE

    # Todo check to header_data -> 0x0000 == 0x00 , 0x0001 == 0x00
    is_header_data = header_data_check(0)
    if is_header_data != PASS:
        return FAIL

    # return PASS

    # (출력) 덤프 내용 파일에 쓰기
    final_dump_path = save_path_module + '\\final_dump_test2.bin'
    with open(final_dump_path, 'wb') as f:
        write_size = f.write(out_final_dump)
        if write_size == byte_buffer_size:
            print(f'최종 덤프 파일 쓰기 성공 : {final_dump_path}')
        else:
            print(f'최종 덤프 파일 쓰기 실패')
    return PASS


def HEXLittleEndian(input, number):
    value = input  # input 은 DEC 타입이여야한다.

    b1_ = struct.pack('<i', value)[0]
    c1_ = format(b1_, '02x')

    b2_ = struct.pack('<i', value)[1]
    c2_ = format(b2_, '02x')

    d = f'0x%s' % (c1_)

    return d  # HEX 로 리턴한다


# 2023-05-08 : 배중호 , 헤더영역의 캘 공정 유무 FP 기록 후 체크섬 계산을 위한 바이트 크기 읽기
def get_header_buffer_from_eeprom(start_address , end_address) -> bytearray:
    simmian = python_simmian_api.Simmian()
    list = [start_address for i in range(end_address+1)]#list = [0x0000 for i in range(0x00fb)] # header area -> checksum 0x00FC ~ 0x00FF

    for i in range(start_address, end_address+1):#for i in range(0x0000, 0x00fb):
        str_hex = "0x%0.4X" % i
        temp = simmian.ReadI2C(0xA0, str_hex, 1)
        list[i] = temp
        str_address = "0x%0.4X" % i
        value = "0x%0.4X" % temp
        print(f'Header, read to eeprom : {str_address} -> value {value}')

    to_byte_array = bytearray(list)
    return to_byte_array


def get_caldata_buffer_from_eeprom(start_address , end_address) -> bytearray:
    simmian = python_simmian_api.Simmian()
    #list = [start_address for i in range(end_address+1)]
    list = [0 for i in range(256)]

    count = 0

    for i in range(start_address, end_address+1):
        str_hex = "0x%0.4X" % i
        temp = simmian.ReadI2C(0xA0, str_hex, 1)
        inumber = end_address-start_address-251
        list[inumber] = temp#list[i] = temp
        # list[i] = format(temp, '02X')
        # print(f'{count} -> address {str_hex} , value {temp} , hex{hex(temp)}')
        count += 1

    to_byte_array = bytearray(list)

    return to_byte_array


def get_caldata_buffer_from_eeprom_1(start_address , end_address) -> bytearray:
    simmian = python_simmian_api.Simmian()
    #list = [start_address for i in range(end_address+1)]
    list = [0 for i in range(255)]

    count = 0

    for i in range(start_address, end_address+1):
        str_hex = "0x%0.4X" % i
        temp = simmian.ReadI2C(0xA0, str_hex, 1)
        inumber = end_address-start_address-19
        list[inumber] = temp#list[i] = temp
        # list[i] = format(temp, '02X')
        # print(f'{count} -> address {str_hex} , value {temp} , hex{hex(temp)}')
        count += 1

    to_byte_array = bytearray(list)

    return to_byte_array


def get_caldata_buffer() :
    list_data = [0 for i in range(25)]

    list_data[0]    = get_caldata_buffer_from_eeprom(0x0100, 0x01fe)
    list_data[1]    = get_caldata_buffer_from_eeprom(0x01FF, 0x02fd)
    list_data[2]    = get_caldata_buffer_from_eeprom(0x02FE, 0x03fc)
    list_data[3]    = get_caldata_buffer_from_eeprom(0x03FD, 0x04fb)
    list_data[4]    = get_caldata_buffer_from_eeprom(0x04FC, 0x05fa)
    list_data[5]    = get_caldata_buffer_from_eeprom(0x05FB, 0x06f9)
    list_data[6]    = get_caldata_buffer_from_eeprom(0x06FA, 0x07f8)
    list_data[7]    = get_caldata_buffer_from_eeprom(0x07F9, 0x08f7)
    list_data[8]    = get_caldata_buffer_from_eeprom(0x08F8, 0x09f6)
    list_data[9]    = get_caldata_buffer_from_eeprom(0x09F7, 0x0af5)
    list_data[10]   = get_caldata_buffer_from_eeprom(0x0AF6, 0x0bf4)
    list_data[11]   = get_caldata_buffer_from_eeprom(0x0BF5, 0x0cf3)
    list_data[12]   = get_caldata_buffer_from_eeprom(0x0CF4, 0x0df2)
    list_data[13]   = get_caldata_buffer_from_eeprom(0x0DF3, 0x0ef1)
    list_data[14]   = get_caldata_buffer_from_eeprom(0x0EF2, 0x0ff0)
    list_data[15]   = get_caldata_buffer_from_eeprom(0x0FF1, 0x10ef)
    list_data[16]   = get_caldata_buffer_from_eeprom(0x10F0, 0x11ee)
    list_data[17]   = get_caldata_buffer_from_eeprom(0x11EF, 0x12ed)
    list_data[18]   = get_caldata_buffer_from_eeprom(0x12EE, 0x13ec)
    list_data[19]   = get_caldata_buffer_from_eeprom(0x13ED, 0x14eb)
    list_data[20]   = get_caldata_buffer_from_eeprom(0x14EC, 0x15ea)
    list_data[21]   = get_caldata_buffer_from_eeprom(0x15EB, 0x16e9)
    list_data[22]   = get_caldata_buffer_from_eeprom(0x16EA, 0x17e8)
    list_data[23]   = get_caldata_buffer_from_eeprom(0x17E9, 0x18e7)

    list_data[24]   = get_caldata_buffer_from_eeprom_1(0x18E8, 0x18fb)

    cal_data_buffer = list_data[0]+list_data[1] + list_data[2] + list_data[3] + list_data[4] + list_data[5]\
                      +list_data[6]+list_data[7]+list_data[8]+list_data[9]+list_data[10]+list_data[11]+list_data[12]\
                        +list_data[13]+list_data[14]+list_data[15]+list_data[16]+list_data[17]+list_data[18]+list_data[19]\
                        +list_data[20]+list_data[21]+list_data[22]+list_data[23]+list_data[24]

    return cal_data_buffer


def get_caldatacommon_buffer_from_eeprom(start_address , end_address) : #-> bytearray:
    simmian = python_simmian_api.Simmian()
    list = [start_address for i in range(end_address+1)]#list = [0x0100 for i in range(0x010b)]

    checksum = 0

    for i in range(start_address, end_address+1):#for i in range(0x0100, 0x010b):
        str_hex = "0x%0.4X" % i
        temp = simmian.ReadI2C(0xA0, str_hex, 1)
        list[i] = temp
        # list[i] = format(temp, '02X')
        str_address = "0x%0.4X" % i
        value = "0x%0.4X" % temp
        print(f'TOF_DATA, read to eeprom : {str_address} -> value {value}')
        checksum += temp

    #to_byte_array = bytearray(list)

    return checksum



def header_area_cal_flag(bresult):
    # 1. Header Checksum (0x00FC ~ 0x00FF) 에 #2의 값을 기록한다. 0X11 CAL 함 , 0XFF CAL 안 함. **************************
    # Temperature CAL   0x00CA , 0x00CB
    # Wiggling CAL      0x00CC , 0x00CD
    # Fppn CAL          0x00CE , 0x00CF
    # Lens CAL          0x00D0 , 0x00D1

    simmian = python_simmian_api.Simmian()

    re = simmian.GetBoardCount()
    if re == 0:  # 인식된 보드가 없을 때 '0' 으로 리턴된다.
        return 100

    if bresult == 0: # 캘 공정이 올바르게 완료가 되었고, 캘 계수가 e2p에 쓰기 완료 된 상태임
        result = simmian.WriteI2C(0xA0, "0x00CA", "0x11FF")
        time.sleep(0.010)  # 10ms
        if result:
            bresult = 0
        else:
            print(f'failed write to eeprom !!! ')
            return 103

        result = simmian.WriteI2C(0xA0, "0x00CC", "0x11FF")
        time.sleep(0.010)  # 10ms
        if result:
            bresult = 0
        else:
            print(f'failed write to eeprom !!! ')
            return 103

        result = simmian.WriteI2C(0xA0, "0x00CE", "0x11FF")
        time.sleep(0.010)  # 10ms
        if result:
            bresult = 0
        else:
            print(f'failed write to eeprom !!! ')
            return 103

        result = simmian.WriteI2C(0xA0, "0x00D0", "0x11FF")
        time.sleep(0.010)  # 10ms
        if result:
            bresult = 0
        else:
            print(f'failed write to eeprom !!! ')
            return 103

    else: # 캘 공정이 올바르게 완료가 되지 않았음.
        result = simmian.WriteI2C(0xA0, "0x00CA", "0xFFFF")
        time.sleep(0.010)  # 10ms
        if result:
            bresult = 0
        else:
            print(f'failed write to eeprom !!! ')
            return 103

        result = simmian.WriteI2C(0xA0, "0x00CC", "0xFFFF")
        time.sleep(0.010)  # 10ms
        if result:
            bresult = 0
        else:
            print(f'failed write to eeprom !!! ')
            return 103

        result = simmian.WriteI2C(0xA0, "0x00CE", "0xFFFF")
        time.sleep(0.010)  # 10ms
        if result:
            bresult = 0
        else:
            print(f'failed write to eeprom !!! ')
            return 103

        result = simmian.WriteI2C(0xA0, "0x00D0", "0xFFFF")
        time.sleep(0.010)  # 10ms
        # re_read = simmian.ReadI2C(0xA0, "0x00D0", 2)
        if result:
            bresult = 0
        else:
            print(f'failed write to eeprom !!! ')
            return 103

    re_read = simmian.ReadI2C(0xA0, "0x00CA", 2)
    print(f'Temperature CAL flag -> {hex(re_read)}')

    re_read = simmian.ReadI2C(0xA0, "0x00CC", 2)
    print(f'Wiggling CAL flag -> {hex(re_read)}')

    re_read = simmian.ReadI2C(0xA0, "0x00CE", 2)
    print(f'Fppn CAL flag -> {hex(re_read)}')

    re_read = simmian.ReadI2C(0xA0, "0x00D0", 2)
    print(f'Lens CAL flag -> {hex(re_read)}')

    return bresult


def header_checksum():
    print(f'Start calculating the checksum of the header area... 0x0000_0000 0x0000_00FF')
    simmian = python_simmian_api.Simmian()

    re = simmian.GetBoardCount()
    if re == 0:  # 인식된 보드가 없을 때 '0' 으로 리턴된다.
        return FAIL_SIMMIAN_INIT

    # Todo check -> 0x0000 == 0x00 , 0x0002 == 0x00
    readvaluep = simmian.ReadI2C(0xA0, "0x0000", 1)
    readvalueq = simmian.ReadI2C(0xA0, "0x0002", 1)

    if readvaluep != 0 or readvalueq != 0:
        simmian.WriteI2C(0xA0, "0x0000", '0x00')
        time.sleep(0.010)
        simmian.WriteI2C(0xA0, "0x0002", '0x00')
        time.sleep(0.010)

        readvaluep = simmian.ReadI2C(0xA0, "0x0000", 1)
        readvalueq = simmian.ReadI2C(0xA0, "0x0002", 1)

        if readvaluep != 0 or readvalueq != 0:
            print(f'FAIL, An incorrect value is recorded at address 0x0000 -> {hex(readvaluep)}.')
            print(f'FAIL, An incorrect value is recorded at address 0x0000 -> {hex(readvalueq)}.')
            return FAIL_OTP_WRITE
    else:
        print(f'')

    # 2. 헤더 영역의 체크섬(0x00FC ~ 0x00FF)을 제외하고 바이트를 읽어온다 ****************************************************
    header_buffer = get_header_buffer_from_eeprom(0x0000, 0x00fb)

    # 3. Checksum -> Header Checksum 계산한다. *************************************************************************
    str_value_hex_format = [0 for i in range(5)]
    checksum = (zlib.crc32(header_buffer) & 0xffffffff)
    print(f'result : {checksum} , result(hex) : {hex(checksum)}')
    hex_checksum = f'{"0x%08x" % (zlib.crc32(header_buffer) & 0xffffffff)}'
    print(f'result : hex_checksum -> {hex_checksum}')
    for i in range(0, 5):
        str_value_hex_format[i] = f'0x{hex_checksum[(i*2):((i*2)+2)]}'

    # 4. 계산된 checksum 값을 기록한다. ::: Header Checksum -> 0x00FC ~ 0x00FF *******************************************
    # 4-2. e2p 에 기록 (리틀엔디안으로 기록하기위해서 str_value_hex_format[] 을 거꾸로 쓴다. **********************************
    is_write = False
    is_write = simmian.WriteI2C(0xA0, "0x00FC", str_value_hex_format[4])
    time.sleep(0.010)  # 10ms
    if not is_write:
        print(f'failed write to eeprom !!! ')
        return FAIL_OTP_WRITE
    read_fc = simmian.ReadI2C(0xA0, "0x00FC", 1)
    time.sleep(0.010)

    is_write = simmian.WriteI2C(0xA0, "0x00FD", str_value_hex_format[3])
    time.sleep(0.010)  # 10ms
    if not is_write:
        print(f'failed write to eeprom !!! ')
        return FAIL_OTP_WRITE
    read_fd = simmian.ReadI2C(0xA0, "0x00FD", 1)
    time.sleep(0.010)

    is_write = simmian.WriteI2C(0xA0, "0x00FE", str_value_hex_format[2])
    time.sleep(0.010)  # 10ms
    if not is_write:
        print(f'failed write to eeprom !!! ')
        return FAIL_OTP_WRITE
    read_fe = simmian.ReadI2C(0xA0, "0x00FE", 1)
    time.sleep(0.010)

    is_write = simmian.WriteI2C(0xA0, "0x00FF", str_value_hex_format[1])
    time.sleep(0.010)  # 10ms
    if not is_write:
        print(f'failed write to eeprom !!! ')
        return FAIL_OTP_WRITE
    read_ff = simmian.ReadI2C(0xA0, "0x00FF", 1)
    time.sleep(0.010)

    print(f'result : {hex_checksum} -> {hex(read_fc)} / {hex(read_fd)} / {hex(read_fe)} / {hex(read_ff)}')
    print(f'Finsh calculating the checksum of the header area... 0x0000_0000 0x0000_00FF')

    # Todo check -> 0x0000 == 0x00 , 0x0002 == 0x00
    readvaluep = simmian.ReadI2C(0xA0, "0x0000", 1)
    readvalueq = simmian.ReadI2C(0xA0, "0x0002", 1)
    if readvaluep != 0 or readvalueq != 0:
        print(f'FAIL, An incorrect value is recorded at address 0x0000 -> {hex(readvaluep)}.')
        print(f'FAIL, An incorrect value is recorded at address 0x0000 -> {hex(readvalueq)}.')
        return FAIL_OTP_WRITE

    return PASS


def header_data_check(protect_mode):
    UNLOCK = 0
    UNLOCK_VALUE = 160  # 0xA0
    LOCK = 1
    LOCK_VALUE = 161  # 0xA1

    simmian = python_simmian_api.Simmian()

    if protect_mode == LOCK:
        is_write = simmian.WriteI2C(0xA0, "0xE000", '0xA0')  # Todo, 주소: 0xE000, 값: 0xA0 (int)160
        time.sleep(0.010)
        if not is_write:
            print(f'failed write to eeprom !!! ')
            return FAIL_OTP_WRITE

        is_read = simmian.ReadI2C(0xA0, "0xE000", 1)
        if is_read != UNLOCK_VALUE:  # Todo 0xA0 (int)160
            print(f'FAIL, Write protection unlocking. ')
            return FAIL_OTP_WRITE  # 103

    # Todo check -> 0x0000 == 0x00 , 0x0002 == 0x00
    readvaluep = simmian.ReadI2C(0xA0, "0x0000", 1)
    readvalueq = simmian.ReadI2C(0xA0, "0x0002", 1)

    if readvaluep != 0 or readvalueq != 0:
        is_write = simmian.WriteI2C(0xA0, "0x0000", '0x00') # Todo 0x0000 에 0x00 을 기록하고
        time.sleep(0.010)
        if not is_write:
            print(f'failed write to eeprom !!! ')
            return FAIL_OTP_WRITE

        is_write = simmian.WriteI2C(0xA0, "0x0002", '0x00') # Todo 0x0002 에 0x00 을 기록하고
        time.sleep(0.010)
        if not is_write:
            print(f'failed write to eeprom !!! ')
            return FAIL_OTP_WRITE

        # Todo 0x0000 , 0x0002 의 값을 읽어오고,
        readvaluep = simmian.ReadI2C(0xA0, "0x0000", 1)
        readvalueq = simmian.ReadI2C(0xA0, "0x0002", 1)

        if readvaluep != 0 or readvalueq != 0:
            print(f'FAIL, An incorrect value is recorded at address 0x0000 -> {hex(readvaluep)}.')
            print(f'FAIL, An incorrect value is recorded at address 0x0000 -> {hex(readvalueq)}.')
            return FAIL_OTP_WRITE
    else:
        pass

    if protect_mode == LOCK: # Todo, e2p 'unlock' 상태이면, 공정 마지막에 체크썸을 한 번만 한다.
        is_header_checksum = header_checksum()
        if is_header_checksum != PASS:
            print(f'FAIL, do not finsh checksum of header area !!!')
            return FAIL_OTP_WRITE

    if protect_mode == LOCK: # Todo, e2p 'lock'이면, 시작할 때, 'unlock -> lock'한다.
        is_write = simmian.WriteI2C(0xA0, "0xE000", '0xA1')  # TODO, 주소: 0xE000, 값: 0xA1 (int)161
        time.sleep(0.010)
        if not is_write:
            print(f'failed write to eeprom !!! ')
            return FAIL_OTP_WRITE

        is_read = simmian.ReadI2C(0xA0, "0xE000", 1)
        if is_read != LOCK_VALUE:  # TODO 0xA1 (int)161
            print(f'FAIL, Write protection locking. ')
            return FAIL_OTP_WRITE

    return PASS


def tofcal_common_checksum():
    print(f'Start calculating the checksum of the ToF Data(-> Common)... 0x0000_0100 0x0000_010B')

    simmian = python_simmian_api.Simmian()

    re = simmian.GetBoardCount()
    if re == 0:  # 인식된 보드가 없을 때 '0' 으로 리턴된다.
        return FAIL_SIMMIAN_INIT

    # 2. ToF Data 영역의 체크섬(0x18FC ~ 0x18FF)을 제외하고 바이트를 읽어온다 ************************************************
    caldata_common_checksum = get_caldatacommon_buffer_from_eeprom(0x0100, 0x010b)

    # 3. Checksum -> ToF Data Checksum 계산한다. ************************************************************************
    caldata_common_checksum &= 0xff # ex (int)746 -> &= 0xff 하면 (int)234
    caldata_common_checksum %= 0xff
    caldata_common_checksum += 0x01 # ex (int)234 -> += 0x01 하면 (int)235

    str_hex = "0x%0.2X" % caldata_common_checksum
    print(f'result : {caldata_common_checksum} , result(hex) : {str_hex}')

    # 4. 계산된 checksum 값을 기록한다. ::: ToF Data Checksum -> 0x18FC ~ 0x18FF ******************************************
    is_write = False
    is_write = simmian.WriteI2C(0xA0, "0x010c", str_hex)
    time.sleep(0.010)  # 10ms
    if not is_write:
        print(f'failed write to eeprom !!! ')
        return FAIL_OTP_WRITE
    re_read1 = simmian.ReadI2C(0xA0, "0x010c", 1)
    time.sleep(0.010)

    print(f'result : {caldata_common_checksum} -> hex {hex(re_read1)} ')
    print(f'Finsh calculating the checksum of the ToF Data(-> Common)... 0x0000_0100 0x0000_010B')

    return PASS


def tofcal_checksum():
    print(f'Start calculating the checksum of the Calibration Data... 0x0000_0100 0x0000_18FB')
    simmian = python_simmian_api.Simmian()

    re = simmian.GetBoardCount()
    if re == 0:  # 인식된 보드가 없을 때 '0' 으로 리턴된다.
        return FAIL_OTP_WRITE

    # 2. ToF Data 영역의 체크섬(0x18FC ~ 0x18FF)을 제외하고 바이트를 읽어온다 ************************************************
    caldata_buffer = get_caldata_buffer()

    # 3. Checksum -> ToF Data Checksum 계산한다. ************************************************************************
    str_value_hex_format = [0 for i in range(5)]
    checksum = (zlib.crc32(caldata_buffer) & 0xffffffff)
    print(f'result : {checksum} , result(hex) : {hex(checksum)}')
    hex_checksum = f'{"0x%08x" % (zlib.crc32(caldata_buffer) & 0xffffffff)}'
    print(f'result : hex_checksum -> {hex_checksum}')
    for i in range(0, 5):
        str_value_hex_format[i] = f'0x{hex_checksum[(i * 2):((i * 2) + 2)]}'

    # 4. 계산된 checksum 값을 기록한다. ::: ToF Data Checksum -> 0x18FC ~ 0x18FF ******************************************
    is_write = False
    is_write = simmian.WriteI2C(0xA0, "0x18FC", str_value_hex_format[4])
    time.sleep(0.010)  # 10ms
    if not is_write:
        print(f'failed write to eeprom !!! ')
        return FAIL_OTP_WRITE
    read_fc = simmian.ReadI2C(0xA0, "0x18FC", 1)
    time.sleep(0.010)

    is_write = simmian.WriteI2C(0xA0, "0x18FD", str_value_hex_format[3])
    time.sleep(0.010)  # 10ms
    if not is_write:
        print(f'failed write to eeprom !!! ')
        return FAIL_OTP_WRITE
    read_fd = simmian.ReadI2C(0xA0, "0x18FD", 1)
    time.sleep(0.010)

    is_write = simmian.WriteI2C(0xA0, "0x18FE", str_value_hex_format[2])
    time.sleep(0.010)  # 10ms
    if not is_write:
        print(f'failed write to eeprom !!! ')
        return FAIL_OTP_WRITE
    read_fe = simmian.ReadI2C(0xA0, "0x18FE", 1)
    time.sleep(0.010)

    is_write = simmian.WriteI2C(0xA0, "0x18FF", str_value_hex_format[1])
    time.sleep(0.010)  # 10ms
    if not is_write:
        print(f'failed write to eeprom !!! ')
        return FAIL_OTP_WRITE
    read_ff = simmian.ReadI2C(0xA0, "0x18FF", 1)
    time.sleep(0.010)

    print(
        f'result : {hex_checksum} -> littleendian {hex(read_fc)} , {hex(read_fd)} , {hex(read_fe)} , {hex(read_ff)}')

    print(f'Finsh calculating the checksum of the Calibration Data... 0x0000_0100 0x0000_18FB')

    return PASS


if __name__ == "__main__":
    #example_write_factory_area()

    # [Cal] 캘 공정 flag
    #example_write_header_area_cal_flag(bresult = 1)


    # [Val] Val에서 캘 flag와 apc_check를 수정했기때문에 헤더영역의 체크썸을 다시 계산해줘야한다.
    #example_write_header_area_checksum()
    #example_write_caldatacommon_area_checksum()
    #example_write_caldata_area_checksum()

    JudgeResult_f1 = [0 for i in range(21)]
    JudgeResult_f2 = [0 for i in range(21)]
    path = f'C:\\LSI_VST63D'

    #example_write_factory_area(JudgeResult_f1, JudgeResult_f2, path)

    sys.exit(-1)
