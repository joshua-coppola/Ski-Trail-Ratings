from decimal import Decimal
import matplotlib.pyplot as plt
import pandas as pd
from pip._vendor.rich.progress import track
from typing import List
from typing import Tuple

import helper
import mapHelper


def cache_trail_points(filename: str, list_dfs: pd.DataFrame) -> None:
    """
    Takes a list of trails and saves them to a cache file to prevent unneeded API calls

    #### Arguments:

        - filename - name of output file location
        - list_dfs - list of trail dicts

    #### Returns:

        - Void
    """
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
        trail['index'] = trail.index
        output_df = pd.concat([output_df, trail])
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
            trail['index'] = trail.index
            output_df = pd.concat([output_df, trail])
    output_df['lat'] = [round(Decimal(x), 8) for x in output_df.lat]
    output_df['lon'] = [round(Decimal(x), 8) for x in output_df.lon]
    output_df['elevation'] = [round(Decimal(x), 2)
                              for x in output_df.elevation]
    output_df['slope'] = [round(Decimal(x), 2) for x in output_df.slope]
    output_df['index'] = output_df['index'].astype(int)
    output_df.drop_duplicates(inplace=True)
    output_df.to_csv('cached/trail_points/{}'.format(filename), index=False)


def cache_lift_points(filename: str, list_dfs: pd.DataFrame) -> None:
    """
    Takes a list of trails and saves them to a cache file to prevent unneeded API calls

    #### Arguments:

        - filename - name of output file location
        - list_dfs - list of trail dicts

    #### Returns:

        - Void
    """
    output_df = pd.DataFrame(
        columns=['lift_id', 'for_display', 'lat', 'lon', 'elevation', 'slope'])
    for entry in list_dfs:
        lift = pd.DataFrame()
        lift['lift_id'] = entry['id']
        lift['for_display'] = True
        lift['lat'] = entry['points_df'].lat
        lift['lon'] = entry['points_df'].lon
        lift['elevation'] = entry['points_df'].elevation
        lift['slope'] = entry['points_df'].slope
        lift['lift_id'] = entry['id']
        lift['for_display'] = True
        lift['index'] = lift.index
        output_df = pd.concat([output_df, lift])
    output_df['lat'] = [round(Decimal(x), 8) for x in output_df.lat]
    output_df['lon'] = [round(Decimal(x), 8) for x in output_df.lon]
    output_df['elevation'] = [round(Decimal(x), 2)
                              for x in output_df.elevation]
    output_df['slope'] = [round(Decimal(x), 2) for x in output_df.slope]
    if(output_df.shape[0]) != 0:
        output_df['index'] = output_df['index'].astype(int)
    output_df.drop_duplicates(inplace=True)
    output_df.to_csv('cached/lift_points/{}'.format(filename), index=False)


def save_attributes(filename: str, trail_list: List[dict], lift_list: List[dict]) -> None:
    """
    Saves a list of trail names and ids to use as a blacklist / whitelist later

    #### Arguments:

        - filename - name of output file location (in the form mountain.csv)
        - trail_list - list(dict)

    #### Returns:

        - Void
    """
    trail_df = pd.DataFrame(trail_list)
    lift_df = pd.DataFrame(lift_list)
    if(trail_df.shape[0]) != 0:
        trail_df = trail_df[['name', 'id', 'is_area', 'difficulty',
                             'difficulty_modifier', 'steepest_pitch', 'vert', 'length']]
        trail_df['difficulty'] = [round(Decimal(x * 100), 1)
                                  for x in trail_df.difficulty]
        trail_df['steepest_pitch'] = [
            round(Decimal(x * 100), 1) for x in trail_df.steepest_pitch]
        trail_df['vert'] = [round(Decimal(x), 1) for x in trail_df.vert]
        trail_df['length'] = [round(Decimal(x), 1) for x in trail_df.length]
    if(lift_df.shape[0]) != 0:
        lift_df = lift_df[['name', 'id']]
    trail_df.to_csv('cached/trails/{}'.format(filename), index=False)
    lift_df.to_csv('cached/lifts/{}'.format(filename), index=False)


def create_map(trails: List[dict], lifts: List[dict], mountain: str, cardinal_direction: str, save: bool = False) -> Tuple[float, float]:
    """
    Takes the information about the mountain, trails, and lifts, and plots them

    #### Arguments:

    - trails - list of trail dicts
        -trail_dict = {
            'name',
            'id',
            'points_df',
            'difficulty_modifier',
            'is_area',
            'area_centerline_df'
        }
    - lifts - list(dict('name', 'points_df'))
    - mountain - name of mountain and OSM file (minus the extension)
    - cardinal_direction - what direction the mountain (mainly) faces
    - save_map - whether to save the map (default - false)

    #### Returns:

    - (mountain_difficulty (float), mountain_ease (float))
    """
    mapHelper.format_map_template(trails, lifts, mountain, cardinal_direction)
    objects = []
    for entry in lifts:
        lift_name = entry['name']
        if '_' in lift_name:
            lift_name = lift_name.split('_')[0]
        lift_dict = {
            'points_df': entry['points_df'],
            'name': lift_name,
            'is_area': False,
            'difficulty_modifier': 0,
            'direction': cardinal_direction,
            'color': 'grey'
        }
        objects.append(lift_dict)

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
        trail_dict = {
            'points_df': entry['points_df'],
            'name': trail_name,
            'is_area': entry['is_area'],
            'difficulty_modifier': entry['difficulty_modifier'],
            'direction': cardinal_direction,
            'color': color
        }
        objects.append(trail_dict)

    for i in track(range(len(objects)), description="Placing Objects…"):
        mapHelper.place_object(objects[i])

    if save:
        plt.savefig(
            'figures/maps/{}.svg'.format(helper.format_name(mountain)), format='svg')
        plt.savefig('figures/transparent_maps/{}.svg'.format(
            helper.format_name(mountain)), format='svg', transparent=True)
    rating_list.sort(reverse=True)
    long_list = 30
    if len(rating_list) < 30:
        long_list = len(rating_list)
    hard_list = [rating_list[0:long_list], rating_list[0:5]]
    mountain_difficulty_rating = (
        (sum(hard_list[0])/long_list) * .2) + ((sum(hard_list[1])/5) * .8)
    mountain_difficulty_rating = round(mountain_difficulty_rating, 1)
    #print('\033[36mDifficultly Rating: {}\033[0m'.format(mountain_difficulty_rating))
    rating_list.sort()
    easy_list = [rating_list[0:long_list], rating_list[0:5]]
    mountain_ease_rating = (
        (sum(easy_list[0])/long_list) * .2) + ((sum(easy_list[1])/5) * .8)
    mountain_ease_rating = round(mountain_ease_rating, 1)

    #print('\033[36mBeginner Friendliness Rating: {}\033[0m'.format(mountain_ease_rating))
    print(
        f'Mountain Rating: \033[36m{mountain_difficulty_rating}D, {mountain_ease_rating}E\033[0m')
    plt.draw()
    return((mountain_difficulty_rating, mountain_ease_rating))


def create_difficulty_barplot(df: pd.DataFrame, file_name: str, save: bool = False) -> None:
    """
    Creates difficulty and ease barplots for the provided dataframe

    #### Arguments
    - df - dataframe[['mountain_name','difficult_rating','ease_rating']]
    - file_name - partial file path (without file extension)
    - save - whether to save file (default = false)

    ### Returns:
    - Void
    """
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
    plt.xlim(0, 55)
    plt.tight_layout()
    plt.grid(axis='x')
    for i, value in enumerate(df.difficulty):
        plt.text(value+1, i, round(value, 1), ha='center', va='center', size=6)
        text_color = 'white'
        if df.diff_color.to_list()[i] == 'gold':
            text_color = 'black'
        plt.text(0.5, i, i + 1, ha='left',
                 va='center', size=7, color=text_color)

    if save:
        plt.savefig(
            'figures/difficulty_barplots/{}.svg'.format(file_name), format='svg')
    plt.draw()
    df['ease_color'] = [helper.set_color(x/100) for x in df['ease']]
    df['ease'] = 30 - df['ease']
    df = df.sort_values(by='ease', ascending=True)
    plt.figure(figsize=(8, (len(df['ease'])*.13) + 1.5))
    plt.barh(df['mountain'], df['ease'], color=df['ease_color'])
    plt.title(f'{name} Beginner Friendliness', fontsize=20)
    plt.xlabel('Longer bar = more beginner friendly')
    plt.xlim(0, 30)
    plt.tight_layout()
    plt.grid(axis='x')
    row_count = len(df.ease)
    for i, value in enumerate(df.ease):
        plt.text(value+.5, i, round(value, 1),
                 ha='center', va='center', size=6)
        plt.text(0.25, i, row_count - i, ha='left',
                 va='center', size=7, color='white')

    if save:
        plt.savefig(
            'figures/beginner_friendliness_barplots/{}.svg'.format(file_name), format='svg')
        print(f'{file_name} SVG saved')
    plt.draw()
