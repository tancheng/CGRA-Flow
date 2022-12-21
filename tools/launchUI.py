import tkinter
from tkinter import ttk
from functools import partial

def helloCallBack():
    pass

TILE_SIZE = 60
LINK_LENGTH = 40
INTERVAL = 10
BORDER = 4

master = tkinter.Tk()
rfr = tkinter.Label(master, text="hello world!!")

ROWS = 4
COLS = 4
GRID_WIDTH = (TILE_SIZE+LINK_LENGTH) * COLS - LINK_LENGTH
GRID_HEIGHT = (TILE_SIZE+LINK_LENGTH) * ROWS - LINK_LENGTH
MEM_WIDTH = 50

class Tile:
    def __init__(self, ID, posX, posY, size):
        self.ID = 0
        self.posX = posX
        self.posY = posY
        self.size = size
    
    def getLeftTop(self):
        return (self.posX, self.posY)
    
    def getRightTop(self):
        return (self.posX+self.size, self.posY)
    
    def getLeftBottom(self):
        return (self.posX, self.posY+self.size)
    
    def getRightBottom(self):
        return (self.posX+self.size, self.posY+self.size)
    
    def getLeftMid(self):
        return (self.posX, self.posY+self.size//2)
    
    def getRightMid(self):
        return (self.posX+self.size, self.posY+self.size//2)
    
    def getTopMid(self):
        return (self.posX+self.size//2, self.posY)
    
    def getBottomMid(self):
        return (self.posX+self.size//2, self.posY+self.size)
        

fuConfigPannels = []
xbarConfigPannels = []
def clickTile(ID):
    fuConfigPannels[0].config(text='Tile '+str(ID)+' functional units')
    xbarConfigPannels[0].config(text='Tile '+str(ID)+' crossbar incoming links')
        
def create_cgra_pannel(root, rows, columns):

    # GRID_WIDTH = (TILE_SIZE+LINK_LENGTH) * COLS - linkLength
    TILE_SIZE = (GRID_WIDTH + LINK_LENGTH) / columns - LINK_LENGTH

    totalWidth = GRID_WIDTH+MEM_WIDTH+LINK_LENGTH
    canvas = tkinter.Canvas(root, bd=5, height=GRID_HEIGHT, width=totalWidth)
    canvas.place(x=INTERVAL, y=INTERVAL)

    # pad contains tile and links
    padSize = TILE_SIZE + linkLength
    
    # draw data memory
    posX = 0
    posY = 0
    memHeight = GRID_HEIGHT
    button = tkinter.Button(canvas, text = "Data\nSPM", fg = 'black', bg = 'gray', relief = 'raised', bd = BORDER, command = helloCallBack)
    button.place(height=memHeight, width=MEM_WIDTH, x = posX, y = posY)
            
    # draw tiles
    tiles = []
    numOfTile = 0
    for i in range(rows):
        for j in range(columns):
            ID = i*columns+j
            button = tkinter.Button(canvas, text = "Tile "+str(ID), fg='black', bg='gray', relief='raised', bd=BORDER, command=partial(
    clickTile, ID))
            posX = padSize * j + MEM_WIDTH + linkLength
            posY = GRID_HEIGHT - padSize * i - TILE_SIZE
            button.place(height=TILE_SIZE, width=TILE_SIZE, x = posX, y = posY)
            if j == 0:
                tiles.append([])
            tile = Tile(ID, posX, posY, TILE_SIZE)
            tiles[-1].append(tile)

    # draw links
    for i in range(rows):
        for j in range(columns):
            if j < columns-1:
                # horizontal
                srcX, srcY = tiles[i][j].getRightMid()
                dstX, dstY = tiles[i][j+1].getLeftMid()
                canvas.create_line(srcX, srcY, dstX, dstY, arrow=tkinter.LAST)
                canvas.create_line(dstX, dstY, srcX, srcY, arrow=tkinter.LAST)
            
            if i < rows-1 and j < columns-1:
                # diagonal left bottom to right top
                srcX, srcY = tiles[i][j].getRightTop()
                dstX, dstY = tiles[i+1][j+1].getLeftBottom()
                canvas.create_line(srcX, srcY, dstX, dstY, arrow=tkinter.LAST)
                canvas.create_line(dstX, dstY, srcX, srcY, arrow=tkinter.LAST)
                
            if i < rows-1 and j > 0:
                # diagonal left top to right bottom
                srcX, srcY = tiles[i][j].getLeftTop()
                dstX, dstY = tiles[i+1][j-1].getRightBottom()
                canvas.create_line(srcX, srcY, dstX, dstY, arrow=tkinter.LAST)
                canvas.create_line(dstX, dstY, srcX, srcY, arrow=tkinter.LAST)
                
            if i < rows-1:
                # vertical
                srcX, srcY = tiles[i][j].getTopMid()
                dstX, dstY = tiles[i+1][j].getBottomMid()
                canvas.create_line(srcX, srcY, dstX, dstY, arrow=tkinter.LAST)
                canvas.create_line(dstX, dstY, srcX, srcY, arrow=tkinter.LAST)
                
            if j == 0:
                # connect to memory
                srcX, srcY = tiles[i][j].getLeftMid()
                dstX, dstY = srcX - linkLength, srcY
                canvas.create_line(srcX, srcY, dstX, dstY, arrow=tkinter.LAST)
                canvas.create_line(dstX, dstY, srcX, srcY, arrow=tkinter.LAST)

def place_fu_options(master, fuList = ["Add"]):
    fuCount = len(fuList)
    for i in range(len(fuList)):
        fu = tkinter.Checkbutton(master, text = fuList[i], variable = "Var1")
        fu.grid(row=i//3, column=i%3, padx=3, pady=3, sticky="W")
        
def place_xbar_options(master):
    xbarList = ["W", "E", "N", "S", "NE", "NW", "SE", "SW"]
    for i in range(8):
        xbar = tkinter.Checkbutton(master, text = xbarList[i], variable = "Var1")
        xbar.grid(row=i//4, column=i%4, padx=BORDER, pady=BORDER, sticky="W")
                
def create_param_pannel(master, x, width, height, fuList):
    paramPannel = tkinter.LabelFrame(master, text='Configuration', bd=BORDER, relief='groove')
    paramPannel.place(height=height, width=width, x=x, y=INTERVAL)
    
    paramPannel.columnconfigure(0, weight=1)
    paramPannel.columnconfigure(1, weight=60)
    paramPannel.columnconfigure(2, weight=1)
    paramPannel.columnconfigure(3, weight=60)

    rowsLabel = ttk.Label(paramPannel, text='Rows:' )
    rowsLabel.grid(row=0, column=0, sticky=tk.W, padx=BORDER, pady=BORDER)
    rowsEntry = ttk.Entry(paramPannel, justify=tkinter.CENTER)
    rowsEntry.grid(row=0, column=1, sticky=tk.W, padx=BORDER, pady=BORDER)
    rowsEntry.insert(0, "4")
    
    columnsLabel = ttk.Label(paramPannel, text='Columns:')
    columnsLabel.grid(row=0, column=2, sticky=tk.E, padx=BORDER, pady=BORDER)
    columnsEntry = ttk.Entry(paramPannel, justify=tkinter.CENTER)
    columnsEntry.grid(row=0, column=3, sticky=tk.E, padx=BORDER, pady=BORDER)
    columnsEntry.insert(0, "4")
    
    configMemLabel = ttk.Label(paramPannel, text='ConfigMemSize (entries):')
    configMemLabel.grid(columnspan=3, row=1, column=0, padx=BORDER, pady=BORDER)
    configMemEntry = ttk.Entry(paramPannel, justify=tkinter.CENTER)
    configMemEntry.grid(row=1, column=3, sticky=tk.E, padx=BORDER, pady=BORDER)
    configMemEntry.insert(0, "8")
    
    dataMemLabel = ttk.Label(paramPannel, text='DataSPMSize (KBs):')
    dataMemLabel.grid(columnspan=3, row=2, column=0, padx=BORDER, pady=BORDER)
    dataMemEntry = ttk.Entry(paramPannel, justify=tkinter.CENTER)
    dataMemEntry.grid(row=2, column=3, sticky=tk.E, padx=BORDER, pady=BORDER)
    dataMemEntry.insert(0, "4")
    
    # updateButton = tkinter.Button(paramPannel, text = "Update demo and script", relief='raised', command = helloCallBack)
    updateButton = tkinter.Button(paramPannel, text = "Update demo and script", relief='raised', command = partial(create_cgra_pannel, master, 5, 5))
    updateButton.grid(columnspan=4, row=3, column=0, padx=BORDER, pady=BORDER)
    
    fuConfigPannel = tkinter.LabelFrame(paramPannel, text='Tile 0 functional units', bd = BORDER, relief='groove')
    # fuConfigPannel.config(text='xxx')
    fuConfigPannel.grid(columnspan=4, row=4, column=0, padx=BORDER, pady=BORDER)
    fuConfigPannels.append(fuConfigPannel)
    
    place_fu_options(fuConfigPannel, fuList)
    
    xbarConfigPannel = tkinter.LabelFrame(paramPannel, text='Tile 0 crossbar incoming links', bd = BORDER, relief='groove')
    # xbarConfigPannel.config(text='y')
    xbarConfigPannel.grid(columnspan=4, row=5, column=0, padx=BORDER, pady=BORDER)
    xbarConfigPannels.append(xbarConfigPannel)
    
    place_xbar_options(xbarConfigPannel)
    
    
def create_script_pannel(master, x, width, height):
    scriptPannel = tkinter.LabelFrame(master, text='Script', bd = BORDER, relief='groove')
    scriptPannel.place(height=height, width=width, x=x, y=INTERVAL)
    
    script = tkinter.Entry(scriptPannel, bd = BORDER, relief='groove')
    script.place(height=height-8*BORDER-30, width=width-4*BORDER, x=BORDER, y=BORDER)
    
    copyButton = tkinter.Button(scriptPannel, text = "Copy script", relief='raised', command = helloCallBack)
    copyButton.place(x=width-4*BORDER-70, y=height-8*BORDER-20)
    
    
def create_test_pannel(master, x, y, width, height):
    testPannel = tkinter.LabelFrame(master, text='Verification', bd = BORDER, relief='groove')
    testPannel.place(height=height, width=width, x=x, y=y)
    testButton = tkinter.Button(testPannel, text = "Run tests", relief='raised', command = helloCallBack)
    testButton.grid(row=0, column=0, sticky=tk.W, padx=BORDER, pady=BORDER//2)
    testProgress = ttk.Progressbar(testPannel, orient='horizontal', mode='determinate', length=170)
    testProgress['value'] = 70
    testProgress.grid(row=0, column=1, padx=BORDER, pady=BORDER//2)
    testShow = tkinter.Label(testPannel, text = "PASS", fg='green')
    testShow.grid(row=0, column=2, sticky=tk.E, padx=BORDER, pady=BORDER//2)

    
def create_report_pannel(master, x, y, width):
    reportPannel = tkinter.LabelFrame(master, text='Report area/power', bd = BORDER, relief='groove')
    reportPannel.place(width=width, x=x, y=y)
    reportButton = tkinter.Button(reportPannel, text = "Report", relief='raised', command = helloCallBack)
    reportButton.grid(row=0, column=0, sticky=tk.W, padx=BORDER, pady=BORDER//2)
    reportProgress = ttk.Progressbar(reportPannel, orient='horizontal', mode='determinate', length=190)
    reportProgress['value'] = 30
    reportProgress.grid(columnspan=3, row=0, column=1, padx=BORDER, pady=BORDER//2)
    
    reportTileAreaLabel = tkinter.Label(reportPannel, text = "Area of tiles:")
    reportTileAreaLabel.grid(row=1, column=0, sticky=tk.E, padx=BORDER, pady=BORDER//2)
    reportTileAreaData = tkinter.Label(reportPannel, text = "0")
    reportTileAreaData.grid(row=1, column=1, sticky=tk.E, padx=BORDER, pady=BORDER//2)
    reportTilePowerLabel = tkinter.Label(reportPannel, text = "Power of tiles:")
    reportTilePowerLabel.grid(row=1, column=2, sticky=tk.E, padx=BORDER, pady=BORDER//2)
    reportTilePowerData = tkinter.Label(reportPannel, text = "0")
    reportTilePowerData.grid(row=1, column=3, sticky=tk.E, padx=BORDER, pady=BORDER//2)
    
    reportSPMAreaLabel = tkinter.Label(reportPannel, text = "Area of SPM:")
    reportSPMAreaLabel.grid(row=2, column=0, sticky=tk.E, padx=BORDER, pady=BORDER//2)
    reportSPMAreaData = tkinter.Label(reportPannel, text = "0")
    reportSPMAreaData.grid(row=2, column=1, sticky=tk.E, padx=BORDER, pady=BORDER//2)
    reportSPMPowerLabel = tkinter.Label(reportPannel, text = "Power of SPM:")
    reportSPMPowerLabel.grid(row=2, column=2, sticky=tk.E, padx=BORDER, pady=BORDER//2)
    reportSPMPowerData = tkinter.Label(reportPannel, text = "0")
    reportSPMPowerData.grid(row=2, column=3, sticky=tk.E, padx=BORDER, pady=BORDER//2)
    
    
def create_layout_pannel(master, x, width, height):
    layoutPannel = tkinter.LabelFrame(master, text='Layout', bd = BORDER, relief='groove')
    layoutPannel.place(height=height, width=width, x=x, y=INTERVAL)
    showButton = tkinter.Button(layoutPannel, text = "Show layout", relief='raised', command = helloCallBack)
    showButton.pack()
    X = tkinter.Label(layoutPannel, text = 'layout figure is coming soon...', fg = 'black')
    X.pack()
                

create_cgra_pannel(master, ROWS, COLS)

paramPadPosX = GRID_WIDTH + MEM_WIDTH + LINK_LENGTH + INTERVAL * 3
paramPadWidth = 250
fuList = ["Add", "Mul", "Shift", "Load", "Store", "MAC"]
create_param_pannel(master, paramPadPosX, paramPadWidth, GRID_HEIGHT, fuList)

scriptPadPosX = paramPadPosX + paramPadWidth + INTERVAL
scriptPadWidth = 300
create_script_pannel(master, scriptPadPosX, scriptPadWidth, GRID_HEIGHT//2)

create_test_pannel(master, scriptPadPosX, GRID_HEIGHT//2+20, scriptPadWidth, GRID_HEIGHT//4-30)

create_report_pannel(master, scriptPadPosX, GRID_HEIGHT*3//4, scriptPadWidth)

layoutPadPosX = scriptPadPosX + scriptPadWidth + INTERVAL
layoutPadWidth = 300
create_layout_pannel(master, layoutPadPosX, layoutPadWidth, GRID_HEIGHT)

master.geometry(str(layoutPadPosX+layoutPadWidth+INTERVAL)+"x"+str(GRID_HEIGHT+INTERVAL*2))


master.mainloop()