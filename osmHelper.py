import pandas as pd
from typing import List


def process_way_tags(line: str, trail_attributes: dict) -> dict:
    """
    Adds / Removes tags based on the passed line from an osm file

    #### Arguments:

    - line - one line from an osm file
    - trail_attributes - dict of trail tags. Created by process_osm

    #### Returns:

    - trail_attributes - dict of trail tags
    """
    if '<nd' in line:
        split_row = line.split('"')
        if split_row[1] != '':
            trail_attributes['node_id_list'].append(split_row[1])
    if '<tag k="name"' in line:
        split_row = line.split('"')
        trail_attributes['way_name'] = split_row[3]
    if '<tag k="piste:difficulty"' in line:
        trail_attributes['is_trail'] = True
    if '<tag k="piste:type"' in line and 'downhill' in line:
        trail_attributes['is_trail'] = True
    if '<tag k="piste:type"' in line and 'backcountry' in line:
        trail_attributes['is_backcountry'] = True
    if '<tag k="piste:type"' in line and 'nordic' in line:
        trail_attributes['is_backcountry'] = True
    if '<tag k="piste:type"' in line and 'skitour' in line:
        trail_attributes['is_backcountry'] = True
    if '<tag k="landuse" v="grass"/>' in line:
        trail_attributes['is_backcountry'] = True
    if '<tag k="natural" v="grassland"/>' in line:
        trail_attributes['is_backcountry'] = True
    if '<tag k="piste:grooming" v="classic+skating"/>' in line:
        trail_attributes['is_backcountry'] = True
    if '<tag k="piste:type" v="hike"/>' in line:
        trail_attributes['is_backcountry'] = True
    if '<tag k="mtb:scale:imba"' in line:
        trail_attributes['is_backcountry'] = True
    if '<tag k="gladed" v="yes"/>' in line and not trail_attributes['is_glade']:
        trail_attributes['difficulty_modifier'] += 1
        trail_attributes['is_glade'] = True
    if '<tag k="gladed" v="no"/>' in line:
        trail_attributes['glade_override'] = True
    if '<tag k="leaf_type"' in line and not trail_attributes['is_glade']:
        trail_attributes['difficulty_modifier'] += 1
        trail_attributes['is_glade'] = True
    if '<tag k="leaf_type"' in line or '<tag k="area" v="yes"/>' in line:
        trail_attributes['is_area'] = True
    if '<tag k="natural" v="wood"/>' in line:
        trail_attributes['is_area'] = True
    if 'glade' in line and not trail_attributes['is_glade']:
        trail_attributes['difficulty_modifier'] += 1
        trail_attributes['is_glade'] = True
    if 'Glade' in line and not trail_attributes['is_glade']:
        trail_attributes['difficulty_modifier'] += 1
        trail_attributes['is_glade'] = True
    if '<tag k="aerialway"' in line and not 'v="zip_line"' in line and not 'v="station"' in line and not 'v="goods"' in line:
        trail_attributes['is_lift'] = True
    if 'Tree Skiing' in line and not trail_attributes['is_glade']:
        trail_attributes['difficulty_modifier'] += 1
        trail_attributes['is_glade'] = True
    return trail_attributes


def process_osm(lines: List[str], blacklist: str, whitelist_mode: bool = False) -> dict:
    """
    Accepts a list of lines from an OSM file and processes them into more useful formats

    #### Arguments:

    - lines - list of strings
    - blacklist - list of trails to blacklist
    - whitelist_mode - whether to invert the blacklist to a whitelist

    #### Returns:

    - parsed_osm - dict {
        'node_df' (dataframe),
        'way_df' (dataframe),
        'lift_df' (dataframe),
        'useful_info_list' (list(tuple)),
        'total_trail_count' (int),
        'name_and_id_list' (list(tuple))
        }
    """
    DEBUG_TRAILS = False

    way_df = pd.DataFrame()
    lift_df = pd.DataFrame()
    id = []  # for node_df
    lat = []  # for node_df
    lon = []  # for node_df
    coordinates = []  # for node_df
    attribute_list = []
    blank_name_count = 0
    total_trail_count = 0
    total_lift_count = 0

    in_way = False

    for row in lines:
        row = str(row)
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
        # start of a way
        if '<way' in row:
            in_way = True
            trail_attributes = {
                'way_name': '',
                'way_id': row.split('"')[1],
                'is_trail': False,
                'is_lift': False,
                'is_glade': False,
                'is_backcountry': False,
                'is_area': False,
                'glade_override': False,
                'difficulty_modifier': 0,
                'node_id_list': []
            }
            if (str(trail_attributes['way_id']) not in blacklist) and whitelist_mode:
                in_way = False
            if (str(trail_attributes['way_id']) in blacklist) and not whitelist_mode:
                in_way = False
        # handling when inside a way
        if in_way:
            if '</way>' in row:
                if trail_attributes['glade_override'] and trail_attributes['is_glade']:
                    trail_attributes['difficulty_modifier'] -= 1
                if trail_attributes['is_trail'] and not trail_attributes['is_backcountry']:
                    total_trail_count += 1
                    if DEBUG_TRAILS:
                        trail_attributes['way_name'] = trail_attributes['way_id']
                    if trail_attributes['way_name'] == '':
                        trail_attributes['way_name'] = ' _' + \
                            str(blank_name_count)
                        blank_name_count += 1
                    if trail_attributes['way_name'] in way_df.columns:
                        trail_attributes['way_name'] = trail_attributes['way_name'] + \
                            '_' + str(blank_name_count)
                        blank_name_count += 1
                    temp_df = pd.DataFrame()
                    temp_df[trail_attributes['way_name']
                            ] = trail_attributes['node_id_list']
                    way_df = pd.concat([way_df, temp_df], axis=1)
                    attribute_list.append(trail_attributes)
                if trail_attributes['is_lift']:
                    total_lift_count += 1
                    if DEBUG_TRAILS:
                        trail_attributes['way_name'] = trail_attributes['way_id']
                    if trail_attributes['way_name'] == '':
                        trail_attributes['way_name'] = ' _' + \
                            str(blank_name_count)
                        blank_name_count += 1
                    if trail_attributes['way_name'] in lift_df.columns:
                        trail_attributes['way_name'] = trail_attributes['way_name'] + \
                            '_' + str(blank_name_count)
                        blank_name_count += 1
                    temp_df = pd.DataFrame()
                    temp_df[trail_attributes['way_name']
                            ] = trail_attributes['node_id_list']
                    lift_df = pd.concat([lift_df, temp_df], axis=1)
                    attribute_list.append(trail_attributes)
                in_way = False
            else:
                trail_attributes = process_way_tags(row, trail_attributes)
    node_df = pd.DataFrame()
    node_df['id'] = id
    node_df['lat'] = lat
    node_df['lon'] = lon
    node_df['coordinates'] = coordinates

    parsed_osm = {
        'node_df': node_df,
        'way_df': way_df,
        'lift_df': lift_df,
        'trail_count': total_trail_count,
        'lift_count': total_lift_count,
        'attribute_list': attribute_list
    }

    return parsed_osm
