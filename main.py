import matplotlib.pyplot as plt
import sys
import getopt

import loadData
import gpx


def main(argv):
    file = ''
    save_flag = False
    osm_flag = False
    csv_flag = False
    gpx_flag = False
    bar_flag = False
    osm_fetch = False
    blacklist = ''
    location = ''
    direction = ''
    try:
        opts, args = getopt.getopt(argv, "hbso:g:d:ci:l:f:", [
                                   "osm=", "csv", "gpx=", "ignore=", "location=", "fetch-files"])
    except getopt.GetoptError:
        print(
            'main.py -o <inputfile> -d <direction> -i <blacklisted_mountain> -l <state> -s')
        print('main.py -g <inputfile>')
        print('main.py -c -s')
        print('main.py -b -s')
        print('main.py -f <filename>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(
                'main.py -o <inputfile> -d <direction> -i <blacklisted_mountain> -l <state> -s')
            print('main.py -g <inputfile>')
            print('main.py -c -s')
            print('main.py -b -s')
            print('main.py -f <filename>')
            sys.exit()
        elif opt in ("-o", "--osm"):
            file = arg
            osm_flag = True
        elif opt in ("-g", "--gpx"):
            file = arg
            gpx_flag = True
        elif opt in ("-d"):
            direction = arg
        elif opt in ("-c", "--csv"):
            csv_flag = True
        elif opt in ("-i", "--ignore"):
            blacklist = arg
        elif opt in ("-l", "--location"):
            location = arg
        elif opt in ("-b"):
            bar_flag = True
        elif opt in ("-s"):
            save_flag = True
        elif opt in ("-f", "--fetch-files"):
            file = arg
            osm_fetch = True

    show_map = True
    if osm_fetch:
        loadData.create_osm(file)
    if csv_flag:
        loadData.bulk_osm()
        show_map = False
    elif osm_flag:
        loadData.osm(file, direction, save_flag, blacklist, location)
    elif gpx_flag:
        gpx.gpx(file)
    if bar_flag:
        loadData.barplot(save_flag)
        show_map = False
    return show_map


if __name__ == "__main__":
    show_map = main(sys.argv[1:])
    if show_map:
        plt.show()
