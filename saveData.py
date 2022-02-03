from decimal import Decimal
import matplotlib.pyplot as plt
import pandas as pd
from tqdm import tqdm

import helper
import mapHelper


def create_gpx_map(df):
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

# Parameters:
# filename: name of csv to save data to
#   type-string
# list_df: list of trails
#   type-list of tuples
# 
# Return: none


def cache_trail_points(filename, list_dfs):
    output_df = pd.DataFrame(columns=['trail_id','for_display','lat','lon','elevation'])
    for entry in list_dfs:
        trail = pd.DataFrame()
        trail['trail_id'] = entry[5]
        trail['for_display'] = True
        trail['lat'] = entry[0].lat
        trail['lon'] = entry[0].lon
        trail['elevation'] = entry[0]['elevation']
        trail['slope'] = entry[0].slope
        trail['trail_id'] = entry[5]
        trail['for_display'] = True
        output_df = output_df.append(trail)
        if entry[3]:
            trail = pd.DataFrame()
            trail['trail_id'] = entry[5]
            trail['for_display'] = False
            trail['lat'] = entry[4].lat
            trail['lon'] = entry[4].lon
            trail['elevation'] = entry[4]['elevation']
            trail['slope'] = entry[4].slope
            trail['trail_id'] = entry[5]
            trail['for_display'] = False
            output_df = output_df.append(trail)
    output_df['lat'] = [round(x, 8) for x in output_df.lat]
    output_df['lon'] = [round(x, 8) for x in output_df.lon]
    output_df['elevation'] = [round(Decimal(x), 2) for x in output_df.elevation]
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
    mapHelper.format_map_template(trails, mountain, cardinal_direction)
    for i in tqdm (range (len(lifts)), desc="Placing Lifts …", ascii=False, ncols=75):
        entry = lifts[i]
        lift_name = entry[1]
        if '_' in lift_name:
            lift_name = lift_name.split('_')[0]
        mapHelper.place_object((entry[0], lift_name, 0, 0), cardinal_direction, 'grey')

    rating_list = []
    for i in tqdm (range (len(trails)), desc="Placing Trails…", ascii=False, ncols=75):
        entry = trails[i]
        if not entry[3]:
            index = 0
        else:
            index = 4
        rating = helper.rate_trail(entry[index]['difficulty'])
        if helper.get_trail_length(entry[index].coordinates) > 100:
            rating_list.append(round((rating * 100), 0))
        color = helper.set_color(rating, entry[2])
        rating = round(rating * 100, 1)
        trail_name = entry[1]
        if '_' in trail_name:
            trail_name = trail_name.split('_')[0]

        trail_name = '{} {}{}'.format(
            trail_name.strip(), rating, u'\N{DEGREE SIGN}')
        mapHelper.place_object((entry[0], trail_name, entry[2], entry[3], entry[4]), cardinal_direction, color)
        
    plt.xticks([])
    plt.yticks([])
    if save:
        plt.savefig('maps/{}.svg'.format(helper.format_name(mountain)), format='svg')
        print('SVG saved')
    rating_list.sort(reverse=True)
    long_list = 30
    if len(rating_list) < 30:
        long_list = len(rating_list)
    hard_list = [rating_list[0:long_list], rating_list[0:5]]
    mountain_difficulty_rating = ((sum(hard_list[0])/long_list) * .2) + ((sum(hard_list[1])/5) * .8)
    mountain_difficulty_rating = round(mountain_difficulty_rating, 1)
    print('Difficultly Rating: {}'.format(mountain_difficulty_rating))
    rating_list.sort()
    easy_list = [rating_list[0:long_list], rating_list[0:5]]
    mountain_ease_rating = ((sum(easy_list[0])/long_list) * .2) + ((sum(easy_list[1])/5) * .8)
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


def create_difficulty_barplot(df, save=False):
    df['mountain'] = [helper.format_name(x) for x in df['mountain']]
    df = df.sort_values(by='difficulty', ascending=False)
    df['diff_color'] = [helper.set_color(x/100) for x in df['difficulty']]
    plt.figure(figsize=(8,len(df['difficulty'])*.15))
    plt.barh(df['mountain'], df['difficulty'], color=df['diff_color'])
    plt.title('Difficulty Comparison')
    plt.xlabel('Longer bar = more expert friendly')
    plt.subplots_adjust(left=0.25, bottom=.03, right=.95,
                        top=.97, wspace=0, hspace=0)
    plt.grid(axis='x')
    if save:
        plt.savefig('maps/comparative_difficulty.svg', format='svg')
        print('SVG saved')
    plt.draw()
    df['ease_color'] = [helper.set_color(x/100) for x in df['ease']]
    df['ease'] = 30 - df['ease']
    df = df.sort_values(by='ease', ascending=True)
    plt.figure(figsize=(8,len(df['ease'])*.15))
    plt.barh(df['mountain'], df['ease'], color=df['ease_color'])
    plt.title('Beginner Friendliness')
    plt.xlabel('Longer bar = more beginner friendly')
    plt.subplots_adjust(left=0.25, bottom=.03, right=.95,
                        top=.97, wspace=0, hspace=0)
    plt.grid(axis='x')
    if save:
        plt.savefig('maps/beginner_friendliness.svg', format='svg')
        print('SVG saved')
    plt.draw()
    plt.show()
