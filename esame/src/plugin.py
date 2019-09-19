# -*- coding: ISO-8859-1 -*-
#===============================================================================
# eSame Game Plugin by DarkVolli 2009
# Original Game kSame by Marcus Kreutzberger
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.
#===============================================================================

from enigma import ePicLoad, eTimer, getDesktop

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Plugins.Plugin import PluginDescriptor

from Components.Pixmap import Pixmap, MovingPixmap
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Button import Button

from Tools.LoadPixmap import LoadPixmap

from stonefield import StoneField

import time


def main(session,**kwargs):
	session.open(eSame)

def Plugins(**kwargs):
	return [PluginDescriptor(name="eSame", description=_("eSame Game Plugin"), where = PluginDescriptor.WHERE_PLUGINMENU, fnc=main)]

# mainwindow...
class eSame(Screen):
	def __init__(self, session, args = 0):
		# some default values - be careful if you change this...
		stone_width = 30
		stone_height = 30
		stone_space = 4

		self.maxslices = 4

		self.stonesX = 15
		self.stonesY = 10
		self.maxstones = self.stonesX * self.stonesY

		path = "/usr/lib/enigma2/python/Plugins/Extensions/eSame/data/"

		# Load bitmaps...
		self.maps = []
		for color in ["red", "blue", "green"]:
			tmp = []
			for x in range(self.maxslices):
				tmp.append(LoadPixmap(path + color + str(x) + ".png"))
			self.maps.append(tmp)

		# solve focus coordinates and generate part of skin...
		self.focuslist = []
		skincontent = ""

		posX = -1
		for x in range(self.maxstones):
			posY = x / self.stonesX
			posX += 1
			if posX >= self.stonesX:
				posX = 0

			absX = stone_space + (posX*(stone_space + stone_width))
			absY = stone_space + (posY*(stone_space + stone_height))
			self.focuslist.append((absX+5, absY+5))
			skincontent += "<widget name=\"stone" + str(x) + "\" position=\"" + str(absX+5)+ "," + str(absY+5) + "\" size=\"" + str(stone_width) + "," + str(stone_height) + "\" zPosition=\"2\" transparent=\"1\" alphatest=\"on\" />"

		# solve window size...
		size_w = 5 + stone_width  * self.stonesX + stone_space * (self.stonesX - 1) + 5
		size_h = 5 + stone_height * self.stonesY + stone_space * (self.stonesY - 1) + 85

		# get framebuffer resolution...
		desk = getDesktop(0)
		w = int(desk.size().width())
		h = int(desk.size().height())

		# display window in center...
		x0 = (w - size_w) / 2
		y0 = (h - size_h) / 2

		# solve skin...
		self.skin = "<screen position=\""+str(x0)+","+str(y0)+"\" size=\"" + str(size_w) + "," + str(size_h) + "\" title=\"eSame  v0.1\" >" +\
		"<widget name=\"frame\" position=\""+str(5+stone_space)+","+str(5+stone_space)+"\" size=\""+str(stone_width)+","+str(stone_height)+"\" pixmap=\""+path+"focus.png\" zPosition=\"1\" alphatest=\"on\" />" +\
		"<widget name=\"lbColors\" position=\"5,"+str(size_h-85)+"\" size=\"170,40\" valign=\"center\" font=\"Regular;17\" />" +\
		"<widget name=\"lbBoard\" position=\"175,"+str(size_h-85)+"\" size=\"140,40\" valign=\"center\" font=\"Regular;17\" />" +\
		"<widget name=\"lbMarked\" position=\"310,"+str(size_h-85)+"\" size=\"100,40\" valign=\"center\" font=\"Regular;17\" />" +\
		"<widget name=\"lbScore\" position=\"410,"+str(size_h-85)+"\" size=\"110,40\" valign=\"center\" font=\"Regular;17\" />" +\
		"<ePixmap name=\"green\" position=\"5,"+str(size_h-45)+"\" zPosition=\"3\" size=\"140,40\" pixmap=\"skin_default/buttons/green.png\" transparent=\"1\" alphatest=\"on\" /> \n" +\
		"<ePixmap name=\"yellow\" position=\""+str(size_w-145)+","+str(size_h-45)+"\" zPosition=\"3\" size=\"140,40\" pixmap=\"skin_default/buttons/yellow.png\" transparent=\"1\" alphatest=\"on\" /> \n" +\
		"<widget name=\"key_green\" position=\"5,"+str(size_h-45)+"\" zPosition=\"4\" size=\"140,40\" valign=\"center\" halign=\"center\" font=\"Regular;18\" transparent=\"1\" foregroundColor=\"white\" shadowColor=\"black\" shadowOffset=\"-1,-1\" /> \n" +\
		"<widget name=\"key_yellow\" position=\""+str(size_w-145)+","+str(size_h-45)+"\" zPosition=\"4\" size=\"140,40\" valign=\"center\" halign=\"center\" font=\"Regular;18\" transparent=\"1\" foregroundColor=\"white\" shadowColor=\"black\" shadowOffset=\"-1,-1\" /> \n" +\
		skincontent + "</screen>"

		Screen.__init__(self, session)

		self["actions"] = ActionMap(["OkCancelActions", "WizardActions", "ColorActions"],
		{
			"cancel": self.Exit,
			"ok": self.key_ok,
			"left": self.key_left,
			"right": self.key_right,
			"up": self.key_up,
			"down": self.key_down,
			"green" : self.key_green,
			"yellow": self.key_yellow,
		}, -1)

		self["frame"] = MovingPixmap()
		self["lbColors"] = Label()
		self["lbBoard"] = Label()
		self["lbMarked"] = Label()
		self["lbScore"] = Label()
		self["key_green"] = Button("new game")
		self["key_yellow"] = Button("reset game")
		for x in range(self.maxstones):
			self["stone"+str(x)] = Pixmap()

		self.maxentry = self.maxstones - 1

		self.stonefield = StoneField(self.stonesX, self.stonesY, 3, 0)

		self.onLayoutFinish.append(self.startup)

	def startup(self):
		self.key_green()
		self.Slice = 0
		self.timer = eTimer()
		self.timer.callback.append(self.timerEvent)
		self.timer.start(250)

	def paintFocus(self):
		if self.maxentry < self.focus or self.focus < 0:
			return
		pos = self.focuslist[self.focus]
		self["frame"].moveTo( pos[0], pos[1], 1)
		self["frame"].startMoving()
		self.moveEvent(self.focus)

	def timerEvent(self):
		self.Slice=(self.Slice+1) % self.maxslices
		self.paintEvent()

	def paintEvent(self):
		for x in range(self.maxstones):
			stone = self.stonefield.field[x]
			if stone.marked or stone.changed:
				self.stonefield.field[x].changed = False

				if stone.color:
					if stone.marked:
						tslice = self.Slice
					else:
						tslice = 0

					self["stone" + str(x)].instance.setPixmap(self.maps[stone.color - 1][tslice])
					self["stone" + str(x)].show()

				else:
					self["stone" + str(x)].hide()

	def moveEvent(self, i):
		if self.stonefield.isGameover():
			self.stonefield.unmark()
			self.printMarked(0)
			return
		sy = i / 15
		sx = i - sy * 15
		marked = self.stonefield.mark1(sx, sy)
		if marked >= 0:
			self.printMarked(marked)
			self.Slice = 0

	def pressEvent(self, i):
		sy = i / 15;
		sx = i - sy * 15;
		if self.stonefield.remove(sx, sy):
			marked = self.stonefield.mark1(sx,sy)
			self.printMarked(marked)
			self.printScore()
			self.printColors()
			if self.stonefield.isGameover():
				self.gameover()
			self.paintEvent()

	def gameover(self):
		if self.stonefield.hasBonus():
			txt1 = "You even removed the last stone, great job!\nThis gave you a score of %d in total." % self.stonefield.getScore()
			txt2 = "You won!"
		else:
			txt1 = "There are no more removeable stones.\nYou got a score of %d in total." % self.stonefield.getScore()
			txt2 = "Game over!"

		msg = self.session.open(MessageBox,txt1, MessageBox.TYPE_INFO)
		msg.setTitle(txt2)

	def printColors(self):
		self["lbColors"].setText(str(self.stonefield.getColors()) + " Colors(" + str(self.stonefield.count(1)) + "," +\
		                                                                         str(self.stonefield.count(2)) + "," +\
		                                                                         str(self.stonefield.count(3)) + ")" )

	def printMarked(self, m):
		self["lbMarked"].setText("Marked: " + str(m))

	def printScore(self):
		self["lbScore"].setText("Score: " + str(self.stonefield.getScore()))

	def printBoard(self):
		self["lbBoard"].setText("Board: " + str(self.stonefield.getBoard()))

	def key_left(self):
		if not self.focus - 1 < 0:
			self.focus -= 1
			self.paintFocus()

	def key_right(self):
		if not self.focus + 1 > self.maxentry:
			self.focus += 1
			self.paintFocus()

	def key_up(self):
		if not self.focus - self.stonesX < 0:
			self.focus -= self.stonesX
			self.paintFocus()

	def key_down(self):
		if not self.focus + self.stonesX > self.maxentry:
			self.focus += self.stonesX
			self.paintFocus()

	def key_green(self):
		board = int(time.time())
		while board >= 1000000:
			board -= 1000000

		self.stonefield.newGame(board, 3)

		self.focus = 0
		self.paintFocus()

		self.printBoard()
		self.printScore()
		self.printColors()

	def key_yellow(self):
		self.stonefield.reset()

		self.focus = 0
		self.paintFocus()

		self.printBoard()
		self.printScore()
		self.printColors()

	def key_ok(self):
		self.pressEvent(self.focus)

	def Exit(self):
		self.timer.stop()
		self.close()
