from tkinter import *

class Cell:
    FILLED_COLOR_BG = "green"
    DONE_COLOR_BG = "blue"
    EMPTY_COLOR_BG = "white"
    FILLED_COLOR_BORDER = "green"
    DONE_COLOR_BORDER = "blue"
    EMPTY_COLOR_BORDER = "black"

    def __init__(self, master, x, y, size):
        """ Constructor of the object called by Cell(...) """
        self.master = master
        self.abs = x
        self.ord = y
        self.size= size
        self.fill= False
        self.done = False

    def _switch(self):
        """ Switch if the cell is filled or not. """
        if self.done:
            self.done = False
        else:
            self.fill = not self.fill


    def draw(self):
        """ order to the cell to draw its representation on the canvas """
        if self.master != None :
            fill = Cell.FILLED_COLOR_BG
            outline = Cell.FILLED_COLOR_BORDER

            if not self.fill and not self.done:
                fill = Cell.EMPTY_COLOR_BG
                outline = Cell.EMPTY_COLOR_BORDER

            if self.done:
                fill = Cell.DONE_COLOR_BG
                outline = Cell.DONE_COLOR_BORDER

            xmin = self.abs * self.size
            xmax = xmin + self.size
            ymin = self.ord * self.size
            ymax = ymin + self.size

            self.master.create_rectangle(xmin, ymin, xmax, ymax, fill = fill, outline = outline)

class CellGrid(Canvas):

    def __init__(self,master, rowNumber, columnNumber, cellSize, *args, **kwargs):
        Canvas.__init__(self, master, width = cellSize * columnNumber , height = cellSize * rowNumber, *args, **kwargs)

        self.cellSize = cellSize
        self.current = None

        self.grid = []
        for row in range(rowNumber):

            line = []
            for column in range(columnNumber):
                line.append(Cell(self, column, row, cellSize))

            self.grid.append(line)

        #memorize the cells that have been modified to avoid many switching of state during mouse motion.
        self.done = []

        #bind click action
        self.bind("<Button-1>", self.handleMouseClick)
        #bind moving while clicking
        # self.bind("<B1-Motion>", self.handleMouseMotion)
        #bind release button action - clear the memory of midified cells.
        # self.bind("<ButtonRelease-1>", lambda event: self.switched.clear())

        self.draw()



    def draw(self):
        for row in self.grid:
            for cell in row:
                cell.draw()

    def _eventCoords(self, event):
        row = int(event.y / self.cellSize)
        column = int(event.x / self.cellSize)
        return row, column

    def handleMouseClick(self, event):
        row, column = self._eventCoords(event)
        cell = self.grid[row][column]
        # if self.current != None and self.current.fill and not self.current.done and cell.done == False:
        #     self.current.done = True
        #     self.current.draw()
        #     print("here")
        if self.current != cell and cell.done == False:
            print("(" + str(row) + ", " + str(column) + ")")
            if self.current != None:
                self.current.fill = False
                self.current.draw()
            self.current = cell

        cell._switch()
        cell.draw()
        #add the cell to the list of cell switched during the click

    def setDone(self):
        if self.current != None:
            self.current.done = True
            self.current.draw()
            print("here")



    # def handleMouseMotion(self, event):
    #     row, column = self._eventCoords(event)
    #     cell = self.grid[row][column]
    #
    #     if cell not in self.done:
    #         cell._switch()
    #         cell.draw()
    #         self.done.append(cell)


if __name__ == "__main__" :
    app = Tk()

    grid = CellGrid(app, 10, 10, 50)
    grid.pack(side=TOP, fill=BOTH, expand=True)
    buttomFrame = Frame(app)
    buttomFrame.pack(side=BOTTOM, fill=X)
    doneButton = Button(buttomFrame, text="Done", command=grid.setDone, width=20)
    doneButton.pack(side=LEFT, padx=5, pady=5)

    app.mainloop()