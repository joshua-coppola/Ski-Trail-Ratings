import csv
import pandas as pd
import matplotlib.pyplot as plt

import loadData

def gpx():
    filename = 'gpx/big-bang-409529.gpx'
    #filename = 'gpx/rimrock-415690.gpx'
    #filename = 'gpx/tuckered-out.gpx'
    loadData.runGPX(filename)

def osm():
    mountain = "cannon"
    cardinal_direction = 'n'
    difficulty_modifiers = True
    save_map = False
    
    loadData.runOSM(mountain, difficulty_modifiers, cardinal_direction, save_map)

def bulk_osm(input_csv):
    difficulty_modifiers = True
    save_map = True
    mountain = []
    mountain_difficulty = []
    mountain_difficulty_color = []
    mountain_ease = []
    mountain_ease_color = []
    with open(input_csv, mode='r') as file:
        csv_file = csv.reader(file)
        next(csv_file)
        for line in csv_file:
            print('\nProcessing {}'.format(line[0]))
            diff_tuple = loadData.runOSM(line[0], difficulty_modifiers, line[1], save_map)
            if diff_tuple == -1:
                continue
            mountain_list = line[0].split('_')
            mountain_name = ''
            for word in mountain_list:
                mountain_name = mountain_name + ('{} '.format(word.capitalize()))
            mountain.append(mountain_name)
            mountain_difficulty.append(diff_tuple[0][0])
            mountain_difficulty_color.append(diff_tuple[0][1])
            mountain_ease.append(diff_tuple[1][0])
            mountain_ease_color.append(diff_tuple[1][1])
    df_difficulty = pd.DataFrame()
    df_difficulty['mountain'] = mountain
    df_difficulty['rating'] = mountain_difficulty
    df_difficulty['color'] = mountain_difficulty_color
    df_ease = pd.DataFrame()
    df_ease['mountain'] = mountain
    df_ease['rating'] = mountain_ease
    df_ease['color'] = mountain_ease_color
    df_difficulty = df_difficulty.sort_values(by='rating', ascending=False)
    df_ease = df_ease.sort_values(by='rating', ascending=False)
    print(df_difficulty)
    print(df_ease)
    plt.barh(df_difficulty['mountain'], df_difficulty['rating'], color=df_difficulty['color'])
    plt.title('Difficulty Comparison')
    plt.xlabel('Higher is harder advanced terrain')
    plt.subplots_adjust(left=0.25, bottom=.1, right=.95,
                            top=.9, wspace=0, hspace=0)
    plt.grid(axis='x')
    plt.show()
    plt.barh(df_ease['mountain'], df_ease['rating'], color=df_ease['color'])
    plt.title('Beginner Friendliness')
    plt.xlabel('Lower is easier beginner terrain')
    plt.subplots_adjust(left=0.25, bottom=.1, right=.95,
                            top=.9, wspace=0, hspace=0)
    plt.grid(axis='x')
    plt.show()

bulk_osm('mountain_list.csv')
#osm()
