import pandas as pd
from os.path import exists
from ast import literal_eval

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
    saveData.create_gpx_map(df)

# accepts a osm filename and returns a list of tuples.
# Each tuple contains a dataframe with
# 4 columns: latitude, longitude, lat/lon pairs, and elevation (meters)
# a string with the trailname,
# and an int (0-1) to denote if the trail is gladed


def load_osm(filename, cached=False, cached_filename=''):
    if not exists('osm/{}'.format(filename)):
        print('OSM file missing')
        return (-1, -1)
    file = open('osm/{}'.format(filename), 'r')
    print('Opening File')
    raw_table = file.readlines()
    node_df = pd.DataFrame()
    way_df = pd.DataFrame()
    lift_df = pd.DataFrame()
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
    is_lift = True
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
            if '<tag k="aerialway"' in row:
                is_lift = True

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
                if is_lift:
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
            #id.append(split_row[1])
            #lat.append(float(split_row[15]))
            #lon.append(float(split_row[17]))
            #coordinates.append((float(split_row[15]), float(split_row[17])))
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
        if trail_num % 10 == 1 or trail_num == total_trail_count:
            print('Processing trail {}/{}'.format(trail_num, total_trail_count))
        temp_df = pd.merge(way_df[column], node_df,
                           left_on=column, right_on='id')
        del temp_df['id']
        del temp_df[column]
        temp_df = helper.fill_in_point_gaps(temp_df, 15)
        for row in useful_info_list:
            if column == row[0]:
                difficulty_modifier = row[1]
                if row[2] == True and helper.get_trail_length(temp_df['coordinates']) < 2000:
                    temp_df = helper.area_to_line(temp_df)
        if not cached:
            result = helper.get_elevation(temp_df['coordinates'], column, api_requests)
            temp_df['elevation'] = result[0]
            api_requests = result[1]
        else:
            row_count = temp_df.shape[0]
            temp_df_2 = pd.merge(temp_df, elevation_df, on='coordinates')
            # if cache is missing data
            if temp_df_2.shape[0] < row_count:
                result = helper.get_elevation(temp_df['coordinates'], column, api_requests)
                temp_df['elevation'] = result[0]
                api_requests = result[1]
            else: temp_df = temp_df_2
        trail_list.append((temp_df, column, difficulty_modifier))
    lift_list = []
    for column in lift_df:
        temp_df = pd.merge(lift_df[column], node_df, left_on=column, right_on='id')
        temp_df = helper.fill_in_point_gaps(temp_df, 50)
        lift_list.append((temp_df, column))
    if total_trail_count == 0:
        print('No trails found.')
        return (-1, -1)
    print('All trails sucessfully loaded')
    print('{} API requests made'.format(api_requests))

    return (trail_list, lift_list)

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
#
# Return: the relative difficultly and ease of the difficult and beginner terrain
#   type-tuple(tuple,tuple)


def runOSM(mountain, difficulty_modifiers=True, cardinal_direction='n', save_map=False):
    trail_list, lift_list = load_osm(mountain + '.osm', True, mountain + '.csv')
    if trail_list == -1:
        return -1
    finished_trail_list = []
    saveData.cache_elevation(mountain + '.csv', trail_list)
    for entry in trail_list:
        trail = entry[0]
        trail['elevation'] = helper.smooth_elevations(
            trail['elevation'].to_list(), 0)
        trail['distance'] = helper.calculate_dist(trail['coordinates'])
        trail['elevation_change'] = helper.calulate_elevation_change(
            trail['elevation'])
        trail['slope'] = helper.calculate_slope(
            trail['elevation_change'], trail['distance'])
        trail['difficulty'] = helper.calculate_point_difficulty(trail['slope'])
        finished_trail_list.append((trail, entry[1], entry[2]))
    if 'w' in cardinal_direction or 'W' in cardinal_direction:
        mtn_difficulty = saveData.create_map(finished_trail_list, lift_list, mountain,
                            difficulty_modifiers, 1, -1, False, save_map)
        # ^^west facing
    if 'e' in cardinal_direction or 'E' in cardinal_direction:
        mtn_difficulty = saveData.create_map(finished_trail_list, lift_list, mountain,
                            difficulty_modifiers, -1, 1, False, save_map)
        # ^^east facing
    if 's' in cardinal_direction or 'S' in cardinal_direction:
        mtn_difficulty = saveData.create_map(finished_trail_list, lift_list, mountain,
                            difficulty_modifiers, 1, 1, True, save_map)
        # ^^south facing
    if 'n' in cardinal_direction or 'N' in cardinal_direction:
        mtn_difficulty = saveData.create_map(finished_trail_list, lift_list, mountain,
                            difficulty_modifiers, -1, -1, True, save_map)
        # ^^north facing
    return mtn_difficulty