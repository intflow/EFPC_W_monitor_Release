#!/bin/bash

sudo apt install curl -y

curl "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o "awscliv2.zip" && \
if [ -e "./awscliv2.zip" ]; then
    unzip awscliv2.zip && \
    sudo ./aws/install

    sudo rm -rf awscliv2.zip aws
fi