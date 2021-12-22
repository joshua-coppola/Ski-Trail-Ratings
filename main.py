import pandas as pd
from pandas.core.arrays.categorical import contains

raw_table = pd.read_csv('rimrock-415690.gpx').to_numpy()

df = pd.DataFrame()
lat = []
lon = []
elevation = []
for row in raw_table:
    row = str(row)
    if 'trkpt lat' in row:
        split_row = row.split('"')
        lat.append(float(split_row[1]))
        lon.append(float(split_row[3]))
    if 'ele' in row:
        elevation.append(float(row.split('>')[1].split('<')[0]))
df['lat'] = lat
df['lon'] = lon
df['elevation'] = elevation

print(df)