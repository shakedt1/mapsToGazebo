import cv2 
import numpy as np
import sys
import itertools

import PIL
from PIL import Image

def loadImageAsBinary(image): 
  image = cv2.imread(image) 
  image = cv2.cvtColor(src=image, code=cv2.COLOR_BGR2GRAY) 
  (thresh, blackAndWhiteImage) = cv2.threshold(image, 200, 255, cv2.THRESH_BINARY)
  return blackAndWhiteImage

def checkIfDoor(white, bRight, bLeft):
    return  bRight > 25 and bLeft > 25  

def Exist(doorStart, doorEnd, doors):
    if len(doors) != 0:
        if ((doorStart[0] , doorStart[1] - 1),  (doorEnd[0] , doorEnd[1] - 1)) in doors:
            return ((doorStart[0] , doorStart[1] - 1),  (doorEnd[0] , doorEnd[1] - 1))
    return 0

def addDoor(doorStart, doorEnd, doors):
    door = Exist(doorStart, doorEnd, doors)
    if door != 0:
        num_of_times = doors[door]
        doors.pop(door)
        doors[(doorStart, doorEnd)] = num_of_times + 1
    else:
        doors[(doorStart, doorEnd)] = 1

def calculateMiddle(door):
    return (int((door[1][0] + door[0][0]) / 2), int((door[1][1] + door[0][1]) / 2))

def drawCircle(image, coor, radius = 20, color = (0, 0, 0), thickness = 2):
    return cv2.circle(image, coor, radius, color, thickness)


def findDoors(start, end, state):
    rooms = []
    for n in range(start, end):
        bLeft = bRight = 0
        white = 0
        doorStart = tuple()
        doorEnd = tuple()
        doors = {}  
        
        image = loadImageAsBinary('dataset/' + str(n) + '.jpg')

        if state:
            image = np.rot90(image)

        minLength = image.shape[1] / 10 

        for i, row in enumerate(image):
            for j, bit in enumerate(row):
                if bit == 0:
                    if  bLeft != 0 and white != 0 and bRight == 0:
                        doorEnd = (j, i)
                        bRight += 1

                    elif bLeft != 0 and white != 0:
                        bRight += 1

                    elif bLeft == 0:
                        bLeft += 1
                        white = 0
                    else:
                        bLeft += 1
                    
                else:
                    if bRight != 0 and white != 0 and bRight != 0:
                        if checkIfDoor(white, bRight, bLeft):
                            addDoor(doorStart, doorEnd, doors)
                        bLeft = bRight
                        bRight = 0
                        white = 0

                    if bLeft != 0 and white == 0 and bRight == 0:
                        doorStart = (j, i)

                    white += 1

            if bRight != 0 and white != 0 and bRight != 0:
                if checkIfDoor(white, bRight, bLeft):
                    addDoor(doorStart, doorEnd, doors)
            bLeft = bRight = white = 0

        doors = { door:num_of_times for door,num_of_times in doors.items() if num_of_times > 3 }

        for door, num_of_times in doors.items():
            door_length = door[1][0] - door[0][0]
            if door_length < minLength:
                minLength = door_length 

        doors = { door:num_of_times for door,num_of_times in doors.items() if ((door[1][0] - door[0][0]) / minLength) < 1.5 or door[0][1] < 25 or door[0][1] > image.shape[0] - 25}

        for door, door_2 in itertools.combinations(doors.keys(), 2):
            if abs(door[0][1] - door_2[0][1]) < 11 and abs(door[0][0] - door_2[0][0]) < 11:
                doors.pop(door)

        # for door, num in doors.items():
        #     print('({}, {}) - ({}, {}) : {}'.format(door[0][0], door[0][1], door[1][0], door[1][1], num))
        image = np.ascontiguousarray(image, dtype=np.uint8)
        new_image = image
        for door in doors.keys():
            new_image = drawCircle(image, calculateMiddle(door))
        
        print(str(n) + ".jpg")
        # cv2.imwrite("doors/" + str(state) + "/" + str(n) + ".jpg", new_image)
        rooms.append([calculateMiddle(door) for door in doors.keys()])
    return rooms
            