import sys
import os
import time
import subprocess
import tkinter
from tkinter import ttk
from tkinter import filedialog as fd
from PIL import Image, ImageTk
from functools import partial

from VectorCGRA.cgra.translate.CGRARTL_test import *

PORT_NORTH     = 0
PORT_SOUTH     = 1
PORT_WEST      = 2
PORT_EAST      = 3
PORT_NORTHWEST = 4
PORT_NORTHEAST = 5
PORT_SOUTHEAST = 6
PORT_SOUTHWEST = 7
PORT_DIRECTION_COUNTS = 8

LINK_NO_MEM   = 0
LINK_FROM_MEM = 1
LINK_TO_MEM   = 2

def helloCallBack():
    pass

TILE_HEIGHT = 60
TILE_WIDTH = 60
LINK_LENGTH = 40
INTERVAL = 10
BORDER = 4

master = tkinter.Tk()
master.title("CGRA-Flow: An Integrated End-to-End Framework for CGRA Exploration, Compilation, and Development")

ROWS = 4
COLS = 4
GRID_WIDTH = (TILE_WIDTH+LINK_LENGTH) * COLS - LINK_LENGTH
GRID_HEIGHT = (TILE_HEIGHT+LINK_LENGTH) * ROWS - LINK_LENGTH
MEM_WIDTH = 50
CONFIG_MEM = 8
DATA_MEM = 4
II = 4

fuTypeList = ["Phi", "Add", "Shift", "Ld", "Sel", "Cmp", "MAC", "St", "Ret", "Mul", "Logic", "Br"]

xbarTypeList = ["W", "E", "N", "S", "NE", "NW", "SE", "SW"]

xbarType2Port = {}
xbarType2Port["W" ] = PORT_WEST
xbarType2Port["E" ] = PORT_EAST
xbarType2Port["N" ] = PORT_NORTH
xbarType2Port["S" ] = PORT_SOUTH
xbarType2Port["NE"] = PORT_NORTHEAST
xbarType2Port["NW"] = PORT_NORTHWEST
xbarType2Port["SE"] = PORT_SOUTHEAST
xbarType2Port["SW"] = PORT_SOUTHWEST

widgets = {}
images = {}
entireTileCheckVar = tkinter.IntVar()
fuCheckVars = {}
fuCheckbuttons = {}
xbarCheckVars = {}
xbarCheckbuttons = {}

class ParamTile:
    def __init__(s, ID, dimX, dimY, posX, posY, tileWidth, tileHeight):
        s.ID = ID
        s.disabled = False
        s.posX = posX
        s.posY = posY
        s.dimX = dimX
        s.dimY = dimY
        s.width = tileWidth
        s.height = tileHeight
        s.outLinks = {}
        s.inLinks = {}
        s.hasToMem = False
        s.hasFromMem = False
        s.invalidOutPorts = set()
        s.invalidInPorts = set()
        s.fuDict = {}
        s.xbarDict = {}
        for i in range( PORT_DIRECTION_COUNTS ):
            s.invalidOutPorts.add(i)
            s.invalidInPorts.add(i)
        
        for xbarType in xbarTypeList:
            s.xbarDict[xbarType] = 1

        for fuType in fuTypeList:
            s.fuDict[fuType] = 1

    def setOutLink(s, portType, link):
        s.outLinks[portType] = link

    def setInLink(s, portType, link):
        s.inLinks[portType] = link

    # position X/Y for drawing the tile
    def getPosXY(s, baseX=0, baseY=0):
        return (baseX+s.posX, baseY+s.posY)
   
    # position X/Y for connecting routing ports
    def getPosXYOnPort(s, portType, baseX=0, baseY=0):
        if portType == PORT_NORTH:
            return s.getNorth(baseX, baseY)
        elif portType == PORT_SOUTH:
            return s.getSouth(baseX, baseY)
        elif portType == PORT_WEST:
            return s.getWest(baseX, baseY)
        elif portType == PORT_EAST:
            return s.getEast(baseX, baseY)
        elif portType == PORT_NORTHEAST:
            return s.getNorthEast(baseX, baseY)
        elif portType == PORT_NORTHWEST:
            return s.getNorthWest(baseX, baseY)
        elif portType == PORT_SOUTHEAST:
            return s.getSouthEast(baseX, baseY)
        else:
            return s.getSouthWest(baseX, baseY)

    def getNorthWest(s, baseX=0, baseY=0):
        return (baseX+s.posX, baseY+s.posY)
    
    def getNorthEast(s, baseX=0, baseY=0):
        return (baseX+s.posX+s.width, baseY+s.posY)
    
    def getSouthWest(s, baseX=0, baseY=0):
        return (baseX+s.posX, baseY+s.posY+s.height)
    
    def getSouthEast(s, baseX=0, baseY=0):
        return (baseX+s.posX+s.width, baseY+s.posY+s.height)
    
    def getWest(s, baseX=0, baseY=0):
        return (baseX+s.posX, baseY+s.posY+s.height//2)
    
    def getEast(s, baseX=0, baseY=0):
        return (baseX+s.posX+s.width, baseY+s.posY+s.height//2)
    
    def getNorth(s, baseX=0, baseY=0):
        return (baseX+s.posX+s.width//2, baseY+s.posY)
    
    def getSouth(s, baseX=0, baseY=0):
        return (baseX+s.posX+s.width//2, baseY+s.posY+s.height)
 
    def getIndex(s, tileList):
        if s.disabled:
            return -1
        index = 0
        for tile in tileList:
            if tile.dimY < s.dimY and not tile.disabled:
                index += 1
            elif tile.dimY == s.dimY and tile.dimX < s.dimX and not tile.disabled:
                index += 1
        return index

    def updateAvailability( s ):
        s.disabled = True
        for fuType in fuTypeList:
            if s.fuDict[fuType] == 1:
                s.disabled = False
                break


class ParamLink:
    def __init__(s, srcTile, dstTile, srcPort, dstPort, memAccessType=LINK_NO_MEM):
        s.srcTile = srcTile
        s.dstTile = dstTile
        s.srcPort = srcPort
        s.dstPort = dstPort
        s.disabled = False
        s.memAccessType = memAccessType
        if s.srcTile != None:
            s.srcTile.setOutLink(s.srcPort, s)
        if s.dstTile != None:
            s.dstTile.setInLink(s.dstPort, s)

    def validatePorts(s):
        if s.memAccessType == LINK_NO_MEM:
            s.srcTile.invalidOutPorts.remove(s.srcPort)
            s.dstTile.invalidInPorts.remove(s.dstPort)
        if s.memAccessType == LINK_TO_MEM:
            s.srcTile.hasToMem = True
        if s.memAccessType == LINK_FROM_MEM:
            s.dstTile.hasFromMem = True

    def getSrcXY(s, baseX=0, baseY=0):
        if s.srcTile != None:
            return s.srcTile.getPosXYOnPort(s.srcPort, baseX, baseY)
        else:
            dstPosX, dstPosY = s.dstTile.getPosXYOnPort(s.dstPort, baseX, baseY)
            return dstPosX-LINK_LENGTH, dstPosY

    def getDstXY(s, baseX=0, baseY=0):
        if s.dstTile != None:
            return s.dstTile.getPosXYOnPort(s.dstPort, baseX, baseY)
        else:
            srcPosX, srcPosY = s.srcTile.getPosXYOnPort(s.srcPort, baseX, baseY)
            return srcPosX-LINK_LENGTH, srcPosY


class ParamCGRA:
    def __init__(s, rows, columns, configMem=CONFIG_MEM, dataMem=DATA_MEM):
        s.rows = rows
        s.columns = columns
        s.configMem = configMem
        s.dataMem = dataMem
        s.tiles = []
        s.links = []
        s.targetTileID = 0

        for fuType in fuTypeList:
            if fuType in fuCheckVars:
                fuCheckVars[fuType].set(1)

        for xbarType in xbarTypeList:
            if xbarType in xbarCheckVars:
                xbarCheckVars[xbarType].set(1)

    def updateMem(s, configMem, dataMem):
        s.configMem = configMem
        s.dataMem = dataMem

    def initTiles(s, tiles):
        for r in range(s.rows):
            for c in range(s.columns):
                s.tiles.append(tiles[r][c])

    def addTile(s, tile):
        s.tiles.append(tile)

    def initLinks(s, links):
        numOfLinks = s.rows*s.columns*2 + (s.rows-1)*s.columns*2 + (s.rows-1)*(s.columns-1)*2*2

        for link in links:
            s.links.append(link)

    def addLink(s, link):
        s.links.append(link)

    def updateFuCheckbutton(s, fuType, value):
        s.getTileOfID(s.targetTileID).fuDict[fuType] = value

    def updateXbarCheckbutton(s, xbarType, value):
        tile = s.getTileOfID(s.targetTileID)
        tile.xbarDict[xbarType] = value
        port = xbarType2Port[xbarType]
        if port in tile.outLinks:
            tile.outLinks[port].disabled = True if value == 0 else False

    def getTileOfID(s, ID):
        for tile in s.tiles:
            if tile.ID == ID:
                return tile
        return None

    def getTileOfDim(s, dimX, dimY):
        for tile in s.tiles:
            if tile.dimX == dimX and tile.dimY == dimY:
                return tile
        return None

    # certain tiles could be disabled due to the disabled FUs/links
    def updateTiles(s):
        pass

    # some links can be fused as single one due to disabled tiles
    def updateLinks(s):
        pass


paramCGRA = ParamCGRA(ROWS, COLS, CONFIG_MEM, DATA_MEM)
targetKernelName = "not selected yet"

def clickGenerateVerilog():
    os.system("mkdir verilog")
    os.chdir("verilog")

    test_cgra_universal()

    widgets["verilogText"].delete("1.0", tkinter.END)
    found = False
    print(os.listdir("./"))
    for fileName in os.listdir("./"):
        if "__" in fileName and ".v" in fileName:
            print("we found the file: ", fileName)
            f = open(fileName, "r")
            widgets["verilogText"].insert("1.0", f.read())
            found = True
            break

    if not found:
        widgets["verilogText"].insert(tkinter.END, "Error exists during Verilog generation")
    os.system("rename s/\.v/\.log/g *")

    os.chdir("..")


def clickTile(ID):
    widgets["fuConfigPannel"].config(text='Tile '+str(ID)+' functional units')
    widgets["xbarConfigPannel"].config(text='Tile '+str(ID)+' crossbar incoming links')
    widgets["entireTileCheckbutton"].config(text='Disable the entire Tile '+str(ID))
    paramCGRA.targetTileID = ID

    disabled = paramCGRA.getTileOfID(ID).disabled
    for fuType in fuTypeList:
        fuCheckVars[fuType].set(paramCGRA.tiles[ID].fuDict[fuType])
        fuCheckbuttons[fuType].configure(state="disabled" if disabled else "normal")

    for xbarType in xbarTypeList:
        xbarCheckVars[xbarType].set(paramCGRA.tiles[ID].xbarDict[xbarType])
        xbarCheckbuttons[xbarType].configure(state="disabled" if disabled else "normal")

    entireTileCheckVar.set(1 if paramCGRA.getTileOfID(ID).disabled else 0)
 

def clickEntireTileCheckbutton():

    paramCGRA.getTileOfID(paramCGRA.targetTileID).disabled = True if entireTileCheckVar.get() == 1 else False
    if entireTileCheckVar.get() == 1:
        for fuType in fuTypeList:
            fuCheckVars[fuType].set(0)
            clickFuCheckbutton(fuType)
            fuCheckbuttons[fuType].configure(state="disabled")
            # paramCGRA.targetTileID tiles[ID].fuDict[fuType])
            # fuCheckbutton.select()
            # paramCGRA.updateFuCheckbutton(fuTypeList[i], fuVar.get())

        for xbarType in xbarTypeList:
            xbarCheckVars[xbarType].set(0)
            clickXbarCheckbutton(xbarType)
            xbarCheckbuttons[xbarType].configure(state="disabled")
 
        paramCGRA.getTileOfID(paramCGRA.targetTileID).disabled = True
    else:
        for fuType in fuTypeList:
            fuCheckVars[fuType].set(0)
            clickFuCheckbutton(fuType)
            fuCheckbuttons[fuType].configure(state="normal")

        for xbarType in xbarTypeList:
            xbarCheckVars[xbarType].set(0)
            clickXbarCheckbutton(xbarType)
            xbarCheckbuttons[xbarType].configure(state="normal")
 
        paramCGRA.getTileOfID(paramCGRA.targetTileID).disabled = False


def clickFuCheckbutton(fuType):
    paramCGRA.updateFuCheckbutton(fuType, fuCheckVars[fuType].get())
    # need to refine/assemble the CGRA model here:


def clickXbarCheckbutton(xbarType):
    paramCGRA.updateXbarCheckbutton(xbarType, xbarCheckVars[xbarType].get())
    # need to refine/assemble the CGRA model here:
    

def clickUpdate(root):
    rows = int(widgets["rowsEntry"].get())
    columns = int(widgets["columnsEntry"].get())
    configMem = int(widgets["configMemEntry"].get())
    dataMem = int(widgets["dataMemEntry"].get())

    global paramCGRA

    if paramCGRA.rows != rows or paramCGRA.columns != columns:
        paramCGRA = ParamCGRA(rows, columns)

    paramCGRA.updateMem(configMem, dataMem)
    paramCGRA.updateTiles()
    paramCGRA.updateLinks()

    create_cgra_pannel(root, rows, columns)
    clickTile(0)

def clickTest():
    # need to provide the paths for lib.so and kernel.bc
    os.system("mkdir test")
    # os.system("cd test")
    os.chdir("test")

    widgets["testShow"].configure(text="0%", fg="red")
    master.update_idletasks()

    # os.system("pytest ../../VectorCGRA")
    testProc = subprocess.Popen(["pytest ../../VectorCGRA", '-u'], stdout=subprocess.PIPE, shell=True, bufsize=1)
    with testProc.stdout:
        for line in iter(testProc.stdout.readline, b''):
            outputLine = line.decode("utf-8")
            print(outputLine)
            if "%]" in outputLine:
                value = int(outputLine.split("[")[1].split("%]")[0])
                widgets["testProgress"].configure(value=value)
                widgets["testShow"].configure(text=str(value)+"%", fg="red")
                master.update_idletasks()

    widgets["testShow"].configure(text="PASSED", fg="green")
    # (out, err) = testProc.communicate()
    # print("check test output:", out)

    os.chdir("..")

def clickSelectKernel():
    global paramCGRA
    kernelName = fd.askopenfilename(title="choose a kernel", initialdir="../", filetypes=(("C/C++ file", "*.cpp"), ("C/C++ file", "*.c"), ("C/C++ file", "*.C"), ("C/C++ file", "*.CPP")))
    targetKernelName = kernelName

    widgets["kernelPathLabel"].configure(state="normal")
    widgets["kernelPathLabel"].delete(0, tkinter.END)
    widgets["kernelPathLabel"].insert(0, targetKernelName)
    widgets["kernelPathLabel"].configure(state="disabled")

def clickCompileKernel():
    # need to provide the paths for lib.so and kernel.bc
    compileProc = subprocess.Popen(["../CGRA-Mapper/test/run_test.sh"], stdout=subprocess.PIPE, shell=True)
    (out, err) = compileProc.communicate()
    print("check program output:", out)

def clickGenerateDFG():
    pass

def clickMapDFG(II):
    # pad contains tile and links
    tileWidth = paramCGRA.tiles[0].width
    tileHeight = paramCGRA.tiles[0].height
    padWidth = tileWidth + LINK_LENGTH
    padHeight = tileHeight + LINK_LENGTH
    baseX = 0

    canvas = widgets["mappingCanvas"]
    canvas.delete("all")
    cgraWidth = GRID_WIDTH + MEM_WIDTH + LINK_LENGTH + 20
    canvas.configure(scrollregion=(0, 0, II*cgraWidth, GRID_HEIGHT))
    
    for ii in range(II):
        # draw data memory
        spmLabel = tkinter.Label(canvas, text="Data\nSPM", fg='black', bg='gray', relief='raised', bd=BORDER)
        canvas.create_window(baseX+BORDER, BORDER, window=spmLabel, height=GRID_HEIGHT, width=MEM_WIDTH, anchor="nw")

        # draw tiles
        for tile in paramCGRA.tiles:
            button = tkinter.Label(canvas, text = "Tile "+str(tile.ID), fg='black', bg='gray', relief='raised', bd=BORDER)
            posX, posY = tile.getPosXY(baseX+BORDER, BORDER)
            canvas.create_window(posX, posY, window=button, height=tileHeight, width=tileWidth, anchor="nw")

        # draw links
        for link in paramCGRA.links:
            srcX, srcY = link.getSrcXY(baseX+BORDER, BORDER)
            dstX, dstY = link.getDstXY(baseX+BORDER, BORDER)
            canvas.create_line(srcX, srcY, dstX, dstY, arrow=tkinter.LAST)
 
        cycleLabel = tkinter.Label(canvas, text="Cycle "+str(ii))
        canvas.create_window(baseX+280, GRID_HEIGHT+10+BORDER, window=cycleLabel, height=20, width=80)

        baseX += GRID_WIDTH + MEM_WIDTH + LINK_LENGTH + 20
        canvas.create_line(baseX-5, INTERVAL, baseX-5, GRID_HEIGHT, width=2, dash=(10,2))


def create_cgra_pannel(root, rows, columns):

    ROWS = rows
    COLS = columns
    TILE_WIDTH = (GRID_WIDTH + LINK_LENGTH) / COLS - LINK_LENGTH
    TILE_HEIGHT = (GRID_HEIGHT + LINK_LENGTH) / ROWS - LINK_LENGTH

    totalWidth = GRID_WIDTH+MEM_WIDTH+LINK_LENGTH
    canvas = tkinter.Canvas(root, bd=5, height=GRID_HEIGHT, width=totalWidth)
    canvas.place(x=INTERVAL, y=INTERVAL)

    # pad contains tile and links
    # padSize = TILE_SIZE + LINK_LENGTH
    padHeight = TILE_HEIGHT + LINK_LENGTH
    padWidth = TILE_WIDTH + LINK_LENGTH
    
    # draw data memory
    memHeight = GRID_HEIGHT
    button = tkinter.Button(canvas, text = "Data\nSPM", fg = 'black', bg = 'gray', relief = 'raised', bd = BORDER, command = helloCallBack)
    button.place(height=memHeight, width=MEM_WIDTH, x = 0, y = 0)
            
    # construct tiles
    if len(paramCGRA.tiles) == 0:
        for i in range(ROWS):
            for j in range(COLS):
                ID = i*COLS+j
                posX = padWidth * j + MEM_WIDTH + LINK_LENGTH
                posY = GRID_HEIGHT - padHeight * i - TILE_HEIGHT

                tile = ParamTile(ID, j, i, posX, posY, TILE_WIDTH, TILE_HEIGHT)
                paramCGRA.addTile(tile)

    # draw tiles
    for tile in paramCGRA.tiles:
        if tile.disabled:
            button = tkinter.Button(canvas, text = "Tile "+str(tile.ID), fg='gray', relief='flat', bd=BORDER, command=partial(clickTile, tile.ID))
        else:
            button = tkinter.Button(canvas, text = "Tile "+str(tile.ID), fg='black', bg='gray', relief='raised', bd=BORDER, command=partial(clickTile, tile.ID))

        posX, posY = tile.getPosXY()
        button.place(height=TILE_HEIGHT, width=TILE_WIDTH, x = posX, y = posY)


    # TODO: draw lines based on the links connected between tiles rather than pos

    # construct links
    if len(paramCGRA.links) == 0:
        for i in range(ROWS):
            for j in range(COLS):
                if j < COLS-1:
                    # horizontal
                    tile0 = paramCGRA.getTileOfDim(j, i)
                    tile1 = paramCGRA.getTileOfDim(j+1, i)
                    link0 = ParamLink(tile0, tile1, PORT_EAST, PORT_WEST)
                    link1 = ParamLink(tile1, tile0, PORT_WEST, PORT_EAST)
                    paramCGRA.addLink(link0)
                    paramCGRA.addLink(link1)

                if i < ROWS-1 and j < COLS-1:
                    # diagonal left bottom to right top
                    tile0 = paramCGRA.getTileOfDim(j, i)
                    tile1 = paramCGRA.getTileOfDim(j+1, i+1)
                    link0 = ParamLink(tile0, tile1, PORT_NORTHEAST, PORT_SOUTHWEST)
                    link1 = ParamLink(tile1, tile0, PORT_SOUTHWEST, PORT_NORTHEAST)
                    paramCGRA.addLink(link0)
                    paramCGRA.addLink(link1)

                if i < ROWS-1 and j > 0:
                    # diagonal left top to right bottom
                    tile0 = paramCGRA.getTileOfDim(j, i)
                    tile1 = paramCGRA.getTileOfDim(j-1, i+1)
                    link0 = ParamLink(tile0, tile1, PORT_NORTHWEST, PORT_SOUTHEAST)
                    link1 = ParamLink(tile1, tile0, PORT_SOUTHEAST, PORT_NORTHWEST)
                    paramCGRA.addLink(link0)
                    paramCGRA.addLink(link1)

                if i < ROWS-1:
                    # vertical
                    tile0 = paramCGRA.getTileOfDim(j, i)
                    tile1 = paramCGRA.getTileOfDim(j, i+1)
                    link0 = ParamLink(tile0, tile1, PORT_NORTH, PORT_SOUTH)
                    link1 = ParamLink(tile1, tile0, PORT_SOUTH, PORT_NORTH)
                    paramCGRA.addLink(link0)
                    paramCGRA.addLink(link1)

                if j == 0:
                    # connect to memory
                    tile0 = paramCGRA.getTileOfDim(j, i)
                    link0 = ParamLink(tile0, None, PORT_WEST, i, LINK_TO_MEM)
                    link1 = ParamLink(None, tile0, i, PORT_WEST, LINK_FROM_MEM)
                    paramCGRA.addLink(link0)
                    paramCGRA.addLink(link1)


    # draw links
    for link in paramCGRA.links:
        if link.disabled:
            pass
        else:
            srcX, srcY = link.getSrcXY()
            dstX, dstY = link.getDstXY()
            canvas.create_line(srcX, srcY, dstX, dstY, arrow=tkinter.LAST)
 

def place_fu_options(master):
    fuCount = len(fuTypeList)
    for i in range(len(fuTypeList)):
        fuVar = tkinter.IntVar()
        fuCheckVars[fuTypeList[i]] = fuVar
        fuCheckbutton = tkinter.Checkbutton(master, variable=fuVar, text=fuTypeList[i], command=partial(clickFuCheckbutton, fuTypeList[i]))
        fuCheckbuttons[fuTypeList[i]] = fuCheckbutton
        fuCheckbutton.select()
        paramCGRA.updateFuCheckbutton(fuTypeList[i], fuVar.get())
        fuCheckbutton.grid(row=i//4, column=i%4, padx=3, pady=3, sticky="W")
        
def place_xbar_options(master):
    for i in range(PORT_DIRECTION_COUNTS):
        xbarVar = tkinter.IntVar()
        xbarCheckVars[xbarTypeList[i]] = xbarVar
        xbarCheckbutton = tkinter.Checkbutton(master, variable=xbarVar, text=xbarTypeList[i], command=partial(clickXbarCheckbutton, xbarTypeList[i]))
        xbarCheckbuttons[xbarTypeList[i]] = xbarCheckbutton
        xbarCheckbutton.select()
        paramCGRA.updateXbarCheckbutton(xbarTypeList[i], xbarVar.get())
        xbarCheckbutton.grid(row=i//4, column=i%4, padx=BORDER, pady=BORDER, sticky="W")
                
def create_param_pannel(master, x, width, height):
    paramPannel = tkinter.LabelFrame(master, text='Configuration', bd=BORDER, relief='groove')
    paramPannel.place(height=height, width=width, x=x, y=INTERVAL)
    
    paramPannel.columnconfigure(0, weight=3)
    paramPannel.columnconfigure(1, weight=1)
    paramPannel.columnconfigure(2, weight=100)
    paramPannel.columnconfigure(3, weight=1)
    paramPannel.columnconfigure(4, weight=100)

    rowsLabel = tkinter.Label(paramPannel, text='Rows & Columns:' )
    rowsLabel.grid(columnspan=2, row=0, column=0, sticky=tkinter.W, padx=BORDER, pady=BORDER)
    rowsEntry = tkinter.Entry(paramPannel, justify=tkinter.CENTER)
    rowsEntry.grid(row=0, column=2, sticky=tkinter.W, padx=BORDER, pady=BORDER)
    rowsEntry.insert(0, str(paramCGRA.rows))
    widgets["rowsEntry"] = rowsEntry
    
    xLabel = tkinter.Label(paramPannel, text='&')
    xLabel.grid(row=0, column=3, sticky=tkinter.W, padx=BORDER, pady=BORDER)
 
    # columnsLabel = tkinter.Label(paramPannel, text='Columns:')
    # columnsLabel.grid(row=0, column=2, sticky=tkinter.E, padx=BORDER, pady=BORDER)
    columnsEntry = tkinter.Entry(paramPannel, justify=tkinter.CENTER)
    columnsEntry.grid(row=0, column=4, sticky=tkinter.W, padx=BORDER, pady=BORDER)
    columnsEntry.insert(0, str(paramCGRA.columns))
    widgets["columnsEntry"] = columnsEntry
    
    configMemLabel = ttk.Label(paramPannel, text='Config Memory (entries/tile):')
    configMemLabel.grid(columnspan=4, row=1, column=0, sticky=tkinter.W, padx=BORDER, pady=BORDER)
    configMemEntry = ttk.Entry(paramPannel, justify=tkinter.CENTER)
    configMemEntry.grid(row=1, column=4, sticky=tkinter.W, padx=BORDER, pady=BORDER)
    configMemEntry.insert(0, paramCGRA.configMem)
    widgets["configMemEntry"] = configMemEntry
    
    dataMemLabel = ttk.Label(paramPannel, text='Data SPM (KBs):')
    dataMemLabel.grid(columnspan=2, row=2, column=0, padx=BORDER, pady=BORDER, sticky=tkinter.W)
    dataMemEntry = ttk.Entry(paramPannel, justify=tkinter.CENTER)
    dataMemEntry.grid(row=2, column=2, sticky=tkinter.W, padx=BORDER, pady=BORDER)
    dataMemEntry.insert(0, str(paramCGRA.dataMem))
    widgets["dataMemEntry"] = dataMemEntry
       
    updateButton = tkinter.Button(paramPannel, text = "Update", relief='raised', command = partial(clickUpdate, master))
    updateButton.grid(columnspan=2, row=2, column=3, sticky=tkinter.W, padx=BORDER)

    # entireTileCheckVar = tkinter.IntVar()
    entireTileCheckVar.set(0)
    entireTileCheckbutton = tkinter.Checkbutton(paramPannel, variable=entireTileCheckVar, text="Disable the entire Tile 0", command=clickEntireTileCheckbutton)
    # entireTileCheckbutton.select()
    # paramCGRA.updateEntireTileCheckbutton(fuTypeList[i], fuVar.get())
    entireTileCheckbutton.grid(columnspan=5, row=3, column=0, padx=BORDER, pady=BORDER, sticky="E")
    widgets["entireTileCheckbutton"] = entireTileCheckbutton

    fuConfigPannel = tkinter.LabelFrame(paramPannel, text='Tile 0 functional units', bd = BORDER, relief='groove')
    # fuConfigPannel.config(text='xxx')
    fuConfigPannel.grid(columnspan=5, row=4, column=0, padx=BORDER, pady=BORDER)
    widgets["fuConfigPannel"] = fuConfigPannel
    
    place_fu_options(fuConfigPannel)
    
    xbarConfigPannel = tkinter.LabelFrame(paramPannel, text='Tile 0 crossbar outgoing links', bd = BORDER, relief='groove')
    # xbarConfigPannel.config(text='y')
    xbarConfigPannel.grid(columnspan=5, row=5, column=0, padx=BORDER, pady=BORDER)
    widgets["xbarConfigPannel"] = xbarConfigPannel
    
    place_xbar_options(xbarConfigPannel)   


def create_test_pannel(master, x, width, height):
    testPannel = tkinter.LabelFrame(master, text='Verification', bd = BORDER, relief='groove')
    testPannel.place(height=height, width=width, x=x, y=INTERVAL)
    testButton = tkinter.Button(testPannel, text = "Run tests", relief='raised', command = clickTest)
    testButton.grid(row=0, column=0, sticky=tkinter.W, padx=BORDER, pady=BORDER//2)
    testProgress = ttk.Progressbar(testPannel, orient='horizontal', mode='determinate', length=width/2.5)
    testProgress['value'] = 0
    widgets["testProgress"] = testProgress
    testProgress.grid(row=0, column=1, padx=BORDER, pady=BORDER//2)
    testShow = tkinter.Label(testPannel, text = " IDLE", fg='gray')
    widgets["testShow"] = testShow
    testShow.grid(row=0, column=2, sticky=tkinter.E, padx=BORDER, pady=BORDER//2)

def create_verilog_pannel(master, x, y, width, height):
    verilogPannel = tkinter.LabelFrame(master, text='SVerilog', bd = BORDER, relief='groove')
    verilogPannel.place(height=height, width=width, x=x, y=y)
    
    verilogText = tkinter.Text(verilogPannel, bd = BORDER, relief='groove')
    widgets["verilogText"] = verilogText
    verilogText.place(height=height-8*BORDER-40, width=width-4*BORDER, x=BORDER, y=BORDER)
    
    generateButton = tkinter.Button(verilogPannel, text="Generate", relief='raised', command=clickGenerateVerilog)
    generateButton.place(x=width-4*BORDER-90, y=height-8*BORDER-30)
 
    
def create_report_pannel(master, x, y, width):
    reportPannel = tkinter.LabelFrame(master, text='Report area/power', bd = BORDER, relief='groove')
    reportPannel.place(width=width, x=x, y=y)
    reportButton = tkinter.Button(reportPannel, text = "Synthesize", relief='raised', command = helloCallBack)
    reportButton.grid(row=0, column=0, sticky=tkinter.W, padx=BORDER, pady=BORDER//2)
    reportProgress = ttk.Progressbar(reportPannel, orient='horizontal', mode='determinate', length=width/1.7)
    reportProgress['value'] = 30
    reportProgress.grid(columnspan=3, row=0, column=1, padx=BORDER, pady=BORDER//2)
    
    reportTileAreaLabel = tkinter.Label(reportPannel, text = "Area of tiles:")
    reportTileAreaLabel.grid(row=1, column=0, sticky=tkinter.E, padx=BORDER, pady=BORDER//2)
    reportTileAreaData = tkinter.Label(reportPannel, text = "0")
    reportTileAreaData.grid(row=1, column=1, sticky=tkinter.E, padx=BORDER, pady=BORDER//2)
    reportTilePowerLabel = tkinter.Label(reportPannel, text = "Power of tiles:")
    reportTilePowerLabel.grid(row=1, column=2, sticky=tkinter.E, padx=BORDER, pady=BORDER//2)
    reportTilePowerData = tkinter.Label(reportPannel, text = "0")
    reportTilePowerData.grid(row=1, column=3, sticky=tkinter.E, padx=BORDER, pady=BORDER//2)
    
    reportSPMAreaLabel = tkinter.Label(reportPannel, text = "Area of SPM:")
    reportSPMAreaLabel.grid(row=2, column=0, sticky=tkinter.E, padx=BORDER, pady=BORDER//2)
    reportSPMAreaData = tkinter.Label(reportPannel, text = "0")
    reportSPMAreaData.grid(row=2, column=1, sticky=tkinter.E, padx=BORDER, pady=BORDER//2)
    reportSPMPowerLabel = tkinter.Label(reportPannel, text = "Power of SPM:")
    reportSPMPowerLabel.grid(row=2, column=2, sticky=tkinter.E, padx=BORDER, pady=BORDER//2)
    reportSPMPowerData = tkinter.Label(reportPannel, text = "0")
    reportSPMPowerData.grid(row=2, column=3, sticky=tkinter.E, padx=BORDER, pady=BORDER//2)
    
    
def create_layout_pannel(master, x, width, height):
    layoutPannel = tkinter.LabelFrame(master, text='Layout', bd = BORDER, relief='groove')
    layoutPannel.place(height=height, width=width, x=x, y=INTERVAL)
    showButton = tkinter.Button(layoutPannel, text = "Show layout", relief='raised', command = helloCallBack)
    showButton.pack()
    X = tkinter.Label(layoutPannel, text = 'layout figure is coming soon...', fg = 'black')
    X.pack()


def create_kernel_pannel(master, x, y, width, height):
    kernelPannel = tkinter.LabelFrame(master, text='Kernel', bd = BORDER, relief='groove')
    kernelPannel.place(height=height+3, width=width, x=x, y=y)

    selectKernelButton = tkinter.Button(kernelPannel, text='Select', fg='black', command=clickSelectKernel)
    selectKernelButton.grid(row=0, column=0, sticky=tkinter.W, padx=BORDER, pady=BORDER//2)

    kernelPathLabel = tkinter.Entry(kernelPannel, fg="black")
    widgets["kernelPathLabel"] = kernelPathLabel
    kernelPathLabel.insert(0, targetKernelName)
    kernelPathLabel.configure(state="disabled")
    kernelPathLabel.grid(row=0, column=1, sticky=tkinter.W, padx=BORDER, pady=BORDER//2)

    # chooseKernelShow = tkinter.Label(kernelPannel, text = u'\u2713', fg='green')
    # chooseKernelShow.place(height=20, width=200)
    # chooseKernelShow.grid(row=0, column=3, sticky=tkinter.W, padx=BORDER, pady=BORDER//2)

    compileKernelButton = tkinter.Button(kernelPannel, text = "Compile", fg="black", command=clickCompileKernel)
    compileKernelButton.grid(row=0, column=2, sticky=tkinter.W, padx=BORDER, pady=BORDER//2)

    compileKernelShow = tkinter.Label(kernelPannel, text=u'\u2713', fg='green')
    compileKernelShow.grid(row=0, column=3, sticky=tkinter.W, padx=BORDER, pady=BORDER//2)

    mapDFGButton = tkinter.Button(kernelPannel, text="Map", fg="black", command = partial(clickMapDFG, II))
    mapDFGButton.grid(row=0, column=4, sticky=tkinter.E, padx=BORDER, pady=BORDER//2)

    dfgPannel = tkinter.LabelFrame(kernelPannel, text='Data-Flow Graph', fg="black", bd=BORDER, relief='groove')
    dfgHeight = height-40-4*BORDER
    dfgWidth = width-4*BORDER
    dfgPannel.place(height=dfgHeight, width=dfgWidth, x=BORDER, y=30+BORDER)
    # dfgPannel.grid(columnspan=4, row=2, column=0, sticky=tkinter.W, padx=BORDER, pady=BORDER//2)
    PIL_image = Image.open("../CGRA-Mapper/test/kernel.png")
    PIL_image_small = PIL_image.resize((dfgWidth-10,dfgHeight-25), Image.Resampling.LANCZOS)
    dfgImage = ImageTk.PhotoImage(PIL_image_small)
    # dfgImage = ImageTk.PhotoImage(PIL_image)
    images["dfgImage"] = dfgImage # This is important due to the garbage collection would remove local variable of image
    dfgLabel = tkinter.Label(dfgPannel, image=dfgImage)
    dfgLabel.pack()

    # X = tkinter.Label(kernelPannel, text = 'Kernel input is coming soon...', fg = 'black')
    # X.pack()
                

def create_mapping_pannel(root, x, y, width):

    # GRID_WIDTH = (TILE_SIZE+LINK_LENGTH) * COLS - linkLength
    TILE_WIDTH = (GRID_WIDTH + LINK_LENGTH) / COLS - LINK_LENGTH
    TILE_HEIGHT = (GRID_HEIGHT + LINK_LENGTH) / ROWS - LINK_LENGTH

    frame = tkinter.LabelFrame(root, text="Mapping", bd=BORDER, relief='groove', width=width, height=GRID_HEIGHT+20)
    frame.place(x=x, y=y)
    # frame.pack(expand=True, fill=tkinter.BOTH) #.grid(row=0,column=0)

    cgraWidth = GRID_WIDTH + MEM_WIDTH + LINK_LENGTH + 20
    mappingCanvas = tkinter.Canvas(frame, height=GRID_HEIGHT+20, width=width, scrollregion=(0,0,cgraWidth, GRID_HEIGHT))
    widgets["mappingCanvas"] = mappingCanvas

    hbar=tkinter.Scrollbar(frame, orient=tkinter.HORIZONTAL, bd=BORDER/4, relief='groove')
    hbar.pack(side=tkinter.BOTTOM, fill=tkinter.X, expand=0)
    hbar.config(command=mappingCanvas.xview)
    mappingCanvas.config(width=width, height=GRID_HEIGHT+20)
    mappingCanvas.config(xscrollcommand=hbar.set)
    mappingCanvas.pack(side=tkinter.LEFT, expand=True, fill=tkinter.BOTH)


create_cgra_pannel(master, ROWS, COLS)

paramPadPosX = GRID_WIDTH + MEM_WIDTH + LINK_LENGTH + INTERVAL * 3
paramPadWidth = 270
create_param_pannel(master, paramPadPosX, paramPadWidth, GRID_HEIGHT)

scriptPadPosX = paramPadPosX + paramPadWidth + INTERVAL
scriptPadWidth = 300

create_test_pannel(master, scriptPadPosX, scriptPadWidth, GRID_HEIGHT//4-30)

create_verilog_pannel(master, scriptPadPosX, GRID_HEIGHT//4-10, scriptPadWidth, GRID_HEIGHT//2-10)

create_report_pannel(master, scriptPadPosX, GRID_HEIGHT*3//4-10, scriptPadWidth)

layoutPadPosX = scriptPadPosX + scriptPadWidth + INTERVAL
layoutPadWidth = 300
create_layout_pannel(master, layoutPadPosX, layoutPadWidth, GRID_HEIGHT)

totalWidth = layoutPadPosX + layoutPadWidth

create_kernel_pannel(master, INTERVAL, GRID_HEIGHT+INTERVAL*2, paramPadPosX-20, GRID_HEIGHT+55)

create_mapping_pannel(master, paramPadPosX, GRID_HEIGHT+INTERVAL*2, totalWidth-paramPadPosX-5)

master.geometry(str(layoutPadPosX+layoutPadWidth+INTERVAL)+"x"+str(GRID_HEIGHT*2+INTERVAL*3+50))

master.mainloop()
