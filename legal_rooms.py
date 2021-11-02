import pickle 
import os


meshes_path = "meshes"

path, dirs, files = next(os.walk(meshes_path))
files = [int(file.split("_")[1]) for file in files]

with open("legal_rooms.pickle", "wb") as f:
    pickle.dump(files, f, protocol=pickle.HIGHEST_PROTOCOL)
