# -*- coding: utf-8 -*-
#===============================================================================
# Vier Gewinnt Plugin by DarkVolli 2011
# ported from neutrino game plugin by fx2
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.
#===============================================================================

VERSION = "0.2r1"

from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Components.Sources.CanvasSource import CanvasSource
from Components.Button import Button
from Components.Label import Label
from Components.ActionMap import ActionMap
from Tools.Directories import resolveFilename, SCOPE_CURRENT_PLUGIN
from enigma import eTimer
import xml.etree.cElementTree
import random

#good old C function :D


def rand():
	return random.randint(0, 32767)


def main(session, **kwargs):
	session.open(vierg)


def Plugins(**kwargs):
	return [PluginDescriptor(name="Vier Gewinnt", description=_("Connect Four Game"), where=[PluginDescriptor.WHERE_PLUGINMENU], icon="vierg.png", fnc=main)]


# mainwindow...
class vierg(Screen):
	def __init__(self, session):
		self.csize = 42
		self.fsize = 50
		self.bsize = 4

		self.cw = 7 * self.fsize + 2 * self.bsize
		self.ch = 7 * self.fsize + 2 * self.bsize

		layout = resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/vierg/layout.png")

		# set skin...
		vierg.skin = """
			<screen position="center,center" size="378,440" title="Vier Gewinnt %s" >
				<widget source="Canvas" render="Canvas" position="10,0" size="358,358" zPosition="1" />
				<ePixmap name="layout" position="0,0" zPosition="2" size="378,440" pixmap="%s" transparent="1" alphatest="on" />
				<widget name="message" position="0,360" size="378,30" zPosition="3" backgroundColor="#062748" valign="center" halign="center" font="Regular;26"/>
				<ePixmap name="red"   position=" 10,390" zPosition="3" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
				<ePixmap name="green" position="228,390" zPosition="3" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
				<widget name="key_red"   position=" 10,390" zPosition="4" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_green" position="228,390" zPosition="4" size="140,40" valign="center" halign="center"  font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			</screen>""" % (VERSION, layout)

		self.skin = vierg.skin
		Screen.__init__(self, session)
		self["Canvas"] = CanvasSource()
		self["message"] = Label(_(" "))
		self["key_red"] = Button(_("quit game"))
		self["key_green"] = Button(_("new game"))

		self["actions"] = ActionMap(["WizardActions", "ColorActions", "SetupActions"],
		{
			"ok": self.ok_pressed,
			"left": self.left_pressed,
			"right": self.right_pressed,
			"red": self.quit,
			"green": self.new_game,
			"cancel": self.quit,
		})

		self.blue = 0x0000ff
		self.red = 0xff0000
		self.bg1 = 0x373737
		self.bg0 = 0x062748

		self.aniTimer = eTimer()
		self.aniTimer.callback.append(self.aniTimerHandler)

		self.onLayoutFinish.append(self.new_game)

	def drawRect(self, x, y, color="bg1"):
		if color == "blue":
			bg = self.blue
		elif color == "red":
			bg = self.red
		elif color == "bg0":
			bg = self.bg0
		else:
			bg = self.bg1
		self["Canvas"].fill(2 * self.bsize + x, 2 * self.bsize + y, self.csize, self.csize, bg)
		self["Canvas"].flush()

	def gameIsOver(self, mask):
		k = self.testGameOver(mask)
		if k == 0:
			return False
		self.aniFall()
		if k == 2: # patt
			self["message"].setText(_("good game!"))
		elif mask == 1:
			self["message"].setText(_("You won!"))
		else:
			self["message"].setText(_("You lose!"))
		self.gameover = True
		return True

	def ok_pressed(self):
		if not self.gameover and not self.locked:
			if self.maze[self.ipos + 35]:
				return

			self.aniList = []
			self.locked = True
			self.fall(self.ipos, "red", 1)
			self.ipos = 3
			if self.gameIsOver(1):
				return

			self.myPlay()
			if self.gameIsOver(2):
				del self.aniList[-1]
				return
			self.aniFall()

	def left_pressed(self):
		if self.ipos > 0 and not self.gameover and not self.locked:
			self.drawRect(self.ipos * self.fsize, 0, "bg0")
			self.ipos -= 1
			self.drawRect(self.ipos * self.fsize, 0, "red")

	def right_pressed(self):
		if self.ipos < 6 and not self.gameover and not self.locked:
			self.drawRect(self.ipos * self.fsize, 0, "bg0")
			self.ipos += 1
			self.drawRect(self.ipos * self.fsize, 0, "red")

	def quit(self):
		self.aniTimer.stop()
		self.close()

	def new_game(self):
		self["message"].setText("")
		self.gameover = False
		self.locked = False

		self.maze = []
		for i in range(42):
			self.maze.append(0)

		self["Canvas"].fill(0, 0, self.cw, self.ch, self.bg0)
		self["Canvas"].fill(0, self.fsize, self.cw, self.ch - self.fsize, self.bg1)
		self["Canvas"].flush()

		self.ipos = 3
		self.drawRect(self.ipos * self.fsize, 0, "red")

	def aniTimerHandler(self):
		self.drawRect(self.aniList[self.aniCnt][0], self.aniList[self.aniCnt][1], self.aniList[self.aniCnt][2])
		if self.aniCnt < len(self.aniList) - 1:
			self.aniCnt += 1
		else:
			self.aniTimer.stop()
			self.locked = False

	def aniFall(self):
		self.aniCnt = 0
		self.aniTimer.start(100)

	def fall(self, x, dr, v):
		for y in range(6):
			if self.maze[(5 - y) * 7 + x]:
				break
			if y:
				self.aniList.append((x * self.fsize, y * self.fsize, "bg1"))
				self.maze[(6 - y) * 7 + x] = 0
			else:
				self.aniList.append((x * self.fsize, y * self.fsize, "bg0"))
			self.maze[(5 - y) * 7 + x] = v
			self.aniList.append((x * self.fsize, y * self.fsize + self.fsize, dr))
		if v == 2:
			self.aniList.append((self.ipos * self.fsize, 0, "red"))

	def cPlay(self, x):
		self.aniList.append((x * self.fsize, 0, "blue"))
		self.fall(x, "blue", 2)

	def vFall(self, x, v):
		idx = x
		for y in range(6):
			if not self.maze[idx]:
				self.maze[idx] = v
				return idx
			idx += 7
		return -1

	def testGameOver(self, mask):
		idx = 0
		for y in range(3):
			for x in range(7):
				if self.maze[idx] & mask: # start-point
					if (x < 4):
						# vertikal nach rechts testen
						if self.maze[idx + 1] & mask and self.maze[idx + 2] & mask and self.maze[idx + 3] & mask:
							return 1 # game over
						# diagonale nach rechts testen
						if self.maze[idx + 8] & mask and self.maze[idx + 16] & mask and self.maze[idx + 24] & mask:
							return 1 # game over
					if (x > 2):
						# diagonale nach links testen
						if self.maze[idx + 6] & mask and self.maze[idx + 12] & mask and self.maze[idx + 18] & mask:
							return 1 # game over
					# nach oben testen
					if self.maze[idx + 7] & mask and self.maze[idx + 14] & mask and self.maze[idx + 21] & mask:
						return 1 # game over
				idx += 1

		# der rest wird nur auf waagerecht untersucht
		for y in range(3, 6):
			#for( x=0; x<7; x++, idx++ )
			for x in range(7):
				if x < 4 and self.maze[idx] & mask: # start-point
					# vertikal nach rechts testen
					if self.maze[idx + 1] & mask and self.maze[idx + 2] & mask and self.maze[idx + 3] & mask:
						return 1 # game over
				idx += 1

		# test auf patt
		idx = 35
		for x in range(7):
			if not self.maze[idx]:
				return 0
			idx += 1
		return 2

	def myPlay(self):
		tst = []
		vidx = []
		max = 0

		for x in range(7):
			tst.append(0)
			vidx.append(0)

		# test: eigener sieg in 1nem zug
		for x in range(7):
			idx = self.vFall(x, 6)
			if idx is not -1:
				if self.testGameOver(2): # great ! - choose it
					self.maze[idx] = 0   # remove virt. chip
					self.cPlay(x)
					return

				k = self.vFall(x, 5) # put playerchip over me
				if k is not -1:
					if self.testGameOver(1): # fault - this field is ugly
						tst[x] -= 50
					else:
						tst[x] += 1
					self.maze[k] = 0 # remove virt. chip
				else:
					tst[x] += 1
				self.maze[idx] = 0 # remove virt. chip
			else:
				tst[x] = -999999 # neg val

		# test: player sieg in 1-2 zuegen
		for x in range(7):
			idx = self.vFall(x, 5)
			if idx is not -1:
				if self.testGameOver(1): # great ! - choose it
					tst[x] += 50
				else:
					for k in range(7):
						if k == x:
							continue
						idx2 = self.vFall(k, 5)
						if idx2 is not -1:
							if self.testGameOver(1): # great ! - choose it
								tst[x] += 10
							self.maze[idx2] = 0 # remove virt. chip
				self.maze[idx] = 0 # remove virt. chip

		# search highest val
		for x in range(7):
			if tst[x] > tst[max]:
				max = x
		idx = 0
		for x in range(7):
			if tst[x] == tst[max] and not self.maze[35 + x]:
				vidx[idx] = x
				idx += 1

		if not idx: # never reached
			return

		if idx > 1:
			for k in range(idx):
				i1 = self.vFall(vidx[k], 5)
				if i1 == -1:
					continue
				for x in range(7):
					i2 = self.vFall(x, 5)
					if i2 == -1:
						continue
					if self.testGameOver(2): # great ! - choose it
						tst[vidx[k]] += 5
					self.maze[i2] = 0 # remove virt. chip
				self.maze[i1] = 0 # remove virt. chip

		# search highest val again
		max = 0
		for x in range(7):
			if tst[x] > tst[max]:
				max = x
		idx = 0
		for x in range(7):
			if tst[x] == tst[max] and not self.maze[35 + x]:
				vidx[idx] = x
				idx += 1

		if not idx: # never reached
			return

		idx = rand() % idx
		self.cPlay(vidx[idx])
