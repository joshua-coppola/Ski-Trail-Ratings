import pandas as pd
from os.path import exists
from ast import literal_eval
import matplotlib.pyplot as plt

import helper
import saveData

# accepts a gpx filename and returns a dataframe
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
    return df

# Parameters:
# filename: name of gpx file. GPX file should contain 1 trail.
#   type-string
#
# Return Type: none

def runGPX(filename):
    df = load_gpx(filename)
    df = helper.fill_in_point_gaps(df, 15, 'gpx')
    df['elevation'] = helper.smooth_elevations(df['elevation'].to_list())
    df['distance'] = helper.calculate_dist(df['coordinates'])
    df['elevation_change'] = helper.calulate_elevation_change(df['elevation'])
    df['slope'] = helper.calculate_slope(df['elevation_change'], df['distance'])
    df['difficulty'] = helper.calculate_point_difficulty(df['slope'].to_list())
    rating = helper.rate_trail(df['difficulty'])
    color = helper.set_color(rating)
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
    is_area = True
    blank_name_count = 0
    difficulty_modifier = 0
    useful_info_list = []
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

            if '</way>' in row:
                if is_trail and not is_backcountry:
                    total_trail_count += 1
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
        temp_df = helper.fill_in_point_gaps(temp_df, 15)
        for row in useful_info_list:
            if column == row[0]:
                difficulty_modifier = row[1]
                if row[2] == True:
                    temp_df = helper.area_to_line(temp_df)
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
                    temp_elevations = helper.get_elevation(
                        piped_coords, column)
                    api_requests += 1
                    if temp_elevations == -1:
                        return -1
                    piped_coords = ''
                    point_count = 0
                    for point in temp_elevations:
                        elevations.append(point)
            if piped_coords != '':
                temp_elevations = helper.get_elevation(piped_coords, column)
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
        trail_list.append((temp_df, column, difficulty_modifier))
    print('All trails sucessfully loaded')
    print('{} API requests made'.format(api_requests))

    return trail_list

# Parameters:
# mountain: name of ski area
#   type-string
# difficulty_modifiers: run with or without increased difficulty for tree trails
#   type-bool
# cardinal_direction: which way does the ski area face
#   type-string
#   valid options-'n','s','e','w' or some combination of the 4
# save_map: whethere to save the output to an svg file
#   type-bool
#   note-not recommended to be set to 'True' if more than one cardinal_direction 
#   is chosen


def runOSM(mountain, difficulty_modifiers=True, cardinal_direction='n', save_map=False):
    trail_list = load_osm(mountain + '.osm', True, mountain + '.csv')
    if trail_list == -1:
        return -1
    finished_trail_list = []
    saveData.cache_elevation(mountain + '.csv', trail_list)
    for entry in trail_list:
        trail = entry[0]
        trail['elevation'] = helper.smooth_elevations(
            trail['elevation'].to_list(), 1)
        trail['distance'] = helper.calculate_dist(trail['coordinates'])
        trail['elevation_change'] = helper.calulate_elevation_change(
            trail['elevation'])
        trail['slope'] = helper.calculate_slope(
            trail['elevation_change'], trail['distance'])
        trail['difficulty'] = helper.calculate_point_difficulty(trail['slope'])
        finished_trail_list.append((trail, entry[1], entry[2]))
    if 'w' in cardinal_direction or 'W' in cardinal_direction:
        saveData.create_map(finished_trail_list, mountain,
                            difficulty_modifiers, 1, -1, False, save_map)
        # ^^west facing
        # okemo, killington, stowe, bristol
    if 'e' in cardinal_direction or 'E' in cardinal_direction:
        saveData.create_map(finished_trail_list, mountain,
                            difficulty_modifiers, -1, 1, False, save_map)
        # ^^east facing
    if 's' in cardinal_direction or 'S' in cardinal_direction:
        saveData.create_map(finished_trail_list, mountain,
                            difficulty_modifiers, 1, 1, True, save_map)
        # ^^south facing
        # bromley
    if 'n' in cardinal_direction or 'N' in cardinal_direction:
        saveData.create_map(finished_trail_list, mountain,
                            difficulty_modifiers, -1, -1, True, save_map)
        # ^^north facing
        # cannon, holiday_valley, sunday_river, purgatory, pat's_peak, 
        # jay_peak, crested_butte
