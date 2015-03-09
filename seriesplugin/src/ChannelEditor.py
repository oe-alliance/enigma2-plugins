# -*- coding: utf-8 -*-
from __init__ import _

from Components.ActionMap import ActionMap, HelpableActionMap
#from Components.Label import Label
from Components.MenuList import MenuList
#from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmap, MultiContentEntryPixmapAlphaTest
#from Tools.LoadPixmap import LoadPixmap
#from Components.Pixmap import Pixmap
#from Components.AVSwitch import AVSwitch
#from Screens.InfoBar import MoviePlayer
#from Components.PluginComponent import plugins
from Components.Button import Button
from Screens.Screen import Screen
#from Plugins.Plugin import PluginDescriptor
#from twisted.web.client import getPage
#from twisted.web.client import downloadPage

#from Components.ServicePosition import ServicePositionGauge
#from Tools.NumericalTextInput import NumericalTextInput
from Tools.BoundFunction import boundFunction
#from Components.ConfigList import ConfigList, ConfigListScreen
from Components.config import config

#from Components.ScrollLabel import ScrollLabel
#from Components.FileList import FileList
#from Components.Sources.StaticText import StaticText

from Screens.HelpMenu import HelpableScreen
#from Screens.InputBox import InputBox
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
#from Screens.Standby import TryQuitMainloop
#from Screens.VirtualKeyBoard import VirtualKeyBoard

from enigma import eListboxPythonMultiContent, eListbox, gFont, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, loadPNG, RT_WRAP, RT_VALIGN_CENTER, RT_VALIGN_TOP, RT_VALIGN_BOTTOM
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
import sys, os, base64, re, time, shutil, datetime, codecs, urllib2
from twisted.web import client, error as weberror
from twisted.internet import reactor, defer
from urllib import urlencode
from skin import parseColor

from difflib import SequenceMatcher

#Internal
from Channels import ChannelsBase, buildSTBchannellist, unifyChannel
from Logger import splog


# Constants
PIXMAP_PATH = os.path.join( resolveFilename(SCOPE_PLUGINS), "Extensions/SeriesPlugin/Images/" )

colorRed    = 0xf23d21
colorGreen  = 0x389416
colorBlue   = 0x0064c7
colorYellow = 0xbab329
colorWhite  = 0xffffff


class ChannelEditor(Screen, HelpableScreen, ChannelsBase):
	
	skinfile = os.path.join( resolveFilename(SCOPE_PLUGINS), "Extensions/SeriesPlugin/skinChannelEditor.xml" )
	skin = open(skinfile).read()
	
	def __init__(self, session):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		ChannelsBase.__init__(self)
		
		self.session = session
		
		self.skinName = [ "SeriesPluginChannelEditor" ]
		
		from plugin import NAME, VERSION
		self.setup_title = NAME + " " + _("Channel Editor") + " " + VERSION
		
		# Buttons
		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("OK"))
		self["key_blue"] = Button(_("Remove"))
		self["key_yellow"] = Button(_("Auto match"))
		
		# Define Actions
		self["actions_1"] = HelpableActionMap(self, "SetupActions", {
			"ok"       : (self.keyAdd, _("Show popup to add Stb Channel")),
			"cancel"   : (self.keyCancel, _("Cancel and close")),
			"deleteForward"   : (self.keyResetChannelMapping, _("Reset channels")),
		}, -1)
		self["actions_2"] = HelpableActionMap(self, "DirectionActions", {
			"left"     : (self.keyLeft, _("Previeous page")),
			"right"    : (self.keyRight, _("Next page")),
			"up"       : (self.keyUp, _("One row up")),
			"down"     : (self.keyDown, _("One row down")),
		}, -1)
		self["actions_3"] = HelpableActionMap(self, "ColorActions", {
			"red"      : (self.keyCancel, _("Cancel and close")),
			"green"    : (self.keySave, _("Save and close")),
			"blue"     : (self.keyRemove, _("Remove channel")),
			"yellow"   : (self.tryToMatchChannels, _("Auto match")),
		}, -2) # higher priority
		
		self.helpList[0][2].sort()

		self["helpActions"] = ActionMap(["HelpActions",], {
			"displayHelp"      : self.showHelp
		}, 0)

		self.chooseMenuList = MenuList([], enableWrapAround=True, content=eListboxPythonMultiContent)
		self.chooseMenuList.l.setFont(0, gFont('Regular', 20 ))
		self.chooseMenuList.l.setItemHeight(25)
		self['list'] = self.chooseMenuList
		self['list'].show()

		self.stbChlist = []
		self.webChlist = []
		self.stbToWebChlist = []
		
		self.onLayoutFinish.append(self.readChannels)

	def readChannels(self):
		self.setTitle(_("Load Web-Channels..."))
		
		self.stbToWebChlist = []
		
		if not self.stbChlist:
			self.stbChlist = buildSTBchannellist(config.plugins.seriesplugin.bouquet_main.value)
		
		if not self.webChlist:
			from WebChannels import WebChannels
			WebChannels(self.setWebChannels).request()
		else:
			self.showChannels()

	def setWebChannels(self, data):
		#data.sort()
		temp = [ (x,unifyChannel(x)) for x in data]
		self.webChlist = sorted(temp, key=lambda tup: tup[0])
		self.showChannels()

	def showChannels(self):
		if len(self.stbChlist) != 0:
			for servicename,serviceref,uservicename in self.stbChlist:
				#splog("SPC: servicename", servicename, uservicename)
				
				webSender = self.lookupChannelByReference(serviceref)
				if webSender is not False:
					self.stbToWebChlist.append((servicename, webSender, serviceref, "1"))
					
				else:
					self.stbToWebChlist.append((servicename, "", serviceref, "0"))
		
		if len(self.stbToWebChlist) != 0:
			self.chooseMenuList.setList(map(self.buildList, self.stbToWebChlist))
		else:
			splog("SPC: Error creating webChlist..")
			self.setTitle(_("Error check log file"))
	
	def tryToMatchChannels(self):
		self.setTitle(_("Channel matching..."))
		self.stbToWebChlist = []
		sequenceMatcher = SequenceMatcher(" ".__eq__, "", "")
		
		if len(self.stbChlist) != 0:
			for servicename,serviceref,uservicename in self.stbChlist:
				#splog("SPC: servicename", servicename, uservicename)
				
				webSender = self.lookupChannelByReference(serviceref)
				if webSender is not False:
					self.stbToWebChlist.append((servicename, webSender, serviceref, "1"))
					
				else:
					if len(self.webChlist) != 0:
						match = ""
						ratio = 0
						for webSender, uwebSender in self.webChlist:
							#splog("SPC: webSender", webSender, uwebSender)
							if uwebSender in uservicename or uservicename in uwebSender:
								
								sequenceMatcher.set_seqs(uservicename, uwebSender)
								newratio = sequenceMatcher.ratio()
								if newratio > ratio:
									splog("SPC: possible match", servicename, uservicename, webSender, uwebSender, ratio)
									ratio = newratio
									match = webSender
						
						if ratio > 0:
							splog("SPC: match", servicename, uservicename, match, ratio)
							self.stbToWebChlist.append((servicename, match, serviceref, "1"))
							self.addChannel(serviceref, servicename, match)
						
						else:
							self.stbToWebChlist.append((servicename, "", serviceref, "0"))
							
					else:
						self.stbToWebChlist.append((servicename, "", serviceref, "0"))
						
		if len(self.stbToWebChlist) != 0:
			self.chooseMenuList.setList(map(self.buildList, self.stbToWebChlist))
		else:
			splog("SPC: Error creating webChlist..")
			self.setTitle(_("Error check log file"))
		
	def buildList(self, entry):
		self.setTitle(_("STB-Channels / Web-Channel"))
		
		(stbSender, webSender, serviceref, status) = entry
		if int(status) == 0:		
			imageStatus = path = os.path.join(PIXMAP_PATH, "minus.png")
		else:
			imageStatus = path = os.path.join(PIXMAP_PATH, "plus.png")
			
		return [entry,
			(eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, 10, 8, 16, 16, loadPNG(imageStatus)),
			(eListboxPythonMultiContent.TYPE_TEXT, 35, 3, 300, 26, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, stbSender),
			(eListboxPythonMultiContent.TYPE_TEXT, 350, 3, 250, 26, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, webSender),
			(eListboxPythonMultiContent.TYPE_TEXT, 600, 3, 250, 26, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, "", colorYellow)
			]

	def getIndexOfWebSender(self, webSender):
		for pos,webCh in enumerate(self.webChlist):
			if(webCh[0] == webSender):
				return pos
		return 0
	
	def keyAdd(self):
		check = self['list'].getCurrent()
		if check == None:
			splog("SPC: list empty")
			return
		else:
			idx = 0
			(servicename, webSender, serviceref, state) = self['list'].getCurrent()[0]
			idx = 0
			if webSender:
				idx = self.getIndexOfWebSender(self.webChlist)
			splog("SPC: keyAdd webSender", webSender, idx)
			self.session.openWithCallback( boundFunction(self.addConfirm, servicename, serviceref, webSender), ChoiceBox,_("Add Web Channel"), self.webChlist, None, idx)
	
	def getIndexOfServiceref(self, serviceref):
		for pos,stbWebChl in enumerate(self.stbToWebChlist):
			if(stbWebChl[2] == serviceref):
				return pos
		return False
	
	def addConfirm(self, servicename, serviceref, webSender, result):
		if not result:
			return
		remote = result[0]
		if webSender and remote == webSender:
			splog("SPC: addConfirm skip already set", servicename, serviceref, remote, webSender)
		elif servicename and serviceref and remote and not webSender:
			idx = self.getIndexOfServiceref(serviceref)
			splog("SPC: addConfirm", servicename, serviceref, remote, idx)
			if idx is not False:
				self.setTitle(_("Channel '- %(servicename)s - %(remote)s -' added.") % {'servicename': servicename, 'remote':remote } )
				self.addChannel(serviceref, servicename, remote)
				self.stbToWebChlist[idx] = (servicename, remote, serviceref, "1")
				self.chooseMenuList.setList(map(self.buildList, self.stbToWebChlist))
		elif servicename and serviceref and remote and webSender:
			splog("SPC: add or replace", servicename, serviceref, remote, webSender)
			self.session.openWithCallback( boundFunction(self.addOrReplace, servicename, serviceref, webSender, remote), MessageBox,_("Add channel (Yes) or replace it (No)"), MessageBox.TYPE_YESNO, default = False)

	def addOrReplace(self, servicename, serviceref, webSender, remote, result):
		idx = self.getIndexOfServiceref(serviceref)
		splog("SPC: addOrReplace", servicename, serviceref, remote, webSender, idx)
		if idx is False:
			return
		
		if result:
			splog("SPC: add", servicename, serviceref, remote, webSender)
			self.setTitle(_("Channel '- %(servicename)s - %(remote)s -' added.") % {'servicename': servicename, 'remote':remote } )
			self.addChannel(serviceref, servicename, remote)
			self.stbToWebChlist[idx] = (servicename, webSender+" / "+remote, serviceref, "1")
			
		else:
			splog("SPC: replace", servicename, serviceref, remote, webSender)
			self.setTitle(_("Channel '- %(servicename)s - %(remote)s -' replaced.") % {'servicename': servicename, 'remote':remote } )
			self.replaceChannel(serviceref, servicename, remote)
			self.stbToWebChlist[idx] = (servicename, remote, serviceref, "1")
			
		self.chooseMenuList.setList(map(self.buildList, self.stbToWebChlist))

	def keyRemove(self):
		check = self['list'].getCurrent()
		if check == None:
			splog("SPC: keyRemove list empty")
			return
		else:
			(servicename, webSender, serviceref, state) = self['list'].getCurrent()[0]
			splog("SPC: keyRemove", servicename, webSender, serviceref, state)
			if serviceref:
				#TODO handle multiple links/alternatives - show a choicebox
				self.session.openWithCallback( boundFunction(self.removeConfirm, servicename, serviceref), MessageBox, _("Remove '%s'?") % servicename, MessageBox.TYPE_YESNO, default = False)

	def removeConfirm(self, servicename, serviceref, answer):
		if not answer:
			return
		if serviceref:
			idx = self.getIndexOfServiceref(serviceref)
			if idx is not False:
				splog("SPC: removeConfirm", servicename, serviceref, idx)
				self.setTitle(_("Channel '- %s -' removed.") % servicename)
				self.removeChannel(serviceref)
				self.stbToWebChlist[idx] = (servicename, "", serviceref, "0")
				self.chooseMenuList.setList(map(self.buildList, self.stbToWebChlist))

	def keyResetChannelMapping(self):
		self.session.openWithCallback(self.channelReset, MessageBox, _("Reset channel list?"), MessageBox.TYPE_YESNO)

	def channelReset(self, answer):
		if answer:
			splog("SPC: channel-list reset...")
			self.resetChannels()
			self.stbChlist = []
			self.webChlist = []
			self.stbToWebChlist = []
			self.readChannels()

	def keyLeft(self):
		self['list'].pageUp()

	def keyRight(self):
		self['list'].pageDown()

	def keyDown(self):
		self['list'].down()

	def keyUp(self):
		self['list'].up()
	
	def keySave(self):
		self.close(ChannelsBase.channels_changed)

	def keyCancel(self):
		self.close(False)

	def hideHelpWindow(self):
		current = self["config"].getCurrent()
		if current and hasattr(current[1], "help_window"):
			help_window = current[1].help_window
			if help_window:
				help_window.hide()
