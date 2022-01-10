from math import atan2, degrees
import time
from ast import literal_eval
from os.path import exists
import json
import requests
import matplotlib.pyplot as plt
from numpy import NAN
from numpy.lib.arraysetops import unique
from numpy.lib.function_base import average
import pandas as pd
import haversine as hs
import math
import random

# accepts a gpx filename and returns a list of 1 dataframe
# with 4 columns: latitude, longitude, lat/lon pairs and elevation (meters)


def load_gpx(filename):
    raw_table = pd.read_csv(filename).to_numpy()
    df = pd.DataFrame()
    lat = []
    lon = []
    coordinates = []
    elevation = []
    for row in raw_table:
        row = str(row)
        if 'trkpt lat' in row:
            split_row = row.split('"')
            lat.append(float(split_row[1]))
            lon.append(float(split_row[3]))
            coordinates.append((float(split_row[1]), float(split_row[3])))
        if 'ele' in row:
            elevation.append(float(row.split('>')[1].split('<')[0]))
    df['lat'] = lat
    df['lon'] = lon
    df['coordinates'] = coordinates
    df['elevation'] = elevation
    return [df]

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

# accepts a osm filename and returns a list of tuples.
# Each tuple contains a dataframe with
# 4 columns: latitude, longitude, lat/lon pairs, and elevation (meters)
# a string with the trailname,
# and an int (0-2) to denote if the trail is gladed, has moguls, or both (unlikely)


def load_osm(filename, cached=False, cached_filename=''):
    file = open('osm/{}'.format(filename), 'r')
    print('Opening File')
    raw_table = file.readlines()
    node_df = pd.DataFrame()
    way_df = pd.DataFrame()
    id = []
    lat = []
    lon = []
    coordinates = []
    in_way = False
    in_way_ids = []
    way_name = ''
    is_trail = False
    is_glade = False
    is_backcountry = False
    blank_name_count = 0
    difficulty_modifier = 0
    difficulty_modifier_list = []
    total_trail_count = 0
    print('Preforming initial pre-processing')
    for row in raw_table:
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
            if '<tag k="piste:type" v="backcountry"/>' in row:
                is_backcountry = True
            if '<tag k="piste:type" v="nordic"/>' in row:
                is_backcountry = True
            if '<tag k="gladed" v="yes"/>' in row and not is_glade:
                difficulty_modifier += 1
                is_glade = True
            if '<tag k="leaf_type"' in row and not is_glade:
                difficulty_modifier += 1
                is_glade = True
            if 'glade' in row and not is_glade:
                difficulty_modifier += 1
                is_glade = True
            if 'Glade' in row and not is_glade:
                difficulty_modifier += 1
                is_glade = True

            if '</way>' in row:
                if is_trail and not is_backcountry:
                    total_trail_count += 1
                    # way_name = ''.join(ch for ch in way_name if ch.isalnum())
                    if way_name == '':
                        way_name = ' _' + str(blank_name_count)
                        blank_name_count += 1
                    if way_name in way_df.columns:
                        way_name = way_name + '_' + str(blank_name_count)
                        blank_name_count += 1
                    temp_df = pd.DataFrame()
                    temp_df[way_name] = in_way_ids
                    way_df = pd.concat([way_df, temp_df], axis=1)
                    difficulty_modifier_list.append(
                        (way_name, difficulty_modifier))
                in_way_ids = []
                in_way = False
                way_name = ''
        # start of a way
        if '<way' in row:
            in_way = True
            is_trail = False
            is_glade = False
            is_backcountry = False
            difficulty_modifier = 0
        # handling nodes
        if '<node' in row:
            split_row = row.split('"')
            id.append(split_row[1])
            lat.append(float(split_row[15]))
            lon.append(float(split_row[17]))
            coordinates.append((float(split_row[15]), float(split_row[17])))
    node_df['id'] = id
    node_df['lat'] = lat
    node_df['lon'] = lon
    node_df['coordinates'] = coordinates

    if not exists('cached/{}'.format(cached_filename)) and cached:
        cached = False
        print('Disabling cache loading: no cache file found.')

    trail_list = []
    trail_num = 0
    api_requests = 0
    if cached:
        elevation_df = pd.read_csv('cached/{}'.format(cached_filename), converters={
                                   'coordinates': literal_eval})
        elevation_df = elevation_df[['coordinates', 'elevation']]
    for column in way_df:
        trail_num += 1
        if trail_num % 10 == 1:
            print('Processing trail {}/{}'.format(trail_num, total_trail_count))
        temp_df = pd.merge(way_df[column], node_df,
                           left_on=column, right_on='id')
        del temp_df['id']
        temp_df = fill_in_point_gaps(temp_df, 15)
        piped_coords = ''
        if not cached:
            point_count = 0
            elevations = []
            for coordinate in temp_df['coordinates']:
                if piped_coords == '':
                    piped_coords = '{},{}'.format(coordinate[0], coordinate[1])
                    continue
                piped_coords = piped_coords + \
                    '|{},{}'.format(coordinate[0], coordinate[1])
                point_count += 1
                if point_count >= 99:
                    temp_elevations = get_elevation(piped_coords, column)
                    api_requests += 1
                    if temp_elevations == -1:
                        return -1
                    piped_coords = ''
                    point_count = 0
                    for point in temp_elevations:
                        elevations.append(point)
            if piped_coords != '':
                temp_elevations = get_elevation(piped_coords, column)
                api_requests += 1
                if temp_elevations == -1:
                    return -1
                for point in temp_elevations:
                    elevations.append(point)
            temp_df['elevation'] = pd.Series(elevations)
        else:
            row_count = temp_df.shape[0]
            temp_df = pd.merge(temp_df, elevation_df, on='coordinates')
            if temp_df.shape[0] < row_count:
                print(
                    '{} has missing elevation data. It will be skipped.'.format(column))
                continue
        for row in difficulty_modifier_list:
            if column in row[0]:
                difficulty_modifier = row[1]
        trail_list.append((temp_df, column, difficulty_modifier))
    print('All trails sucessfully loaded')
    print('{} API requests made'.format(api_requests))

    return trail_list


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
            slope.append(math.degrees(math.atan(x/y)))
        else:
            slope.append(0)
    slope[0] = 0
    for i, point in enumerate(slope):
        if point > 0:
            slope[i] = 0
    return slope

# accepts a list of slopes and returns a list of difficulties (0-.9 scale)


def calculate_point_difficulty(slope):
    difficulty = []
    for point in slope:
        difficulty.append((abs(point)/90)*.9)
    difficulty[0] = 0
    return difficulty

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
# possible colors: green, royalblue, black, red


def set_color(rating, difficultly_modifier=0):
    rating += .07 * difficultly_modifier
    if rating < .16:
        return 'green'
    if rating < .23:
        return 'royalblue'
    if rating < .32:
        return 'black'
    elif rating < .45:
        return 'red'
    else:
        print(rating)
        return 'gold'


# accepts a list of trails and saves the latitude, longitude, and elevation
# to a csv as a cache


def cache_elevation(filename, list_dfs):
    if exists('cached/{}'.format(filename)):
        return
    output_df = pd.DataFrame(columns=['coordinates', 'elevation'])
    for entry in list_dfs:
        trail = entry[0][['coordinates', 'elevation']]
        output_df = output_df.append(trail)
    output_df.to_csv(filename)


# accepts a list of trail tuples, the name of the ski area, a boolean for
# whether to use difficulty modifiers, and a pair of ints (plus a bool) to
# rotate the map. Their values should be -1 or 1 and T/F for the bool. The
# last param is a bool for whether to save the map.


def create_map(trails, mountain, difficulty_modifiers, lat_mirror=1, lon_mirror=1, flip_lat_lon=False, save=False):
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
    n_s_length = calculate_dist([top_corner, bottom_corner])[1] / 1000
    e_w_length = calculate_dist([bottom_corner, bottom_corner_alt])[1] / 1000
    if flip_lat_lon:
        temp = n_s_length
        n_s_length = e_w_length
        e_w_length = temp

    plt.figure(figsize=(n_s_length*2, e_w_length*2))
    for entry in trails:
        rating = rate_trail(entry[0]['difficulty'])
        if difficulty_modifiers:
            color = set_color(rating, entry[2])
        else:
            color = set_color(rating)
        trail_name = entry[1]
        if '_' in trail_name:
            trail_name = trail_name.split('_')[0]
        midpoint = int(len(entry[0].lat.to_list())/2)
        dx = (entry[0].lat.to_list()[midpoint]) - \
            (entry[0].lat.to_list()[midpoint+2])
        dy = (entry[0].lon.to_list()[midpoint])- \
            (entry[0].lon.to_list()[midpoint+2])
        if not flip_lat_lon:
            ang = degrees(atan2(dx, dy)) - 90
            if ang < -90:
                ang += 180
            if entry[2] == 0:
                plt.plot(entry[0].lat * lat_mirror,
                         entry[0].lon * lon_mirror, c=color, label=trail_name)
            if entry[2] > 0:
                plt.plot(entry[0].lat * lat_mirror, entry[0].lon *
                         lon_mirror, c=color, linestyle='dashed', label=trail_name)
            plt.text((entry[0].lat.to_list()[midpoint]) * lat_mirror,
                     (entry[0].lon.to_list()[midpoint]) * lon_mirror, trail_name, 
                     {'color': color, 'size': 2, 'rotation': ang}, ha='center', 
                     backgroundcolor='white', bbox=dict(boxstyle='square,pad=0.01', 
                     fc='white', ec='none'))
        if flip_lat_lon:
            ang = degrees(atan2(dx, dy))
            if ang < -90:
                ang -= 180
            if ang > 90:
                ang -= 180
            if entry[2] == 0:
                plt.plot(entry[0].lon * lon_mirror,
                         entry[0].lat * lat_mirror, c=color, label=trail_name)
            if entry[2] > 0:
                plt.plot(entry[0].lon * lon_mirror, entry[0].lat *
                         lat_mirror, c=color, linestyle='dashed', label=trail_name)
            plt.text((entry[0].lon.to_list()[midpoint]) * lon_mirror,
                     (entry[0].lat.to_list()[midpoint]) * lat_mirror, trail_name, 
                     {'color': color, 'size': 2, 'rotation': ang}, ha='center', 
                     backgroundcolor='white', bbox=dict(boxstyle='square,pad=0.01', 
                     fc='white', ec='none'))
    plt.xticks([])
    plt.yticks([])
    if mountain != '':
        mountain_list = mountain.split('_')
        mountain = ''
        for word in mountain_list:
            mountain = mountain + ('{} '.format(word.capitalize()))
        plt.title(mountain)
        plt.subplots_adjust(left=0.05, bottom=.02, right=.95,
                            top=.92, wspace=0, hspace=0)
    else:
        plt.subplots_adjust(left=0, bottom=0, right=1,
                            top=1, wspace=0, hspace=0)
    if save:
        plt.savefig('maps/{}.svg'.format(mountain.strip()), format='svg')
        print('SVG saved')
    plt.show()


def main():
    # df = load_gpx('rimrock-415690.gpx')[0]
    # df = load_gpx('tuckered-out.gpx')[0]
    df = load_gpx('gpx/big-bang-409529.gpx')[0]
    df = fill_in_point_gaps(df)
    df['elevation'] = smooth_elevations(df['elevation'].to_list())
    df['distance'] = calculate_dist(df['coordinates'])
    df['elevation_change'] = calulate_elevation_change(df['elevation'])
    df['slope'] = calculate_slope(df['elevation_change'], df['distance'])
    df['difficulty'] = calculate_point_difficulty(df['slope'].to_list())
    rating = rate_trail(df['difficulty'])
    color = set_color(rating)
    print(rating)
    print(color)

    plt.plot(df.lon, df.lat, c=color, alpha=.25)
    plt.scatter(df.lon, df.lat, s=8, c=abs(
        df.slope), cmap='gist_rainbow', alpha=1)
    plt.colorbar(label='Degrees', orientation='horizontal')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.xticks([])
    plt.yticks([])
    plt.show()


def main2():
    difficulty_modifiers = True
    mountain = 'stowe'
    trail_list = load_osm(mountain + '.osm', True, mountain + '.csv')
    if trail_list == -1:
        return
    finished_trail_list = []
    cache_elevation(mountain + '.csv', trail_list)
    for entry in trail_list:
        trail = entry[0]
        trail['elevation'] = smooth_elevations(
            trail['elevation'].to_list(), 1)
        trail['distance'] = calculate_dist(trail['coordinates'])
        trail['elevation_change'] = calulate_elevation_change(
            trail['elevation'])
        trail['slope'] = calculate_slope(
            trail['elevation_change'], trail['distance'])
        trail['difficulty'] = calculate_point_difficulty(trail['slope'])
        finished_trail_list.append((trail, entry[1], entry[2]))
    create_map(finished_trail_list, mountain, difficulty_modifiers, 1, -1, False, True)
    # ^^west facing
    # okemo, killington, stowe
    # create_map(finished_trail_list, mountain, difficulty_modifiers, -1, 1)
    # ^^east facing
    # create_map(finished_trail_list, mountain, difficulty_modifiers, 1, 1, True)
    # ^^south facing
    #create_map(finished_trail_list, mountain, difficulty_modifiers, -1, -1, True, True)
    # ^^north facing
    # cannon, holiday_valley, sunday_river, purgatory


main2()
