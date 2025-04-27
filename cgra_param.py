from constants import *
from cgra_param_tile import ParamTile
from cgra_param_spm import ParamSPM
from cgra_param_link import ParamLink
import customtkinter


class CGRAParam:
    def __init__(s, rows, columns, configMemSize=CONFIG_MEM_SIZE, dataMemSize=DATA_MEM_SIZE, masterWidgets = {}):
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
        s.widgets = masterWidgets
        # These will be injected later.
        s.switchDataSPMOutLinks = None
        s.updateFunCheckoutButtons = None
        s.updateFunCheckVars = None
        s.updateXbarCheckbuttons = None
        s.updateXbarCheckVars = None

    def get_row(s):
        return s.rows
    
    def get_col(s):
        return s.columns

    
    def set_cgra_param_callbacks(s,
                         switchDataSPMOutLinks,
                         updateFunCheckoutButtons,
                         updateFunCheckVars,
                         updateXbarCheckbuttons,
                         updateXbarCheckVars,
                         getFunCheckVars,
                         getXbarCheckVars):
        s.switchDataSPMOutLinks = switchDataSPMOutLinks
        s.updateFunCheckoutButtons = updateFunCheckoutButtons
        s.updateFunCheckVars = updateFunCheckVars
        s.updateXbarCheckbuttons = updateXbarCheckbuttons
        s.updateXbarCheckVars = updateXbarCheckVars
        s.getFunCheckVars = getFunCheckVars
        s.getXbarCheckVars = getXbarCheckVars
    
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
            if fuType in s.getFunCheckVars():
                s.updateFunCheckVars(fuType, targetTile.fuDict[fuType])

        for xbarType in xbarTypeList:
            if xbarType in s.getXbarCheckVars():
                s.updateXbarCheckVars(xbarType, targetTile.xbarDict[xbarType])

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
        numOfLinks = s.rows * s.columns * 2 + (s.rows - 1) * s.columns * 2 + (s.rows - 1) * (s.columns - 1) * 2 * 2

        for link in links:
            s.templateLinks.append(link)

    def resetTiles(s):

        for tile in s.tiles:
            tile.reset()

            # TODO: updates this variable internally and trigger UI updates back to UI python file
            for fuType in fuTypeList:
                s.updateFunCheckVars(fuType, tile.fuDict[fuType])
                s.updateFunCheckoutButtons(fuType, "normal")

            for xbarType in xbarTypeList:
                s.updateXbarCheckVars(xbarType, tile.xbarDict[xbarType])
                s.updateXbarCheckbuttons(xbarType, "normal")

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

        for portType in range(PORT_DIRECTION_COUNTS):
            if portType in s.getTileOfID(s.targetTileID).neverUsedOutPorts:
                s.updateXbarCheckbuttons(s.xbarPort2Type[portType], "disabled")

    def addTemplateLink(s, link):
        s.templateLinks.append(link)

    def addUpdatedLink(s, link):
        s.updatedLinks.append(link)

    def removeUpdatedLink(s, link):
        s.updatedLinks.remove(link)

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

    def updateSpmOutlinks(s):
        spmOutlinksSwitches = s.widgets['spmOutlinksSwitches']
        spmConfigPannel = s.widgets["spmConfigPannel"]
        for switch in spmOutlinksSwitches:
            switch.destroy()
        for port in s.dataSPM.outLinks:
            switch = customtkinter.CTkSwitch(spmConfigPannel, text=f"link {port}", command=s.switchDataSPMOutLinks)
            if not s.dataSPM.outLinks[port].disabled:
                switch.select()
            switch.pack(pady=(5, 10))
            spmOutlinksSwitches.insert(0, switch)