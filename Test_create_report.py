import pandas as pd  # pip install pandas
import python_simmian_api

JudgeResult_f1 = [0 for i in range(21)]
JudgeResult_f2 = [0 for i in range(21)]
gSensor_id_dec = [0 for i in range(13)]

simmian = python_simmian_api.Simmian()


def resultdata():
    JudgeResult_f1[16] = 0  # 100 MHz Result
    JudgeResult_f1[0] = 301.8609517
    JudgeResult_f1[1] = 498.0456543
    JudgeResult_f1[2] = 427.7941691
    JudgeResult_f1[3] = 424.9218852
    JudgeResult_f1[4] = 425.5151265
    JudgeResult_f1[5] = 421.0870667
    JudgeResult_f1[6] = 1.735324423
    JudgeResult_f1[7] = 2.980343342
    JudgeResult_f1[8] = 2.446365992
    JudgeResult_f1[9] = 2.94152379
    JudgeResult_f1[10] = 3.428522189
    JudgeResult_f1[11] = 6091.026667
    JudgeResult_f1[12] = 7464.013333
    JudgeResult_f1[13] = 7509.413333
    JudgeResult_f1[14] = 7053.586667
    JudgeResult_f1[15] = 7025.8
    JudgeResult_f1[17] = f'0x4687'
    JudgeResult_f1[18] = 811
    JudgeResult_f1[19] = 496

    JudgeResult_f2[16] = 0  # 100 MHz Result
    JudgeResult_f2[0] = 283.5784912
    JudgeResult_f2[1] = 499.4903463
    JudgeResult_f2[2] = 511.5600586
    JudgeResult_f2[3] = 512.5488485
    JudgeResult_f2[4] = 515.5334473
    JudgeResult_f2[5] = 514.1113281
    JudgeResult_f2[6] = 6.03793939
    JudgeResult_f2[7] = 7.422795137
    JudgeResult_f2[8] = 4.471993128
    JudgeResult_f2[9] = 5.021643162
    JudgeResult_f2[10] = 5.892681599
    JudgeResult_f2[11] = 15810.58667
    JudgeResult_f2[12] = 17183.62667
    JudgeResult_f2[13] = 17200.05333
    JudgeResult_f2[14] = 19236.85333
    JudgeResult_f2[15] = 20303.52
    JudgeResult_f2[17] = f'0xc45c'
    JudgeResult_f2[18] = 809
    JudgeResult_f2[19] = 809


def get_sensor_id():
    global gSensor_id_dec

    list = [0 for i in range(13)]

    gSensor_id_dec[0] = simmian.ReadI2C(0xA0, "0x00B9", 1)
    list[0] = format(gSensor_id_dec[0], '02X')
    # print(f'simmian readI2C 0x00B9 1 Byte  -> {temp} , hex -> {list[0]}')

    gSensor_id_dec[1] = simmian.ReadI2C(0xA0, "0x00BA", 1)
    list[1] = format(gSensor_id_dec[1], '02X')
    # print(f'simmian readI2C 0x00BA 1 Byte  -> {temp} , hex -> {list[1]}')

    gSensor_id_dec[2] = simmian.ReadI2C(0xA0, "0x00BB", 1)
    list[2] = format(gSensor_id_dec[2], '02X')
    # print(f'simmian readI2C 0x00BB 1 Byte  -> {temp} , hex -> {list[2]}')

    gSensor_id_dec[3] = simmian.ReadI2C(0xA0, "0x00BC", 1)
    list[3] = format(gSensor_id_dec[3], '02X')
    # print(f'simmian readI2C 0x00BC 1 Byte  -> {temp} , hex -> {list[3]}')

    gSensor_id_dec[4] = simmian.ReadI2C(0xA0, "0x00BD", 1)
    list[4] = format(gSensor_id_dec[4], '02X')
    # print(f'simmian readI2C 0x00BD 1 Byte  -> {temp} , hex -> {list[4]}')

    gSensor_id_dec[5] = simmian.ReadI2C(0xA0, "0x00BE", 1)
    list[5] = format(gSensor_id_dec[5], '02X')
    # print(f'simmian readI2C 0x00BE 1 Byte  -> {temp} , hex -> {list[5]}')

    gSensor_id_dec[6] = simmian.ReadI2C(0xA0, "0x00BF", 1)
    list[6] = format(gSensor_id_dec[6], '02X')
    # print(f'simmian readI2C 0x00BF 1 Byte  -> {temp} , hex -> {list[6]}')

    gSensor_id_dec[7] = simmian.ReadI2C(0xA0, "0x00C0", 1)
    list[7] = format(gSensor_id_dec[7], '02X')
    # print(f'simmian readI2C 0x00C0 1 Byte  -> {temp} , hex -> {list[7]}')

    gSensor_id_dec[8] = simmian.ReadI2C(0xA0, "0x00C1", 1)
    list[8] = format(gSensor_id_dec[8], '02X')
    # print(f'simmian readI2C 0x00C1 1 Byte  -> {temp} , hex -> {list[8]}')

    gSensor_id_dec[9] = simmian.ReadI2C(0xA0, "0x00C2", 1)
    list[9] = format(gSensor_id_dec[9], '02X')
    # print(f'simmian readI2C 0x00C2 1 Byte  -> {temp} , hex -> {list[9]}')

    gSensor_id_dec[10] = simmian.ReadI2C(0xA0, "0x00C3", 1)
    list[10] = format(gSensor_id_dec[10], '02X')
    # print(f'simmian readI2C 0x00C3 1 Byte  -> {temp} , hex -> {list[10]}')

    gSensor_id_dec[11] = simmian.ReadI2C(0xA0, "0x00C4", 1)
    list[11] = format(gSensor_id_dec[11], '02X')
    # print(f'simmian readI2C 0x00C4 1 Byte  -> {temp} , hex -> {list[11]}')

    gSensor_id_dec[12] = simmian.ReadI2C(0xA0, "0x00C5", 1)
    list[12] = format(gSensor_id_dec[12], '02X')
    # print(f'simmian readI2C 0x00C5 1 Byte  -> {temp} , hex -> {list[12]}')

    str_sensorid = "".join(list)

    return str_sensorid


if __name__ == "__main__":

    simmian = python_simmian_api.Simmian()
    simmian.Play()

    Path = f'c:/LSI_VST63D/4_Validation/save/231C1D0705AD89A0004003603D'
    gSensor_id = get_sensor_id() #gSensor_id = f'231C1D0705AA9FA0004003603D'

    resultdata()

    result_100mhz = 112
    result_20mhz = 0

    if result_100mhz == 0 and result_20mhz == 0:
        JudgeResult_f1[16] = 0
        JudgeResult_f2[16] = 0
        JudgeResult = 0
    else:
        JudgeResult_f1[16] = result_100mhz
        JudgeResult_f2[16] = result_20mhz
        JudgeResult = 1

    # report 엑셀 출력
    df1 = pd.DataFrame(
        [
            [JudgeResult_f1[16],
             JudgeResult_f1[0],
             JudgeResult_f1[1], JudgeResult_f1[2], JudgeResult_f1[3], JudgeResult_f1[4], JudgeResult_f1[5],
             JudgeResult_f1[6], JudgeResult_f1[7], JudgeResult_f1[8], JudgeResult_f1[9], JudgeResult_f1[10],
             JudgeResult_f1[11], JudgeResult_f1[12], JudgeResult_f1[13], JudgeResult_f1[14],
             JudgeResult_f1[15],
             JudgeResult_f1[17],  # gBoard_offset_f1 -> find offset( ) 에서 global offset 을 계산한다.
             JudgeResult_f1[18],
             JudgeResult_f1[19],
             ''],
            [JudgeResult_f2[16],
             JudgeResult_f2[0],
             JudgeResult_f2[1], JudgeResult_f2[2], JudgeResult_f2[3], JudgeResult_f2[4], JudgeResult_f2[5],
             JudgeResult_f2[6], JudgeResult_f2[7], JudgeResult_f2[8], JudgeResult_f2[9], JudgeResult_f2[10],
             JudgeResult_f2[11], JudgeResult_f2[12], JudgeResult_f2[13], JudgeResult_f2[14],
             JudgeResult_f2[15],
             JudgeResult_f2[17],  # gBoard_offset_f2 -> find offset( ) 에서 global offset 을 계산한다.
             JudgeResult_f2[18],
             JudgeResult_f2[19],
             ''],
            [JudgeResult,
             ''],
            [gSensor_id,
             gSensor_id_dec[0], gSensor_id_dec[1], gSensor_id_dec[2], gSensor_id_dec[3], gSensor_id_dec[4],
             gSensor_id_dec[5], gSensor_id_dec[6], gSensor_id_dec[7], gSensor_id_dec[8], gSensor_id_dec[9],
             gSensor_id_dec[10], gSensor_id_dec[11], gSensor_id_dec[12],
             '']
        ],
        index=['100', '20', 'Result', 'SensorID'],
        columns=['Judge',
                 'Error_CT_300',
                 'Error_CT_500', 'Error_LT_500', 'Error_RT_500', 'Error_RB_500', 'Error_LB_500',
                 'Noise_CT_500', 'Noise_LT_500', 'Noise_RT_500', 'Noise_RB_500', 'Noise_LB_500',
                 'Intensity_CT_500', 'Intensity_LT_500', 'Intensity_RT_500', 'Intensity_RB_500',
                 'Intensity_LB_500',
                 'board_offset f1/f2',
                 'APC Check 2700mA',
                 'APC Check 1500mA',
                 ''
                 ])

    file_path = r'{0}\{1}.csv'.format(Path, gSensor_id)  # file_path = r'{0}\{1}.csv'.format(Path, f'result')
    df1.to_csv(file_path, index=True, mode='w', header=True)

    print(f'closed')
