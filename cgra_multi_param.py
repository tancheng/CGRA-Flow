from cgra_param import CGRAParam 
from constants import *

class MultiCGRAParam:
    def __init__(self, rows, cols, golbalWidgets):
        self.rows = rows
        self.cols = cols
        self.cgras = [[CGRAParam(ROWS, COLS, CONFIG_MEM_SIZE, DATA_MEM_SIZE, golbalWidgets) for c in range(cols)] for r in range(rows)]
        self.selectedCgraParam = None
        self.selected_row = 0
        self.selected_col = 0

    def setSelectedCgra(self, row, col):
        if 0 <= row < self.rows and 0 <= col < self.cols:
            self.selectedCgraParam = self.cgras[row][col]
            self.selected_row = row
            self.selected_col = col
        else:
            raise IndexError(f"Invalid CGRA coordinates: ({row}, {col})")

    def getSelectedCgra(self):
        return self.selectedCgraParam
    
    def getSelectedCgraId(self):
        return self.selected_row * self.rows + self.selected_col

    def getCgraParam(self, row, col):
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.cgras[row][col]
        else:
            raise IndexError(f"Invalid CGRA coordinates: ({row}, {col})")