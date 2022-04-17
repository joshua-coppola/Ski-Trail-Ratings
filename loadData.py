import pandas as pd
from os.path import exists
import time
from pip._vendor.rich.progress import track
from decimal import Decimal

import helper
import saveData
import osmHelper


def generate_trails_and_lifts(mountain: str, blacklist: str = ''):
    """
    Accepts the name of a mountain and the name of a mountain to blacklist
    and returns a tuple with a list of trails and a list of lifts

    #### Arguments: 
    - mountain - name of a ski area / name of an osm file w/o the file extension
    - blacklist - name of a ski area to ignore the trails for
        - if blacklist == mountain, only trails previously found for the mountain
        will be processed

    #### Returns:
    - (list(trail dict), list(lift dict))
        - trail dict = name (str), id (str), points_df (df), difficulty_modifier (float), is_area (bool), area_centerline_df (df)
        - lift dict = name (str), points_df (df)
    """
    filename = mountain + '.osm'
    cached_filename = mountain + '.csv'
    if not exists('osm/{}'.format(filename)):
        print('osm/{}'.format(filename))
        print('OSM file missing')
        return (-1, -1)
    if not exists('cached/trails/{}.csv'.format(blacklist)) and blacklist != '':
        print('Blacklist file missing')

    file = open('osm/{}'.format(filename), 'r')
    raw_table = file.readlines()

    if blacklist != '':
        try:
            blacklist_ids = (pd.read_csv(
                'cached/trails/{}.csv'.format(blacklist)))['id'].to_list()
            blacklist_ids_lifts = (pd.read_csv(
                'cached/lifts/{}.csv'.format(blacklist))['id'].to_list())
            blacklist_ids += blacklist_ids_lifts
            blacklist_ids = [str(x) for x in blacklist_ids]
        except:
            blacklist_ids = []
    else:
        blacklist_ids = []

    whitelist_mode = False
    if blacklist == mountain:
        whitelist_mode = True
    parsed_osm = osmHelper.process_osm(
        raw_table, blacklist_ids, whitelist_mode)

    #saveData.save_attributes(parsed_osm['attribute_list'], mountain + '.csv')

    cached = True
    if not exists('cached/trail_points/{}'.format(cached_filename)) and cached:
        cached = False
        print('Disabling trail cache loading: missing trail cache file.')

    lift_cached = True
    if not exists('cached/lift_points/{}'.format(cached_filename)) and cached:
        lift_cached = False
        print('Disabling lift cache loading: missing lift cache file.')

    trail_list = []
    api_requests = 0
    if cached:
        elevation_df = pd.read_csv(
            'cached/trail_points/{}'.format(cached_filename))
        elevation_df['coordinates'] = [
            (round(Decimal(x), 8), round(Decimal(y), 8)) for x, y in zip(elevation_df.lat, elevation_df.lon)]
        ele_dict = dict(zip(elevation_df.coordinates, elevation_df.elevation))
    if lift_cached:
        elevation_df = pd.read_csv(
            'cached/lift_points/{}'.format(cached_filename))
        elevation_df['coordinates'] = [
            (round(Decimal(x), 8), round(Decimal(y), 8)) for x, y in zip(elevation_df.lat, elevation_df.lon)]
        try:
            lift_ele_dict = dict(
                zip(elevation_df.coordinates, elevation_df.elevation))
        except:
            lift_ele_dict = {}
    last_called = time.time()

    print('Found \033[36m{} trails\033[0m and \033[36m{} lifts\033[0m\n'.format(
        parsed_osm['trail_count'], parsed_osm['lift_count']))

    # insert dummy column so that the progress bar completes properly
    parsed_osm['way_df'] = pd.concat(
        [parsed_osm['way_df'], pd.Series(0)], axis=1)
    for column, _ in zip(parsed_osm['way_df'], track(range(parsed_osm['trail_count']), description="Loading Trails… ")):
        temp_df = pd.merge((parsed_osm['way_df'])[column], parsed_osm['node_df'],
                           left_on=column, right_on='id')
        del temp_df['id']
        del temp_df[column]
        temp_df = helper.fill_in_point_gaps(temp_df, 15)
        temp_df['coordinates'] = [(round(Decimal(x[0]), 8), round(Decimal(x[1]), 8))
                                  for x in temp_df.coordinates]

        for row in parsed_osm['attribute_list']:
            if column == row['way_name']:
                difficulty_modifier = row['difficulty_modifier']
                area_flag = row['is_area']
                way_id = row['way_id']
        try:
            temp_df['elevation'] = [ele_dict[x] for x in temp_df.coordinates]
        except:
            result = helper.get_elevation(
                temp_df['coordinates'], last_called, column, api_requests)
            temp_df['elevation'] = result[0]
            api_requests = result[1]
            last_called = result[2]
        temp_area_line_df = pd.DataFrame()
        if area_flag:
            temp_area_line_df = helper.area_to_line(temp_df)
            temp_area_line_df['coordinates'] = [
                (round(Decimal(x[0]), 8), round(Decimal(x[1]), 8)) for x in temp_area_line_df.coordinates]
            try:
                temp_area_line_df['elevation'] = [ele_dict[x]
                                                  for x in temp_area_line_df.coordinates]
            except:
                result = helper.get_elevation(
                    temp_area_line_df['coordinates'], last_called, column, api_requests)
                temp_area_line_df['elevation'] = result[0]
                api_requests = result[1]
                last_called = result[2]
        trail_dict = {
            'name': column,
            'id': way_id,
            'points_df': temp_df,
            'difficulty_modifier': difficulty_modifier,
            'is_area': area_flag,
            'area_centerline_df': temp_area_line_df
        }
        trail_list.append(trail_dict)
    lift_list = []
    # insert dummy column so that the progress bar completes properly
    parsed_osm['lift_df'] = pd.concat(
        [parsed_osm['lift_df'], pd.Series(0)], axis=1)
    for column, _ in zip(parsed_osm['lift_df'], track(range(parsed_osm['lift_count']), description="Loading Lifts…  ")):
        temp_df = pd.merge(parsed_osm['lift_df'][column], parsed_osm['node_df'],
                           left_on=column, right_on='id')
        for row in parsed_osm['attribute_list']:
            if column == row['way_name']:
                way_id = row['way_id']
        temp_df = helper.fill_in_point_gaps(temp_df, 50)
        temp_df['coordinates'] = [(round(Decimal(x[0]), 8), round(Decimal(x[1]), 8))
                                  for x in temp_df.coordinates]
        try:
            temp_df['elevation'] = [lift_ele_dict[x]
                                    for x in temp_df.coordinates]
        except:
            result = helper.get_elevation(
                temp_df['coordinates'], last_called, column, api_requests)
            temp_df['elevation'] = result[0]
            api_requests = result[1]
            last_called = result[2]
        lift_list.append({'name': column, 'id': way_id, 'points_df': temp_df})
    if parsed_osm['trail_count'] == 0:
        print('No trails found.')
        return (-1, -1)
    print('\033[35m{} API Requests\033[0m\n'.format(api_requests))

    return (trail_list, lift_list)


def process_mountain(mountain: str, cardinal_direction: str, save_map: bool = False, blacklist: str = ''):
    """
    Takes in the general information about the mountain and calls the relevant
    functions to parse the osm, calculate difficulty, and create the map. The
    function returns the descriptive statistics about the mountain.

    #### Arguments:

    - mountain - name of mountain and OSM file (minus the extension)
    - cardinal_direction - what direction the mountain (mainly) faces
    - save_map - whether to save the map (default - false)
    - blacklist - name of a ski area to ignore the trails for
        - if blacklist == mountain, only trails previously found for the mountain
        will be processed

    #### Returns:

    - dict(difficulty (float), ease (float), vertical (float), trail_count (int), lift_count (int))
    - -1 in the case of failure
    """
    trail_list, lift_list = generate_trails_and_lifts(mountain, blacklist)
    if trail_list == -1:
        return -1

    for trail in trail_list:
        if not trail['is_area']:
            trail_points = trail['points_df']
        else:
            trail_points = trail['area_centerline_df']
            perimeter = trail['points_df']
            perimeter['distance'] = helper.calculate_dist(
                perimeter['coordinates'])
            perimeter['elevation_change'] = helper.calculate_elevation_change(
                perimeter['elevation'])
            perimeter['slope'] = helper.calculate_slope(
                perimeter['elevation_change'], perimeter['distance'])

        trail_points['distance'] = helper.calculate_dist(
            trail_points['coordinates'])
        trail_points['elevation_change'] = helper.calculate_elevation_change(
            trail_points['elevation'])
        trail_points['slope'] = helper.calculate_slope(
            trail_points['elevation_change'], trail_points['distance'])
        trail_points['difficulty'] = helper.calculate_point_difficulty(
            trail_points['slope'])

        if not trail['is_area']:
            trail['points_df'] = trail_points
        else:
            trail['points_df'] = perimeter
            trail['area_centerline_df'] = trail_points
        trail['difficulty'] = helper.rate_trail(trail_points.difficulty)
        trail['steepest_pitch'] = trail['difficulty']
        trail['vert'] = helper.calculate_trail_vert(trail_points.elevation)
        trail['length'] = helper.get_trail_length(trail_points.coordinates)

    for lift in lift_list:
        lift_points = lift['points_df']
        lift_points['distance'] = helper.calculate_dist(
            lift_points['coordinates'])
        lift_points['elevation_change'] = helper.calculate_elevation_change(
            lift_points['elevation'])
        lift_points['slope'] = helper.calculate_slope(
            lift_points['elevation_change'], lift_points['distance'])
        lift['points_df'] = lift_points

    mtn_difficulty = saveData.create_map(
        trail_list, lift_list, mountain, cardinal_direction, save_map)
    if mtn_difficulty == -1:
        return -1
    vert = helper.calculate_mtn_vert(trail_list)
    saveData.save_attributes(mountain + '.csv', trail_list, lift_list)
    saveData.cache_trail_points(mountain + '.csv', trail_list)
    saveData.cache_lift_points(mountain + '.csv', lift_list)
    saveData.save_bounding_box(mountain + '.csv', trail_list, lift_list)

    output = {
        'difficulty': mtn_difficulty[0],
        'ease': mtn_difficulty[1],
        'vertical': round(vert),
        'trail_count': len(trail_list),
        'lift_count': len(lift_list)
    }
    return output


def osm(mountain: str, direction: str = '', save_map: bool = False, blacklist: str = '', location: str = ''):
    """
    Takes in the general information about the mountain, fills in missing information
    if it is stored from missing runs, calls process mountain, then saves the results
    to mountain_list.csv

    #### Arguments:

    - mountain - name of mountain/ OSM file
    - direction - what direction the mountain (mainly) faces
    - save_map - whether to save the map (default - false)
    - blacklist - name of a ski area to ignore the trails for
        - if blacklist == mountain, only trails previously found for the mountain
        will be processed
    - location - what state the mountain is in (2 letter codes)

    #### Returns:

    - 0 for success, -1 for failure
    """

    if '.osm' in mountain:
        mountain = mountain.replace('.osm', '')

    filename = f'{mountain}.osm'

    print('\n\033[1mProcessing {}\033[0m'.format(helper.format_name(mountain)))
    mountain_df = pd.read_csv('mountain_list.csv')
    previously_run = False
    if filename in mountain_df.file_name.to_list():
        previously_run = True
        mountain_row = mountain_df.loc[mountain_df.file_name == filename]
    if direction == '' and previously_run:
        value = mountain_row.direction.to_list()[0]
        if str(value) != 'nan':
            direction = value
    if blacklist == '' and previously_run:
        value = mountain_row.blacklist.to_list()[0]
        if str(value) != 'nan':
            blacklist = value
    if location == '' and previously_run:
        value = mountain_row.state.to_list()[0]
        if str(value) != 'nan':
            location = value
    mountain_attributes = process_mountain(
        mountain, direction, save_map, blacklist)
    if mountain_attributes == -1:
        return -1
    if save_map and exists('mountain_list.csv'):
        # row = (mountain, direction, state, region, difficulty, ease, vert, trail_count, lift_count, blacklist)
        row = [[helper.format_name(mountain), f'{mountain}.osm', direction, location, helper.assign_region(location), mountain_attributes['difficulty'], mountain_attributes['ease'],
                mountain_attributes['vertical'], mountain_attributes['trail_count'], mountain_attributes['lift_count'], blacklist]]
        if previously_run:
            mountain_df.loc[mountain_df.mountain == mountain] = row
            output = mountain_df
        else:
            row = pd.Series(row[0], index=mountain_df.columns)
            output = mountain_df.append(row, ignore_index=True)
            output.sort_values(by=['mountain'], inplace=True)
        output['trail_count'] = output['trail_count'].astype(int)
        output['lift_count'] = output['lift_count'].astype(int)
        output.to_csv('mountain_list.csv', index=False)
    else:
        print('Mountain data not saved. If this is unexpected, please make sure you have a file called mountain_list.csv')
    return 0


def bulk_osm(input_csv: str = 'mountain_list.csv'):
    """
    Accepts the name of a csv that contains the information to create maps for
    a list of mountains and calls osm to process each one

    #### Arguments:

    - input_csv - csv filename with or without the file extension

    #### Return:

    - Void
    """
    if '.csv' not in input_csv:
        input_csv += '.csv'

    mountain_info_df = pd.read_csv(input_csv, keep_default_na=False)
    for row in mountain_info_df.itertuples():
        if row.mountain[0] == '#':
            continue
        osm(row.file_name.split('.')[0], row.direction, True, row.blacklist, row.state)


def barplot(save_output: bool = False):
    """
    Creates Difficulty Barplots for all mountains within mountain_list.csv

    #### Arguments:

    - save_output - whether to save plots (default = false)

    #### Return:

    - Void
    """

    if not exists('mountain_list.csv'):
        print('Missing cache files, please run bulk_osm or osm and set save_map=True.')
        return
    df = pd.read_csv('mountain_list.csv')
    df['mountain'] = [helper.format_name(x) for x in df['mountain']]
    saveData.create_difficulty_barplot(df, 'USA', save_output)

    state_list = df.state.unique()
    for state in state_list:
        if len(state.split()) > 1:
            continue
        temp_df = df[df['state'].str.contains(state)]
        region = helper.assign_region(state)
        saveData.create_difficulty_barplot(
            temp_df, f'{region}/{state}', save_output)
    for region in ['northeast', 'southeast', 'midwest', 'west']:
        temp_df = df.loc[df['region'] == region]
        saveData.create_difficulty_barplot(
            temp_df, helper.format_name(region), save_output)
