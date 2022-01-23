# Ski-Trail-Ratings

This program accepts a OSM or GPX file of a ski trail (OSM or GPX) or ski area (OSM only) and creates a map using a universal difficulty. For larger imports of OSM files, there is a bulk ingest function that accepts a csv file with the names of the OSM files and the orientation of the resort. One current limitation to note is this only works on ski areas in the United States. The elevation data I am currently using only contains points within the US.

The ratings are created by evaluating the average of the steepest 60 meter stretch on the trail in degrees. If the trail is gladed, it will then have a modifier applied that adds 7 degrees to approximate the difficulty increase of glades compared to an open ski slope of the same pitch. The table of ratings can be seen below.

Pitch (in degrees) | Difficulty | Color on Map
--- | --- | ---
0-17 | beginner | green
17-24 | intermeidate | blue
24-30 | advanced | black
30-45 | expert | red
45+ | extreme terrain | yellow

### GPX files

As the program currently stands, it accepts a gpx file and will output a graph of the gpx track where yellow is the steepest point on the trail and purple is the flattest. 
The background line color will be set according to the chart above.

### OSM files

It will take an osm file, and output a map of all ski trails with a difficultly assigned based on the steepest pitch. There are still some quirks with the slopes that are calculated because of assumptions made about the elevation data, but overall the osm files are now working well.

For each mountain, an overall difficulty rating is created. This metric takes the median rating for the top 5 hardest trails and the top 20, then averages the two together. In short, this metric indicates how hard the most difficult trails are at a particular area.

There is also a metric produced using the same methods but reversed. This indicates how challenging the easiest terrain is, and indicates how difficult the easiest terrain may be for a beginner skier.

### Bulk OSM

Should the bulk import function be used, a bar graph for each of these metrics will be created to rank the relative difficulty of all resorts inputted.

## What's next?
Trail name placement is working well most of the time, but there is room for improvement.

Areas are converted into a line with mixed results. Additional logic would probably improve results.

Add support for international ski areas by adding logic to switch to alternative elevation sources when outside the US.