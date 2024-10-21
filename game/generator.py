from PIL import Image, ImageDraw, ImageFont
from random import randint

MAP_SIZE = 2048
START_X, START_Y = (109, 109)
IMAGES = "game/static/"
MAP_NAME = "full-map.png"
CASTLE = "clan-castle.png"
MINE = "gold-mine.png"
OIL_RIG = "oil-rig.png"
OIL_DERRICK = "oil-derick.png"
GRID_X, GRID_Y = (238, 238)
BORDER_SIZE = 16
ICON_SIZE = 220

MARKUP_COLORS = [(0, 0, 255, 128),
                (0, 255, 0, 128),
                (0, 0, 0, 128),
                (255, 255, 0, 128),
                (255, 0, 0, 128),
                (255, 255, 255, 128),
                (0, 0, 0, 128),
                (255, 0, 0, 128)]

IDX4ICON = lambda x, y: [
    (BORDER_SIZE + (BORDER_SIZE + GRID_X) * x) + ((GRID_X - ICON_SIZE) // 2),
    (BORDER_SIZE + (BORDER_SIZE + GRID_Y) * y) + ((GRID_Y - ICON_SIZE) // 2)
]

IDX4MARKUP = lambda x, y: [
    int(((BORDER_SIZE + GRID_X) * x) + BORDER_SIZE),
    int(((BORDER_SIZE + GRID_Y) * y) + BORDER_SIZE)
]


ICON_GRID = [[IDX4ICON(x, y) 
        for y in range(8)] 
        for x in range(8)]

MARKUP_GRID = [[IDX4MARKUP(x, y) 
        for y in range(8)] 
        for x in range(8)]

print(MARKUP_GRID)



def getMap():
    #with Image.open(IMAGES + MAP_NAME) as map:
        #map = map.crop((START_X, START_Y, START_X + MAP_SIZE, START_Y + MAP_SIZE))
    return Image.open(IMAGES + MAP_NAME).convert("RGBA")

def generateCastles():
    map = getMap()
    overlay = Image.new('RGBA', map.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for i in range(8):
        if i == 0 or i == 7: 
            randgrid = randint(0,7)
            iX, iY = ICON_GRID[i][randgrid]
            gX, gY = MARKUP_GRID[i][randgrid]
        else:
            continue
        with Image.open(IMAGES + CASTLE) as castle:
            castle = castle.resize((GRID_X - 20, GRID_Y - 20))
        draw.rectangle([gX, gY, gX + GRID_X, gY + GRID_Y], fill=MARKUP_COLORS[i])
        map = Image.alpha_composite(map, overlay)
        map.paste(castle, (iX, iY), castle)
    map.save(IMAGES + "test.png")

generateCastles()