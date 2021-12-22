from numpy import NAN, absolute
import pandas as pd
import haversine as hs
import math
import matplotlib.pyplot as plt

# accepts a gpx filename and returns a dataframe
# with 4 columns: latitude, longitude, lat/lon pairs and elevation (in meters)


def load_data(filename):
    raw_table = pd.read_csv(filename).to_numpy()
    df = pd.DataFrame()
    lat = []
    lon = []
    coordinates = []
    elevation = []
    for row in raw_table:
        row = str(row)
        if 'trkpt lat' in row:
            split_row = row.split('"')
            lat.append(float(split_row[1]))
            lon.append(float(split_row[3]))
            coordinates.append((float(split_row[1]), float(split_row[3])))
        if 'ele' in row:
            elevation.append(float(row.split('>')[1].split('<')[0]))
    df['lat'] = lat
    df['lon'] = lon
    df['coordinates'] = coordinates
    df['elevation'] = elevation
    return df

# accepts a list of lat/lon pairs and returns a list of distances (in meters)


def calculate_dist(coordinates):
    previous_row = (NAN, NAN)
    distance = []
    for row in coordinates:
        distance.append(hs.haversine(row, previous_row, unit=hs.Unit.METERS))
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
df2 = load_data('tuckered-out.gpx')
df['distance'] = calculate_dist(df['coordinates'])
df['elevation_change'] = calulate_elevation_change(df['elevation'])
df['slope'] = calculate_slope(df['elevation_change'], df['distance'])

df2['distance'] = calculate_dist(df2['coordinates'])
df2['elevation_change'] = calulate_elevation_change(df2['elevation'])
df2['slope'] = calculate_slope(df2['elevation_change'], df2['distance'])

print(df.slope.min())
plt.plot(df.lon, df.lat, alpha=.25)
plt.scatter(df.lon, df.lat, s=8 ,c=abs(df.slope), alpha=1)
plt.plot(df2.lon, df2.lat, alpha=.25)
plt.scatter(df2.lon, df2.lat, s=8 ,c=abs(df2.slope), alpha=1)
plt.colorbar(label='Degrees', orientation='horizontal')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.xticks([])
plt.yticks([])
plt.show()