import find_doors
# import cv2 
import numpy as np
import pickle
import sys

def save_rooms(rooms):
    try:
        with open("rooms.pickle", "wb") as f:
            pickle.dump(rooms, f, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception as ex:
        print("Error during pickling object (Possibly unsupported):", ex)

if __name__ == "__main__":
    start = int(sys.argv[1])
    end = int(sys.argv[2]) + 1
    roomsOutsideDoors = {}
    for j in range(2):
        rooms = find_doors.findDoors(start, end, j)
        for i, room in enumerate(rooms, start):
            image = find_doors.loadImageAsBinary('dataset/' + str(i) + '.jpg')
            image = np.rot90(image, j)
            
            outsideDoors = []
            minDist = image.shape[0]
            for door in room:
                if door[1] < 25:
                    outsideDoors.append(((door, 0 + (j * 2)), 0))
                    minDist = 0
                    continue
                
                if door[1] > image.shape[0] - 25:
                    outsideDoors.append(((door, 1 + (j * 2)), 0))
                    minDist = 0
                    continue

                upDoor = door[1]
                while upDoor > 0:
                    if image[upDoor][door[0]] == 0:
                        break
                    upDoor -= 1

                if upDoor == 0:
                    distance = door[1] - upDoor
                    outsideDoors.append(((door, 0 + (j * 2)), distance))
                    minDist = min(minDist, distance)
                    continue

                downDoor = door[1]
                while downDoor < image.shape[0]:
                    if image[downDoor][door[0]] == 0:
                        break
                    downDoor += 1    

                if downDoor == image.shape[0]:
                    distance = downDoor - door[1]
                    outsideDoors.append(((door, 1 + (j * 2)), distance))
                    minDist = min(minDist, distance)

            outsideDoors = [ door[0] for door in outsideDoors if door[1] < minDist + 25]
            if j:
                roomsOutsideDoors[i] += outsideDoors
            else:
                roomsOutsideDoors[i] = outsideDoors

            image = np.ascontiguousarray(image, dtype=np.uint8)
            new_image = image
            for door in outsideDoors:
                new_image = find_doors.drawCircle(image, door[0])
                
            print(str(i) + ".jpg")
            #cv2.imwrite("doors/outside_horizontal/" + str(i) + ".jpg", new_image)
    print(roomsOutsideDoors)
    save_rooms(roomsOutsideDoors)