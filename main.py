import csv
from genericpath import exists
import pandas as pd
import matplotlib.pyplot as plt
import sys
import getopt

import loadData
import saveData
import helper


def gpx(filename):
    #filename = 'gpx/big-bang-409529.gpx'
    #filename = 'gpx/rimrock-415690.gpx'
    #filename = 'gpx/tuckered-out.gpx'
    loadData.run_gpx(filename)


def osm(mountain='', direction='', save_map=False, blacklist='', location=''):
    print('\nProcessing {}'.format(helper.format_name(mountain)))
    mountain_df = pd.read_csv('mountain_list.csv')
    previously_run = False
    if mountain in mountain_df.mountain.to_list():
        previously_run = True
        mountain_row = mountain_df.loc[mountain_df.mountain == mountain]
    if direction == '' and previously_run:
        value = mountain_row.direction.to_list()[0]
        if str(value) != 'nan':
            direction = value
    if blacklist == '' and previously_run:
        value = mountain_row.blacklist.to_list()[0]
        if str(value) != 'nan':
            blacklist = value
    if location == '' and previously_run:
        value = mountain_row.state.to_list()[0]
        if str(value) != 'nan':
            location = value
    diff_tuple = loadData.run_osm(mountain, direction, save_map, blacklist)
    if diff_tuple == -1:
        return -1
    if save_map and exists('mountain_list.csv'):
        # row = (mountain, direction, state, difficulty, ease, vert, trail_count, lift_count, blacklist)
        row = [[mountain, direction, location, diff_tuple[0], diff_tuple[1],
                diff_tuple[2], diff_tuple[3], diff_tuple[4], blacklist]]
        if previously_run:
            mountain_df.loc[mountain_df.mountain == mountain] = row
            output = mountain_df
        else:
            row = pd.Series(row[0], index=mountain_df.columns)
            output = mountain_df.append(row, ignore_index=True)
            output.sort_values(by=['mountain'], inplace=True)
        output['trail_count'] = output['trail_count'].astype(int)
        output['lift_count'] = output['lift_count'].astype(int)
        output.to_csv('mountain_list.csv', index=False)
    else:
        print('Mountain data not saved. If this is unexpected, please make sure you have a file called mountain_list.csv')


def bulk_osm(input_csv, save_map=False):
    if input_csv[:-4] != '.csv':
        input_csv = input_csv + '.csv'
    with open(input_csv, mode='r') as file:
        csv_file = csv.reader(file)
        next(csv_file)
        for line in csv_file:
            if len(line) == 0:
                break
            if line[0][0] == '#':
                continue
            osm(line[0], line[1], save_map, line[8], line[2])


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
    blacklist = ''
    location = ''
    try:
        opts, args = getopt.getopt(argv, "hbso:g:c:d:i:l:", [
                                   "osm=", "gpx=", "csv=", "direction=", "ignore=", "location="])
    except getopt.GetoptError:
        print(
            'main.py -o <inputfile> -d <direction> -i <blacklisted_mountain> -l <state> -s')
        print('main.py -g <inputfile>')
        print('main.py -c <inputfile> -s')
        print('main.py -b -s')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(
                'main.py -o <inputfile> -d <direction> -i <blacklisted_mountain> -l <state> -s')
            print('main.py -g <inputfile>')
            print('main.py -c <inputfile> -s')
            print('main.py -b -s')
            sys.exit()
        elif opt in ("-o", "--osm"):
            file = arg
            osm_flag = True
        elif opt in ("-g", "--gpx"):
            file = arg
            gpx_flag = True
        elif opt in ("-c", "--csv"):
            file = arg
            csv_flag = True
        elif opt in ("-d", "--direction"):
            direction = arg
        elif opt in ("-i", "--ignore"):
            blacklist = arg
        elif opt in ("-l", "--location"):
            location = arg
        elif opt in ("-b"):
            bar_flag = True
        elif opt in ("-s"):
            save_flag = True

    show_map = True
    if csv_flag:
        bulk_osm(file, save_flag)
        show_map = False
    elif osm_flag:
        osm(file, direction, save_flag, blacklist, location)
    elif gpx_flag:
        gpx(file)
    if bar_flag:
        barplot(save_flag)
    return show_map


if __name__ == "__main__":
    show_map = main(sys.argv[1:])
    if show_map:
        plt.show()
