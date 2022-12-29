#!/bin/bash

git clone https://github.com/pjueon/JetsonGPIO && \
if [ -d "./JetsonGPIO" ]; then
    cd JetsonGPIO
    mkdir build && cd build && \
    sudo cmake .. && \
    time sudo make -j4 && \
    sudo make install && \
    cd ../../ && \
    sudo rm -rf JetsonGPIO/
fi