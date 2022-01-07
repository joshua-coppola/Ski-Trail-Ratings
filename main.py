from numpy import NAN, maximum, not_equal
import numpy as np
from numpy.lib.arraysetops import unique
from numpy.lib.function_base import average
import pandas as pd
import haversine as hs
import math
import matplotlib.pyplot as plt
import requests
import json

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

# accepts a list of elevations and smooths the gaps between groupings of
# same valued points. Returns a list


def smooth_elevations(elevations):
    for _ in range(20):
        previous_previous_point = elevations[0]
        previous_point = elevations[0]
        for i, point in enumerate(elevations):
            new_point = (point + previous_point + previous_previous_point) / 3
            if i > 1:
                elevations[i-1] = new_point
            previous_previous_point = previous_point
            previous_point = point
    return elevations

# accepts a osm filename and returns a list of dataframes with
# 4 columns: latitude, longitude, lat/lon pairs, and elevation (meteres)


def load_osm(filename):
    file = open(filename, 'r')
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
    blank_name_count = 0
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
            if '</way>' in row:
                if is_trail:
                    way_name = ''.join(ch for ch in way_name if ch.isalnum())
                    if way_name == '':
                        way_name = str(blank_name_count)
                        blank_name_count += 1
                    if way_name in way_df.columns:
                        way_name = way_name + str(blank_name_count)
                        blank_name_count += 1
                    temp_df = pd.DataFrame()
                    temp_df[way_name] = in_way_ids
                    way_df = pd.concat([way_df, temp_df], axis=1)
                in_way_ids = []
                in_way = False
                way_name = ''
        # start of a way
        if '<way' in row:
            in_way = True
            is_trail = False
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

    trail_list = []
    for column in way_df:
        temp_df = pd.merge(way_df[column], node_df,
                           left_on=column, right_on='id')
        del temp_df['id']
        piped_coords = ''
        for coordinate in temp_df['coordinates']:
            if piped_coords == '':
                piped_coords = '{},{}'.format(coordinate[0], coordinate[1])
                continue
            piped_coords = piped_coords + \
                '|{},{}'.format(coordinate[0], coordinate[1])
        url = 'https://api.open-elevation.com/api/v1/lookup?locations={}'
        response = requests.get(url.format(piped_coords))
        if response.status_code == 200:
            elevation = []
            for result in json.loads(response.content)['results']:
                elevation.append(result['elevation'])
        temp_df['elevation'] = pd.Series(smooth_elevations(elevation))
        trail_list.append(temp_df)

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


def fill_in_point_gaps(df):
    lat = df['lat'].tolist()
    lon = df['lon'].tolist()
    coordinates = df['coordinates'].tolist()
    elevation = df['elevation'].tolist()
    done = False
    while not done:
        distances = calculate_dist(coordinates)
        not_changed = 0
        for index, point in enumerate(distances):
            if point > 20:
                new_lat = (lat[index]+lat[index-1])/2
                new_lon = (lon[index]+lon[index-1])/2
                lat.insert(index, new_lat)
                lon.insert(index, new_lon)
                coordinates.insert(index, (new_lat, new_lon))
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
    new_df['elevation'] = elevation
    return new_df


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
    #sorted_difficulty = difficulty.sort_values(ascending=False)
    #if len(sorted_difficulty) >= 10:
    #    return sorted_difficulty.head(10).sum()/10
    #return sorted_difficulty.sum()/len(sorted_difficulty)
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


def set_color(rating):
    if rating < .18:
        return 'green'
    if rating < .24:
        return 'royalblue'
    if rating < .45:
        return 'black'
    return 'red'


def main():
    #df = load_gpx('rimrock-415690.gpx')[0]
    #df = load_gpx('tuckered-out.gpx')[0]
    df = load_gpx('big-bang-409529.gpx')[0]
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

    plt.plot(df.lon, df.lat, c = color, alpha = .25)
    plt.scatter(df.lon, df.lat, s=8, c=abs(df.slope), cmap='gist_rainbow',alpha=1)
    plt.colorbar(label='Degrees', orientation='horizontal')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.xticks([])
    plt.yticks([])
    plt.show()


def main2():
    trail_list = load_osm('cannon.osm')
    tempDF = pd.DataFrame(columns=['lat', 'lon', 'coordinates', 'elevation',
                          'distance', 'elevation_change', 'slope', 'difficulty'])
    for trail in trail_list:
        trail = fill_in_point_gaps(trail)
        trail['distance'] = calculate_dist(trail['coordinates'])
        trail['elevation_change'] = calulate_elevation_change(
            trail['elevation'])
        trail['slope'] = calculate_slope(
            trail['elevation_change'], trail['distance'])
        trail['difficulty'] = calculate_point_difficulty(trail['slope'])
        rating = rate_trail(trail['difficulty'])
        color = set_color(rating)
        tempDF = tempDF.append(trail)
        plt.plot(abs(trail.lat), abs(trail.lon), c = color)
    #plt.scatter(tempDF.lon, tempDF.lat, s=6, c=abs(tempDF.slope),
    #            cmap='gist_rainbow', alpha=1)
    #plt.colorbar(label='Rating (Higher is more difficult)', orientation='horizontal')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.xticks([])
    plt.yticks([])
    plt.show()


main2()
