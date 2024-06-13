import sys
import os
import time
import threading
import subprocess
import json
import math
import tkinter
import tkinter.messagebox
from tkinter import ttk
from tkinter import filedialog as fd
from PIL import Image, ImageTk, ImageFile
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
TILE_HEIGHT = 70
TILE_WIDTH = 70
LINK_LENGTH = 40
INTERVAL = 10
BORDER = 4
ROWS = 4
COLS = 4
GRID_WIDTH = (TILE_WIDTH+LINK_LENGTH) * COLS - LINK_LENGTH
GRID_HEIGHT = (TILE_HEIGHT+LINK_LENGTH) * ROWS - LINK_LENGTH
MEM_WIDTH = 50
CONFIG_MEM_SIZE = 8
DATA_MEM_SIZE = 4
def window_size(window, width, height):
    window.geometry(f"{width}x{height}")
master = tkinter.Tk()
master.title("CGRA-Flow: An Integrated End-to-End Framework for CGRA Exploration, Compilation, and Development")


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
mappingAlgoCheckVar = tkinter.IntVar()
fuCheckVars = {}
fuCheckbuttons = {}
xbarCheckVars = {}
xbarCheckbuttons = {}
kernelOptions = tkinter.StringVar()
kernelOptions.set("Not selected yet")
synthesisRunning = False

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
        s.mapping = {}

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
        s.mapping = {}

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

    def getPosX(s, baseX):
        return s.posX + baseX

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
        s.mapping = set()

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
            spmPosX = s.srcTile.getPosX(baseX)
            return spmPosX, dstPosY

    def getDstXY(s, baseX=0, baseY=0):
        if type(s.dstTile) != ParamSPM:
            return s.dstTile.getPosXYOnPort(s.dstPort, baseX, baseY)
        else:
            srcPosX, srcPosY = s.srcTile.getPosXYOnPort(s.srcPort, baseX, baseY)
            spmPosX = s.dstTile.getPosX(baseX)
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
        s.targetAppName = "   Not selected yet"
        s.compilationDone = False
        s.verilogDone = False
        s.targetKernels = []
        s.targetKernelName = None
        s.DFGNodeCount = -1
        s.resMII = -1
        s.recMII = -1

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
                if tile.hasToMem() or tile.hasFromMem():
                    # for now, the compiler doesn't support seperate read or write, both of them need to locate in the same tile
                    if tile.hasToMem() and tile.hasFromMem() and tile.fuDict["Ld"] == 1 and tile.fuDict["St"] == 1:
                        memExist = True
                    else:
                        return "Tile " + str(tile.ID) + " needs to contain the Load/Store functional units."

                for fuType in fuTypeList:
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
            link.mapping = set()

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

    def getUpdatedLink(s, srcTile, dstTile):
        for link in s.updatedLinks:
            if link.srcTile == srcTile and link.dstTile == dstTile:
                return link
        return None

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



class ToolTip(object):

    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def showtip(self, text):
        "Display text in tooltip window"
        self.text = text
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 57
        y = y + cy + self.widget.winfo_rooty() +27
        self.tipwindow = tw = tkinter.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tkinter.Label(tw, text=self.text, justify=tkinter.LEFT,
                              background="#ffffe0", relief=tkinter.SOLID, borderwidth=1,
                              font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

def CreateToolTip(widget, text):
    toolTip = ToolTip(widget)
    def enter(event):
        toolTip.showtip(text)
    def leave(event):
        toolTip.hidetip()
    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)


paramCGRA = ParamCGRA(ROWS, COLS, CONFIG_MEM_SIZE, DATA_MEM_SIZE)



def clickTile(ID):
    widgets["fuConfigPannel"].config(text='Tile '+str(ID)+' functional units')
    widgets["xbarConfigPannel"].config(text='Tile '+str(ID)+' crossbar outgoing links')
    # After clicking the tile, the pannel will fill all directions
    widgets["xbarConfigPannel"].grid(columnspan=4, row=7, column=0, rowspan=2, sticky="nsew")
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
    # After clicking the SPM, the pannel will fill all directions
    spmConfigPannel.grid(row=7, column=0, rowspan=2, columnspan=4, sticky="nsew")

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
    oldCGRA = paramCGRA

    if paramCGRA.rows != rows or paramCGRA.columns != columns:
        paramCGRA = ParamCGRA(rows, columns)

    create_cgra_pannel(root, rows, columns)

    # kernel related information and be kept to avoid redundant compilation
    paramCGRA.updateMemSize(configMemSize, dataMemSize)
    paramCGRA.updateTiles()
    paramCGRA.updateLinks()
    paramCGRA.targetAppName = oldCGRA.targetAppName
    paramCGRA.compilationDone = oldCGRA.compilationDone
    paramCGRA.targetKernels = oldCGRA.targetKernels
    paramCGRA.targetKernelName = oldCGRA.targetKernelName
    paramCGRA.DFGNodeCount = oldCGRA.DFGNodeCount
    paramCGRA.recMII = oldCGRA.recMII
    paramCGRA.verilogDone = False

    widgets["verilogText"].delete("1.0", tkinter.END)
    widgets["resMIIEntry"].delete(0, tkinter.END)
    if len(paramCGRA.getValidTiles()) > 0 and paramCGRA.DFGNodeCount > 0:
        paramCGRA.resMII = math.ceil((paramCGRA.DFGNodeCount+0.0)/len(paramCGRA.getValidTiles())) // 1
        widgets["resMIIEntry"].insert(0, paramCGRA.resMII)
    else:
        widgets["resMIIEntry"].insert(0, 0)


def clickReset(root):
    rows = int(widgets["rowsEntry"].get())
    columns = int(widgets["columnsEntry"].get())
    configMemSize = int(widgets["configMemEntry"].get())
    dataMemSize = int(widgets["dataMemEntry"].get())

    global paramCGRA
    oldCGRA = paramCGRA

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

    # kernel related information and be kept to avoid redundant compilation
    paramCGRA.targetAppName = oldCGRA.targetAppName
    paramCGRA.compilationDone = oldCGRA.compilationDone
    paramCGRA.targetKernels = oldCGRA.targetKernels
    paramCGRA.targetKernelName = oldCGRA.targetKernelName
    paramCGRA.DFGNodeCount = oldCGRA.DFGNodeCount
    paramCGRA.recMII = oldCGRA.recMII

    widgets["verilogText"].delete(0, tkinter.END)
    widgets["resMIIEntry"].delete(0, tkinter.END)
    if len(paramCGRA.getValidTiles()) > 0 and paramCGRA.DFGNodeCount > 0:
        paramCGRA.resMII = math.ceil((paramCGRA.DFGNodeCount+0.0)/len(paramCGRA.getValidTiles())) // 1
        widgets["resMIIEntry"].insert(0, paramCGRA.resMII)
    else:
        widgets["resMIIEntry"].insert(0, 0)


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
            outputLine = line.decode("ISO-8859-1")
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


def clickGenerateVerilog():

    message = paramCGRA.getErrorMessage()
    if message != "":
        tkinter.messagebox.showerror(title="CGRA Model Checking", message=message)
        return

    os.system("mkdir verilog")
    os.chdir("verilog")

    # pymtl function that is used to generate synthesizable verilog
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

    paramCGRA.verilogDone = True
    if not found:
        paramCGRA.verilogDone = False
        widgets["verilogText"].insert(tkinter.END, "Error exists during Verilog generation")

    os.system("mv CGRATemplateRTL__*.v design.v")
    # os.system("rename s/\.v/\.log/g *")

    os.chdir("..")


def setReportProgress(value):
    widgets["reportProgress"].configure(value=value)

def countSynthesisTime():
    global synthesisRunning
    timeCost = 0.0
    while synthesisRunning:
        time.sleep(0.1)
        widgets["synthesisTimeEntry"].delete(0, tkinter.END)
        widgets["synthesisTimeEntry"].insert(0, round(timeCost, 1))
        timeCost += 0.1

def runYosys():
    global synthesisRunning
    os.system("make 3")

    statsFile = open("3-open-yosys-synthesis/stats.txt", 'r')
    statsLines = statsFile.readlines()
      
    tileArea = 0.0
    for line in statsLines:
        if "Chip area for module " in line:
            tileArea = round(float(line.split(": ")[1]) / 1000000, 2)
            break

    statsFile.close()

    widgets["reportTileAreaData"].delete(0, tkinter.END)
    widgets["reportTileAreaData"].insert(0, tileArea)

    widgets["reportTilePowerData"].delete(0, tkinter.END)
    widgets["reportTilePowerData"].insert(0, "-")

    widgets["reportProgress"].configure(value=100)

    os.chdir("../../../build")

    synthesisRunning = False


def clickSynthesize():

    global paramCGRA
    global synthesisRunning

    if synthesisRunning:
        return

    if not paramCGRA.verilogDone:
        tkinter.messagebox.showerror(title="Sythesis", message="The verilog generation needs to be done first.")
        return

    synthesisRunning = True
    synthesisTimerRun = threading.Thread(target=countSynthesisTime)
    synthesisTimerRun.start()

    os.system("mkdir verilog")
    os.chdir("verilog")

    # Cacti SPM power/area estimation:
    sizePattern = "[SPM_SIZE]"
    readPortPattern = "[READ_PORT_COUNT]"
    writePortPattern = "[WRITE_PORT_COUNT]"
      
    updatedSizePattern = str(paramCGRA.dataMemSize * 1024)
    updatedReadPortPattern = str(paramCGRA.dataSPM.getNumOfValidReadPorts())
    updatedWritePortPattern = str(paramCGRA.dataSPM.getNumOfValidWritePorts())
      
    with open(r'../../tools/cacti/spm_template.cfg', 'r') as file:
        data = file.read()

        data = data.replace(sizePattern, updatedSizePattern)
        data = data.replace(readPortPattern, updatedReadPortPattern)
        data = data.replace(writePortPattern, updatedWritePortPattern)
      
    with open(r'../../tools/cacti/spm_temp.cfg', 'w') as file:
        file.write(data)

    os.chdir("../../tools/cacti")

    cactiCommand = "./cacti -infile spm_temp.cfg"
    cactiProc = subprocess.Popen([cactiCommand, '-u'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, bufsize=1)
    (out, err) = cactiProc.communicate()
    success = False
    line = out.decode("ISO-8859-1")

    if "Power Components:" in line:
        success = True
        strSPMPower = line.split("Data array: Total dynamic read energy/access  (nJ): ")[1].split("\n")[0]
        strSPMTiming = line.split("Data side (with Output driver) (ns): ")[1].split("\n")[0]
        spmPower = float(strSPMPower) / float(strSPMTiming) * 1000

        widgets["reportSPMPowerData"].delete(0, tkinter.END)
        widgets["reportSPMPowerData"].insert(0, str(spmPower))

        strSPMArea = line.split("Data array: Area (mm2): ")[1].split("\n")[0]
        spmArea = float(strSPMArea)

        widgets["reportSPMAreaData"].delete(0, tkinter.END)
        widgets["reportSPMAreaData"].insert(0, str(spmArea))


    else:
        tkinter.messagebox.showerror(title="Sythesis", message="Execution of Cacti failed.")

    progress = threading.Thread(target=setReportProgress, args=[20])
    progress.start()

    os.chdir("../../build/verilog")
    # mflowgen synthesis:
    os.system("../../tools/sv2v/bin/sv2v design.v > design_sv2v.v")
    progress = threading.Thread(target=setReportProgress, args=[40])
    progress.start()

    os.system("sed -i 's/CGRATemplateRTL__.*/CGRATemplateRTL (/g' design_sv2v.v")
    progress = threading.Thread(target=setReportProgress, args=[50])
    progress.start()

    # os.system("mv design.v ../../mflowgen1/designs/cgra/rtl/outputs/design.v")
    os.system("cp design_sv2v.v ../../tools/mflowgen/designs/cgra/rtl/outputs/design.v")
    os.chdir("../../tools/mflowgen")
    os.system("mkdir ./build")
    os.chdir("./build")
    os.system("rm -r ./*")
    os.system("mflowgen run --design ../designs/cgra")

    os.system("make 2")
    progress = threading.Thread(target=setReportProgress, args=[70])
    progress.start()

    yosysRun = threading.Thread(target=runYosys)
    yosysRun.start()


def clickSelectApp(event):
    global paramCGRA
    paramCGRA.compilationDone = False 
    appName = fd.askopenfilename(title="choose an application", initialdir="../", filetypes=(("C/C++ file", "*.cpp"), ("C/C++ file", "*.c"), ("C/C++ file", "*.C"), ("C/C++ file", "*.CPP")))
    paramCGRA.targetAppName = appName

    # widgets["appPathEntry"].configure(state="normal")
    widgets["appPathEntry"].delete(0, tkinter.END)
    widgets["appPathEntry"].insert(0, paramCGRA.targetAppName)
    # widgets["appPathEntry"].configure(state="disabled")

    widgets["compileAppShow"].config(text="IDLE", fg='grey')

def clickCompileApp():
    global paramCGRA
    fileName = paramCGRA.targetAppName
    if not fileName or fileName == "   Not selected yet":
        return

    os.system("mkdir kernel")
    os.chdir("kernel")

    compileCommand = "clang-12 -emit-llvm -fno-unroll-loops -O3 -o kernel.bc -c " + fileName
    compileProc = subprocess.Popen([compileCommand, '-u'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    (compileOut, compileErr) = compileProc.communicate()

    disassembleCommand = "llvm-dis-12 kernel.bc -o kernel.ll"
    disassembleProc = subprocess.Popen([disassembleCommand, '-u'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    (disassembleOut, disassembleErr) = disassembleProc.communicate()

    if compileErr:
        widgets["compileAppShow"].config(text=u'\u2717\u2717\u2717', fg='red')
        os.chdir("..")
        print("Compile error message: ", compileErr)
        return
    if disassembleErr:
        widgets["compileAppShow"].config(text=u'\u2717\u2717\u2717', fg='red')
        os.chdir("..")
        print("Disassemble error message: ", disassembleErr)
        return
    
    widgets["compileAppShow"].config(text=u'\u2713\u2713\u2713', fg='green')
    paramCGRA.compilationDone = True

    # collect the potentially targeting kernel/function
    irFile = open('kernel.ll', 'r')
    irLines = irFile.readlines()
      
    # Strips the newline character
    paramCGRA.targetKernels = []
    for line in irLines:
        if "define " in line and "{" in line and "@" in line:
            funcName = line.split("@")[1].split("(")[0]
            if "main" not in funcName:
                paramCGRA.targetKernels.append(funcName)

    irFile.close()

    kernelNameMenu = widgets["kernelNameMenu"]
    kernelNameMenu["menu"].delete(0, "end")
    for kernelName in paramCGRA.targetKernels: 
        kernelNameMenu["menu"].add_command(label=kernelName, command=tkinter._setit(kernelOptions, kernelName))
    # options.set(my_list[0])

    widgets["generateDFGShow"].config(text="IDLE", fg='grey')

    os.chdir("..")

def clickKernelMenu(*args):
    global paramCGRA
    name = kernelOptions.get()
    if name == None or name == " " or name == "Not selected yet":
        return
    paramCGRA.targetKernelName = name

def dumpParamCGRA2JSON(fileName):
    global paramCGRA
    paramCGRAJson = {}
    paramCGRAJson["tiles"] = {}
    for tile in paramCGRA.tiles:
        curDict = {}
        if tile.disabled:
            curDict["disabled"] = True
        else:
            curDict["disabled"] = False
            if tile.isDefaultFus():
                curDict["supportAllFUs"] = True
            else:
                curDict["supportAllFUs"] = False
                curDict["supportedFUs"] = []
                for fuType in tile.fuDict:
                    if tile.fuDict[fuType] == 1:
                        curDict["supportedFUs"].append(fuType)
            
            if (tile.hasFromMem() and tile.fuDict["Ld"] == 1) and\
               (tile.hasToMem()   and tile.fuDict["St"] == 1):
                curDict["accessMem"] = True

        paramCGRAJson["tiles"][str(tile.ID)] = curDict

    paramCGRAJson["links"] = []
    for link in paramCGRA.updatedLinks:
        curDict = {}
        srcTile = link.srcTile
        dstTile = link.dstTile
        if not link.disabled and not srcTile.disabled and not dstTile.disabled and type(srcTile) != ParamSPM and type(dstTile) != ParamSPM:
            curDict["srcTile"] = srcTile.ID
            curDict["dstTile"] = dstTile.ID
            paramCGRAJson["links"].append(curDict)

    paramCGRAJsonObject = json.dumps(paramCGRAJson, indent=4)
     
    # Writing to sample.json
    with open(fileName, "w") as outfile:
        outfile.write(paramCGRAJsonObject)



def clickShowDFG():
    os.system("mkdir kernel")
    os.chdir("kernel")
    fileExist = os.path.exists("kernel.bc")
    global paramCGRA
    
    if not fileExist or not paramCGRA.compilationDone or paramCGRA.targetKernelName == None:
        os.chdir("..")
        tkinter.messagebox.showerror(title="DFG Generation", message="The compilation and kernel selection need to be done first.")
        return

    paramCGRA.targetKernelName = kernelOptions.get()

    genDFGJson = {
            "kernel"                : paramCGRA.targetKernelName,
            "targetFunction"        : False,
            "targetNested"          : True,
            "targetLoopsID"         : [0],
            "doCGRAMapping"         : False,
            "row"                   : paramCGRA.rows,
            "column"                : paramCGRA.columns,
            "precisionAware"        : False,
            "heterogeneity"         : False,
            "isTrimmedDemo"         : True,
            "heuristicMapping"      : True,
            "parameterizableCGRA"   : True,
            "diagonalVectorization" : False,
            "bypassConstraint"      : 8,
            "isStaticElasticCGRA"   : False,
            "ctrlMemConstraint"     : 200,
            "regConstraint"         : 12,
        }
     
    json_object = json.dumps(genDFGJson, indent=4)
     
    with open("param.json", "w") as outfile:
        outfile.write(json_object)

    dumpParamCGRA2JSON("paramCGRA.json")

    genDFGCommand = "opt-12 -load ../../CGRA-Mapper/build/src/libmapperPass.so -mapperPass ./kernel.bc"
    print("trying to run opt-12")
    genDFGProc = subprocess.Popen([genDFGCommand, "-u"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

    with genDFGProc.stdout:
        for line in iter(genDFGProc.stdout.readline, b''):
            outputLine = line.decode("ISO-8859-1")
            print(outputLine)
            if "DFG node count: " in outputLine:
                paramCGRA.DFGNodeCount = int(outputLine.split("DFG node count: ")[1].split(";")[0])
            if "[RecMII: " in outputLine:
                paramCGRA.recMII = int(outputLine.split("[RecMII: ")[1].split("]")[0])

    (out, err) = genDFGProc.communicate()
    print("opt-12 out: ", out)
    print("opt-12 err: ", err)

    paramCGRA.resMII = math.ceil((paramCGRA.DFGNodeCount+0.0)/len(paramCGRA.getValidTiles())) // 1
    widgets["resMIIEntry"].delete(0, tkinter.END)
    widgets["resMIIEntry"].insert(0, paramCGRA.resMII)

    widgets["recMIIEntry"].delete(0, tkinter.END)
    widgets["recMIIEntry"].insert(0, paramCGRA.recMII)

    convertCommand = "dot -Tpng " + paramCGRA.targetKernelName + ".dot -o kernel.png"
    convertProc = subprocess.Popen([convertCommand, "-u"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    (out, err) = convertProc.communicate()

    PIL_image = Image.open("kernel.png")
    ImageFile.LOAD_TRUNCATED_IMAGES = True
    PIL_image_small = PIL_image.resize((220, 330), Image.Resampling.LANCZOS)
    dfgImage = ImageTk.PhotoImage(PIL_image_small)
    images["dfgImage"] = dfgImage # This is important due to the garbage collection would remove local variable of image
    widgets["dfgLabel"].config(image=dfgImage)

    widgets["generateDFGShow"].config(text=u'\u2713\u2713\u2713', fg='green')
 
    os.chdir("..")

mappingProc = None

def countMapTime():
    global mappingProc
    timeCost = 0.0
    while mappingProc == None or mappingProc.poll() is None:
        time.sleep(0.1)
        widgets["mapTimeEntry"].delete(0, tkinter.END)
        widgets["mapTimeEntry"].insert(0, round(timeCost, 1))
        timeCost += 0.1

def drawSchedule():
    global mappingProc
    mappingCommand = "opt-12 -load ../../CGRA-Mapper/build/src/libmapperPass.so -mapperPass ./kernel.bc"
    mappingProc = subprocess.Popen(["exec " + mappingCommand, '-u'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, bufsize=1)
    (out, err) = mappingProc.communicate()
    success = False
    mappingII = -1
    line = out.decode("ISO-8859-1")
    if "Mapping Success" in line:
        success = True
    if "[Mapping II: " in line:
        strMapII = line.split("[Mapping II: ")[1].split("]")[0]
        mappingII = int(strMapII)

    if not success or mappingII == -1:
        tkinter.messagebox.showerror(title="DFG mapping", message="Mapping failed.")
        os.chdir("..")
        return

    widgets["mapIIEntry"].delete(0, tkinter.END)
    widgets["mapIIEntry"].insert(0, mappingII)
    widgets["mapSpeedupEntry"].delete(0, tkinter.END)
    widgets["mapSpeedupEntry"].insert(0, paramCGRA.DFGNodeCount/mappingII)

    # pad contains tile and links
    tileWidth = paramCGRA.tiles[0].width
    tileHeight = paramCGRA.tiles[0].height
    padWidth = tileWidth + LINK_LENGTH
    padHeight = tileHeight + LINK_LENGTH
    baseX = 0

    # load schedule.json for mapping demonstration
    f = open("schedule.json")
    schedule = json.load(f)
    
    # Iterating through the json
    for strTileID in schedule["tiles"]:
        tileID = int(strTileID)
        tile = paramCGRA.getTileOfID(tileID)
        for strCycle in schedule["tiles"][strTileID]:
            cycle = int(strCycle)
            optID = schedule["tiles"][strTileID][strCycle]
            tile.mapping[cycle] = optID[0]


    for strSrcTileID in schedule["links"]:
        for strDstTileID in schedule["links"][strSrcTileID]:
            srcTile = paramCGRA.getTileOfID(int(strSrcTileID))
            dstTile = paramCGRA.getTileOfID(int(strDstTileID))
            link = paramCGRA.getUpdatedLink(srcTile, dstTile)
            for cycle in schedule["links"][strSrcTileID][strDstTileID]:
                link.mapping.add(cycle)

    f.close()
    os.chdir("..")

    canvas = widgets["mappingCanvas"]
    canvas.delete("all")
    cgraWidth = GRID_WIDTH + MEM_WIDTH + LINK_LENGTH + 20
    canvas.configure(scrollregion=(0, 0, mappingII*cgraWidth, GRID_HEIGHT))
    

    for ii in range(mappingII):
        # draw data memory
        spmLabel = tkinter.Label(canvas, text="Data\nSPM", fg='black', bg='gray', relief='raised', bd=BORDER)
        canvas.create_window(baseX+BORDER, BORDER, window=spmLabel, height=GRID_HEIGHT, width=MEM_WIDTH, anchor="nw")



        # draw tiles
        for tile in paramCGRA.tiles:
            if not tile.disabled:
                button = None
                if ii in tile.mapping:
                    button = tkinter.Label(canvas, text = "Opt "+str(tile.mapping[ii]), fg="black", bg="cornflowerblue", relief="raised", bd=BORDER)
                else:
                    button = tkinter.Label(canvas, text = "Tile "+str(tile.ID), fg="black", bg="grey", relief="raised", bd=BORDER)
                posX, posY = tile.getPosXY(baseX+BORDER, BORDER)
                canvas.create_window(posX, posY, window=button, height=tileHeight, width=tileWidth, anchor="nw")

        # draw links
        for link in paramCGRA.updatedLinks:
            if not link.disabled:
                srcX, srcY = link.getSrcXY(baseX+BORDER, BORDER)
                dstX, dstY = link.getDstXY(baseX+BORDER, BORDER)
                if ii in link.mapping:
                    canvas.create_line(srcX, srcY, dstX, dstY, arrow=tkinter.LAST, fill="red")
                else:
                    canvas.create_line(srcX, srcY, dstX, dstY, arrow=tkinter.LAST, fill="black")
 
        cycleLabel = tkinter.Label(canvas, text="Cycle "+str(ii))
        canvas.create_window(baseX+280, GRID_HEIGHT+10+BORDER, window=cycleLabel, height=20, width=80)

        baseX += GRID_WIDTH + MEM_WIDTH + LINK_LENGTH + 20
        canvas.create_line(baseX-5, INTERVAL, baseX-5, GRID_HEIGHT, width=2, dash=(10,2))

def clickTerminateMapping():
    global mappingProc
    if mappingProc == None:
        return

    if mappingProc.poll() is None:
        mappingProc.kill()

    path = os.getcwd()
    if path.split("\\")[-1] == "kernel":
        os.chdir("..")


def clickMapDFG():
    global mappingProc
    mappingProc = None
    heuristic = mappingAlgoCheckVar.get() == 1

    os.system("mkdir kernel")
    os.chdir("kernel")
    fileExist = os.path.exists("kernel.bc")
    global paramCGRA

    if not fileExist or not paramCGRA.compilationDone or paramCGRA.targetKernelName == None:
        os.chdir("..")
        # tkinter.messagebox.showerror(title="DFG mapping", message="The compilation and kernel selection need to be done first.")
        if not fileExist:
            tkinter.messagebox.showerror(title="DFG mapping", message="The kernel.bc doesn't exist.")
        if not paramCGRA.compilationDone:
            tkinter.messagebox.showerror(title="DFG mapping", message="The compilation needs to be done first.")
        if paramCGRA.targetKernelName == None:
            tkinter.messagebox.showerror(title="DFG mapping", message="The kernel name is not selected yet.")
        return

    mappingJson = {
            "kernel"                : paramCGRA.targetKernelName,
            "targetFunction"        : False,
            "targetNested"          : True,
            "targetLoopsID"         : [0],
            "doCGRAMapping"         : True,
            "row"                   : paramCGRA.rows,
            "column"                : paramCGRA.columns,
            "precisionAware"        : False,
            "heterogeneity"         : False,
            "isTrimmedDemo"         : True,
            "heuristicMapping"      : heuristic,
            "parameterizableCGRA"   : True,
            "diagonalVectorization" : False,
            "bypassConstraint"      : 8,
            "isStaticElasticCGRA"   : False,
            "ctrlMemConstraint"     : paramCGRA.configMemSize,
            "regConstraint"         : 12,
        }
     
    mappingJsonObject = json.dumps(mappingJson, indent=4)
     
    with open("param.json", "w") as outfile:
        outfile.write(mappingJsonObject)

    dumpParamCGRA2JSON("paramCGRA.json")

    mappingCommand = "opt-12 -load ../../CGRA-Mapper/build/src/libmapperPass.so -mapperPass ./kernel.bc"

    widgets["mapTimeEntry"].delete(0, tkinter.END)
    widgets["mapTimeEntry"].insert(0, 0)

    drawer = threading.Thread(target=drawSchedule)
    drawer.start()
    timer = threading.Thread(target=countMapTime)
    timer.start()


def create_cgra_pannel(master, rows, columns):

    ROWS = rows
    COLS = columns
    TILE_WIDTH = (GRID_WIDTH + LINK_LENGTH) / COLS - LINK_LENGTH
    TILE_HEIGHT = (GRID_HEIGHT + LINK_LENGTH) / ROWS - LINK_LENGTH

    cgraPannel = tkinter.LabelFrame(master, text='CGRA', bd=BORDER, relief='groove')
    cgraPannel.grid(row=0, column=0, rowspan=1, columnspan=1, sticky="nsew")
    canvas = tkinter.Canvas(cgraPannel)
    widgets["canvas"] = canvas
    baseX = 0

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
    spmLabel = tkinter.Button(canvas, text = "Data\nSPM", fg = 'black', bg = 'gray', relief = 'raised', bd = BORDER, command = clickSPM)
    # Data memory will be placed in the upper left corner
    canvas.create_window(baseX+BORDER, BORDER, window=spmLabel, height=GRID_HEIGHT, width=MEM_WIDTH, anchor="nw")
            
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
        if not tile.disabled:
            button = tkinter.Button(canvas, text = "Tile "+str(tile.ID), fg='black', bg='gray', relief='raised', bd=BORDER, command=partial(clickTile, tile.ID))
            posX, posY = tile.getPosXY()
            # Tiles will be placed near the Data memory
            canvas.create_window(posX, posY, window=button, height=TILE_HEIGHT, width=TILE_WIDTH, anchor="nw") 


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
    
    canvas.pack(side="top", fill="both", expand=True)
    hbar = tkinter.Scrollbar(cgraPannel, orient="horizontal", command=canvas.xview)
    hbar.pack(side="bottom", fill="x")
    canvas.config(xscrollcommand=hbar.set)
    canvas.config(scrollregion=canvas.bbox("all"))

def place_fu_options(master):
    fuCount = len(fuTypeList)
    for i in range(len(fuTypeList)):
        fuVar = tkinter.IntVar()
        fuCheckVars[fuTypeList[i]] = fuVar
        fuCheckbutton = tkinter.Checkbutton(master, variable=fuVar, text=fuTypeList[i], command=partial(clickFuCheckbutton, fuTypeList[i]))
        fuCheckbuttons[fuTypeList[i]] = fuCheckbutton
        fuCheckbutton.select()
        paramCGRA.updateFuCheckbutton(fuTypeList[i], fuVar.get())
        fuCheckbutton.grid(row=i//4, column=i%4, padx=33, pady=30, sticky="nsew")
        
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

        xbarCheckbutton.grid(row=i//4, column=i%4, padx=33, pady=30, sticky="nsew")



def create_param_pannel(master):
    paramPannel = tkinter.LabelFrame(master, text='Configuration', bd=BORDER, relief='groove')
    paramPannel.grid(row=0, column=1, rowspan=1, columnspan=1, sticky="nsew")

    # Use columnconfigure and rowconfigure to partition the columns, so that each column and row will fill the corresponding space
    # The 'weight' represents the weight of the corresponding row/column length.  
    for i in range(10):
        paramPannel.rowconfigure(i, weight=1)
    for i in range(3):
        paramPannel.columnconfigure(i, weight=1)
    rowsLabel = tkinter.Label(paramPannel, text='Rows  Columns:' )
    rowsLabel.grid(row=0, column=0, sticky=tkinter.W)
    rowsEntry = tkinter.Entry(paramPannel, justify=tkinter.CENTER)
    rowsEntry.grid(row=0, column=1)
    rowsEntry.insert(0, str(paramCGRA.rows))
    widgets["rowsEntry"] = rowsEntry
    columnsEntry = tkinter.Entry(paramPannel, justify=tkinter.CENTER)
    columnsEntry.grid(row=0, column=2)
    columnsEntry.insert(0, str(paramCGRA.columns))
    widgets["columnsEntry"] = columnsEntry
    
    configMemLabel = ttk.Label(paramPannel, text='Config Memory (entries/tile):')
    configMemLabel.grid(columnspan=2, row=1, column=0, sticky=tkinter.W)
    configMemEntry = ttk.Entry(paramPannel, justify=tkinter.CENTER)
    configMemEntry.grid(row=1, column=2)
    configMemEntry.insert(0, paramCGRA.configMemSize)
    widgets["configMemEntry"] = configMemEntry
    
    dataMemLabel = ttk.Label(paramPannel, text='Data SPM (KBs):')
    dataMemLabel.grid(row=2, column=0, sticky=tkinter.W)
    dataMemEntry = ttk.Entry(paramPannel, justify=tkinter.CENTER)
    dataMemEntry.grid(row=2, column=1)
    dataMemEntry.insert(0, str(paramCGRA.dataMemSize))
    widgets["dataMemEntry"] = dataMemEntry   
    updateButton = tkinter.Button(paramPannel, text = " Reset ", relief='raised', command = partial(clickReset, master))
    updateButton.grid(row=2, column=2)

    entireTileCheckVar.set(0)
    entireTileCheckbutton = tkinter.Checkbutton(paramPannel, variable=entireTileCheckVar, text="Disable entire Tile 0", command=clickEntireTileCheckbutton)
    entireTileCheckbutton.grid(columnspan=2, row=3, column=0, sticky="W")
    widgets["entireTileCheckbutton"] = entireTileCheckbutton
    resetButton = tkinter.Button(paramPannel, text = "Update", relief='raised', command = partial(clickUpdate, master))
    resetButton.grid(row=3, column=2)

    fuConfigPannel = tkinter.LabelFrame(paramPannel, text='Tile 0 functional units', bd = BORDER, relief='groove')
    fuConfigPannel.grid(columnspan=4, row=4, column=0, rowspan=3, sticky="nsew")
    widgets["fuConfigPannel"] = fuConfigPannel

    # Use columnconfigure to partition the columns, so that each column fills the corresponding space
    for i in range(4):
        fuConfigPannel.columnconfigure(i, weight=1)  
    place_fu_options(fuConfigPannel)

    xbarConfigPannel = tkinter.LabelFrame(paramPannel, text='Tile 0 crossbar outgoing links', bd=BORDER, relief='groove')
    xbarConfigPannel.grid(columnspan=4, row=7, column=0, rowspan=2, sticky="nsew")
    widgets["xbarConfigPannel"] = xbarConfigPannel

    # Use columnconfigure to partition the columns, so that each column fills the corresponding space
    for i in range(4):
        xbarConfigPannel.columnconfigure(i, weight=1)  
    place_xbar_options(xbarConfigPannel)

    spmConfigPannel = tkinter.LabelFrame(paramPannel, text='Data SPM outgoing links', bd=BORDER, relief='groove')
    spmConfigPannel.grid(row=7, column=0, rowspan=2, columnspan=4, sticky="nsew")
    widgets["spmConfigPannel"] = spmConfigPannel

    # Use columnconfigure and rowconfigure to partition the columns, so that each column and row fills the corresponding space
    for i in range(3):
        spmConfigPannel.rowconfigure(i, weight=1)
    for i in range(5):
        spmConfigPannel.columnconfigure(i, weight=1)
    
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
    spmEnabledLabel.grid(row=0, column=0, rowspan=3, sticky="nsew")

    spmEnabledScrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
    spmEnabledListbox.pack()

    spmDisableArrow0 = tkinter.Label(spmConfigPannel, text="=>")
    spmDisableArrow1 = tkinter.Label(spmConfigPannel, text="=>")
    spmEnableArrow0 = tkinter.Label(spmConfigPannel, text="<=")
    spmEnableArrow1 = tkinter.Label(spmConfigPannel, text="<=")

    spmDisableArrow0.grid(row=0, column=1, sticky="nsew")
    spmDisableButton.grid(row=0, column=2, sticky="nsew")
    spmDisableArrow1.grid(row=0, column=3, sticky="nsew")

    spmEnableArrow0.grid(row=2, column=1, sticky="nsew")
    spmEnableButton.grid(row=2, column=2, sticky="nsew")
    spmEnableArrow1.grid(row=2, column=3, sticky="nsew")

    spmDisabledLabel.grid(row=0, column=4, rowspan=3, sticky="new")

    spmDisabledScrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
    spmDisabledListbox.pack()

    spmEnabledListbox.delete(0)
    spmDisabledListbox.delete(0)
    for port in paramCGRA.dataSPM.outLinks:
        if not paramCGRA.dataSPM.outLinks[port].disabled:
            spmEnabledListbox.insert(0, port)



 

def create_test_pannel(master):
    dataPannel =tkinter.LabelFrame(master)
    dataPannel.grid(row=0, column=2, rowspan=1, columnspan=1, sticky="nsew")
    dataPannel.grid_rowconfigure(0, weight=1)
    dataPannel.grid_rowconfigure(1, weight=2)
    dataPannel.grid_rowconfigure(2, weight=1)
    dataPannel.grid_columnconfigure(0, weight=1)
    dataPannel.grid_columnconfigure(1, weight=1)
    dataPannel.grid_columnconfigure(2, weight=1)
    testPannel = tkinter.LabelFrame(dataPannel, text='Verification', bd=BORDER, relief='groove')
    testPannel.grid(row=0, column=0, rowspan=1, columnspan=3, sticky="nsew")
    testPannel.columnconfigure(0, weight=1)
    testPannel.columnconfigure(1, weight=1)
    testPannel.columnconfigure(2, weight=1) 
    testButton = tkinter.Button(testPannel, text = "Run tests", relief='raised', command = clickTest)
    testButton.grid(row=0, column=0, rowspan=1, columnspan=1, sticky=tkinter.W)
    testProgress = ttk.Progressbar(testPannel, orient='horizontal', mode='determinate')
    testProgress['value'] = 0
    widgets["testProgress"] = testProgress
    testProgress.grid(row=0, column=1, rowspan=1, columnspan=1, sticky="nsew")
    testShow = tkinter.Label(testPannel, text = "  IDLE ", fg='gray')
    widgets["testShow"] = testShow
    testShow.grid(row=0, column=2, sticky=tkinter.E)

    verilogPannel = tkinter.LabelFrame(dataPannel,text="SVerilog",bd=BORDER,relief="groove")
    verilogPannel.grid(row=1, column=0, rowspan=1, columnspan=3, sticky="nsew")
    CreateToolTip(verilogPannel, text = "The code might be too big to be copied,\nthe generated verilog can be found in\nthe 'verilog' folder.")
    generateVerilogButton = tkinter.Button(verilogPannel, text="Generate", relief='raised', command=clickGenerateVerilog)
    generateVerilogButton.pack(side=tkinter.BOTTOM, anchor="sw", padx=BORDER, pady=BORDER)
    verilogScroll = tkinter.Scrollbar(verilogPannel, orient="vertical")
    verilogScroll.pack(side=tkinter.RIGHT, fill="y")
    verilogText = tkinter.Text(verilogPannel, yscrollcommand=verilogScroll.set,width=10,height=5)
    verilogText.pack(side=tkinter.LEFT, fill="both", expand=True)
    verilogScroll.config(command=verilogText.yview)
    widgets["verilogText"] = verilogText
    
    reportPannel = tkinter.LabelFrame(dataPannel,text='Report area/power', bd = BORDER, relief='groove')
    reportPannel.grid(row=2, column=0, rowspan=1, columnspan=3, sticky='nesw')
    reportPannel.columnconfigure(0, weight=1)
    reportPannel.columnconfigure(1, weight=1)
    reportButton = tkinter.Button(reportPannel, text="Synthesize", relief="raised", command=clickSynthesize)

    reportProgress = ttk.Progressbar(reportPannel, orient="horizontal", mode="determinate")
    reportProgress['value'] = 0
    widgets["reportProgress"] = reportProgress

    synthesisTimeEntry = tkinter.Entry(reportPannel, fg="black", justify=tkinter.CENTER)
    widgets["synthesisTimeEntry"] = synthesisTimeEntry

    reportTimecostLabel = tkinter.Label(reportPannel, text = " Time cost")
    CreateToolTip(reportTimecostLabel, text = "Time is in s.")
    
    reportTileAreaLabel = tkinter.Label(reportPannel, text = " Tiles area")
    CreateToolTip(reportTileAreaLabel, text = "Area is in mm^2.")

    reportTileAreaData = tkinter.Entry(reportPannel, justify=tkinter.CENTER)
    widgets["reportTileAreaData"] = reportTileAreaData

    reportTilePowerLabel = tkinter.Label(reportPannel, text = "Tiles power")
    CreateToolTip(reportTilePowerLabel, text = "Yosys is not able to provide\npower estimation.")

    reportTilePowerData = tkinter.Entry(reportPannel, justify=tkinter.CENTER)
    widgets["reportTilePowerData"] = reportTilePowerData

    reportSPMAreaLabel = tkinter.Label(reportPannel, text = " SPM area")
    CreateToolTip(reportSPMAreaLabel, text = "Area is in mm^2.")

    reportSPMAreaData = tkinter.Entry(reportPannel, justify=tkinter.CENTER)
    widgets["reportSPMAreaData"] = reportSPMAreaData

    reportSPMPowerLabel = tkinter.Label(reportPannel, text = "SPM power")
    CreateToolTip(reportSPMPowerLabel, text = "Power is in mW.")

    reportSPMPowerData = tkinter.Entry(reportPannel, justify=tkinter.CENTER)
    widgets["reportSPMPowerData"] = reportSPMPowerData

    reportButton.grid(row=0, column=1)
    reportProgress.grid(row=0, column=0)

    synthesisTimeEntry.grid(row=1, column=0, pady=10)
    reportTimecostLabel.grid(row=1, column=1, pady=10)

    reportTileAreaLabel.grid(row=2, column=1, pady=10)
    reportTileAreaData.grid(row=2, column=0, pady=10)
    reportTilePowerLabel.grid(row=3, column=1, pady=10)
    reportTilePowerData.grid(row=3, column=0, pady=10)

    reportSPMAreaLabel.grid(row=4, column=1, pady=10)
    reportSPMAreaData.grid(row=4, column=0, pady=10)
    reportSPMPowerLabel.grid(row=5, column=1, pady=10)
    reportSPMPowerData.grid(row=5, column=0, pady=10)



def create_layout_pannel(master):
    layoutPannel = tkinter.LabelFrame(master, text='Layout', bd=BORDER, relief='groove')
    layoutPannel.grid(row=0, column=3, rowspan=1, columnspan=1, sticky="nsew")
    canvas = tkinter.Canvas(layoutPannel, bd=0)
    scrollbar = tkinter.Scrollbar(layoutPannel, orient="horizontal", command=canvas.xview)
    scrollbar.pack(side="bottom", fill="x")
    canvas.config(xscrollcommand=scrollbar.set)
    canvas.pack(side="top", fill="both", expand=True)
    layout_frame = tkinter.Frame(canvas)
    canvas.create_window((0, 0), window=layout_frame, anchor="nw")
    showButton = tkinter.Button(layoutPannel, text = "Display layout", relief='raised')
    CreateToolTip(showButton, text = "The layout demonstration is\nunder development.")
    showButton.place(relx=0.5, rely=0.05, anchor="center")
    X = tkinter.Label(layout_frame, fg="black")
    X.pack()

def create_mapping_pannel(master):
    mappingPannel = tkinter.LabelFrame(master, text='Mapping', bd=BORDER, relief='groove')
    mappingPannel.grid(row=1, column=1, rowspan=1, columnspan=3, sticky="nsew")
    mappingCanvas = tkinter.Canvas(mappingPannel, bd=0)
    widgets["mappingCanvas"] = mappingCanvas
    hbar = tkinter.Scrollbar(mappingPannel, orient="horizontal", command=mappingCanvas.xview)
    hbar.pack(side="bottom", fill="x")
    mappingCanvas.config(xscrollcommand=hbar.set)
    vbar = tkinter.Scrollbar(mappingPannel, orient="vertical", command=mappingCanvas.yview)
    vbar.pack(side=tkinter.RIGHT, fill="y")
    mappingCanvas.config(yscrollcommand=vbar.set)
    mappingCanvas.pack(side="top", fill="both", expand=True)

def create_kernel_pannel(master):
    kernelPannel = tkinter.LabelFrame(master, text="Kernel", bd=BORDER, relief='groove')
    kernelPannel.grid(row=1, column=0, rowspan=1, columnspan=1, sticky="nsew")
    for row in range(12):
        kernelPannel.grid_rowconfigure(row, weight=1)
    kernelPannel.grid_columnconfigure(0, weight=3)
    kernelPannel.grid_columnconfigure(1, weight=2)
    kernelPannel.grid_columnconfigure(2, weight=2)
    kernelPannel.grid_columnconfigure(3, weight=1)

    selectAppLabel = tkinter.Label(kernelPannel, text=" Application:", fg='black')
    selectAppLabel.grid(row=0, column=0, sticky="nsew")

    appPathEntry = tkinter.Entry(kernelPannel, fg="black")
    widgets["appPathEntry"] = appPathEntry
    appPathEntry.grid(row=0, column=1, sticky="nsew")
    appPathEntry.bind("<Button-1>", clickSelectApp)

    compileAppButton = tkinter.Button(kernelPannel, text=" Compile app  ", fg="black", command=clickCompileApp)
    compileAppButton.grid(row=0, column=2, sticky="nsew")

    compileAppShow = tkinter.Label(kernelPannel, text=" IDLE", fg='gray')
    compileAppShow.grid(row=0, column=3, sticky="ew")
    widgets["compileAppShow"] = compileAppShow

    kernelNameLabel = tkinter.Label(kernelPannel, text=" Kernel name:", fg='black')
    kernelNameLabel.grid(row=1, column=0, sticky="nsew")

    tempOptions = [ "Not selected yet" ]
    kernelNameMenu = tkinter.OptionMenu(kernelPannel, kernelOptions, *tempOptions)
    kernelOptions.trace("w", clickKernelMenu)
    widgets["kernelNameMenu"] = kernelNameMenu
    kernelNameMenu.grid(row=1, column=1, sticky="nsew")

    generateDFGButton = tkinter.Button(kernelPannel, text = "Generate DFG", fg="black", command=clickShowDFG)
    generateDFGButton.grid(row=1, column=2, sticky="nsew")

    generateDFGShow = tkinter.Label(kernelPannel, text=" IDLE", fg='gray')
    generateDFGShow.grid(row=1, column=3, sticky="ew")
    widgets["generateDFGShow"] = generateDFGShow

    dfgPannel = tkinter.LabelFrame(kernelPannel, text='Data-Flow Graph', fg="black", bd=BORDER, relief='groove')
    dfgPannel.grid(row=2, column=0, rowspan=10, columnspan=2, sticky="nsew")
    dfgLabel = tkinter.Label(dfgPannel)
    widgets["dfgLabel"] = dfgLabel
    dfgLabel.pack()

    recMIILabel = tkinter.Label(kernelPannel, text=" RecMII: ", fg='black')
    recMIILabel.grid(row=2, column=2, sticky="nsew")
    recMIIEntry = tkinter.Entry(kernelPannel, fg="black", justify=tkinter.CENTER)
    widgets["recMIIEntry"] = recMIIEntry
    recMIIEntry.insert(0, "0")
    recMIIEntry.grid(row=2, column=3, sticky="ew")
    resMIILabel = tkinter.Label(kernelPannel, text=" ResMII: ", fg='black')
    resMIILabel.grid(row=3, column=2, sticky="nsew")
    resMIIEntry = tkinter.Entry(kernelPannel, fg="black", justify=tkinter.CENTER)
    widgets["resMIIEntry"] = resMIIEntry
    resMIIEntry.insert(0, "0")
    resMIIEntry.grid(row=3, column=3, sticky="ew")

    mappingOptionLabel = tkinter.Label(kernelPannel, text="Mapping algo:", fg='black')
    mappingOptionLabel.grid(row=4, column=2, columnspan=2, sticky="nsew")
    heuristicRatiobutton = tkinter.Radiobutton(kernelPannel, text="Heuristic", variable=mappingAlgoCheckVar, value=1)
    widgets["heuristicRatiobutton"] = heuristicRatiobutton
    heuristicRatiobutton.grid(row=5, column=2, columnspan=2, sticky="nsew")
    exhaustiveRatiobutton = tkinter.Radiobutton(kernelPannel, text="Exhaustive", variable=mappingAlgoCheckVar, value=0)
    widgets["exhaustiveRatiobutton"] = exhaustiveRatiobutton
    exhaustiveRatiobutton.grid(row=6, column=2, columnspan=2, sticky="nsew")

    mapDFGButton = tkinter.Button(kernelPannel, text="Map DFG", fg="black", command=clickMapDFG)
    mapDFGButton.grid(row=7, column=2, columnspan=2, sticky="new")
    terminateMapButton = tkinter.Button(kernelPannel, text="Terminate", fg="black", command=clickTerminateMapping)
    terminateMapButton.grid(row=8, column=2, columnspan=2, sticky="new")

    mapSecLabel = tkinter.Label(kernelPannel, text="Time (s): ", fg='black')
    mapSecLabel.grid(row=9, column=2, sticky="nsew")
    mapTimeEntry = tkinter.Entry(kernelPannel, fg="black", justify=tkinter.CENTER)
    widgets["mapTimeEntry"] = mapTimeEntry
    mapTimeEntry.insert(0, "0")
    mapTimeEntry.grid(row=9, column=3, sticky="ew")
    mapIILabel = tkinter.Label(kernelPannel, text=" Map II: ", fg='black')
    mapIILabel.grid(row=10, column=2, sticky="nsew")
    mapIIEntry = tkinter.Entry(kernelPannel, fg="black", justify=tkinter.CENTER)
    widgets["mapIIEntry"] = mapIIEntry
    mapIIEntry.insert(0, "0")
    mapIIEntry.grid(row=10, column=3, sticky="ew")

    speedupLabel = tkinter.Label(kernelPannel, text="Speedup: ", fg='black')
    speedupLabel.grid(row=11, column=2, sticky="nsew")
    CreateToolTip(speedupLabel, text = "The speedup is the improvement of\nthe execution cycles with respect to\na single-issue in-order CPU.")
    mapSpeedupEntry = tkinter.Entry(kernelPannel, fg="black", justify=tkinter.CENTER)
    widgets["mapSpeedupEntry"] = mapSpeedupEntry
    mapSpeedupEntry.insert(0, "0")
    mapSpeedupEntry.grid(row=11, column=3, sticky="ew")

#paramPadPosX = GRID_WIDTH + MEM_WIDTH + LINK_LENGTH + INTERVAL * 3
#paramPadWidth = 270
#scriptPadPosX = paramPadPosX + paramPadWidth + INTERVAL
#scriptPadWidth = 300
#layoutPadPosX = scriptPadPosX + scriptPadWidth + INTERVAL
#layoutPadWidth = 300
#layoutPadHeight = GRID_HEIGHT
create_kernel_pannel(master)
create_mapping_pannel(master)
create_cgra_pannel(master, ROWS, COLS)
create_param_pannel(master)
create_test_pannel(master)
create_layout_pannel(master)  
# The width and height of the entire window
default_width = 1600
default_height = 1050
window_size(master, default_width, default_height) 
#master.grid_rowconfigure(0, weight=1)
master.grid_rowconfigure(1, weight=2)
master.grid_columnconfigure(0, weight=1)
master.grid_columnconfigure(1, weight=1)
master.grid_columnconfigure(2, weight=1)
master.grid_columnconfigure(3, weight=1)
#print(master.winfo_width())
#print(master.winfo_height())
master.mainloop()