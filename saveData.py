from decimal import Decimal
import matplotlib.pyplot as plt
import pandas as pd
from pip._vendor.rich.progress import track

import helper
import mapHelper

# Parameters:
# filename: name of csv to save data to
#   type-string
# list_df: list of trails
#   type-list of tuples
#
# Return: none


def cache_trail_points(filename, list_dfs):
    output_df = pd.DataFrame(
        columns=['trail_id', 'for_display', 'lat', 'lon', 'elevation'])
    for entry in list_dfs:
        trail = pd.DataFrame()
        trail['trail_id'] = entry['id']
        trail['for_display'] = True
        trail['lat'] = entry['points_df'].lat
        trail['lon'] = entry['points_df'].lon
        trail['elevation'] = entry['points_df'].elevation
        trail['slope'] = entry['points_df'].slope
        trail['trail_id'] = entry['id']
        trail['for_display'] = True
        output_df = output_df.append(trail)
        if entry['is_area']:
            trail = pd.DataFrame()
            trail['trail_id'] = entry['id']
            trail['for_display'] = False
            trail['lat'] = entry['area_centerline_df'].lat
            trail['lon'] = entry['area_centerline_df'].lon
            trail['elevation'] = entry['area_centerline_df'].elevation
            trail['slope'] = entry['area_centerline_df'].slope
            trail['trail_id'] = entry['id']
            trail['for_display'] = False
            output_df = output_df.append(trail)
    output_df['lat'] = [round(Decimal(x), 8) for x in output_df.lat]
    output_df['lon'] = [round(Decimal(x), 8) for x in output_df.lon]
    output_df['elevation'] = [round(Decimal(x), 2)
                              for x in output_df.elevation]
    output_df['slope'] = [round(Decimal(x), 2) for x in output_df.slope]
    output_df.drop_duplicates(inplace=True)
    output_df.to_csv('cached/trail_points/{}'.format(filename))

# Parameters:
# tuple_list: list of trail names and osm ids
#   type-list of tuples
# mountain_name: name of ski area
#   type-string
#
# Return: none


def save_trail_ids(tuple_list, filename):
    name_list = [x[0] for x in tuple_list]
    id_list = [x[1] for x in tuple_list]
    export_df = pd.DataFrame()
    export_df['name'] = name_list
    export_df['id'] = id_list
    export_df.to_csv('cached/osm_ids/{}'.format(filename), index=False)


# accepts a list of trail tuples, a list of lift tuples, the name of the ski area,
# and the direction the map should face. The last param is a bool for whether to
# save the map.
#
# Return: the relative difficulty of hard terrain and the relative ease
# for beginner terrain
#   type-tuple(float,float)


def create_map(trails, lifts, mountain, cardinal_direction, save=False):
    print('Creating Map')
    mapHelper.format_map_template(trails, lifts, mountain, cardinal_direction)
    objects = []
    for entry in lifts:
        lift_name = entry['name']
        if '_' in lift_name:
            lift_name = lift_name.split('_')[0]
        objects.append(((entry['points_df'], lift_name, 0, 0), cardinal_direction, 'grey'))

    rating_list = []
    for entry in trails:
        if not entry['is_area']:
            index = 'points_df'
        else:
            index = 'area_centerline_df'
        rating = helper.rate_trail(entry[index]['difficulty'])
        if helper.get_trail_length(entry[index].coordinates) > 100:
            rating_list.append(round((rating * 100), 0))
        color = helper.set_color(rating, entry['difficulty_modifier'])
        rating = round(rating * 100, 1)
        trail_name = entry['name']
        if '_' in trail_name:
            trail_name = trail_name.split('_')[0]

        trail_name = '{} {}{}'.format(
            trail_name.strip(), rating, u'\N{DEGREE SIGN}')
        objects.append(((entry['points_df'], trail_name, entry['difficulty_modifier'], entry['is_area'], entry['area_centerline_df']), cardinal_direction, color))

    for i in track(range(len(objects)), description="Placing Objects…"):
        mapHelper.place_object(objects[i])
    

    if save:
        plt.savefig(
            'maps/{}.svg'.format(helper.format_name(mountain)), format='svg')
        print('SVG saved')
    rating_list.sort(reverse=True)
    long_list = 30
    if len(rating_list) < 30:
        long_list = len(rating_list)
    hard_list = [rating_list[0:long_list], rating_list[0:5]]
    mountain_difficulty_rating = (
        (sum(hard_list[0])/long_list) * .2) + ((sum(hard_list[1])/5) * .8)
    mountain_difficulty_rating = round(mountain_difficulty_rating, 1)
    print('Difficultly Rating: {}'.format(mountain_difficulty_rating))
    rating_list.sort()
    easy_list = [rating_list[0:long_list], rating_list[0:5]]
    mountain_ease_rating = (
        (sum(easy_list[0])/long_list) * .2) + ((sum(easy_list[1])/5) * .8)
    mountain_ease_rating = round(mountain_ease_rating, 1)

    print('Beginner Friendliness Rating: {}'.format(mountain_ease_rating))
    plt.draw()
    return((mountain_difficulty_rating, mountain_ease_rating))

# Parameters:
# df_difficulty: dataframe with column for mountain name, difficulty rating, and color
#   type-df(string, float, string)
# df_ease: dataframe with column for mountain name, beginner friendliness rating, and color
#   type-df(string, float, string)
# save: bool for whether to save the output to an svg
#   type-bool
#
# Return: none


def create_difficulty_barplot(df, file_name ,save=False):
    if len(file_name.split('/')) > 1:
        name = file_name.split('/')[1]
    else:
        name = file_name 
    df = df.sort_values(by='difficulty', ascending=False)
    df['diff_color'] = [helper.set_color(x/100) for x in df['difficulty']]
    plt.figure(figsize=(8, (len(df['difficulty'])*.13) + 1.5))
    plt.barh(df['mountain'], df['difficulty'], color=df['diff_color'])
    plt.title('{} Difficulty Comparison'.format(name), fontsize=20)
    plt.xlabel('Longer bar = more expert friendly')
    plt.xlim(0,55)
    plt.tight_layout()
    plt.grid(axis='x')
    for i, value in enumerate(df.difficulty):
        plt.text(value+1, i, round(value, 1), ha='center', va='center', size=6)
        text_color = 'white'
        if df.diff_color.to_list()[i] == 'gold':
            text_color = 'black'
        plt.text(0.5, i, i + 1, ha='left', va='center', size = 7, color=text_color)

    if save:
        plt.savefig('maps/difficulty_barplots/{}.svg'.format(file_name), format='svg')
    plt.draw()
    df['ease_color'] = [helper.set_color(x/100) for x in df['ease']]
    df['ease'] = 30 - df['ease']
    df = df.sort_values(by='ease', ascending=True)
    plt.figure(figsize=(8, (len(df['ease'])*.13) + 1.5))
    plt.barh(df['mountain'], df['ease'], color=df['ease_color'])
    plt.title(f'{name} Beginner Friendliness', fontsize=20)
    plt.xlabel('Longer bar = more beginner friendly')
    plt.xlim(0,30)
    plt.tight_layout()
    plt.grid(axis='x')
    row_count = len(df.ease)
    for i, value in enumerate(df.ease):
        plt.text(value+.5, i, round(value, 1), ha='center', va='center', size=6)
        plt.text(0.25, i, row_count - i, ha='left', va='center', size = 7, color='white')

    if save:
        plt.savefig('maps/beginner_friendliness_barplots/{}.svg'.format(file_name), format='svg')
        print(f'{file_name} SVG saved')
    plt.draw()
