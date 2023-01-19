# model 업데이트 하기
## 1. onnx 파일 넣기
.onnx 파일을 git repo의 `edgefarm_config/model/`에 넣기
## 2. model_version.txt 업데이트하기
`edgefarm_config/model/model_version.txt` 파일을 열어서 버전을 올려준다.<br>
`model_version.txt` 파일 예시
```
1.0.0.0
```
## 3. commit 및 push 하기
위의 과정이 완료되면 commit & push를 해준다.
<br>
<br>


# 0 
```
cd /home/intflow/works
git clone {현재 레포 주소}
```
# <span style="color:red"> 필수 적용 사항!!!!!!!!!!!!!!!!!!!!!!!!!!!!</span>
**사용자 계정에 sudo 명령어를 비밀번호 없이 쓸 수 있도록 사전 설정을 해야한다.**
```
sudo visudo
```
위 명령어로 파일이 열리면<br>
파일 맨 아래에 아래의 내용을 추가한다.<br>
<span style="color:red">**(한 글자라도 틀리면 계정 접속 안되므로 주의!!!)**</span><br>
<span style="color:red">**(NOPASSWORD 아님. NOPASSWD 임)**</span>
```
{사용자계정이름} ALL=NOPASSWD: ALL

ex)
intflow ALL=NOPASSWD: ALL
```

---
<br>

# 1. `edgefarm_config` 디렉토리 복사하기
```
cp -r ./edgefarm_config /
```
`edgefarm_config` 디렉토리 채로 최상단 디렉토리(`/`)로 복사.<br><br>
**그리고 권한 바꿔주기**
```
sudo chmod 777 -R /edgefarm_config/
```
<br>

# 2. 각 엣지 디바이스에 맞는 모델 변경 
Set the model to load on its own device
```
/edgefarm_config/model/intflow_model.engine # 여기에 edgefarm model 넣어줘야함 
```


# 3. dependency
## 마우스 커서 없애기
### 1.Install Unclutter and Create a file called ".unclutter" in your home directory
```
sudo apt install unclutter -y
touch ~/.unclutter
```
### 2. Open the ".unclutter" file in a text editor
```
nano ~/.unclutter
```
### 3. Add the following line to the file
```
unclutter -idle 0.1 -root
```
Save and close the file.
### 4. To start Unclutter at boot
```
mkdir -p ~/.config/lxsession/LXDE-pi/
nano ~/.config/lxsession/LXDE-pi/autostart
```
you can add the following line to your "~/.config/lxsession/LXDE-pi/autostart" file
```
@unclutter -idle 0.1 -root
```
Save and close the file.<br>
### 5. reboot
<br>

## python libraries
```
sudo apt install -y python3-pip && \
python3 -m pip install pip getmac natsort gitpython psutil
```
## opencv
```
bash opencv_build.sh
```
## RapidJson
```
bash rapidjson_build.sh
```
## JetsonGPIO
```
bash jetsongpio_build.sh
```
<br>

# 4. docker 권한변경
```
sudo usermod -aG sudo $USER
sudo usermod -aG docker $USER
sudo chown -R $USER:$USER /home/$USER/.docker
```
로그아웃 후 재로그인 혹은 ssh 다시 접속



# 5. SmartRecord seTTing 
- /edgefarm_config/Smart_Record.txt파일 
```
Smart_Recoding  # 녹화할 영상의 title ex)darvi_hallway 
/edgefarm_config/Recording   # 녹화 동영상 path  , docker에서 돌았을때 저장 될  path로 설정
```


# 6. auto runs service 
```
bash autorun_service_registration.sh
```

# 7. service_down.sh
### lightdm 디스플레이로 변경됨
```
#!/bin/bash
systemctl stop networkd-dispatcher.service
systemctl stop snapd.seeded.service
systemctl stop snapd.socket
systemctl stop snapd.service
systemctl stop lightdm.service
systemctl stop ModemManager.service
systemctl stop apt-daily.timer
systemctl stop apt-daily.service
systemctl stop apt-daily-upgrade.timer
systemctl stop apt-daily-upgrade.service
systemctl stop fwupd.service
systemctl stop speech-dispatcher.service
systemctl stop wpa_supplicant.service

systemctl disable networkd-dispatcher.service
systemctl disable snapd.seeded.service
systemctl disable snapd.socket
systemctl disable snapd.service
systemctl disable lightdm.service
systemctl disable ModemManager.service
systemctl disable apt-daily.timer
systemctl disable apt-daily.service
systemctl disable apt-daily-upgrade.timer
systemctl disable apt-daily-upgrade.service
systemctl disable fwupd.service
systemctl disable speech-dispatcher.service
systemctl disable wpa_supplicant.service

sudo apt remove --purge -y gdm3
sudo apt remove --purge -y lightdm
sudo apt autoremove --purge -y
sudo apt install lightdm
```
## lightdm 디스플레이모드일때 auto login 하는법
sudo nano /etc/lightdm/lightdm.conf
```
[SeatDefaults]
autologin-user=intflow
autologin-user-timeout=0
user-session=ubuntu
# Uncomment the following, if running Unity
#greeter-session=unity-greeter
```
## screensaver 끄는법 
sudo nano ~/.xscreensaver

mode off 하거나 timeout , cycle 을 0으로 변경하고 저장

# 8. 바탕화면 파일 및 폴더들 지우기
```
rm -rf /home/intflow/Desktop/*
```

# 9. 바탕화면 바꾸기
```
bash set_background.sh
```

