from cgra_param_spm import ParamSPM

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
