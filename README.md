# Ski-Trail-Ratings

The plan for this program is to create a system to feed the topograpy of a ski trail in, and get a standarized rating out. What a rating means depends on the ski area, and this would provide a way to standardize between areas.

## Current Status

### GPX files

As the program currently stands, it accepts a gpx file and will output a graph of the gpx track where yellow is the steepest point on the trail and purple is the flattest. 

### OSM files

It will take an osm file, and output a map of all ski trails with a difficultly assigned based on the steepest pitch. There are still some quirks with the slopes that are calculated because of assumptions made about the elevation data, but overall the osm files are now working well.

## What's next?

At this point, the maps are mostly down to fine tuning. There are some trails that are broken up into several pieces, and I want to stitch them back together.