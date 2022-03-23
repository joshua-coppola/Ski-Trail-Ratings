import imp
import time
import json
from typing import Tuple
from typing import List
from typing import Union
import pandas as pd
from numpy import NAN
import haversine as hs
from math import degrees, atan
from requests.api import get


def elevation_api(piped_coords: str, last_called: float, trailname: str = '') -> Tuple[list, float]:
    """
    Helper function for get_elevation. Accepts piped_coords, timestamp, and
    trailname and queries an elevation API to fetch elevation data at each
    point.

    #### Arguments:

    - piped_coords - string of coords separated by a |
    - last_called - time.time object for last time the API was requested
    - trailname - name of current trail

    #### Returns:

    - (elevation (list), last_called (time.time()))
    """
    # url = 'https://api.open-elevation.com/api/v1/lookup?locations={}'
    url = 'https://api.opentopodata.org/v1/ned10m?locations={}'
    # url = 'https://api.opentopodata.org/v1/mapzen?locations={}'
    if time.time() - last_called < 1:
        time.sleep(1 - (time.time() - last_called))
    last_called = time.time()
    response = get(url.format(piped_coords))
    if response.status_code == 200:
        elevation = []
        for result in json.loads(response.content)['results']:
            elevation.append(result['elevation'])
    else:
        print('Elevation API call failed on {} with code:'.format(trailname))
        print(response.status_code)
        print(response.content)
        return -1
    return (elevation, last_called)


def get_elevation(coordinates: Union[list, pd.Series], last_called: Union[float, None] = None, trail_name: str ='', api_requests: int =0):
    """
    Takes in coordinates, and optionally a timestamp, trailname, and previous API requests count
    and returns a series of elevations (float)

    #### Arguments:

    - coordinates - list of coordinates (lat,lon)
    - last called - time.time object for last API call time (default = current time)
    - trail_name - name of current trail. Used for error messages (default = '')
    - api_requests - number of API requests made by the program (default = 0)

    #### Returns:

    - tuple(elevations (series), api_requests (int), last_called (time))
    - -1 if error
    """

    if last_called == None:
        last_called = time.time()

    piped_coords = ''
    point_count = 0
    elevations = []
    for coordinate in coordinates:
        if piped_coords == '':
            piped_coords = '{},{}'.format(coordinate[0], coordinate[1])
            continue
        piped_coords = piped_coords + \
            '|{},{}'.format(coordinate[0], coordinate[1])
        point_count += 1
        if point_count >= 99:
            temp_elevations, last_called = elevation_api(
                piped_coords, last_called, trail_name)
            api_requests += 1
            if temp_elevations == -1:
                return -1
            piped_coords = ''
            point_count = 0
            for point in temp_elevations:
                elevations.append(point)
    if piped_coords != '':
        temp_elevations, last_called = elevation_api(
            piped_coords, last_called, trail_name)
        api_requests += 1
        if temp_elevations == -1:
            return -1
        for point in temp_elevations:
            elevations.append(point)
    return (pd.Series(elevations), api_requests, last_called)


def calculate_dist(coordinates: Union[list, pd.Series]) -> List[float]:
    """
    Accepts a list of coordinates and returns a list of distances between each point

    #### Arguments:

    - coordinates - list of coordinates (lat,lon)

    #### Returns:

    - distance - list of distances
    """
    previous_row = (NAN, NAN)
    distance = []
    for row in coordinates:
        distance.append(hs.haversine(row, previous_row, unit=hs.Unit.METERS))
        previous_row = row
    return distance


def fill_in_point_gaps(df: pd.DataFrame, max_gap: int = 20, elevation_included: bool = False) -> pd.DataFrame:
    """
    Accepts a dataframe with lat, lon, coordinates, and optionally elevation,
    and returns a new dataframe with each point being separated by no more
    than the max_gap (in meters).

    #### Arguments:
    - df - dataframe(lat,lon,coordinates), and optionally an elevation column
    - max_gap - maximum acceptable gap between points (in meters) (default = 20)
    - elevation_included - boolean for whether there is an elevation column in the df

    #### Returns:

    - new_df - dataframe(lat,lon,coordinates), and optionally an elevation column
    """
    lat = df['lat'].tolist()
    lon = df['lon'].tolist()
    coordinates = df['coordinates'].tolist()
    if elevation_included == True:
        elevation = df['elevation'].tolist()
    done = False
    while not done:
        distances = calculate_dist(coordinates)
        not_changed = 0
        for index, point in enumerate(distances):
            if point > max_gap and index > 0:
                new_lat = (lat[index]+lat[index-1])/2
                new_lon = (lon[index]+lon[index-1])/2
                lat.insert(index, new_lat)
                lon.insert(index, new_lon)
                coordinates.insert(index, (new_lat, new_lon))
                if elevation_included == True:
                    elevation.insert(
                        index, (elevation[index]+elevation[index-1])/2)
                break
            not_changed += 1
        if not_changed == len(coordinates):
            done = True
    new_df = pd.DataFrame()
    new_df['lat'] = lat
    new_df['lon'] = lon
    new_df['coordinates'] = coordinates
    if elevation_included == True:
        new_df['elevation'] = elevation
    return new_df


def area_to_line(df: pd.DataFrame, point_gap: int = 15) -> pd.DataFrame:
    """
    Converts the perimeter of an area into a centerline.

    #### Arguments:

    - df - dataframe(lat,lon,coordinates), the df may have additional columns
    - point_gap - set the distance between points in the centerline (default = 15)

    #### Returns:

    - new_df - dataframe(lat,lon,coordinates)
    """
    coordinates = df.coordinates.to_list()
    new_lat = []
    new_lon = []
    new_coords = []
    max_ele = (0, 0)
    min_ele = (10000, 0)
    for i, point in enumerate(df.elevation):
        if point > max_ele[0]:
            max_ele = (point, i)
        if point < min_ele[0]:
            min_ele = (point, i)
    center_lat = df.lat.mean()
    center_lon = df.lon.mean()
    new_lat.append(df.lat[max_ele[1]])
    new_lon.append(df.lon[max_ele[1]])
    new_lat.append(center_lat)
    new_lon.append(center_lon)
    new_lat.append(df.lat[min_ele[1]])
    new_lon.append(df.lon[min_ele[1]])
    new_lat.append(coordinates[min_ele[1]][0])
    new_lon.append(coordinates[min_ele[1]][1])
    new_coords = [(x[0], x[1]) for x in zip(new_lat, new_lon)]
    new_df = pd.DataFrame()
    new_df['lat'] = new_lat
    new_df['lon'] = new_lon
    new_df['coordinates'] = new_coords

    new_df = fill_in_point_gaps(new_df, point_gap)
    return new_df


def rate_trail(difficulty: Union[list, pd.Series]) -> float:
    """
    Provides a numerical rating for a trail

    #### Arguments:

    - difficults - list of difficulties (float)

    #### Returns:

    - max_difficulty - the average rating from the hardest section of trail (float)
    """
    max_difficulty = 0
    previous = 0
    previous_2 = 0
    for point in difficulty:
        nearby_avg = (point + previous + previous_2) / 3
        if nearby_avg > max_difficulty:
            max_difficulty = nearby_avg
        previous_2 = previous
        previous = point
    return max_difficulty


def set_color(rating: float, difficultly_modifier: Union[int, float]=0):
    """
    Converts a trail rating and difficulty modifier into a color to print to
    the map.

    #### Arguments:

    - rating - trail rating created by rate_trail (float)
    - difficulty_modifier - additional modifier beyond pitch (float) (default = 0)

    #### Returns:

    - color - css color name (str)
    """
    rating += .07 * difficultly_modifier
    # 0-17 degrees: green
    if rating < .17:
        return 'green'
    # 17-24 degrees: blue
    if rating < .242:
        return 'royalblue'
    # 24-30 degrees: black
    if rating < .30:
        return 'black'
    # 30-45 degrees: red
    elif rating < .45:
        return 'red'
    # >45 degrees: yellow
    else:
        return 'gold'


def smooth_elevations(elevations: Union[list, pd.Series], passes: int = 20) -> Union[list, pd.Series]:
    """
    Smoothes out errors in elevation data

    #### Arguments:

    - elevations - list of elevations
    - passes - number of times to repeat smoothing (default = 20)

    #### Returns:

    - elevations - list of elevations
    """
    if len(elevations) == 0:
        print('No Elevations provided')
        return
    for _ in range(passes):
        previous_previous_point = elevations[0]
        previous_point = elevations[0]
        for i, point in enumerate(elevations):
            new_point = (point + previous_point + previous_previous_point) / 3
            if i > 1:
                elevations[i-1] = new_point
            previous_previous_point = previous_point
            previous_point = point
    return elevations


def calulate_elevation_change(elevation: Union[list, pd.Series]) -> List[float]:
    """
    Calculate the elevation change between pairs of points in a list

    #### Arguments:

    - elevation - list of elevations

    #### Returns:

    - elevation_change - list of elevation differences between points
    """
    previous_row = NAN
    elevation_change = []
    for row in elevation:
        elevation_change.append(row-previous_row)
        previous_row = row
    return elevation_change


def calculate_slope(elevation_change: Union[list, pd.Series], distance) -> List[float]:
    """
    Calculate the slope at each point in a list

    #### Arguments:

    - elevation_change - list of elevation differences between points
    - distance - list of distances between points

    #### Returns:

    -slope - list of slopes (in degrees) at a given point    
    """
    slope = []
    for x, y in zip(elevation_change, distance):
        if y != 0:
            slope.append(degrees(atan(x/y)))
        else:
            slope.append(0)
    slope[0] = 0
    return slope


def calculate_point_difficulty(slope: Union[list, pd.Series]) -> List[float]:
    """
    Converts slopes into difficulty

    #### Arguments:
    - slope - a list of slopes (in degrees)

    #### Returns:

    - difficulty - a list of difficulties (0-90 scale, float)
    """
    difficulty = []
    for point in slope:
        difficulty.append((abs(point)/90)*.9)
    difficulty[0] = 0
    return difficulty


def get_trail_length(coordinates: Union[list, pd.Series]) -> float:
    """
    Calculates the length of a trail from a list of coordinates

    #### Arguments:

    - coordinates - list of (lat, lon) tuples

    #### Returns:

    - length - trail length in meters (float)
    """
    distances = calculate_dist(coordinates)
    return(sum(distances[1:]))


def format_name(name: str) -> str:
    """
    Converts a string to have all major words capitalized

    #### Arguments:

    - name - string

    #### Returns:

    - name - formatted name
    """
    name_list = name.split('_')
    name = ''
    for word in name_list:
        if word[:3] == 'mcc':
            word = 'McC' + word[3:]
            name = '{}{} '.format(name, word)
            continue
        if len(word) > 2 or word == 'fe':
            name = '{}{} '.format(name, word.capitalize())
        else:
            name = '{}{} '.format(name, word)
    return name.strip()


def calculate_mtn_vert(trail_list: List[dict]) -> float:
    """
    Calulates the vertical drop from the highest trail to lowest

    #### Arguments:

    - trail_list - list of trail dicts

    #### Returns:

    - vertical_drop - vertical drop when combining all provided trails
    """
    min_ele = 10000
    max_ele = 0
    for trail in trail_list:
        if trail['points_df'].elevation.max() > max_ele:
            max_ele = trail['points_df'].elevation.max()
        if trail['points_df'].elevation.min() < min_ele:
            min_ele = trail['points_df'].elevation.min()
    return(max_ele-min_ele)


def calculate_trail_vert(elevation: Union[list, pd.Series]) -> float:
    """
    Calulates the vertical drop for a given list of elevations

    #### Arguments:

    - elevation - list of elevations

    #### Returns:

    - vertical_drop - vertical drop for the given elevations
    """
    return elevation.max() - elevation.min()


def assign_region(state: str):
    """
    Takes a 2 letter state code and outputs its region

    #### Arguments:

    - state - US state abbreviations

    #### Returns:

    - region - 'northeast', 'southeast', 'midwest', or 'west'
    """
    northeast = ['ME', 'NH', 'VT', 'NY', 'MA', 'RI', 'CT', 'PA', 'NJ']
    southeast = ['MD', 'DE', 'VA', 'WV', 'KY', 'TN',
                 'NC', 'SC', 'GA', 'FL', 'AL', 'MS', 'LA', 'AR']
    midwest = ['ND', 'SD', 'MN', 'WI', 'MI', 'OH',
               'IN', 'IL', 'IA', 'NE', 'KS', 'MO', 'OK', 'TX']
    west = ['NM', 'AZ', 'CA', 'NV', 'UT', 'CO',
            'WY', 'ID', 'OR', 'WA', 'MT', 'AK', 'HI']

    if len(state.split()) > 1:
        state = state.split()[0]

    if state in northeast:
        return 'northeast'

    if state in southeast:
        return 'southeast'

    if state in midwest:
        return 'midwest'

    if state in west:
        return 'west'
    return 'error'
