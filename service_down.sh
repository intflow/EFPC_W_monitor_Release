#!/bin/bash

sudo systemctl stop networkd-dispatcher.service
sudo systemctl stop snapd.seeded.service
sudo systemctl stop snapd.socket
sudo systemctl stop snapd.service
sudo systemctl stop lightdm.service
sudo systemctl stop ModemManager.service
sudo systemctl stop apt-daily.timer
sudo systemctl stop apt-daily.service
sudo systemctl stop apt-daily-upgrade.timer
sudo systemctl stop apt-daily-upgrade.service
sudo systemctl stop fwupd.service
sudo systemctl stop speech-dispatcher.service
sudo systemctl stop wpa_supplicant.service

sudo systemctl disable networkd-dispatcher.service
sudo systemctl disable snapd.seeded.service
sudo systemctl disable snapd.socket
sudo systemctl disable snapd.service
sudo systemctl disable lightdm.service
sudo systemctl disable ModemManager.service
sudo systemctl disable apt-daily.timer
sudo systemctl disable apt-daily.service
sudo systemctl disable apt-daily-upgrade.timer
sudo systemctl disable apt-daily-upgrade.service
sudo systemctl disable fwupd.service
sudo systemctl disable speech-dispatcher.service
sudo systemctl disable wpa_supplicant.service

sudo apt remove --purge -y gdm3 lightdm
sudo apt autoremove --purge -y
sudo apt install lightdm