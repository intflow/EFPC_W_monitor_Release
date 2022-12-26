#!/bin/bash

echo ${USER}

git clone https://github.com/Tencent/rapidjson.git
if [ -d "./rapidjson" ]; then
    cd rapidjson
    git submodule update --init
    mkdir build
    cd build
    sudo cmake .. && \
    time sudo make -j4 && \
    sudo make install && \
    sudo rm -rf rapidjson/
fi