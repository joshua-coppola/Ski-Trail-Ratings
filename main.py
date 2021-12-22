from numpy import NAN
import pandas as pd
import haversine as hs

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
            coordinates.append((float(split_row[1]),float(split_row[3])))
        if 'ele' in row:
            elevation.append(float(row.split('>')[1].split('<')[0]))
    df['coordinates'] = coordinates
    df['elevation'] = elevation
    return df

#accepts a list of lat/lon pairs and returns a list of distances (in feet)
def calculate_dist(coordinates):
    previous_row = (NAN,NAN)
    distance = []
    for row in coordinates:
        distance.append(hs.haversine(row, previous_row,unit=hs.Unit.FEET))
        previous_row = row
    return distance

df = load_data('rimrock-415690.gpx')
df['distance'] = calculate_dist(df['coordinates'])
print(df)