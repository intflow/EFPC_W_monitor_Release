from concurrent.futures import thread
import os
import re
import datetime
import subprocess
import time
import requests
import json
import getmac
import threading
import multiprocessing
from queue import Queue
import struct
import configs
from utils import *
import firmwares_manager
import logging
BOOL_FORMAT = '?'

def key_match(src_key, src_data, target_data):
    if src_key in configs.key_match_dict:
        target_key = configs.key_match_dict[src_key]
        if target_key in target_data:
            target_val = target_data[target_key]
            print(f"{src_key} : {src_data[src_key]} -> {target_val}")
            src_data[src_key] = target_val 

# folder scale check
def get_dir_size(path='.'):
    total = 0
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += get_dir_size(entry.path)
    return total

def get_size(path='.'):
    if os.path.isfile(path):
        return os.path.getsize(path)
    elif os.path.isdir(path):
        return get_dir_size(path)
def get_jetson_stats():
    cpu_usage = psutil.cpu_percent(interval=1)
    gpu_usage = psutil.disk_usage('/').percent
    ram_usage = psutil.virtual_memory().percent
    logging.info(f"[{datetime.datetime.now()}] CPU 사용량: {cpu_usage}% GPU 사용량: {gpu_usage}% RAM 사용량: {ram_usage}%")

def folder_value_check(_time, _path_, ALLOW_CAPACITY_RATE, BOOL_HOUR_CHECK, FIRST_BOOT_REMOVER = False):
    
    if (_time.minute == 0 and _time.second < 5 and BOOL_HOUR_CHECK == False) or FIRST_BOOT_REMOVER:
            
        try: # 이 자리에 시간마다 처리하고 싶은 코드를 집어 넣으면 됨.
            _path_ = re.sub("\n", "", _path_)
            diskInfo  = os.statvfs(_path_)
            
            used      = diskInfo.f_bsize * (diskInfo.f_blocks - diskInfo.f_bavail) / (1024.0 * 1024.0 * 1000.0)
            free      = diskInfo.f_bsize * diskInfo.f_bavail / (1024.0 * 1024.0 * 1000.0)
            total     = diskInfo.f_bsize * diskInfo.f_blocks / (1024.0 * 1024.0 * 1000.0)
            
            print(f"use : {used:.2f} | free : {free:.2f} | target : {(total * ALLOW_CAPACITY_RATE):.2f} | total : {total:.2f}")
            
            if free < total * ALLOW_CAPACITY_RATE:
                max_day_cnt = 30
                while (max_day_cnt >= -1):
                    
                    # folder 내부 날짜순으로 제거
                    os.system(f"sudo find {_path_} -name '*.mp4' -ctime +{max_day_cnt}" + " -exec rm -rf {} \;")
                    os.system(f"sudo find {_path_} -name '*.jpeg' -ctime +{max_day_cnt}" + " -exec rm -rf {} \;")
                    os.system(f"sudo find {_path_} -name '*.jpg' -ctime +{max_day_cnt}" + " -exec rm -rf {} \;")
                    
                    diskInfo  = os.statvfs(_path_)
                    free      = diskInfo.f_bsize * diskInfo.f_bavail / (1024.0 * 1024.0 * 1000.0)
                    
                    if free > total * ALLOW_CAPACITY_RATE:
                        print(f"After remove file : {free:.2f} GB")
                        break
                    
                    max_day_cnt -= 1
                    
        except Exception as e: # 에러 출력
            print(e) 
            
        if BOOL_HOUR_CHECK == False:
            BOOL_HOUR_CHECK = True
    
    elif _time.minute == 0 and _time.second > 5 and BOOL_HOUR_CHECK == True:
        BOOL_HOUR_CHECK = False
        
    return BOOL_HOUR_CHECK

if __name__ == "__main__":
    max_power_mode()
    disable_error_reports()
    configs.internet_ON = internet_check()    
    fan_speed_set(configs.FAN_SPEED)
    KST_timezone_set()
    
    shm_id = shm_id_get()
    deepstream_check_on = True
    shm_val = struct.pack(BOOL_FORMAT, deepstream_check_on)
    shm_id.write(shm_val)
    
    efpc_box_process_list = []
    
    docker_repo = configs.docker_repo
    docker_image, docker_image_id = find_lastest_docker_image(docker_repo)
    docker_image_tag_header = configs.docker_image_tag_header    

    os.makedirs(configs.firmware_dir, exist_ok=True)
    firmwares_manager.copy_firmwares()
    
    device_install()
    check_aws_install()
    model_update_check()    
    check_libcpprest_dev()

    # 폴더 자동삭제를 위한 설정
    f = open("/edgefarm_config/Smart_Record.txt","rt")
    _ = f.readline()
    _path_ = f.readline()
    f.close()
    print(f"[Info] target video folder : {_path_}")
    
    ALLOW_CAPACITY_RATE = 0.02 # 단위 : rate, 폴더 저장 MAX percent
    BOOL_HOUR_CHECK = False # 한시간 마다 체크, 시간 상태 처리를 한번만 할 때 유용함
    LOG_DIR_CHECK = False
    
    # ! 맨 처음 실행했을 떄 한번 체크하게 설정
    _time = datetime.datetime.now()
    folder_value_check(_time, _path_, ALLOW_CAPACITY_RATE, BOOL_HOUR_CHECK, FIRST_BOOT_REMOVER = True)
    deepstreamCheck_thread_list = []
    deepstreamCheck_thread_mutex = threading.Lock()
    deepstreamCheck_thread_cd = threading.Condition()
    # deepstreamCheck_thread = threading.Thread(target=check_deepstream_exec, name="check_deepstream_exec_thread", args=(first_booting,))
    # deepstreamCheck_thread.start()
    deepstreamCheck_thread_list.append(threading.Thread(target=send_logfile, name="send_logfile", daemon=True))
    deepstreamCheck_thread_list[0].start()
    # send_logfile()
    # regular_internet_check = False

    # edgefarm 구동.
    while (True):
        shm_val = shm_id.read(byte_count=1)
        deepstream_check_on = struct.unpack(BOOL_FORMAT, shm_val)[0]
        
        # # 1분에 한번씩 인터넷 체크
        # if _time.second == 0:
            # if regular_internet_check == False:
            #     configs.internet_ON = internet_check()
            #     regular_internet_check = True
        get_jetson_stats()
              
        
        if is_process_running("efpc_box") == False:
            if len(efpc_box_process_list) == 0:
                efpc_box_process_list.append(multiprocessing.Process(target=run_blackBox, daemon=True))
                efpc_box_process_list[0].start()
            elif not efpc_box_process_list[0].is_alive():
                del efpc_box_process_list[0]
                efpc_box_process_list.append(multiprocessing.Process(target=run_blackBox, daemon=True))
                efpc_box_process_list[0].start()
            
        # edgefarm docker 가 켜져있는지 체크
        if deepstream_check_on:
            if check_deepstream_status():
                pass
            else:
                # docker 실행과 동시에 edgefarm 실행됨.
                docker_image, docker_image_id = find_lastest_docker_image(docker_repo)
                run_docker(docker_image, docker_image_id)
            
            
        # 동영상 폴더 제거 알고리즘
        _time = datetime.datetime.now()
        BOOL_HOUR_CHECK = folder_value_check(_time, _path_, ALLOW_CAPACITY_RATE, BOOL_HOUR_CHECK)         
        LOG_DIR_CHECK = log_dir_vol_manage(_time, LOG_DIR_CHECK)
        
        # git pull
        firmwares_manager.git_pull()
        
        

        time.sleep(0.5) # 1초 지연.

    print("\nEdgefarm End...\n")

