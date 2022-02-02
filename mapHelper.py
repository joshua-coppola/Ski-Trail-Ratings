from math import degrees, atan2
import matplotlib.pyplot as plt

import helper

# Parameters:
# df: dataframe with columns for lat, lon, and coordinates
#   type-df(float, float, tuple)
# length: number of characters in label
#   type-int
#
# Returns: tuple with point number and angle
#   type-tuple(float, float)


def get_label_placement(df, length, flip_lat_lon):
    point_count = len(df.coordinates)
    point_gap = sum(helper.calculate_dist(df.coordinates)[1:])/point_count
    letter_size = 10 / point_gap
    label_length = point_gap * length * letter_size
    label_length_in_points = int(label_length / point_gap)
    point = int(len(df.coordinates)/2)
    angle_list = []
    valid_list = []
    for i, _ in enumerate(df.coordinates):
        valid = False
        if helper.get_trail_length(df.coordinates[0:i]) > label_length / 2:
            if helper.get_trail_length(df.coordinates[i:-1]) > label_length / 2:
                valid = True
        if i == 0:
            ang = 0
        else:
            dx = (df.lat[i])-(df.lat[i-1])
            dy = (df.lon[i])-(df.lon[i-1])
            ang = degrees(atan2(dx, dy))
        angle_list.append(ang)
        valid_list.append(valid)
    frac_correct = (1, 0, 0)
    for i, _ in enumerate(angle_list):
        if valid_list[i]:
            slice = angle_list[i-int(label_length_in_points / 2):i +
                               int(label_length_in_points / 2)]
            if len(slice) == 0:
                continue
            expected = sum(slice) / len(slice)
            frac_correct_current = 0
            correct = 0
            for value in slice:
                if abs(value-expected) < 5:
                    correct += 1
            frac_correct_current = correct / len(slice)
            if frac_correct_current > frac_correct[1]:
                frac_correct = (i, frac_correct_current, 0)
    if frac_correct[1] != 0:
        point = frac_correct[0]
    if point == 0:
        dx = 0
        dy = 0
    else:
        dx = (df.lat[point])-(df.lat[point-1])
        dy = (df.lon[point])-(df.lon[point-1])
        if point > 1 and dx == 0 and dy == 0:
            dx = (df.lat[point])-(df.lat[point-2])
            dy = (df.lon[point])-(df.lon[point-2])
    ang = degrees(atan2(dx, dy))
    if flip_lat_lon:
        if ang < -90:
            ang -= 180
        if ang > 90:
            ang -= 180
        return(point, ang)
    ang -= 90
    if ang < -90:
        ang += 180
    return(point, ang)

# Parameters:
# trails: list of trail tuples
#   type-list of tuples
# mountain: name of ski area
#   type-string
# cardinal_direction: direction for map to face
#   type-char
#
# Return: none

def format_map_template(trails, mountain, cardinal_direction):
    mountain_max_lat = 0
    mountain_min_lat = 90
    mountain_max_lon = 0
    mountain_min_lon = 180
    for entry in trails:
        trail_max_lat = abs(entry[0]['lat']).max()
        trail_min_lat = abs(entry[0]['lat']).min()
        if trail_max_lat > mountain_max_lat:
            mountain_max_lat = trail_max_lat
        if trail_min_lat < mountain_min_lat:
            mountain_min_lat = trail_min_lat
        trail_max_lon = abs(entry[0]['lon']).max()
        trail_min_lon = abs(entry[0]['lon']).min()
        if trail_max_lon > mountain_max_lon:
            mountain_max_lon = trail_max_lon
        if trail_min_lon < mountain_min_lon:
            mountain_min_lon = trail_min_lon
    top_corner = (mountain_max_lat, mountain_max_lon)
    bottom_corner = (mountain_min_lat, mountain_max_lon)
    bottom_corner_alt = (mountain_min_lat, mountain_min_lon)
    x_length = helper.calculate_dist([top_corner, bottom_corner])[1] / 1000
    y_length = helper.calculate_dist([bottom_corner, bottom_corner_alt])[1] / 1000
    if 's' in cardinal_direction or 'n' in cardinal_direction:
        temp = x_length
        x_length = y_length
        y_length = temp

    #plt.subplots(facecolor='silver', figsize=(x_length*2, y_length*2))
    plt.subplots(figsize=(x_length*2, y_length*2))

    if mountain != '':
        mountain = helper.format_name(mountain)
        size = int(x_length*10)
        if size > 25:
            size = 25
        if size < 5:
            size = 5
        if y_length < 1.5:
            top = .88
        if y_length >= 1.5:
            top = .88
        if y_length < 1:
            top = .80
        plt.title(mountain, fontsize=size, y=1, pad = size * .5)
        plt.subplots_adjust(left=0.05, bottom=.02, right=.95,
                            top=top, wspace=0, hspace=0)
    else:
        plt.subplots_adjust(left=0, bottom=0, right=1,
                            top=1, wspace=0, hspace=0)
    #plt.axis('off')

# Parameters:
# object_tuple: trail/lift tuple
#   type-tuple(df(float, float, tuple), string, int)
# direction: map direction
#   type-char
# color: color of object
#   type-string
#
# Returns: none


def place_object(object_tuple, direction, color):
    lat_mirror = 1
    lon_mirror = -1
    flip_lat_lon = False
    if 'e' in direction or 'E' in direction:
        lat_mirror = -1
        lon_mirror = 1
    if 's' in direction or 'S' in direction:
        lon_mirror = 1
        flip_lat_lon = True
    if 'n' in direction or 'N' in direction:
        lat_mirror = -1
        flip_lat_lon = True

    point, ang = get_label_placement(
        object_tuple[0][['lat', 'lon', 'coordinates']], len(object_tuple[1]), flip_lat_lon)
    area = object_tuple[3]
    if not flip_lat_lon:
        X = object_tuple[0].lat
        Y = object_tuple[0].lon
    if flip_lat_lon:
        X = object_tuple[0].lon
        Y = object_tuple[0].lat
        temp = lat_mirror
        lat_mirror = lon_mirror
        lon_mirror = temp
    if not area:
        if object_tuple[2] == 0:
            plt.plot(X * lat_mirror, Y * lon_mirror, c=color)
        if object_tuple[2] > 0:
            plt.plot(X * lat_mirror, Y * lon_mirror, c=color, linestyle='dashed')
    if area:
        if object_tuple[2] == 0:
            plt.fill(X * lat_mirror, Y * lon_mirror, alpha=.1, fc=color)
            plt.fill(X * lat_mirror, Y * lon_mirror, ec=color, fc='none')
        if object_tuple[2] > 0:
            plt.fill(X * lat_mirror, Y * lon_mirror, alpha=.1, fc=color)
            plt.fill(X * lat_mirror, Y * lon_mirror, ec=color, fc='none', linestyle='dashed')
    if color == 'gold':
        color = 'black'
    if helper.get_trail_length(object_tuple[0].coordinates) > 200:
        plt.text(X[point] * lat_mirror, Y[point] * lon_mirror, object_tuple[1], {
                    'color': color, 'size': 2, 'rotation': ang}, ha='center', 
                    backgroundcolor='white', va='center', bbox=dict(boxstyle='square,pad=0.01', 
                    fc='white', ec='none'))
