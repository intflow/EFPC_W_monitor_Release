

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
```
sudo apt install -y python3-pip
python3 -m pip install pip
python3 -m pip install getmac
python3 -m pip install natsort
python3 -m pip install gitpython
python3 -m pip install psutil
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


# 6 auto runs service 
```
bash autorun_service_registration.sh
bash autorun_service_start.sh
```
```
bash autorun_service_stop.sh
```
