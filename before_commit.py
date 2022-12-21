import git
import os
import configs
from utils import *
import shutil
import subprocess

git_pull_done = False
c_dir = os.path.dirname(os.path.abspath(__file__))

firmware_list = \
[
    "deepstream-custom-pipeline",    
    "libnvdsparsebbox_yoloxoad.so",    
    "libnvdsgst_dsexample.so",    
    "libnvdsgst_dsexample2.so",    
    "efpc_box",
    "font"
]

def copy_firmwares():    
    firmware_path = os.path.join(c_dir, "firmwares")
    
    all_files = os.listdir(firmware_path)
    
    print("Copy Firmwares : /home/intflow/works/firmwares/ to ./firmwares/")
    
    for i in all_files:
        if i not in firmware_list:
            continue
        
        file_path = os.path.join(configs.firmware_dir, i)
        target_path = os.path.join(firmware_path, i)
        
        if os.path.isdir(file_path):
            target_path = firmware_path
            subprocess.run(f"sudo cp -ra {file_path} {target_path}", shell=True)
        else:
            # shutil.copy2(file_path, target_path)
            subprocess.run(f"sudo cp -a {file_path} {target_path}", shell=True)
        
        print(f"cp {file_path} {target_path}")
    
    print("Copy Firmwares Completed !!\n\n")
    
    
if __name__ == "__main__":
    copy_firmwares()
    