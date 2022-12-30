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

def helloCallBack():
    pass

TILE_SIZE = 60
LINK_LENGTH = 40
INTERVAL = 10
BORDER = 4

master = tkinter.Tk()
master.title("CGRA-Flow: An Integrated End-to-End Framework for CGRA Exploration, Compilation, and Development")

ROWS = 4
COLS = 4
GRID_WIDTH = (TILE_SIZE+LINK_LENGTH) * COLS - LINK_LENGTH
GRID_HEIGHT = (TILE_SIZE+LINK_LENGTH) * ROWS - LINK_LENGTH
MEM_WIDTH = 50
CONFIG_MEM = 8
DATA_MEM = 4
II = 4

fuTypeList = ["Phi", "Add", "Shift", "Ld", "Sel", "Cmp", "MAC", "St", "Ret", "Mul", "Logic", "Br"]

xbarTypeList = ["W", "E", "N", "S", "NE", "NW", "SE", "SW"]

DIRECTION_COUNTS = 8

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
        
widgets = {}
images = {}
fuCheckVars = {}
xbarCheckVars = {}

class ParamTile:
    def __init__( s, posX, posY ):
        s.disabled = False
        s.posX = posX
        s.posY = posY
        s.hasToMem = False
        s.hasFromMem = False
        s.invalidOutPorts = set()
        s.invalidInPorts = set()
        s.fuDict = {}
        s.xbarDict = {}
        for i in range( DIRECTION_COUNTS ):
            s.invalidOutPorts.add(i)
            s.invalidInPorts.add(i)
        
        for xbarType in xbarTypeList:
            s.xbarDict[xbarType] = 1

        for fuType in fuTypeList:
            s.fuDict[fuType] = 1

    def getIndex( s, tileList ):
        if s.disabled:
            return -1
        index = 0
        for tile in tileList:
            if tile.posY < s.posY and not tile.disabled:
                index += 1
            elif tile.posY == s.posY and tile.posX < s.posX and not tile.disabled:
                index += 1
        return index

class ParamLink:
    def __init__(s, srcTile, dstTile, srcPort, dstPort):
        s.srcTile = srcTile
        s.dstTile = dstTile
        s.srcPort = srcPort
        s.dstPort = dstPort
        s.disabled = False
        s.isToMem = False
        s.isFromMem = False

    def validatePorts(s):
        if not s.isToMem and not s.isFromMem:
            s.srcTile.invalidOutPorts.remove(s.srcPort)
            s.dstTile.invalidInPorts.remove(s.dstPort)
        if s.isToMem:
            s.srcTile.hasToMem = True
        if s.isFromMem:
            s.dstTile.hasFromMem = True

class ParamCGRA:
    def __init__(s, rows, columns, configMem=CONFIG_MEM, dataMem=DATA_MEM):
        s.rows = rows
        s.columns = columns
        s.configMem = configMem
        s.dataMem = dataMem
        s.tiles = []
        s.links = []
        s.targetTileID = 0
        s.initTiles(rows, columns)
        numOfLinks = rows*columns*2 + (rows-1)*columns*2 + (rows-1)*(columns-1)*2*2
        s.initLinks(numOfLinks)

        for fuType in fuTypeList:
            if fuType in fuCheckVars:
                fuCheckVars[fuType].set(1)

        for xbarType in xbarTypeList:
            if xbarType in xbarCheckVars:
                xbarCheckVars[xbarType].set(1)

    def updateMem(s, configMem, dataMem):
        s.configMem = configMem
        s.dataMem = dataMem

    def initTiles(s, rows, columns):
        for r in range(rows):
            for c in range(columns):
                s.tiles.append(ParamTile(c, r))

    def initLinks(s, numOfLinks):
        for _ in range(numOfLinks):
            s.links.append(ParamLink(None, None, 0, 0))


    def updateFuCheckbutton(s, fuType, value):
        s.tiles[s.targetTileID].fuDict[fuType] = value

    def updateXbarCheckbutton(s, xbarType, value):
        s.tiles[s.targetTileID].xbarDict[xbarType] = value


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
    paramCGRA.targetTileID = ID
    for fuType in fuTypeList:
        fuCheckVars[fuType].set(paramCGRA.tiles[ID].fuDict[fuType])

    for xbarType in xbarTypeList:
        xbarCheckVars[xbarType].set(paramCGRA.tiles[ID].xbarDict[xbarType])


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

def clickMapDFG():
    pass

def create_cgra_pannel(root, rows, columns):

    ROWS = rows
    COLS = columns
    TILE_SIZE = (GRID_WIDTH + LINK_LENGTH) / COLS - LINK_LENGTH

    totalWidth = GRID_WIDTH+MEM_WIDTH+LINK_LENGTH
    canvas = tkinter.Canvas(root, bd=5, height=GRID_HEIGHT, width=totalWidth)
    canvas.place(x=INTERVAL, y=INTERVAL)

    # pad contains tile and links
    padSize = TILE_SIZE + LINK_LENGTH
    
    # draw data memory
    posX = 0
    posY = 0
    memHeight = GRID_HEIGHT
    button = tkinter.Button(canvas, text = "Data\nSPM", fg = 'black', bg = 'gray', relief = 'raised', bd = BORDER, command = helloCallBack)
    button.place(height=memHeight, width=MEM_WIDTH, x = posX, y = posY)
            
    # draw tiles
    tiles = []
    numOfTile = 0
    for i in range(ROWS):
        for j in range(COLS):
            ID = i*COLS+j
            button = tkinter.Button(canvas, text = "Tile "+str(ID), fg='black', bg='gray', relief='raised', bd=BORDER, command=partial(
    clickTile, ID))
            posX = padSize * j + MEM_WIDTH + LINK_LENGTH
            posY = GRID_HEIGHT - padSize * i - TILE_SIZE
            button.place(height=TILE_SIZE, width=TILE_SIZE, x = posX, y = posY)
            if j == 0:
                tiles.append([])
            tile = Tile(ID, posX, posY, TILE_SIZE)
            tiles[-1].append(tile)

    # draw links
    for i in range(ROWS):
        for j in range(COLS):
            if j < COLS-1:
                # horizontal
                srcX, srcY = tiles[i][j].getRightMid()
                dstX, dstY = tiles[i][j+1].getLeftMid()
                canvas.create_line(srcX, srcY, dstX, dstY, arrow=tkinter.LAST)
                canvas.create_line(dstX, dstY, srcX, srcY, arrow=tkinter.LAST)
            
            if i < ROWS-1 and j < COLS-1:
                # diagonal left bottom to right top
                srcX, srcY = tiles[i][j].getRightTop()
                dstX, dstY = tiles[i+1][j+1].getLeftBottom()
                canvas.create_line(srcX, srcY, dstX, dstY, arrow=tkinter.LAST)
                canvas.create_line(dstX, dstY, srcX, srcY, arrow=tkinter.LAST)
                
            if i < ROWS-1 and j > 0:
                # diagonal left top to right bottom
                srcX, srcY = tiles[i][j].getLeftTop()
                dstX, dstY = tiles[i+1][j-1].getRightBottom()
                canvas.create_line(srcX, srcY, dstX, dstY, arrow=tkinter.LAST)
                canvas.create_line(dstX, dstY, srcX, srcY, arrow=tkinter.LAST)
                
            if i < ROWS-1:
                # vertical
                srcX, srcY = tiles[i][j].getTopMid()
                dstX, dstY = tiles[i+1][j].getBottomMid()
                canvas.create_line(srcX, srcY, dstX, dstY, arrow=tkinter.LAST)
                canvas.create_line(dstX, dstY, srcX, srcY, arrow=tkinter.LAST)
                
            if j == 0:
                # connect to memory
                srcX, srcY = tiles[i][j].getLeftMid()
                dstX, dstY = srcX - LINK_LENGTH, srcY
                canvas.create_line(srcX, srcY, dstX, dstY, arrow=tkinter.LAST)
                canvas.create_line(dstX, dstY, srcX, srcY, arrow=tkinter.LAST)

def place_fu_options(master):
    fuCount = len(fuTypeList)
    for i in range(len(fuTypeList)):
        fuVar = tkinter.IntVar()
        fuCheckVars[fuTypeList[i]] = fuVar
        fuCheckbutton = tkinter.Checkbutton(master, variable=fuVar, text=fuTypeList[i], command=partial(clickFuCheckbutton, fuTypeList[i]))
        fuCheckbutton.select()
        paramCGRA.updateFuCheckbutton(fuTypeList[i], fuVar.get())
        fuCheckbutton.grid(row=i//4, column=i%4, padx=3, pady=3, sticky="W")
        
def place_xbar_options(master):
    for i in range(8):
        xbarVar = tkinter.IntVar()
        xbarCheckVars[xbarTypeList[i]] = xbarVar
        xbarCheckbutton = tkinter.Checkbutton(master, variable=xbarVar, text=xbarTypeList[i], command=partial(clickXbarCheckbutton, xbarTypeList[i]))
        xbarCheckbutton.select()
        paramCGRA.updateXbarCheckbutton(xbarTypeList[i], xbarVar.get())
        xbarCheckbutton.grid(row=i//4, column=i%4, padx=BORDER, pady=BORDER, sticky="W")
                
def create_param_pannel(master, x, width, height):
    paramPannel = tkinter.LabelFrame(master, text='Configuration', bd=BORDER, relief='groove')
    paramPannel.place(height=height, width=width, x=x, y=INTERVAL)
    
    paramPannel.columnconfigure(0, weight=1)
    paramPannel.columnconfigure(1, weight=60)
    paramPannel.columnconfigure(2, weight=1)
    paramPannel.columnconfigure(3, weight=60)

    rowsLabel = ttk.Label(paramPannel, text='Rows:' )
    rowsLabel.grid(row=0, column=0, sticky=tkinter.W, padx=BORDER, pady=BORDER)
    rowsEntry = ttk.Entry(paramPannel, justify=tkinter.CENTER)
    rowsEntry.grid(row=0, column=1, sticky=tkinter.W, padx=BORDER, pady=BORDER)
    rowsEntry.insert(0, str(paramCGRA.rows))
    widgets["rowsEntry"] = rowsEntry
    
    columnsLabel = ttk.Label(paramPannel, text='Columns:')
    columnsLabel.grid(row=0, column=2, sticky=tkinter.E, padx=BORDER, pady=BORDER)
    columnsEntry = ttk.Entry(paramPannel, justify=tkinter.CENTER)
    columnsEntry.grid(row=0, column=3, sticky=tkinter.E, padx=BORDER, pady=BORDER)
    columnsEntry.insert(0, str(paramCGRA.columns))
    widgets["columnsEntry"] = columnsEntry
    
    configMemLabel = ttk.Label(paramPannel, text='ConfigMemSize (entries):')
    configMemLabel.grid(columnspan=3, row=1, column=0, padx=BORDER, pady=BORDER)
    configMemEntry = ttk.Entry(paramPannel, justify=tkinter.CENTER)
    configMemEntry.grid(row=1, column=3, sticky=tkinter.E, padx=BORDER, pady=BORDER)
    configMemEntry.insert(0, paramCGRA.configMem)
    widgets["configMemEntry"] = configMemEntry
    
    dataMemLabel = ttk.Label(paramPannel, text='DataSPMSize (KBs):')
    dataMemLabel.grid(columnspan=3, row=2, column=0, padx=BORDER, pady=BORDER)
    dataMemEntry = ttk.Entry(paramPannel, justify=tkinter.CENTER)
    dataMemEntry.grid(row=2, column=3, sticky=tkinter.E, padx=BORDER, pady=BORDER)
    dataMemEntry.insert(0, str(paramCGRA.dataMem))
    widgets["dataMemEntry"] = dataMemEntry
       
    fuConfigPannel = tkinter.LabelFrame(paramPannel, text='Tile 0 functional units', bd = BORDER, relief='groove')
    # fuConfigPannel.config(text='xxx')
    fuConfigPannel.grid(columnspan=4, row=3, column=0, padx=BORDER, pady=BORDER)
    widgets["fuConfigPannel"] = fuConfigPannel
    
    place_fu_options(fuConfigPannel)
    
    xbarConfigPannel = tkinter.LabelFrame(paramPannel, text='Tile 0 crossbar incoming links', bd = BORDER, relief='groove')
    # xbarConfigPannel.config(text='y')
    xbarConfigPannel.grid(columnspan=4, row=4, column=0, padx=BORDER, pady=BORDER)
    widgets["xbarConfigPannel"] = xbarConfigPannel
    
    place_xbar_options(xbarConfigPannel)   
   
    updateButton = tkinter.Button(paramPannel, text = "Update model", relief='raised', command = partial(clickUpdate, master))
    updateButton.grid(columnspan=4, row=5, column=0, padx=BORDER, pady=BORDER)
 

def create_test_pannel(master, x, width, height):
    testPannel = tkinter.LabelFrame(master, text='Verification', bd = BORDER, relief='groove')
    testPannel.place(height=height, width=width, x=x, y=INTERVAL)
    testButton = tkinter.Button(testPannel, text = "Run tests", relief='raised', command = clickTest)
    testButton.grid(row=0, column=0, sticky=tkinter.W, padx=BORDER, pady=BORDER//2)
    testProgress = ttk.Progressbar(testPannel, orient='horizontal', mode='determinate', length=width/2.5)
    testProgress['value'] = 0
    widgets["testProgress"] = testProgress
    testProgress.grid(row=0, column=1, padx=BORDER, pady=BORDER//2)
    testShow = tkinter.Label(testPannel, text = "IDLE", fg='gray')
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

    mapDFGButton = tkinter.Button(kernelPannel, text="Map", fg="black", command = clickMapDFG)
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
                

def create_mapping_pannel(root, x, y, width, height):

    # GRID_WIDTH = (TILE_SIZE+LINK_LENGTH) * COLS - linkLength
    TILE_SIZE = (GRID_WIDTH + LINK_LENGTH) / COLS - LINK_LENGTH
    memHeight = height

    frame = tkinter.LabelFrame(root, text="Mapping", bd=BORDER, relief='groove', width=width, height=height+20)
    frame.place(x=x, y=y)
    # frame.pack(expand=True, fill=tkinter.BOTH) #.grid(row=0,column=0)

    cgraWidth = GRID_WIDTH + MEM_WIDTH + LINK_LENGTH + 20
    canvas = tkinter.Canvas(frame, bd=-1, height=height+20, width=width, scrollregion=(0,0,II*cgraWidth, height))
    # canvas.place(x=x, y=y)

    hbar=tkinter.Scrollbar(frame, orient=tkinter.HORIZONTAL, bd=BORDER/4, relief='groove')
    hbar.pack(side=tkinter.BOTTOM, fill=tkinter.X)
    # hbar.place(x=0, y=memHeight+20)
    hbar.config(command=canvas.xview)
    canvas.config(width=width, height=height+20)
    canvas.config(xscrollcommand=hbar.set)
    canvas.pack(side=tkinter.LEFT, expand=True, fill=tkinter.BOTH)


    # pad contains tile and links
    padSize = TILE_SIZE + LINK_LENGTH
    baseX = 0
    
    for ii in range(II):

      # draw data memory
      posX = baseX
      posY = 0
      spmButton = tkinter.Label(canvas, text = "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\nData\nSPM", fg = 'black', bg = 'gray', relief = 'raised', bd = BORDER)
      adjustedHeight = (memHeight - TILE_SIZE/2)*2 + 10
      canvas.create_window(posX+30, posY+30, window=spmButton, height=adjustedHeight, width=MEM_WIDTH)
      # spmButton.place(height=memHeight, width=MEM_WIDTH, x = posX, y = posY)
              
      # draw tiles
      tiles = []
      numOfTile = 0
      for i in range(ROWS):
          for j in range(COLS):
              ID = i*COLS+j
              button = tkinter.Label(canvas, text = "Tile "+str(ID), fg='black', bg='gray', relief='raised', bd=BORDER)
              posX = baseX+BORDER+padSize * j + MEM_WIDTH + LINK_LENGTH
              posY = BORDER+height - padSize * i - TILE_SIZE
              canvas.create_window(posX+30, posY+30, window=button, height=TILE_SIZE, width=TILE_SIZE)
              # button.place(height=TILE_SIZE, width=TILE_SIZE, x = posX, y = posY)
              if j == 0:
                  tiles.append([])
              tile = Tile(ID, posX, posY, TILE_SIZE)
              tiles[-1].append(tile)

      # draw links
      for i in range(ROWS):
          for j in range(COLS):
              if j < COLS-1:
                  # horizontal
                  srcX, srcY = tiles[i][j].getRightMid()
                  dstX, dstY = tiles[i][j+1].getLeftMid()
                  canvas.create_line(srcX, srcY, dstX, dstY, arrow=tkinter.LAST)
                  canvas.create_line(dstX, dstY, srcX, srcY, arrow=tkinter.LAST)
              
              if i < ROWS-1 and j < COLS-1:
                  # diagonal left bottom to right top
                  srcX, srcY = tiles[i][j].getRightTop()
                  dstX, dstY = tiles[i+1][j+1].getLeftBottom()
                  canvas.create_line(srcX, srcY, dstX, dstY, arrow=tkinter.LAST)
                  canvas.create_line(dstX, dstY, srcX, srcY, arrow=tkinter.LAST)
                  
              if i < ROWS-1 and j > 0:
                  # diagonal left top to right bottom
                  srcX, srcY = tiles[i][j].getLeftTop()
                  dstX, dstY = tiles[i+1][j-1].getRightBottom()
                  canvas.create_line(srcX, srcY, dstX, dstY, arrow=tkinter.LAST)
                  canvas.create_line(dstX, dstY, srcX, srcY, arrow=tkinter.LAST)
                  
              if i < ROWS-1:
                  # vertical
                  srcX, srcY = tiles[i][j].getTopMid()
                  dstX, dstY = tiles[i+1][j].getBottomMid()
                  canvas.create_line(srcX, srcY, dstX, dstY, arrow=tkinter.LAST)
                  canvas.create_line(dstX, dstY, srcX, srcY, arrow=tkinter.LAST)
                  
              if j == 0:
                  # connect to memory
                  srcX, srcY = tiles[i][j].getLeftMid()
                  dstX, dstY = srcX - LINK_LENGTH, srcY
                  canvas.create_line(srcX, srcY, dstX, dstY, arrow=tkinter.LAST)
                  canvas.create_line(dstX, dstY, srcX, srcY, arrow=tkinter.LAST)
      cycleLabel = tkinter.Label(canvas, text="Cycle "+str(ii))
      canvas.create_window(baseX+width/3, memHeight+10+BORDER, window=cycleLabel, height=20, width=80)

      baseX += GRID_WIDTH + MEM_WIDTH + LINK_LENGTH + 20
      canvas.create_line(baseX-5, INTERVAL, baseX-5, memHeight, width=2, dash=(10,2))
      # cycleLabel.place(x=MEM_WIDTH+LINK_LENGTH+TILE_SIZE, y=memHeight+BORDER)



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

create_mapping_pannel(master, paramPadPosX, GRID_HEIGHT+INTERVAL*2, totalWidth-paramPadPosX-5, GRID_HEIGHT)

master.geometry(str(layoutPadPosX+layoutPadWidth+INTERVAL)+"x"+str(GRID_HEIGHT*2+INTERVAL*3+50))

master.mainloop()
