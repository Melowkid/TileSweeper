import math
import exceptions
import Tkinter
import random
import time
import copy

class Score:
    points = 0
    scoreMap = {}
    def __init__(self,number,scoreRange):  #Score range is number of different tiles, bombmin, bombmax, tileaverage, tilerange
        #Create score map model
        self.scoreMap[0] = 0
        self.scoreMap[1] = -1*random.randint(scoreRange[0],scoreRange[1])
        for x in range(2,number+1):
            self.scoreMap[x] = random.randint(0,scoreRange[2])-scoreRange[3]
    def update(self,index):
        if index == None: return
        self.points += self.scoreMap[index]
    def get(self):
        return self.points      

class RuleGenerator:
    #These are the basic possible rules that the tiles can be distributed with
    #If the random rule is chosen, the tile is distributed randomly
    #If the relation rule is chosen, the tile is distributed as a relation to a previous tile
    #If the within rule is chosen, the tile is distributed to every place that has exactly one
    #neighbor of the appropreate kind
    #If the and rule is chosen, the tile is distributed according to either:
    #       WITHIN and WITHIN
    #       RELATION and WITHIN
    #       RELATION and RELATION
    possibleRules = ["RANDOM","RELATION","WITHIN","AND"]            #Three possible types of rules
    orientationList = ["Upper Left","Left","Lower Left","Upper Middle","Lower Middle","Upper Right","Right","Lower Right"]     #Eight possible relational locations
    ruleTypeWeights = [5,45,35,15]
    relationWeights = [30,40,20,5,3,2]
    withinWeights = [30,40,20,5,3,2]
    andWeights = [30,40,20,5,3,2]
    def __init__(self,ruleTypeWeights = None,relationWeights = None,withinWeights = None):
        if ruleTypeWeights != None:
            self.ruleTypeWeights = ruleTypeWeights
        if relationWeights != None:
            self.relationWeights = relationWeights
        if withinWeights != None:
            self.withinWeights = withinWeights
    def randomRule(self):
        place = random.randint(0,sum(self.ruleTypeWeights))
        index = 0
        for x in range(len(self.ruleTypeWeights)):
            if sum(self.ruleTypeWeights[:x+1]) > place:
                index = x
                break
        return self.possibleRules[index]
    def expandRandom(self,grid):
        return ["RANDOM"]
    def expandRelation(self,grid):
        #A map of the sizes of the possible within rules
        sizeMap = {}
        #Store the possible rules and thier sizes
        for x in range(grid.size[0]):
            for y in range(grid.size[1]):
                if grid.remainingMap[(x,y)]:
                    neighbors = grid.findNeighbors((x,y))
                    for z in range(len(neighbors)):
                        if neighbors[z] < 1: continue
                        placeIndex = z
                        placeName = self.orientationList[placeIndex]
                        try:
                            sizeMap[(neighbors[z],placeName,placeIndex)] += 1
                        except:
                            sizeMap[(neighbors[z],placeName,placeIndex)] = 1
        #Order the possible rules by the amount of tiles they cover
        ruleList = sorted(sizeMap.keys(),key=lambda item: sizeMap[item])
        ruleList.reverse()
        #Select one at random with a weight term
        place = random.randint(0,sum(self.withinWeights[:len(ruleList)]))
        index = 0
        for x in range(len(self.withinWeights)):
            if sum(self.withinWeights[:x+1]) > place:
                index = x
                break
        return ["RELATION",ruleList[index]]
    def expandWithin(self,grid):
        #A map of the sizes of the possible within rules
        sizeMap = {}
        #Store the possible rules and thier sizes
        for x in range(grid.size[0]):
            for y in range(grid.size[1]):
                if grid.remainingMap[(x,y)]:
                    neighbors = grid.findNeighbors((x,y))
                    potential = [z for z in neighbors if z > 0]
                    for z in set(potential):
                        size = neighbors.count(z)
                        try:
                            sizeMap[(z,size)] += 1
                        except:
                            sizeMap[(z,size)] = 1
        #Order the possible rules by the amount of tiles they cover
        ruleList = sorted(sizeMap.keys(),key=lambda item: sizeMap[item])
        ruleList.reverse()
        #Select one at random with a weight term
        place = random.randint(0,sum(self.withinWeights[:len(ruleList)]))
        index = 0
        for x in range(len(self.withinWeights)):
            if sum(self.withinWeights[:x+1]) > place:
                index = x
                break
        return ["WITHIN",ruleList[index]]
    def expandAnd(self,grid):
        #Decide whether to do within or relation
        first = random.choice(["WITHIN","RELATION"])
        second = random.choice(["WITHIN","RELATION"])
        #Create maps for the first and second choice
        firstMap = {}
        secondMap = {}
        for x in range(grid.size[0]):
            for y in range(grid.size[1]):
                if grid.remainingMap[(x,y)]:
                    neighbors = grid.findNeighbors((x,y))
                    potential = [z for z in neighbors if z > 0]
                    if first == "RELATION":
                        for z in range(len(neighbors)):
                            if neighbors[z] < 1: continue
                            placeIndex = z
                            placeName = self.orientationList[placeIndex]
                            try:
                                firstMap[("RELATION",neighbors[z],placeName,placeIndex)] += 1
                            except:
                                firstMap[("RELATION",neighbors[z],placeName,placeIndex)] = 1
                    else:
                        for z in set(potential):
                            size = neighbors.count(z)
                            try:
                                firstMap[("WITHIN",z,size)] += 1
                            except:
                                firstMap[("WITHIN",z,size)] = 1
                    if second == "RELATION":
                        for z in range(len(neighbors)):
                            if neighbors[z] < 1: continue
                            placeIndex = z
                            placeName = self.orientationList[placeIndex]
                            try:
                                secondMap[("RELATION",neighbors[z],placeName,placeIndex)] += 1
                            except:
                                secondMap[("RELATION",neighbors[z],placeName,placeIndex)] = 1
                    else:
                        for z in set(potential):
                            size = neighbors.count(z)
                            try:
                                secondMap[("WITHIN",z,size)] += 1
                            except:
                                secondMap[("WITHIN",z,size)] = 1
        #Final size map for the combinations
        sizeMap = {}
        #Create all combinations of first and second
        for first in range(len(firstMap.keys())):
            for next in range(first+1,len(secondMap.keys())):
                firstRule = firstMap.keys()[first]
                secondRule = secondMap.keys()[next]
                #Test this combination, add it to the size map
                thisRule = (firstRule,secondRule)
                for x in range(grid.size[0]):
                    for y in range(grid.size[1]):
                        if grid.remainingMap[(x,y)]:
                            neighbors = grid.findNeighbors((x,y))
                            firstSuccess = False
                            secondSuccess = False
                            if firstRule[0] == "WITHIN":
                                firstSuccess = neighbors.count(firstRule[1]) == firstRule[2]
                            if firstRule[0] == "RELATION":
                                fristSuccess = neighbors[firstRule[3]] == firstRule[1]
                            if secondRule[0] == "WITHIN":
                                secondSuccess = neighbors.count(secondRule[1]) == secondRule[2]
                            if secondRule[0] == "RELATION":
                                secondSuccess = neighbors[secondRule[3]] == secondRule[1]
                            if firstSuccess and secondSuccess:
                                try:
                                    sizeMap[thisRule] += 1
                                except:
                                    sizeMap[thisRule] = 1
        #Order the possible rules by the amount of tiles they cover
        ruleList = sorted(sizeMap.keys(),key=lambda item: sizeMap[item])
        ruleList.reverse()
        if len(ruleList) == 0: return None
        #Select one at random with a weight term
        place = random.randint(0,sum(self.withinWeights[:len(ruleList)]))
        index = 0
        for x in range(len(self.andWeights)):
            if sum(self.andWeights[:x+1]) > place:
                index = x
                break
        return ["AND",ruleList[index]]
    def createRandomRule(self,grid):
        #Get a random rule type
        ruleType = self.randomRule()
        #Expand a rule of that type with metadata about relations in the grid
        if ruleType == "RANDOM": return self.expandRandom(grid)
        elif ruleType == "RELATION": return self.expandRelation(grid)
        elif ruleType == "WITHIN": return self.expandWithin(grid)
        elif ruleType == "AND": return self.expandAnd(grid)
    def updateGrid(self,grid,rule,value):
        #Randomly place the tiles in remaining places in the grid
        if rule[0] == "RANDOM":
            for x in range(grid.size[0]):
                for y in range(grid.size[1]):
                    if((random.random() < 1.0/grid.number) and grid.remainingMap[(x,y)]):
                        grid.gridMap[(x,y)] = value
                        grid.remainingMap[(x,y)] = False
        if rule[0] == "WITHIN":
            for x in range(grid.size[0]):
                for y in range(grid.size[1]):
                    neighbors = grid.findNeighbors((x,y))
                    count = neighbors.count(rule[1][0])
                    if(count == rule[1][1] and grid.remainingMap[(x,y)]):
                        grid.gridMap[(x,y)] = value
                        grid.remainingMap[(x,y)] = False
        if rule[0] == "RELATION":
            for x in range(grid.size[0]):
                for y in range(grid.size[1]):
                    neighbors = grid.findNeighbors((x,y))
                    if(neighbors[rule[1][2]] == rule[1][0] and grid.remainingMap[(x,y)]):
                        grid.gridMap[(x,y)] = value
                        grid.remainingMap[(x,y)] = False
        if rule[0] == "AND":
            for x in range(grid.size[0]):
                for y in range(grid.size[1]):
                    if(grid.remainingMap[(x,y)]):
                        neighbors = grid.findNeighbors((x,y))
                        firstRule = rule[1][0]
                        secondRule = rule[1][1]
                        firstSuccess = False
                        secondSuccess = False
                        if firstRule[0] == "WITHIN":
                            firstSuccess = neighbors.count(firstRule[1]) == firstRule[2]
                        if firstRule[0] == "RELATION":
                            fristSuccess = neighbors[firstRule[3]] == firstRule[1]
                        if secondRule[0] == "WITHIN":
                            secondSuccess = neighbors.count(secondRule[1]) == secondRule[2]
                        if secondRule[0] == "RELATION":
                            secondSuccess = neighbors[secondRule[3]] == secondRule[1]
                        if firstSuccess and secondSuccess:
                            grid.gridMap[(x,y)] = value
                            grid.remainingMap[(x,y)] = False
                    
        
class Grid:
    stringRepresentation = "Get the highest score possible!\n"
    display = False
    number = 0
    size = (0,0)
    gridMap = {}
    remainingMap = {}
    ruleMap = {}
    def __init__(self,number,size,condition = "WITH_RULES"): 
        #Create the state of the rule generator
        self.size = size
        self.number = number
        self.condition = condition
        generator = RuleGenerator([10,30,30,30])
        #Initialize the grid and the remaining map
        for x in range(self.size[0]):
            for y in range(self.size[1]):
                self.gridMap[(x,y)] = 0
                self.remainingMap[(x,y)] = True
        #Place the bombs
        generator.updateGrid(self,["RANDOM"],1)
        self.ruleMap[1] = ["RANDOM"]
        #Place the next tile numbers
        for x in range(2,self.number):
            rule = generator.createRandomRule(self)
            if rule == None: continue
            generator.updateGrid(self,rule,x)
            self.ruleMap[x] = rule
    def findNeighbors(self,index):
        neighborList = []
        for x in range(-1,2):
            for y in range(-1,2):
                if x == 0 and y == 0: continue
                try:
                    neighborList.append(self.gridMap[(index[0]+x,index[1]+y)])
                except:
                    neighborList.append(-1)
        return neighborList
    def __getitem__(self,index):
        return self.gridMap[index]
    def getText(self,tileModel,scoreModel):
        self.stringRepresentation = "Get the highest score possible!\n"
        if not self.condition == "WITH_RULES": return self.stringRepresentation
        else:
            for x in self.ruleMap.keys():
                rule = self.ruleMap[x]
                color = tileModel.gridColorMap[x].upper()
                addString = ""
                if rule[0] == "RANDOM":
                    addString = " are randomly placed."
                if rule[0] == "RELATION":
                    addString = " have a "+tileModel.gridColorMap[rule[1][0]].upper()+" tile to the "+rule[1][1]+"."
                if rule[0] == "WITHIN":
                    addString = " have "+str(rule[1][1])+" adjacent "+tileModel.gridColorMap[rule[1][0]].upper()+" tile(s)."
                if rule[0] == "AND":
                    fristString = ""
                    if rule[1][0][0] == "WITHIN":
                        firstString = " "+str(rule[1][0][2])+" adjacent "+tileModel.gridColorMap[rule[1][0][1]].upper()+" tile(s) and"
                    if rule[1][0][0] == "RELATION":
                        firstString = " a "+tileModel.gridColorMap[rule[1][0][1]].upper()+" tile to the "+rule[1][0][2]+"."
                    if rule[1][1][0] == "WITHIN":
                        secondString = " "+str(rule[1][1][2])+" adjacent "+tileModel.gridColorMap[rule[1][1][1]].upper()+" tile(s)."
                    if rule[1][1][0] == "RELATION":
                        secondString = " a "+tileModel.gridColorMap[rule[1][1][1]].upper()+" tile to the "+rule[1][1][2]+"."
                    addString = "have"+firstString+secondString
                self.stringRepresentation += "\n\n"+color+" tiles are worth "+str(scoreModel.scoreMap[x])+" points and "+addString
        return self.stringRepresentation

class Tile:
    covered = True
    def __init__(self):
        self.covered = True
    def uncover(self):
        if self.covered: returner = True
        else: returner = False
        self.covered = False
        return returner
        
class TileGrid:
    coverColor = ""
    pallete = ()
    number = 0
    grid = {}
    tileGrid = {}
    gridColorMap = {}
    def __init__(self,grid,cover,pallete):
        #Store stuff locally for ease of use
        self.grid = grid
        self.coverColor = cover
        #Map between the colors given and the rule numbers
        for x in range(grid.number):
            self.gridColorMap[x] = pallete[x]
        #Make a tilegrid from the color grid
        for x in range(grid.size[0]):
            for y in range(grid.size[1]):
                self.tileGrid[(x,y)] = Tile()
    def size(self):
        return self.grid.size
    def __getitem__(self,index):
        if index[0] > self.size()[0] or index[0] < 0: raise IndexError()
        if index[1] > self.size()[1] or index[1] < 0: raise IndexError()
        if self.tileGrid[index].covered:
            return self.coverColor
        else:
            return self.gridColorMap[self.grid[index]]
    def uncover(self,index):
        if(self.tileGrid[index].uncover()): return self.grid[index]
        return None
        
class Timer:
    def __init__(self,remaining):
        self.length = remaining
    def start(self):
        self.startTime = time.clock()
    def get(self):
        return self.startTime+self.length - time.clock()

class RulesView(Tkinter.Button):
    window = None
    def __init__(self,parent,ruleModel,tileModel,scoreModel,font = None,**kwargs):
        #Extend the button class
        Tkinter.Button.__init__(self,parent,**kwargs)
        #Store the rule, tile, and score model pointers
        self.ruleModel = ruleModel
        self.tileModel = tileModel
        self.scoreModel = scoreModel
        self.font = font
        #Configure the button
        self.configure(font = self.font)
    def bind(self):
        self.configure(text = "Rules",command = self.open)
    def open(self):
        if self.window == None:
            pass
        else:
            self.window.geometry("700x700+50+100")
            self.window.focus_force()
            return
        #Make the window
        self.window = Tkinter.Toplevel(self)
        self.window.wm_title("Rule Display")
        self.window.resizable(0,0)
        self.window.wm_attributes("-topmost",1)     #Windows only
        self.window.wm_attributes("-toolwindow",1)  #Windows only
        self.window.geometry("700x700+50+100")
        #Display the rules
        ruleLabel = Tkinter.Label(self.window)
        ruleLabel.configure(wraplength = 500,text = self.ruleModel.getText(self.tileModel,self.scoreModel),font = self.font)
        ruleLabel.pack(fill = Tkinter.BOTH,expand = True)
        #Bind exit to close function
        self.window.focus_force()   #Make sure that the rule window has focus so that escape doesn't kill everything
        self.window.protocol("WM_DELETE_WINDOW",self.close)
        self.window.bind("<Escape>",self.close)
    def minimize(self,event = None):
        print "this"
        pass
    def close(self,event = None):
        self.window.destroy()
        self.window = None
        
class ScoreView(Tkinter.Label):
    def __init__(self,parent,score,**kwargs):
        #Extend the label class
        Tkinter.Label.__init__(self,parent,**kwargs)
        #Initialize the score model
        self.score = score
        #Paint the initial model
        self.configure(width = 13)
        self.paint()
    def paint(self):
        displayText = "Score:"+'{:>7}'.format(str(self.score.get()))
        self.configure(text = displayText)
        
class TimerView(Tkinter.Label):
    def __init__(self,parent,timer,**kwargs):
        #Extend the label class
        Tkinter.Label.__init__(self,parent,**kwargs)
        #Initialize the time model
        self.timer = timer
    def paint(self):
        timePoint = self.timer.get()
        if timePoint < 0: timePoint = 0
        seconds = int(time.strftime("%S",time.gmtime(timePoint)))
        minuets = int(time.strftime("%M",time.gmtime(timePoint)))
        displayText = "Time Left -- "+time.strftime("%M:%S",time.gmtime(timePoint))
        if(minuets == 0 and seconds <= 5):
            self.configure(fg = "red")
        self.configure(text = displayText)

class InfoView(Tkinter.Frame):
    def __init__(self,parent,rules,tiles,score,timer,font = None,**kwargs):
        #Extend the frame class
        Tkinter.Frame.__init__(self,parent,**kwargs)
        #Make a score in upper left and a timer in the middle
        self.rules = rules
        self.tiles = tiles
        self.score = score
        self.timer = timer
        #Make the views for them
        self.rulesView = RulesView(self,self.rules,self.tiles,self.score,font = font)
        self.scoreView = ScoreView(self,self.score,font = font)
        self.timerView = TimerView(self,self.timer,font = font)
        #Pack the views, arranging them correctly
        self.rulesView.pack(fill = Tkinter.X,side = Tkinter.LEFT,padx = 50,anchor = Tkinter.W)
        self.timerView.pack(fill = Tkinter.X,side = Tkinter.RIGHT,padx = 50)
        self.scoreView.pack(fill = Tkinter.X,side = Tkinter.RIGHT)
        #Bind the button
        self.rulesView.bind()
    def paint(self,event = None):
        self.scoreView.paint()
        self.timerView.paint()
        
class TileGridView(Tkinter.Canvas):
    initialized = False
    objects = {}
    ids = {}
    outPad = 50 #The padding between grid and edge of window
    inPad = 3   #The padding between boxes
    def __init__(self,parent,tileGrid,**kwargs):
        #Expand the canvas class
        Tkinter.Canvas.__init__(self,parent,**kwargs)
        self.configure(background = "#777777")
        #Dynamically resize it to fit the window
        self.bind("<Configure>", self.resize)
        self.width = self.winfo_reqwidth()
        self.height = self.winfo_reqheight()
        #Initialize the grid model reference
        self.tileGrid = tileGrid
        #Draw each cell of the grid
        self.paint()
    def repaint(self,index):
        self.itemconfig(self.objects[index],fill = self.tileGrid[index])
    def paint(self,event = None):
        #Calculate the locations and sizes of the boxes
        xSize = ((self.width-2*self.outPad)/self.tileGrid.size()[0])
        ySize = ((self.height-2*self.outPad)/self.tileGrid.size()[1])
        #Make the boxes square
        boxSize = min(xSize,ySize) - self.inPad
        #Place the boxes on the canvas
        if not self.initialized: #If the grid is not initialized, initialize it
            for x in range(self.tileGrid.size()[0]):
                for y in range(self.tileGrid.size()[1]):
                    self.objects[(x,y)] = self.create_rectangle(self.outPad+xSize*x,self.outPad+ySize*y,self.outPad+xSize*x+boxSize,self.outPad+ySize*y+boxSize,fill = self.tileGrid[(x,y)])
                    self.ids[self.objects[(x,y)]] = (x,y)
            self.initialized = True
        else:
            for x in range(self.tileGrid.size()[0]):
                for y in range(self.tileGrid.size()[1]):
                    self.coords(self.objects[(x,y)],self.outPad+xSize*x,self.outPad+ySize*y,self.outPad+xSize*x+boxSize,self.outPad+ySize*y+boxSize)  
    def resize(self,event = None):
        #If there is an event, update the state
        if not event == None:
            self.width = event.width
            self.height = event.height
        #Repaint the things
        self.paint()

class ScoreController:
    def __init__(self,score,scoreView):
        #Set pointers for ease of use
        self.score = score
        self.scoreView = scoreView
    def update(self,index):
        self.score.update(index)
        self.scoreView.paint()

class TimerController:
    def __init__(self,timer,timerView):
        #Set pointers for ease of use
        self.timer = timer
        self.timerView = timerView
        #Bindings to call at different times
        self.bindings = {}
    def start(self):
        self.timer.start()
    def run(self,root):
        self.timerView.paint()
        for x in self.bindings.keys():
            if self.timer.get() <= x:
                self.bindings[x]()
        root.after(1000, lambda: self.run(root))
    def bind(self,time,call):
        self.bindings[time] = call
        
        
class TileGridController:
    def __init__(self,tileGrid,tileGridView,pointCallback):
        #Sets whether the grid is active or not
        self.active = True
        #Set pointers for ease of use
        self.tileGrid = tileGrid
        self.gridView = tileGridView
        self.pointCallback = pointCallback
        #Bind callbacks
        for x in range(self.tileGrid.size()[0]):
            for y in range(self.tileGrid.size()[1]):
                index = (x,y)
                self.gridView.tag_bind(self.gridView.objects[index],"<Button-1>", self.tileBind)
    def tileBind(self,event):
        if not self.active: return
        id = self.gridView.find_closest(event.x, event.y)
        index = self.gridView.ids[id[0]]
        tileType = self.tileGrid.uncover(index)
        self.gridView.repaint(index)
        #Send the point indexes to the score model
        self.pointCallback(tileType)
    def reveal(self,event = None):
        #Reveal the whole tile grid
        for x in range(self.tileGrid.size()[0]):
            for y in range(self.tileGrid.size()[1]):
                index = (x,y)
                self.tileGrid.uncover(index)
                self.gridView.repaint(index)
    def deactivate(self):
        self.active = False
        
class QuitWindow:
    def __init__(self,parent):
        #Bind the parent
        self.parent = parent
        #Make the window
        self.window = Tkinter.Toplevel(parent)
        self.window.wm_title("Quit?")
        self.window.resizable(0,0)
        self.window.wm_attributes("-topmost",1)     #Windows only
        self.window.wm_attributes("-toolwindow",1)  #Windows only
        self.window.geometry("200x100+400+200")
        #Make the window contents
        dialog = Tkinter.Label(self.window,text = "Do you want to quit?")
        yes = Tkinter.Button(self.window,text = "yes",command = self.yes)
        no = Tkinter.Button(self.window,text = "no",command = self.no)
        #Pack the contents
        dialog.pack()
        yes.pack(side = Tkinter.LEFT,padx = 30)
        no.pack(side = Tkinter.RIGHT,padx = 30)
        #Grab focus
        self.window.focus_force()
        #Maintain focus
        self.window.bind("<FocusOut>",self.focus)
        self.window.bind("<Escape>",self.yes)
    def focus(self,event = None):
        self.window.focus_force()
    def yes(self,event = None):
        self.parent.destroy()
    def no(self,event = None):
        self.window.destroy()
        
class MainFrame(Tkinter.Frame):
    def __init__(self,parent,condition,**kwargs):
        #Expand the frame class
        Tkinter.Frame.__init__(self,parent,**kwargs)
        #Create a handle to the window that contains the main Tkinter frame
        self.master = parent
        self.condition = condition          #The experimental condition this subject is in
        #Make the window cover the screen
        w, h = self.master.winfo_screenwidth(), self.master.winfo_screenheight()
        self.master.overrideredirect(1)
        self.master.geometry("%dx%d+0+0" % (w, h))
        #Create the simple models needed
        self.font = "Helvetica 18 bold"     #The font of the information labels
        self.coverColor = "white"           #The tile covers are white
        self.pallete = [                    #The pallete for coloring tiles is 8 different colors
            "brown",
            "black",
            "red",
            "green",
            "blue",
            "cyan",
            "yellow",
            "magenta"
        ]
        self.gridSize = (30,15)             #Size of the grid
        self.ruleSize = 8                   #Use seven different rules
        self.scoreRange = (60,100,40,15)    #The range of tile point values to use: (bombmin,bombmax,tilemean,tilerange)
        self.timerLength = 1200               #The length of the countdown timer
        random.shuffle(self.pallete)        #Randomize the pallete
        #Create the complex models needed
        self.score = Score(self.ruleSize,self.scoreRange)
        self.timer = Timer(self.timerLength)
        self.grid = Grid(self.ruleSize,self.gridSize,self.condition)
        self.tileGrid = TileGrid(self.grid,self.coverColor,self.pallete)
        #Create the views needed
        self.infoView = InfoView(self,self.grid,self.tileGrid,self.score,self.timer,font = self.font)
        self.tileGridView = TileGridView(self,self.tileGrid)
        self.infoView.pack(fill = Tkinter.X,anchor = Tkinter.N)
        self.tileGridView.pack(fill = Tkinter.BOTH,expand = 1)
        #Create the controllers needed
        self.master.bind("<Escape>", self.quit)     #REMOVE FOR GAME
        self.master.bind("<Shift-R>", self.reveal)  #REMOVE FOR GAME
        self.scoreController = ScoreController(self.score,self.infoView.scoreView)
        self.timerController = TimerController(self.timer,self.infoView.timerView)
        self.gridController = TileGridController(self.tileGrid,self.tileGridView,self.scoreController.update)
        #Start the timer
        self.timerController.start()
        self.timerController.run(self.master)
        self.timerController.bind(0,self.gridController.deactivate) #Make the timer deactivate the grid at zero
        self.timerController.bind(-2,self.master.destroy)
        #Force the focus
        self.focus_force()
    def reveal(self,event = None):
        self.gridController.reveal()
    def quit(self,event = None):
        self.quitWindow = QuitWindow(self.master)
       
class DispatchFrame(Tkinter.Frame):
    def __init__(self,parent,**kwargs):
        #Expand the frame class
        Tkinter.Frame.__init__(self,parent,**kwargs)
        #Create a handle to the window that contains the main Tkinter frame
        self.master = parent
        self.counter = 1
        #Make the window cover the screen
        w, h = self.master.winfo_screenwidth(), self.master.winfo_screenheight()
        self.master.overrideredirect(1)
        self.master.geometry("%dx%d+0+0" % (w, h))
        #Assign an experimental condition
        self.condition = random.choice(["WITH_RULES","WITHOUT_RULES"])
        #Button dialog to start the game
        self.dialog = Tkinter.Label(self,text = "Press the button to start game 1 of 3",font = "Helvetica 18")
        self.start = Tkinter.Button(self,text = "start",command = self.start,font = "Helvetica 14 bold")
        self.dialog.place(relx=.5,rely=.5,anchor = Tkinter.CENTER)
        self.start.place(relx=.5,rely=.55,anchor = Tkinter.CENTER)
        self.master.bind("<Escape>",self.quit)
    def start(self):
        #Create a new window with the game on it
        random.seed(time.clock())
        self.window = Tkinter.Toplevel(self.master)
        instance = MainFrame(self.window,self.condition)
        instance.pack(fill = Tkinter.BOTH,expand = 1)
        self.wait_window(self.window)
        self.focus_force()
        #Update the dialog
        self.counter += 1
        self.dialog.configure(text = "Press the button to start game "+str(self.counter)+" of 3")
        if self.counter > 3:
            print "Thank you for playing!"
            self.quit()
    def quit(self,event = None):
        self.master.destroy()
                
if __name__ == "__main__":
    root = Tkinter.Tk()
    root.wm_title("Tile Sweeper")
    root.configure(background = "white")
    app = DispatchFrame(root)
    app.pack(fill = Tkinter.BOTH,expand = 1)
    root.mainloop()
