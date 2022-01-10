import time
import json
import requests
import pandas as pd
from numpy import NAN
import haversine as hs
from math import degrees, atan

# accepts a string with coords separated by a | and returns a list of elevations


def get_elevation(piped_coords, column):
    # url = 'https://api.open-elevation.com/api/v1/lookup?locations={}'
    url = 'https://api.opentopodata.org/v1/ned10m?locations={}'
    time.sleep(1)
    response = requests.get(url.format(piped_coords))
    if response.status_code == 200:
        elevation = []
        for result in json.loads(response.content)['results']:
            elevation.append(result['elevation'])
    else:
        print('Elevation API call failed on {} with code:'.format(column))
        print(response.status_code)
        print(response.content)
        return -1
    return elevation

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


def fill_in_point_gaps(df, max_gap=20):
    lat = df['lat'].tolist()
    lon = df['lon'].tolist()
    coordinates = df['coordinates'].tolist()
    done = False
    while not done:
        distances = calculate_dist(coordinates)
        not_changed = 0
        for index, point in enumerate(distances):
            if point > max_gap:
                new_lat = (lat[index]+lat[index-1])/2
                new_lon = (lon[index]+lon[index-1])/2
                lat.insert(index, new_lat)
                lon.insert(index, new_lon)
                coordinates.insert(index, (new_lat, new_lon))
                # elevation.insert(
                #    index, (elevation[index]+elevation[index-1])/2)
                break
            not_changed += 1
        if not_changed == len(coordinates):
            done = True
    new_df = pd.DataFrame()
    new_df['lat'] = lat
    new_df['lon'] = lon
    new_df['coordinates'] = coordinates
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
    previous_3 = 0
    for point in difficulty:
        nearby_avg = (point + previous + previous_2 + previous_3) / 4
        if nearby_avg > max_difficulty:
            max_difficulty = nearby_avg
        previous_3 = previous_2
        previous_2 = previous
        previous = point
    return max_difficulty

# accepts a float and converts it into a trail color (return a string)
# possible colors: green, royalblue, black, red, gold


def set_color(rating, difficultly_modifier=0):
    rating += .07 * difficultly_modifier
    # 0-16 degrees: green
    if rating < .16:
        return 'green'
    # 16-23 degrees: blue
    if rating < .23:
        return 'royalblue'
    # 23-32 degrees: black
    if rating < .32:
        return 'black'
    # 32-45 degrees: red
    elif rating < .45:
        return 'red'
    # >45 degrees: yellow
    else:
        print(rating)
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