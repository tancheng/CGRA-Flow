from constants import *
from cgra_param_spm import ParamSPM

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

        for i in range(PORT_DIRECTION_COUNTS):
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
        return (baseX + s.posX, baseY + s.posY)

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
        return (baseX + s.posX, baseY + s.posY)

    def getNorthEast(s, baseX=0, baseY=0):
        return (baseX + s.posX + s.width, baseY + s.posY)

    def getSouthWest(s, baseX=0, baseY=0):
        return (baseX + s.posX, baseY + s.posY + s.height)

    def getSouthEast(s, baseX=0, baseY=0):
        return (baseX + s.posX + s.width, baseY + s.posY + s.height)

    def getWest(s, baseX=0, baseY=0):
        return (baseX + s.posX, baseY + s.posY + s.height // 2)

    def getEast(s, baseX=0, baseY=0):
        return (baseX + s.posX + s.width, baseY + s.posY + s.height // 2)

    def getNorth(s, baseX=0, baseY=0):
        return (baseX + s.posX + s.width // 2, baseY + s.posY)

    def getSouth(s, baseX=0, baseY=0):
        return (baseX + s.posX + s.width // 2, baseY + s.posY + s.height)

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
