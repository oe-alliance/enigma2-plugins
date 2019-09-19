# -*- coding: ISO-8859-1 -*-
#===============================================================================
# Sudoku Plugin by DarkVolli 2009
# class board by Robert Wohleb
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.
#===============================================================================

from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.Sources.CanvasSource import CanvasSource
from Components.Button import Button
from Components.Label import Label
from Components.ActionMap import ActionMap
from Tools.Directories import fileExists, resolveFilename, SCOPE_CURRENT_SKIN
from enigma import eTimer, gFont, getDesktop, RT_HALIGN_CENTER, RT_VALIGN_CENTER
import random
import xml.etree.cElementTree

SAVEFILE = "/usr/lib/enigma2/python/Plugins/Extensions/Sudoku/Sudoku.sav"

def RGB(r,g,b):
	return (r<<16)|(g<<8)|b


def main(session,**kwargs):
	session.open(Sudoku)


def Plugins(**kwargs):
	return [PluginDescriptor(name="Sudoku", description=_("Sudoku Game"), where = [PluginDescriptor.WHERE_PLUGINMENU], fnc=main)]


# thanks to Robert Wohleb for this class...
class board:
	boardlist = []
	partialboardlist = []


	def generate(self, numFilled=(9*9)):
		slots = []
		fillOrder = []

		random.seed()

		# setup board
		row = [0,0,0,0,0,0,0,0,0]
		for i in range(0, 9):
			self.boardlist.append(row[:])

		for j in range(0, 9):
			for i in range(0, 9):
				slots.append((i,j))

		self.search(slots, 0)
		
		while len(slots) > 0:
			i = random.randint(0, len(slots)-1)
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
			i = random.randint(0, len(nums)-1)
			fillOrder.append(nums[i])
			del nums[i]

		for i in fillOrder:
			x = slots[index][0]
			y = slots[index][1]
			self.boardlist[x][y] = i
			if (self.check()):
				if self.search(slots, index+1):
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
		xoffset = (3*(square % 3))
		yoffset = int(square / 3) * 3
		for j in range(0, 3):
			for i in range(0, 3):
				if not self.boardlist[xoffset+i][yoffset+j] == 0:
					if self.boardlist[xoffset+i][yoffset+j] in found:
						return False
					found.append(self.boardlist[xoffset+i][yoffset+j])
		return True


# Sudoku cell...
class SudokuCell:
	def __init__(self, canvas, x, y, w, h):
		self.canvas = canvas
		self.x      = x
		self.y      = y
		self.w      = w
		self.h      = h

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
		fg    = RGB(255,255,255) # foreground
		black = RGB(  0,  0,  0) # background readonly
		focus = RGB(192,192,  0) # background focus
		grey  = RGB( 70, 70, 70) # background not readonly
		green = RGB(  0,255,  0) # background solved
		red   = RGB(255,  0,  0) # background error

		b  = 2

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

		self.canvas.fill(self.x+b, self.y+b, self.w-2*b, self.h-2*b, bg)

		if self.value_ > 0:
			self.canvas.writeText(self.x, self.y, self.w, self.h, fg, bg, gFont("Regular", 24), str(self.value_), RT_HALIGN_CENTER|RT_VALIGN_CENTER)

		self.canvas.flush()


# mainwindow...
class Sudoku(Screen):

	def __init__(self, session):
		# get framebuffer resolution...
		desk = getDesktop(0)
		w = int(desk.size().width())
		h = int(desk.size().height())

		# display window in center...
		x = (w - 520) / 2
		y = (h - 390) / 2

		# set skin...
		# ToDo: change for HD Skins...
		Sudoku.skin = """
			<screen position="%d,%d" size="520,390" title="Sudoku 0.1" >
				<widget source="Canvas" render="Canvas" position="10,20" size="354,354" />
				<widget name="gamelevel" position="380,25" size="140,40" font="Regular;21"/>
				<ePixmap name="green"    position="375,98"   zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
				<ePixmap name="yellow"  position="375,178" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
				<ePixmap name="blue" position="375,258" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
				<ePixmap name="red"   position="375,338" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
				<widget name="key_green"    position="375,98"   zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_yellow"  position="375,178" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_blue" position="375,258" zPosition="5" size="140,40" valign="center" halign="center"  font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_red"   position="375,338" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			</screen>""" % (x, y)

		# i'm not really sure if this is the right way to get the background color from a skinned window?
		# there must exist a better way? everything is taken from skin.py
		# find xml for actual skin...
		filename = resolveFilename(SCOPE_CURRENT_SKIN) + "skin.xml"
		actualSkin = xml.etree.cElementTree.parse(filename).getroot()

		# get colors from skin and write to dictionary
		colorNames = dict()
		for c in actualSkin.findall("colors"):
			for color in c.findall("color"):
				get_attr = color.attrib.get
				name = get_attr("name")
				color = get_attr("value")
				if name and color:
					colorNames[name] = color
					#print "Color:", name, color

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
					#print type, color
					# at least get the background color...
					if type == "Background":
						bgcolor = int(color[1:], 0x10)
		#if not bgcolor:
		bgcolor = RGB(  0,  0,  0)

		self.skin = Sudoku.skin
		Screen.__init__(self, session)
		self["Canvas"] = CanvasSource()
		self["gamelevel"] = Label(_(" <    easy    >"))
		self["key_green"] = Button(_("new game"))
		self["key_yellow"] = Button(_("check game"))
		self["key_blue"] = Button(_("restart game"))
		self["key_red"] = Button(_("solve game"))
		
		self.cnt = 0;
		self.timer = eTimer()
		self.timer.callback.append(self.timerHandler)

		self.xFocus = 4
		self.yFocus = 4

		self.gameLevel = 0

		self["actions"] = ActionMap(["WizardActions", "ColorActions", "SetupActions"],
		{
			"0"     : self.bt_0_pressed,
			"1"     : self.bt_1_pressed,
			"2"     : self.bt_2_pressed,
			"3"     : self.bt_3_pressed,
			"4"     : self.bt_4_pressed,
			"5"     : self.bt_5_pressed,
			"6"     : self.bt_6_pressed,
			"7"     : self.bt_7_pressed,
			"8"     : self.bt_8_pressed,
			"9"     : self.bt_9_pressed,
			"up"    : self.up_pressed,
			"down"  : self.down_pressed,
			"left"  : self.left_pressed,
			"right" : self.right_pressed,
			"red"   : self.bt_solve_game,
			"green" : self.bt_new_game,
			"yellow": self.bt_check_game,
			"blue"  : self.bt_restart_game,
			"cancel": self.quit,
			"deleteForward" : self.next_pressed,
			"deleteBackward": self.previous_pressed,
		})
		# fill canvas with background color...
		self["Canvas"].fill(0, 0, 354, 354, bgcolor)

		self.board_cells = []
		self.board_values= []
		# ToDo: change for HD Skins...
		GROUP_SIZE	= 108
		CELL_SIZE	= 35
		CELL_OFFSET	= 4

		for j in range(9):
			tmp = []
			for i in range(9):
				cell = SudokuCell(self["Canvas"],
								  j * (CELL_SIZE + CELL_OFFSET) + (j / 3) * (GROUP_SIZE - 3 * CELL_SIZE),
								  i * (CELL_SIZE + CELL_OFFSET) + (i / 3) * (GROUP_SIZE - 3 * CELL_SIZE),
								  CELL_SIZE, CELL_SIZE)
				tmp.append(cell)
			self.board_cells.append(tmp)

		row = [0,0,0,0,0,0,0,0,0]
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
			self.yFocus = self.yFocus-1
			cell = self.board_cells[self.xFocus][self.yFocus]
			cell.setFocus(True)
			cell.paint()


	def down_pressed(self):
		if self.yFocus < 8:
			cell = self.board_cells[self.xFocus][self.yFocus]
			cell.setFocus(False)
			cell.paint()
			self.yFocus = self.yFocus+1
			cell = self.board_cells[self.xFocus][self.yFocus]
			cell.setFocus(True)
			cell.paint()


	def left_pressed(self):
		if self.xFocus > 0:
			cell = self.board_cells[self.xFocus][self.yFocus]
			cell.setFocus(False)
			cell.paint()
			self.xFocus = self.xFocus-1
			cell = self.board_cells[self.xFocus][self.yFocus]
			cell.setFocus(True)
			cell.paint()


	def right_pressed(self):
		if self.xFocus < 8:
			cell = self.board_cells[self.xFocus][self.yFocus]
			cell.setFocus(False)
			cell.paint()
			self.xFocus = self.xFocus+1
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
			self.instance.setTitle("Sudoku 0.1 %10d sec" % self.cnt)
			self.cnt += 1
		else:
			self.instance.setTitle("Sudoku 0.1")


	# look for wrong cells...
	def check_game(self, highlight):
		empty = False;
		correct = True;
	
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
						if ((i != k	and self.board_cells[k][j].value() == val) or (j != k and self.board_cells[i][k].value() == val)):
							err = True
							break
	
					if err:
						if highlight:
							cell.color(3) #red
							cell.paint()
	
						correct	= False

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
		n =	11 * (5 - self.gameLevel)
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
		self.cnt=0;
		for j in range(0, 9):
			for i in range(0, 9):
				cell = self.board_cells[i][j]
	
				cell.setValue(self.board_values[i][j])
				cell.setReadonly(True)
				cell.color(0) #black
				cell.paint()


	# save actual game to file...
	def save_game(self):
		sav = open(SAVEFILE, "w")
		sav.write( "%d %d\n" % (self.gameLevel, self.cnt) )

		for j in range(0, 9):
			for i in range(0, 9):
				sav.write("%d %d %d\n" % (self.board_values[i][j], self.board_cells[i][j].value(), self.board_cells[i][j].readonly()))

		sav.close()


	# load game from file...
	def load_game(self):
		solved = True

		if fileExists(SAVEFILE, "r"):
			sav = open(SAVEFILE, "r")
			inp = sav.readline()
			inplist = inp.split()
			
			self.gameLevel = int(inplist[0])
			self.cnt = int(inplist[1])
	
			for j in range(0, 9):
				for i in range(0, 9):
					inp = sav.readline()
					inp = inp.strip()
					inplist = inp.split()
					self.board_values[i][j] = int(inplist[0])
					cell = self.board_cells[i][j]
					cell.setValue(int(inplist[1]))
					cell.setReadonly(int(inplist[2]))
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
