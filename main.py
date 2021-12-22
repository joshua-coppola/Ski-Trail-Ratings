from numpy import NAN
import pandas as pd
import haversine as hs
import math
import matplotlib.pyplot as plt

# accepts a gpx filename and returns a dataframe
# with 2 columns: lat/lon pairs and elevation (in feet)


def load_data(filename):
    raw_table = pd.read_csv(filename).to_numpy()
    df = pd.DataFrame()
    coordinates = []
    elevation = []
    for row in raw_table:
        row = str(row)
        if 'trkpt lat' in row:
            split_row = row.split('"')
            coordinates.append((float(split_row[1]), float(split_row[3])))
        if 'ele' in row:
            elevation.append(float(row.split('>')[1].split('<')[0]))
    df['coordinates'] = coordinates
    df['elevation'] = elevation
    return df

# accepts a list of lat/lon pairs and returns a list of distances (in feet)


def calculate_dist(coordinates):
    previous_row = (NAN, NAN)
    distance = []
    for row in coordinates:
        distance.append(hs.haversine(row, previous_row, unit=hs.Unit.FEET))
        previous_row = row
    return distance

# accepts a list of elevations and returns the difference between
# neighboring elevations


def calulate_elevation_change(elevation):
    previous_row = NAN
    elevation_change = []
    for row in elevation:
        elevation_change.append(row-previous_row)
        previous_row = row
    return elevation_change

# accepts 2 lists: distance and elevation change, both using the same unit
# returns a list of slopes (in degrees)


def calculate_slope(elevation_change, distance):
    return [math.degrees(math.atan(x/y)) for x,y in zip(elevation_change, distance)]

df = load_data('rimrock-415690.gpx')
df['distance'] = calculate_dist(df['coordinates'])
df['elevation_change'] = calulate_elevation_change(df['elevation'])
df['slope'] = calculate_slope(df['elevation_change'], df['distance'])
print(df)