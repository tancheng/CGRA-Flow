import sys
import os
import time
import subprocess
import tkinter
import tkinter.messagebox
from tkinter import ttk
from tkinter import filedialog as fd
from PIL import Image, ImageTk
from functools import partial

from VectorCGRA.cgra.translate.CGRATemplateRTL_test import *

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
CONFIG_MEM_SIZE = 8
DATA_MEM_SIZE = 4
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

xbarPort2Type = {}
xbarPort2Type[PORT_WEST      ] = "W"
xbarPort2Type[PORT_EAST      ] = "E"
xbarPort2Type[PORT_NORTH     ] = "N"
xbarPort2Type[PORT_SOUTH     ] = "S"
xbarPort2Type[PORT_NORTHEAST ] = "NE"
xbarPort2Type[PORT_NORTHWEST ] = "NW"
xbarPort2Type[PORT_SOUTHEAST ] = "SE"
xbarPort2Type[PORT_SOUTHWEST ] = "SW"

xbarPortOpposites = {}
xbarPortOpposites[PORT_WEST     ] = PORT_EAST
xbarPortOpposites[PORT_EAST     ] = PORT_WEST
xbarPortOpposites[PORT_NORTH    ] = PORT_SOUTH
xbarPortOpposites[PORT_SOUTH    ] = PORT_NORTH
xbarPortOpposites[PORT_NORTHWEST] = PORT_SOUTHEAST
xbarPortOpposites[PORT_NORTHEAST] = PORT_SOUTHWEST
xbarPortOpposites[PORT_SOUTHWEST] = PORT_NORTHEAST
xbarPortOpposites[PORT_SOUTHEAST] = PORT_NORTHWEST

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
        s.neverUsedOutPorts = set()
        s.fuDict = {}
        s.xbarDict = {}
        for i in range( PORT_DIRECTION_COUNTS ):
            s.neverUsedOutPorts.add(i)
        
        for xbarType in xbarTypeList:
            s.xbarDict[xbarType] = 0

        for fuType in fuTypeList:
            s.fuDict[fuType] = 1

    def hasFromMem(s):
        for link in s.inLinks.values():
            if not link.disabled and link.isFromMem():
                return True
        return False

    def hasToMem(s):
        for link in s.outLinks.values():
            if not link.disabled and link.isToMem():
                return True
        return False

    def getInvalidInPorts(s):
        invalidInPorts = set()
        for port in range(PORT_DIRECTION_COUNTS):
            if port not in s.inLinks:
                invalidInPorts.add(port)
                continue
            link = s.inLinks[port]
            if link.disabled or type(link.srcTile) == ParamSPM or link.srcTile.disabled:
                invalidInPorts.add(port)
                continue
        return invalidInPorts

    def isDefaultFus(s):
        for fuType in fuTypeList:
            if s.fuDict[fuType] != 1:
                return False
        return True

    def getAllValidFuTypes(s):
        fuTypes = set()
        for fuType in fuTypeList:
            if s.fuDict[fuType] == 1:
                if fuType == "Ld" or fuType == "St":
                    fuTypes.add("Ld")
                else:
                    fuTypes.add(fuType)
        return list(fuTypes)

    def getInvalidOutPorts(s):
        invalidOutPorts = set()
        for port in range(PORT_DIRECTION_COUNTS):
            if port not in s.outLinks:
                invalidOutPorts.add(port)
                continue
            link = s.outLinks[port]
            if link.disabled or type(link.dstTile) == ParamSPM or link.dstTile.disabled:
                invalidOutPorts.add(port)
                continue
        return invalidOutPorts

    def reset(s):
        s.disabled = False

        for i in range(PORT_DIRECTION_COUNTS):
            s.neverUsedOutPorts.add(i)
 
        for xbarType in xbarTypeList:
            s.xbarDict[xbarType] = 0

        for fuType in fuTypeList:
            s.fuDict[fuType] = 1

    def resetOutLink(s, portType, link):
        s.outLinks[portType] = link
        s.xbarDict[xbarPort2Type[portType]] = 1
        if portType in s.neverUsedOutPorts:
            s.neverUsedOutPorts.remove(portType)

    def resetInLink(s, portType, link):
        s.inLinks[portType] = link
    
    def setOutLink(s, portType, link):
        s.outLinks[portType] = link

    def setInLink(s, portType, link):
        s.resetInLink(portType, link)

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

    def getDimXY(s):
        return s.dimX, s.dimY
 
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


class ParamSPM:
    def __init__(s, posX, numOfReadPorts, numOfWritePorts):
        s.posX = posX
        s.ID = -1
        s.numOfReadPorts = numOfReadPorts
        s.numOfWritePorts = numOfWritePorts
        s.disabled = False
        s.inLinks = {}
        s.outLinks = {}

    def getNumOfValidReadPorts(s):
        ports = 0
        for physicalPort in range(s.numOfReadPorts):
            if physicalPort not in s.inLinks:
                continue
            if s.inLinks[physicalPort].disabled:
                continue
            ports += 1
        return ports

    def getNumOfValidWritePorts(s):
        ports = 0
        for physicalPort in range(s.numOfWritePorts):
            if physicalPort not in s.outLinks:
                continue
            if s.outLinks[physicalPort].disabled:
                continue
            ports += 1
        return ports

    def getValidReadPort(s, logicalPort):
        port = 0
        for physicalPort in range(logicalPort+1):
            if physicalPort not in s.inLinks:
                continue
            if s.inLinks[physicalPort].disabled:
                continue
            if physicalPort == logicalPort:
                return port
            port += 1
        return -1

    def getValidWritePort(s, logicalPort):
        port = 0
        for physicalPort in range(logicalPort+1):
            if physicalPort not in s.outLinks:
                continue
            if s.outLinks[physicalPort].disabled:
                continue
            if physicalPort == logicalPort:
                return port
            port += 1
        return -1

    def getPosX(s):
        return s.posX

    def setInLink(s, portType, link):
        s.inLinks[portType] = link

    def resetInLink(s, portType, link):
        s.setInLink(portType, link)
 
    def setOutLink(s, portType, link):
        s.outLinks[portType] = link

    def resetOutLink(s, portType, link):
        s.setOutLink(portType, link)

class ParamLink:
    def __init__(s, srcTile, dstTile, srcPort, dstPort):
        s.srcTile = srcTile
        s.dstTile = dstTile
        s.srcPort = srcPort
        s.dstPort = dstPort
        s.disabled = False
        s.srcTile.resetOutLink(s.srcPort, s)
        s.dstTile.resetInLink(s.dstPort, s)

    def getMemReadPort(s):
        if s.isFromMem():
            spm = s.srcTile
            return spm.getValidReadPort(s.srcPort)
        return -1

    def getMemWritePort(s):
        if s.isToMem():
            spm = s.dstTile
            return spm.getValidWritePort(s.dstPort)
        return -1

    def isToMem(s):
        return type(s.dstTile) == ParamSPM

    def isFromMem(s):
        return type(s.srcTile) == ParamSPM

    def getSrcXY(s, baseX=0, baseY=0):
        if type(s.srcTile) != ParamSPM:
            return s.srcTile.getPosXYOnPort(s.srcPort, baseX, baseY)
        else:
            dstPosX, dstPosY = s.dstTile.getPosXYOnPort(s.dstPort, baseX, baseY)
            spmPosX = s.srcTile.getPosX()
            return spmPosX, dstPosY

    def getDstXY(s, baseX=0, baseY=0):
        if type(s.dstTile) != ParamSPM:
            return s.dstTile.getPosXYOnPort(s.dstPort, baseX, baseY)
        else:
            srcPosX, srcPosY = s.srcTile.getPosXYOnPort(s.srcPort, baseX, baseY)
            spmPosX = s.dstTile.getPosX()
            return spmPosX, srcPosY


class ParamCGRA:
    def __init__(s, rows, columns, configMemSize=CONFIG_MEM_SIZE, dataMemSize=DATA_MEM_SIZE):
        s.rows = rows
        s.columns = columns
        s.configMemSize = configMemSize
        s.dataMemSize = dataMemSize
        s.tiles = []
        s.templateLinks = []
        s.updatedLinks = []
        s.targetTileID = 0
        s.dataSPM = None

    # return error message if the model is not valid
    def getErrorMessage(s):
        # at least one tile can perform mem acess
        memExist = False
        # at least one tile exists
        tileExist = False
        for tile in s.tiles:
            if not tile.disabled:
                tileExist = True
                # a tile contains at least one FU
                fuExist = False
                # the tile connect to mem need to able to access mem
                memTileValid = False

                for fuType in fuTypeList:
                    if (fuType == "Ld" or fuType == "St") and (tile.hasToMem() or tile.hasFromMem()):
                        memTileValid = True if tile.fuDict[fuType] == 1 else False
                        if not memTileValid:
                            return "Tile " + str(tile.ID) + " needs to contain the Load/Store functional units."
                        memExist = True
                    else:
                        memTileValid = True
                    if tile.fuDict[fuType] == 1:
                        fuExist = True
                if not fuExist:
                    return "At least one functional unit needs to exist in tile " + str(tile.ID) + "."

        if not tileExist:
            return "At least one tile needs to exist in the CGRA."

        if not memExist:
            return "At least one tile including a Load/Store functional unit needs to directly connect to the data SPM."

        return ""

    def getValidTiles(s):
        validTiles = []
        for tile in s.tiles:
            if not tile.disabled:
                validTiles.append(tile)
        return validTiles

    def getValidLinks(s):
        validLinks = []
        for link in s.updatedLinks:
            if not link.disabled and not link.srcTile.disabled and not link.dstTile.disabled:
                validLinks.append(link)
        return validLinks

    def updateFuXbarPannel(s):
        targetTile = s.getTileOfID(s.targetTileID)
        for fuType in fuTypeList:
            if fuType in fuCheckVars:
                fuCheckVars[fuType].set(targetTile.fuDict[fuType])

        for xbarType in xbarTypeList:
            if xbarType in xbarCheckVars:
                xbarCheckVars[xbarType].set(targetTile.xbarDict[xbarType])

    def initDataSPM(s, dataSPM):
        s.dataSPM = dataSPM

    def updateMemSize(s, configMemSize, dataMemSize):
        s.configMemSize = configMemSize
        s.dataMemSize = dataMemSize

    def initTiles(s, tiles):
        for r in range(s.rows):
            for c in range(s.columns):
                s.tiles.append(tiles[r][c])

    def addTile(s, tile):
        s.tiles.append(tile)

    def initTemplateLinks(s, links):
        numOfLinks = s.rows*s.columns*2 + (s.rows-1)*s.columns*2 + (s.rows-1)*(s.columns-1)*2*2

        for link in links:
            s.templateLinks.append(link)

    def resetTiles(s):

        for tile in s.tiles:
            tile.reset()

            for fuType in fuTypeList:
                fuCheckVars[fuType].set(tile.fuDict[fuType])
                fuCheckbuttons[fuType].configure(state="normal")
    
            for xbarType in xbarTypeList:
                xbarCheckVars[xbarType].set(tile.xbarDict[xbarType])
                xbarCheckbuttons[xbarType].configure(state="normal")


    def enableAllTemplateLinks(s):
        for link in s.templateLinks:
            link.disabled = False

    def resetLinks(s):
        for link in s.templateLinks:
            link.disabled = False
            link.srcTile.resetOutLink(link.srcPort, link)
            link.dstTile.resetInLink(link.dstPort, link)

        s.updatedLinks = s.templateLinks[:]

        for portType in range( PORT_DIRECTION_COUNTS ):
            if portType in s.getTileOfID(s.targetTileID).neverUsedOutPorts:
                xbarCheckbuttons[xbarPort2Type[portType]].configure(state="disabled")

    def addTemplateLink(s, link):
        s.templateLinks.append(link)

    def addUpdatedLink(s, link):
        s.updatedLinks.append(link)

    def removeUpdatedLink(s, link):
        s.updatedLinks.remove(link)
        # src = link.srcTile
        # src.xbarDict[link.srcPort] = 0

    def updateFuCheckbutton(s, fuType, value):
        tile = s.getTileOfID(s.targetTileID)
        tile.fuDict[fuType] = value

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


    # tiles could be disabled due to the disabled links
    def updateTiles(s):
        unreachableTiles = set()
        for tile in s.tiles:
            unreachableTiles.add(tile)

        for link in s.updatedLinks:
            if link.disabled == False and type(link.dstTile) == ParamTile:
                if link.dstTile in unreachableTiles:
                    unreachableTiles.remove(link.dstTile)
                    if len(unreachableTiles) == 0:
                        break

        for tile in unreachableTiles:
            tile.disabled = True


    # TODO: also need to consider adding back after removing...
    def updateLinks(s):

        needRemoveLinks = set()
        for link in s.updatedLinks:
            if link.disabled:
                needRemoveLinks.add((link.srcTile, link.dstTile))

        for link in s.templateLinks:
            link.srcTile.setOutLink(link.srcPort, link)
            link.dstTile.setInLink(link.dstPort, link)
        s.updatedLinks = s.templateLinks[:]

        for tile in s.tiles:
            if tile.disabled:
                for portType in tile.outLinks:
                    outLink = tile.outLinks[portType]
                    dstNeiTile = outLink.dstTile
                    oppositePort = xbarPortOpposites[portType]
                    if oppositePort in tile.inLinks:
                        inLink = tile.inLinks[oppositePort]
                        srcNeiTile = inLink.srcTile

                        # some links can be fused as single one due to disabled tiles
                        if not inLink.disabled and not outLink.disabled and inLink in s.updatedLinks and outLink in s.updatedLinks:
                            updatedLink = ParamLink(srcNeiTile, dstNeiTile, inLink.srcPort, outLink.dstPort)
                            s.addUpdatedLink(updatedLink)
                            s.removeUpdatedLink(inLink)
                            s.removeUpdatedLink(outLink)
                        # links that are disabled need to be removed
                        if inLink.disabled and inLink in s.updatedLinks:
                            s.removeUpdatedLink(inLink)
                        if outLink.disabled and outLink in s.updatedLinks:
                            s.removeUpdatedLink(outLink)

                    else:
                        if outLink in s.updatedLinks:
                            s.removeUpdatedLink(outLink)

                for portType in tile.outLinks:
                    outLink = tile.outLinks[portType]
                    if outLink in s.updatedLinks:
                        s.removeUpdatedLink(outLink)


                for portType in tile.inLinks:
                    inLink = tile.inLinks[portType]
                    if inLink in s.updatedLinks:
                        s.removeUpdatedLink(inLink)

        for link in s.updatedLinks:
            if (link.srcTile, link.dstTile) in needRemoveLinks:
                link.disabled = True
                if type(link.srcTile) == ParamTile:
                    link.srcTile.xbarDict[xbarPort2Type[link.srcPort]] = 0


paramCGRA = ParamCGRA(ROWS, COLS, CONFIG_MEM_SIZE, DATA_MEM_SIZE)
targetKernelName = "not selected yet"

def clickGenerateVerilog():

    message = paramCGRA.getErrorMessage()
    if message != "":
        tkinter.messagebox.showerror(title="CGRA Model Checking", message=message)
        return

    os.system("mkdir verilog")
    os.chdir("verilog")

    test_cgra_universal(paramCGRA)

    widgets["verilogText"].delete("1.0", tkinter.END)
    found = False
    print(os.listdir("./"))
    for fileName in os.listdir("./"):
        if "__" in fileName and ".v" in fileName:
            print("Found the file: ", fileName)
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
    widgets["xbarConfigPannel"].config(text='Tile '+str(ID)+' crossbar outgoing links')
    widgets["xbarConfigPannel"].grid(columnspan=5, row=5, column=0, padx=BORDER, pady=BORDER)
    widgets["entireTileCheckbutton"].config(text='Disable entire Tile '+str(ID), state="normal")
    widgets["spmConfigPannel"].grid_forget()
    paramCGRA.targetTileID = ID

    disabled = paramCGRA.getTileOfID(ID).disabled
    for fuType in fuTypeList:
        fuCheckVars[fuType].set(paramCGRA.tiles[ID].fuDict[fuType])
        fuCheckbuttons[fuType].configure(state="disabled" if disabled else "normal")

    for xbarType in xbarTypeList:
        xbarCheckVars[xbarType].set(paramCGRA.tiles[ID].xbarDict[xbarType])
        xbarCheckbuttons[xbarType].configure(state="disabled" if disabled or xbarType2Port[xbarType] in paramCGRA.tiles[ID].neverUsedOutPorts else "normal")

    entireTileCheckVar.set(1 if paramCGRA.getTileOfID(ID).disabled else 0)
 

def clickSPM():
    widgets["fuConfigPannel"].config(text='Tile '+str(paramCGRA.targetTileID)+' functional units')

    for fuType in fuTypeList:
        fuCheckVars[fuType].set(paramCGRA.tiles[paramCGRA.targetTileID].fuDict[fuType])
        fuCheckbuttons[fuType].configure(state="disabled")

    widgets["xbarConfigPannel"].grid_forget()

    spmConfigPannel = widgets["spmConfigPannel"]
    spmConfigPannel.config(text='DataSPM outgoing links')
    spmConfigPannel.grid(columnspan=5, row=5, column=0, padx=BORDER, pady=BORDER)

    spmEnabledListbox = widgets["spmEnabledListbox"]
    spmDisabledListbox = widgets["spmDisabledListbox"]

    widgets["entireTileCheckbutton"].config(text='Disable entire Tile '+str(paramCGRA.targetTileID), state="disabled")


def clickSPMPortDisable():
    spmEnabledListbox = widgets["spmEnabledListbox"]
    portIndex = spmEnabledListbox.curselection()
    if portIndex:
        port = spmEnabledListbox.get(portIndex)
        spmEnabledListbox.delete(portIndex)
        widgets["spmDisabledListbox"].insert(0, port)

        link = paramCGRA.dataSPM.outLinks[port]
        link.disabled = True

def clickSPMPortEnable():
    spmDisabledListbox = widgets["spmDisabledListbox"]
    portIndex = spmDisabledListbox.curselection()
    if portIndex:
        port = spmDisabledListbox.get(portIndex)
        spmDisabledListbox.delete(portIndex)

        widgets["spmEnabledListbox"].insert(0, port)

        link = paramCGRA.dataSPM.outLinks[port]
        link.disabled = False


def clickEntireTileCheckbutton():

    if entireTileCheckVar.get() == 1:

        for fuType in fuTypeList:
            fuCheckVars[fuType].set(0)
            tile = paramCGRA.getTileOfID(paramCGRA.targetTileID)
            tile.fuDict[fuType] = 0
            # clickFuCheckbutton(fuType)
            fuCheckbuttons[fuType].configure(state="disabled")

        paramCGRA.getTileOfID(paramCGRA.targetTileID).disabled = True
    else:
        for fuType in fuTypeList:
            fuCheckVars[fuType].set(0)
            tile = paramCGRA.getTileOfID(paramCGRA.targetTileID)
            tile.fuDict[fuType] = 0
            # clickFuCheckbutton(fuType)
            fuCheckbuttons[fuType].configure(state="normal")

        # paramCGRA.getTileOfID(paramCGRA.targetTileID).disabled = False


def clickFuCheckbutton(fuType):
    if fuType == "Ld":
        fuCheckVars["St"].set(fuCheckVars["Ld"].get())
        paramCGRA.updateFuCheckbutton("St", fuCheckVars["St"].get())
    elif fuType == "St":
        fuCheckVars["Ld"].set(fuCheckVars["St"].get())
        paramCGRA.updateFuCheckbutton("Ld", fuCheckVars["Ld"].get())
    paramCGRA.updateFuCheckbutton(fuType, fuCheckVars[fuType].get())

def clickXbarCheckbutton(xbarType):
    paramCGRA.updateXbarCheckbutton(xbarType, xbarCheckVars[xbarType].get())
    

def clickUpdate(root):
    rows = int(widgets["rowsEntry"].get())
    columns = int(widgets["columnsEntry"].get())
    configMemSize = int(widgets["configMemEntry"].get())
    dataMemSize = int(widgets["dataMemEntry"].get())

    global paramCGRA

    if paramCGRA.rows != rows or paramCGRA.columns != columns:
        paramCGRA = ParamCGRA(rows, columns)

    paramCGRA.updateMemSize(configMemSize, dataMemSize)
    paramCGRA.updateTiles()
    paramCGRA.updateLinks()

    create_cgra_pannel(root, rows, columns)

    widgets["verilogText"].delete("1.0", tkinter.END)

def clickReset(root):
    rows = int(widgets["rowsEntry"].get())
    columns = int(widgets["columnsEntry"].get())
    configMemSize = int(widgets["configMemEntry"].get())
    dataMemSize = int(widgets["dataMemEntry"].get())

    global paramCGRA

    if paramCGRA.rows != rows or paramCGRA.columns != columns:
        paramCGRA = ParamCGRA(rows, columns)

    paramCGRA.updateMemSize(configMemSize, dataMemSize)
    paramCGRA.resetTiles()
    paramCGRA.enableAllTemplateLinks()
    paramCGRA.resetLinks()

    create_cgra_pannel(root, rows, columns)

    for _ in range(paramCGRA.rows):
        widgets["spmEnabledListbox"].delete(0)
        widgets["spmDisabledListbox"].delete(0)

    for port in paramCGRA.dataSPM.outLinks:
        if not paramCGRA.dataSPM.outLinks[port].disabled:
            widgets["spmEnabledListbox"].insert(0, port)
        else:
            widgets["spmDisabledListbox"].insert(0, port)


def clickTest():
    # need to provide the paths for lib.so and kernel.bc
    os.system("mkdir test")
    # os.system("cd test")
    os.chdir("test")

    widgets["testShow"].configure(text="0%", fg="red")
    master.update_idletasks()

    # os.system("pytest ../../VectorCGRA")
    testProc = subprocess.Popen(["pytest ../../VectorCGRA", '-u'], stdout=subprocess.PIPE, shell=True, bufsize=1)
    failed = 0
    total = 0
    with testProc.stdout:
        for line in iter(testProc.stdout.readline, b''):
            outputLine = line.decode("utf-8")
            print(outputLine)
            if "%]" in outputLine:
                value = int(outputLine.split("[")[1].split("%]")[0])
                widgets["testProgress"].configure(value=value)
                widgets["testShow"].configure(text=str(value)+"%", fg="red")
                master.update_idletasks()
                total += 1
                if ".py F" in outputLine:
                    failed += 1

    widgets["testShow"].configure(text="PASSED" if failed==0 else str(total-failed)+"/"+str(total), fg="green")
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
        for link in paramCGRA.updatedLinks:
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

    # construct data memory
    if paramCGRA.dataSPM == None:
        dataSPM = ParamSPM(MEM_WIDTH, rows, rows)
        paramCGRA.initDataSPM(dataSPM)

    # draw data memory
    memHeight = GRID_HEIGHT
    button = tkinter.Button(canvas, text = "Data\nSPM", fg = 'black', bg = 'gray', relief = 'raised', bd = BORDER, command = clickSPM)
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
        # if tile.disabled:
            # button = tkinter.Button(canvas, text = "Tile "+str(tile.ID), fg='gray', relief='flat', bd=BORDER, command=partial(clickTile, tile.ID))
        if not tile.disabled:
            button = tkinter.Button(canvas, text = "Tile "+str(tile.ID), fg='black', bg='gray', relief='raised', bd=BORDER, command=partial(clickTile, tile.ID))

            posX, posY = tile.getPosXY()
            button.place(height=TILE_HEIGHT, width=TILE_WIDTH, x = posX, y = posY)


    # construct links
    if len(paramCGRA.templateLinks) == 0:
        for i in range(ROWS):
            for j in range(COLS):
                if j < COLS-1:
                    # horizontal
                    tile0 = paramCGRA.getTileOfDim(j, i)
                    tile1 = paramCGRA.getTileOfDim(j+1, i)
                    link0 = ParamLink(tile0, tile1, PORT_EAST, PORT_WEST)
                    link1 = ParamLink(tile1, tile0, PORT_WEST, PORT_EAST)
                    paramCGRA.addTemplateLink(link0)
                    paramCGRA.addTemplateLink(link1)

                if i < ROWS-1 and j < COLS-1:
                    # diagonal left bottom to right top
                    tile0 = paramCGRA.getTileOfDim(j, i)
                    tile1 = paramCGRA.getTileOfDim(j+1, i+1)
                    link0 = ParamLink(tile0, tile1, PORT_NORTHEAST, PORT_SOUTHWEST)
                    link1 = ParamLink(tile1, tile0, PORT_SOUTHWEST, PORT_NORTHEAST)
                    paramCGRA.addTemplateLink(link0)
                    paramCGRA.addTemplateLink(link1)

                if i < ROWS-1 and j > 0:
                    # diagonal left top to right bottom
                    tile0 = paramCGRA.getTileOfDim(j, i)
                    tile1 = paramCGRA.getTileOfDim(j-1, i+1)
                    link0 = ParamLink(tile0, tile1, PORT_NORTHWEST, PORT_SOUTHEAST)
                    link1 = ParamLink(tile1, tile0, PORT_SOUTHEAST, PORT_NORTHWEST)
                    paramCGRA.addTemplateLink(link0)
                    paramCGRA.addTemplateLink(link1)

                if i < ROWS-1:
                    # vertical
                    tile0 = paramCGRA.getTileOfDim(j, i)
                    tile1 = paramCGRA.getTileOfDim(j, i+1)
                    link0 = ParamLink(tile0, tile1, PORT_NORTH, PORT_SOUTH)
                    link1 = ParamLink(tile1, tile0, PORT_SOUTH, PORT_NORTH)
                    paramCGRA.addTemplateLink(link0)
                    paramCGRA.addTemplateLink(link1)

                if j == 0:
                    # connect to memory
                    tile0 = paramCGRA.getTileOfDim(j, i)
                    link0 = ParamLink(tile0, paramCGRA.dataSPM, PORT_WEST, i)
                    link1 = ParamLink(paramCGRA.dataSPM, tile0, i, PORT_WEST)
                    paramCGRA.addTemplateLink(link0)
                    paramCGRA.addTemplateLink(link1)


    paramCGRA.updateLinks()
    paramCGRA.updateFuXbarPannel()

    # draw links
    for link in paramCGRA.updatedLinks:
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
        portType = i
        xbarType = xbarPort2Type[i]
        xbarVar = tkinter.IntVar()
        xbarCheckVars[xbarType] = xbarVar
        xbarCheckbutton = tkinter.Checkbutton(master, variable=xbarVar, text=xbarType, command=partial(clickXbarCheckbutton, xbarType))
        xbarCheckbuttons[xbarType] = xbarCheckbutton

        if paramCGRA.getTileOfID(0).xbarDict[xbarType] == 1:
            xbarCheckbutton.select()

        paramCGRA.updateXbarCheckbutton(xbarType, xbarVar.get())

        if portType in paramCGRA.getTileOfID(0).neverUsedOutPorts:
            xbarCheckbutton.configure(state="disabled")

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
    configMemEntry.insert(0, paramCGRA.configMemSize)
    widgets["configMemEntry"] = configMemEntry
    
    dataMemLabel = ttk.Label(paramPannel, text='Data SPM (KBs):')
    dataMemLabel.grid(columnspan=2, row=2, column=0, padx=BORDER, pady=BORDER, sticky=tkinter.W)
    dataMemEntry = ttk.Entry(paramPannel, justify=tkinter.CENTER)
    dataMemEntry.grid(row=2, column=2, sticky=tkinter.W, padx=BORDER, pady=BORDER)
    dataMemEntry.insert(0, str(paramCGRA.dataMemSize))
    widgets["dataMemEntry"] = dataMemEntry
       
    updateButton = tkinter.Button(paramPannel, text = " Reset ", relief='raised', command = partial(clickReset, master))
    updateButton.grid(columnspan=2, row=2, column=3, sticky=tkinter.W, padx=BORDER)

    # entireTileCheckVar = tkinter.IntVar()
    entireTileCheckVar.set(0)
    entireTileCheckbutton = tkinter.Checkbutton(paramPannel, variable=entireTileCheckVar, text="Disable entire Tile 0", command=clickEntireTileCheckbutton)
    # entireTileCheckbutton.select()
    # paramCGRA.updateEntireTileCheckbutton(fuTypeList[i], fuVar.get())
    entireTileCheckbutton.grid(columnspan=3, row=3, column=0, padx=BORDER, pady=BORDER, sticky="W")
    widgets["entireTileCheckbutton"] = entireTileCheckbutton

    resetButton = tkinter.Button(paramPannel, text = "Update", relief='raised', command = partial(clickUpdate, master))
    resetButton.grid(columnspan=2, row=3, column=3, sticky=tkinter.W, padx=BORDER)

    fuConfigPannel = tkinter.LabelFrame(paramPannel, text='Tile 0 functional units', bd = BORDER, relief='groove')
    # fuConfigPannel.config(text='xxx')
    fuConfigPannel.grid(columnspan=5, row=4, column=0, padx=BORDER, pady=BORDER)
    widgets["fuConfigPannel"] = fuConfigPannel
    
    place_fu_options(fuConfigPannel)
    
    xbarConfigPannel = tkinter.LabelFrame(paramPannel, text='Tile 0 crossbar outgoing links', bd=BORDER, relief='groove')
    # xbarConfigPannel.config(text='y')
    xbarConfigPannel.grid(columnspan=5, row=5, column=0, padx=BORDER, pady=BORDER)
    # xbarConfigPannel.config(width=width-30, height=80)
    widgets["xbarConfigPannel"] = xbarConfigPannel
    
    place_xbar_options(xbarConfigPannel)   

    spmConfigPannel = tkinter.LabelFrame(paramPannel, text='Data SPM outgoing links', bd=BORDER, relief='groove')
    spmConfigPannel.config(width=225, height=85)
    # xbarConfigPannel.config(text='y')
    widgets["spmConfigPannel"] = spmConfigPannel

    spmEnabledOutVar = tkinter.IntVar()
    spmDisabledOutVar = tkinter.IntVar()

    spmEnabledLabel = tkinter.Label(spmConfigPannel)
    spmDisabledLabel = tkinter.Label(spmConfigPannel)

    spmEnabledScrollbar = tkinter.Scrollbar(spmEnabledLabel)
    spmDisabledScrollbar = tkinter.Scrollbar(spmDisabledLabel)

    spmEnabledListbox = tkinter.Listbox(spmEnabledLabel, listvariable=spmEnabledOutVar)
    spmDisabledListbox = tkinter.Listbox(spmDisabledLabel, listvariable=spmDisabledOutVar)

    widgets["spmEnabledListbox"] = spmEnabledListbox
    widgets["spmDisabledListbox"] = spmDisabledListbox

    spmDisableButton = tkinter.Button(spmConfigPannel, text="Disable", relief='raised', command=clickSPMPortDisable)
    spmEnableButton = tkinter.Button(spmConfigPannel, text="Enable", relief='raised', command=clickSPMPortEnable)

    spmEnabledScrollbar.config(command=spmEnabledListbox.yview)
    spmEnabledListbox.config(yscrollcommand=spmEnabledScrollbar.set)
    spmDisabledScrollbar.config(command=spmDisabledListbox.yview)
    spmDisabledListbox.config(yscrollcommand=spmDisabledScrollbar.set)

    # spmEnabledLabel.config(width=50, height=80)
    spmEnabledListbox.config(width=50, height=50)
    # spmEnabledListbox.place(x=BORDER, y=BORDER, width=0, height=20)
    # spmEnabledLabel.grid(rowspan=2, row=0, column=0)
    spmEnabledLabel.place(x=0, y=0, width=50, height=60)

    spmEnabledScrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
    spmEnabledListbox.pack()

    # spmDisableButton.grid(row=0, column=1)
    # spmEnableButton.grid(row=1, column=1)
    spmDisableArrow0 = tkinter.Label(spmConfigPannel, text="=>")
    spmDisableArrow1 = tkinter.Label(spmConfigPannel, text="=>")
    spmEnableArrow0 = tkinter.Label(spmConfigPannel, text="<=")
    spmEnableArrow1 = tkinter.Label(spmConfigPannel, text="<=")

    spmDisableArrow0.place(x=55, y=BORDER, width=20, height=25)
    spmDisableButton.place(x=80, y=BORDER, width=60, height=25)
    spmDisableArrow1.place(x=145, y=BORDER, width=20, height=25)

    spmEnableArrow0.place(x=55, y=BORDER+30, width=20, height=25)
    spmEnableButton.place(x=80, y=BORDER+30, width=60, height=25)
    spmEnableArrow1.place(x=145, y=BORDER+30, width=20, height=25)

    # spmEnableButton.pack()

    # spmDisableButton.place(x=30, y=30, width=20, height=20)
    # spmEnableButton.place(x=30, y=60, width=20, height=20)

    # spmDisabledListbox.place(x=50, y=BORDER, width=0, height=20)
    # spmDisabledLabel.config(width=50, height=80)
    spmDisabledListbox.config(width=50, height=50)
    spmDisabledLabel.place(x=165, y=0, width=50, height=60)
    # spmDisabledLabel.grid(rowspan=2, row=0, column=2)

    spmDisabledScrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
    spmDisabledListbox.pack()

    # enabledPorts = [ i for i in range(paramCGRA.dataSPM.ports)]
    # enabledPorts.reverse()

    spmEnabledListbox.delete(0)
    spmDisabledListbox.delete(0)
    for port in paramCGRA.dataSPM.outLinks:
        if not paramCGRA.dataSPM.outLinks[port].disabled:
            spmEnabledListbox.insert(0, port)
        else:
            spmDisabledListbox.insert(0, port)


def create_test_pannel(master, x, width, height):
    testPannel = tkinter.LabelFrame(master, text='Verification', bd = BORDER, relief='groove')
    testPannel.place(height=height, width=width, x=x, y=INTERVAL)
    testButton = tkinter.Button(testPannel, text = "Run tests", relief='raised', command = clickTest)
    testButton.grid(row=0, column=0, sticky=tkinter.W, padx=BORDER, pady=BORDER//2)
    testProgress = ttk.Progressbar(testPannel, orient='horizontal', mode='determinate', length=width/2.5)
    testProgress['value'] = 0
    widgets["testProgress"] = testProgress
    testProgress.grid(row=0, column=1, padx=BORDER, pady=BORDER//2)
    testShow = tkinter.Label(testPannel, text = "  IDLE ", fg='gray')
    widgets["testShow"] = testShow
    testShow.grid(row=0, column=2, padx=BORDER, pady=BORDER//2)

def create_verilog_pannel(master, x, y, width, height):
    verilogPannel = tkinter.LabelFrame(master, text='SVerilog', bd = BORDER, relief='groove')
    verilogPannel.place(height=height, width=width, x=x, y=y)

    verilogFrame = tkinter.Frame(verilogPannel, bd=BORDER, relief="groove")
    verilogFrame.place(height=height-8*BORDER-40, width=width-4*BORDER, x=BORDER, y=BORDER)

    verilogScroll=tkinter.Scrollbar(verilogFrame, orient='vertical')
    verilogScroll.pack(side=tkinter.RIGHT, fill='y')

    # verilogText = tkinter.Text(verilogPannel, bd = BORDER, relief='groove', yscrollcommand=v.set)
    verilogText = tkinter.Text(verilogFrame, yscrollcommand=verilogScroll.set)
    verilogScroll.config(command=verilogText.yview)
    widgets["verilogText"] = verilogText
    verilogText.pack()

    generateVerilogButton = tkinter.Button(verilogPannel, text="Generate", relief='raised', command=clickGenerateVerilog)
    generateVerilogButton.place(x=width-4*BORDER-90, y=height-8*BORDER-30)
 
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

    selectKernelButton = tkinter.Button(kernelPannel, text='Select app', fg='black', command=clickSelectKernel)
    selectKernelButton.grid(row=0, column=0, sticky=tkinter.W, padx=BORDER, pady=BORDER//2)

    kernelPathLabel = tkinter.Entry(kernelPannel, fg="black")
    widgets["kernelPathLabel"] = kernelPathLabel
    kernelPathLabel.insert(0, targetKernelName)
    kernelPathLabel.configure(state="disabled")
    kernelPathLabel.grid(columnspan=2, row=0, column=1, sticky=tkinter.W, padx=BORDER, pady=BORDER//2)

    # chooseKernelShow = tkinter.Label(kernelPannel, text = u'\u2713', fg='green')
    # chooseKernelShow.place(height=20, width=200)
    # chooseKernelShow.grid(row=0, column=3, sticky=tkinter.W, padx=BORDER, pady=BORDER//2)

    compileKernelButton = tkinter.Button(kernelPannel, text = "  Compile  ", fg="black", command=clickCompileKernel)
    compileKernelButton.grid(row=0, column=3, sticky=tkinter.W, padx=BORDER, pady=BORDER//2)

    compileKernelShow = tkinter.Label(kernelPannel, text=u'  \u2713\u2713\u2713', fg='green')
    compileKernelShow.grid(row=0, column=4, sticky=tkinter.W, padx=BORDER, pady=BORDER//2)

    kernelNameLabel = tkinter.Label(kernelPannel, text=" Kernel name:", fg='black')
    kernelNameLabel.grid(row=1, column=0, sticky=tkinter.W, padx=BORDER, pady=BORDER//2)

    kernelNameEntry= tkinter.Entry(kernelPannel, fg="black")
    widgets["kernelNameEntry"] = kernelNameEntry
    kernelNameEntry.grid(columnspan=2, row=1, column=1, sticky=tkinter.W, padx=BORDER, pady=BORDER//2)

    generateDFGButton = tkinter.Button(kernelPannel, text = "Show DFG ", fg="black", command=clickGenerateDFG)
    generateDFGButton.grid(row=1, column=3, sticky=tkinter.W, padx=BORDER, pady=BORDER//2)

    mapDFGButton = tkinter.Button(kernelPannel, text="Map", fg="black", command = partial(clickMapDFG, II))
    mapDFGButton.grid(row=1, column=4, sticky=tkinter.E, padx=BORDER, pady=BORDER//2)

    dfgPannel = tkinter.LabelFrame(kernelPannel, text='Data-Flow Graph', fg="black", bd=BORDER, relief='groove')
    dfgHeight = height-80-4*BORDER
    dfgWidth = width-4*BORDER
    dfgPannel.place(height=dfgHeight, width=dfgWidth, x=BORDER, y=70+BORDER)
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
