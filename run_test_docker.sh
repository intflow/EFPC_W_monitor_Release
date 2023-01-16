#!/bin/bash

container_name="dev_w_1"
docker_image="intflow/efpc_w:res_v0.0.1.1"

docker run -it \
--name=${container_name} \
--net=host \
--privileged \
--ipc=host \
--runtime nvidia \
-v /edgefarm_config:/edgefarm_config \
-v /sys/devices/:/sys/devices \
-v /sys/class/gpio:/sys/class/gpio \
-v /home/intflow/.Xauthority:/root/.Xauthority:rw \
-v /tmp/.X11-unix:/tmp/.X11-unix \
-v /dev/input:/dev/input \
-v /home/intflow/works:/works \
-v /etc/localtime:/etc/localtime:ro \
-v /etc/timezone:/etc/timezone:ro \
-w /opt/nvidia/deepstream/deepstream/sources/apps/sample_apps/ef_custompipline \
${docker_image} bash

