from math import sqrt
import matplotlib.pyplot as plt
import pandas as pd
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
    output_df = pd.DataFrame(columns=['coordinates', 'elevation'])
    output_df.drop_duplicates(inplace=True)
    for entry in list_dfs:
        trail = entry[0][['coordinates', 'elevation']]
        output_df = output_df.append(trail)
        if entry[3]:
            trail = entry[4][['coordinates', 'elevation']]
            output_df = output_df.append(trail)
    output_df.to_csv('cached/elevation/{}'.format(filename), index=False)

# Parameters:
# tuple_list: list of trail names and osm ids
#   type-list of tuples
# mountain_name: name of ski area
#   type-string
# 
# Return: none

def save_trail_ids(tuple_list, mountain_name):
    name_list = [x[0] for x in tuple_list]
    id_list = [x[1] for x in tuple_list]
    export_df = pd.DataFrame()
    export_df['name'] = name_list
    export_df['id'] = id_list
    export_df.to_csv('cached/osm_ids/{}'.format(mountain_name), index=False)


# accepts a list of trail tuples, a list of lift tuples, the name of the ski area,
# and the direction the map should face. The last param is a bool for whether to
# save the map.
#
# Return: the relative difficulty of hard terrain and the relative ease
# for beginner terrain
#   type-tuple(float,float)


def create_map(trails, lifts, mountain, cardinal_direction, save=False):
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
    e_w_length = helper.calculate_dist(
        [bottom_corner, bottom_corner_alt])[1] / 1000
    if 's' in cardinal_direction or 'n' in cardinal_direction:
        temp = n_s_length
        n_s_length = e_w_length
        e_w_length = temp
    #print((n_s_length, e_w_length))
    print('Creating Map')

    plt.figure(figsize=(n_s_length*2, e_w_length*2))
    for entry in lifts:
        lift_name = entry[1]
        if '_' in lift_name:
            lift_name = lift_name.split('_')[0]
        helper.place_object((entry[0], lift_name, 0, 0), cardinal_direction, 'grey')

    rating_list = []
    for entry in trails:
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
        helper.place_object((entry[0], trail_name, entry[2], entry[3], entry[4]), cardinal_direction, color)
        
    plt.xticks([])
    plt.yticks([])
    if mountain != '':
        mountain = helper.format_name(mountain)
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
    #rating_list = [x**2 for x in rating_list]
    rating_list.sort(reverse=True)
    long_list = 30
    if len(rating_list) < 30:
        long_list = 30
    hard_list = [rating_list[0:long_list], rating_list[0:5]]
    mountain_difficulty_rating = (sum(hard_list[0])/long_list + sum(hard_list[1])/5 + hard_list[0][0]) / 3
    mountain_difficulty_rating = round(mountain_difficulty_rating, 1)
    print('Difficultly Rating:')
    print(mountain_difficulty_rating)
    rating_list.sort()
    easy_list = [rating_list[0:long_list], rating_list[0:5]]
    mountain_ease_rating = (sum(easy_list[0])/long_list + sum(easy_list[1])/5 + easy_list[0][0]) / 3
    mountain_ease_rating = round(mountain_ease_rating, 1)

    print('Beginner Friendliness Rating:')
    print(mountain_ease_rating)
    plt.draw()
    return((mountain_difficulty_rating, mountain_ease_rating))

# Parameters:
# df_difficulty: dataframe with column for mountain name, difficulty rating, and color
#   type-df(string, float, string)
# df_ease: dataframe with column for mountain name, beginner friendliness rating, and color
#   type-df(string, float, string)
# save: bool for whether to save the output to an svg
#   type-bool
# Return: none


def create_difficulty_barplot(df, save=False):
    df['mountain'] = [helper.format_name(x) for x in df['mountain']]
    df = df.sort_values(by='difficulty', ascending=False)
    df['diff_color'] = [helper.set_color(x/100) for x in df['difficulty']]
    plt.figure(figsize=(8,len(df['difficulty'])*.2))
    plt.barh(df['mountain'], df['difficulty'], color=df['diff_color'])
    plt.title('Difficulty Comparison')
    plt.xlabel('Longer bar = more expert friendly')
    plt.subplots_adjust(left=0.25, bottom=.1, right=.95,
                        top=.9, wspace=0, hspace=0)
    plt.grid(axis='x')
    if save:
        plt.savefig('maps/comparative_difficulty.svg', format='svg')
        print('SVG saved')
    plt.draw()
    df['ease_color'] = [helper.set_color(x/100) for x in df['ease']]
    df['ease'] = 20 - df['ease']
    df = df.sort_values(by='ease', ascending=True)
    plt.figure(figsize=(8,len(df['ease'])*.2))
    plt.barh(df['mountain'], df['ease'], color=df['ease_color'])
    plt.title('Beginner Friendliness')
    plt.xlabel('Longer bar = more beginner friendly')
    plt.subplots_adjust(left=0.25, bottom=.1, right=.95,
                        top=.9, wspace=0, hspace=0)
    plt.grid(axis='x')
    if save:
        plt.savefig('maps/beginner_friendliness.svg', format='svg')
        print('SVG saved')
    plt.draw()
    plt.show()
