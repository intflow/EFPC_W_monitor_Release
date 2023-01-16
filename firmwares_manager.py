import git
import os
import configs
from utils import *
import shutil
import subprocess
import json
import datetime as dt

git_pull_done = False
c_dir = os.path.dirname(os.path.abspath(__file__))

def copy_firmwares():    
    firmware_path = os.path.join(c_dir, "firmwares")
    
    all_files = os.listdir(firmware_path)
    
    print("Copy Firmwares : ./firmwares/ to /home/intflow/works/firmwares/")
    
    for i in all_files:
        file_path = os.path.join(firmware_path, i)
        target_path = os.path.join(configs.firmware_dir, i)
        
        if os.path.isdir(file_path):
            target_path = configs.firmware_dir
            subprocess.run(f"sudo cp -ra {file_path} {target_path}", shell=True)
        else:
            # shutil.copy2(file_path, target_path)
            subprocess.run(f"sudo cp -a {file_path} {target_path}", shell=True)
        
        print(f"cp {file_path} {target_path}")
    
    print("Copy Firmwares Completed !!\n\n")
    

def git_pull():
    global git_pull_done, c_dir
    
    now_dt = dt.datetime.now()
    # print(now_dt)
          
    # pull 받기
    if now_dt.hour == configs.update_hour and now_dt.minute == configs.update_min:
    # if now_dt.hour == 16 and now_dt.minute >= 38:
        try:
            if git_pull_done == False:
                print("\n  git pull from remote repository")
                git_dir = c_dir  
                repo = git.Repo(git_dir)
                # 변경사항 지우기
                repo.head.reset(index=True, working_tree=True)
                # pull 받기
                repo.remotes.origin.pull()
                # repo.remotes.release.pull() # 개발용
                print("  Done\n")
                
                copy_firmwares()
                git_pull_done = True
        except Exception as e:
            print(e)
            pass
    else:
        git_pull_done = False
    
    
if __name__ == "__main__":
    copy_firmwares()
    # git_pull()
