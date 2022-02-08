import pandas as pd

# Parameters:
# line: one line of the osm file
#   type-str
# difficulty_modifier: int value for additional difficulty parameters
#   type-int
# is_trail: trail flag
#   type-bool
# is_lift: lift flag
#   type-bool
# is_glade: woods trail flag
#   type-bool
# is_area: area flag
#   type-bool
# is_backcountry: non-frontside trail flag
#   type-bool
# glade_override: overrides is_glade if set
#   type-bool
#
# Return: the modified states of the parameters plus node_id and way_name
#   type-tuple(str, str, int, bool, bool, bool, bool, bool, bool)

def process_way_tags(line, difficulty_modifier, is_trail, is_lift, is_glade, is_area, is_backcountry, glade_override):
    node_id = ''
    way_name = ''
    if '<nd' in line:
        split_row = line.split('"')
        node_id = split_row[1]
    if '<tag k="name"' in line:
        split_row = line.split('"')
        way_name = split_row[3]
    if '<tag k="piste:difficulty"' in line:
        is_trail = True
    if '<tag k="piste:type"' in line and 'downhill' in line:
        is_trail = True
    if '<tag k="piste:type"' in line and 'backcountry' in line:
        is_backcountry = True
    if '<tag k="piste:type"' in line and 'nordic' in line:
        is_backcountry = True
    if '<tag k="piste:type"' in line and 'skitour' in line:
        is_backcountry = True
    if '<tag k="gladed" v="yes"/>' in line and not is_glade:
        difficulty_modifier += 1
        is_glade = True
    if '<tag k="gladed" v="no"/>' in line:
        glade_override = True
    if '<tag k="leaf_type"' in line and not is_glade:
        difficulty_modifier += 1
        is_glade = True
    if '<tag k="leaf_type"' in line or '<tag k="area" v="yes"/>' in line:
        is_area = True
    if '<tag k="natural" v="wood"/>' in line:
        is_area = True
    if 'glade' in line and not is_glade:
        difficulty_modifier += 1
        is_glade = True
    if 'Glade' in line and not is_glade:
        difficulty_modifier += 1
        is_glade = True
    if '<tag k="aerialway"' in line and not 'v="zip_line"' in line and not 'v="station"' in line:
        is_lift = True
    if 'Tree Skiing' in line and not is_glade:
        difficulty_modifier += 1
        is_glade = True
    return((node_id, way_name, difficulty_modifier, is_trail, is_lift, is_glade, is_area, is_backcountry, glade_override))

# Parameters:
# lines: a list of lines from the osm file
#   type-list(str)
# blacklist: name of blacklist files
#   type-str
# whitelist_mode: toggle between using a whitelist or a blacklist
#   type-bool
#
# Returns: tuple of nodes and trail and lift info
#   type-tuple(df, df, df, list, int, list)

def process_osm(lines, blacklist, whitelist_mode=False):
    DEBUG_TRAILS = False

    way_df = pd.DataFrame()
    lift_df = pd.DataFrame()
    id = []  # for node_df
    lat = []  # for node_df
    lon = []  # for node_df
    coordinates = []  # for node_df
    in_way_ids = []  # all OSM ids for a way, used for way_df
    useful_info_list = []  # list((way_name, difficulty_modifier, is_area))
    trail_and_id_list = []  # list((trail_name, OSM id))
    blank_name_count = 0
    total_trail_count = 0

    in_way = False
    way_name = ''

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
            is_trail = False
            is_glade = False
            is_backcountry = False
            is_area = False
            is_lift = False
            glade_override = False
            difficulty_modifier = 0
            way_id = row.split('"')[1]
            if (str(way_id) not in blacklist) and whitelist_mode:
                in_way = False
            if (str(way_id) in blacklist) and not whitelist_mode:
                in_way = False
        # handling when inside a way
        if in_way:
            if '</way>' in row:
                if glade_override and is_glade:
                    difficulty_modifier -= 1
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
                        (way_name, difficulty_modifier, is_area, way_id))
                if is_lift:
                    trail_and_id_list.append((way_name, way_id))
                    if DEBUG_TRAILS:
                        way_name = way_id
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
            else:
                tags = process_way_tags(row, difficulty_modifier, is_trail, is_lift, is_glade, is_area,is_backcountry, glade_override)
                if tags[0] != '':
                    in_way_ids.append(tags[0])
                if tags[1] != '':
                    way_name = tags[1]
                _, _, difficulty_modifier, is_trail, is_lift, is_glade, is_area, is_backcountry, glade_override = tags
    node_df = pd.DataFrame()
    node_df['id'] = id
    node_df['lat'] = lat
    node_df['lon'] = lon
    node_df['coordinates'] = coordinates

    return (node_df, way_df, lift_df, useful_info_list, total_trail_count, trail_and_id_list)