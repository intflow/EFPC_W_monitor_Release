#!/bin/bash

export DISPLAY=:0
export XHOST_OK=0

#sleep 120s

while [ true ] ; do

        xhost + && export XHOST_OK=1

        if [ ${XHOST_OK} -eq 1 ] ; then
                echo "DISPLAY=${DISPLAY}"

                sudo jetson_clocks
                sudo sh -c 'echo 150 > /sys/devices/pwm-fan/target_pwm'

                python3 ./for_supervisor.py

                break
        else
                echo "NO DISPLAY"
                sleep 0.5s
        fi
done
