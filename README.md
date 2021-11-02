# MapsToGazebo

This project take blueprints of 2d maps of rooms and convert them to 3d gazebo maps (meshes).

The project is based on https://github.com/shilohc/map2gazebo, and require it in order to work.\

The project take the 2d blueprints find their enrty points (the doors) and convert them to 3d as the doors are the 0,0 point at the gazebo, each door is like a new room. The final output should look like that:

        meshes/
        |── 1
        |   |── map_1_1.stl
        |   |── map_1_2.stl
        |── map_2_1.stl
        |── map_3_1.stl
        |── 4
        |   |── map_4_1.stl
        |   |── map_4_2.stl
        |   |── map_4_4.stl

Each room with more than one door gets a folder and each file is the same map with different door as the 0,0
room with only one door is without folder,
and a room with no doors is an empty folder.



There are two parts to the project.

# Find doors

Each room has entry points and we need to locate them in order to place the room in the gazebo at 0,0
First we find all the doors in each rooms, and then we check if its an outside door. 
Then there are 4 possabilities for the side of the door, and each side gets identifier so later we can rotate the door to be in the right location.
All the data about the doors saved to `pickle` file.

*** all the doors must be horizontal or vertical, otherwise it won't work. ***

for that just run `outside_doors.py`.

# Map to gazebo

Then we take all the doors we found, load them from the pickle file, broadcast each one with `map_server` and process with `map2gazebo`.
`map2gazebo` is not meant to be used for a lot of doors at once, thats why we need to restart him sometimes, and for that we have `refresh_map2gazebo.py` which taking care of it.

in order for that to work, install map2gazebo in the workspace https://github.com/shilohc/map2gazebo, and copy this `map2gazebo.py` file to theirs.
than copy `refresh_map2gazebo.py` to the same folder and run it.
after some time all the meshes will be in `map2gazebo/models/map/meshes`.
*** it is important to change the meshes path in all the relevent python files ***

if you want to validate that all the files created successfully, run `validateRoomMissing.py`, if there is no output, all the rooms are successfully created.

# Gazebo

In order to see the map in the gazebo, go to `map2gazebo/models/map/model.sdf` and change the two uri's to the path of the map you want to see. 
than run 
```
roslaunch map2gazebo gazebo_world.launch
```
