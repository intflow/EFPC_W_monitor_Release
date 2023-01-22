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
import psutil
from pathlib import Path

import datetime as dt
import pytz
from functools import cmp_to_key
from dateutil import parser


current_dir = os.path.dirname(os.path.abspath(__file__))

def docker_log_save_start():
    os.makedirs(configs.log_save_dir_path, exist_ok=True)
    
    now_dt = dt.datetime.now()

    # print(now_dt.strftime("%Y%m%d_%H%M%S_log"))
    
    file_name = now_dt.strftime("%Y%m%d_%H%M%S.log")
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
    
def port_info_set():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    configs.last_ip=s.getsockname()[0].split('.')[-1]

    with open(configs.edgefarm_port_info_path, 'r') as port_info_f:
        content = port_info_f.readlines()
        num_line = len(content)

        if configs.last_ip is not None:
            if num_line >= 3:
                udp_host = "224.224.255." + configs.last_ip + "\n"
                content[2] = udp_host

    with open(configs.edgefarm_port_info_path, 'w') as port_info_f:
        port_info_f.writelines(content)

def kill_edgefarm():
    subprocess.run(f"docker exec -it {configs.container_name} bash ./kill_edgefarm.sh", shell=True)

def run_docker(docker_image, docker_image_id):
    edgefarm_config_check()
    fan_speed_set(configs.FAN_SPEED)
    port_info_set()
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
                        + "-v /etc/localtime:/etc/localtime:ro "\
                        + "-v /etc/timezone:/etc/timezone:ro "\
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

def export_model(docker_image, docker_image_id, mode=""):
    if docker_image == None or docker_image_id == None:
        for i in range(10):
            print("\nNo Docker Image...\n")
        return -1
    print("export model!\n")
    
    # sync mode 는 background 에서 실행안하고 끝날 때까지 기다림.
    if mode == "sync":
        run_docker_command = "docker run -i "\
                                + "--rm "\
                                + f"--name={configs.model_export_container_name} "\
                                + "--net=host "\
                                + "--privileged "\
                                + "--ipc=host "\
                                + "--runtime nvidia "\
                                + "-v /edgefarm_config:/edgefarm_config "\
                                + "-v /home/intflow/works:/works "\
                                + "-w /edgefarm_config/ "\
                                + f"{docker_image_id} bash ./export_model.sh"
    else:
        run_docker_command = "docker run -di "\
                                + "--rm "\
                                + f"--name={configs.model_export_container_name} "\
                                + "--net=host "\
                                + "--privileged "\
                                + "--ipc=host "\
                                + "--runtime nvidia "\
                                + "-v /edgefarm_config:/edgefarm_config "\
                                + "-v /home/intflow/works:/works "\
                                + "-w /edgefarm_config/ "\
                                + f"{docker_image_id} bash ./export_model.sh"
    # print(run_docker_command)
    subprocess.call(run_docker_command, shell=True)


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

## 실행 중이면 True, 실행 중이 아니면 False 반환.
def check_model_export_status():
    res = subprocess.check_output("docker ps --format \"{{.Names}}\"", shell=True)
    res = str(res, 'utf-8').split("\n")[:-1]

    if configs.model_export_container_name in res:
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
        
    if len(candidate_group) == 0:
        return ["None", "None"]
        
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
def send_json_api(path, mac_address,serial_number,firmware_version):
    url = configs.API_HOST2 + path + '/' 
    content={}
    content['mac_address']=mac_address
    content['serial_number']=serial_number
    content['version']=firmware_version
    print(url)
    
    try:
        # response = requests.post(url, data=json.dumps(metadata))
        response = requests.put(url, json=content)

        print("response status : %r" % response.status_code)
        if response.status_code == 200:
            # return True
            return response.json()
        else:
            # return False
            return None
        # return response.json()
    except Exception as ex:
        print(ex)
        # return False
        return None
def copy_to(src_path, target_path):
    if os.path.isdir(src_path):
        subprocess.run(f"sudo cp -rfa {src_path} {target_path}", shell=True)
    else:
        subprocess.run(f"sudo cp -fa {src_path} {target_path}", shell=True)
    print(f"copy {src_path} to {target_path}")

def read_serial_number():
    with open(os.path.join(configs.local_edgefarm_config_path, "serial_number.txt"), 'r') as mvf:
        serial_numbertxt = mvf.readline()
    return serial_numbertxt.split('\n')[0]

def read_firmware_version():
    with open(os.path.join(configs.firmware_dir, "__version__.txt"), 'r') as mvf:
        firmware_versiontxt = mvf.readline()
    return firmware_versiontxt.split('\n')[0]

def model_update_check(check_only = False):
    print("Check Model version...")
    lastest = True
    
    serial_number = read_serial_number()

    model_file_name = f"{serial_number}/{configs.server_model_file_name}"
    local_model_file_path = os.path.join(configs.local_edgefarm_config_path, configs.local_model_file_relative_path)
    
    print(f"s3://{configs.server_bucket_of_model}/{model_file_name}")

    try:
        res = subprocess.check_output(f"aws s3api head-object --bucket {configs.server_bucket_of_model} --key {model_file_name}", shell=True)
    except Exception as e:
        print("Can not find model file in server!")
        return False
        
    res_str = res.decode()

    model_file_metadata = json.loads(res_str)
    model_file_metadata["LastModified"]

    last_modified_server_string = model_file_metadata["LastModified"]
    last_modified_server = parser.parse(last_modified_server_string)

    kst = pytz.timezone('Asia/Seoul')

    last_modified_server = last_modified_server.astimezone(kst)

    last_modified_local = os.path.getmtime(local_model_file_path)

    last_modified_local = dt.datetime.fromtimestamp(last_modified_local)
    last_modified_local = kst.localize(last_modified_local)

    print(f"  server : {last_modified_server}")
    print(f"  local  : {last_modified_local}")

    #date_kst
    if last_modified_server > last_modified_local:
        print("Model Update required...")
        lastest = False
    elif last_modified_server <= last_modified_local:
        print("Lastest version of model")

    if not check_only and lastest == False:
        # 혹시 엣지팜 켜져있으면 끄기.
        while check_deepstream_status():
            print("Try to kill Edgefarm Engine...")
            kill_edgefarm()
            time.sleep(1)
        # model 업데이트하기
        model_update(mode='sync')

def model_update(mode=""):
    # /edgefarm_config/model 디렉토리가 없으면 생성.
    if not os.path.exists(os.path.join(configs.local_edgefarm_config_path, "model")):
        os.makedirs(os.path.join(configs.local_edgefarm_config_path, "model"), exist_ok=True)
        
    serial_number = read_serial_number()
    
    print("Start Model Update!")
    
    model_file_name = f"{serial_number}/{configs.server_model_file_name}"
    local_model_file_path = os.path.join(configs.local_edgefarm_config_path, configs.local_model_file_relative_path)
    
    # 서버에서 모델 파일 복사해오기
    # copy_to(os.path.join(git_edgefarm_config_path, "model/intflow_model.onnx"), os.path.join(configs.local_edgefarm_config_path, "model/intflow_model.onnx"))
    subprocess.run(f"aws s3 cp s3://{configs.server_bucket_of_model}/{model_file_name} {local_model_file_path}", shell=True)
    
    docker_image, docker_image_id = find_lastest_docker_image(configs.docker_repo)
    # onnx to engine
    export_model(docker_image, docker_image_id, mode=mode)
    # # 버전 파일 복사.
    if mode == "sync" : print("\nModel Update Completed")

def edgefarm_config_check():
    # /edgefarm_config 가 없으면 전체 복사
    if os.path.isdir("/edgefarm_config") == False:
        subprocess.run("sudo mkdir /edgefarm_config", shell=True)
        print("make directory /edgefarm_config")
    subprocess.run("sudo chown intflow:intflow -R /edgefarm_config", shell=True)
    
    git_edgefarm_config_path = os.path.join(current_dir, "edgefarm_config")
    
    # 모델 관련 파일이 있나 검사. 하나라도 없으면 복사해주고 모델 export
    model_related_list = ['model', 'model/intflow_model.onnx', 'model/intflow_model.engine']
    no_model = False
    for m_i in model_related_list:
        tmp_p = os.path.join(configs.local_edgefarm_config_path, m_i)
        if not os.path.exists(tmp_p):
            no_model = True
    if no_model:    
        model_update(mode='sync')
    
    # 디렉토리 내부 검색을 위한 일회용 재귀함수.
    def listdirs(rootdir):
        for path in Path(rootdir).iterdir():
            path_str = str(path)
            local_path_str = path_str.replace(git_edgefarm_config_path, configs.local_edgefarm_config_path)
                
            local_path = Path(local_path_str)
                
            # /edgefarm_config 에 없으면 복사하기.
            if local_path.exists() == False:
                copy_to(path_str, str(local_path.parent))
            # 있더라도 configs.MUST_copy_edgefarm_config_list 목록에 있으면 무조건 복사.
            elif path.name in configs.MUST_copy_edgefarm_config_list:
                copy_to(path_str, str(local_path.parent))
                
            if path.is_dir():
                listdirs(path)
                
    listdirs(git_edgefarm_config_path) 

def key_match(src_key, src_data, target_data):
    if src_key in configs.key_match_dict:
        target_key = configs.key_match_dict[src_key]
        if target_key in target_data:
            target_val = target_data[target_key]
            print(f"{src_key} : {src_data[src_key]} -> {target_val}")
            src_data[src_key] = target_val 
            
def add_key_to_edgefarm_config():
    # 만약 이 repo 에 있는 edgefarm_config.json 의 키가 /edgefarm_config/edgefarm_config.json 에 없으면 해당 키만 추가해주기.
    # file read
    with open(configs.edgefarm_config_json_path, "r") as edgefarm_config_file:
        edgefarm_config = json.load(edgefarm_config_file)
        
    with open(os.path.join(current_dir, "edgefarm_config/edgefarm_config.json"), "r") as edgefarm_config_file:
        edgefarm_config_git = json.load(edgefarm_config_file)

    print()
    for key in edgefarm_config_git.keys():
        if key not in edgefarm_config:
            print(f"\"{key}\" is not in \"{configs.edgefarm_config_json_path}\".\nAdd \"{key}\" to \"{configs.edgefarm_config_json_path}\"\n")
            edgefarm_config[key] = edgefarm_config_git[key]

    # file save
    with open(configs.edgefarm_config_json_path, "w") as edgefarm_config_file:
        json.dump(edgefarm_config, edgefarm_config_file, indent=4)    

def device_install():
    # 만약 이 repo 에 있는 edgefarm_config.json 의 키가 /edgefarm_config/edgefarm_config.json 에 없으면 해당 키만 추가해주기.
    
    # mac address 뽑기
    mac_address = getmac.get_mac_address()
    serial_number=read_serial_number()
    firmware_version=read_firmware_version()
    docker_repo = configs.docker_repo
    docker_image, docker_image_id = find_lastest_docker_image(docker_repo)
    docker_image_tag_header = configs.docker_image_tag_header
    e_version=docker_image.replace(docker_image_tag_header+'_','').split('_')[0]
    device_info=send_json_api(configs.access_api_path, mac_address, serial_number, firmware_version)
    # device 정보 받기 (api request)
    # device_info = send_api(configs.server_api_path, mac_address, e_version)
    
    edgefarm_config_check()
    
    add_key_to_edgefarm_config()

    # if device_info is not None:
    if device_info is not None and len(device_info) > 0:
        # 정보 받아왔으면 일단 edgefarm_config 들 복사
        print(device_info)

        # file read
        with open(configs.edgefarm_config_json_path, "r") as edgefarm_config_file:
            edgefarm_config = json.load(edgefarm_config_file)
        edgefarm_config['device_id']=device_info['id']
        edgefarm_config['end_interval']=device_info['camera_list'][0]['end_interval']
        edgefarm_config['reboot_time']=device_info['reboot_time']
        edgefarm_config['update_time']=device_info['update_time']
        edgefarm_config['upload_time']=device_info['upload_time']
        edgefarm_config['linegap']=device_info['camera_list'][0]['linegap']
        edgefarm_config['linegap_position']=device_info['camera_list'][0]['linegap_position']
        edgefarm_config['cam_id']=device_info['camera_list'][0]['id']
        rtsp_src_address=device_info['camera_list'][0]["rtsp"]
        edgefarm_config['language']=device_info['language_info']["id"]
        # file save
        with open(configs.edgefarm_config_json_path, "w") as edgefarm_config_file:
            json.dump(edgefarm_config, edgefarm_config_file, indent=4)
        # rtsp address set
        with open('/edgefarm_config/rtsp_address.txt', 'w') as rtsp_src_addr_file:
            rtsp_src_addr_file.write(rtsp_src_address)
        
        # update time set
        update_time_str = ""
        if "update_time" in device_info:
            update_time_str = device_info["update_time"]
        # else:

        if len(update_time_str) > 0:
            update_time_slice = update_time_str.split(":")
            if len(update_time_slice) == 3:
                configs.update_hour, configs.update_min, configs.update_sec = list(map(int,update_time_slice))
            else:
                print("Invalid data type : \"update_time\"")
        else:
            configs.update_hour, configs.update_min, configs.update_sec = [23, 50, 0]        

    else:
        print("device_info is None!")
        # file read
        with open(configs.edgefarm_config_json_path, "r") as edgefarm_config_file:
            edgefarm_config = json.load(edgefarm_config_file)
        
        edgefarm_config["device_id"] = -1
        edgefarm_config["cam_id"] = -1
            
        # file save
        with open(configs.edgefarm_config_json_path, "w") as edgefarm_config_file:
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
    
def send_ak_api(path, mac_address, serial_number):
    url = configs.API_HOST2 + path + '/' 
    content={}
    content['mac_address']=mac_address
    content['serial_number']=serial_number
    print(url)
    
    try:
        # response = requests.post(url, data=json.dumps(metadata))
        response = requests.put(url, json=content)

        print("response status : %r" % response.status_code)
        if response.status_code == 200:
            # return True
            return response.json()
        else:
            # return False
            return None
        # return response.json()
    except Exception as ex:
        print(ex)
        # return False
        return None    
    
def check_aws_install():
    res = os.popen('which aws').read()

    if "/usr/local/bin/aws" in res:
        print("AWS CLI installed")
        pass
    else:
        print("Install AWS CLI ...")
        subprocess.run("bash ./aws_cli_build.sh", shell=True)
        
    mac_address = getmac.get_mac_address()
    serial_number=read_serial_number()
        
    akres = send_ak_api("/device/upload/key", mac_address, serial_number)

    if not os.path.isdir("/home/intflow/.aws"):
        os.makedirs("/home/intflow/.aws", exist_ok=True)
        
    subprocess.run('sudo chown intflow:intflow /home/intflow/.aws -R', shell=True)

    with open("/home/intflow/.aws/credentials", "w") as f:
        f.write(f"[default]\naws_access_key_id = {akres['access']}\naws_secret_access_key = {akres['secret']}\n")

def show_docker_images_list(docker_image_head):
    subprocess.run("docker images --filter=reference=\"{}*\"".format(docker_image_head), shell=True)
    
def set_background():
    subprocess.Popen(f"pcmanfm --set-wallpaper=\"{os.path.join(current_dir, 'imgs/intflow_wallpaper.jpg')}\"", shell=True)

def run_blackBox():
    subprocess.run("xrandr -s 640x480", shell=True)
    subprocess.run("/home/intflow/works/firmwares/efpc_box", shell=True)
    
def is_process_running(process_name):
    # Iterate over all running processes
    for process in psutil.process_iter():
        # Get the name of the process
        name = process.name()
        # Check if the process name matches the specified name
        if name == process_name:
            return True
    return False

def KST_timezone_set():
    subprocess.run("sudo ln -sf /usr/share/zoneinfo/Asia/Seoul /etc/localtime", shell=True)
    print("Set TimeZone to Seoul")

if __name__ == "__main__":
    # device_install()
    set_background()
    
    model_update_check(check_only = True)


