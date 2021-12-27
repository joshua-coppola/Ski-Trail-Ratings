from numpy import NAN
import numpy as np
import pandas as pd
import haversine as hs
import math
import matplotlib.pyplot as plt
import requests

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
        temp_df = pd.merge(way_df[column], node_df, left_on=column, right_on='id')
        del temp_df['id']
        elevation = []
        for coordinate in temp_df['coordinates']:
            url = 'https://api.open-elevation.com/api/v1/lookup?locations={},{}'
            response = requests.get(url.format(coordinate[0], coordinate[1]))
            if response.status_code == 200:
                elevation.append(float(str(response.content).split()[-1].split('}')[0]))
        temp_df['elevation'] = elevation
        print(elevation)
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
    return [math.degrees(math.atan(x/y)) for x, y in zip(elevation_change, distance)]

def main():
    df = load_gpx('rimrock-415690.gpx')[0]
    df2 = load_gpx('tuckered-out.gpx')[0]
    df['distance'] = calculate_dist(df['coordinates'])
    df['elevation_change'] = calulate_elevation_change(df['elevation'])
    df['slope'] = calculate_slope(df['elevation_change'], df['distance'])

    df2['distance'] = calculate_dist(df2['coordinates'])
    df2['elevation_change'] = calulate_elevation_change(df2['elevation'])
    df2['slope'] = calculate_slope(df2['elevation_change'], df2['distance'])

    print(df.slope.min())
    plt.plot(df.lon, df.lat, alpha=.25)
    plt.scatter(df.lon, df.lat, s=8, c=abs(df.slope), alpha=1)
    plt.plot(df2.lon, df2.lat, alpha=.25)
    plt.scatter(df2.lon, df2.lat, s=8, c=abs(df2.slope), alpha=1)
    plt.colorbar(label='Degrees', orientation='horizontal')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.xticks([])
    plt.yticks([])
    plt.show()

def main2():
    trail_list = load_osm('jay_peak.osm')
    for trail in trail_list:
        trail['distance'] = calculate_dist(trail['coordinates'])
        trail['elevation_change'] = calulate_elevation_change(trail['elevation'])
        trail['slope'] = calculate_slope(trail['elevation_change'], trail['distance'])
        plt.plot(trail.lon, trail.lat, alpha=.25)
        plt.scatter(trail.lon, trail.lat, s=8, c=abs(trail.slope), alpha=1)
    plt.colorbar(label='Degrees', orientation='horizontal')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.xticks([])
    plt.yticks([])
    plt.show()

main2()
