from concurrent.futures import thread
import subprocess
import time
import requests
import json
import getmac
import threading
import multiprocessing
from queue import Queue
import struct
import natsort
import configs
from utils import *
from for_supervisor import *
import firmwares_manager

current_dir = os.path.dirname(os.path.abspath(__file__))

def autorun_service_check():
    result = subprocess.run("systemctl status ef_count_autorun.service", stdout=subprocess.PIPE, shell=True)
    res_str = result.stdout.decode()
    active_index = res_str.find('Active: active (running)')
    
    if active_index == -1:
        return "STOPPED"
    else:
        return "RUNNING"

def autorun_service_start():
    subprocess.run("sudo systemctl start ef_count_autorun.service", shell=True)

def autorun_service_stop():
    subprocess.run("sudo systemctl stop ef_count_autorun.service", shell=True) 

def control_edgefarm_monitor(control_queue, docker_repo, control_thread_cd):
    global last_docker_image_dockerhub, docker_update_history
    # global control_thread_mutex
    wait_pass = True
    not_print = False
    while True:
        # control_thread_mutex.acquire()
        if wait_pass:
            wait_pass = False
        else:
            with control_thread_cd:
                control_thread_cd.wait()
        if not not_print:
            autorun_service_status = autorun_service_check()
            last_docker_image_local = find_lastest_docker_image(docker_repo)[0]
            current_running_docker_image = current_running_image(docker_repo + ":" + configs.docker_image_tag_header)
            if autorun_service_status == "RUNNING":
                autorun_service_status = "\033[92mRUNNING\033[0m"
            ef_engine_status = "\033[92mRUNNING\033[0m" if check_deepstream_status() else "STOPPED"
            model_export_status = "\033[92mRUNNING\033[0m" if check_model_export_status() else "STOPPED"
            
            print("\n======================================================")
            print("             Edge Farm Engine Monitor")
            print("\n                                              By. Ryu ")
            print("\nAutoRun Service Status : {}".format(autorun_service_status))
            print("Edge Farm Engine Status : {}".format(ef_engine_status))
            print("Model Export Status : {}".format(model_export_status))
            print("\nDocker repo : {}".format(docker_repo))
            print("Current \033[92mRUNNING\033[0m docker image   : {}".format(current_running_docker_image))
            print("Last docker image (Local)      : {}".format(last_docker_image_local))
            print("Last docker image (Docker hub) : {}".format(last_docker_image_dockerhub))
            if docker_update_history > 0:
                print("\033[36m{} Update(s) available\033[0m".format(docker_update_history))
            elif docker_update_history == 0:
                print("\033[36mThis is the latest version\033[0m")
            if get_local_model_mtime() is not None:
                model_mtime = get_local_model_mtime().strftime("%Y-%m-%d %H:%M:%S")
            else:
                model_mtime = "No model"               
            print("\nModel's modified time : {}".format(model_mtime))
            print("\n======================================================\n")
            print("Tips.")
            print(" - To change \"\033[92mRUNNING\033[0m (Temporary or Invalid)\" to \"\033[92mRUNNING\033[0m (Background)\", 7.autostop and then 6.autostart")
            print("\n-----------------")
            print("    COMMANDS")
            print("1. start : Edgefarm engine start")
            print("2. log : view docker log mode")
            print("3. logkill : terminate view docker log mode")
            print("4. restart : Restart Edgefarm docker")
            print("5. kill : Kill Edgefarm engine. (Warning) Auto Run Service will be stopped")
            print("6. autostart : Start Auto Run Service")
            print("7. autostop : Stop Auto Run Service")
            print("8. export : create intflow model engine")
            print("10. images : show \"{}\" docker images".format(docker_repo + ":" + configs.docker_image_tag_header))
            print("11. updatecheck : Check Last docker image from docker hub")
            print("12. updateimage : Pull lastest version image from docker hub")
            print("13. end : Close Edge Farm Engine Monitor")
            print("-----------------\n")
        # control_thread_mutex.release()
        not_print = False
        # print(f"\n\n\n not print : {not_print}\n\n\n")
        user_command = input()
        # print(f"\n\n\n user cm : {user_command}")
        if control_queue.empty():
            if user_command in ["start", "1"]:
                control_queue.put(1)
            elif user_command in ["log", "2"]:
                control_queue.put(2)
                not_print = True
            elif user_command in ["logkill", "3"]:
                control_queue.put(3)
            elif user_command in ["restart", "4"]:
                control_queue.put(4)
            elif user_command in ["kill", "5"]:
                control_queue.put(5)
            elif user_command in ["autostart", "6"]:
                control_queue.put(6)
            elif user_command in ["autostop", "7"]:
                control_queue.put(7)
            elif user_command in ["export", "8"]:
                control_queue.put(8)
            elif user_command in ["images", "10"]:
                control_queue.put(10)
            elif user_command in ["updatecheck", "11"]:
                control_queue.put(11)
            elif user_command in ["updateimage", "12"]:
                control_queue.put(12)
            elif user_command in ["end", "13"]:
                control_queue.put(13)
                break
            elif user_command == "test":
                control_queue.put(99)
            else:
                wait_pass = True

def print_with_lock(content):
    # global control_thread_mutex
    # control_thread_mutex.acquire()
    global control_thread_cd
    with control_thread_cd:
        print(content)
        control_thread_cd.notifyAll()
    # control_thread_mutex.release()

def docker_log_process_kill(docker_log_process_list):
    if docker_log_process_list[0].is_alive():
        docker_log_end_print()
    docker_log_process_list[0].terminate() # ????????????
    # docker_log_process_list[0].close() # ?????? ?????? . 3.7?????? ????????????
    del(docker_log_process_list[0]) # ??????????????? ?????????

def docker_log_process_start(docker_log_process_list):
    # ????????? process ??????.
    # control_thread_mutex.acquire()
    # control_thread_mutex.release()
    global control_thread_cd 
    with control_thread_cd:
        print("\n===========================================")
        print("       View docker log mode")
        print("===========================================\n")
        control_thread_cd.notifyAll()
    docker_log_process_list.append(multiprocessing.Process(target=docker_log_view))
    docker_log_process_list[0].start()


if __name__ == "__main__":
    fan_speed_set(configs.FAN_SPEED)
    KST_timezone_set()
    
    # docker_image_head = "intflow/edgefarm:hallway_dev"
    docker_repo = configs.docker_repo
    docker_image, docker_image_id = find_lastest_docker_image(docker_repo)
    docker_image_tag_header = configs.docker_image_tag_header
    
    last_docker_image_dockerhub = "None"
    docker_update_history = -1
    
    docker_log_process_list = []

    # control thread ??????
    control_queue = Queue()
    control_thread_mutex = threading.Lock()
    control_thread_cd = threading.Condition()
    control_thread = threading.Thread(target=control_edgefarm_monitor, args=(control_queue, docker_repo, control_thread_cd,))
    control_thread.start()

    docker_log_queue = Queue()


    # edgefarm ??????.
    while (True):
        # edgefarm docker ??? ??????????????? ??????
        # if check_deepstream_status():
        # print("control_queue.empty() : {}".format(control_queue.empty()))
        # ?????? queue ??? ?????? ????????????.
        if not control_queue.empty():
            user_command = control_queue.get()
            # print(f"\ncontrol queue get => {user_command}\n")
            if user_command == 1:
                # docker ????????? ????????? edgefarm engine ?????????.
                if (check_deepstream_status()):
                    print_with_lock("\nEdge Farm is Already Running\n")
                else:
                    firmwares_manager.copy_firmwares()
                    device_install()
                    model_update_check()
                    with control_thread_cd:
                        docker_image, docker_image_id = find_lastest_docker_image(docker_repo)
                        run_docker(docker_image, docker_image_id) # docker ??????
                        control_thread_cd.notifyAll()
            elif user_command == 4: # ?????????.
                if (check_deepstream_status()): # engine ??? ???????????????
                    print("\nRestart Edgefarm!")
                    with control_thread_cd:
                        # if autorun_service_check() == "RUNNING": # autorun ??? ???????????????
                        #     kill_edgefarm() # engine docker container ??? ????????????. autorun ???????????? ????????? ?????? ???????????? ?????? restart ??? ????????????.
                        # else: # autorun ??? ??????????????? 
                        #     docker_image, docker_image_id = find_lastest_docker_image(docker_repo)
                        #     run_docker(docker_image, docker_image_id) # docker ??????.
                        
                        ### edgefarm ??????, autorun service ??? ??????
                        if autorun_service_check() == "RUNNING": # autorun service ??? ?????? ????????????
                            autorun_service_stop() # autorun service ?????????
                            
                            kill_edgefarm() # engine ???.
                            
                            autorun_service_start() # autorun service ??????, edgefarm docker ??? ???????????? ??????.
                                  
                        else: # autorun service ??? ?????? ?????? ???????????????
                            kill_edgefarm() # engine ???.            
                            
                            firmwares_manager.copy_firmwares()
                            device_install() # api request
                            model_update_check()
                                                        
                            docker_image, docker_image_id = find_lastest_docker_image(docker_repo)
                            run_docker(docker_image, docker_image_id) # docker ??????                        
                            
                        control_thread_cd.notifyAll()
                else:
                    print_with_lock("\nEdge Farm is not Running\n")
            elif user_command == 5: # edgefarm end. autorun sevice ??? ??????.
                if (check_deepstream_status()): # engine ???????????????
                    print("\nKill Edgefarm!")
                    with control_thread_cd:
                        if autorun_service_check() == "RUNNING": # autorun service ??? ?????? ????????????
                            autorun_service_stop() # autorun service ?????????
                            
                        kill_edgefarm() # engine ???. autorun ??? ??????????????? ??????????????? ??????.
                        control_thread_cd.notifyAll()                    
                else:
                    print_with_lock("\nEdge Farm is not Running\n")
            elif user_command == 2: # docker log ??????
                if check_deepstream_status():
                    if len(docker_log_process_list) > 0:
                        if docker_log_process_list[0].is_alive(): # process ??? ??????????????? pass
                            print_with_lock("\nAlready Running View docker log mode...\n")
                        else: # ???????????????
                            docker_log_process_kill(docker_log_process_list) # ??????????????????
                            docker_log_process_start(docker_log_process_list) # ??????

                    else: # list ????????? 0?????????
                        # ????????? process ??????.
                        docker_log_process_start(docker_log_process_list) # ??????
                else:
                    print_with_lock("\nEdge Farm is not Running\n")
            elif user_command == 3: # docker log ?????? ?????? ??????
                if len(docker_log_process_list) > 0:
                    if docker_log_process_list[0].is_alive(): # process ??? ???????????????
                        docker_log_process_kill(docker_log_process_list) # ?????????
                        print_with_lock("\nTerminate View docker log mode\n")
                    else: # ???????????????
                        docker_log_process_kill(docker_log_process_list) # ????????????
                        print_with_lock("\nNot Running View docker log mode\n")
                else:
                    print_with_lock("\nNot Running View docker log mode\n")
            elif user_command == 6: # supervisor start
                
                subprocess.run("bash ./autorun_service_registration.sh", shell=True)
                
                # kill_edgefarm()
                with control_thread_cd:
                    if autorun_service_check() == "RUNNING":
                        print("\nAuto Run Service is Already Running\n")
                    else:
                        autorun_service_start() # autorun service ??????
                    control_thread_cd.notifyAll()
            elif user_command == 7: # supervisor stop
                with control_thread_cd:
                    if autorun_service_check() == "STOPPED":
                        print("\nAuto Run Service is not Running\n")
                    else:
                        autorun_service_stop() # autorun service ??????
                    control_thread_cd.notifyAll()
            elif user_command == 8:
                with control_thread_cd:
                    git_edgefarm_config_path = os.path.join(current_dir, "edgefarm_config")
                    model_update()
                    control_thread_cd.notifyAll()
            elif user_command == 10: # show docker image list
                with control_thread_cd:
                    show_docker_images_list(docker_repo + ":" + configs.docker_image_tag_header) # ????????? docker images list ??????
                    control_thread_cd.notifyAll()
            elif user_command == 11: # end
                with control_thread_cd:
                    print("\nCheck update\n")
                    last_docker_image_dockerhub, docker_update_history = search_dockerhub_last_docker_image(docker_repo)
                    control_thread_cd.notifyAll()
            elif user_command == 12:
                with control_thread_cd:
                    if last_docker_image_dockerhub != "None" and docker_update_history > 0:
                        # subprocess.run("docker pull {}".format(docker_repo + ":" + last_docker_image_dockerhub), shell=True)
                        docker_pull(docker_repo, last_docker_image_dockerhub)
                    elif docker_update_history == 0:
                        print("\nAlready lastest version!\n")
                    else:
                        print("\nPlease updatecheck!\n")
                    control_thread_cd.notifyAll()
            elif user_command == 13: # end
                break
            elif user_command == 99:
                print_with_lock("\n\ntest success!\n\n")

        # else:
        #     # docker ????????? ????????? edgefarm ?????????.
        #     run_docker(docker_image)

        time.sleep(0.5) # 1??? ??????.

    if len(docker_log_process_list) > 0 and docker_log_process_list[0].is_alive(): docker_log_process_kill(docker_log_process_list)
    control_thread.join()
    print("docker control thread end")

    print("\nEdge Farm Monitor End\n")

