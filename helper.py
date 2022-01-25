import time
import json
import pandas as pd
from numpy import NAN
import haversine as hs
from math import degrees, atan
from requests.api import get
import numpy as np


def rmse(actual, pred):
    actual, pred = np.array(actual), np.array(pred)
    return np.sqrt(np.square(np.subtract(actual, pred)).mean())

def process_osm(table, blacklist):
    DEBUG_TRAILS = False

    way_df = pd.DataFrame()
    lift_df = pd.DataFrame()
    id = [] # for node_df
    lat = [] # for node_df
    lon = [] # for node_df
    coordinates = [] # for node_df
    in_way_ids = [] # all OSM ids for a way, used for way_df
    useful_info_list = [] # list((way_name, difficulty_modifier, is_area))
    trail_and_id_list = [] # list((trail_name, OSM id))
    blank_name_count = 0
    total_trail_count = 0

    in_way = False
    way_name = ''

    for row in table:
        row = str(row)
        # handling when inside a way
        if in_way:
            if '<nd' in row:
                split_row = row.split('"')
                in_way_ids.append(split_row[1])
            if '<tag k="name"' in row:
                split_row = row.split('"')
                way_name = split_row[3]
            if '<tag k="piste:difficulty"' in row:
                is_trail = True
            if '<tag k="piste:type"' in row and 'backcountry' in row:
                is_backcountry = True
            if '<tag k="piste:type"' in row and 'nordic' in row:
                is_backcountry = True
            if '<tag k="piste:type"' in row and 'skitour' in row:
                is_backcountry = True
            if '<tag k="gladed" v="yes"/>' in row and not is_glade:
                difficulty_modifier += 1
                is_glade = True
            if '<tag k="leaf_type"' in row and not is_glade:
                difficulty_modifier += 1
                is_glade = True
            if '<tag k="leaf_type"' in row or '<tag k="area" v="yes"/>' in row:
                is_area = True
            if '<tag k="natural" v="wood"/>' in row:
                is_area = True
            if 'glade' in row and not is_glade:
                difficulty_modifier += 1
                is_glade = True
            if 'Glade' in row and not is_glade:
                difficulty_modifier += 1
                is_glade = True
            if '<tag k="aerialway"' in row:
                is_lift = True
            if 'Tree Skiing' in row:
                difficulty_modifier += 1
                is_glade = True

            if '</way>' in row:
                if is_trail and not is_backcountry:
                    total_trail_count += 1
                    trail_and_id_list.append((way_name, way_id))
                    if DEBUG_TRAILS:
                        way_name = way_id
                    if way_name == '':
                        way_name = ' _' + str(blank_name_count)
                        blank_name_count += 1
                    if way_name in way_df.columns:
                        way_name = way_name + '_' + str(blank_name_count)
                        blank_name_count += 1
                    temp_df = pd.DataFrame()
                    temp_df[way_name] = in_way_ids
                    way_df = pd.concat([way_df, temp_df], axis=1)
                    useful_info_list.append(
                        (way_name, difficulty_modifier, is_area))
                if is_lift:
                    trail_and_id_list.append((way_name, way_id))
                    if way_name == '':
                        way_name = ' _' + str(blank_name_count)
                        blank_name_count += 1
                    if way_name in lift_df.columns:
                        way_name = way_name + '_' + str(blank_name_count)
                        blank_name_count += 1
                    temp_df = pd.DataFrame()
                    temp_df[way_name] = in_way_ids
                    lift_df = pd.concat([lift_df, temp_df], axis=1)
                in_way_ids = []
                in_way = False
                way_name = ''
        # start of a way
        if '<way' in row:
            in_way = True
            is_trail = False
            is_glade = False
            is_backcountry = False
            is_area = False
            is_lift = False
            difficulty_modifier = 0
            way_id = row.split('"')[1]
            if str(way_id) in blacklist:
                in_way = False
        # handling nodes
        if '<node' in row:
            split_row = row.split('"')
            for i, word in enumerate(split_row):
                if ' id=' in word:
                    id.append(split_row[i+1])
                if 'lat=' in word:
                    lat.append(float(split_row[i+1]))
                if 'lon=' in word:
                    lon.append(float(split_row[i+1]))
            coordinates.append((lat[-1], lon[-1]))
    node_df = pd.DataFrame()
    node_df['id'] = id
    node_df['lat'] = lat
    node_df['lon'] = lon
    node_df['coordinates'] = coordinates

    return (node_df, way_df, lift_df, useful_info_list, total_trail_count, trail_and_id_list)

# accepts a string with coords separated by a | and returns a list of elevations


def elevation_api(piped_coords, last_called, trailname=''):
    # url = 'https://api.open-elevation.com/api/v1/lookup?locations={}'
    url = 'https://api.opentopodata.org/v1/ned10m?locations={}'
    if time.time() - last_called < 1:
        time.sleep(1 - (time.time() - last_called))
    last_called = time.time()
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
    return (elevation, last_called)

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


def get_elevation(coordinates, last_called, trail_name='', api_requests=0):
    piped_coords = ''
    point_count = 0
    elevations = []
    for coordinate in coordinates:
        if piped_coords == '':
            piped_coords = '{},{}'.format(coordinate[0], coordinate[1])
            continue
        piped_coords = piped_coords + \
            '|{},{}'.format(coordinate[0], coordinate[1])
        point_count += 1
        if point_count >= 99:
            temp_elevations, last_called = elevation_api(piped_coords, last_called,trail_name)
            api_requests += 1
            if temp_elevations == -1:
                return -1
            piped_coords = ''
            point_count = 0
            for point in temp_elevations:
                elevations.append(point)
    if piped_coords != '':
        temp_elevations, last_called = elevation_api(piped_coords, last_called,trail_name)
        api_requests += 1
        if temp_elevations == -1:
            return -1
        for point in temp_elevations:
            elevations.append(point)
    return (pd.Series(elevations), api_requests, last_called)

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
    max_ele = (0, 0)
    min_ele = (10000, 0)
    for i, point in enumerate(df.elevation):
        if point > max_ele[0]:
            max_ele = (point, i)
        if point < min_ele[0]:
            min_ele = (point, i)
    center_lat = df.lat.mean()
    center_lon = df.lon.mean()
    new_lat.append(df.lat[max_ele[1]])
    new_lon.append(df.lon[max_ele[1]])
    new_lat.append(center_lat)
    new_lon.append(center_lon)
    new_lat.append(df.lat[min_ele[1]])
    new_lon.append(df.lon[min_ele[1]])
    new_lat.append(coordinates[min_ele[1]][0])
    new_lon.append(coordinates[min_ele[1]][1])
    new_coords = [(x[0], x[1]) for x in zip(new_lat, new_lon)]
    new_df = pd.DataFrame()
    new_df['lat'] = new_lat
    new_df['lon'] = new_lon
    new_df['coordinates'] = new_coords

    new_df = fill_in_point_gaps(new_df, 15)
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
    # for i, point in enumerate(slope):
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
# name: name of an object
#   type-string
#
# Returns: name, but with spaces replacing the underscores, and each word capitalized
#   type-string

def format_name(name):
    name_list = name.split('_')
    name = ''
    for word in name_list:
        name = '{}{} '.format(name, word.capitalize())
    return name.strip()
