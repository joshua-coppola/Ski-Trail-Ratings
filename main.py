import csv
from genericpath import exists
import pandas as pd
import matplotlib.pyplot as plt
import sys, getopt

import loadData
import saveData

def gpx(filename):
    #filename = 'gpx/big-bang-409529.gpx'
    #filename = 'gpx/rimrock-415690.gpx'
    #filename = 'gpx/tuckered-out.gpx'
    loadData.runGPX(filename)

def osm(mountain='', direction='n', save_map=False):
    print('\nProcessing {}'.format(mountain))
    diff_tuple = loadData.runOSM(mountain, direction, save_map)
    if diff_tuple == -1:
        return -1
    if save_map and exists('mountain_list.csv'):
        row = [[mountain, direction, diff_tuple[0], diff_tuple[1]]]
        mountains = pd.read_csv('mountain_list.csv')
        if mountain in mountains.mountain.to_list():
            mountains.loc[mountains.mountain == mountain] = row
            output = mountains
        else:
            row = pd.Series(row[0], index=mountains.columns)
            output = mountains.append(row, ignore_index=True)
            output.sort_values(by=['mountain'], inplace=True)
        output.to_csv('mountain_list.csv', index=False)
    else:
        print('Mountain data not saved. If this is unexpected, please make sure you have a file called mountain_list.csv')
    plt.show()

def bulk_osm(input_csv, save_map = False):
    with open(input_csv, mode='r') as file:
        csv_file = csv.reader(file)
        next(csv_file)
        for line in csv_file:
            osm(line[0], line[1], save_map)
            

def barplot(save):
    if not exists('mountain_list.csv'):
        print('Missing cache files, please run bulk_osm or osm and set save_map=True.')
        return
    df = pd.read_csv('mountain_list.csv')
    saveData.create_difficulty_barplot(df, save)


def main(argv):
    file = ''
    save_flag = False
    osm_flag = False
    csv_flag = False
    gpx_flag = False
    bar_flag = False
    direction = ''
    try:
        opts, args = getopt.getopt(argv,"hbso:g:c:d:",["osm=","gpx=","csv=", "direction="])
    except getopt.GetoptError:
        print('main.py -[o,g,c] <inputfile> -s')
        print('main.py -[o,g,c] <inputfile>')
        print('main.py -b -s')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('main.py -[o,g,c] <inputfile> -s')
            print('main.py -[o,g,c] <inputfile>')
            print('main.py -b')
            sys.exit()
        elif opt in ("-o", "--osm"):
            file = arg
            osm_flag = True
            print()
        elif opt in ("-g", "--gpx"):
            file = arg
            gpx_flag = True
        elif opt in ("-c", "--csv"):
            file = arg
            csv_flag = True
        elif opt in ("-d", "--direction"):
            direction = arg
        elif opt in ("-b"):
            bar_flag = True
        elif opt in ("-s"):
            save_flag = True
    
    if csv_flag:
        bulk_osm(file, save_flag)
    elif osm_flag:
        osm(file, direction, save_flag)
    elif gpx_flag:
        gpx(file)
    if bar_flag:
        barplot(save_flag)

if __name__ == "__main__":
    main(sys.argv[1:])