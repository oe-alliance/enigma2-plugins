# -*- coding: utf-8 -*-

# for localized messages
from __future__ import print_function
from . import _x

import os
from Components.ConfigList import ConfigListScreen
from Screens.Screen import Screen
from Components.Label import Label
from Components.ActionMap import HelpableActionMap, ActionMap, NumberActionMap

from Components.Input import Input
from Screens.InputBox import InputBox
from Screens.MessageBox import MessageBox

SerienFilmVersion = "v1.1"


class SerienFilmCfg(Screen):
	skin = """
		<screen position="130,150" size="500,200" title="SerienFilm setup" >
			<widget name="myLabel" position="10,20" size="480,160" font="Regular;20"/>
		</screen>"""

	def __init__(self, session, args=None):
		print("[SF-Plugin] SerienFilmCfg init")
		self.session = session
		Screen.__init__(self, session)
		self["myLabel"] = Label(_x("This plugin is configured by the MENU key in the movielist\n\nApplication details provides the HELP key in the movielist"))
		self["myActionMap"] = ActionMap(["SetupActions"],
		{
			"ok": self.close,
			"cancel": self.close
		}, -1)


class EpiSepCfg(Screen):

	def __init__(self, session, separator=None):

		skincontent = """
			<widget name="sfLabel" position="10,20" size="590,220" font="Regular;20"/>
			<widget name="sfRedBtn" position="10,250" size="140,40" backgroundColor="red" valign="center" halign="center" zPosition="2"  foregroundColor="white" font="Regular;20"/>
			<widget name="sfGreenBtn" position="160,250" size="140,40" backgroundColor="green" valign="center" halign="center" zPosition="2"  foregroundColor="white" font="Regular;20"/>
			<widget name="sfYellowBtn" position="310,250" size="140,40" backgroundColor="yellow" valign="center" halign="center" zPosition="2"  foregroundColor="white" font="Regular;20"/>
			<widget name="sfBlueBtn" position="460,250" size="140,40" backgroundColor="blue" valign="center" halign="center" zPosition="2"  foregroundColor="white" font="Regular;20"/>
		</screen>"""

		self.skin = "<screen position=\"130,150\" size=\"610,300\" title=\"" + _x("Configuration of the title:episode separator") + "\" >" + skincontent

		self.session = session
		self.defaultsep = _x(": ")
		self.newsep = self.currentsep = separator
		Screen.__init__(self, session)
		self.skinName = "skin"

		intro = _x("Usually the episode of a series is tansmitted separate of the title in the description field\nIn a few series however it is appended to the title behind a colon\ne.g. Tatort: Der Fluch der Mumie\n\nA commen part of the title up to this title:episode separator shared by several movies creates a series")
		self.firstlevel = [intro, _("Exit"), _x("Set default"), _x("Change"), _x("Disable ")]
		if not separator:
			self.firstlevel[4] = _x("Enable ")

		self.secondformat = _x("The current title:episode separator is \"%s\" (%d characters)\nTo change it: first Set size and then Edit")

		self.secondlevel = ["", _("Cancel"), _("Save"), _("Edit"), _x("Set size")]
		self.secondlevel[0] = self.secondformat % (self.currentsep, len(self.currentsep))

		self.level = 1

		self["sfLabel"] = Label()
		self["sfRedBtn"] = Label()
		self["sfGreenBtn"] = Label()
		self["sfYellowBtn"] = Label()
		self["sfBlueBtn"] = Label()
		self["sfActionMap"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"ok": self.gotOk,
			"cancel": self.gotCancel,
			"red": self.gotCancel,
			"green": self.gotGreen,
			"yellow": self.gotEdit,
			"blue": self.gotBlue
		}, -1)
		self.onShown.append(self.sfsetLabel)

	def gotCancel(self):
		if self.newsep == self.currentsep:
			self.exitConfirmed(True)
		else:
			self.session.openWithCallback(self.exitConfirmed, MessageBox, _("Really close without saving settings?"))

	def exitConfirmed(self, confirmed):
		if confirmed:
			if self.level == 1:
				self.close(self.currentsep)
			else:
				self.newsep = self.currentsep  # discard changes
				self.level = 1
				self.secondlevel[0] = self.secondformat % (self.currentsep, len(self.currentsep))
				self.sfsetLabel()

	def gotOk(self):
		if self.level == 1:
			self.close(self.newsep)
		else:
			self.gotGreen()  # save and back to level 1

	def gotEdit(self):
		if self.level == 1:
			self.level = 2
			self.sfsetLabel()
		else:
			self.session.openWithCallback(self.setSeparator,		# edit serarator
				InputBox,
				windowTitle=_x("Edit title:episode separator"),
				title=_x("Key 0 provides special chracters, key 1 blank"),
				text=self.newsep,
				maxSize=True,
				type=Input.TEXT)

	def gotGreen(self):
		if self.level == 1:
			self.currentsep = self.newsep = self.defaultsep  # set default
		else:
			self.currentsep = self.newsep  # save
			self.level = 1		# and back to level 1
			self.sfsetLabel()

	def gotBlue(self):
		if self.level == 1:
			if self.newsep:
				self.firstlevel[4] = _x("Enable ")
				self.currentsep = ""
			else:
				self.firstlevel[4] = _x("Disable ")
				self.currentsep = self.defaultsep  # set default
			self.setSeparator(self.currentsep)
		else:
			self.session.openWithCallback(self.setSeparatorSize,  # set size
				InputBox,
				title=_x("Number of characters"),
				windowTitle=_x("Length of the title:episode separator"),
				text=str(len(self.newsep)),
				type=Input.NUMBER)

	def setSeparatorSize(self, length):
		len = int(length)
		self.setSeparator(self.newsep[:len].ljust(len))

	def setSeparator(self, sep):
		if sep == None:
			sep = ""
#		print "[SF-Plugin] EpiSepCfg.setSeparator >%s< to >%s<" % (self.newsep, sep)
		self.newsep = sep
		self.secondlevel[0] = self.secondformat % (sep, len(sep))
		self.sfsetLabel()

	def sfsetLabel(self):
		if self.level == 1:
			labels = self.firstlevel
		else:
			labels = self.secondlevel
		self["sfLabel"].setText(labels[0])
		self["sfRedBtn"].setText(labels[1])
		self["sfGreenBtn"].setText(labels[2])
		self["sfYellowBtn"].setText(labels[3])
		self["sfBlueBtn"].setText(labels[4])
