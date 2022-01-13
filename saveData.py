from math import atan2, degrees, sqrt
import matplotlib.pyplot as plt
import pandas as pd
from os.path import exists
from decimal import Decimal

import helper

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

# accepts a list of trails and saves the latitude, longitude, and elevation
# to a csv as a cache


def cache_elevation(filename, list_dfs):
    if exists('cached/{}'.format(filename)):
        return
    output_df = pd.DataFrame(columns=['coordinates', 'elevation'])
    for entry in list_dfs:
        trail = entry[0][['coordinates', 'elevation']]
        output_df = output_df.append(trail)
    output_df.to_csv('cached/{}'.format(filename), index=False)

# accepts a list of trail tuples, the name of the ski area, a boolean for
# whether to use difficulty modifiers, and a pair of ints (plus a bool) to
# rotate the map. Their values should be -1 or 1 and T/F for the bool. The
# last param is a bool for whether to save the map.
#
# Return: the relative difficulty of hard terrain and the relative ease 
# for beginner terrain
#   type-tuple of tuples


def create_map(trails, lifts, mountain, difficulty_modifiers, lat_mirror=1, lon_mirror=1, flip_lat_lon=False, save=False):
    mountain_max_lat = 0
    mountain_min_lat = 90
    mountain_max_lon = 0
    mountain_min_lon = 180
    for entry in trails:
        trail_max_lat = abs(entry[0]['lat']).max()
        trail_min_lat = abs(entry[0]['lat']).min()
        if trail_max_lat > mountain_max_lat:
            mountain_max_lat = trail_max_lat
        if trail_min_lat < mountain_min_lat:
            mountain_min_lat = trail_min_lat
        trail_max_lon = abs(entry[0]['lon']).max()
        trail_min_lon = abs(entry[0]['lon']).min()
        if trail_max_lon > mountain_max_lon:
            mountain_max_lon = trail_max_lon
        if trail_min_lon < mountain_min_lon:
            mountain_min_lon = trail_min_lon
    top_corner = (mountain_max_lat, mountain_max_lon)
    bottom_corner = (mountain_min_lat, mountain_max_lon)
    bottom_corner_alt = (mountain_min_lat, mountain_min_lon)
    n_s_length = helper.calculate_dist([top_corner, bottom_corner])[1] / 1000
    e_w_length = helper.calculate_dist([bottom_corner, bottom_corner_alt])[1] / 1000
    if flip_lat_lon:
        temp = n_s_length
        n_s_length = e_w_length
        e_w_length = temp
    print((n_s_length, e_w_length))

    plt.figure(figsize=(n_s_length*2, e_w_length*2))
    for entry in lifts:
        lift_name = entry[1]
        if '_' in lift_name:
            lift_name = lift_name.split('_')[0]
        midpoint, ang = helper.get_label_placement(entry[0][['lat','lon','coordinates']], len(lift_name), flip_lat_lon)
        if not flip_lat_lon:
            plt.plot(entry[0].lat * lat_mirror,
                    entry[0].lon * lon_mirror, c='grey')
            if helper.get_trail_length(entry[0].coordinates) > 200:
                plt.text((entry[0].lat.to_list()[midpoint]) * lat_mirror,
                        (entry[0].lon.to_list()[midpoint]) * lon_mirror, lift_name, 
                        {'color': 'grey', 'size': 2, 'rotation': ang}, ha='center', 
                        backgroundcolor='white', va='center', bbox=dict(boxstyle='square,pad=0.01', 
                        fc='white', ec='none'))
        if flip_lat_lon:
            plt.plot(entry[0].lon * lon_mirror,
                    entry[0].lat * lat_mirror, c='grey')
            if helper.get_trail_length(entry[0].coordinates) > 200:
                plt.text((entry[0].lon.to_list()[midpoint]) * lon_mirror,
                        (entry[0].lat.to_list()[midpoint]) * lat_mirror, lift_name, 
                        {'color': 'grey', 'size': 2, 'rotation': ang}, ha='center', 
                        backgroundcolor='white', va='center', bbox=dict(boxstyle='square,pad=0.01', 
                        fc='white', ec='none'))
            
    rating_list = []    
    for entry in trails:
        rating = helper.rate_trail(entry[0]['difficulty'])
        if helper.get_trail_length(entry[0].coordinates) > 200:
            rating_list.append(round((rating * 100), 0))
        if difficulty_modifiers:
            color = helper.set_color(rating, entry[2])
        else:
            color = helper.set_color(rating)
        rating = round(Decimal(rating) * 100, 1)
        trail_name = entry[1]
        if '_' in trail_name:
            trail_name = trail_name.split('_')[0]

        trail_name = '{} {}{}'.format(trail_name, rating, u'\N{DEGREE SIGN}')
        midpoint, ang = helper.get_label_placement(entry[0][['lat', 'lon', 'coordinates']], len(trail_name), flip_lat_lon)
        print((trail_name, midpoint, ang))
        if not flip_lat_lon:
            if entry[2] == 0:
                plt.plot(entry[0].lat * lat_mirror,
                         entry[0].lon * lon_mirror, c=color)
            if entry[2] > 0:
                plt.plot(entry[0].lat * lat_mirror, entry[0].lon *
                         lon_mirror, c=color, linestyle='dashed')
            if helper.get_trail_length(entry[0].coordinates) > 200:
                plt.text((entry[0].lat.to_list()[midpoint]) * lat_mirror,
                     (entry[0].lon.to_list()[midpoint]) * lon_mirror, trail_name, 
                     {'color': color, 'size': 2, 'rotation': ang}, ha='center', 
                     backgroundcolor='white', va='center', bbox=dict(boxstyle='square,pad=0.01', 
                     fc='white', ec='none'))
        if flip_lat_lon:
            if entry[2] == 0:
                plt.plot(entry[0].lon * lon_mirror,
                         entry[0].lat * lat_mirror, c=color)
            if entry[2] > 0:
                plt.plot(entry[0].lon * lon_mirror, entry[0].lat *
                         lat_mirror, c=color, linestyle='dashed')
            if helper.get_trail_length(entry[0].coordinates) > 200:
                plt.text((entry[0].lon.to_list()[midpoint]) * lon_mirror,
                     (entry[0].lat.to_list()[midpoint]) * lat_mirror, trail_name, 
                     {'color': color, 'size': 2, 'rotation': ang}, ha='center', 
                     backgroundcolor='white', va='center', bbox=dict(boxstyle='square,pad=0.01', 
                     fc='white', ec='none'))
    plt.xticks([])
    plt.yticks([])
    if mountain != '':
        mountain_list = mountain.split('_')
        mountain = ''
        for word in mountain_list:
            mountain = mountain + ('{} '.format(word.capitalize()))
        size = int(e_w_length*10)
        if size > 25:
            size = 25
        if size < 5:
            size = 5
        plt.title(mountain, fontsize=size)
        if e_w_length < 1.5:
            top = .88
        if e_w_length >= 1.5:
            top = .92
        if e_w_length < 1:
            top = .80
        plt.subplots_adjust(left=0.05, bottom=.02, right=.95,
                            top=top, wspace=0, hspace=0)
    else:
        plt.subplots_adjust(left=0, bottom=0, right=1,
                            top=1, wspace=0, hspace=0)
    if save:
        plt.savefig('maps/{}.svg'.format(mountain.strip()), format='svg')
        print('SVG saved')
    rating_list = [x**2 for x in rating_list]
    rating_list.sort(reverse=True)
    hard_list = [rating_list[0:15], rating_list[0:5]]
    mountain_difficulty_rating = (sqrt(sum(hard_list[0])/15) + sqrt(sum(hard_list[1])/5) + sqrt(hard_list[0][0])) / 3
    mountain_difficulty_rating = (round(mountain_difficulty_rating, 1), helper.set_color(mountain_difficulty_rating/100))
    print('Difficultly Rating:')
    print(mountain_difficulty_rating)
    rating_list.sort()
    easy_list = [rating_list[0:15], rating_list[0:5]]
    mountain_ease_rating = (sqrt(sum(easy_list[0])/15) + sqrt(sum(easy_list[1])/5) + sqrt(easy_list[0][0])) / 3
    mountain_ease_rating = (round(mountain_ease_rating, 1), helper.set_color(mountain_ease_rating/100))

    print('Beginner Friendliness Rating:')
    print(mountain_ease_rating)
    plt.show()
    print()
    return((mountain_difficulty_rating, mountain_ease_rating))

# Parameters:
# df_difficulty: dataframe with column for mountain name, difficulty rating, and color
#   type-df(string, float, string)
# df_ease: dataframe with column for mountain name, beginner friendliness rating, and color
#   type-df(string, float, string)
# save: bool for whether to save the output to an svg
#   type-bool
# Return: none

def create_difficulty_barplot(df_difficulty, df_ease, save=False):
    df_difficulty = df_difficulty.sort_values(by='rating', ascending=False)
    df_ease['rating'] = 20 - df_ease['rating'] 
    df_ease = df_ease.sort_values(by='rating', ascending=True)
    plt.barh(df_difficulty['mountain'], df_difficulty['rating'], color=df_difficulty['color'])
    plt.title('Difficulty Comparison')
    plt.xlabel('Longer bar = more expert friendly')
    plt.subplots_adjust(left=0.25, bottom=.1, right=.95,
                            top=.9, wspace=0, hspace=0)
    plt.grid(axis='x')
    if save:
        plt.savefig('maps/comparative_difficulty.svg', format='svg')
        print('SVG saved')
        df_difficulty.to_csv('cached/mountain_difficulty', index=False)
    plt.show()
    plt.barh(df_ease['mountain'], df_ease['rating'], color=df_ease['color'])
    plt.title('Beginner Friendliness')
    plt.xlabel('Longer bar = more beginner friendly')
    plt.subplots_adjust(left=0.25, bottom=.1, right=.95,
                            top=.9, wspace=0, hspace=0)
    plt.grid(axis='x')
    if save:
        plt.savefig('maps/beginner_friendliness.svg', format='svg')
        print('SVG saved')
        df_ease['rating'] = 20 - df_ease['rating']
        df_ease.to_csv('cached/mountain_ease', index=False)
    plt.show()
