import matplotlib.pyplot as plt

import loadData
import saveData
import helper

def main():
    # df = load_gpx('rimrock-415690.gpx')[0]
    # df = load_gpx('tuckered-out.gpx')[0]
    df = loadData.load_gpx('gpx/big-bang-409529.gpx')[0]
    df = helper.fill_in_point_gaps(df)
    df['elevation'] = helper.smooth_elevations(df['elevation'].to_list())
    df['distance'] = helper.calculate_dist(df['coordinates'])
    df['elevation_change'] = helper.calulate_elevation_change(df['elevation'])
    df['slope'] = helper.calculate_slope(df['elevation_change'], df['distance'])
    df['difficulty'] = helper.calculate_point_difficulty(df['slope'].to_list())
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


def main2():
    difficulty_modifiers = True
    mountain = "crested_butte"
    trail_list = loadData.load_osm(mountain + '.osm', True, mountain + '.csv')
    if trail_list == -1:
        return
    finished_trail_list = []
    saveData.cache_elevation(mountain + '.csv', trail_list)
    for entry in trail_list:
        trail = entry[0]
        trail['elevation'] = helper.smooth_elevations(
            trail['elevation'].to_list(), 1)
        trail['distance'] = helper.calculate_dist(trail['coordinates'])
        trail['elevation_change'] = helper.calulate_elevation_change(
            trail['elevation'])
        trail['slope'] = helper.calculate_slope(
            trail['elevation_change'], trail['distance'])
        trail['difficulty'] = helper.calculate_point_difficulty(trail['slope'])
        finished_trail_list.append((trail, entry[1], entry[2]))
    #create_map(finished_trail_list, mountain, difficulty_modifiers, 1, -1, False, False)
    # ^^west facing
    # okemo, killington, stowe, bristol
    # create_map(finished_trail_list, mountain, difficulty_modifiers, -1, 1)
    # ^^east facing
    #create_map(finished_trail_list, mountain, difficulty_modifiers, 1, 1, True, True)
    # ^^south facing
    # bromley
    saveData.create_map(finished_trail_list, mountain, difficulty_modifiers, -1, -1, True, True)
    # ^^north facing
    # cannon, holiday_valley, sunday_river, purgatory, pat's_peak, jay_peak, crested_butte


main2()
