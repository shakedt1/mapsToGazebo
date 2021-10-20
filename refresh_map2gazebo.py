import os 
import time
import subprocess
import shutil
from roslaunch.parent import ROSLaunchParent

meshes_path = "meshes"
path, dirs, files = next(os.walk(meshes_path))
dirs.sort(key=float)
files.sort(key=lambda file: int(file.split("_")[1]))

if dirs and int(dirs[-1]) > int(files[-1].split("_")[1]):
    shutil.rmtree(meshes_path + "/" + dirs[-1])
    dirs.pop(0)
file_count = len(files) + len(dirs)

while (file_count != 510):
    parent = ROSLaunchParent(str(file_count), [], is_core=True)    
    parent.start()
    time.sleep(3)
    subprocess.Popen("rosrun map2gazebo map2gazebo.py " + str(file_count + 1), shell=True).wait()
    path, dirs, files = next(os.walk(meshes_path))
    dirs.sort(key=float)
    files.sort(key=lambda file: int(file.split("_")[1]))
    if dirs and int(dirs[-1]) > int(files[-1].split("_")[1]):
        shutil.rmtree(meshes_path + "/" + dirs[-1])
        dirs.pop(0)
    file_count = len(files) + len(dirs)
    print("Created " + str(file_count) + " files !!!")
    parent.shutdown()
    time.sleep(3)

