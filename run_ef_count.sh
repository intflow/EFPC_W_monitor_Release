#!/bin/bash

export DISPLAY=:0
export XHOST_OK=0

#sleep 120s

LOG_FILE=/home/intflow/works/logs/$(date +%Y%m%d_%H%M%S)_monitor.log

while [ true ] ; do

        xhost + && export XHOST_OK=1

        if [ ${XHOST_OK} -eq 1 ] ; then
                echo "DISPLAY=${DISPLAY}"

                sudo jetson_clocks
                sudo sh -c 'echo 150 > /sys/devices/pwm-fan/target_pwm'

                python3 ./for_supervisor.py > "$LOG_FILE" 2>&1

                break
        else
                echo "NO DISPLAY"
                sleep 0.5s
        fi
done
