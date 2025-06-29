# constants.py

# === Canvas Colors ===
CANVAS_BG_COLOR = "#212121"
CANVAS_LINE_COLOR = "white"

# === Multi-CGRA UI Colors ===
MULTI_CGRA_FRAME_COLOR = "#14375E"
MULTI_CGRA_TILE_COLOR = "#1F538D"
MULTI_CGRA_TXT_COLOR = "white"
MULTI_CGRA_SELECTED_COLOR = "lightblue"

# === Port Directions ===
PORT_NORTH = 0
PORT_SOUTH = 1
PORT_WEST = 2
PORT_EAST = 3
PORT_NORTHWEST = 4
PORT_NORTHEAST = 5
PORT_SOUTHEAST = 6
PORT_SOUTHWEST = 7
PORT_DIRECTION_COUNTS = 8

# === Default CGRA Dimensions ===
CGRA_ROWS = 3
CGRA_COLS = 3
ROWS = 4
COLS = 4

# === Layout Settings ===
INTERVAL = 10
BORDER = 4
HIGHLIGHT_THICKNESS = 1
FRAME_LABEL_FONT_SIZE = 15

# === Memory Sizes ===
MEM_WIDTH = 50
CONFIG_MEM_SIZE = 8
DATA_MEM_SIZE = 4


fuTypeList = ["Phi", "Add", "Shift", "Ld", "Sel", "Cmp", "MAC", "St", "Ret", "Mul", "Logic", "Br"]
xbarTypeList = ["W", "E", "N", "S", "NE", "NW", "SE", "SW"]

xbarType2Port = {
    "W": PORT_WEST,
    "E": PORT_EAST,
    "N": PORT_NORTH,
    "S": PORT_SOUTH,
    "NE": PORT_NORTHEAST,
    "NW": PORT_NORTHWEST,
    "SE": PORT_SOUTHEAST,
    "SW": PORT_SOUTHWEST
}

xbarPort2Type = {v: k for k, v in xbarType2Port.items()}

xbarPortOpposites = {
    PORT_WEST: PORT_EAST,
    PORT_EAST: PORT_WEST,
    PORT_NORTH: PORT_SOUTH,
    PORT_SOUTH: PORT_NORTH,
    PORT_NORTHWEST: PORT_SOUTHEAST,
    PORT_NORTHEAST: PORT_SOUTHWEST,
    PORT_SOUTHWEST: PORT_NORTHEAST,
    PORT_SOUTHEAST: PORT_NORTHWEST
}