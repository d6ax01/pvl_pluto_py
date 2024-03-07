import logging
import json
import os
import shutil
from distutils.dir_util import copy_tree
import sys
import subprocess
import xml.dom.minidom as minidom
from commented_tree_builder import CommentedTreeBuilder
from error_list import NumberOfFilesError
from error_list import FolderSizeError
from folderdict import FolderDict
from lens_fppn_file_name_change import *
from pathlib import Path
from tof_cal_bin_to_eeprom import start_tof_cal_writer
from xml.etree.ElementTree import ElementTree, Element, SubElement, dump
from xml.sax.saxutils import unescape
from utils.logger import Logger, logger
import python_simmian_api #2023-02-16, read to sensor id on simmian API

DEFAULT_WIGG_AVGNUM = 1

with open('json/settings.json', 'r') as f:
    config = json.load(f)

# update element in ToFCalParam.xml
def update_xml(xml_path, module_number, cal_bin_folder_name, lensfppn_output_folder_name, wigg_output_folder_name, temp_driftbinfilepath, wigg_disend, wigg_disstep, wigg_avgnum):
    if not os.path.exists(xml_path):
        raise FileNotFoundError

    dom = minidom.parse(xml_path)

    # update <COMM_CalFinalBinFilePath>
    COMM_CalFinalBinFilePath = dom.getElementsByTagName('COMM_CalFinalBinFilePath')[0]
    COMM_CalFinalBinFilePath.firstChild.replaceWholeText(f'{config["module_root_path"]}\\{module_number}\\{cal_bin_folder_name}\\')
    # update <LENS_RawFilePath>
    LENS_RawFilePath = dom.getElementsByTagName('LENS_RawFilePath')[0]
    LENS_RawFilePath.firstChild.replaceWholeText(f'{config["module_root_path"]}\\{module_number}\\{lensfppn_output_folder_name}\\')
    # update <WIGG_BinFilePath>
    WIGG_BinFilePath = dom.getElementsByTagName('WIGG_RawFilePath')[0]
    WIGG_BinFilePath.firstChild.replaceWholeText(f'{config["module_root_path"]}\\{module_number}\\{wigg_output_folder_name}\\')
    # update <TEMP_DriftBinFilePath>
    TEMP_DriftBinFilePath = dom.getElementsByTagName('TEMP_DriftBinFilePath')[0]
    TEMP_DriftBinFilePath.firstChild.replaceWholeText(f'{temp_driftbinfilepath}\\')
    # update <WIGG_DisEnd>
    WIGG_DisEnd = dom.getElementsByTagName('WIGG_DisEnd')[0]
    WIGG_DisEnd.firstChild.data = wigg_disend
    # update <WIGG_DisStep>
    WIGG_DisStep = dom.getElementsByTagName('WIGG_DisStep')[0]
    WIGG_DisStep.firstChild.data = wigg_disstep
    # update <WIGG_AvgNum>
    WIGG_AvgNum = dom.getElementsByTagName('WIGG_AvgNum')[0]
    WIGG_AvgNum.firstChild.data = wigg_avgnum

    with open(xml_path, 'w') as f:
        dom.writexml(f)


def start_tof_calibration(folder_path):
    full_path = f'{folder_path}\\{config["tof_calibration_file_name"]}'
    if not os.path.exists(full_path):
        raise FileNotFoundError

    process = subprocess.Popen(full_path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=folder_path)

    msg = f''
    with process.stdout:
        for line in iter(process.stdout.readline, b''):
            logger().info(line.decode("utf-8").strip())
            msg = line.decode("utf-8").strip()


    # folder_path = f'{tof_cal_maker_root_path}\\{modulation_suffix}Mhz'
    # full_path = f'{folder_path}\\{tof_calibration_file_name}'
    # if not os.path.exists(full_path):
    #     raise FileNotFoundError

    # os.chdir(folder_path)
    # os.system(full_path)
    # #subprocess.call(full_path)


def count_files_in_dir(path: str) -> int:
    return len([entry for entry in os.scandir(path) if entry.is_file()])


def get_folder_size(path: str) -> int:
    return sum(os.path.getsize(f) for f in os.listdir('.') if os.path.isfile(f))


def create_folder(path):
    try:
        if not os.path.exists(path):
            os.makedirs(path)
    except OSError:
        logger().exception(f'[ERROR] Create Directory. {path}.')


def check_if_raw_folder_has_no_problem(root_path, folder_name, bCheckFolderSize):
    full_path = f'{root_path}\\{folder_name}'
    if not os.path.isdir(full_path):
        raise FileNotFoundError(f'folder is not found : {full_path}')
    expected_file_count = FolderDict().get_file_count(folder_name)
    count_file = count_files_in_dir(full_path)
    if count_file != expected_file_count:
        raise NumberOfFilesError(full_path, expected_file_count, count_file)
    if bCheckFolderSize:
        folder_size = get_folder_size(full_path)
        expected_folder_size = FolderDict().get_folder_size(folder_name)
        if expected_folder_size != folder_size:
            raise FolderSizeError(expected_folder_size, folder_size)

    return True


def check_if_output_folder_have_no_problem(raw_root_path: str, folder_list: list) -> bool:
    for f in folder_list:
        if not check_if_raw_folder_has_no_problem(raw_root_path, f, False):
            return False

    return True


def check_if_tof_cal_bin_has_no_problem(root_path, folder_name):
    file_name = FolderDict().get_tof_cal_bin_filename(folder_name)
    full_path = f'{root_path}\\{folder_name}\\{file_name}'
    if not os.path.exists(full_path):
        raise FileNotFoundError
    if os.path.getsize(full_path) == 0:
        return False

    return True


def check_if_result_folder_has_problem(raw_path):
    result = True
    try:
        for i in config['frequency_list']:
            result &= check_if_raw_folder_has_no_problem(raw_path, i["cal_bin_folder_name"], False)
            result &= check_if_tof_cal_bin_has_no_problem(raw_path, i["cal_bin_folder_name"])
    except ValueError as e:
        logger().error(f'[ERROR] decoding config json has failed {e}')
    finally:
        return result



def rename_folder(source, destination):
    #if not os.path.isdir(source):
    #    return False

    #shutil.move(source, destination) #덮어쓰기가 안됨

    if os.path.isdir(destination): # 동일폴더있으면 삭제한다.
        shutil.rmtree(destination)

    shutil.move(source, destination)  # 덮어쓰기가 안됨



def copy_file(source, destination):
    if not os.path.exists(source):
        logger().error(f'[ERROR] copy_file error! file does not exist. path : {source}')
        return False

    shutil.copyfile(source, destination)
    return True


def get_temp_drift_bin_folder_list() -> list:
    result = []
    try:
        for i in config['frequency_list']:
            result.append(i['temp_drift_bin_folder_path'])
    except ValueError as e:
        logger().error(f'[ERROR] decoding config json has failed {e}')
    finally:
        return result


def get_wiggling_output_folder_list() -> list:
    result = []
    try:
        for i in config['frequency_list']:
            result.append(i['wigg_output_folder_name'])
    except ValueError as e:
        print(f'[ERROR] decoding config json has failed {e}')
    finally:
        return result

def get_lensfppn_output_folder_list() -> list:
    result = []
    try:
        for i in config['frequency_list']:
            result.append(i['lensfppn_output_folder_name'])
    except ValueError as e:
        print(f'[ERROR] decoding config json has failed {e}')
    finally:
        return result


def get_output_folder_list() -> list:
    result = [*get_wiggling_output_folder_list(), *get_lensfppn_output_folder_list()]
    return result

def get_cal_bin_folder_list() -> list:
    result = []
    try:
        for i in config['frequency_list']:
            result.append(i['cal_bin_folder_name'])
    except ValueError as e:
        logger().error(f'[ERROR] decoding config json has failed {e}')
    finally:
        return result


def get_tof_cal_maker_path_list() -> list:
    result = []
    try:
        for i in config['frequency_list']:
            result.append(i['tof_cal_maker_path'])
    except ValueError as e:
        logger().error(f'[ERROR] decoding config json has failed {e}')
    finally:
        return result


def create_tof_cal_bin(module_number: str, b_eeprom_write: bool):
    try:
        temp_drift_bin_folder_list = get_temp_drift_bin_folder_list()
        # r'{0}\temp_calibration\230106'.format(os.getcwd())
        for i in temp_drift_bin_folder_list:
            if not os.path.isdir(f'{os.getcwd()}\\{i}'):
                raise FileNotFoundError(f'temperature drift folder does not exist. {os.getcwd()}\\{i}')

        module_path = f'{config["module_root_path"]}\\{module_number}'

        if os.path.exists(module_path):
            yes_choices = ['yes', 'y']
            no_choices = ['no', 'n']

            user_choice = 'y' #input(f'Folder({module_path}) is exists. Are you sure you want to overwrite?(Y/N)')
            if user_choice.lower() in no_choices:
                sys.exit(0)

        output_folder_list = get_output_folder_list()
        for i in output_folder_list:
            rename_folder(f'{config["output_path"]}\\{i}', f'{module_path}\\{i}')

        if not check_if_output_folder_have_no_problem(module_path, output_folder_list):
            logger().error(f'[ERROR] \"{module_path}\" has problem. Please check error message')
            raise FileNotFoundError(f'raw folder has problem.')

        cal_bin_folder_list = get_cal_bin_folder_list()
        for i in cal_bin_folder_list:
            create_folder(f'{module_path}\\{i}')

        lensfppn_output_folder_list = get_lensfppn_output_folder_list()
        for i in lensfppn_output_folder_list:
            change_lensfppn_filename_to_tof_calibration_format(f'{module_path}\\{i}')

        for i in config["frequency_list"]:
            xml_path = f'{os.getcwd()}\\{i["tof_cal_maker_path"]}\\{config["xml_file_name"]}'
            temp_driftbinfilepath = f'{os.getcwd()}\\{i["temp_drift_bin_folder_path"]}'
            wigg_avgnum = config.get("wigg_avgnum", DEFAULT_WIGG_AVGNUM)
            update_xml(xml_path=xml_path,
                module_number=module_number,
                cal_bin_folder_name=i["cal_bin_folder_name"],
                lensfppn_output_folder_name=i["lensfppn_output_folder_name"],
                wigg_output_folder_name=i["wigg_output_folder_name"],
                temp_driftbinfilepath=temp_driftbinfilepath,
                wigg_disend=i["wigg_dis_end"],
                wigg_disstep=i["step"],
                wigg_avgnum=wigg_avgnum
            )

        # for i in temp_drift_bin_folder_list:
        #     temp_driftbinfilepath = f'{os.getcwd()}\\{i}'
        #     update_xml(module_number, temp_driftbinfilepath)

        tof_cal_maker_path_list = get_tof_cal_maker_path_list()
        for i in tof_cal_maker_path_list:
            start_tof_calibration(f'{os.getcwd()}\\{i}')

        if not check_if_result_folder_has_problem(module_path):
            logger().error(f'[ERROR] result path ({module_path}) has problem. Please check error message')

        if b_eeprom_write:
            bresult = start_tof_cal_writer(module_path)

            if bresult == 0: #if bresult == True:
                logger().info('Succeeded!')
            else :
                logger().info('Failed!')

            return bresult


    except FileNotFoundError as error:
        logging.exception(f'module_number={module_number}: File or Folder Not Found Error.')
    except NumberOfFilesError as error:
        logging.exception(
            f'module_number={module_number}: Number of raw files does not match. Please check the error message ')
    except ValueError as error:
        logging.exception(f'[ERROR] module_number={module_number}: module number must be integer. ')
    except KeyError as error:
        logging.exception(f'[ERROR] module_number={module_number}: KeyError occure.')
    except AttributeError as error:
        logging.exception(f'[ERROR] module_number={module_number}: AttributeError occure.')
    finally:
        if os.path.exists(f'{config["log_path"]}\\{config["lensfppn_log_filename"]}'):
            copy_file(f'{config["log_path"]}\\{config["lensfppn_log_filename"]}', f'{module_path}\\{config["lensfppn_log_filename"]}')
        if os.path.exists(f'{config["log_path"]}\\{config["wiggling_log_filename"]}'):
            copy_file(f'{config["log_path"]}\\{config["wiggling_log_filename"]}', f'{module_path}\\{config["wiggling_log_filename"]}')


def get_sensor_id():
    sim = python_simmian_api.Simmian()
    list = [0 for i in range(13)]

    temp = sim.ReadI2C(0xA0, "0x00B9", 1)
    list[0] = format(temp, '02X')
    #print(f'simmian readI2C 0x00B9 1 Byte  -> {temp} , hex -> {list[0]}')

    temp = sim.ReadI2C(0xA0, "0x00BA", 1)
    list[1] = format(temp, '02X')
    #print(f'simmian readI2C 0x00BA 1 Byte  -> {temp} , hex -> {list[1]}')

    temp = sim.ReadI2C(0xA0, "0x00BB", 1)
    list[2] = format(temp, '02X')
    #print(f'simmian readI2C 0x00BB 1 Byte  -> {temp} , hex -> {list[2]}')

    temp = sim.ReadI2C(0xA0, "0x00BC", 1)
    list[3] = format(temp, '02X')
    #print(f'simmian readI2C 0x00BC 1 Byte  -> {temp} , hex -> {list[3]}')

    temp = sim.ReadI2C(0xA0, "0x00BD", 1)
    list[4] = format(temp, '02X')
    #print(f'simmian readI2C 0x00BD 1 Byte  -> {temp} , hex -> {list[4]}')

    temp = sim.ReadI2C(0xA0, "0x00BE", 1)
    list[5] = format(temp, '02X')
    #print(f'simmian readI2C 0x00BE 1 Byte  -> {temp} , hex -> {list[5]}')

    temp = sim.ReadI2C(0xA0, "0x00BF", 1)
    list[6] = format(temp, '02X')
    #print(f'simmian readI2C 0x00BF 1 Byte  -> {temp} , hex -> {list[6]}')

    temp = sim.ReadI2C(0xA0, "0x00C0", 1)
    list[7] = format(temp, '02X')
    #print(f'simmian readI2C 0x00C0 1 Byte  -> {temp} , hex -> {list[7]}')

    temp = sim.ReadI2C(0xA0, "0x00C1", 1)
    list[8] = format(temp, '02X')
    #print(f'simmian readI2C 0x00C1 1 Byte  -> {temp} , hex -> {list[8]}')

    temp = sim.ReadI2C(0xA0, "0x00C2", 1)
    list[9] = format(temp, '02X')
    #print(f'simmian readI2C 0x00C2 1 Byte  -> {temp} , hex -> {list[9]}')

    temp = sim.ReadI2C(0xA0, "0x00C3", 1)
    list[10] = format(temp, '02X')
    #print(f'simmian readI2C 0x00C3 1 Byte  -> {temp} , hex -> {list[10]}')

    temp = sim.ReadI2C(0xA0, "0x00C4", 1)
    list[11] = format(temp, '02X')
    #print(f'simmian readI2C 0x00C4 1 Byte  -> {temp} , hex -> {list[11]}')

    temp = sim.ReadI2C(0xA0, "0x00C5", 1)
    list[12] = format(temp, '02X')
    #print(f'simmian readI2C 0x00C5 1 Byte  -> {temp} , hex -> {list[12]}')

    str_sensorid = "".join(list)

    return str_sensorid


if __name__ == "__main__":

    Logger.init(config["lensfppn_log_filename"])

    # 2023-02-16 ::: JH BAE -> Get sensor id
    # module_number = input('input module number: ')
    get_sensor_id_ = get_sensor_id()

    print(f'input module number : {get_sensor_id_}')

    module_number = get_sensor_id_

    create_tof_cal_bin(module_number, True)




