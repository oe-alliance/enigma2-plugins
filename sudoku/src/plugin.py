# -*- coding: ISO-8859-1 -*-
#===============================================================================
# Sudoku Plugin by DarkVolli 2009
# class board by Robert Wohleb
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.
# modded by Lululla to 20220713 - skin by MMark
#===============================================================================

from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.Sources.CanvasSource import CanvasSource
from Components.Button import Button
from Components.Label import Label
from Components.ActionMap import ActionMap
from Tools.Directories import fileExists, resolveFilename, SCOPE_CURRENT_PLUGIN, SCOPE_CURRENT_SKIN
from enigma import eTimer, gFont, getDesktop, RT_HALIGN_CENTER, RT_VALIGN_CENTER
from random import seed, randint
from xml.etree.cElementTree import parse
# from six.moves import range

VERSION = "7.1r0"
SAVEFILE = resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/Schiffe/schiffe.sav")
helper ='The playing strength can be changed with the "<" and ">"\nkeys pressing the "0" the current field is deleted.\nUse CH + / CH- to change level. When you quit the game,\nthe game state is saved in the plugin directory and reloaded\nautomatically on next start ...good fun!\nDark Volli - by Robert Wohleb\nModded by Lululla - Skin by MMark at 20220714'

def getDesktopSize():
    from enigma import getDesktop
    s = getDesktop(0).size()
    return (s.width(), s.height())

def isFHD():
    desktopSize = getDesktopSize()
    return desktopSize[0] == 1920

def main(session, **kwargs):
        session.open(Sudoku)

def Plugins(**kwargs):
    return [PluginDescriptor(name="Sudoku", description=_("Sudoku Game"), where = [PluginDescriptor.WHERE_PLUGINMENU],
            icon="sudoku.png", fnc=main)]

def RGB(r, g, b):
    return (r << 16) | (g << 8) | b

# thanks to Robert Wohleb for this class...
class board:
    boardlist = []
    partialboardlist = []

    def generate(self, numFilled=(9 * 9)):
        slots = []
        fillOrder = []

        seed()

        # setup board
        row = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        for i in range(0, 9):
            self.boardlist.append(row[:])

        for j in range(0, 9):
            for i in range(0, 9):
                slots.append((i, j))

        self.search(slots, 0)

        while len(slots) > 0:
            i = randint(0, len(slots) - 1)
            fillOrder.append(slots[i])
            del slots[i]

        # setup board
        for i in range(0, 9):
            self.partialboardlist.append(row[:])

        for i in range(0, numFilled):
            j = fillOrder[i]
            self.partialboardlist[j[0]][j[1]] = self.boardlist[j[0]][j[1]]

    def search(self, slots, index):
        nums = []
        fillOrder = []

        if len(slots) == index:
            return self.check()

        for i in range(1, 10):
            nums.append(i)

        while len(nums) > 0:
            i = randint(0, len(nums) - 1)
            fillOrder.append(nums[i])
            del nums[i]

        for i in fillOrder:
            x = slots[index][0]
            y = slots[index][1]
            self.boardlist[x][y] = i
            if (self.check()):
                if self.search(slots, index + 1):
                    return True
            self.boardlist[x][y] = 0
        return False

    def check(self):
        for i in range(0, 9):
            if (not self.checkRow(i)) or (not self.checkCol(i)) or (not self.checkSquare(i)):
                return False
        return True

    def checkRow(self, row):
        found = []
        for i in range(0, 9):
            if not self.boardlist[i][row] == 0:
                if self.boardlist[i][row] in found:
                    return False
                found.append(self.boardlist[i][row])
        return True

    def checkCol(self, col):
        found = []
        for j in range(0, 9):
            if not self.boardlist[col][j] == 0:
                if self.boardlist[col][j] in found:
                    return False
                found.append(self.boardlist[col][j])
        return True

    def checkSquare(self, square):
        found = []
        xoffset = (3 * (square % 3))
        yoffset = int(square // 3) * 3
        for j in range(0, 3):
            for i in range(0, 3):
                if not self.boardlist[xoffset + i][yoffset + j] == 0:
                    if self.boardlist[xoffset + i][yoffset + j] in found:
                        return False
                    found.append(self.boardlist[xoffset + i][yoffset + j])
        return True


# Sudoku cell...
class SudokuCell:
    def __init__(self, canvas, x, y, w, h):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.w = w
        self.h = h

        self.value_ = 0
        self.focus_ = False
        self.readonly_ = False
        self.bg_color = 0

    def setValue(self, v):
        self.value_ = v

    def value(self):
        return self.value_

    def setFocus(self, f):
        self.focus_ = f

    def focus(self):
        return self.focus_

    def setReadonly(self, r):
        self.readonly_ = r

    def readonly(self):
        return self.readonly_

    def color(self, col):
        self.bg_color = col

    def paint(self):
        fg = RGB(255, 255, 255) # foreground
        black = RGB(0, 0, 0) # background readonly
        focus = RGB(150, 73, 7) # background focus
        grey = RGB(70, 70, 70) # background not readonly
        green = RGB(0, 255, 0) # background solved
        red = RGB(255, 0, 0) # background error

        b = 2
        self.canvas.fill(self.x, self.y, self.w, self.h, fg)

        if self.bg_color == 0:
            bg = black
        elif self.bg_color == 1:
            bg = grey
        elif self.bg_color == 2:
            bg = green
        elif self.bg_color == 3:
            bg = red

        if self.focus_:
            bg = focus

        self.canvas.fill(self.x + b, self.y + b, self.w - 2 * b, self.h - 2 * b, bg)

        if self.value_ > 0:
            self.canvas.writeText(self.x, self.y, self.w, self.h, fg, bg, gFont("Regular", 24), str(self.value_), RT_HALIGN_CENTER | RT_VALIGN_CENTER)
            if isFHD():
                self.canvas.writeText(self.x, self.y, self.w, self.h, fg, bg, gFont("Regular", 32), str(self.value_), RT_HALIGN_CENTER | RT_VALIGN_CENTER)

        self.canvas.flush()


# mainwindow...
class Sudoku(Screen):
    def __init__(self, session):
        # get framebuffer resolution...
        desk = getDesktop(0)
        w = int(desk.size().width())
        h = int(desk.size().height())
        # display window in center...
        if isFHD():
            x = 60
            y = 140
        else:
            x = 0
            y = 0
            # x = (w - 520) // 2
            # y = (h - 390) // 2
        # set skin...
        if isFHD():
            Sudoku.skin = """
                    <screen name="Sudoku" position="%d,%d" size="1800,900" title="Sudoku" backgroundColor="#101010">
                        <ePixmap position="0,0" size="1800,900" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Sudoku/pic/sudoku.jpg" />
                        <widget name="gamelevel" position="50,10" size="350,70" valign="center" halign="center" font="Regular;40" foregroundColor="yellow" backgroundColor="#000000" transparent="1" zPosition="1" />
                        <widget source="Canvas" render="Canvas" position="794,150" size="696,661" backgroundColor="#60ffffff" transparent="1" alphatest="blend" zPosition="2" />
                        <ePixmap position="50,165" pixmap="buttons/key_green.png" size="80,40" alphatest="blend" zPosition="2" />
                        <widget name="key_green" font="Regular;30" position="150,165" size="450,40" halign="left" valign="center" backgroundColor="black" zPosition="1" transparent="1" />
                        <ePixmap position="50,215" pixmap="buttons/key_red.png" size="80,40" alphatest="blend" zPosition="2" />
                        <widget name="key_red" font="Regular;30" position="150,215" size="450,40" halign="left" valign="center" backgroundColor="black" zPosition="1" transparent="1" />
                        <ePixmap position="50,265" pixmap="buttons/key_blue.png" size="80,40" alphatest="blend" zPosition="2" />
                        <widget name="key_blue" font="Regular;30" position="152,265" size="450,40" halign="left" valign="center" backgroundColor="black" zPosition="1" transparent="1" />
                        <eLabel position="50,315" size="300,3" backgroundColor="#202020" zPosition="1" />
                        <ePixmap position="47,82" size="80,80" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Sudoku/pic/rocket.png" alphatest="blend" zPosition="3" />
                        <widget name="result" render="Label" position="23,518" size="710,340" font="Regular; 32" halign="left" foregroundColor="#ffff00" backgroundColor="#000000" transparent="1" zPosition="3" />
                        <widget name="movex" render="Label" position="136,98" size="229,50" font="Regular; 34" halign="left" foregroundColor="yellow" backgroundColor="#000000" transparent="1" zPosition="3" />
                    </screen>""" % (x, y)

        else:
            Sudoku.skin = """
                        <screen name="Sudoku" position="%d,%d" size="1260,720" title="Sudoku" backgroundColor="#101010">
                        <ePixmap position="0,0" size="1259,720" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Sudoku/pic/sudokuHD.jpg" />
                        <widget name="gamelevel" position="50,10" size="350,70" valign="center" halign="center" font="Regular;40" foregroundColor="yellow" backgroundColor="#000000" transparent="1" zPosition="1" />
                        <widget source="Canvas" render="Canvas" position="534,28" size="696,661" backgroundColor="#60ffffff" transparent="1" alphatest="blend" zPosition="2" />
                        <widget name="key_green" font="Regular;30" position="135,165" size="450,40" halign="left" valign="center" backgroundColor="black" zPosition="1" transparent="1" />
                        <widget name="key_red" font="Regular;30" position="135,216" size="450,40" halign="left" valign="center" backgroundColor="black" zPosition="1" transparent="1" />
                        <widget name="key_blue" font="Regular;30" position="133,265" size="450,40" halign="left" valign="center" backgroundColor="black" zPosition="1" transparent="1" />
                        <eLabel position="50,315" size="300,3" backgroundColor="#202020" zPosition="1" />
                        <ePixmap position="47,82" size="80,80" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Sudoku/pic/rocket.png" alphatest="blend" zPosition="3" />
                        <widget name="result" render="Label" position="28,316" size="495,370" font="Regular; 22" halign="left" foregroundColor="#ffff00" backgroundColor="#000000" transparent="1" zPosition="4" />
                        <widget name="movex" render="Label" position="136,98" size="229,50" font="Regular; 34" halign="left" foregroundColor="yellow" backgroundColor="dark" transparent="1" zPosition="3" />
                        <eLabel name="" position="28,316" size="495,370" zPosition="2" />
                        <eLabel name="" position="134,164" size="385,138" />
                        <eLabel name="" position="62,216" size="70,40" backgroundColor="red" zPosition="3" />
                        <eLabel name="" position="61,266" size="70,40" backgroundColor="StarBlue" zPosition="3" />
                        <eLabel name="" position="57,164" size="70,40" zPosition="3" backgroundColor="green" />
                        </screen>
                        """ % (x, y)

        # i'm not really sure if this is the right way to get the background color from a skinned window?
        # there must exist a better way? everything is taken from skin.py
        # find xml for actual skin...
        filename = resolveFilename(SCOPE_CURRENT_SKIN) + "skin.xml"
        actualSkin = parse(filename).getroot()

        # get colors from skin and write to dictionary
        colorNames = dict()
        for c in actualSkin.findall("colors"):
            for color in c.findall("color"):
                get_attr = color.attrib.get
                name = get_attr("name")
                color = get_attr("value")
                if name and color:
                    colorNames[name] = color
                    #print("Color:", name, color)

        # find colors for skinned window...
        for windowstyle in actualSkin.findall("windowstyle"):
            # look or skinned window...
            if windowstyle.attrib.get("id") == "0":
                for color in windowstyle.findall("color"):
                    get_attr = color.attrib.get
                    type = get_attr("name")
                    color = get_attr("color")
                    # is it a "named" color?
                    if color[0] != '#':
                        # is "named" color, have to look in dictionary...
                        color = colorNames[color]
                    #print(type, color)
                    # at least get the background color...
                    if type == "Background":
                        bgcolor = int(color[1:], 0x10)
        #if not bgcolor:
        bgcolor = RGB(0, 0, 0)

        self.skin = Sudoku.skin
        Screen.__init__(self, session)
        self.setTitle("Sudoku %s" % VERSION)
        self["Canvas"] = CanvasSource()
        self["gamelevel"] = Label(_(" <    easy    >"))
        self["key_green"] = Button(_("new game"))
        self["key_yellow"] = Button(_("check game"))
        self["key_blue"] = Button(_("restart game"))
        self["key_red"] = Button(_("solve game"))
        self["result"] = Label(_(helper))
        self["movex"] = Label(_(""))

        self.cnt = 0
        self.timer = eTimer()
        self.timer.callback.append(self.timerHandler)

        self.xFocus = 4
        self.yFocus = 4

        self.gameLevel = 0

        self["actions"] = ActionMap(["WizardActions", "ColorActions", "SetupActions"],
        {
            "0": self.bt_0_pressed,
            "1": self.bt_1_pressed,
            "2": self.bt_2_pressed,
            "3": self.bt_3_pressed,
            "4": self.bt_4_pressed,
            "5": self.bt_5_pressed,
            "6": self.bt_6_pressed,
            "7": self.bt_7_pressed,
            "8": self.bt_8_pressed,
            "9": self.bt_9_pressed,
            "up": self.up_pressed,
            "down": self.down_pressed,
            "left": self.left_pressed,
            "right": self.right_pressed,
            "red": self.bt_solve_game,
            "green": self.bt_new_game,
            "yellow": self.bt_check_game,
            "blue": self.bt_restart_game,
            "cancel": self.quit,
            "deleteForward": self.next_pressed,
            "deleteBackward": self.previous_pressed,
        })
        # fill canvas with background color...

        # self["Canvas"].fill(0, 0, 354, 354, bgcolor)
        # if isFHD():
        self["Canvas"].fill(0, 0, 500, 500, bgcolor)
        #

        self.board_cells = []
        self.board_values = []
        # ToDo: change for HD Skins...

        # edit lululla original
        # GROUP_SIZE = 108
        # CELL_SIZE = 35
        # CELL_OFFSET = 4

        # if isFHD():
        GROUP_SIZE = 208
        CELL_SIZE = 70
        CELL_OFFSET = 4

        for j in range(9):
            tmp = []
            for i in range(9):
                cell = SudokuCell(self["Canvas"],
                      j * (CELL_SIZE + CELL_OFFSET) + (j // 3) * (GROUP_SIZE - 3 * CELL_SIZE),
                      i * (CELL_SIZE + CELL_OFFSET) + (i // 3) * (GROUP_SIZE - 3 * CELL_SIZE),
                      CELL_SIZE, CELL_SIZE)
                tmp.append(cell)
            self.board_cells.append(tmp)

        row = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        for i in range(0, 9):
            self.board_values.append(row[:])

        self.onLayoutFinish.append(self.load_game)

    def bt_0_pressed(self):
        self.key_event1(0)

    def bt_1_pressed(self):
        self.key_event1(1)

    def bt_2_pressed(self):
        self.key_event1(2)

    def bt_3_pressed(self):
        self.key_event1(3)

    def bt_4_pressed(self):
        self.key_event1(4)

    def bt_5_pressed(self):
        self.key_event1(5)

    def bt_6_pressed(self):
        self.key_event1(6)

    def bt_7_pressed(self):
        self.key_event1(7)

    def bt_8_pressed(self):
        self.key_event1(8)

    def bt_9_pressed(self):
        self.key_event1(9)

    def key_event1(self, key):
        cell = self.board_cells[self.xFocus][self.yFocus]
        if not cell.readonly():
            cell.setValue(key)
            cell.color(1) #grey
            cell.paint()
            self.check_game(False)

    def up_pressed(self):
        if self.yFocus > 0:
            cell = self.board_cells[self.xFocus][self.yFocus]
            cell.setFocus(False)
            cell.paint()
            self.yFocus = self.yFocus - 1
            cell = self.board_cells[self.xFocus][self.yFocus]
            cell.setFocus(True)
            cell.paint()

    def down_pressed(self):
        if self.yFocus < 8:
            cell = self.board_cells[self.xFocus][self.yFocus]
            cell.setFocus(False)
            cell.paint()
            self.yFocus = self.yFocus + 1
            cell = self.board_cells[self.xFocus][self.yFocus]
            cell.setFocus(True)
            cell.paint()

    def left_pressed(self):
        if self.xFocus > 0:
            cell = self.board_cells[self.xFocus][self.yFocus]
            cell.setFocus(False)
            cell.paint()
            self.xFocus = self.xFocus - 1
            cell = self.board_cells[self.xFocus][self.yFocus]
            cell.setFocus(True)
            cell.paint()

    def right_pressed(self):
        if self.xFocus < 8:
            cell = self.board_cells[self.xFocus][self.yFocus]
            cell.setFocus(False)
            cell.paint()
            self.xFocus = self.xFocus + 1
            cell = self.board_cells[self.xFocus][self.yFocus]
            cell.setFocus(True)
            cell.paint()

    def next_pressed(self):
        self.session.openWithCallback(self.next_pressedCallback, MessageBox, _("Change the game level and start new game?"))

    def next_pressedCallback(self, result):
        if result:
            self.gameLevel += 1
            if self.gameLevel > 3:
                self.gameLevel = 0
            self.setGamelLevelLabel()
            self.new_game()

    def previous_pressed(self):
        self.session.openWithCallback(self.previous_pressedCallback, MessageBox, _("Change the game level and start new game?"))

    def previous_pressedCallback(self, result):
        if result:
            self.gameLevel -= 1
            if self.gameLevel < 0:
                self.gameLevel = 3
            self.setGamelLevelLabel()
            self.new_game()

    def setGamelLevelLabel(self):
        if self.gameLevel == 0:
            self["gamelevel"].setText("<     easy     >")
        elif self.gameLevel == 1:
            self["gamelevel"].setText("<   medium   >")
        elif self.gameLevel == 2:
            self["gamelevel"].setText("<     hard     >")
        elif self.gameLevel == 3:
            self["gamelevel"].setText("< impossible >")

    def bt_new_game(self):
        self.new_game()

    def bt_check_game(self):
        self.cnt += 100
        self.check_game(True)

    def bt_restart_game(self):
        self.restart_game()

    def bt_solve_game(self):
        self.solve_game()

    def quit(self):
        self.timer.stop()
        self.save_game()
        self.close()

    # displays time in title...

    def timerHandler(self):
        if self.cnt > 0:
            self["movex"].setText("%10d sec" % self.cnt)
            self.cnt += 1
        else:
            self["movex"].setText("HELLO")

    # look for wrong cells...
    def check_game(self, highlight):
        empty = False
        correct = True

        for j in range(0, 9):
            for i in range(0, 9):
                cell = self.board_cells[i][j]
                val = cell.value()

                if cell.readonly():
                    continue

                if not val:
                    empty = True
                else:
                    err = False
                    for k in range(0, 9):
                        if ((i != k and self.board_cells[k][j].value() == val) or (j != k and self.board_cells[i][k].value() == val)):
                            err = True
                            break

                    if err:
                        if highlight:
                            cell.color(3) #red
                            cell.paint()

                        correct = False

                    elif highlight:
                        cell.color(1) #grey
                        cell.paint()

        if not empty and correct:
            self.timer.stop()
            for j in range(0, 9):
                for i in range(0, 9):
                    cell = self.board_cells[i][j]
                    cell.color(2) #green
                    cell.paint()
                    cell.setReadonly(True)

    # create new game...

    def new_game(self):
        cell = self.board_cells[self.xFocus][self.yFocus]
        cell.setFocus(True)

        b = board()
        del b.boardlist[:]
        del b.partialboardlist[:]
        n = 11 * (5 - self.gameLevel)
        #n = 80
        b.generate(n)
        self.board_values = b.boardlist
        for j in range(0, 9):
            for i in range(0, 9):
                cell = self.board_cells[i][j]
                cell.setValue(b.partialboardlist[i][j])
                if b.partialboardlist[i][j] == 0:
                    cell.setReadonly(False)
                    cell.color(1) #grey
                else:
                    cell.setReadonly(True)
                    cell.color(0) #black
                cell.paint()

        self.cnt = 1
        self.timer.start(1000)

    # Restart game...

    def restart_game(self):
        solved = True

        for j in range(0, 9):
            for i in range(0, 9):
                cell = self.board_cells[i][j]

                if not cell.readonly():
                    solved = False
                    cell.color(1) #grey
                    cell.setValue(0)
                    cell.paint()

        if solved:
            self.new_game()

    # display all values and stop game...

    def solve_game(self):
        self.cnt = 0
        for j in range(0, 9):
            for i in range(0, 9):
                cell = self.board_cells[i][j]

                cell.setValue(self.board_values[i][j])
                cell.setReadonly(True)
                cell.color(0) #black
                cell.paint()

    # save actual game to file...

    def save_game(self):
        try:
            sav = open(SAVEFILE, "w")
            sav.write("%d %d\n" % (self.gameLevel, self.cnt))

            for j in range(0, 9):
                for i in range(0, 9):
                    sav.write("%d %d %d\n" % (self.board_values[i][j], self.board_cells[i][j].value(), self.board_cells[i][j].readonly()))
            sav.close()
        except IOError:
            pass


    # load game from file...

    def load_game(self):
        solved = True
        if fileExists(SAVEFILE, "r"):
            sav = open(SAVEFILE, "r")
            inp = sav.readline().strip()
            inplist = inp.split()
            self.gameLevel = int(float(inplist[0]))
            self.cnt = int(float(inplist[1]))
            # self.gameLevel = int(inplist[0])
            # self.cnt = int(inplist[1])
            for j in range(0, 9):
                for i in range(0, 9):
                    inp = sav.readline()
                    inp = inp.strip()
                    inplist = inp.split()
                    self.board_values[i][j] = int(float(inplist[0]))
                    cell = self.board_cells[i][j]
                    cell.setValue(int(float(inplist[1])))
                    cell.setReadonly(int(float(inplist[2])))
                    if cell.readonly():
                        cell.color(0) # black
                    else:
                        cell.color(1) # grey
                        solved = False
                    cell.paint()
            sav.close()
        if solved:
            self.new_game()
        else:
            cell = self.board_cells[self.xFocus][self.yFocus]
            cell.setFocus(True)
            cell.paint()
            self.check_game(False)
            self.setGamelLevelLabel()
        self.timer.start(1000)
