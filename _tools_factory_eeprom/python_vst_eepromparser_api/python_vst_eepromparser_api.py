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

    for i in range(VST_EEPROM_PARSER.EEPROM_START_ADDRESS, VST_EEPROM_PARSER.EEPROM_CALIBRATIONDATA_END_ADDRESS+1):
        str_hex = "0x%0.4X" % i
        temp = simmian.ReadI2C(0xA0, str_hex, 1)
        list[i] = temp
        # list[i] = format(temp, '02X')

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


def example_write_factory_area():
    header_and_calibration_buffer = get_header_and_calibration_buffer_from_eeprom()

    # Bytearray can be cast to bytes
    immutable_bytes = bytes(header_and_calibration_buffer)

    # # Write bytes to file
    # with open("testtesttest.dump", "wb") as binary_file:
    #     binary_file.write(immutable_bytes)

    # header 영역과 calibration 영역이 쓰여진 덤프파일을 읽어서 바이트 버퍼에 담습니다. -> byte_buffer
    byte_buffer_size = len(header_and_calibration_buffer)
    byte_buffer_ctype = ctypes.c_byte * byte_buffer_size

    # 사용하지 않은 변수입니다. False 입력해주세요.
    # board_offset 수정 여부 -> 밸리데이션 설비에서 직접 board offset값을 수정해서 현재 사용 안하므로 무조건 False값 집어넣음
    update_board_offset = False

    # board offset f1 (update_board_offset 변수가 True일때만 수정됨)
    board_offset_f1 = 0x0000

    # board_offset f2 (update_board_offset 변수가 True일때만 수정됨)
    board_offset_f2 = 0x0000

    # Depth_Validation_Data_f1_QVGA_500mm
    Depth_Validation_Data_f1_QVGA_500mm = DepthValidationData500mm()
    Depth_Validation_Data_f1_QVGA_500mm.Depth_mean_of_center_ROI = 500.6121724
    Depth_Validation_Data_f1_QVGA_500mm.Depth_mean_of_0dot6F_ROI_LT = 505.050618489583
    Depth_Validation_Data_f1_QVGA_500mm.Depth_mean_of_0dot6F_ROI_RT = 507.213795979817
    Depth_Validation_Data_f1_QVGA_500mm.Depth_mean_of_0dot6F_ROI_RB = 509.127838134765
    Depth_Validation_Data_f1_QVGA_500mm.Depth_mean_of_0dot6F_ROI_LB = 504.611206054687
    Depth_Validation_Data_f1_QVGA_500mm.Validation_Noise_of_Center_ROI = 3.01812084515889
    Depth_Validation_Data_f1_QVGA_500mm.Validation_Noise_of_0dot6F_ROI_LT = 2.24987395604451
    Depth_Validation_Data_f1_QVGA_500mm.Validation_Noise_of_0dot6F_ROI_RT = 1.43647293249766
    Depth_Validation_Data_f1_QVGA_500mm.Validation_Noise_of_0dot6F_ROI_RB = 2.4546783765157
    Depth_Validation_Data_f1_QVGA_500mm.Validation_Noise_of_0dot6F_ROI_LB = 3.23293113708496

    # VCSEL_Optical_Power_Data_f1
    VCSEL_Optical_Power_Data_f1 = VcselOpticalPowerData()
    VCSEL_Optical_Power_Data_f1.Center_ROI = 4352.29333333333
    VCSEL_Optical_Power_Data_f1.Side_0dot6F_LB = 5426.66666666666
    VCSEL_Optical_Power_Data_f1.Side_0dot6F_LT = 5462.66666666666
    VCSEL_Optical_Power_Data_f1.Side_0dot6F_RB = 5131.30666666666
    VCSEL_Optical_Power_Data_f1.Side_0dot6F_RT = 5155.12

    # Depth_Validation_Data_f1_300mm
    Depth_Validation_Data_f1_300mm = DepthValidationData300mm()
    Depth_Validation_Data_f1_300mm.Depth_mean_of_center_ROI = 311.305541992187

    # Depth_Validation_Data_f2_QVGA_500mm
    Depth_Validation_Data_f2_QVGA_500mm = DepthValidationData500mm()
    Depth_Validation_Data_f2_QVGA_500mm.Depth_mean_of_center_ROI = 502.45361328125
    Depth_Validation_Data_f2_QVGA_500mm.Depth_mean_of_0dot6F_ROI_LT = 500.970469156901
    Depth_Validation_Data_f2_QVGA_500mm.Depth_mean_of_0dot6F_ROI_RT = 507.235727945963
    Depth_Validation_Data_f2_QVGA_500mm.Depth_mean_of_0dot6F_ROI_RB = 513.992329915364
    Depth_Validation_Data_f2_QVGA_500mm.Depth_mean_of_0dot6F_ROI_LB = 507.666015625
    Depth_Validation_Data_f2_QVGA_500mm.Validation_Noise_of_Center_ROI = 5.3678175608317
    Depth_Validation_Data_f2_QVGA_500mm.Validation_Noise_of_0dot6F_ROI_LT = 5.1181747118632
    Depth_Validation_Data_f2_QVGA_500mm.Validation_Noise_of_0dot6F_ROI_RT = 3.2521112759908
    Depth_Validation_Data_f2_QVGA_500mm.Validation_Noise_of_0dot6F_ROI_RB = 4.08844947814941
    Depth_Validation_Data_f2_QVGA_500mm.Validation_Noise_of_0dot6F_ROI_LB = 3.53293593724568

    # VCSEL_Optical_Power_Data_f2
    VCSEL_Optical_Power_Data_f2 = VcselOpticalPowerData()
    VCSEL_Optical_Power_Data_f2.Center_ROI = 15834.2666666666
    VCSEL_Optical_Power_Data_f2.Side_0dot6F_LB = 17083.52
    VCSEL_Optical_Power_Data_f2.Side_0dot6F_LT = 17198.56
    VCSEL_Optical_Power_Data_f2.Side_0dot6F_RB = 18534.8533333333
    VCSEL_Optical_Power_Data_f2.Side_0dot6F_RT = 19567.5733333333

    # Depth_Validation_Data_f2_300mm
    Depth_Validation_Data_f2_300mm = DepthValidationData300mm()
    Depth_Validation_Data_f2_300mm.Depth_mean_of_center_ROI = 293.820190429687

    # (출력) 최종 덤프가 저장될 메모리영역을 생성합니다. -> out_final_dump
    out_final_dump = bytearray(byte_buffer_size)
    out_final_dump_ctype = ctypes.c_byte * len(out_final_dump)

    # (출력) 최종 덤프 파일의 사이즈를 리턴합니다
    out_file_dump_size = [0]

    # 사용하지 않는 변수입니다. False로 입력해주세요.
    # (출력) lens_calibration_checksum 수정 여부를 리턴합니다.
    #         - Tof_Calibration.exe 프로그램의 버그로 인해 우회하려고 만든 변수입니다. -> 버그 내용 : Lens Calibration checksum(0x1662)이 잘못된 값으로 쓰여지던 버그
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
        sys.exit(-1)


    # EEPROM에 데이터 쓰기
    simmian = python_simmian_api.Simmian()
    for i in range(VST_EEPROM_PARSER.EEPROM_FACTORY_START_ADDRESS, VST_EEPROM_PARSER.EEPROM_CAL_MAP_SIZE, 2):
        str_address = "0x%0.4X" % i
        str_value = bytes([out_final_dump[i], out_final_dump[i + 1]])
        str_value_hex_format = f'0x{format_bytes_as_hex(str_value, split="")}'
        print(f'{i} = {str_value_hex_format}')

        result = simmian.WriteI2C(0xA0, str_address, str_value_hex_format)
        time.sleep(0.010)  # 10ms
        if result:
            print(f'EEPROM 번지: {str_address} -> 값 {str_value_hex_format} 쓰기 성공!')
        else:
            print(f'EEPROM 번지: {str_address} -> 값 {str_value_hex_format} 쓰기 실패!')


    # # (출력) 덤프 내용 파일에 쓰기
    # final_dump_path = 'final_dump_test2.dump'
    # with open(final_dump_path, 'wb') as f:
    #     write_size = f.write(out_final_dump)
    #     if write_size == byte_buffer_size:
    #         print(f'최종 덤프 파일 쓰기 성공 : {final_dump_path}')
    #     else:
    #         print(f'최종 덤프 파일 쓰기 실패')


if __name__ == "__main__":
    example_write_factory_area()