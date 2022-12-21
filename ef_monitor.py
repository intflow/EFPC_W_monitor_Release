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
            
            print("\n======================================================")
            print("             Edge Farm Engine Monitor")
            print("\n                                              By. Ryu ")
            print("\nAutoRun Service Status : {}".format(autorun_service_status))
            print("Edge Farm Engine Status : {}".format(ef_engine_status))
            print("\nDocker repo : {}".format(docker_repo))
            print("Current \033[92mRUNNING\033[0m docker image   : {}".format(current_running_docker_image))
            print("Last docker image (Local)      : {}".format(last_docker_image_local))
            print("Last docker image (Docker hub) : {}".format(last_docker_image_dockerhub))
            if docker_update_history > 0:
                print("\033[36m{} Update(s) available\033[0m".format(docker_update_history))
            elif docker_update_history == 0:
                print("\033[36mThis is the latest version\033[0m")
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
    docker_log_process_list[0].terminate() # 확인사살
    # docker_log_process_list[0].close() # 자원 해제 . 3.7부터 추가된대
    del(docker_log_process_list[0]) # 리스트에서 없애기

def docker_log_process_start(docker_log_process_list):
    # 새로운 process 시작.
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
    port_info_set()
    
    # docker_image_head = "intflow/edgefarm:hallway_dev"
    docker_repo = configs.docker_repo
    docker_image, docker_image_id = find_lastest_docker_image(docker_repo)
    docker_image_tag_header = configs.docker_image_tag_header
    
    last_docker_image_dockerhub = "None"
    docker_update_history = -1
    
    docker_log_process_list = []

    # control thread 실행
    control_queue = Queue()
    control_thread_mutex = threading.Lock()
    control_thread_cd = threading.Condition()
    control_thread = threading.Thread(target=control_edgefarm_monitor, args=(control_queue, docker_repo, control_thread_cd,))
    control_thread.start()

    docker_log_queue = Queue()


    # edgefarm 구동.
    while (True):
        # edgefarm docker 가 켜져있는지 체크
        # if check_deepstream_status():
        # print("control_queue.empty() : {}".format(control_queue.empty()))
        # 명령 queue 에 값이 들어오면.
        if not control_queue.empty():
            user_command = control_queue.get()
            # print(f"\ncontrol queue get => {user_command}\n")
            if user_command == 1:
                # docker 실행과 동시에 edgefarm engine 실행됨.
                if (check_deepstream_status()):
                    print_with_lock("\nEdge Farm is Already Running\n")
                else:
                    firmwares_manager.copy_firmwares()
                    device_install()
                    with control_thread_cd:
                        docker_image, docker_image_id = find_lastest_docker_image(docker_repo)
                        run_docker(docker_image, docker_image_id) # docker 실행
                        control_thread_cd.notifyAll()
            elif user_command == 4: # 재시작.
                if (check_deepstream_status()): # engine 이 켜져있다면
                    print("\nRestart Edgefarm!")
                    firmwares_manager.copy_firmwares()
                    device_install() # api request
                    with control_thread_cd:
                        # if autorun_service_check() == "RUNNING": # autorun 이 켜져있다면
                        #     kill_edgefarm() # engine docker container 를 종료시킴. autorun 파이썬에 의해서 다시 켜지므로 결국 restart 와 마찬가지.
                        # else: # autorun 이 꺼져있다면 
                        #     docker_image, docker_image_id = find_lastest_docker_image(docker_repo)
                        #     run_docker(docker_image, docker_image_id) # docker 실행.
                        
                        ### edgefarm 끄기, autorun service 도 끄기
                        if autorun_service_check() == "RUNNING": # autorun service 가 실행 중이라면
                            autorun_service_stop() # autorun service 멈추기
                            
                            kill_edgefarm() # engine 킬.
                            
                            autorun_service_start() # autorun service 시작, edgefarm docker 도 자동으로 시작.
                                  
                        else: # autorun service 가 실행 중이 아니었다면
                            kill_edgefarm() # engine 킬.            
                            
                            docker_image, docker_image_id = find_lastest_docker_image(docker_repo)
                            run_docker(docker_image, docker_image_id) # docker 실행                        
                            
                        control_thread_cd.notifyAll()
                else:
                    print_with_lock("\nEdge Farm is not Running\n")
            elif user_command == 5: # edgefarm end. autorun sevice 도 종료.
                if (check_deepstream_status()): # engine 켜져있다면
                    print("\nKill Edgefarm!")
                    with control_thread_cd:
                        if autorun_service_check() == "RUNNING": # autorun service 가 실행 중이라면
                            autorun_service_stop() # autorun service 멈추기
                            
                        kill_edgefarm() # engine 킬. autorun 이 꺼졌으므로 재시작하지 않음.
                        control_thread_cd.notifyAll()                    
                else:
                    print_with_lock("\nEdge Farm is not Running\n")
            elif user_command == 2: # docker log 보기
                if check_deepstream_status():
                    if len(docker_log_process_list) > 0:
                        if docker_log_process_list[0].is_alive(): # process 가 살아있다면 pass
                            print_with_lock("\nAlready Running View docker log mode...\n")
                        else: # 죽어있다면
                            docker_log_process_kill(docker_log_process_list) # 확인사살하고
                            docker_log_process_start(docker_log_process_list) # 시작

                    else: # list 개수가 0이라면
                        # 새로운 process 시작.
                        docker_log_process_start(docker_log_process_list) # 시작
                else:
                    print_with_lock("\nEdge Farm is not Running\n")
            elif user_command == 3: # docker log 보기 종료 신호
                if len(docker_log_process_list) > 0:
                    if docker_log_process_list[0].is_alive(): # process 가 살아있다면
                        docker_log_process_kill(docker_log_process_list) # 죽이기
                        print_with_lock("\nTerminate View docker log mode\n")
                    else: # 죽어있다면
                        docker_log_process_kill(docker_log_process_list) # 확인사살
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
                        autorun_service_start() # autorun service 시작
                    control_thread_cd.notifyAll()
            elif user_command == 7: # supervisor stop
                with control_thread_cd:
                    if autorun_service_check() == "STOPPED":
                        print("\nAuto Run Service is not Running\n")
                    else:
                        autorun_service_stop() # autorun service 멈춤
                    control_thread_cd.notifyAll()
            elif user_command == 10: # show docker image list
                with control_thread_cd:
                    show_docker_images_list(docker_repo + ":" + configs.docker_image_tag_header) # 연관된 docker images list 출력
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
        #     # docker 실행과 동시에 edgefarm 실행됨.
        #     run_docker(docker_image)

        time.sleep(0.5) # 1초 지연.

    if len(docker_log_process_list) > 0 and docker_log_process_list[0].is_alive(): docker_log_process_kill(docker_log_process_list)
    control_thread.join()
    print("docker control thread end")

    print("\nEdge Farm Monitor End\n")

