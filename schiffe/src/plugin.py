# -*- coding: utf-8 -*-
#===============================================================================
# Battleship Plugin by DarkVolli 2011
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
from Tools.Directories import fileExists, resolveFilename, SCOPE_CURRENT_PLUGIN, SCOPE_CURRENT_SKIN
from enigma import eTimer, gFont, getDesktop, RT_HALIGN_CENTER, RT_VALIGN_CENTER
import xml.etree.cElementTree
import random

VERSION = "0.2r0"
SAVEFILE = resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/Schiffe/Schiffe.sav")

XMAX = 10
YMAX = 10
XYMAX = 100


def RGB(r, g, b):
	return (r << 16) | (g << 8) | b


def main(session, **kwargs):
	session.open(Schiffe)


def Plugins(**kwargs):
	return [PluginDescriptor(name="Schiffe versenken", description=_("Battleship Game"), where=[PluginDescriptor.WHERE_PLUGINMENU],
	        icon="Schiffe.png", fnc=main)]

# Game cell...


class GameCell:
	def __init__(self, canvas, x, y, w, h):
		self.canvas = canvas
		self.x = x
		self.y = y
		self.w = w
		self.h = h
		self.value_ = 0
		self.focus_ = False
		self.hide_ = False

	def setValue(self, v):
		self.value_ = v

	def value(self):
		return self.value_

	def setFocus(self, f):
		self.focus_ = f

	def focus(self):
		return self.focus_

	def setHide(self, f):
		self.hide_ = f

	def paint(self):
		fg = RGB(255, 255, 255) # foreground
		blue = RGB(0, 0, 255) # background water
		focus = RGB(192, 192, 0) # background focus
		green = RGB(0, 255, 0) # background Ship
		red = RGB(255, 0, 0) # background Ship hit

		if self.value_ == 0:
			bg = blue
		elif self.value_ == 1:
			bg = blue
		elif self.value_ == 2:
			bg = blue
		elif self.value_ == 3:
			if not self.hide_:
				bg = green
			else:
				bg = blue
		elif self.value_ == 4:
			bg = red

		b = 0
		if self.focus_:
			b = 2
			self.canvas.fill(self.x, self.y, self.w, self.h, focus)

		self.canvas.fill(self.x + b, self.y + b, self.w - 2 * b, self.h - 2 * b, bg)

		if self.value_ == 2:
			self.canvas.writeText(self.x, self.y, self.w, self.h, fg, bg, gFont("Regular", 24), '*', RT_HALIGN_CENTER | RT_VALIGN_CENTER)

		self.canvas.flush()

# mainwindow...


class Schiffe(Screen):
	def __init__(self, session):
		# get framebuffer resolution...
		desk = getDesktop(0)
		wdesktop = int(desk.size().width())

		# cellsize depends from framebuffer resolution...
		if wdesktop == 720:
			CELL_SIZE = 20
		elif wdesktop == 1024:
			CELL_SIZE = 30
		elif wdesktop == 1280:
			CELL_SIZE = 40
		else:
			CELL_SIZE = 20

		# calculate skindata...
		CELL_OFFSET = 2
		cellfield = XMAX * CELL_SIZE + (XMAX - 1) * CELL_OFFSET
		CW = 2 * cellfield + 150 # canvas w
		CH = cellfield         # canvas h
		X0_OFFSET = 0                 # xoffset cellfield box
		X1_OFFSET = cellfield + 150   # xoffset cellfield you
		W = CW + 10           # window w
		H = CH + 40           # window h
		WX = cellfield + 10    # widgets xoffset
		W0Y = 25                # widget0 yoffset
		W1Y = cellfield - 116   # widget1 yoffset
		W2Y = cellfield - 66    # widget2 yoffset
		W3Y = cellfield - 16    # widget3 yoffset

		# set skin...
		Schiffe.skin = """
			<screen position="center,center" size="%d,%d" title="Schiffe versenken %s" >
				<widget source="Canvas" render="Canvas" position="5,20" size="%d,%d" />
				<widget name="message" position="%d,%d" size="140,40" valign="center" halign="center" font="Regular;21"/>
				<ePixmap name="green"    position="%d,%d"   zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
				<ePixmap name="blue" position="%d,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
				<ePixmap name="red"   position="%d,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
				<widget name="key_green"    position="%d,%d"   zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_blue" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center"  font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_red"   position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			</screen>""" % (W, H, VERSION, CW, CH, WX, W0Y, WX, W1Y, WX, W2Y, WX, W3Y, WX, W1Y, WX, W2Y, WX, W3Y)

		# get window background color - find xml for actual skin...
		filename = resolveFilename(SCOPE_CURRENT_SKIN, "skin.xml")
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
					# at least get the background color...
					if type == "Background":
						bgcolor = int(color[1:], 0x10)
		if not bgcolor:
			bgcolor = RGB(0, 0, 0)

		self.skin = Schiffe.skin
		Screen.__init__(self, session)
		self["Canvas"] = CanvasSource()
		self["message"] = Label(_("Status"))
		self["key_green"] = Button(_("new game"))
		self["key_blue"] = Button(_("solve game"))
		self["key_red"] = Button(_("quit game"))

		self.cnt = 0
		self.timer = eTimer()
		self.timer.callback.append(self.timerHandler)

		self.message = 0

		self["actions"] = ActionMap(["WizardActions", "ColorActions", "SetupActions"],
		{
			"ok": self.ok_pressed,
			"up": self.up_pressed,
			"down": self.down_pressed,
			"left": self.left_pressed,
			"right": self.right_pressed,
			"red": self.quit_game,
			"green": self.new_game,
			"blue": self.solve_game,
			"cancel": self.quit_game
		})

		# fill canvas with background color...
		self["Canvas"].fill(0, 0, CW, CH, bgcolor)

		self.you = []
		self.box = []
		self.youCells = []
		self.boxCells = []

		for j in range(YMAX):
			for i in range(XMAX):
				cell = GameCell(self["Canvas"],
								  i * (CELL_SIZE + CELL_OFFSET) + X0_OFFSET,
								  j * (CELL_SIZE + CELL_OFFSET),
								  CELL_SIZE, CELL_SIZE)
				self.boxCells.append(cell)

		for j in range(YMAX):
			for i in range(XMAX):
				cell = GameCell(self["Canvas"],
								  i * (CELL_SIZE + CELL_OFFSET) + X1_OFFSET,
								  j * (CELL_SIZE + CELL_OFFSET),
								  CELL_SIZE, CELL_SIZE)
				self.youCells.append(cell)

		self.onLayoutFinish.append(self.load_game)

	def ok_pressed(self):
		if not self.gameover:
			# check user input...
			cell = self.boxCells[self.Focus]
			# cell targeted some moves ago...
			if cell.value() in [2, 4]:
				return
			if cell.value() == 0:
				cell.setValue(2)
			elif cell.value() == 3:
				cell.setValue(4)
			cell.paint()
			self.moves += 1

			# check if user has won...
			cnt = 0
			for cell in self.boxCells:
				if cell.value() == 4:
					cnt += 1
			if cnt == 23:
				self.gameover = True
				self["message"].setText("you won!")
				self.timer.stop()
			else:
				# not won, next move for box...
				calcNewField(self.you)
				for i, cell in enumerate(self.youCells):
					cell.setValue(self.you[i])
					cell.paint()

				# check if box has won...
				cnt = 0
				for cell in self.youCells:
					if cell.value() == 4:
						cnt += 1
				if cnt == 23:
					self.gameover = True
					self["message"].setText("you lose!")
					self.timer.stop()
					# box has won, show all cells...
					for cell in self.boxCells:
						cell.setHide(False)
						cell.paint()
		else:
			print "Game over, start new game!"

	def up_pressed(self):
		if self.Focus > XMAX - 1:
			cell = self.boxCells[self.Focus]
			cell.setFocus(False)
			cell.paint()
			self.Focus -= XMAX
			cell = self.boxCells[self.Focus]
			cell.setFocus(True)
			cell.paint()

	def down_pressed(self):
		if self.Focus < XYMAX - XMAX:
			cell = self.boxCells[self.Focus]
			cell.setFocus(False)
			cell.paint()
			self.Focus += XMAX
			cell = self.boxCells[self.Focus]
			cell.setFocus(True)
			cell.paint()

	def left_pressed(self):
		if self.Focus > 0:
			if self.Focus % XMAX == 0:
				return
			cell = self.boxCells[self.Focus]
			cell.setFocus(False)
			cell.paint()
			self.Focus -= 1
			cell = self.boxCells[self.Focus]
			cell.setFocus(True)
			cell.paint()

	def right_pressed(self):
		if self.Focus < XYMAX - 1:
			if (self.Focus + 1) % XMAX == 0:
				return
			cell = self.boxCells[self.Focus]
			cell.setFocus(False)
			cell.paint()
			self.Focus += 1
			cell = self.boxCells[self.Focus]
			cell.setFocus(True)
			cell.paint()

	# displays moves and time in title...
	def timerHandler(self):
		self.instance.setTitle("Schiffe versenken %s %10d shots %10d sec" % (VERSION, self.moves, self.cnt))
		self.cnt += 1

	# create new game...
	def new_game(self, loadFromFile=False):
		self["message"].setText("")
		self.gameover = False
		self.Focus = 0

		if not loadFromFile:
			self.moves = 0
			self.cnt = 0

			self.you = []
			for y in range(XYMAX):
				self.you.append(0)
			ships(self.you)

			self.box = []
			for y in range(XYMAX):
				self.box.append(0)
			ships(self.box)

		for i, cell in enumerate(self.youCells):
			cell.setValue(self.you[i])
			cell.paint()

		for i, cell in enumerate(self.boxCells):
			cell.setValue(self.box[i])
			cell.setHide(True)
			if i == self.Focus:
				cell.setFocus(True)
			else:
				cell.setFocus(False)
			cell.paint()

		self.timer.start(1000)

	# display all ships and stop game...
	def solve_game(self):
		if not self.gameover:
			self.gameover = True
			self["message"].setText("you capitulated!")
			self.timer.stop()
			# show all cells...
			for cell in self.boxCells:
				cell.setHide(False)
				cell.paint()

	# save running game to file...
	def save_game(self):
		if not self.gameover:
			sav = open(SAVEFILE, "w")
			sav.write("%d %d\n" % (self.moves, self.cnt))

			for i, cell in enumerate(self.boxCells):
				sav.write("%d " % cell.value())
				if (i + 1) % XMAX == 0:
					sav.write("\n")

			for i, cell in enumerate(self.youCells):
				sav.write("%d " % cell.value())
				if (i + 1) % XMAX == 0:
					sav.write("\n")

			sav.close()
		else:
			# gameover no savefile needed...
			if fileExists(SAVEFILE):
				import os
				os.remove(SAVEFILE)

	# load game from file...
	def load_game(self):
		if fileExists(SAVEFILE, "r"):
			sav = open(SAVEFILE, "r")
			inp = sav.readline()
			inplist = inp.split()
			self.moves = int(inplist[0])
			self.cnt = int(inplist[1])

			self.box = []
			for y in range(YMAX):
				inp = sav.readline()
				inp = inp.strip()
				inplist = inp.split()
				for x in inplist:
					self.box.append(int(x))

			self.you = []
			for y in range(YMAX):
				inp = sav.readline()
				inp = inp.strip()
				inplist = inp.split()
				for x in inplist:
					self.you.append(int(x))

			sav.close()
			self.new_game(True)
		else:
			self.new_game()

	def quit_game(self):
		self.timer.stop()
		self.save_game()
		self.close()

###### enigma2 stuff ends here... ######

#good old C function :D


def rand():
	return random.randint(0, 32767)

# ships is derived from C++ source code by Stephan Dobretsberger 2001


def ships(field):
	# init shadow map...
	shadow = []
	row = []
	for x in range(XMAX + 3):
		row.append(0)
	for y in range(YMAX + 3):
		shadow.append(row[:])

	for shipLen in range(5, 1, -1):
		if shipLen == 2:
			shipNrMax = 4
		elif shipLen == 3:
			shipNrMax = 2
		else:
			shipNrMax = 1

		for shipNr in range(shipNrMax):
			# try 100 times to place the ship...
			ok = False
			for i in range(100):
				if not ok:
					ok = True
					if rand() % 2 == 0:
						# place ship horizontal...
						x = rand() % (XMAX - shipLen + 1)
						y = rand() % YMAX

						for j in range(shipLen + 2):
							if shadow[x + j][y] != 0 or shadow[x + j][y + 1] != 0 or shadow[x + j][y + 2] != 0:
								ok = False

						if ok:
							for j in range(shipLen):
								field[x + y * XMAX + j] = 3
								shadow[x + j + 1][y + 1] = 1

					else:
						# place ship vertical...
						x = rand() % XMAX
						y = rand() % (YMAX - shipLen + 1)

						for j in range(shipLen + 2):
							if shadow[x][y + j] != 0 or shadow[x + 1][y + j] != 0 or shadow[x + 2][y + j] != 0:
								ok = False

						if ok:
							for j in range(shipLen):
								field[x + (y + j) * XMAX] = 3
								shadow[x + 1][y + j + 1] = 1

			if not ok:
				# something went wrong...
				return False

	# everything is fine...
	return True

# calcNewField is derived from C++ source code by Stephan Dobretsberger 2001


def calcNewField(field):
	for i in range(XYMAX):
		if field[i] == 4:
			lx = i % XMAX
			ly = i / XMAX
			if lx > 0:
				if field[lx + ly * XMAX - 1] == 0:
					field[lx + ly * XMAX - 1] = 2
					return
				if field[lx + ly * XMAX - 1] == 3:
					field[lx + ly * XMAX - 1] = 4
					lx -= 1
					if lx > 0 and ly > 0 and field[lx + ly * XMAX - 1 - XMAX] != 2:
						field[lx + ly * XMAX - 1 - XMAX] = 1
					if lx > 0 and ly < YMAX - 1 and field[lx + ly * XMAX - 1 + XMAX] != 2:
						field[lx + ly * XMAX - 1 + XMAX] = 1
					if lx < XMAX - 1 and ly > 0 and field[lx + ly * XMAX + 1 - XMAX] != 2:
						field[lx + ly * XMAX + 1 - XMAX] = 1
					if lx < XMAX - 1 and ly < YMAX - 1 and field[lx + ly * XMAX + 1 + XMAX] != 2:
						field[lx + ly * XMAX + 1 + XMAX] = 1
					return
			if lx < XMAX - 1:
				if field[lx + ly * XMAX + 1] == 0:
					field[lx + ly * XMAX + 1] = 2
					return
				if field[lx + ly * XMAX + 1] == 3:
					field[lx + ly * XMAX + 1] = 4
					lx += 1
					if lx > 0 and ly > 0 and field[lx + ly * XMAX - 1 - XMAX] != 2:
						field[lx + ly * XMAX - 1 - XMAX] = 1
					if lx > 0 and ly < YMAX - 1 and field[lx + ly * XMAX - 1 + XMAX] != 2:
						field[lx + ly * XMAX - 1 + XMAX] = 1
					if lx < XMAX - 1 and ly > 0 and field[lx + ly * XMAX + 1 - XMAX] != 2:
						field[lx + ly * XMAX + 1 - XMAX] = 1
					if lx < XMAX - 1 and ly < YMAX - 1 and field[lx + ly * XMAX + 1 + XMAX] != 2:
						field[lx + ly * XMAX + 1 + XMAX] = 1
					return
			if ly > 0:
				if field[lx + ly * XMAX - XMAX] == 0:
					field[lx + ly * XMAX - XMAX] = 2
					return
				if field[lx + ly * XMAX - XMAX] == 3:
					field[lx + ly * XMAX - XMAX] = 4
					ly -= 1
					if lx > 0 and ly > 0 and field[lx + ly * XMAX - 1 - XMAX] != 2:
						field[lx + ly * XMAX - 1 - XMAX] = 1
					if lx > 0 and ly < YMAX - 1 and field[lx + ly * XMAX - 1 + XMAX] != 2:
						field[lx + ly * XMAX - 1 + XMAX] = 1
					if lx < XMAX - 1 and ly > 0 and field[lx + ly * XMAX + 1 - XMAX] != 2:
						field[lx + ly * XMAX + 1 - XMAX] = 1
					if lx < XMAX - 1 and ly < YMAX - 1 and field[lx + ly * XMAX + 1 + XMAX] != 2:
						field[lx + ly * XMAX + 1 + XMAX] = 1
					return
			if ly < YMAX - 1:
				if field[lx + ly * XMAX + XMAX] == 0:
					field[lx + ly * XMAX + XMAX] = 2
					return
				if field[lx + ly * XMAX + XMAX] == 3:
					field[lx + ly * XMAX + XMAX] = 4
					ly += 1
					if lx > 0 and ly > 0 and field[lx + ly * XMAX - 1 - XMAX] != 2:
						field[lx + ly * XMAX - 1 - XMAX] = 1
					if lx > 0 and ly < YMAX - 1 and field[lx + ly * XMAX - 1 + XMAX] != 2:
						field[lx + ly * XMAX - 1 + XMAX] = 1
					if lx < XMAX - 1 and ly > 0 and field[lx + ly * XMAX + 1 - XMAX] != 2:
						field[lx + ly * XMAX + 1 - XMAX] = 1
					if lx < XMAX - 1 and ly < YMAX - 1 and field[lx + ly * XMAX + 1 + XMAX] != 2:
						field[lx + ly * XMAX + 1 + XMAX] = 1
					return

	lx = -1
	i = 0
	while 1:
		if i + 1 < XYMAX:
			x = rand() % XMAX
			y = 2 * (rand() % (YMAX / 2)) + (x % 2)
		else:
			x = rand() % XMAX
			y = rand() % YMAX

		if field[x + y * XMAX] == 0: #fail (water)
			field[x + y * XMAX] = 2
			return

		if field[x + y * XMAX] == 3: #hit ship
			field[x + y * XMAX] = 4
			if x > 0 and y > 0:
				field[x + y * XMAX - 1 - XMAX] = 1
			if x > 0 and y < YMAX - 1:
				field[x + y * XMAX - 1 + XMAX] = 1
			if x < XMAX - 1 and y > 0:
				field[x + y * XMAX + 1 - XMAX] = 1
			if x < XMAX - 1 and y < YMAX - 1:
				field[x + y * XMAX + 1 + XMAX] = 1
			lx = x
			ly = y
			return
