import numpy as np
import copy
import json
from svg.path import parse_path
from xml.dom import minidom
import sys

def find_between_r( s, first, last ):
    try:
        start = s.rindex( first ) + len( first )
        end = s.rindex( last, start )
        return s[start:end]
    except ValueError:
        return ""


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def connect(ends):
    d0, d1 = np.abs(np.diff(ends, axis=0))[0]
    if d0 > d1:
        return np.c_[np.linspace(ends[0, 0], ends[1, 0], d0+1, dtype=np.int32),
                     np.round(np.linspace(ends[0, 1], ends[1, 1], d0+1))
                     .astype(np.int32)]
    else:
        return np.c_[np.round(np.linspace(ends[0, 0], ends[1, 0], d1+1))
                     .astype(np.int32),
                     np.linspace(ends[0, 1], ends[1, 1], d1+1, dtype=np.int32)]

def slope(x1, y1, x2, y2):
    return (y2-y1)/(x2-x1)

def angle(x1, y1, x2, y2):
    return np.rad2deg(np.arctan2(y2 - y1, x2 - x1))

def round_to(x, base=5):
    return base * round(x/base)

def get_point_at(path, distance, scale, offset):
    pos = path.point(distance)
    pos += offset
    pos *= scale
    return pos.real, pos.imag


def points_from_path(path, density, scale, offset):
    step = int(path.length() * density)
    last_step = step - 1

    if last_step == 0:
        yield get_point_at(path, 0, scale, offset)
        return

    for distance in range(step):
        yield get_point_at(
            path, distance / last_step, scale, offset)


def points_from_doc(doc, density=5, scale=0.5, offset=0):
    offset = offset[0] + offset[1] * 1j
    points = []
    for element in doc.getElementsByTagName("path"):
        for path in parse_path(element.getAttribute("d")):
            points.extend(points_from_path(
                path, density, scale, offset))

    return points

def turn_float_tuple_to_int_tuple(t, width_modifier=1.75):
    return ([int(t[0] * width_modifier), int(t[1])])

# loading arguments

FILENAME = sys.argv[1]

DENSITY = sys.argv[2]

SCALE = sys.argv[3]

if DENSITY == "DEFAULT":
    DENSITY = 1
else:
    DENSITY = float(DENSITY)

if SCALE == "DEFAULT":
    SCALE = 0.5
else:
    SCALE = float(SCALE)

f = open(FILENAME, "r") # svg should be 100 x 100 but idk if it actually matters
svg_string = f.read()

#print(svg_string)

all_path_strings = []

all_paths = []

svg_paths = svg_string.split("<path")
skip = True
for path in svg_paths:
    if skip:
        skip = False
    else:
        temp = path.split("/>")
        path_string = "<path" + temp[0] + "/>"
        all_path_strings.append(path_string)

for path_string in all_path_strings:
    doc = minidom.parseString(path_string)
    sets_of_points = points_from_doc(doc, density=DENSITY, scale=SCALE, offset=(0, 5))
    doc.unlink()

    sets_of_points = list(map(turn_float_tuple_to_int_tuple, sets_of_points))

    all_paths.append(sets_of_points)

sets_of_points = copy.deepcopy(all_paths)

start_and_end_points = []


MAX_X = 0
MAX_Y = 0

for points_tuples in sets_of_points:

    for point in points_tuples:
        if point[0] > MAX_X:
            MAX_X = point[0]
        if point[1] > MAX_Y:
            MAX_Y = point[1]

MAX_X += 1
MAX_Y += 1

string_array = []
for a in range(MAX_X):
    line_array = []
    for b in range(MAX_Y):
        line_array.append(" ")
    string_array.append(line_array)

print("lines:", len(string_array), "rows:", len(string_array[0]), "max_x", MAX_X, "max_y", MAX_Y)
pointer_index = 0
for points_tuples in sets_of_points:

    errors = 0
    non_errors = 0

    for i in range(len(points_tuples)):
        if i+1 == len(points_tuples):
            break
        curr = points_tuples[i]
        next = points_tuples[i+1]

        ends = np.array([curr, next])

        middle_points = list(connect(ends))
        for p in middle_points:
            try:
                string_array[p[0]][p[1]] = "."
            except IndexError:
                print("out of bounds at", p[0], p[1])

    # mark cornerstones
    temp_start_end = [pointer_index]

    for point in points_tuples:
        try:
            string_array[point[0]][point[1]] = pointer_index
            pointer_index += 1
        except:
            print("failed with", pointer_index)
    temp_start_end.append(pointer_index)
    start_and_end_points.append(temp_start_end)

    print("original points_tuples is", points_tuples)
    print('original points_tuples length is', len(points_tuples))


    # rotating it 90 degrees
string_array = list(zip(*string_array[::-1]))

    # reflecting it
string_array = list(np.flip(string_array, 1))

print("start and end points is", start_and_end_points)
print("length of start and end points is", len(start_and_end_points))

# regenerate point tuples

new_points_tuples = []
for start_and_end_point in start_and_end_points:
    points_tuples = []
    for i in range(start_and_end_point[0], start_and_end_point[1]):
        for a in range(len(string_array)):
            for b in range(len(string_array[0])):
                if str(string_array[a][b]) == str(i):
                    points_tuples.append([a, b])
    new_points_tuples.append(points_tuples)

print("new_points_tuples:", new_points_tuples)
print("length of new_points_tuples is", len(new_points_tuples))


for npt in new_points_tuples:
    for i in range(len(npt)):
        if i+1 == len(npt):
            break
        curr = npt[i]
        next = npt[i+1]

        ends = np.array([curr, next])

        middle_points = list(connect(ends))
        for p in middle_points:
            string_array[p[0]][p[1]] = "#"

        middle_points_into_chunks = list(chunks(middle_points, 2))
        for _chunk in middle_points_into_chunks:
            if len(_chunk) < 2:
                print("in here once")
                for p in _chunk:
                    string_array[p[0]][p[1]] = "."
            else:
                first_point = _chunk[0]
                last_point = _chunk[1]
                #slope_between_points = slope(first_point[0], first_point[1], last_point[0], last_point[1])
                angle_between_points = int(angle(first_point[0], first_point[1], last_point[0], last_point[1]))
                if angle_between_points < 0:
                    angle_between_points = 360 + angle_between_points

                angle_between_points = round_to(angle_between_points, 10) # used ot be 20, and hten + 10
                print("angle between points is", angle_between_points)


                try:
                    if angle_between_points == 180:
                        for p in _chunk:
                            string_array[p[0]][p[1]] = "|"
                    if angle_between_points == 190:
                        string_array[_chunk[0][0]][_chunk[0][1]] = "|"
                        string_array[_chunk[1][0]][_chunk[1][1]] = "."
                        string_array[_chunk[2][0]][_chunk[2][1]] = "\\"
                    if angle_between_points == 200:
                        string_array[_chunk[0][0]][_chunk[0][1]] = "\\"
                        string_array[_chunk[1][0]][_chunk[1][1]] = "\\"
                        string_array[_chunk[2][0]][_chunk[2][1]] = "\\"
                    if angle_between_points == 210:
                        string_array[_chunk[0][0]][_chunk[0][1]] = "\\"
                        string_array[_chunk[1][0]][_chunk[1][1]] = "\\"
                        string_array[_chunk[2][0]][_chunk[2][1]] = "\\"
                    if angle_between_points == 220:
                        string_array[_chunk[0][0]][_chunk[0][1]] = "`"
                        string_array[_chunk[1][0]][_chunk[1][1]] = "."
                        string_array[_chunk[2][0]][_chunk[2][1]] = "\\"
                    if angle_between_points == 230:
                        string_array[_chunk[0][0]][_chunk[0][1]] = "`."
                        string_array[_chunk[1][0]][_chunk[1][1]] = "`."
                        string_array[_chunk[2][0]][_chunk[2][1]] = "`"
                    if angle_between_points == 240:
                        string_array[_chunk[0][0]][_chunk[0][1]] = "`-."
                        string_array[_chunk[1][0]][_chunk[1][1]] = "" # THIS ONE IS EMPTY
                        string_array[_chunk[2][0]][_chunk[2][1]] = "`-."
                    if angle_between_points == 250:
                        string_array[_chunk[0][0]][_chunk[0][1]] = "--"
                        string_array[_chunk[1][0]][_chunk[1][1]] = ".."
                        string_array[_chunk[2][0]][_chunk[2][1]] = "``"
                    if angle_between_points == 260:
                        string_array[_chunk[0][0]][_chunk[0][1]] = "--"
                        string_array[_chunk[1][0]][_chunk[1][1]] = ".."
                        string_array[_chunk[2][0]][_chunk[2][1]] = "``"
                    if angle_between_points == 270:
                        string_array[_chunk[0][0]][_chunk[0][1]] = "_"
                        string_array[_chunk[1][0]][_chunk[1][1]] = "_"
                        string_array[_chunk[2][0]][_chunk[2][1]] = "_"
                    if angle_between_points == 280:
                        string_array[_chunk[0][0]][_chunk[0][1]] = "--"
                        string_array[_chunk[1][0]][_chunk[1][1]] = ".."
                        string_array[_chunk[2][0]][_chunk[2][1]] = "''"
                    if angle_between_points == 290:
                        string_array[_chunk[0][0]][_chunk[0][1]] = "--"
                        string_array[_chunk[1][0]][_chunk[1][1]] = ".."
                        string_array[_chunk[2][0]][_chunk[2][1]] = "''"
                    if angle_between_points == 300:
                        string_array[_chunk[0][0]][_chunk[0][1]] = ".-'"
                        string_array[_chunk[1][0]][_chunk[1][1]] = "" # THIS ONE IS EMPTY
                        string_array[_chunk[2][0]][_chunk[2][1]] = ".-'"
                    if angle_between_points == 310:
                        string_array[_chunk[0][0]][_chunk[0][1]] = ".'"
                        string_array[_chunk[1][0]][_chunk[1][1]] = ".'"
                        string_array[_chunk[2][0]][_chunk[2][1]] = "'"
                    if angle_between_points == 320:
                        string_array[_chunk[0][0]][_chunk[0][1]] = "'"
                        string_array[_chunk[1][0]][_chunk[1][1]] = "."
                        string_array[_chunk[2][0]][_chunk[2][1]] = "/"
                    if angle_between_points == 330:
                        string_array[_chunk[0][0]][_chunk[0][1]] = "/"
                        string_array[_chunk[1][0]][_chunk[1][1]] = "/"
                        string_array[_chunk[2][0]][_chunk[2][1]] = "/"
                    if angle_between_points == 340:
                        string_array[_chunk[0][0]][_chunk[0][1]] = "/"
                        string_array[_chunk[1][0]][_chunk[1][1]] = "/"
                        string_array[_chunk[2][0]][_chunk[2][1]] = "/"
                    if angle_between_points == 350:
                        string_array[_chunk[0][0]][_chunk[0][1]] = "|"
                        string_array[_chunk[1][0]][_chunk[1][1]] = "."
                        string_array[_chunk[2][0]][_chunk[2][1]] = "/"
                    if angle_between_points == 360:
                        string_array[_chunk[0][0]][_chunk[0][1]] = "|"
                        string_array[_chunk[1][0]][_chunk[1][1]] = "|"
                        string_array[_chunk[2][0]][_chunk[2][1]] = "|"

                    if angle_between_points == 0:
                        string_array[_chunk[0][0]][_chunk[0][1]] = "|"
                        string_array[_chunk[1][0]][_chunk[1][1]] = "."
                        string_array[_chunk[2][0]][_chunk[2][1]] = "\\"
                    if angle_between_points == 10:
                        string_array[_chunk[0][0]][_chunk[0][1]] = "\\"
                        string_array[_chunk[1][0]][_chunk[1][1]] = "\\"
                        string_array[_chunk[2][0]][_chunk[2][1]] = "\\"
                    if angle_between_points == 20:
                        string_array[_chunk[0][0]][_chunk[0][1]] = "\\"
                        string_array[_chunk[1][0]][_chunk[1][1]] = "\\"
                        string_array[_chunk[2][0]][_chunk[2][1]] = "\\"
                    if angle_between_points == 30:
                        string_array[_chunk[0][0]][_chunk[0][1]] = "`"
                        string_array[_chunk[1][0]][_chunk[1][1]] = "."
                        string_array[_chunk[2][0]][_chunk[2][1]] = "\\"
                    if angle_between_points == 40:
                        string_array[_chunk[0][0]][_chunk[0][1]] = "`."
                        string_array[_chunk[1][0]][_chunk[1][1]] = "`."
                        string_array[_chunk[2][0]][_chunk[2][1]] = "`"
                    if angle_between_points == 50:
                        string_array[_chunk[0][0]][_chunk[0][1]] = "`-."
                        string_array[_chunk[1][0]][_chunk[1][1]] = "" # THIS ONE IS EMPTY
                        string_array[_chunk[2][0]][_chunk[2][1]] = "`-."
                    if angle_between_points == 60:
                        string_array[_chunk[0][0]][_chunk[0][1]] = "--"
                        string_array[_chunk[1][0]][_chunk[1][1]] = ".."
                        string_array[_chunk[2][0]][_chunk[2][1]] = "``"
                    if angle_between_points == 70:
                        string_array[_chunk[0][0]][_chunk[0][1]] = "--"
                        string_array[_chunk[1][0]][_chunk[1][1]] = ".."
                        string_array[_chunk[2][0]][_chunk[2][1]] = "``"
                    if angle_between_points == 80:
                        string_array[_chunk[0][0]][_chunk[0][1]] = "_"
                        string_array[_chunk[1][0]][_chunk[1][1]] = "_"
                        string_array[_chunk[2][0]][_chunk[2][1]] = "_"
                    if angle_between_points == 90:
                        string_array[_chunk[0][0]][_chunk[0][1]] = "_"
                        string_array[_chunk[1][0]][_chunk[1][1]] = "_"
                        string_array[_chunk[2][0]][_chunk[2][1]] = "_"
                    if angle_between_points == 100:
                        string_array[_chunk[0][0]][_chunk[0][1]] = "--"
                        string_array[_chunk[1][0]][_chunk[1][1]] = ".."
                        string_array[_chunk[2][0]][_chunk[2][1]] = "''"
                    if angle_between_points == 110:
                        string_array[_chunk[0][0]][_chunk[0][1]] = ".-'"
                        string_array[_chunk[1][0]][_chunk[1][1]] = "" # THIS ONE IS EMPTY
                        string_array[_chunk[2][0]][_chunk[2][1]] = ".-'"
                    if angle_between_points == 120:
                        string_array[_chunk[0][0]][_chunk[0][1]] = ".'"
                        string_array[_chunk[1][0]][_chunk[1][1]] = ".'"
                        string_array[_chunk[2][0]][_chunk[2][1]] = "'"
                    if angle_between_points == 130:
                        string_array[_chunk[0][0]][_chunk[0][1]] = "'"
                        string_array[_chunk[1][0]][_chunk[1][1]] = "."
                        string_array[_chunk[2][0]][_chunk[2][1]] = "/"
                    if angle_between_points == 140:
                        string_array[_chunk[0][0]][_chunk[0][1]] = "/"
                        string_array[_chunk[1][0]][_chunk[1][1]] = "/"
                        string_array[_chunk[2][0]][_chunk[2][1]] = "/"
                    if angle_between_points == 150:
                        string_array[_chunk[0][0]][_chunk[0][1]] = "/"
                        string_array[_chunk[1][0]][_chunk[1][1]] = "/"
                        string_array[_chunk[2][0]][_chunk[2][1]] = "/"
                    if angle_between_points == 160:
                        string_array[_chunk[0][0]][_chunk[0][1]] = "|"
                        string_array[_chunk[1][0]][_chunk[1][1]] = "."
                        string_array[_chunk[2][0]][_chunk[2][1]] = "/"
                    if angle_between_points == 170:
                        string_array[_chunk[0][0]][_chunk[0][1]] = "|"
                        string_array[_chunk[1][0]][_chunk[1][1]] = "|"
                        string_array[_chunk[2][0]][_chunk[2][1]] = "|"

                except:
                    print("out of bounds with", _chunk)

# printing it
numbers = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]

return_string = ""
for a in range(len(string_array)):
    for b in range(len(string_array[0])):
        return_string += str(string_array[a][b])
    return_string += "\n"

for str_number in numbers:
    return_string = return_string.replace(str_number, " ")

with open(FILENAME + ".txt", "w") as f:
    f.write(return_string);

#print("errors:", errors, "nonerrors:", non_errors)

# instead of adding a dot, divide the sections by 3-5 by slope and then add each character of the slope to where the dot would be

# break down svg into multiple points on the svg path, then run this algorithm



# code fills in the shape:

# print("original points_tuples is", points_tuples)
# print('original points_tuples length is', len(points_tuples))
# points_tuples = []
# for a in range(len(string_array)):
#     for b in range(len(string_array[0])):
#         if string_array[a][b] == ".":
#             points_tuples.append([a, b])
#
# for point in points_tuples:
#     if point[0] > MAX_X:
#         MAX_X = point[0]
#     if point[1] > MAX_Y:
#         MAX_Y = point[1]
#         # append to points_tuples
# MAX_X += 1
# MAX_Y += 1
# string_array = []
# for a in range(MAX_X):
#     line_array = []
#     for b in range(MAX_Y):
#         line_array.append(" ")
#     string_array.append(line_array)
#
# print("new points_tuples is", points_tuples)
# print('new points_tuples length is', len(points_tuples))
