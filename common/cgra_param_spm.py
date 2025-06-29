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
        for physicalPort in range(logicalPort + 1):
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
        for physicalPort in range(logicalPort + 1):
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