import time
import json
import pandas as pd
from numpy import NAN
import haversine as hs
from math import degrees, atan, atan2
from requests.api import get
import numpy as np

def rmse(actual, pred): 
    actual, pred = np.array(actual), np.array(pred)
    return np.sqrt(np.square(np.subtract(actual,pred)).mean())

# accepts a string with coords separated by a | and returns a list of elevations


def elevation_api(piped_coords, trailname=''):
    # url = 'https://api.open-elevation.com/api/v1/lookup?locations={}'
    url = 'https://api.opentopodata.org/v1/ned10m?locations={}'
    time.sleep(1)
    response = get(url.format(piped_coords))
    if response.status_code == 200:
        elevation = []
        for result in json.loads(response.content)['results']:
            elevation.append(result['elevation'])
    else:
        print('Elevation API call failed on {} with code:'.format(trailname))
        print(response.status_code)
        print(response.content)
        return -1
    return elevation

# Parameters:
# coordinates: list/series of latitude and longitude tuples
#   type-list/series of tuples
# trail_name: name of ski trail
#   type-string
# api-requests: number of api requests made
#   type-int
#
# Returns: tuple containing series of coordinates and api_requests
#   type-tuple(series of tuples, int)

def get_elevation(coordinates, trail_name='', api_requests=0):
    piped_coords = ''
    point_count = 0
    elevations = []
    for coordinate in coordinates:
        if piped_coords == '':
            piped_coords = '{},{}'.format(coordinate[0], coordinate[1])
            continue
        piped_coords = piped_coords + '|{},{}'.format(coordinate[0], coordinate[1])
        point_count += 1
        if point_count >= 99:
            temp_elevations = elevation_api(piped_coords, trail_name)
            api_requests += 1
            if temp_elevations == -1:
                return -1
            piped_coords = ''
            point_count = 0
            for point in temp_elevations:
                elevations.append(point)
    if piped_coords != '':
        temp_elevations = elevation_api(piped_coords, trail_name)
        api_requests += 1
        if temp_elevations == -1:
            return -1
        for point in temp_elevations:
            elevations.append(point)
    return (pd.Series(elevations), api_requests)

# accepts a list of lat/lon pairs and returns a list of distances (in meters)


def calculate_dist(coordinates):
    previous_row = (NAN, NAN)
    distance = []
    for row in coordinates:
        distance.append(hs.haversine(row, previous_row, unit=hs.Unit.METERS))
        previous_row = row
    return distance

# accepts a df with lat, lon, lat/lon pairs, and elevation and returns
# a df with the same columns, but points spaced out by no more than 20


def fill_in_point_gaps(df, max_gap=20, filetype='osm'):
    lat = df['lat'].tolist()
    lon = df['lon'].tolist()
    coordinates = df['coordinates'].tolist()
    if filetype == 'gpx':
        elevation = df['elevation'].tolist()
    done = False
    while not done:
        distances = calculate_dist(coordinates)
        not_changed = 0
        for index, point in enumerate(distances):
            if point > max_gap and index > 0:
                new_lat = (lat[index]+lat[index-1])/2
                new_lon = (lon[index]+lon[index-1])/2
                lat.insert(index, new_lat)
                lon.insert(index, new_lon)
                coordinates.insert(index, (new_lat, new_lon))
                if filetype == 'gpx':
                    elevation.insert(
                        index, (elevation[index]+elevation[index-1])/2)
                break
            not_changed += 1
        if not_changed == len(coordinates):
            done = True
    new_df = pd.DataFrame()
    new_df['lat'] = lat
    new_df['lon'] = lon
    new_df['coordinates'] = coordinates
    if filetype == 'gpx':
        new_df['elevation'] = elevation
    return new_df

# accepts a df with 3 columns: lat, lon, lat/lon pairs. Retruns the information
# as a line down the middle of the area in the same format.


def area_to_line(df):
    coordinates = df.coordinates.to_list()
    new_lat = []
    new_lon = []
    new_coords = []
    midpoint = int(len(coordinates)/2)
    for i, _ in enumerate(coordinates):
        if i > midpoint:
            break
        new_lat_point = (coordinates[i][0] + coordinates[-i][0]) / 2
        new_lon_point = (coordinates[i][1] + coordinates[-i][1]) / 2
        new_lat.append(new_lat_point)
        new_lon.append(new_lon_point)
        new_coords.append((new_lat_point, new_lon_point))
    new_df = pd.DataFrame()
    new_df['lat'] = new_lat
    new_df['lon'] = new_lon
    new_df['coordinates'] = new_coords
    return new_df

# accepts a series of difficulties and returns an overall trail rating (0-.9 scale) as a float


def rate_trail(difficulty):
    max_difficulty = 0
    previous = 0
    previous_2 = 0
    for point in difficulty:
        nearby_avg = (point + previous + previous_2) / 3
        if nearby_avg > max_difficulty:
            max_difficulty = nearby_avg
        previous_2 = previous
        previous = point
    return max_difficulty

# accepts a float and converts it into a trail color (return a string)
# possible colors: green, royalblue, black, red, gold


def set_color(rating, difficultly_modifier=0):
    rating += .07 * difficultly_modifier
    # 0-17 degrees: green
    if rating < .17:
        return 'green'
    # 17-24 degrees: blue
    if rating < .242:
        return 'royalblue'
    # 24-30 degrees: black
    if rating < .30:
        return 'black'
    # 30-45 degrees: red
    elif rating < .45:
        return 'red'
    # >45 degrees: yellow
    else:
        return 'gold'

# accepts a list of elevations and smooths the gaps between groupings of
# same valued points. Returns a list


def smooth_elevations(elevations, passes=20):
    if len(elevations) == 0:
        print('No Elevations provided')
        return
    for _ in range(passes):
        previous_previous_point = elevations[0]
        previous_point = elevations[0]
        for i, point in enumerate(elevations):
            new_point = (point + previous_point + previous_previous_point) / 3
            if i > 1:
                elevations[i-1] = new_point
            previous_previous_point = previous_point
            previous_point = point
    return elevations

# accepts a list of elevations and returns the difference between
# neighboring elevations


def calulate_elevation_change(elevation):
    previous_row = NAN
    elevation_change = []
    for row in elevation:
        elevation_change.append(row-previous_row)
        previous_row = row
    return elevation_change

# accepts 2 lists: distance and elevation change, both using the same unit
# returns a list of slopes (in degrees)


def calculate_slope(elevation_change, distance):
    slope = []
    for x, y in zip(elevation_change, distance):
        if y != 0:
            slope.append(degrees(atan(x/y)))
        else:
            slope.append(0)
    slope[0] = 0
    #for i, point in enumerate(slope):
    #    if point > 0:
    #        slope[i] = 0
    return slope

# accepts a list of slopes and returns a list of difficulties (0-.9 scale)


def calculate_point_difficulty(slope):
    difficulty = []
    for point in slope:
        difficulty.append((abs(point)/90)*.9)
    difficulty[0] = 0
    return difficulty

# Parameters:
# coordinates: list/series of coordinates
#   type-list/series of tuples
#
# Returns: trail length
#   type-float

def get_trail_length(coordinates):
    distances = calculate_dist(coordinates)
    return(sum(distances[1:]))

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
    point_gap = sum(calculate_dist(df.coordinates)[1:])/point_count
    letter_size = 10 / point_gap
    label_length = point_gap * length * letter_size
    label_length_in_points = int(label_length / point_gap)
    point = int(len(df.coordinates)/2)
    angle_list = []
    valid_list = []
    for i, _ in enumerate(df.coordinates):
        valid = False
        if get_trail_length(df.coordinates[0:i]) > label_length / 2:
            if get_trail_length(df.coordinates[i:-1]) > label_length / 2:
                valid = True
        if i == 0:
            ang = 0
        else:
            dx = (df.lat[i])-(df.lat[i-1])
            dy = (df.lon[i])-(df.lon[i-1])
            ang = degrees(atan2(dx, dy))
        angle_list.append(ang)
        valid_list.append(valid)
    rmse_min = (1, 10000000)
    for i, _ in enumerate(angle_list):
        if valid_list[i]:
            slice = angle_list[i-label_length_in_points:i+label_length_in_points]
            if len(slice) == 0:
                continue
            expected = sum(slice) / len(slice)
            if rmse(expected, slice) < rmse_min[1]:
                rmse_min = (i, rmse(expected, slice))
        
    if rmse_min[1] != 10000000:
        point = rmse_min[0]
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
