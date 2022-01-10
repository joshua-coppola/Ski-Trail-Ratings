from math import atan2, degrees
import matplotlib.pyplot as plt
import pandas as pd
from os.path import exists

import helper

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


def create_map(trails, mountain, difficulty_modifiers, lat_mirror=1, lon_mirror=1, flip_lat_lon=False, save=False):
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

    plt.figure(figsize=(n_s_length*2, e_w_length*2))
    for entry in trails:
        rating = helper.rate_trail(entry[0]['difficulty'])
        if difficulty_modifiers:
            color = helper.set_color(rating, entry[2])
        else:
            color = helper.set_color(rating)
        trail_name = entry[1]
        if '_' in trail_name:
            trail_name = trail_name.split('_')[0]
        midpoint = int(len(entry[0].lat.to_list())/2)
        if midpoint < 2:
            dx = 0
            dy = 0
        if midpoint >= 2:    
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
        plt.title(mountain)
        plt.subplots_adjust(left=0.05, bottom=.02, right=.95,
                            top=.92, wspace=0, hspace=0)
    else:
        plt.subplots_adjust(left=0, bottom=0, right=1,
                            top=1, wspace=0, hspace=0)
    if save:
        plt.savefig('maps/{}.svg'.format(mountain.strip()), format='svg')
        print('SVG saved')
    plt.show()
    