import git
import os
import configs
from utils import *
import shutil
import subprocess

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
    
    KST_timezone = pytz.timezone('Asia/Seoul')
    now_kst = dt.datetime.now().astimezone(KST_timezone)
    # print(now_kst)
    
    # 11시 50분에 pull 받기
    if now_kst.hour == 23 and now_kst.minute >= 50:
    # if now_kst.hour == 16 and now_kst.minute >= 38:
        print("\n  git pull from remote repository")
        try:
            if git_pull_done == False:
                git_dir = c_dir  
                repo = git.Repo(git_dir)
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
    