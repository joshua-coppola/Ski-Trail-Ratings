# Ski-Trail-Ratings

This program accepts a OSM or GPX file of a ski trail (OSM or GPX) or ski area (OSM only) and creates a map using a universal difficulty. For larger imports of OSM files, there is a bulk ingest function that accepts a csv file with the names of the OSM files and the orientation of the resort. One current limitation to note is this only works on ski areas in the United States. The elevation data I am currently using only contains points within the US.

The ratings are created by evaluating the average of the steepest 60 meter stretch on the trail in degrees. If the trail is gladed, it will then have a modifier applied that adds 7 degrees to approximate the difficulty increase of glades compared to an open ski slope of the same pitch. The table of ratings can be seen below.

Pitch (in degrees) | Difficulty | Color on Map
--- | --- | ---
0-17 | beginner | green
17-24 | intermediate | blue
24-30 | advanced | black
30-45 | expert | red
45+ | extreme terrain | yellow

## GPX files

As the program currently stands, it accepts a gpx file and will output a graph of the gpx track where yellow is the steepest point on the trail and purple is the flattest.
The background line color will be set according to the chart above.

## OSM files

It will take an osm file, and output a map of all ski trails with a difficultly assigned based on the steepest pitch. There are still some quirks with the slopes that are calculated because of assumptions made about the elevation data, but overall the osm files are now working well.

For each mountain, an overall difficulty rating is created. This metric takes the mean of the hardest 30, 5 and 1 trails, then averages them together. In short, this metric indicates how hard the most difficult trails are at a particular area.

There is also a metric produced using the same methods but reversed. This indicates how challenging the easiest terrain is, and indicates how difficult the easiest terrain may be for a beginner skier.

## Bulk OSM

A CSV file may be provided where each line contains the necessary information to run the program on an OSM file. This provides the same functionality as running a single OSM file, but with added speed for processing many mountains in one batch.

## CLI Usage and Arguments

``` bash
python3 main.py <ARGS>
```

Arguments | Function | Can be used with
--- | --- | ---
`-h` | help page | none
`-s` | save figures | `-[o,i,d,l]`
`-o`, `--osm` | create map from OSM file | `-[s,i,d,l]`
`-c`, `--csv` | create many maps from a csv file where each line. refers to an osm file, direction, and mountains to ignore. Will alway save. | none
`-g`, `--gpx` | create map from GPX file of a single trail | none
`-d`, `--direction` | specifies which way a map should face | `-[s,o,i,l]`
`-i`, `--ignore` | specify a mountain that has been run previously to prevent overlap | `-[s,o,d,l]`
`-l`, `--location` | specify the state where the mountain is located. For multiple states, add quotes and add a space between each state | `-[s,o,i,d]`
`-b` | create barplot comparing difficulty between mountains | `-s`

All filename arguments should not contain the file extension.

Should `-[d,i,l]` not be provided when run with `-o`, the values from the stored mountain information will be used.

If `-i` is used with the same mountain name as specified with `-o`, it will enable a whitelist mode. Only trails that are at that resort based on the trail list created on the previous run of that mountain will be included in the map. This is useful when some trails were manually removed from an osm file and the osm file was updated at a later date.

Example:

``` bash
python3 main.py -s -o deer_valley -d n -i park_city
python3 main.py -s -c mountain_list
python3 main.py -s -b
```

## What's next?

Trail name placement is working well most of the time, but there is room for improvement.

Areas are converted into a line with mixed results. Additional logic would probably improve results.

Add support for international ski areas by adding logic to switch to alternative elevation sources when outside the US.
