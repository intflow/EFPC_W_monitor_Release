import subprocess
import configs
import requests
from requests.auth import HTTPBasicAuth
import getpass
import natsort
import json
import getmac
import time
import os
import socket

import datetime as dt
import pytz
from functools import cmp_to_key

current_dir = os.path.dirname(os.path.abspath(__file__))

def docker_log_save_start():
    os.makedirs(configs.log_save_dir_path, exist_ok=True)
    
    KST_timezone = pytz.timezone('Asia/Seoul')
    now_kst = dt.datetime.now().astimezone(KST_timezone)

    # print(now_kst.strftime("%Y%m%d_%H%M%S_log"))
    
    file_name = now_kst.strftime("%Y%m%d_%H%M%S.log")
    file_path = os.path.join(configs.log_save_dir_path, file_name)
    
    subprocess.Popen(f"docker logs -f {configs.container_name} > {file_path} &", shell=True)
    
    print(f"\nThe real-time log is being saved at \"{file_path}\"\n")

def get_log_file_list(dirpath):
    file_list = [x for x in os.listdir(dirpath) if os.path.splitext(x)[-1] == ".log"]
    file_list.sort(key = lambda f: os.path.getmtime(os.path.join(dirpath, f)), reverse=True)
    
    return file_list

def get_dir_size(path='.'):
    total = 0
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += get_dir_size(entry.path)
    return total

def check_log_dir_vol():
    print("\nCheck log dir volume!")    
    
    if get_dir_size(configs.log_save_dir_path) >= configs.log_max_volume:
        log_f_list = get_log_file_list(configs.log_save_dir_path)
    
        while get_dir_size(configs.log_save_dir_path) >= configs.log_max_volume:
            if len(log_f_list) == 0:
                break
            print(f"Remove \"{os.path.join(configs.log_save_dir_path, log_f_list[-1])}\"")
            os.remove(os.path.join(configs.log_save_dir_path, log_f_list[-1]))
            del log_f_list[-1]
    print("Done!\n")
    
def log_dir_vol_manage(now_dt, LOG_DIR_CHECK):
    if now_dt.minute == 0 and now_dt.second == 0:
    # if now_dt.second == 0:
        if LOG_DIR_CHECK == False:
            check_log_dir_vol()
            LOG_DIR_CHECK = True
    else:
        LOG_DIR_CHECK = False  
    
    return LOG_DIR_CHECK 

def port_status_check(port):
    try:
        res = subprocess.check_output("netstat -ltu | grep {}".format(port), shell=True)
        res = res.decode().split('\n')[:-1]
    except subprocess.CalledProcessError:
        res = []
        
    if len(res) > 0 and res[0].split()[-1] == "LISTEN":
        return True
    else:
        return False

def kill_edgefarm():
    subprocess.run(f"docker exec -it {configs.container_name} bash ./kill_edgefarm.sh", shell=True)

def run_docker(docker_image, docker_image_id):
    if os.path.isdir("/edgefarm_config") == False:
        os.makedirs("/edgefarm_config", exist_ok=True)
        copy_edgefarm_config(mode="all")
    fan_speed_set(configs.FAN_SPEED)
    if docker_image == None or docker_image_id == None:
        for i in range(10):
            print("\nNo Docker Image...\n")
        return -1
    
    run_docker_command = "docker run -dit "\
                        + "--rm "\
                        + f"--name={configs.container_name} "\
                        + "--net=host "\
                        + "--privileged "\
                        + "--ipc=host "\
                        + "--runtime nvidia "\
                        + "-e DISPLAY=$DISPLAY "\
                        + "-v /etc/localtime:/etc/localtime:ro"\
                        + "-v /etc/timezone:/etc/timezone:ro"\
                        + "-v /edgefarm_config:/edgefarm_config "\
                        + "-v /home/intflow/works:/works "\
                        + "-v /sys/devices/:/sys/devices " \
                        + "-v /sys/class/gpio:/sys/class/gpio "\
                        + "-v /home/intflow/.Xauthority:/root/.Xauthority:rw "\
                        + "-v /tmp/.X11-unix:/tmp/.X11-unix "\
                        + "-v /dev/input:/dev/input "\
                        + "-v /bin/systemctl:/bin/systemctl "\
                        + "-v /run/systemd/system:/run/systemd/system "\
                        + "-v /var/run/dbus/system_bus_socket:/var/run/dbus/system_bus_socket "\
                        + "-v /sys/fs/cgroup:/sys/fs/cgroup "\
                        + "-w /opt/nvidia/deepstream/deepstream-6.0/sources/apps/sample_apps/ef_custompipline "\
                        + f"{docker_image_id} bash ./run_edgefarm.sh"
                        # + "{} bash".format(lastest_docker_image_info[1])

    while check_deepstream_status():
        print("Try to kill Edgefarm Engine...")
        kill_edgefarm()
        time.sleep(1)

    print(f"Docker Image : {docker_image}\n")
    #subprocess.call("xhost +", shell=True)
    subprocess.call("echo $DISPLAY", shell=True)
    subprocess.call(run_docker_command, shell=True)
    print("\nDocker run!\n")
    
    docker_log_save_start()    


def fan_speed_set(speed):
    # 팬 속도
    subprocess.run("sudo sh -c 'echo {} > /sys/devices/pwm-fan/target_pwm'".format(speed), stderr=subprocess.PIPE, shell=True)

## 실행 중이면 True, 실행 중이 아니면 False 반환.
def check_deepstream_status():
    res = subprocess.check_output("docker ps --format \"{{.Names}}\"", shell=True)
    res = str(res, 'utf-8').split("\n")[:-1]

    if configs.container_name in res:
        return True
    else:
        return False

def current_running_image(docker_image_head):
    res = subprocess.check_output("docker images --filter=reference=\"{}*\" --format \"{{{{.Tag}}}} {{{{.ID}}}}\"".format(docker_image_head), shell=True)
    res = str(res, 'utf-8').split("\n")[:-1]
    res = [i.split(" ") for i in res]
    res = natsort.natsorted(res, key = lambda x: x[0], reverse=True)
    # print(res)

    c_image_id = None
    c_image_name = None
    c_res = subprocess.check_output("docker ps --format \"{{.Names}} {{.Image}}\"", shell=True)
    c_res = str(c_res, 'utf-8').split("\n")[:-1]
    c_res = [i.split(" ") for i in c_res]
    # print(c_res)

    for container_name, image in c_res:
        if container_name == configs.container_name:
            c_image_id = image
            # print(c_image_id)
        
    if c_image_id is not None:
        for image_name, image_id in res:
            if image_id == c_image_id:
                # print(image_name)
                c_image_name = image_name
    
    return c_image_name

def docker_image_sort(a, b): 
    a_ver = a[0][a[0].find('_v') + 2 :]
    b_ver = b[0][b[0].find('_v') + 2 :]
    
    if a_ver > b_ver:
        return -1
    elif a_ver == b_ver:
        if "res" in a[0] and "dev" in b[0]:
            return -1
        elif "dev" in a[0] and "res" in b[0]:
            return 1
        else:
            return 0
    else:
        return 1

def find_lastest_docker_image(docker_repo, mode=0):
    docker_image_tag_header_list = configs.docker_image_tag_header_list
    
    candidate_group = []
    
    for tag_header in docker_image_tag_header_list:
        docker_image_head = docker_repo + ":" + tag_header
        
        res = subprocess.check_output("docker images --filter=reference=\"{}*\" --format \"{{{{.Tag}}}} {{{{.ID}}}}\"".format(docker_image_head), shell=True)
        res = str(res, 'utf-8').split("\n")[:-1]
        if len(res) == 0:
            continue
        
        res = [i.split(" ") for i in res]

        res = natsort.natsorted(res, key = lambda x: x[0], reverse=True)
    
        if mode == 1:
            print(f"\n{docker_image_head} docker image list")
            for i in res:
                print('  ', i)
    
        candidate_group.append(res[0])
        
    res2 = sorted(candidate_group, key=cmp_to_key(docker_image_sort))[0]
    
    configs.docker_image_tag_header = res2[0][:res2[0].find("_v")]
        
    return res2

def docker_pull(docker_repo, last_docker_image_dockerhub):
    if configs.docker_id == None or configs.docker_pw == None:
        configs.docker_id = input("UserID for 'https://hub.docker.com/': ")
        configs.docker_pw = getpass.getpass("Password for 'https://hub.docker.com/': ")        
    subprocess.run(f"docker login docker.io -u \"{configs.docker_id}\" -p \"{configs.docker_pw}\"", shell=True)
    subprocess.run("docker pull {}".format(docker_repo + ":" + last_docker_image_dockerhub), shell=True)
    subprocess.run("docker logout", shell=True)

def docker_image_tag_api(image):
    docker_api_host = "https://registry.hub.docker.com"
    path = "/v1/repositories/" + image + "/tags"
    url = docker_api_host + path
    if configs.docker_id == None or configs.docker_pw == None:
        configs.docker_id = input("UserID for 'https://hub.docker.com/': ")
        configs.docker_pw = getpass.getpass("Password for 'https://hub.docker.com/': ")   
    # print(url)
    try:
        response = requests.get(url,auth = HTTPBasicAuth(configs.docker_id, configs.docker_pw))

        # print("response status : %r" % response.status_code)
        return response.json()
    except Exception as ex:
        print(ex)
        return None
    
def search_dockerhub_last_docker_image(docker_repo):
    # res = docker_image_tag_api('intflow/edgefarm')
    res = docker_image_tag_api(docker_repo)
    
    current_image = find_lastest_docker_image(docker_repo)[0]
    
    if res is not None:
        image_tag_list = []

        for each_r in res:
            # print(each_r["name"])
            # if "hallway_dev" in each_r["name"]:
            if configs.docker_image_tag_header in each_r["name"]:
                # print(each_r["name"])
                image_tag_list.append(each_r["name"])
                
        image_tag_list = natsort.natsorted(image_tag_list, key = lambda x: x, reverse=True)
        
        if len(image_tag_list) > 0:
            if current_image is None:
                update_history = len(image_tag_list)
            else:
                if current_image in image_tag_list:
                    update_history = image_tag_list.index(current_image)
                else:
                    update_history = -1
            return [image_tag_list[0], update_history]
        else:
            return ["None", -1]
    else:
        return ["None", -1]

def send_api(path, mac_address, e_version):
    # url = configs.API_HOST + path + '/' + mac_address+ '/' + e_version
    url = configs.API_HOST + path + '/' + mac_address

    print(url)
    
    try:
        # response = requests.put(url)
        response = requests.get(url)

        print("response status : %r" % response.status_code)
        return response.json()
    except Exception as ex:
        print(ex)
        return None
    
def copy_edgefarm_config(mode="default"):
    # print(f"cp {os.path.join(current_dir, 'edgefarm_config/edgefarm_config.json')} /edgefarm_config/edgefarm_config.json")
    # subprocess.run(f"sudo cp {os.path.join(current_dir, 'edgefarm_config/edgefarm_config.json')} /edgefarm_config/edgefarm_config.json", shell=True)
    
    config_list = os.listdir(os.path.join(current_dir, 'edgefarm_config'))
    for e_f in config_list:
        file_path = os.path.join(current_dir, f'edgefarm_config/{e_f}')
        if mode != "all":
            if e_f in configs.not_copy_edgefarm_config_list:
                continue
        if os.path.isdir(file_path):
            subprocess.run(f"sudo cp -r {file_path} /edgefarm_config/", shell=True)
        else:
            subprocess.run(f"sudo cp {file_path} /edgefarm_config/", shell=True)
        print(f"copy {file_path} to /edgefarm_config/")
        

def key_match(src_key, src_data, target_data):
    if src_key in configs.key_match_dict:
        target_key = configs.key_match_dict[src_key]
        if target_key in target_data:
            target_val = target_data[target_key]
            print(f"{src_key} : {src_data[src_key]} -> {target_val}")
            src_data[src_key] = target_val 

def device_install():
    # mac address 뽑기
    mac_address = getmac.get_mac_address().replace(':','')
    docker_repo = configs.docker_repo
    docker_image, docker_image_id = find_lastest_docker_image(docker_repo)
    docker_image_tag_header = configs.docker_image_tag_header
    e_version=docker_image.replace(docker_image_tag_header+'_','').split('_')[0]
    # device 정보 받기 (api request)
    device_info = send_api(configs.server_api_path, mac_address, e_version)
    
    # /edgefarm_config 가 없으면 전체 복사
    if os.path.isdir("/edgefarm_config") == False:
        os.makedirs("/edgefarm_config", exist_ok=True)
        copy_edgefarm_config(mode="all")

    # if device_info is not None:
    if device_info is not None and len(device_info) > 0:
        # 정보 받아왔으면 일단 edgefarm_config 들 복사
        copy_edgefarm_config()
        print(device_info)
        device_info = device_info[0]

        # file read
        with open(configs.edgefarm_config_path, "r") as edgefarm_config_file:
            edgefarm_config = json.load(edgefarm_config_file)
        for key, val in edgefarm_config.items():
            if key in device_info:
                if key in configs.not_copy_DB_config_list:
                    continue
                else:
                    print(f'{key} : {val} -> {device_info[key]}')
                    edgefarm_config[key] = device_info[key]
            else:
                key_match(key, edgefarm_config, device_info)

        # file save
        with open(configs.edgefarm_config_path, "w") as edgefarm_config_file:
            json.dump(edgefarm_config, edgefarm_config_file, indent=4)

        # rtsp address set
        if 'default_rtsp' in device_info:
            rtsp_src_address = device_info['default_rtsp']
            print(f"\nRTSP source address : {rtsp_src_address}\n")
            if rtsp_src_address is not None:
                with open('/edgefarm_config/rtsp_address.txt', 'w') as rtsp_src_addr_file:
                    rtsp_src_addr_file.write(rtsp_src_address)

    else:
        print("device_info is None!")
        # file read
        with open(configs.edgefarm_config_path, "r") as edgefarm_config_file:
            edgefarm_config = json.load(edgefarm_config_file)
        
        # edgefarm_config["device_id"] = -1
            
        # file save
        with open(configs.edgefarm_config_path, "w") as edgefarm_config_file:
            json.dump(edgefarm_config, edgefarm_config_file, indent=4)
    

def docker_log_end_print():
    print("\n===========================================")
    print("       View docker log mode End")
    print("===========================================\n")
    # control_thread_mutex.release()
    
def docker_log_view():
    ## docker log 보는 subprocess 실행
    docker_log = subprocess.Popen(f"docker logs -f -t {configs.container_name}", stdout=subprocess.PIPE, shell=True)

    while docker_log.poll() == None:
        out = docker_log.stdout.readline()
        print(out.decode(), end='')

    docker_log_end_print()

def show_docker_images_list(docker_image_head):
    subprocess.run("docker images --filter=reference=\"{}*\"".format(docker_image_head), shell=True)
 

def run_blackBox():
    subprocess.run("/home/intflow/works/efpc_box/bin/efpc_box")

if __name__ == "__main__":
    # subprocess.call(f"docker login docker.io -u \"{configs.docker_id}\" -p \"{configs.docker_pw}\"", shell=True)
    # subprocess.run("docker logout", shell=True)
    
    # docker_image, docker_image_id = find_lastest_docker_image("intflow/efpc_f")
    # print(docker_image[:docker_image.find("_v")])
    
    # print(configs.docker_image_tag_header)
    copy_edgefarm_config()

