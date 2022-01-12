from math import atan2, degrees
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
    output_df.to_csv('cached/{}'.format(filename))

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
    rating_list = []
    for entry in lifts:
        lift_name = entry[1]
        if '_' in lift_name:
            lift_name = lift_name.split('_')[0]
        midpoint = int(len(entry[0].lat.to_list())/2)
        if midpoint <= 2:
            dx = 0
            dy = 0
        if midpoint > 2:    
            dx = (entry[0].lat.to_list()[midpoint]) - \
                (entry[0].lat.to_list()[midpoint+2])
            dy = (entry[0].lon.to_list()[midpoint])- \
                (entry[0].lon.to_list()[midpoint+2])
        if not flip_lat_lon:
            ang = degrees(atan2(dx, dy)) - 90
            if ang < -90:
                ang += 180
            plt.plot(entry[0].lat * lat_mirror,
                    entry[0].lon * lon_mirror, c='grey')
            if helper.get_trail_length(entry[0].coordinates) > 200:
                plt.text((entry[0].lat.to_list()[midpoint]) * lat_mirror,
                        (entry[0].lon.to_list()[midpoint]) * lon_mirror, lift_name, 
                        {'color': 'grey', 'size': 2, 'rotation': ang}, ha='center', 
                        backgroundcolor='white', bbox=dict(boxstyle='square,pad=0.01', 
                        fc='white', ec='none'))
        if flip_lat_lon:
            ang = degrees(atan2(dx, dy))
            if ang < -90:
                ang -= 180
            if ang > 90:
                ang -= 180
            plt.plot(entry[0].lon * lon_mirror,
                    entry[0].lat * lat_mirror, c='grey')
            if helper.get_trail_length(entry[0].coordinates) > 200:
                plt.text((entry[0].lon.to_list()[midpoint]) * lon_mirror,
                        (entry[0].lat.to_list()[midpoint]) * lat_mirror, lift_name, 
                        {'color': 'grey', 'size': 2, 'rotation': ang}, ha='center', 
                        backgroundcolor='white', bbox=dict(boxstyle='square,pad=0.01', 
                        fc='white', ec='none'))
            
        
    for entry in trails:
        rating = helper.rate_trail(entry[0]['difficulty'])
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
        midpoint = int(len(entry[0].lat.to_list())/2)
        if midpoint <= 2:
            dx = 0
            dy = 0
        if midpoint > 2:    
            dx = (entry[0].lat.to_list()[midpoint]) - \
                (entry[0].lat.to_list()[midpoint+2])
            dy = (entry[0].lon.to_list()[midpoint])- \
                (entry[0].lon.to_list()[midpoint+2])
        if not flip_lat_lon:
            ang = degrees(atan2(dx, dy)) - 90
            if ang < -90:
                ang += 180
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
                     backgroundcolor='white', bbox=dict(boxstyle='square,pad=0.01', 
                     fc='white', ec='none'))
        if flip_lat_lon:
            ang = degrees(atan2(dx, dy))
            if ang < -90:
                ang -= 180
            if ang > 90:
                ang -= 180
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
                     backgroundcolor='white', bbox=dict(boxstyle='square,pad=0.01', 
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
    top5_median = pd.Series(rating_list).sort_values(ascending=False).head().median()
    top20_median = pd.Series(rating_list).sort_values(ascending=False).head(20).median()
    mountain_difficulty_rating = (top5_median + top20_median) / 2
    mountain_difficulty_rating = (mountain_difficulty_rating, helper.set_color(mountain_difficulty_rating/100))
    print('Difficultly Rating:')
    print(mountain_difficulty_rating)
    bottom5_median = pd.Series(rating_list).sort_values().head().median()
    bottom20_median = pd.Series(rating_list).sort_values().head(20).median()
    mountain_ease_rating = (bottom5_median + bottom20_median) / 2
    mountain_ease_rating = (mountain_ease_rating, helper.set_color(mountain_ease_rating/100))
    print('Beginner Friendliness Rating:')
    print(mountain_ease_rating)
    plt.show()
    return((mountain_difficulty_rating, mountain_ease_rating))