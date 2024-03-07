import json
import os

result_eeprom = 1

with open('json/settings.json', 'r') as f:
    config = json.load(f)

#r'{0}\_tof_cal_maker_221101'.format(os.getcwd())

def get_cal_bin_path_list_string(module_root_path: str) -> str:
    result = []

    try:
        for i in config["frequency_list"]:
            result.append(f'{module_root_path}\\{i["cal_bin_folder_name"]}\\{i["cal_bin_filename"]}')
    except ValueError as e:
        print(f'[ERROR] decoding config json has failed {e}')
    finally:
        return result


def start_tof_cal_writer(module_path):
    full_path = f'{os.getcwd()}\\{config["eeprom_writer_folder_path"]}\\{config["eeprom_writer_file_name"]}'
    if not os.path.exists(full_path):
        raise FileNotFoundError(f'file is not found : {full_path}')

    cal_bin_path_list = get_cal_bin_path_list_string(module_path)
    for i in cal_bin_path_list:
        if not os.path.exists(i):
            raise FileNotFoundError(f'file is not found : {i}')

    cal_bin_path_list_string = " ".join(cal_bin_path_list)

    os.chdir(f'{os.getcwd()}\\{config["eeprom_writer_folder_path"]}')

    # 2023-02-09 :: verify e2p write!!!
    #os.system(f'{full_path} {config["slave_address"]} {cal_bin_path_list_string}')
    path = f'{full_path} {config["slave_address"]} {cal_bin_path_list_string}'
    result = os.popen(path).read().strip().split('\n')
    print(f'')
    print(f'==================== Write EEPROM ====================')
    print(result)
    str1 = ''.join(str(s) for s in result)
    strsurch = 'Write Succeed'
    if strsurch in str1:
        print(f'PASS <- Write EEPROM Process')
        print(f'==================== Write EEPROM ====================')
        print(f'')
        result_eeprom = 0

    else:
        print(f'FAIL <- Write EEPROM Process')
        print(f'==================== Write EEPROM ====================')
        print(f'')
        result_eeprom = 103

    return result_eeprom


if __name__ == "__main__" :
    module_number = input('input module number: ')
    module_path = f'{config["module_root_path"]}\\{module_number}'
    start_tof_cal_writer(module_path)
    # module_root_path = r'C:\VST\calibration\2'
    # start_tof_cal_writer(module_root_path)