# -*- coding: utf-8 -*-
#===============================================================================
# dirSelectDlg 0.1 by DarkVolli 2009
# extensions by Dre 2011
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.
#===============================================================================

# for localized messages
#from __init__ import _

from __future__ import print_function
from Screens.Screen import Screen

from Components.ActionMap import ActionMap
from Components.Pixmap import Pixmap
from Components.Label import Label
from Components.Button import Button
from Components.FileList import FileList


class dirSelectDlg(Screen): # 90,140
	skin = """
		<screen name="dirSelectDlg" position="center,center" size="560,360">
			<widget name="filelist" position="10,10" size="540,210" scrollbarMode="showOnDemand" />
			<widget name="ButtonGreentext" position="70,270" size="460,25" halign="left" zPosition="10" font="Regular;21" transparent="1" />
			<widget name="ButtonGreen" pixmap="skin_default/buttons/button_green.png" position="30,270" zPosition="10" size="35,25" transparent="1" alphatest="on" />
			<widget name="ButtonRedtext" position="70,300" size="460,25" halign="left" zPosition="10" font="Regular;21" transparent="1" />
			<widget name="ButtonRed" pixmap="skin_default/buttons/button_red.png" position="30,300" zPosition="10" size="35,25" transparent="1" alphatest="on" />
			<widget name="ButtonOKtext" position="70,330" size="460,25" halign="left" zPosition="10" font="Regular;21" transparent="1" />
			<widget name="ButtonOK" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/fstabEditor/ok.png" position="30,330" zPosition="10" size="35,25" transparent="1" alphatest="on" />
		</screen>"""

	def __init__(self, session, currDir, showFilesBoolean):
		self.skin = dirSelectDlg.skin
		Screen.__init__(self, session)
		self.session = session
		self.showFilesBoolean = showFilesBoolean

		self["ButtonGreen"] = Pixmap()
		self["ButtonGreentext"] = Button()
		self["ButtonRed"] = Pixmap()
		self["ButtonRedtext"] = Label(_("Close"))
		self["ButtonOK"] = Pixmap()
		self["ButtonOKtext"] = Label(_("Enter directory"))
		self["filelist"] = FileList(currDir, showDirectories=True, showFiles=showFilesBoolean, showMountpoints=True, useServiceRef=False)

		self["actions"] = ActionMap(["WizardActions", "DirectionActions", "ColorActions"],
		{
			"ok": self.ok,
			"back": self.cancel,
			"left": self.left,
			"right": self.right,
			"up": self.up,
			"down": self.down,
			"green": self.green,
			"red": self.red
		}, -1)

		self.onLayoutFinish.append(self.setStartDir)

	def setStartDir(self):
		if self["filelist"].canDescent():
			self["filelist"].descent()
		self.CurrentDirectory = self["filelist"].getCurrentDirectory()
		self.instance.setTitle(self.CurrentDirectory)
		self.setPathName()

	def updatePathName(self):
		print(self["filelist"].getFilename())
		try:
			len(self["filelist"].getFilename())
		except TypeError:
			pass
		else:
			if len(self["filelist"].getFilename()) > len(self.CurrentDirectory):
				self.setPathName()
			elif self.showFilesBoolean:
				self.setPathName()
			else:
				self["ButtonGreentext"].hide()
				self["ButtonGreen"].hide()
		self.instance.setTitle(self.CurrentDirectory)

	def setPathName(self):
		if self.showFilesBoolean and self["filelist"].canDescent() == False:
			self.epath = self.CurrentDirectory + self["filelist"].getFilename()
		else:
			self.epath = self["filelist"].getFilename()
		print(self.epath)
		if len(self.epath) > 1 and self.epath.endswith('/'):
			self.epath = self.epath[:-1]
		self["ButtonGreentext"].setText(_("select:") + " " + self.epath)
		self["ButtonGreentext"].show()
		self["ButtonGreen"].show()

	def ok(self):
		if self["filelist"].canDescent():
			self["filelist"].descent()
			if len(self["filelist"].getFilename()) > len(self["filelist"].getCurrentDirectory()):
				self.setPathName()
			else:
				self["ButtonGreentext"].hide()
				self["ButtonGreen"].hide()
			self.CurrentDirectory = self["filelist"].getCurrentDirectory()
			self.instance.setTitle(self.CurrentDirectory)

	def up(self):
		self["filelist"].up()
		self.updatePathName()

	def down(self):
		self["filelist"].down()
		self.updatePathName()

	def left(self):
		self["filelist"].pageUp()
		self.updatePathName()

	def right(self):
		self["filelist"].pageDown()
		self.updatePathName()

	def cancel(self):
		self.close(False)

	def red(self):
		self.close(False)

	def green(self):
		self.close(self.epath)
