import os 
import time
import subprocess
import shutil

meshes_path = "meshes"
path, dirs, files = next(os.walk(meshes_path))
dirs.sort(key=float)

def find_missing(lst):
    return [x for x in range(lst[0], lst[-1]+1) 
                               if x not in lst]

aray = []
filesdirs = dirs + files

for n in (filesdirs):
    if len(n) > 3:
        n = n.split("_")[1]      
    aray.append(int(n))
aray.sort(key=float)
find_missing(aray)

count = 1 
for n in aray:
    if n != count:
        print count
        count += 1
    count += 1