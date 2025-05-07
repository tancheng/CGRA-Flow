import json
import math
import os
import platform
import subprocess
import threading
import time
import tkinter
import tkinter.messagebox
from functools import partial
from tkinter import filedialog as fd
from constants import *
from cgra_param_tile import ParamTile
from cgra_param_spm import ParamSPM
from cgra_param_link import ParamLink
from cgra_param import CGRAParam
from cgra_multi_param import MultiCGRAParam
import customtkinter
from PIL import Image, ImageTk, ImageFile

import argparse
parser=argparse.ArgumentParser()
parser.add_argument("--theme")
args=parser.parse_args()
customtkinter.set_appearance_mode("dark")  # Modes: system (default), light, dark
customtkinter.set_default_color_theme("dark-blue")  # Themes: blue (default), dark-blue, green
# CANVAS_BG_COLOR = "#2B2B2B"
CANVAS_BG_COLOR = "#212121"
CANVAS_LINE_COLOR = "white"
MULTI_CGRA_FRAME_COLOR = "#14375E"
MULTI_CGRA_TILE_COLOR = "#1F538D"
MULTI_CGRA_TXT_COLOR = "white"
MULTI_CGRA_SELECTED_COLOR = "lightblue"

if args.theme:
   # print(f'Input theme argument: {args.theme}')
   if args.theme == 'light':
       customtkinter.set_appearance_mode("light")  # Modes: system (default), light, dark
       customtkinter.set_default_color_theme("dark-blue")  # Themes: blue (default), dark-blue, green
       CANVAS_BG_COLOR = "#E5E5E5"
       CANVAS_LINE_COLOR = "black"
       MULTI_CGRA_FRAME_COLOR = "#325882"
       MULTI_CGRA_TILE_COLOR = "#3A7EBF"
       MULTI_CGRA_TXT_COLOR = "black"

from VectorCGRA.cgra.translate.CGRATemplateRTL_test import *

# importing module
import logging

# Create and configure logger
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def window_size(window, width, height):
    window.geometry(f"{width}x{height}")

master = customtkinter.CTk()
master.title("Neura: An Integrated End-to-End Framework for Multi-CGRA Exploration, Compilation, Synthesis and Evaluation")


# Stores the UI elements that need to communicate between UI components
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
constraintFilePath = ""
configFilePath = ""

mapped_tile_color_list = ['#FFF113', '#75D561', '#F2CB67', '#FFAC73', '#F3993A', '#B3FF04', '#C2FFFF']

processOptions = tkinter.StringVar()
processOptions.set("asap7")

# TODO: Removes this and uses MultiCGRAParams.py 
class CgraOfMultiCgra:
    def __init__(s, cgraId, xStartPos, yStartPos, tileRows, tileCols):
        s.cgraId = cgraId
        s.xStartPos = xStartPos
        s.yStartPos = yStartPos
        s.tileRows = tileRows
        s.tileCols = tileCols

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
        y = y + cy + self.widget.winfo_rooty() + 27
        # self.tipwindow = tw = tkinter.Toplevel(self.widget)
        self.tipwindow = tw = customtkinter.CTkToplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        # label = tkinter.Label(tw, text=self.text, justify=tkinter.LEFT,
        #                       background="#ffffe0", relief=tkinter.SOLID, borderwidth=1,
        #                       font=("tahoma", "8", "normal"))
        label = customtkinter.CTkLabel(tw, text=self.text)
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


def clickTile(ID):
    print("click Title ")
    # widgets["fuConfigPannel"].configure(text='Tile ' + str(ID) + ' functional units')
    widgets["fuConfigPannel"].configure(label_text='Tile ' + str(ID) + '\nfunctional units')
    # widgets["xbarConfigPannel"].config(text='Tile ' + str(ID) + ' crossbar outgoing links')
    widgets["xbarConfigPannel"].configure(label_text='Tile ' + str(ID) + '\ncrossbar outgoing links')
    widgets["xbarCentralTilelabel"].configure(text='Tile ' + str(ID))
    # print(widgets['spmOutlinksSwitches'])
    # After clicking the tile, the pannel will fill all directions
    # widgets["xbarConfigPannel"].grid(columnspan=4, row=9, column=0, rowspan=3, sticky="nsew")
    widgets["entireTileCheckbutton"].configure(text='Disable entire Tile ' + str(ID), state="normal")
    # widgets["spmConfigPannel"].grid_forget()
    selectedCgraParam.targetTileID = ID

    disabled = selectedCgraParam.getTileOfID(ID).disabled
    for fuType in fuTypeList:
        fuCheckVars[fuType].set(selectedCgraParam.tiles[ID].fuDict[fuType])
        fuCheckbuttons[fuType].configure(state="disabled" if disabled else "normal")

    for xbarType in xbarTypeList:
        xbarCheckVars[xbarType].set(selectedCgraParam.tiles[ID].xbarDict[xbarType])
        xbarCheckbuttons[xbarType].configure(state="disabled" if disabled or xbarType2Port[xbarType] in selectedCgraParam.tiles[
            ID].neverUsedOutPorts else "normal")

    entireTileCheckVar.set(1 if selectedCgraParam.getTileOfID(ID).disabled else 0)


def clickSPM():
    print('clickSPM')
    # widgets["fuConfigPannel"].config(text='Tile ' + str(cgraParam.targetTileID) + ' functional units')
    # widgets["fuConfigPannelLabel"].configure(text='Tile ' + str(cgraParam.targetTileID) + ' functional units')
    #
    # for fuType in fuTypeList:
    #     fuCheckVars[fuType].set(cgraParam.tiles[cgraParam.targetTileID].fuDict[fuType])
    #     fuCheckbuttons[fuType].configure(state="disabled")
    #
    # widgets["xbarConfigPannel"].grid_forget()
    #
    # spmConfigPannel = widgets["spmConfigPannel"]
    # spmConfigPannel.config(text='DataSPM outgoing links')
    # # After clicking the SPM, the pannel will fill all directions
    # spmConfigPannel.grid(row=9, column=0, rowspan=3, columnspan=4, sticky="nsew")
    #
    # spmEnabledListbox = widgets["spmEnabledListbox"]
    # spmDisabledListbox = widgets["spmDisabledListbox"]
    #
    # widgets["entireTileCheckbutton"].configure(text='Disable entire Tile ' + str(cgraParam.targetTileID), state="disabled")


def switchDataSPMOutLinks():
    spmOutlinksSwitches = widgets['spmOutlinksSwitches']
    for portIdx, switch in enumerate(spmOutlinksSwitches):
        link = selectedCgraParam.dataSPM.outLinks[portIdx]
        if switch.get():
            link.disabled = False
        else:
            link.disabled = True


# TODO : move this inside CGRAParams and trigger UI update.
def updateFunCheckVars(type, value):
    fuCheckVars[type].set(value)

def updateFunCheckoutButtons(type, updatedState):
    fuCheckbuttons[type].configure(state=updatedState)

# TODO : move this inside CGRAParams and trigger UI update.
def updateXbarCheckVars(type, value):
    xbarCheckVars[type].set(value)

def updateXbarCheckbuttons(type, updateState):
    xbarCheckbuttons[type].configure(state=updateState)

def getFunCheckVars():
    return fuCheckVars

def getXbarCheckVars():
    return xbarCheckVars


multiCgraParam = MultiCGRAParam(rows=CGRA_ROWS, cols=CGRA_COLS, golbalWidgets = widgets)
multiCgraParam.setSelectedCgra(0, 0)
selectedCgraParam = multiCgraParam.getSelectedCgra()
selectedCgraParam.set_cgra_param_callbacks(switchDataSPMOutLinks=switchDataSPMOutLinks,
    updateFunCheckoutButtons=updateFunCheckoutButtons,
    updateFunCheckVars=updateFunCheckVars,
    updateXbarCheckbuttons=updateXbarCheckbuttons,
    updateXbarCheckVars=updateXbarCheckVars,
    getFunCheckVars=getFunCheckVars,
    getXbarCheckVars= getXbarCheckVars)

def clickSPMPortDisable():
    spmEnabledListbox = widgets["spmEnabledListbox"]
    portIndex = spmEnabledListbox.curselection()
    if portIndex:
        port = spmEnabledListbox.get(portIndex)
        spmEnabledListbox.delete(portIndex)
        widgets["spmDisabledListbox"].insert(0, port)

        link = selectedCgraParam.dataSPM.outLinks[port]
        link.disabled = True


def clickSPMPortEnable():
    spmDisabledListbox = widgets["spmDisabledListbox"]
    portIndex = spmDisabledListbox.curselection()
    if portIndex:
        port = spmDisabledListbox.get(portIndex)
        spmDisabledListbox.delete(portIndex)

        widgets["spmEnabledListbox"].insert(0, port)

        link = selectedCgraParam.dataSPM.outLinks[port]
        link.disabled = False


def clickEntireTileCheckbutton():
    if entireTileCheckVar.get() == 1:

        for fuType in fuTypeList:
            fuCheckVars[fuType].set(0)
            tile = selectedCgraParam.getTileOfID(selectedCgraParam.targetTileID)
            tile.fuDict[fuType] = 0
            # clickFuCheckbutton(fuType)
            fuCheckbuttons[fuType].configure(state="disabled")

        selectedCgraParam.getTileOfID(selectedCgraParam.targetTileID).disabled = True
    else:
        for fuType in fuTypeList:
            fuCheckVars[fuType].set(0)
            tile = selectedCgraParam.getTileOfID(selectedCgraParam.targetTileID)
            tile.fuDict[fuType] = 0
            # clickFuCheckbutton(fuType)
            fuCheckbuttons[fuType].configure(state="normal")

        # cgraParam.getTileOfID(cgraParam.targetTileID).disabled = False


def clickFuCheckbutton(fuType):
    if fuType == "Ld":
        fuCheckVars["St"].set(fuCheckVars["Ld"].get())
        selectedCgraParam.updateFuCheckbutton("St", fuCheckVars["St"].get())
    elif fuType == "St":
        fuCheckVars["Ld"].set(fuCheckVars["St"].get())
        selectedCgraParam.updateFuCheckbutton("Ld", fuCheckVars["Ld"].get())
    selectedCgraParam.updateFuCheckbutton(fuType, fuCheckVars[fuType].get())


def clickXbarCheckbutton(xbarType):
    selectedCgraParam.updateXbarCheckbutton(xbarType, xbarCheckVars[xbarType].get())


def clickUpdate(root):
    rows = int(widgets["rowsEntry"].get())
    columns = int(widgets["columnsEntry"].get())
    configMemSize = int(widgets["configMemEntry"].get())
    dataMemSize = int(widgets["dataMemEntry"].get())

    global selectedCgraParam
    oldCGRA = selectedCgraParam

    old_rows_num = selectedCgraParam.rows
    if selectedCgraParam.rows != rows or selectedCgraParam.columns != columns:
        selectedCgraParam = CGRAParam(rows, columns ,CONFIG_MEM_SIZE, DATA_MEM_SIZE, widgets)
        selectedCgraParam.set_cgra_param_callbacks(switchDataSPMOutLinks=switchDataSPMOutLinks,
                                           updateFunCheckoutButtons=updateFunCheckoutButtons,
                                           updateFunCheckVars=updateFunCheckVars,
                                           updateXbarCheckbuttons=updateXbarCheckbuttons,
                                           updateXbarCheckVars=updateXbarCheckVars,
                                           getFunCheckVars=getFunCheckVars,
                                           getXbarCheckVars= getXbarCheckVars)

    multiCgraParam.cgras[multiCgraParam.selected_row][multiCgraParam.selected_col] = selectedCgraParam    

    # dataSPM = ParamSPM(MEM_WIDTH, rows, rows)
    # cgraParam.initDataSPM(dataSPM)

    create_cgra_pannel(root, rows, columns)

    # kernel related information and be kept to avoid redundant compilation
    selectedCgraParam.updateMemSize(configMemSize, dataMemSize)
    selectedCgraParam.updateTiles()
    selectedCgraParam.updateLinks()
    if old_rows_num != rows:
        selectedCgraParam.updateSpmOutlinks()

    selectedCgraParam.targetAppName = oldCGRA.targetAppName
    selectedCgraParam.compilationDone = oldCGRA.compilationDone
    selectedCgraParam.targetKernels = oldCGRA.targetKernels
    selectedCgraParam.targetKernelName = oldCGRA.targetKernelName
    selectedCgraParam.DFGNodeCount = oldCGRA.DFGNodeCount
    selectedCgraParam.recMII = oldCGRA.recMII
    selectedCgraParam.verilogDone = False

    widgets["verilogText"].delete("1.0", tkinter.END)
    widgets["resMIIEntry"].delete(0, tkinter.END)
    if len(selectedCgraParam.getValidTiles()) > 0 and selectedCgraParam.DFGNodeCount > 0:
        selectedCgraParam.resMII = math.ceil((selectedCgraParam.DFGNodeCount + 0.0) / len(selectedCgraParam.getValidTiles())) // 1
        widgets["resMIIEntry"].insert(0, selectedCgraParam.resMII)
    else:
        widgets["resMIIEntry"].insert(0, 0)


def clickReset(root):
    rows = int(widgets["rowsEntry"].get())
    columns = int(widgets["columnsEntry"].get())
    configMemSize = int(widgets["configMemEntry"].get())
    dataMemSize = int(widgets["dataMemEntry"].get())

    global selectedCgraParam
    oldCGRA = selectedCgraParam

    if selectedCgraParam.rows != rows or selectedCgraParam.columns != columns:
        selectedCgraParam = CGRAParam(rows, columns, CONFIG_MEM_SIZE, DATA_MEM_SIZE, widgets)
        selectedCgraParam.set_cgra_param_callbacks(switchDataSPMOutLinks=switchDataSPMOutLinks,
                                           updateFunCheckoutButtons=updateFunCheckoutButtons,
                                           updateFunCheckVars=updateFunCheckVars,
                                           updateXbarCheckbuttons=updateXbarCheckbuttons,
                                           updateXbarCheckVars=updateXbarCheckVars,
                                           getFunCheckVars=getFunCheckVars,
                                           getXbarCheckVars= getXbarCheckVars)

    selectedCgraParam.updateMemSize(configMemSize, dataMemSize)
    selectedCgraParam.resetTiles()
    selectedCgraParam.enableAllTemplateLinks()
    selectedCgraParam.resetLinks()

    selectedCgraParam.updateSpmOutlinks()

    create_cgra_pannel(root, rows, columns)

    # for _ in range(cgraParam.rows):
    #     widgets["spmEnabledListbox"].delete(0)
    #     widgets["spmDisabledListbox"].delete(0)

    # widgets['spmOutlinksSwitches'] = []
    # spmOutlinksSwitches = []
    # spmConfigPannel = widgets["spmConfigPannel"]
    # for port in cgraParam.dataSPM.outLinks:
    #     switch = customtkinter.CTkSwitch(spmConfigPannel, text=f"link {port}", command=switchDataSPMOutLinks)
    #     if not cgraParam.dataSPM.outLinks[port].disabled:
    #         switch.select()
    #     switch.pack(pady=(5, 10))
    #     spmOutlinksSwitches.insert(0, switch)
    # widgets['spmOutlinksSwitches'] = spmOutlinksSwitches

    # kernel related information and be kept to avoid redundant compilation
    selectedCgraParam.targetAppName = oldCGRA.targetAppName
    selectedCgraParam.compilationDone = oldCGRA.compilationDone
    selectedCgraParam.targetKernels = oldCGRA.targetKernels
    selectedCgraParam.targetKernelName = oldCGRA.targetKernelName
    selectedCgraParam.DFGNodeCount = oldCGRA.DFGNodeCount
    selectedCgraParam.recMII = oldCGRA.recMII

    widgets["verilogText"].delete(0, tkinter.END)
    widgets["resMIIEntry"].delete(0, tkinter.END)
    if len(selectedCgraParam.getValidTiles()) > 0 and selectedCgraParam.DFGNodeCount > 0:
        selectedCgraParam.resMII = math.ceil((selectedCgraParam.DFGNodeCount + 0.0) / len(selectedCgraParam.getValidTiles())) // 1
        widgets["resMIIEntry"].insert(0, selectedCgraParam.resMII)
    else:
        widgets["resMIIEntry"].insert(0, 0)


def clickTest():
    # need to provide the paths for lib.so and kernel.bc
    os.system("mkdir test")
    # os.system("cd test")
    os.chdir("test")

    widgets["testShow"].configure(text="0%")
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
                # print(f'testProgress value: {value}')
                widgets["testProgress"].set(value/100)
                widgets["testShow"].configure(text=str(value) + "%")
                master.update_idletasks()
                total += 1
                if ".py F" in outputLine:
                    failed += 1

    widgets["testShow"].configure(text=" PASSED " if failed == 0 else str(total - failed) + "/" + str(total))
    # (out, err) = testProc.communicate()
    # print("check test output:", out)

    os.chdir("..")


def clickGenerateVerilog():
    message = selectedCgraParam.getErrorMessage()
    if message != "":
        tkinter.messagebox.showerror(title="CGRA Model Checking", message=message)
        return

    os.system("mkdir verilog")
    os.chdir("verilog")

    # pymtl function that is used to generate synthesizable verilog
    cmdline_opts = {'test_verilog': 'zeros', 'test_yosys_verilog': '', 'dump_textwave': False, 'dump_vcd': False,
                    'dump_vtb': False, 'max_cycles': None}
    test_cgra_universal(cgraParam = selectedCgraParam)

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

    selectedCgraParam.verilogDone = True
    if not found:
        selectedCgraParam.verilogDone = False
        widgets["verilogText"].insert(tkinter.END, "Error exists during Verilog generation")

    os.system("mv CGRATemplateRTL__*.v design.v")
    # os.system("rename s/\.v/\.log/g *")

    os.chdir("..")


def setReportProgress(value):
    # widgets["reportProgress"].configure(value=value)
    widgets["reportProgress"].set(value/100)


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

    # widgets["reportProgress"].configure(value=100)
    widgets["reportProgress"].set(1)

    os.chdir("../../../build")

    synthesisRunning = False


def clickSynthesize():
    global selectedCgraParam
    global synthesisRunning

    if synthesisRunning:
        return

    if not selectedCgraParam.verilogDone:
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

    updatedSizePattern = str(selectedCgraParam.dataMemSize * 1024)
    updatedReadPortPattern = str(selectedCgraParam.dataSPM.getNumOfValidReadPorts())
    updatedWritePortPattern = str(selectedCgraParam.dataSPM.getNumOfValidWritePorts())

    with open(r'../../tools/cacti/spm_template.cfg', 'r') as file:
        data = file.read()

        data = data.replace(sizePattern, updatedSizePattern)
        data = data.replace(readPortPattern, updatedReadPortPattern)
        data = data.replace(writePortPattern, updatedWritePortPattern)

    with open(r'../../tools/cacti/spm_temp.cfg', 'w') as file:
        file.write(data)

    os.chdir("../../tools/cacti")

    cactiCommand = "./cacti -infile spm_temp.cfg"
    cactiProc = subprocess.Popen([cactiCommand, '-u'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True,
                                 bufsize=1)
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
    global selectedCgraParam
    selectedCgraParam.compilationDone = False
    appName = fd.askopenfilename(title="choose an application", initialdir="../", filetypes=(
    ("C/C++ file", "*.cpp"), ("C/C++ file", "*.c"), ("C/C++ file", "*.C"), ("C/C++ file", "*.CPP")))
    selectedCgraParam.targetAppName = appName

    # widgets["appPathEntry"].configure(state="normal")
    widgets["appPathEntry"].delete(0, tkinter.END)
    widgets["appPathEntry"].insert(0, selectedCgraParam.targetAppName)
    # widgets["appPathEntry"].configure(state="disabled")

    widgets["compileAppShow"].configure(text="IDLE")


def clickCompileApp():
    global selectedCgraParam
    fileName = selectedCgraParam.targetAppName
    if not fileName or fileName == "   Not selected yet":
        return

    os.system("mkdir kernel")
    os.chdir("kernel")

    compileCommand = "clang-12 -emit-llvm -fno-unroll-loops -O3 -o kernel.bc -c " + fileName
    compileProc = subprocess.Popen([compileCommand, '-u'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    (compileOut, compileErr) = compileProc.communicate()

    disassembleCommand = "llvm-dis-12 kernel.bc -o kernel.ll"
    disassembleProc = subprocess.Popen([disassembleCommand, '-u'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       shell=True)
    (disassembleOut, disassembleErr) = disassembleProc.communicate()

    if compileErr:
        widgets["compileAppShow"].configure(text=u'\u2717\u2717\u2717')
        os.chdir("..")
        print("Compile error message: ", compileErr)
        return
    if disassembleErr:
        widgets["compileAppShow"].configure(text=u'\u2717\u2717\u2717')
        os.chdir("..")
        print("Disassemble error message: ", disassembleErr)
        return

    widgets["compileAppShow"].configure(text=u'\u2713\u2713\u2713')
    selectedCgraParam.compilationDone = True

    # collect the potentially targeting kernel/function
    irFile = open('kernel.ll', 'r')
    irLines = irFile.readlines()

    # Strips the newline character
    selectedCgraParam.targetKernels = []
    for line in irLines:
        if "define " in line and "{" in line and "@" in line:
            funcName = line.split("@")[1].split("(")[0]
            if "main" not in funcName:
                selectedCgraParam.targetKernels.append(funcName)

    irFile.close()

    kernelNameMenu = widgets["kernelNameMenu"]
    kernelPannel = widgets["kernelPannel"]
    # kernelNameMenu["menu"].delete(0, "end")
    kernelNameMenu.destroy()
    kernelNameOptions = [kernelName for kernelName in selectedCgraParam.targetKernels]
    kernelNameMenu = customtkinter.CTkOptionMenu(kernelPannel, variable=kernelOptions, values=kernelNameOptions)
    kernelNameMenu.grid(row=2, column=1)
    widgets["kernelNameMenu"] = kernelNameMenu
    # for kernelName in cgraParam.targetKernels:
    #     # kernelNameMenu["menu"].add_command(label=kernelName, command=tkinter._setit(kernelOptions, kernelName))
    #     print(f'kernelName: {kernelName}')
    # options.set(my_list[0])

    widgets["generateDFGShow"].configure(text="IDLE")

    os.chdir("..")


def clickKernelMenu(*args):
    global selectedCgraParam
    name = kernelOptions.get()
    if name == None or name == " " or name == "Not selected yet":
        return
    selectedCgraParam.targetKernelName = name


def dumpcgraParam2JSON(fileName):
    global selectedCgraParam
    cgraParamJson = {}
    cgraParamJson["tiles"] = {}
    for tile in selectedCgraParam.tiles:
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

            if (tile.hasFromMem() and tile.fuDict["Ld"] == 1) and \
                    (tile.hasToMem() and tile.fuDict["St"] == 1):
                curDict["accessMem"] = True

        cgraParamJson["tiles"][str(tile.ID)] = curDict

    cgraParamJson["links"] = []
    for link in selectedCgraParam.updatedLinks:
        curDict = {}
        srcTile = link.srcTile
        dstTile = link.dstTile
        if not link.disabled and not srcTile.disabled and not dstTile.disabled and type(srcTile) != ParamSPM and type(
                dstTile) != ParamSPM:
            curDict["srcTile"] = srcTile.ID
            curDict["dstTile"] = dstTile.ID
            cgraParamJson["links"].append(curDict)

    cgraParamJsonObject = json.dumps(cgraParamJson, indent=4)

    # Writing to sample.json
    with open(fileName, "w") as outfile:
        outfile.write(cgraParamJsonObject)


def clickShowDFG():
    os.system("mkdir kernel")
    os.chdir("kernel")
    fileExist = os.path.exists("kernel.bc")
    global selectedCgraParam

    if not fileExist or not selectedCgraParam.compilationDone or selectedCgraParam.targetKernelName == None:
        os.chdir("..")
        tkinter.messagebox.showerror(title="DFG Generation",
                                     message="The compilation and kernel selection need to be done first.")
        return

    selectedCgraParam.targetKernelName = kernelOptions.get()

    genDFGJson = {
        "kernel": selectedCgraParam.targetKernelName,
        "targetFunction": False,
        "targetNested": True,
        "targetLoopsID": [0],
        "doCGRAMapping": False,
        "row": selectedCgraParam.rows,
        "column": selectedCgraParam.columns,
        "precisionAware": False,
        "heterogeneity": False,
        "isTrimmedDemo": True,
        "heuristicMapping": True,
        "parameterizableCGRA": True,
        "diagonalVectorization": False,
        "bypassConstraint": 8,
        "isStaticElasticCGRA": False,
        "ctrlMemConstraint": 200,
        "regConstraint": 12,
    }

    json_object = json.dumps(genDFGJson, indent=4)

    with open("param.json", "w") as outfile:
        outfile.write(json_object)

    dumpcgraParam2JSON("cgraParam.json")

    genDFGCommand = "opt-12 -load ../../CGRA-Mapper/build/src/libmapperPass.so -mapperPass ./kernel.bc"
    print("trying to run opt-12")
    genDFGProc = subprocess.Popen([genDFGCommand, "-u"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

    with genDFGProc.stdout:
        for line in iter(genDFGProc.stdout.readline, b''):
            outputLine = line.decode("ISO-8859-1")
            print(outputLine)
            if "DFG node count: " in outputLine:
                selectedCgraParam.DFGNodeCount = int(outputLine.split("DFG node count: ")[1].split(";")[0])
            if "[RecMII: " in outputLine:
                selectedCgraParam.recMII = int(outputLine.split("[RecMII: ")[1].split("]")[0])

    (out, err) = genDFGProc.communicate()
    print("opt-12 out: ", out)
    print("opt-12 err: ", err)

    selectedCgraParam.resMII = math.ceil((selectedCgraParam.DFGNodeCount + 0.0) / len(selectedCgraParam.getValidTiles())) // 1
    widgets["resMIIEntry"].delete(0, tkinter.END)
    widgets["resMIIEntry"].insert(0, selectedCgraParam.resMII)

    widgets["recMIIEntry"].delete(0, tkinter.END)
    widgets["recMIIEntry"].insert(0, selectedCgraParam.recMII)

    convertCommand = "dot -Tpng " + selectedCgraParam.targetKernelName + ".dot -o kernel.png"
    convertProc = subprocess.Popen([convertCommand, "-u"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    (out, err) = convertProc.communicate()

    # Gets the size of the whole window
    master.update_idletasks()
    window_width = master.winfo_width()
    window_height = master.winfo_height()

    PIL_image = Image.open("kernel.png")
    ImageFile.LOAD_TRUNCATED_IMAGES = True
    PIL_image_stretched = PIL_image.resize((window_width // 6, window_height // 3), Image.Resampling.BILINEAR)
    PIL_image_stretched = PIL_image_stretched.convert("RGBA")
    datas = PIL_image_stretched.getdata()

    new_data = []
    for item in datas:
        if item[0] == 255 and item[1] == 255 and item[2] == 255:
            # Makes the white parts of the image white
            new_data.append((255, 255, 255, 255))
        else:
            new_data.append(item)
    PIL_image_stretched.putdata(new_data)

    # dfgImage = ImageTk.PhotoImage(PIL_image_stretched)
    dfgImage = customtkinter.CTkImage(PIL_image_stretched, size=(260, 380))
    images["dfgImage"] = dfgImage  # This is important due to the garbage collection would remove local variable of image
    widgets["dfgLabel"].configure(image=dfgImage)

    widgets["generateDFGShow"].configure(text=u'\u2713\u2713\u2713')

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
    mappingProc = subprocess.Popen(["exec " + mappingCommand, '-u'], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   shell=True, bufsize=1)
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
    widgets["mapSpeedupEntry"].insert(0, selectedCgraParam.DFGNodeCount / mappingII)

    # pad contains tile and links
    tileWidth = selectedCgraParam.tiles[0].width
    tileHeight = selectedCgraParam.tiles[0].height
    padWidth = tileWidth + LINK_LENGTH
    padHeight = tileHeight + LINK_LENGTH
    baseX = 0

    # load schedule.json for mapping demonstration
    f = open("schedule.json")
    schedule = json.load(f)

    # Iterating through the json
    for strTileID in schedule["tiles"]:
        tileID = int(strTileID)
        tile = selectedCgraParam.getTileOfID(tileID)
        for strCycle in schedule["tiles"][strTileID]:
            cycle = int(strCycle)
            optID = schedule["tiles"][strTileID][strCycle]
            tile.mapping[cycle] = optID[0]

    for strSrcTileID in schedule["links"]:
        for strDstTileID in schedule["links"][strSrcTileID]:
            srcTile = selectedCgraParam.getTileOfID(int(strSrcTileID))
            dstTile = selectedCgraParam.getTileOfID(int(strDstTileID))
            link = selectedCgraParam.getUpdatedLink(srcTile, dstTile)
            for cycle in schedule["links"][strSrcTileID][strDstTileID]:
                link.mapping.add(cycle)

    f.close()
    os.chdir("..")

    canvas = widgets["mappingCanvas"]
    canvas.delete("all")
    #ROWS = widgets["ROWS"]
    #COLS = widgets["COLS"]
    GRID_WIDTH = (TILE_WIDTH + LINK_LENGTH) * selectedCgraParam.columns - LINK_LENGTH
    GRID_HEIGHT = (TILE_HEIGHT + LINK_LENGTH) * selectedCgraParam.rows - LINK_LENGTH
    cgraWidth = GRID_WIDTH + MEM_WIDTH + LINK_LENGTH + 20
    canvas.configure(scrollregion=(0, 0, mappingII * cgraWidth, GRID_HEIGHT + 40 + BORDER))

    for ii in range(mappingII):
        # draw data memory
        # spmLabel = tkinter.Label(canvas, text="Data\nSPM", fg='black', bg='gray', relief='raised', bd=BORDER,
        #                          highlightbackground="black", highlightthickness=HIGHLIGHT_THICKNESS)
        spmLabel = customtkinter.CTkButton(canvas, text="Data\nSPM", state='disabled', text_color_disabled='white')
        canvas.create_window(baseX + BORDER, BORDER, window=spmLabel, height=GRID_HEIGHT, width=MEM_WIDTH, anchor="nw")

        mapped_tile_color = mapped_tile_color_list[ii % len(mapped_tile_color_list)]

        # draw tiles
        for tile in selectedCgraParam.tiles:
            if not tile.disabled:
                button = None
                if ii in tile.mapping:
                    # button = tkinter.Label(canvas, text="Opt " + str(tile.mapping[ii]), fg="black", bg="cornflowerblue",
                    #                        relief="raised", bd=BORDER, highlightbackground="black",
                    #                        highlightthickness=HIGHLIGHT_THICKNESS)
                    button = customtkinter.CTkButton(canvas, text="Opt " + str(tile.mapping[ii]), state='disabled',
                                                     border_width=2,
                                                     font=customtkinter.CTkFont(weight="bold"),
                                                     text_color_disabled='black',
                                                     fg_color=mapped_tile_color,
                                                     border_color=mapped_tile_color)
                else:
                    # button = tkinter.Label(canvas, text="Tile " + str(tile.ID), fg="black", bg="grey", relief="raised",
                    #                        bd=BORDER, highlightbackground="black",
                    #                        highlightthickness=HIGHLIGHT_THICKNESS)
                    button = customtkinter.CTkButton(canvas, text="Tile " + str(tile.ID), state='disabled', text_color_disabled='white')
                posX, posY = tile.getPosXY(baseX + BORDER, BORDER)
                canvas.create_window(posX, posY, window=button, height=tileHeight, width=tileWidth, anchor="nw")

        # draw links
        for link in selectedCgraParam.updatedLinks:
            if not link.disabled:
                srcX, srcY = link.getSrcXY(baseX + BORDER, BORDER)
                dstX, dstY = link.getDstXY(baseX + BORDER, BORDER)
                if ii in link.mapping:
                    canvas.create_line(srcX, srcY, dstX, dstY, arrow=tkinter.LAST, width=3, fill=mapped_tile_color)
                else:
                    canvas.create_line(srcX, srcY, dstX, dstY, arrow=tkinter.LAST, fill=CANVAS_LINE_COLOR)

        # cycleLabel = tkinter.Label(canvas, text="Cycle " + str(ii))
        cycleLabel = customtkinter.CTkLabel(canvas, text="Cycle " + str(ii) + " ",
                                            font=customtkinter.CTkFont(size=FRAME_LABEL_FONT_SIZE, weight="bold"))
        canvas.create_window(baseX + (cgraWidth)/2, GRID_HEIGHT + 30 + BORDER, window=cycleLabel, height=20, width=80)

        baseX += GRID_WIDTH + MEM_WIDTH + LINK_LENGTH + 20
        canvas.create_line(baseX - 5, INTERVAL, baseX - 5, GRID_HEIGHT, width=2, dash=(10, 2), fill="grey")


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
    heuristic = mappingAlgoCheckVar.get() == 0

    os.system("mkdir kernel")
    os.chdir("kernel")
    fileExist = os.path.exists("kernel.bc")
    global selectedCgraParam

    if not fileExist or not selectedCgraParam.compilationDone or selectedCgraParam.targetKernelName == None:
        os.chdir("..")
        # tkinter.messagebox.showerror(title="DFG mapping", message="The compilation and kernel selection need to be done first.")
        if not fileExist:
            tkinter.messagebox.showerror(title="DFG mapping", message="The kernel.bc doesn't exist.")
        if not selectedCgraParam.compilationDone:
            tkinter.messagebox.showerror(title="DFG mapping", message="The compilation needs to be done first.")
        if selectedCgraParam.targetKernelName == None:
            tkinter.messagebox.showerror(title="DFG mapping", message="The kernel name is not selected yet.")
        return

    mappingJson = {
        "kernel": selectedCgraParam.targetKernelName,
        "targetFunction": False,
        "targetNested": True,
        "targetLoopsID": [0],
        "doCGRAMapping": True,
        "row": selectedCgraParam.rows,
        "column": selectedCgraParam.columns,
        "precisionAware": False,
        "heterogeneity": False,
        "isTrimmedDemo": True,
        "heuristicMapping": heuristic,
        "parameterizableCGRA": True,
        "diagonalVectorization": False,
        "bypassConstraint": 8,
        "isStaticElasticCGRA": False,
        "ctrlMemConstraint": selectedCgraParam.configMemSize,
        "regConstraint": 12,
    }

    mappingJsonObject = json.dumps(mappingJson, indent=4)

    with open("param.json", "w") as outfile:
        outfile.write(mappingJsonObject)

    dumpcgraParam2JSON("cgraParam.json")

    mappingCommand = "opt-12 -load ../../CGRA-Mapper/build/src/libmapperPass.so -mapperPass ./kernel.bc"

    widgets["mapTimeEntry"].delete(0, tkinter.END)
    widgets["mapTimeEntry"].insert(0, 0)

    drawer = threading.Thread(target=drawSchedule)
    drawer.start()
    timer = threading.Thread(target=countMapTime)
    timer.start()


def _on_mousewheel(canvas, event):
    platformSystem = platform.system()
    logging.info("Current platform.system: %s", platformSystem)
    if platformSystem == "Windows":
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    elif platformSystem == "Linux":
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    else:
        canvas.yview_scroll(int(-1*event.delta), "units")

# Defines selected cgra frame in multi-cgra panel.
selected_cgra_frame = None

def cgra_frame_clicked(event, cgraId, frame):
    global selected_cgra_frame, selectedCgraParam
    if selected_cgra_frame and selected_cgra_frame != frame:
        selected_cgra_frame.config(bg=MULTI_CGRA_FRAME_COLOR)
        selected_cgra_frame.is_selected = False

    if getattr(frame, 'is_selected', False) == False:
        print(f"cgraId: {cgraId} selected!")
        frame.is_selected = True
        frame.config(bg=MULTI_CGRA_SELECTED_COLOR)  
        selected_cgra_frame = frame
        multiCgraParam.setSelectedCgra(cgraId//multiCgraParam.rows,cgraId%multiCgraParam.cols)
        selectedCgraParam = multiCgraParam.getSelectedCgra()
        selectedCgraParam.set_cgra_param_callbacks(switchDataSPMOutLinks=switchDataSPMOutLinks,
                                                   updateFunCheckoutButtons=updateFunCheckoutButtons,
                                                   updateFunCheckVars=updateFunCheckVars,
                                                   updateXbarCheckbuttons=updateXbarCheckbuttons,
                                                   updateXbarCheckVars=updateXbarCheckVars,
                                                   getFunCheckVars=getFunCheckVars,
                                                   getXbarCheckVars= getXbarCheckVars)
        # Only re-draw if this re-draw is triggered from user click
        if (event != None):
            create_cgra_pannel(master, selectedCgraParam.rows, selectedCgraParam.columns)
    else:
        print(f"cgraId: {cgraId} unselected!, do nothing")
    

def create_multi_cgra_panel(master, cgraRows=2, cgraCols=2):
    multiCgraPanel = customtkinter.CTkFrame(master)
    # multiCgraPanel.grid(row=0, column=0, padx=(0, 5), sticky="nsew")
    multiCgraLabel = customtkinter.CTkLabel(multiCgraPanel, text='Multi-CGRA',
                                       font=customtkinter.CTkFont(size=FRAME_LABEL_FONT_SIZE, weight="bold"))
    multiCgraLabel.pack(anchor="w", ipadx=5)
    multiCgraCanvas = customtkinter.CTkCanvas(multiCgraPanel, bg=CANVAS_BG_COLOR, bd=0, highlightthickness=0)

    # canvas base 0, 0
    # suppose default rowsxcols 2x2, may extra operation to connect cgra frames when one row only
    xStartPos, yStartPos = 0, 0
    distanceOfCgraAndRouter = 20
    cgraSquareLength = 80 # 100
    routerDiameter = cgraSquareLength / 4
    distanceOfCgras = 140 # 200

    x, y = xStartPos, yStartPos
    cgraId = 0
    for row in range(cgraRows):
        for col in range(cgraCols):
            # draw
            print(f"cgraFrame: {x} x {y}, cgraSquareLength: {cgraSquareLength}")
            cgraFrame = tkinter.Frame(multiCgraCanvas, bg=MULTI_CGRA_FRAME_COLOR, border=4)
            cgraFrame.is_selected = False
            # add command for frame
            cgraFrame.bind('<Button-1>', partial(cgra_frame_clicked, cgraId=cgraId, frame=cgraFrame))
            multiCgraCanvas.create_window(x, y, window=cgraFrame, height=cgraSquareLength, width=cgraSquareLength,
                                          anchor="nw")
            multiCgraCanvas.create_text(x + cgraSquareLength/2 + 5, y + cgraSquareLength + 10, font=customtkinter.CTkFont(weight="bold"),
                         text=f"CGRA {cgraId}", fill=MULTI_CGRA_TXT_COLOR)
            if (multiCgraParam.getCgraParam(row, col) == selectedCgraParam):
                cgra_frame_clicked(None, cgraId= cgraId, frame=cgraFrame)
                # current cgra param model is the selected one, hightlight it.
            cgraId = cgraId + 1

            # todo
            # mock the last col's tile to 3x3, need make it configurable
            # if(col != cols - 1):
            # if col == 0 and row == 0:
            create_cgra_tiles_on_multi_cgra_panel(multiCgraCanvas, x, y, 4, 4, cgraSquareLength)

            # router for each cgra frame
            multiCgraCanvas.create_oval(x + cgraSquareLength + distanceOfCgraAndRouter,
                                        y + cgraSquareLength + distanceOfCgraAndRouter,
                                        x + cgraSquareLength + distanceOfCgraAndRouter + routerDiameter,
                                        y + cgraSquareLength + distanceOfCgraAndRouter + routerDiameter, fill=MULTI_CGRA_FRAME_COLOR)
            # line between cgra and router
            multiCgraCanvas.create_line(x + cgraSquareLength, y + cgraSquareLength,
                                        x + cgraSquareLength + distanceOfCgraAndRouter + 5,
                                        y + cgraSquareLength + distanceOfCgraAndRouter + 5, fill=CANVAS_LINE_COLOR)

            routerCenterX, routerCenterY = x + cgraSquareLength + distanceOfCgraAndRouter + routerDiameter / 2, y + cgraSquareLength + distanceOfCgraAndRouter + routerDiameter / 2
            # if not last col: draws horizontal line, connects to right route
            if col != cgraCols - 1:
                rightRouterLeftEdgeX = routerCenterX + distanceOfCgras - routerDiameter / 2
                rightRouterCenterY = routerCenterY
                multiCgraCanvas.create_line(routerCenterX + routerDiameter / 2, routerCenterY, rightRouterLeftEdgeX, rightRouterCenterY, fill=CANVAS_LINE_COLOR, arrow=tkinter.BOTH, width=2)
                # multiCgraCanvas.create_line(rightRouterLeftEdgeX, rightRouterCenterY, routerCenterX + routerDiameter / 2, routerCenterY, fill=CANVAS_LINE_COLOR, arrow=tkinter.LAST, width=2)
            # if not last row: draws a vertical line, connects to down route
            if row != cgraRows - 1:
                downRouterCenterX = routerCenterX
                downRouterUpEdgeY = routerCenterY + distanceOfCgras - routerDiameter / 2
                multiCgraCanvas.create_line(routerCenterX, routerCenterY + routerDiameter / 2, downRouterCenterX, downRouterUpEdgeY, fill=CANVAS_LINE_COLOR, arrow=tkinter.BOTH, width=2)
                # multiCgraCanvas.create_line(downRouterCenterX, downRouterUpEdgeY, routerCenterX, routerCenterY + routerDiameter / 2, fill=CANVAS_LINE_COLOR, arrow=tkinter.LAST, width=2)

            x = x + distanceOfCgras
        # new row
        x = xStartPos
        y = y + distanceOfCgras


    vbar = customtkinter.CTkScrollbar(multiCgraPanel, orientation="vertical", command=multiCgraCanvas.yview)
    vbar.pack(side=tkinter.RIGHT, fill="y")
    multiCgraCanvas.config(yscrollcommand=vbar.set)

    scrollregionTuple = multiCgraCanvas.bbox("all")
    adjustTuple = (30, 30, -30, -30)
    adjustScrollregionTuple = tuple(x - y for x, y in zip(scrollregionTuple, adjustTuple))

    multiCgraCanvas.config(scrollregion=adjustScrollregionTuple)
    hbar = customtkinter.CTkScrollbar(multiCgraPanel, orientation="horizontal", command=multiCgraCanvas.xview)
    hbar.pack(side="bottom", fill="x")
    multiCgraCanvas.config(xscrollcommand=hbar.set)

    multiCgraCanvas.pack(side="top", fill="both", expand=True)

    return multiCgraPanel


def create_cgra_tiles_on_multi_cgra_panel(parentCanvas, rootX, rootY, rows, cols, cgraSquareLength):
    # mork cgra nxn
    intraCgraTileRows = rows
    intraCgraTileCols = cols
    tileXMargin, tileYMargin = 10, 10
    intraCgraTileMargin = 10

    # n*tileLen + (n-1)*tileMargin = (cgraSquareLength - intraCgraTileMargin*2)
    tileXLength = ((cgraSquareLength - intraCgraTileMargin * 2) - (
                intraCgraTileCols - 1) * tileXMargin) / intraCgraTileCols
    tileYLength = ((cgraSquareLength - intraCgraTileMargin * 2) - (
                intraCgraTileRows - 1) * tileYMargin) / intraCgraTileRows

    tileSquareLength = min(tileXLength, tileYLength)
    # need adjust tileXMargin
    if tileXLength > tileYLength:
        tileXMargin = ((cgraSquareLength - intraCgraTileMargin * 2) - (tileSquareLength * intraCgraTileCols)) / (
                    intraCgraTileCols - 1)
    else:
        tileYMargin = ((cgraSquareLength - intraCgraTileMargin * 2) - (tileSquareLength * intraCgraTileRows)) / (
                    intraCgraTileRows - 1)

    tileX, tileY = rootX + intraCgraTileMargin, rootY + intraCgraTileMargin
    for cgraRow in range(intraCgraTileRows):
        for cgraCol in range(intraCgraTileCols):
            cgraTileFrame = tkinter.Frame(parentCanvas, bg=MULTI_CGRA_TILE_COLOR, border=4)
            parentCanvas.create_window(tileX, tileY, window=cgraTileFrame, height=tileSquareLength,
                                          width=tileSquareLength,
                                          anchor="nw")
            tileX = tileX + tileSquareLength + tileXMargin
        tileX = rootX + intraCgraTileMargin
        tileY = tileY + tileSquareLength + tileYMargin


def create_multi_cgra_config_panel(master):
    multiCgraConfigPanel = customtkinter.CTkFrame(master, width=240)
    multiCgraConfigPanel.grid_propagate(0)
    # multiCgraConfigPanel.grid(row=0, column=1, sticky="nsew")
    for i in range(8):
        multiCgraConfigPanel.rowconfigure(i, weight=1)
    multiCgraConfigPanel.rowconfigure(8, weight=10)
    for i in range(2):
        multiCgraConfigPanel.columnconfigure(i, weight=1)

    multiCgraConfigLabel = customtkinter.CTkLabel(multiCgraConfigPanel, text='Multi-CGRA Modeling',
                                                font=customtkinter.CTkFont(size=FRAME_LABEL_FONT_SIZE, weight="bold"))
    multiCgraConfigLabel.grid(row=0, column=0, columnspan=2, ipadx=5, pady=(5, 0), sticky="nw")

    totalSRAMSizeLabel = customtkinter.CTkLabel(multiCgraConfigPanel, text='Per-CGRA\nSRAM (KBs):')
    totalSRAMSizeLabel.grid(row=1, column=0, padx=5, sticky="w")
    totalSRAMSizeLabelEntry = customtkinter.CTkEntry(multiCgraConfigPanel, justify=tkinter.CENTER)
    totalSRAMSizeLabelEntry.grid(row=1, column=1, padx=5)
    totalSRAMSizeLabelEntry.insert(0, str(32))

    interCgraTopologyLabel = customtkinter.CTkLabel(multiCgraConfigPanel, text='Inter-CGRA\ntopology:')
    interCgraTopologyLabel.grid(row=2, column=0, padx=5, sticky="w")
    interCgraTopologyOptions = [
        "Mesh",
        "Ring"
    ]
    topologyVariable = tkinter.StringVar(multiCgraConfigPanel)
    topologyVariable.set(interCgraTopologyOptions[0])
    topologyOptionMenu = customtkinter.CTkOptionMenu(multiCgraConfigPanel, variable=topologyVariable, values=interCgraTopologyOptions)
    topologyOptionMenu.grid(row=2, column=1, padx=5)

    multiCgraRowsLabel = customtkinter.CTkLabel(multiCgraConfigPanel, text='Multi-CGRA\nRows:')
    multiCgraRowsLabel.grid(row=3, column=0, padx=5, sticky="w")
    multiCgraRowsLabelEntry = customtkinter.CTkEntry(multiCgraConfigPanel, justify=tkinter.CENTER)
    multiCgraRowsLabelEntry.grid(row=3, column=1, padx=5)
    multiCgraRowsLabelEntry.insert(0, str(3))
    widgets["multiCgraRowsLabelEntry"] = multiCgraRowsLabelEntry

    multiCgraColumnsLabel = customtkinter.CTkLabel(multiCgraConfigPanel, text='Multi-CGRA\nColumns:')
    multiCgraColumnsLabel.grid(row=4, column=0, padx=5, sticky="w")
    multiCgraColumnsEntry = customtkinter.CTkEntry(multiCgraConfigPanel, justify=tkinter.CENTER)
    multiCgraColumnsEntry.grid(row=4, column=1, padx=5)
    multiCgraColumnsEntry.insert(0, str(3))
    widgets["multiCgraColumnsEntry"] = multiCgraColumnsEntry

    vectorLanesLabel = customtkinter.CTkLabel(multiCgraConfigPanel, text='Vector Lanes:')
    vectorLanesLabel.grid(row=5, column=0, padx=5, sticky="w")
    vectorLanesEntry = customtkinter.CTkEntry(multiCgraConfigPanel, justify=tkinter.CENTER)
    vectorLanesEntry.grid(row=5, column=1, padx=5)
    vectorLanesEntry.insert(0, str(4))

    dataBitwidthLabel = customtkinter.CTkLabel(multiCgraConfigPanel, text='Data Bitwidth:')
    dataBitwidthLabel.grid(row=6, column=0, padx=5, sticky="w")
    dataBitwidthEntry = customtkinter.CTkEntry(multiCgraConfigPanel, justify=tkinter.CENTER)
    dataBitwidthEntry.grid(row=6, column=1, padx=5)
    dataBitwidthEntry.insert(0, str(32))

    multiCgraConfigUpdateButton = customtkinter.CTkButton(multiCgraConfigPanel, text="Update", command=partial(clickMultiCgraUpdate, master))
    multiCgraConfigUpdateButton.grid(row=7, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

    return multiCgraConfigPanel


def clickMultiCgraUpdate(root):
    cgraRows = int(widgets["multiCgraRowsLabelEntry"].get())
    cgraCols = int(widgets["multiCgraColumnsEntry"].get())

    # Refreshes the multi-cgra data model when row/col changes
    global multiCgraParam
    global selectedCgraParam

    multiCgraParam = MultiCGRAParam(rows=cgraRows, cols=cgraCols, golbalWidgets = widgets)
    multiCgraParam.setSelectedCgra(0, 0)
    selectedCgraParam = multiCgraParam.getSelectedCgra()
    selectedCgraParam.set_cgra_param_callbacks(switchDataSPMOutLinks=switchDataSPMOutLinks,
                                               updateFunCheckoutButtons=updateFunCheckoutButtons,
                                               updateFunCheckVars=updateFunCheckVars,
                                               updateXbarCheckbuttons=updateXbarCheckbuttons,
                                               updateXbarCheckVars=updateXbarCheckVars,
                                               getFunCheckVars=getFunCheckVars,
                                               getXbarCheckVars= getXbarCheckVars)

    multiCgraPanel = create_multi_cgra_panel(root, cgraRows, cgraCols)
    multiCgraPanel.grid(row=0, column=0, padx=(0, 5), sticky="nsew")  
    create_cgra_pannel(root, selectedCgraParam.rows, selectedCgraParam.columns)
    create_param_pannel(root)


def create_cgra_pannel(master, rows, columns):
        # Clear previous CGRA panel if it exists
    if 'cgraPannel' in widgets:
        print("cgra_pannel exists, destroy the original view")
        widgets["cgraPannel"].destroy()

    print(f"create_cgra_pannel - ROWS: {rows}, COLS: {columns}")
    # master.grid_propagate(0)
    # Use solid black board to let the pannel look better
    cgraPannel = customtkinter.CTkFrame(master)
    widgets['cgraPannel'] = cgraPannel
    # cgraPannel = tkinter.LabelFrame(master, text='CGRA', bd=BORDER, relief='groove')
    # cgraPannel.grid(row=0, column=2, rowspan=1, columnspan=2, padx=(5, 5), sticky="nsew")
    # cgraPannel.pack()
    # cgraPannel.grid_propagate(0)
    # create label for cgraPannel
    cgraLabel = customtkinter.CTkLabel(cgraPannel, text='Per-CGRA (id: 0)', font=customtkinter.CTkFont(size=FRAME_LABEL_FONT_SIZE, weight="bold"))
    widgets['cgraLabel'] = cgraLabel

    widgets["cgraLabel"].configure(text=f"Per-CGRA (id: {multiCgraParam.getSelectedCgraId()})")

    # cgraLabel.grid(row=0, column=0, sticky="nsew")
    cgraLabel.pack(anchor="w", ipadx=5)

    canvas = customtkinter.CTkCanvas(cgraPannel, bg=CANVAS_BG_COLOR, bd=0, highlightthickness=0)
    # with Windows OS
    # canvas.bind_all("<MouseWheel>", partial(_on_mousewheel, canvas))
    # with Linux OS
    # canvas.bind_all("<Button-4>", partial(_on_mousewheel, canvas))
    # canvas.bind_all("<Button-5>", partial(_on_mousewheel, canvas))

    widgets["canvas"] = canvas
    baseX = 0

    # construct data memory
    if selectedCgraParam.dataSPM == None:
        dataSPM = ParamSPM(MEM_WIDTH, rows, rows)
        selectedCgraParam.initDataSPM(dataSPM)

    # pad contains tile and links
    # padSize = TILE_SIZE + LINK_LENGTH
    padHeight = TILE_HEIGHT + LINK_LENGTH
    padWidth = TILE_WIDTH + LINK_LENGTH

    GRID_HEIGHT = (TILE_HEIGHT + LINK_LENGTH) * rows - LINK_LENGTH
    # draw data memory
    memHeight = GRID_HEIGHT
    # spmLabel = tkinter.Button(canvas, text="Data\nSPM", fg='black', bg='gray', relief='raised', bd=BORDER,
    #                           command=clickSPM, highlightbackground="black", highlightthickness=HIGHLIGHT_THICKNESS)
    spmLabel = customtkinter.CTkButton(canvas, text="Data\nSPM",
                                       #fg='black', bg='gray', relief='raised', bd=BORDER,
                                       command=clickSPM#,
                                       #highlightbackground="black",
                                       #highlightthickness=HIGHLIGHT_THICKNESS
                                       )
    # Data memory will be placed in the upper left corner
    canvas.create_window(baseX + BORDER, BORDER, window=spmLabel, height=GRID_HEIGHT, width=MEM_WIDTH, anchor="nw")

    # construct tiles
    if len(selectedCgraParam.tiles) == 0:
        for i in range(rows):
            for j in range(columns):
                ID = i * columns + j
                posX = padWidth * j + MEM_WIDTH + LINK_LENGTH
                posY = GRID_HEIGHT - padHeight * i - TILE_HEIGHT

                tile = ParamTile(ID, j, i, posX, posY, TILE_WIDTH, TILE_HEIGHT)
                selectedCgraParam.addTile(tile)

    # draw tiles
    print(f"create_cgra_pannel - selectedCgraParam has : {selectedCgraParam.tiles} titles")

    for tile in selectedCgraParam.tiles:
        if not tile.disabled:
            # button = tkinter.Button(canvas, text="Tile " + str(tile.ID), fg='black', bg='gray', relief='raised',
            #                         bd=BORDER, command=partial(clickTile, tile.ID), highlightbackground="black",
            #                         highlightthickness=HIGHLIGHT_THICKNESS)
            button = customtkinter.CTkButton(canvas, text="Tile " + str(tile.ID),
                                    # fg='black', bg='gray', relief='raised', bd=BORDER,
                                    command=partial(clickTile, tile.ID)#,
                                    # highlightbackground="black",
                                    # highlightthickness=HIGHLIGHT_THICKNESS
                                    )
            posX, posY = tile.getPosXY()
            # Tiles will be placed near the Data memory
            canvas.create_window(posX, posY, window=button, height=TILE_HEIGHT, width=TILE_WIDTH, anchor="nw")

            # construct links
    if len(selectedCgraParam.templateLinks) == 0:
        for i in range(rows):
            for j in range(columns):
                if j < columns - 1:
                    # horizontal
                    tile0 = selectedCgraParam.getTileOfDim(j, i)
                    tile1 = selectedCgraParam.getTileOfDim(j + 1, i)
                    link0 = ParamLink(tile0, tile1, PORT_EAST, PORT_WEST)
                    link1 = ParamLink(tile1, tile0, PORT_WEST, PORT_EAST)
                    selectedCgraParam.addTemplateLink(link0)
                    selectedCgraParam.addTemplateLink(link1)

                if i < rows - 1 and j < columns - 1:
                    # diagonal left bottom to right top
                    tile0 = selectedCgraParam.getTileOfDim(j, i)
                    tile1 = selectedCgraParam.getTileOfDim(j + 1, i + 1)
                    link0 = ParamLink(tile0, tile1, PORT_NORTHEAST, PORT_SOUTHWEST)
                    link1 = ParamLink(tile1, tile0, PORT_SOUTHWEST, PORT_NORTHEAST)
                    selectedCgraParam.addTemplateLink(link0)
                    selectedCgraParam.addTemplateLink(link1)

                if i < rows - 1 and j > 0:
                    # diagonal left top to right bottom
                    tile0 = selectedCgraParam.getTileOfDim(j, i)
                    tile1 = selectedCgraParam.getTileOfDim(j - 1, i + 1)
                    link0 = ParamLink(tile0, tile1, PORT_NORTHWEST, PORT_SOUTHEAST)
                    link1 = ParamLink(tile1, tile0, PORT_SOUTHEAST, PORT_NORTHWEST)
                    selectedCgraParam.addTemplateLink(link0)
                    selectedCgraParam.addTemplateLink(link1)

                if i < columns - 1:
                    # vertical
                    tile0 = selectedCgraParam.getTileOfDim(j, i)
                    tile1 = selectedCgraParam.getTileOfDim(j, i + 1)
                    link0 = ParamLink(tile0, tile1, PORT_NORTH, PORT_SOUTH)
                    link1 = ParamLink(tile1, tile0, PORT_SOUTH, PORT_NORTH)
                    selectedCgraParam.addTemplateLink(link0)
                    selectedCgraParam.addTemplateLink(link1)

                if j == 0:
                    # connect to memory
                    tile0 = selectedCgraParam.getTileOfDim(j, i)
                    link0 = ParamLink(tile0, selectedCgraParam.dataSPM, PORT_WEST, i)
                    link1 = ParamLink(selectedCgraParam.dataSPM, tile0, i, PORT_WEST)
                    selectedCgraParam.addTemplateLink(link0)
                    selectedCgraParam.addTemplateLink(link1)

    selectedCgraParam.updateLinks()
    selectedCgraParam.updateFuXbarPannel()

    # draw links
    for link in selectedCgraParam.updatedLinks:
        if link.disabled:
            pass
        else:
            srcX, srcY = link.getSrcXY()
            dstX, dstY = link.getDstXY()
            canvas.create_line(srcX, srcY, dstX, dstY, arrow=tkinter.LAST, fill=CANVAS_LINE_COLOR)

    vbar = customtkinter.CTkScrollbar(cgraPannel, orientation="vertical", command=canvas.yview)
    vbar.pack(side=tkinter.RIGHT, fill="y")
    canvas.config(yscrollcommand=vbar.set)
    canvas.config(scrollregion=canvas.bbox("all"))
    canvas.pack(side="top", fill="both", expand=True)
    hbar = customtkinter.CTkScrollbar(cgraPannel, orientation="horizontal", command=canvas.xview)
    hbar.pack(side="bottom", fill="x")
    canvas.config(xscrollcommand=hbar.set)

    cgraPannel.grid(row=0, column=2, rowspan=1, columnspan=2, padx=(5, 5), sticky="nsew")

    return cgraPannel

def place_fu_options(master):
    fuCount = len(fuTypeList)
    for i in range(len(fuTypeList)):
        fuVar = tkinter.IntVar()
        fuCheckVars[fuTypeList[i]] = fuVar
        fuCheckbutton = customtkinter.CTkCheckBox(master, variable=fuVar, text=fuTypeList[i],
                                            command=partial(clickFuCheckbutton, fuTypeList[i]))
        fuCheckbuttons[fuTypeList[i]] = fuCheckbutton
        fuCheckbutton.select()
        selectedCgraParam.updateFuCheckbutton(fuTypeList[i], fuVar.get())
        fuCheckbutton.grid(row=(i // 2), column=i % 2, pady=6)


def place_xbar_options(master):
    for i in range(PORT_DIRECTION_COUNTS):
        portType = i
        xbarType = xbarPort2Type[i]
        xbarVar = tkinter.IntVar()
        xbarCheckVars[xbarType] = xbarVar
        xbarCheckbutton = customtkinter.CTkCheckBox(master, variable=xbarVar, text=xbarType,
                                              command=partial(clickXbarCheckbutton, xbarType))
        xbarCheckbuttons[xbarType] = xbarCheckbutton

        if selectedCgraParam.getTileOfID(0).xbarDict[xbarType] == 1:
            xbarCheckbutton.select()

        selectedCgraParam.updateXbarCheckbutton(xbarType, xbarVar.get())

        if portType in selectedCgraParam.getTileOfID(0).neverUsedOutPorts:
            xbarCheckbutton.configure(state="disabled")

        # xbarCheckbutton.grid(row=(i // 3)+1, column=i % 3, padx=15, pady=15, sticky="nsew")
        if i== PORT_NORTH:
            xbarCheckbutton.grid(row=0, column=1, padx=5, pady=(6, 25))
        elif i== PORT_SOUTH:
            xbarCheckbutton.grid(row=2, column=1, padx=5, pady=25)
        elif i== PORT_WEST:
            xbarCheckbutton.grid(row=1, column=0, padx=5, pady=25)
        elif i== PORT_EAST:
            xbarCheckbutton.grid(row=1, column=2, padx=5, pady=25)
        elif i== PORT_NORTHWEST:
            xbarCheckbutton.grid(row=0, column=0, padx=5, pady=(6, 25))
        elif i== PORT_NORTHEAST:
            xbarCheckbutton.grid(row=0, column=2, padx=5, pady=(6, 25))
        elif i== PORT_SOUTHEAST:
            xbarCheckbutton.grid(row=2, column=2, padx=5, pady=25)
        elif i== PORT_SOUTHWEST:
            xbarCheckbutton.grid(row=2, column=0, padx=5, pady=25)

        # centralRadioButton = customtkinter.CTkRadioButton(master, text='Tile 0', variable=tkinter.IntVar(value=0))
        # centralRadioButton.configure(state="disabled")
        # centralRadioButton.grid(row=1, column=1, padx=5, pady=25)
        # widgets["centralRadioButton"] = centralRadioButton
        xbarCentralTilelabel = customtkinter.CTkLabel(master, text='Tile 0', font=customtkinter.CTkFont(weight="bold", underline=True))
        xbarCentralTilelabel.grid(row=1, column=1, padx=(0, 5), pady=25)
        widgets["xbarCentralTilelabel"] = xbarCentralTilelabel

def create_param_pannel(master):
    # paramPannel = tkinter.LabelFrame(master, text='Configuration', bd=BORDER, relief='groove')
    paramPannel = customtkinter.CTkFrame(master, width=550, height=480)
    # paramPannel.grid(row=0, column=4, columnspan=2, sticky="nsew")

    # Use columnconfigure and rowconfigure to partition the columns, so that each column and row will fill the corresponding space
    # The 'weight' represents the weight of the corresponding row/column length
    for i in range(9):
        paramPannel.rowconfigure(i, weight=1)
    for i in range(3):
        paramPannel.columnconfigure(i, weight=1)
    paramPannel.grid_propagate(0)
    configurationLabel = customtkinter.CTkLabel(paramPannel, text='Per-CGRA Modeling', font=customtkinter.CTkFont(size=FRAME_LABEL_FONT_SIZE, weight="bold"))
    configurationLabel.grid(row=0, column=0, columnspan=2, padx=(5,0), pady=(5,0), sticky="nw")

    rowsLabel = customtkinter.CTkLabel(paramPannel, text='Rows  Columns:')
    rowsLabel.grid(row=1, column=0)
    rowsEntry = customtkinter.CTkEntry(paramPannel, justify=tkinter.CENTER#,
                                       #highlightbackground="black",
                                       #highlightthickness=HIGHLIGHT_THICKNESS
                                       )
    rowsEntry.grid(row=1, column=1, padx=5, pady=5)
    rowsEntry.insert(0, str(selectedCgraParam.rows))
    widgets["rowsEntry"] = rowsEntry
    columnsEntry = customtkinter.CTkEntry(paramPannel, justify=tkinter.CENTER#,
                                          #highlightbackground="black",
                                          #highlightthickness=HIGHLIGHT_THICKNESS
                                          )
    columnsEntry.grid(row=1, column=2, padx=2, pady=5)
    columnsEntry.insert(0, str(selectedCgraParam.columns))
    widgets["columnsEntry"] = columnsEntry

    dataMemLabel = customtkinter.CTkLabel(paramPannel, text='Per-Bank SRAM (KBs):')
    dataMemLabel.grid(row=2, column=0)
    dataMemEntry = customtkinter.CTkEntry(paramPannel, justify=tkinter.CENTER#,
                                          #highlightbackground="black",
                                          #highlightthickness=HIGHLIGHT_THICKNESS
                                          )
    dataMemEntry.grid(row=2, column=1, padx=5, pady=5)
    dataMemEntry.insert(0, str(selectedCgraParam.dataMemSize))
    widgets["dataMemEntry"] = dataMemEntry
    resetButton = customtkinter.CTkButton(paramPannel, text="Reset",
                                          #relief='raised',
                                          command=partial(clickReset, master)#,
                                          #highlightbackground="black", highlightthickness=HIGHLIGHT_THICKNESS
                                          )
    resetButton.grid(row=2, column=2, columnspan=2)


    configMemLabel = customtkinter.CTkLabel(paramPannel, text='Config Memory \n (entries/tile):')
    configMemLabel.grid(row=3, column=0)
    configMemEntry = customtkinter.CTkEntry(paramPannel, justify=tkinter.CENTER#,
                                            #highlightbackground="black",
                                            #highlightthickness=HIGHLIGHT_THICKNESS
                                            )
    configMemEntry.grid(row=3, column=1, pady=5)
    configMemEntry.insert(0, selectedCgraParam.configMemSize)
    widgets["configMemEntry"] = configMemEntry
    updateButton = customtkinter.CTkButton(paramPannel, text="Update",
                                           #relief='raised',
                                           command=partial(clickUpdate, master)#,
                                           #highlightbackground="black", highlightthickness=HIGHLIGHT_THICKNESS
                                           )
    updateButton.grid(row=3, column=2, columnspan=2)


    entireTileCheckVar.set(0)
    entireTileCheckbutton = customtkinter.CTkCheckBox(paramPannel, variable=entireTileCheckVar, text="Disable entire Tile 0", command=clickEntireTileCheckbutton)
    entireTileCheckbutton.grid(row=4, column=0, columnspan=2, padx=(5,0), sticky="w")
    widgets["entireTileCheckbutton"] = entireTileCheckbutton


    # Data SPM outgoing links
    spmConfigPannel = customtkinter.CTkScrollableFrame(paramPannel, label_text="Data SPM\noutgoing links", width=80)
    spmConfigPannel.grid(row=5, column=0, rowspan=3, pady=(5,0), sticky="nsew")
    widgets["spmConfigPannel"] = spmConfigPannel
    # spmConfigPannel.rowconfigure(0, weight=1)
    # spmConfigPannel.rowconfigure(1, weight=3)
    # for i in range(4):
    #     spmConfigPannel.columnconfigure(i, weight=1)
    # spmConfigPannel.grid_propagate(0)
    # spmConfigPannelLabel = customtkinter.CTkLabel(spmConfigPannel, text='Data SPM\noutgoing links',
    #                                               font=customtkinter.CTkFont(size=FRAME_LABEL_LEVEL_1_FONT_SIZE,
    #                                                                          weight="bold", slant='italic'))
    # spmConfigPannelLabel.grid(row=0, column=0, sticky="nsew")
    # spmConfigPannelLabel.pack()
    # spmConfigPannelLabel.grid_propagate(0)
    # spmConfigScrollablePannel = customtkinter.CTkScrollableFrame(spmConfigPannel, height=240)
    # spmConfigScrollablePannel.grid(row=1, column=0, sticky="nsew")
    # spmConfigScrollablePannel.pack()

    spmOutlinksSwitches = []
    # for i in range(10):
    #     switch = customtkinter.CTkSwitch(spmConfigScrollablePannel, text=f"link {i}")
    #     switch.select()
    #     # switch.grid(row=i + 1, column=0, padx=5, pady=(0, 10))
    #     switch.pack(pady=(5, 10))
    #     scrollable_frame_switches.append(switch)
    for port in selectedCgraParam.dataSPM.outLinks:
        switch = customtkinter.CTkSwitch(spmConfigPannel, text=f"link {port}", command=switchDataSPMOutLinks)
        if not selectedCgraParam.dataSPM.outLinks[port].disabled:
            switch.select()
        switch.pack(pady=(5, 10))
        spmOutlinksSwitches.insert(0, switch)
    widgets['spmOutlinksSwitches'] = spmOutlinksSwitches



    # Tile x functional units
    fuConfigPannel = customtkinter.CTkScrollableFrame(paramPannel, label_text="Tile 0\nfunctional units")
    fuConfigPannel.grid(row=5, column=1, rowspan=3, padx=(5,5), pady=(5,0), sticky="nsew")
    widgets["fuConfigPannel"] = fuConfigPannel

    # Use columnconfigure to partition the columns, so that each column fills the corresponding space
    # for i in range(2):
    #     fuConfigPannel.columnconfigure(i, weight=1)
    # fuConfigPannel.grid_propagate(0)
    # fuConfigPannelLabel = customtkinter.CTkLabel(fuConfigPannel, text='Tile 0\nfunctional units',
    #                                              font=customtkinter.CTkFont(size=FRAME_LABEL_LEVEL_1_FONT_SIZE,
    #                                                                         weight="bold", slant='italic'))
    # fuConfigPannelLabel.grid(row=0, column=0, sticky="nsew")
    # fuConfigPannelLabel.pack()
    # widgets["fuConfigPannelLabel"] = fuConfigPannelLabel
    # fuConfigSubPannel = customtkinter.CTkFrame(fuConfigPannel)
    for i in range(2):
        fuConfigPannel.columnconfigure(i, weight=1)
    place_fu_options(fuConfigPannel)
    # fuConfigSubPannel.pack()


    # Tile x crossbar outgoing links
    xbarConfigPannel = customtkinter.CTkScrollableFrame(paramPannel, label_text="Tile 0\ncrossbar outgoing links")
    xbarConfigPannel.grid(row=5, column=2, rowspan=3, pady=(5, 0), sticky="nsew")
    widgets["xbarConfigPannel"] = xbarConfigPannel

    # Use columnconfigure to partition the columns, so that each column fills the corresponding space
    # for i in range(3):
    #     xbarConfigPannel.columnconfigure(i, weight=1)
    # for i in range(4):
    #     xbarConfigPannel.rowconfigure(i, weight=1)
    # xbarConfigPannel.grid_propagate(0)
    # xbarConfigPannelLabel = customtkinter.CTkLabel(xbarConfigPannel, text='Tile 0\ncrossbar outgoing links',
    #                                                font=customtkinter.CTkFont(size=FRAME_LABEL_LEVEL_1_FONT_SIZE,
    #                                                                           weight="bold", slant='italic'))
    # # xbarConfigPannelLabel.grid(row=0, column=0, sticky="nsew")
    # xbarConfigPannelLabel.pack()
    # widgets["xbarConfigPannelLabel"] = xbarConfigPannelLabel
    # xbarConfigSubPannel = customtkinter.CTkFrame(xbarConfigPannel)
    for i in range(3):
        xbarConfigPannel.columnconfigure(i, weight=1)
    for i in range(3):
        xbarConfigPannel.rowconfigure(i, weight=1)
    place_xbar_options(xbarConfigPannel)
    # xbarConfigSubPannel.pack()
    paramPannel.grid(row=0, column=4, columnspan=2, sticky="nsew")

    return paramPannel


def create_test_pannel(master):
    dataPannel = customtkinter.CTkFrame(master, width=80, height=480)
    # dataPannel.grid(row=1, column=4, pady=(5,0), sticky="nsew")
    # Increase the size of the 'SVerilog' panel
    dataPannel.grid_rowconfigure(1, weight=2)

    dataPannel.grid_columnconfigure(0, weight=1)
    dataPannel.grid_columnconfigure(1, weight=1)
    dataPannel.grid_columnconfigure(2, weight=1)
    dataPannel.grid_propagate(0)
    # testPannel = tkinter.LabelFrame(dataPannel, text='Verification', bd=BORDER, relief='groove')
    testPannel = customtkinter.CTkFrame(dataPannel)
    testPannel.grid(row=0, column=0, rowspan=1, columnspan=3, sticky="nsew")
    testPannel.columnconfigure(0, weight=1)
    testPannel.columnconfigure(1, weight=1)
    testPannel.columnconfigure(2, weight=1)
    testPannelLabel = customtkinter.CTkLabel(testPannel, text='Verification ',
                                             # width=100,
                                             font=customtkinter.CTkFont(size=FRAME_LABEL_FONT_SIZE, weight="bold"))
    testPannelLabel.grid(row=0, column=0, columnspan=3, ipadx=5, sticky="w")
    testButton = customtkinter.CTkButton(testPannel, text="Run tests", # relief='raised',
                                         command=clickTest,
                                         width=50
                                         # highlightbackground="black", highlightthickness=HIGHLIGHT_THICKNESS
                                         )
    testButton.grid(row=1, column=0, ipadx=5)
    # testProgress = ttk.Progressbar(testPannel, orient='horizontal', mode='determinate')
    testProgress = customtkinter.CTkProgressBar(testPannel, orientation='horizontal', mode='determinate', width=160)
    testProgress.set(0)
    widgets["testProgress"] = testProgress
    testProgress.grid(row=1, column=1, rowspan=1, columnspan=1, padx=5, sticky="w")
    testShow = customtkinter.CTkLabel(testPannel, text="IDLE ")
    widgets["testShow"] = testShow
    testShow.grid(row=1, column=2, sticky=tkinter.E, padx=(5, 5))

    # verilogPannel = tkinter.LabelFrame(dataPannel, text="SVerilog", bd=BORDER, relief="groove")
    verilogPannel = customtkinter.CTkFrame(dataPannel)
    verilogPannel.grid(row=1, column=0, rowspan=1, columnspan=3, pady=(5,5), sticky="nsew")
    verilogPannelLabel = customtkinter.CTkLabel(verilogPannel, text='SVerilog ',
                                             # width=100,
                                             font=customtkinter.CTkFont(size=FRAME_LABEL_FONT_SIZE,
                                                                        weight="bold"))
    verilogPannelLabel.pack(anchor="w", padx=(5,0))
    CreateToolTip(verilogPannel,
                  text="The code might be too big to be copied,\nthe generated verilog can be found in\nthe 'verilog' folder.")
    generateVerilogButton = customtkinter.CTkButton(verilogPannel, text="Generate", width=50,
                                           command=clickGenerateVerilog)
    generateVerilogButton.pack(side=tkinter.BOTTOM, anchor="sw", padx=BORDER, pady=BORDER)
    # verilogScroll = tkinter.Scrollbar(verilogPannel, orient="vertical")
    # verilogScroll.pack(side=tkinter.RIGHT, fill="y")
    # verilogText = tkinter.Text(verilogPannel, yscrollcommand=verilogScroll.set, width=10, height=5)
    # verilogText.pack(side=tkinter.LEFT, fill="both", expand=True)
    # verilogScroll.config(command=verilogText.yview)
    verilogText = customtkinter.CTkTextbox(verilogPannel, width=10, height=5)
    verilogText.pack(side=tkinter.LEFT, fill="both", expand=True)
    widgets["verilogText"] = verilogText

    # reportPannel = tkinter.LabelFrame(dataPannel, text='Report area/power', bd=BORDER, relief='groove')
    reportPannel = customtkinter.CTkFrame(dataPannel)
    reportPannel.grid(row=2, column=0, rowspan=1, columnspan=3, sticky='nesw')
    reportPannel.columnconfigure(0, weight=1)
    reportPannel.columnconfigure(1, weight=1)
    reportPannelLabel = customtkinter.CTkLabel(reportPannel, text='Report Area/Power ',
                                             # width=100,
                                             font=customtkinter.CTkFont(size=FRAME_LABEL_FONT_SIZE,
                                                                        weight="bold"))

    reportButton = customtkinter.CTkButton(reportPannel, text="Synthesize", command=clickSynthesize, width=60)

    reportProgress = customtkinter.CTkProgressBar(reportPannel, orientation="horizontal", mode="determinate", width=140)
    reportProgress.set(0)
    widgets["reportProgress"] = reportProgress

    synthesisTimeEntry = customtkinter.CTkEntry(reportPannel, justify=tkinter.CENTER)
    widgets["synthesisTimeEntry"] = synthesisTimeEntry

    reportTimecostLabel = customtkinter.CTkLabel(reportPannel, text=" Time cost:")
    CreateToolTip(reportTimecostLabel, text="Time is in s.")

    reportTileAreaLabel = customtkinter.CTkLabel(reportPannel, text=" Tiles area:")
    CreateToolTip(reportTileAreaLabel, text="Area is in mm^2.")

    reportTileAreaData = customtkinter.CTkEntry(reportPannel, justify=tkinter.CENTER)
    widgets["reportTileAreaData"] = reportTileAreaData

    reportTilePowerLabel = customtkinter.CTkLabel(reportPannel, text="Tiles power:")
    CreateToolTip(reportTilePowerLabel, text="Yosys is not able to provide\npower estimation.")

    reportTilePowerData = customtkinter.CTkEntry(reportPannel, justify=tkinter.CENTER)
    widgets["reportTilePowerData"] = reportTilePowerData

    reportSPMAreaLabel = customtkinter.CTkLabel(reportPannel, text=" SPM area:")
    CreateToolTip(reportSPMAreaLabel, text="Area is in mm^2.")

    reportSPMAreaData = customtkinter.CTkEntry(reportPannel, justify=tkinter.CENTER)
    widgets["reportSPMAreaData"] = reportSPMAreaData

    reportSPMPowerLabel = customtkinter.CTkLabel(reportPannel, text="SPM power:")
    CreateToolTip(reportSPMPowerLabel, text="Power is in mW.")

    reportSPMPowerData = customtkinter.CTkEntry(reportPannel, justify=tkinter.CENTER)
    widgets["reportSPMPowerData"] = reportSPMPowerData

    reportPannelLabel.grid(row=0, column=0, columnspan=2, padx=(5,0), sticky="w")
    reportButton.grid(row=1, column=0)
    reportProgress.grid(row=1, column=1)

    synthesisTimeEntry.grid(row=2, column=1, pady=5)
    reportTimecostLabel.grid(row=2, column=0, pady=5)

    reportTileAreaLabel.grid(row=3, column=0, pady=5)
    reportTileAreaData.grid(row=3, column=1, pady=5)
    reportTilePowerLabel.grid(row=4, column=0, pady=5)
    reportTilePowerData.grid(row=4, column=1, pady=5)

    reportSPMAreaLabel.grid(row=5, column=0, pady=5)
    reportSPMAreaData.grid(row=5, column=1, pady=5)
    reportSPMPowerLabel.grid(row=6, column=0, pady=5)
    reportSPMPowerData.grid(row=6, column=1, pady=5)

    return dataPannel

def create_layout_pannel(master):
    layoutPannel = customtkinter.CTkFrame(master, width=80)
    # layoutPannel.grid(row=1, column=5, padx=(5,0), pady=(5,0), sticky="nsew")
    layoutPannel.grid_propagate(0)
    for row in range(5):
        layoutPannel.grid_rowconfigure(row, weight=1)
    layoutPannel.grid_rowconfigure(5, weight=40)
    layoutPannel.grid_columnconfigure(0, weight=1)
    layoutPannel.grid_columnconfigure(1, weight=1)
    layoutPannelLabel = customtkinter.CTkLabel(layoutPannel, text='Layout ',
                                               # width=100,
                                               font=customtkinter.CTkFont(size=FRAME_LABEL_FONT_SIZE, weight="bold"))
    layoutPannelLabel.grid(row=0, column=0, padx=(5,0), sticky="nw")

    # Adds the entry for user to select constraint.sdc
    constraintLabel = customtkinter.CTkLabel(layoutPannel, text="Constraint.sdc")
    constraintLabel.grid(row=1, column=0)
    constraintPathEntry = customtkinter.CTkEntry(layoutPannel)
    constraintPathEntry.grid(row=1, column=1)
    constraintPathEntry.bind("<Button-1>", clickSelectConstraintFile)
    widgets["constraintPathEntry"] = constraintPathEntry

    # Adds the entry for user to select config.mk
    configLabel = customtkinter.CTkLabel(layoutPannel, text="Config.mk")
    configLabel.grid(row=2, column=0, padx=(0, 5))
    configPathEntry = customtkinter.CTkEntry(layoutPannel)
    configPathEntry.grid(row=2, column=1)
    configPathEntry.bind("<Button-1>", clickSelectConfigFile)
    widgets["configPathEntry"] = configPathEntry

    # Adds the option menu to select process technology.
    processNameLabel = customtkinter.CTkLabel(layoutPannel, text="Process:")
    processNameLabel.grid(row=3, column=0)
    tempOptions = ["asap7", "nangate45", "sky130hd"]
    processNameMenu = customtkinter.CTkOptionMenu(layoutPannel, variable=processOptions, values=tempOptions)
    processNameMenu.grid(row=3, column=1, padx=(5, 5))

    # Adds the button to trigger RTL->Layout flow.
    openRoadButton = customtkinter.CTkButton(layoutPannel, text="RTL -> Layout", command=clickRTL2Layout)
    openRoadButton.grid(row=4, column=0, columnspan=2, sticky='we', padx=(10, 10))

    # Adds a placeholder to show the layout image saved from OpenRoad.
    global layoutLabel
    layoutLabel = customtkinter.CTkLabel(layoutPannel, text='')
    layoutLabel.grid(row=5, column=0, padx=(0, 5), pady=(5, 5), columnspan=2)

    return layoutPannel
"""
    canvas = customtkinter.CTkCanvas(layoutPannel, bg=CANVAS_BG_COLOR, bd=0, highlightthickness=0)
    scrollbar = customtkinter.CTkScrollbar(layoutPannel, orientation="horizontal", command=canvas.xview)
    scrollbar.pack(side="bottom", fill="x")
    canvas.config(xscrollcommand=scrollbar.set)
    canvas.pack(side="top", fill="both", expand=True)
    layout_frame = customtkinter.CTkFrame(canvas)
    canvas.create_window((0, 0), window=layout_frame, anchor="nw")
    showButton = customtkinter.CTkButton(layoutPannel, text="Display layout")
    CreateToolTip(showButton, text="The layout demonstration is\nunder development.")
    showButton.place(relx=0.5, rely=0.1, anchor="center")
"""

def constructDependencyFiles(cgraflow_basepath, standard_module_name, test_platform_name, verilog_srcfile_path, mk_sdc_file_path, orfs_basePath):
    # Finds the target RTL design and transforms the format.
    files = os.listdir(cgraflow_basepath + "/build/verilog")
    for f in files:
        # Finds the generated verilog file.
        if f == "design.v":
            os.chdir(cgraflow_basepath + "/build/verilog")
            # Manually copies design.v to design.sv to make sv2v work normally.
            print("Renaming the system verilog file generated by PyMTL3.")
            subprocess.run(["cp design.v design.sv"], shell=True, encoding="utf-8")
            # Uses sv2v to convert system verilog to verilg.
            print("Converting the system verilog file to verilog file.")
            subprocess.run(["../../tools/sv2v/bin/sv2v --write=adjacent " + "design.sv"], shell=True, encoding="utf-8")
            # Changes the top module name in design.v to standard_module_name.
            print("Standardizing the top module name in verilog file.")
            contents = ""
            with open("design.v", "r", encoding="utf-8") as lines:
                for line in lines:
                    if standard_module_name in line:
                        line = "module " + standard_module_name + " ("
                    contents += line
            with open(standard_module_name + ".v", "w", encoding="utf-8") as newFile:
                newFile.write(contents)
            break

    # Makes directories and copies CGRATemplateRTL.v, the pre-defined config.mk, and constraint.sdc to their respective directories.
    global constraintFilePath, configFilePath
    os.chdir(orfs_basePath)
    subprocess.run(["mkdir -p " + verilog_srcfile_path], shell=True, encoding="utf-8")
    subprocess.run(["cp " + cgraflow_basepath + "/build/verilog/" + standard_module_name + ".v " + verilog_srcfile_path], shell=True, encoding="utf-8")
    subprocess.run(["mkdir -p " + mk_sdc_file_path], shell=True, encoding="utf-8")
    subprocess.run(["cp " + constraintFilePath + " " + mk_sdc_file_path], shell=True, encoding="utf-8")
    subprocess.run(["cp " + configFilePath + " " + mk_sdc_file_path], shell=True, encoding="utf-8")

    # Updates process within the config.mk to the user selected one.
    with open(mk_sdc_file_path + "config.mk", 'r') as file:
        # Reads all lines within the file.
        lines = file.readlines()
        # Modifies the first line, replaces the PLATFORM with the user selected process technology.
        lines[0] = "export PLATFORM         = " + test_platform_name + "\n"
    with open(mk_sdc_file_path + "config.mk", 'w') as file:
        # Writes the updated content back to config.mk.
        file.writelines(lines)

def runOpenRoad(mk_sdc_file_path, cmd_path, odb_path, layout_path):
    # Runs the test module from RTL to GDSII.
    subprocess.run(["make DESIGN_CONFIG=./" + mk_sdc_file_path + "config.mk"], shell=True, encoding="utf-8")
    # Generates a cmd.tcl file for openroad
    if os.path.exists(cmd_path):
        os.remove(cmd_path)
    with open(cmd_path, mode="a", encoding="utf-8") as file:
        # Load the test module layout file.
        file.write("read_db " + odb_path + "\n")
        # Saves layout to image.
        file.write("save_image " + layout_path + "\n")
        file.write("exit")
    # Runs openroad.
    subprocess.run(["openroad", cmd_path], shell=False, encoding="utf-8")

def clickRTL2Layout():
    global constraintFilePath, configFilePath
    standard_module_name = "CGRATemplateRTL"
    cgraflow_basepath = os.path.dirname(os.path.abspath(__file__))
    test_platform_name = processOptions.get()
    print("Test platform is %s" % (test_platform_name))
    orfs_basePath = cgraflow_basepath + "/tools/OpenROAD-flow-scripts/flow/"
    layout_path = cgraflow_basepath + "/build/" + "layout.png"
    odb_path = orfs_basePath + "results/" + test_platform_name + "/" + standard_module_name + "/base/6_final.odb"
    cmd_path = orfs_basePath + "cmd.tcl"
    verilog_srcfile_path = "designs/src/" + standard_module_name + "/"
    mk_sdc_file_path = "designs/" + test_platform_name + "/" + standard_module_name  + "/"

    if constraintFilePath == ""  or configFilePath == "":
         tkinter.messagebox.showerror(title="Missing files for RTL->Layout",
                                     message="constraint.sdc and config.mk need to be selected first.")
         return

    # Checks if layout.png of target design already exists.
    # If yes, directly shows.
    if os.path.exists(layout_path):
        display_layout_image(layout_path)
    # If not, runs the design from RTL to GDSII and saves layout.png, finally shows.
    else:
        # Generates all dependency files for openroad.
        constructDependencyFiles(cgraflow_basepath, standard_module_name, test_platform_name,
                                verilog_srcfile_path, mk_sdc_file_path, orfs_basePath)
        # Runs openroad.
        runOpenRoad(mk_sdc_file_path, cmd_path, odb_path, layout_path)
        # Shows the layout image on CGRA-Flow GUI.
        display_layout_image(layout_path)

def clickSelectConstraintFile(event):
    global constraintFilePath
    constraintFilePath = fd.askopenfilename(title="Chooses constraint.sdc for synthesis.", initialdir="./", filetypes=(("SDC file", "*.sdc"),))
    widgets["constraintPathEntry"].delete(0, tkinter.END)
    widgets["constraintPathEntry"].insert(0, constraintFilePath)
    print(constraintFilePath)

def clickSelectConfigFile(event):
    global configFilePath
    configFilePath = fd.askopenfilename(title="Chooses config.mk for OpenRoad.", initialdir="./", filetypes=(("MK file", "*.mk"),))
    widgets["configPathEntry"].delete(0, tkinter.END)
    widgets["configPathEntry"].insert(0, configFilePath)
    print(configFilePath)

def display_layout_image(image_path):
    layoutImage = customtkinter.CTkImage(light_image=Image.open(image_path),
                                  dark_image=Image.open(image_path),
                                  size=(320, 320))
    layoutLabel.configure(image=layoutImage)

def create_mapping_pannel(master):
    # mappingPannel = tkinter.LabelFrame(master, text='Mapping', bd=BORDER, relief='groove')
    mappingPannel = customtkinter.CTkFrame(master)
    # mappingPannel.grid(row=1, column=1, rowspan=1, columnspan=3, padx=(0, 5), pady=(5, 0), sticky="nsew")
    mappingPannelLabel = customtkinter.CTkLabel(mappingPannel, text='Mapping ',
                                               # width=100,
                                               font=customtkinter.CTkFont(size=FRAME_LABEL_FONT_SIZE,
                                                                          weight="bold"))
    mappingPannelLabel.pack(anchor="w", padx=(5, 0))
    mappingCanvas = customtkinter.CTkCanvas(mappingPannel, bg=CANVAS_BG_COLOR, bd=0, highlightthickness=0)
    widgets["mappingCanvas"] = mappingCanvas
    hbar = customtkinter.CTkScrollbar(mappingPannel, orientation="horizontal", command=mappingCanvas.xview)
    hbar.pack(side="bottom", fill="x")
    mappingCanvas.config(xscrollcommand=hbar.set)
    vbar = customtkinter.CTkScrollbar(mappingPannel, orientation="vertical", command=mappingCanvas.yview)
    vbar.pack(side=tkinter.RIGHT, fill="y")
    mappingCanvas.config(yscrollcommand=vbar.set)
    mappingCanvas.pack(side="top", fill="both", expand=True)

    return mappingPannel


def create_kernel_pannel(master):
    # kernelPannel = tkinter.LabelFrame(master, text="Kernel", bd=BORDER, relief='groove')
    kernelPannel = customtkinter.CTkFrame(master, width=280)
    kernelPannel.grid_propagate(0)
    # kernelPannel.grid(row=1, column=0, padx=(0, 5), pady=(5, 0), sticky="nsew")
    for row in range(14):
        kernelPannel.grid_rowconfigure(row, weight=1)
    kernelPannel.grid_rowconfigure(5, weight=2)
    kernelPannel.grid_columnconfigure(0, weight=3)
    kernelPannel.grid_columnconfigure(1, weight=2)
    kernelPannel.grid_columnconfigure(2, weight=2)
    kernelPannel.grid_columnconfigure(3, weight=1)

    kernelPannellLabel = customtkinter.CTkLabel(kernelPannel, text='Kernel ',
                                                # width=100,
                                                font=customtkinter.CTkFont(size=FRAME_LABEL_FONT_SIZE,
                                                                           weight="bold"))
    kernelPannellLabel.grid(row=0, column=0, padx=(5, 0), sticky="wn")

    selectAppLabel = customtkinter.CTkLabel(kernelPannel, text=" Application:")
    selectAppLabel.grid(row=1, column=0)

    appPathEntry = customtkinter.CTkEntry(kernelPannel)
    widgets["appPathEntry"] = appPathEntry
    appPathEntry.grid(row=1, column=1)
    appPathEntry.bind("<Button-1>", clickSelectApp)

    compileAppButton = customtkinter.CTkButton(kernelPannel, text=" Compile app  ", command=clickCompileApp)
    compileAppButton.grid(row=1, column=2, padx=5)

    compileAppShow = customtkinter.CTkLabel(kernelPannel, text=" IDLE")
    compileAppShow.grid(row=1, column=3)
    widgets["compileAppShow"] = compileAppShow

    kernelNameLabel = customtkinter.CTkLabel(kernelPannel, text=" Kernel name:")
    kernelNameLabel.grid(row=2, column=0)

    tempOptions = ["Not selected yet"]
    # kernelNameMenu = tkinter.OptionMenu(kernelPannel, kernelOptions, *tempOptions)
    kernelNameMenu = customtkinter.CTkOptionMenu(kernelPannel, variable=kernelOptions, values=tempOptions)
    kernelOptions.trace("w", clickKernelMenu)
    widgets["kernelNameMenu"] = kernelNameMenu
    widgets["kernelPannel"] = kernelPannel
    kernelNameMenu.grid(row=2, column=1)

    generateDFGButton = customtkinter.CTkButton(kernelPannel, text="Generate DFG", command=clickShowDFG)
    generateDFGButton.grid(row=2, column=2, padx=5)

    generateDFGShow = customtkinter.CTkLabel(kernelPannel, text=" IDLE")
    generateDFGShow.grid(row=2, column=3, sticky="ew")
    widgets["generateDFGShow"] = generateDFGShow

    dfgPannel = customtkinter.CTkFrame(kernelPannel)
    dfgPannel.grid(row=3, column=0, rowspan=11, columnspan=2, padx=(0,5), pady=(5,0), sticky="nsew")
    dfgPannelLabel = customtkinter.CTkLabel(dfgPannel, text='Data-Flow Graph ',
                                             font=customtkinter.CTkFont(size=FRAME_LABEL_FONT_SIZE,
                                                                        weight="bold"))
    dfgPannelLabel.pack(anchor="w", padx=(5, 0))
    dfgLabel = customtkinter.CTkLabel(dfgPannel, text="")
    widgets["dfgLabel"] = dfgLabel
    dfgLabel.pack()

    recMIILabel = customtkinter.CTkLabel(kernelPannel, text=" RecMII: ")
    recMIILabel.grid(row=3, column=2, sticky="nsew")
    recMIIEntry = customtkinter.CTkEntry(kernelPannel, justify=tkinter.CENTER)
    widgets["recMIIEntry"] = recMIIEntry
    recMIIEntry.insert(0, "0")
    recMIIEntry.grid(row=3, column=3)
    resMIILabel = customtkinter.CTkLabel(kernelPannel, text=" ResMII: ")
    resMIILabel.grid(row=4, column=2, sticky="nsew")
    resMIIEntry = customtkinter.CTkEntry(kernelPannel, justify=tkinter.CENTER)
    widgets["resMIIEntry"] = resMIIEntry
    resMIIEntry.insert(0, "0")
    resMIIEntry.grid(row=4, column=3)

    mappingAlgoPannel = customtkinter.CTkFrame(kernelPannel)
    mappingAlgoPannel.grid(row=5, column=2, rowspan=3, columnspan=2, pady=(5,10), sticky="nsew")
    for row in range(2):
        mappingAlgoPannel.grid_rowconfigure(row, weight=1)
    mappingAlgoPannel.grid_columnconfigure(0, weight=1)
    mappingAlgoPannel.grid_columnconfigure(1, weight=1)
    # mappingOptionLabel = customtkinter.CTkLabel(mappingAlgoPannel, text="Mapping algo:")
    mappingOptionLabel = customtkinter.CTkLabel(mappingAlgoPannel, text='Mapping Algorithm',
                                            font=customtkinter.CTkFont(size=FRAME_LABEL_FONT_SIZE,
                                                                       weight="bold"))
    mappingOptionLabel.grid(row=0, column=0, columnspan=2)
    heuristicRadioButton = customtkinter.CTkRadioButton(mappingAlgoPannel, text="Heuristic", variable=mappingAlgoCheckVar, value=0)
    widgets["heuristicRadioButton"] = heuristicRadioButton
    heuristicRadioButton.grid(row=1, column=0, pady=(0, 5), sticky="nsew")
    exhaustiveRadioButton = customtkinter.CTkRadioButton(mappingAlgoPannel, text="Exhaustive", variable=mappingAlgoCheckVar, value=1)
    widgets["exhaustiveRadioButton"] = exhaustiveRadioButton
    exhaustiveRadioButton.grid(row=1, column=1, pady=(0, 5), sticky="nsew")

    tarCgraIdLabel = customtkinter.CTkLabel(kernelPannel, text=" Target CGRA id: ")
    tarCgraIdLabel.grid(row=8, column=2)

    targetCgraIdOptions = ["0", "1", "2", "3"]
    targetCgraIdVariable = tkinter.StringVar(kernelPannel)
    targetCgraIdVariable.set(targetCgraIdOptions[0])
    targetCgraIdOptionMenu = customtkinter.CTkOptionMenu(kernelPannel, variable=targetCgraIdVariable,
                                                     values=targetCgraIdOptions)
    targetCgraIdOptionMenu.grid(row=8, column=3)

    mapDFGButton = customtkinter.CTkButton(kernelPannel, text="Map DFG", command=clickMapDFG,)
    mapDFGButton.grid(row=9, column=2, columnspan=2, sticky="new")
    terminateMapButton = customtkinter.CTkButton(kernelPannel, text="Terminate", command=clickTerminateMapping)
    terminateMapButton.grid(row=10, column=2, columnspan=2, sticky="new")

    mapSecLabel = customtkinter.CTkLabel(kernelPannel, text="Time (s): ")
    mapSecLabel.grid(row=11, column=2)
    mapTimeEntry = customtkinter.CTkEntry(kernelPannel, justify=tkinter.CENTER)
    widgets["mapTimeEntry"] = mapTimeEntry
    mapTimeEntry.insert(0, "0")
    mapTimeEntry.grid(row=11, column=3)
    mapIILabel = customtkinter.CTkLabel(kernelPannel, text=" Map II: ")
    mapIILabel.grid(row=12, column=2)
    mapIIEntry = customtkinter.CTkEntry(kernelPannel, justify=tkinter.CENTER)
    widgets["mapIIEntry"] = mapIIEntry
    mapIIEntry.insert(0, "0")
    mapIIEntry.grid(row=12, column=3)

    speedupLabel = customtkinter.CTkLabel(kernelPannel, text="Speedup: ")
    speedupLabel.grid(row=13, column=2)
    CreateToolTip(speedupLabel,
                  text="The speedup is the improvement of\nthe execution cycles with respect to\na single-issue in-order CPU.")
    mapSpeedupEntry = customtkinter.CTkEntry(kernelPannel, justify=tkinter.CENTER)
    widgets["mapSpeedupEntry"] = mapSpeedupEntry
    mapSpeedupEntry.insert(0, "0")
    mapSpeedupEntry.grid(row=13, column=3)

    return kernelPannel

# Performs a perodical checks on whether the UI components are drawn into the screen or not.
def check_ui_ready(
    master: customtkinter.CTk,
    multiCgraPanel: customtkinter.CTkFrame,
    multiCgraConfigPanel: customtkinter.CTkFrame,
    kernel_panel: customtkinter.CTkFrame,
    mapping_panel: customtkinter.CTkFrame,
    cgra_panel: customtkinter.CTkFrame,
    param_panel: customtkinter.CTkFrame,
    data_panel: customtkinter.CTkFrame,
    layout_panel: customtkinter.CTkFrame,
    window: customtkinter.CTkToplevel,
):
    panels = [
        multiCgraPanel,
        multiCgraConfigPanel,
        kernel_panel,
        mapping_panel,
        cgra_panel,
        param_panel,
        data_panel,
        layout_panel,
    ]

    if all(panel.winfo_ismapped() for panel in panels):
        master.after(100, window.destroy)
    else:
        master.after(200, lambda: check_ui_ready(master, *panels, window))

# Display all the UI components by calling grid() and start a periodical checks on when they are ready.
def show_all_ui(master: customtkinter.CTk, window: customtkinter.CTkToplevel):
    multiCgraConfigPanel = create_multi_cgra_config_panel(master)
    kernelPannel = create_kernel_pannel(master)
    mappingPannel = create_mapping_pannel(master)
    cgraPannel = create_cgra_pannel(master, selectedCgraParam.rows, selectedCgraParam.columns)
    multiCgraPanel = create_multi_cgra_panel(master, multiCgraParam.rows, multiCgraParam.cols)
    paramPannel = create_param_pannel(master)
    dataPannel = create_test_pannel(master)
    layoutPannel = create_layout_pannel(master)
    multiCgraPanel.grid(row=0, column=0, padx=(0, 5), sticky="nsew")
    multiCgraConfigPanel.grid(row=0, column=1, sticky="nsew")
    kernelPannel.grid(row=1, column=0, padx=(0, 5), pady=(5, 0), sticky="nsew")
    mappingPannel.grid(row=1, column=1, rowspan=1, columnspan=3, padx=(0, 5), pady=(5, 0), sticky="nsew")
    #paramPannel.grid(row=0, column=4, columnspan=2, sticky="nsew")
    dataPannel.grid(row=1, column=4, pady=(5,0), sticky="nsew")
    layoutPannel.grid(row=1, column=5, padx=(5,0), pady=(5,0), sticky="nsew")
    # Once kernel is drawn stop the check loop after 100ms.
    if (kernelPannel.winfo_ismapped()):
        master.after(100, window.destroy())
    # Keeps checking if UI components are drawn in every 2 seconds.
    else:
        master.after(2000, lambda: check_ui_ready(master, multiCgraPanel, multiCgraConfigPanel, kernelPannel, mappingPannel, cgraPannel, paramPannel, dataPannel, layoutPannel, window))


# paramPadPosX = GRID_WIDTH + MEM_WIDTH + LINK_LENGTH + INTERVAL * 3
# paramPadWidth = 270
# scriptPadPosX = paramPadPosX + paramPadWidth + INTERVAL
# scriptPadWidth = 300
# layoutPadPosX = scriptPadPosX + scriptPadWidth + INTERVAL
# layoutPadWidth = 300
# layoutPadHeight = GRID_HEIGHT
TILE_HEIGHT = 70
TILE_WIDTH = 70
LINK_LENGTH = 40
GRID_WIDTH = (TILE_WIDTH + LINK_LENGTH) * COLS - LINK_LENGTH
GRID_HEIGHT = (TILE_HEIGHT + LINK_LENGTH) * ROWS - LINK_LENGTH

# Sets size first to avoid window keep resizing during loading.
w, h = master.winfo_screenwidth(), master.winfo_screenheight()
master.geometry("%dx%d" % (w-10, h-70))
master.geometry("+%d+%d" % (0, 0))

main_frame = customtkinter.CTkFrame(master)

overlay = customtkinter.CTkToplevel(master)
overlay.geometry("%dx%d" % (w-10, h-70))
overlay.transient(master)
overlay.grab_set()

loading_label = customtkinter.CTkLabel(overlay, text="Loading...", font=("Arial", 24, "bold"))
loading_label.place(relx=0.5, rely=0.4, anchor="center")

progress = customtkinter.CTkProgressBar(overlay)
progress.place(relx=0.5, rely=0.5, anchor="center")
progress.start()

# Adds other UI components in a separate thread.
threading.Thread(target=show_all_ui(master, overlay), daemon=True).start()

# # kernel
# create_kernel_pannel(master)
# # mapping
# create_mapping_pannel(master)
# # multi cgra
# create_multi_cgra_panel(master, CGRA_ROWS, CGRA_COLS)
# # multi cgra config
# create_multi_cgra_config_panel(master)
# # cgra
# create_cgra_pannel(master, ROWS, COLS)
# # configuration
# create_param_pannel(master)
# # verification
# create_test_pannel(master)
# # layout
# create_layout_pannel(master)
# The width and height of the entire window
default_width = 1650
default_height = 1000
window_size(master, default_width, default_height)
# master.grid_rowconfigure(0, weight=1)
master.grid_rowconfigure(1, weight=2)
master.grid_columnconfigure(0, weight=5)
master.grid_columnconfigure(1, weight=1)
master.grid_columnconfigure(2, weight=5)
master.grid_columnconfigure(3, weight=1)
master.grid_columnconfigure(4, weight=1)
master.grid_columnconfigure(5, weight=1)
# print(master.winfo_width())
# print(master.winfo_height())
# w, h = master.winfo_screenwidth(), master.winfo_screenheight()
master.geometry("%dx%d" % (w-10, h-70))
master.geometry("+%d+%d" % (0, 0))
master.mainloop()
