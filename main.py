import csv
from genericpath import exists
import pandas as pd
import matplotlib.pyplot as plt

import loadData
import saveData

def gpx():
    filename = 'gpx/big-bang-409529.gpx'
    #filename = 'gpx/rimrock-415690.gpx'
    #filename = 'gpx/tuckered-out.gpx'
    loadData.runGPX(filename)

def osm():
    mountain = "palisades_tahoe_alpine"
    cardinal_direction = 'n'
    save_map = True
    
    loadData.runOSM(mountain, cardinal_direction, save_map)
    plt.show()

def bulk_osm(input_csv, save_map = False):
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
            diff_tuple = loadData.runOSM(line[0], line[1], save_map)
            if diff_tuple == -1:
                continue
            mountain_list = line[0].split('_')
            mountain_name = ''
            for word in mountain_list:
                mountain_name = mountain_name + ('{} '.format(word.capitalize()))
            mountain.append(mountain_name.strip())
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
    saveData.create_difficulty_barplot(df_difficulty, df_ease, save_map)

def osm_standalone_barplot(save):
    if not exists('cached/mountain_difficulty') or not exists('cached/mountain_ease'):
        print('Missing cache files, please run bulk_osm with save=True to create them.')
        return
    df_difficulty = pd.read_csv('cached/mountain_difficulty.csv')
    df_ease = pd.read_csv('cached/mountain_ease.csv')
    saveData.create_difficulty_barplot(df_difficulty, df_ease, save)

#bulk_osm('mountain_list.csv', True, True)
#osm_standalone_barplot(True)
osm()
