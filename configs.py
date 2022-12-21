FAN_SPEED = 150

API_HOST = "http://intflowserver2.iptime.org:20051"

docker_repo = "intflow/efpc_w"
docker_image_tag_header_list = ["dev", "res"] # res 우선
docker_image_tag_header = None # Don't Touch!! 수정하지 말고 놔두기!! 자동으로 잡음.
edgefarm_config_path = "/edgefarm_config/edgefarm_config.json"
edgefarm_port_info_path = "/edgefarm_config/port_info.txt"
container_name = "efhall_test"
commit_container_name = "for_commit"

key_match_dict = {
    'cam_id' : 'id'
}

MUST_copy_edgefarm_config_list=[] # model 업데이트 됐을 때 "model" 추가 시켜주기!
not_copy_DB_config_list=['hallway_width_pixel','hallway_width_cm','vpi_k1','zy_perspect','zx_perspect','x_focus','y_focus','y_rotate','x_rotate']

server_api_path = "/device/info"

last_ip = None

engine_socket_port_end = 70
device_socket_port_end = 71
http_server_port_end = 72

log_save_dir_path = "/home/intflow/works/logs/"
log_max_volume = 536870912 # bytes 단위 3달은 버팀.
# log_max_volume = 200000 # bytes 단위 3달은 버팀.

firmware_dir = "/home/intflow/works/firmwares"
