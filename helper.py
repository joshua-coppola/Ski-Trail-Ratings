import time
import json
import pandas as pd
from numpy import NAN
import haversine as hs
from math import degrees, atan
from requests.api import get

# accepts a string with coords separated by a | and returns a list of elevations


def elevation_api(piped_coords, last_called, trailname=''):
    # url = 'https://api.open-elevation.com/api/v1/lookup?locations={}'
    url = 'https://api.opentopodata.org/v1/ned10m?locations={}'
    # url = 'https://api.opentopodata.org/v1/mapzen?locations={}'
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
            temp_elevations, last_called = elevation_api(
                piped_coords, last_called, trail_name)
            api_requests += 1
            if temp_elevations == -1:
                return -1
            piped_coords = ''
            point_count = 0
            for point in temp_elevations:
                elevations.append(point)
    if piped_coords != '':
        temp_elevations, last_called = elevation_api(
            piped_coords, last_called, trail_name)
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
        if word[:3] == 'mcc':
            word = 'McC' + word[3:]
            name = '{}{} '.format(name, word)
            continue
        if len(word) > 2 or word == 'fe':
            name = '{}{} '.format(name, word.capitalize())
        else:
            name = '{}{} '.format(name, word)
    return name.strip()

# Parameters:
# object: list of trails
#   type-list of tuples
#
# Returns: mountain vertical drop
#   type-float


def calculate_mtn_vert(trail_list):
    min_ele = 10000
    max_ele = 0
    for trail in trail_list:
        if trail['points_df'].elevation.max() > max_ele:
            max_ele = trail['points_df'].elevation.max()
        if trail['points_df'].elevation.min() < min_ele:
            min_ele = trail['points_df'].elevation.min()
    return(max_ele-min_ele)

# Parameters:
# elevation: a series of elevations
#   type-series
#
# Returns: the vertical drop of the trail
#   type-float


def calculate_trail_vert(elevation):
    return elevation.max() - elevation.min()

# Parameters:
# state: 2 letter state code
#   type-string
#
# Returns: the region of the state
#   type-string

def assign_region(state):
    northeast = ['ME', 'NH', 'VT', 'NY', 'MA', 'RI', 'CT', 'PA', 'NJ']
    southeast = ['MD', 'DE', 'VA', 'WV', 'KY', 'TN', 'NC', 'SC', 'GA', 'FL', 'AL', 'MS', 'LA', 'AR']
    midwest = ['ND', 'SD', 'MN', 'WI', 'MI', 'OH', 'IN', 'IL', 'IA', 'NE', 'KS', 'MO', 'OK', 'TX']
    west = ['NM', 'AZ', 'CA', 'NV', 'UT', 'CO', 'WY', 'ID', 'OR', 'WA', 'MT', 'AK', 'HI']

    if len(state.split()) > 1:
        state = state.split()[0]
    
    if state in northeast:
        return 'northeast'

    if state in southeast:
        return 'southeast'
    
    if state in midwest:
        return 'midwest'

    if state in west:
        return 'west'
