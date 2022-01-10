import loadData

def gpx():
    filename = 'gpx/big-bang-409529.gpx'
    #filename = 'gpx/rimrock-415690.gpx'
    #filename = 'gpx/tuckered-out.gpx'
    loadData.runGPX(filename)

def osm():
    difficulty_modifiers = True
    save_map = False
    cardinal_direction = 'n'
    mountain = "crested_butte"
    loadData.runOSM(mountain, difficulty_modifiers, cardinal_direction, save_map)

osm()
