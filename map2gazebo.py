#!/usr/bin/env python

import cv2
import numpy as np
import trimesh
import os
import yaml
import subprocess
import sys
import time
from matplotlib.tri import Triangulation
import pickle

import rospy
from nav_msgs.msg import OccupancyGrid
from os.path import expanduser
import time

dataset = "dataset/"
rooms_data = "rooms.pickle"
yaml_file_path = os.path.abspath(dataset + "mymap.yaml")

class MapConverter(object):
    def __init__(self, map_topic, threshold=1, height=2.0):
        self.test_map_pub = rospy.Publisher(
                "test_map", OccupancyGrid, latch=True, queue_size=1)
        rospy.Subscriber(map_topic, OccupancyGrid, self.map_callback)
        self.threshold = threshold
        self.height = height
        # Probably there's some way to get trimesh logs to point to ROS
        # logs, but I don't know it.  Uncomment the below if something
        # goes wrong with trimesh to get the logs to print to stdout.
        #trimesh.util.attach_to_log()

    def map_callback(self, map_msg, i=[int(sys.argv[1])], j=[1]):
        time.sleep(3)
        rospy.loginfo("Received map")

        # create folder if more than one door
        folder = ""
        if len(rooms[i[0]]) != 1:
            folder = "/" + str(i[0])

        export_dir = "meshes" + folder
        # if folder is not already exists
        if not os.path.isdir(export_dir):
            os.mkdir(export_dir)

        # no doors    
        if not rooms[i[0]]:
            i[0] += 1
            j[0] = 1
            file_name = dataset + str(i[0]) + ".jpg"
            if os.path.exists(file_name):
                print("map: " + str(i[0]) + "_" + str(j[0]))
                call_map_server(file_name, j[0])

        door = rooms[i[0]][j[0] - 1]
        map_dims = (map_msg.info.height, map_msg.info.width)

        map_array = np.array(map_msg.data).reshape(map_dims)
        
        rotation = door[1]

        # if door is vertical act like map is rotated
        if  rotation > 1:
            map_dims = (map_dims[1], map_dims[0])
            map_msg.info.height, map_msg.info.width = map_msg.info.width, map_msg.info.height 
        
        # just architecture
        if rotation != 0:
            rotation = (rotation % 3) + 1

        map_array = np.rot90(map_array, rotation)
        
        
        # set all -1 (unknown) values to 0 (unoccupied)
        map_array[map_array < 0] = 0
        contours = self.get_occupied_regions(map_array)
        meshes = [self.contour_to_mesh(c, map_msg.info) for c in contours]

        corners = list(np.vstack(contours))
        corners = [c[0] for c in corners]
        self.publish_test_map(corners, map_msg.info, map_msg.header)
        mesh = trimesh.util.concatenate(meshes)

        # Export as STL
        with open(export_dir + "/map_" + str(i[0]) + "_" + str(j[0]) + ".stl", 'w') as f:
            mesh.export(f, "stl")
        rospy.loginfo("Exported STL.  You can shut down this node now")
        if len(rooms[i[0]]) == j[0]:
            i[0] += 1
            j[0] = 1
        else:
            j[0] += 1
        file_name = dataset + str(i[0]) + ".jpg"
        if os.path.exists(file_name):
            print("map: " + str(i[0]) + "_" + str(j[0]))
            call_map_server(file_name, j[0])
        


    def publish_test_map(self, points, metadata, map_header):
        """
        For testing purposes, publishes a map highlighting certain points.
        points is a list of tuples (x, y) in the map's coordinate system.
        """
        test_map = np.zeros((metadata.height, metadata.width))
        for x, y in points:
            test_map[y, x] = 100
        test_map_msg = OccupancyGrid()
        test_map_msg.header = map_header
        test_map_msg.header.stamp = rospy.Time.now()
        test_map_msg.info = metadata
        test_map_msg.data = list(np.ravel(test_map))
        self.test_map_pub.publish(test_map_msg)

    def get_occupied_regions(self, map_array):
        """
        Get occupied regions of map
        """
        map_array = map_array.astype(np.uint8)
        _, thresh_map = cv2.threshold(
                map_array, self.threshold, 100, cv2.THRESH_BINARY)
        image, contours, hierarchy = cv2.findContours(
                thresh_map, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
        # Using cv2.RETR_CCOMP classifies external contours at top level of
        # hierarchy and interior contours at second level.  
        # If the whole space is enclosed by walls RETR_EXTERNAL will exclude
        # all interior obstacles e.g. furniture.
        # https://docs.opencv.org/trunk/d9/d8b/tutorial_py_contours_hierarchy.html
        hierarchy = hierarchy[0]
        corner_idxs = [i for i in range(len(contours)) if hierarchy[i][3] == -1]
        return [contours[i] for i in corner_idxs]

    def contour_to_mesh(self, contour, metadata):
        height = np.array([0, 0, self.height])
        s3 = 3**0.5 / 3.
        meshes = []
        for point in contour:
            x, y = point[0]
            vertices = []
            new_vertices = [
                    coords_to_loc((x, y), metadata),
                    coords_to_loc((x, y+1), metadata),
                    coords_to_loc((x+1, y), metadata),
                    coords_to_loc((x+1, y+1), metadata)]
            vertices.extend(new_vertices)
            vertices.extend([v + height for v in new_vertices])
            faces = [[0, 2, 4],
                     [4, 2, 6],
                     [1, 2, 0],
                     [3, 2, 1],
                     [5, 0, 4],
                     [1, 0, 5],
                     [3, 7, 2],
                     [7, 6, 2],
                     [7, 4, 6],
                     [5, 4, 7],
                     [1, 5, 3],
                     [7, 3, 5]]
            mesh = trimesh.Trimesh(vertices=vertices, faces=faces)
            if not mesh.is_volume:
                rospy.logdebug("Fixing mesh normals")
                mesh.fix_normals()
            meshes.append(mesh)
        mesh = trimesh.util.concatenate(meshes)
        mesh.remove_duplicate_faces()
        # mesh will still have internal faces.  Would be better to get
        # all duplicate faces and remove both of them, since duplicate faces
        # are guaranteed to be internal faces
        return mesh
        
def call_map_server(file_name, door_number):
    print(file_name)
    with open(yaml_file_path, "r") as file:
        data = yaml.safe_load(file)
  
    img = cv2.imread(file_name, cv2.IMREAD_UNCHANGED)

    room_number = int(file_name[len(dataset):-4])
    data['image'] = str(room_number) + ".jpg"

    # if doors exist
    if rooms[room_number]:
        door = rooms[room_number][door_number - 1]

        state = door[1] % 2

        rotated = 0

        # if map is rotated, the height and width swap
        if  door[1] > 1:
            rotated = 1
        x, y = abs(((state) * img.shape[1 - rotated]) - door[0][0]), abs((((1 - state)) * img.shape[rotated]) - door[0][1])

        data['origin'] = [x * -0.01, y * -0.01, 0.0]
        # data['origin'] = [0.0, 0.0, 0.0]

        print(data['origin'])

        with open(yaml_file_path, 'w') as fp:
            yaml.safe_dump(data, fp, default_flow_style=None)
    print("som")
    subprocess.Popen("rosrun map_server map_server " + yaml_file_path, shell=True)
        


def coords_to_loc(coords, metadata):
    x, y = coords
    loc_x = x * metadata.resolution + metadata.origin.position.x
    loc_y = y * metadata.resolution + metadata.origin.position.y
    # TODO: transform (x*res, y*res, 0.0) by Pose map_metadata.origin
    # instead of assuming origin is at z=0 with no rotation wrt map frame
    return np.array([loc_x, loc_y, 0.0])

if __name__ == "__main__":
    rospy.init_node("map2gazebo")
    map_topic = rospy.get_param("~map_topic", "map")
    occupied_thresh = rospy.get_param("~occupied_thresh", 1)
    box_height = rospy.get_param("~box_height", 2.0)
    converter = MapConverter(map_topic,
            threshold=occupied_thresh, height=box_height)
    rospy.loginfo("map2gazebo running")
    with open(rooms_data, "rb") as data:
        rooms = pickle.load(data)
    call_map_server(dataset + sys.argv[1] + ".jpg", 1)
    rospy.spin()
