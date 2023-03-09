FAN_SPEED = 150

API_HOST = "http://intflowserver2.iptime.org:20051"
API_HOST2 = "http://intflowserver2.iptime.org:60080"

docker_repo = "intflow/efpc_w"
docker_image_tag_header_list = ["dev", "res"] # res 우선
docker_image_tag_header = "None" # Don't Touch!! 수정하지 말고 놔두기!! 자동으로 잡음.

local_edgefarm_config_path = "/edgefarm_config"
edgefarm_config_json_path = "/edgefarm_config/edgefarm_config.json"
edgefarm_port_info_path = "/edgefarm_config/port_info.txt"
edgefarm_rtsp_txt_path="/edgefarm_config/rtsp_address.txt"
container_name = "edgefarm_docker"
model_export_container_name = "export_model"
server_bucket_of_model = "intflow-models"
server_bucket_of_log = "intflow-log"
server_model_file_name = "intflow_model.onnx"
local_model_file_relative_path = "model/intflow_model.onnx"
local_engine_file_relative_path = "model/intflow_model.engine"
commit_container_name = "for_commit"

key_match_dict = {
    'cam_id' : 'id'
}

MUST_copy_edgefarm_config_list=[] 
not_copy_DB_config_list=[
    'hallway_width_pixel',
    'hallway_width_cm',
    'vpi_k1',
    'zy_perspect',
    'zx_perspect',
    'x_focus',
    'y_focus',
    'y_rotate',
    'x_rotate',
    'direction',
    'limit_max_weight',
    'weight_bias',
    'ship_direction',
    'reference_weight']

server_api_path = "/device/info"
access_api_path = "/device/access"

last_ip = None

log_save_dir_path = "/home/intflow/works/logs/"
log_max_volume = 536870912 # bytes 단위 3달은 버팀.
# log_max_volume = 200000 # bytes 단위 3달은 버팀.

firmware_dir = "/home/intflow/works/firmwares"

update_hour, update_min, update_sec = [23,50,0]

internet_ON = False

SHM_KEY = 3309
