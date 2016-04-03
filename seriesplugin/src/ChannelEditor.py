# -*- coding: utf-8 -*-
from __init__ import _

import sys, os, base64, re, time, shutil, datetime, codecs, urllib2

from Components.ActionMap import ActionMap, HelpableActionMap
from Components.MenuList import MenuList
from Components.Button import Button
from Screens.Screen import Screen

from Tools.BoundFunction import boundFunction
from Components.config import config

from Screens.HelpMenu import HelpableScreen
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox

from enigma import eListboxPythonMultiContent, eListbox, gFont, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, loadPNG, RT_WRAP, RT_VALIGN_CENTER, RT_VALIGN_TOP, RT_VALIGN_BOTTOM
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_CURRENT_PLUGIN
from twisted.web import client, error as weberror
from twisted.internet import reactor, defer
from urllib import urlencode
from skin import parseColor, parseFont, parseSize

try:
	from skin import TemplatedListFonts
except:
	TemplatedListFonts = None

from difflib import SequenceMatcher

#Internal
from Channels import ChannelsBase, buildSTBchannellist, unifyChannel, getTVBouquets, lookupChannelByReference
from Logger import log
from WebChannels import WebChannels

# Constants
PIXMAP_PATH = resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/SeriesPlugin/Images/" )

colorRed    = 0xf23d21
colorGreen  = 0x389416
colorBlue   = 0x0064c7
colorYellow = 0xbab329
colorWhite  = 0xffffff


class MatchList(MenuList): 
	"""Defines a simple Component to show Timer name""" 

	def __init__(self): 
		MenuList.__init__(self, [], enableWrapAround=True, content=eListboxPythonMultiContent) 

		self.listFont = None
		self.itemHeight = 30
		self.iconPosX = 8
		self.iconPosY = 8
		self.iconSize = 16
		self.colWidthStb = 300
		self.colWidthWeb = 250
		self.margin = 5
		
		self.l.setBuildFunc(self.buildListboxEntry) 
		
		global TemplatedListFonts
		if TemplatedListFonts is not None:
			tlf = TemplatedListFonts()
			self.l.setFont(0, gFont(tlf.face(tlf.MEDIUM), tlf.size(tlf.MEDIUM)))
		else:
			self.l.setFont(0, gFont('Regular', 20 ))

	def applySkin(self, desktop, parent): 
		# This is a very bad way to get the skin attributes
		# This function is called for every skin element, we should parse the attributes depending on the element name
		attribs = [ ] 
		if self.skinAttributes is not None:
			for (attrib, value) in self.skinAttributes:
				if attrib == "font":
					self.listFont = parseFont(value, ((1,1),(1,1)))
					self.l.setFont(0, self.listFont)
				elif attrib == "itemHeight":
					self.itemHeight = int(value)
					self.l.setItemHeight(self.itemHeight)
				elif attrib == "iconPosX":
					self.iconPosX = int(value)
				elif attrib == "iconPosY":
					self.iconPosY = int(value)
				elif attrib == "iconSize":
					self.iconSize = int(value)
				elif attrib == "colWidthStb":
					self.colWidthStb = int(value)
				elif attrib == "colWidthWeb":
					self.colWidthWeb = int(value)
				elif attrib == "margin":
					self.margin = int(value)
				else:
					attribs.append((attrib, value))
		self.skinAttributes = attribs
		return MenuList.applySkin(self, desktop, parent) 

	def buildListboxEntry(self, stbSender, webSender, serviceref, status):
		
		size = self.l.getItemSize() 
		
		if int(status) == 0:		
			imageStatus = path = os.path.join(PIXMAP_PATH, "minus.png")
		else:
			imageStatus = path = os.path.join(PIXMAP_PATH, "plus.png")
		
		l = [(stbSender, webSender, serviceref, status),]
		
		pos = self.margin + self.iconPosX
		l.append( (eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, pos, self.iconPosY, self.iconSize,     self.iconSize,  loadPNG(imageStatus)) )
		
		pos += self.iconSize + self.margin
		l.append( (eListboxPythonMultiContent.TYPE_TEXT,             pos, 0,             self.colWidthStb,  self.itemHeight, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, stbSender) )
		
		pos += self.colWidthStb + self.margin
		l.append( (eListboxPythonMultiContent.TYPE_TEXT,             pos, 0,             self.colWidthWeb,  self.itemHeight, 0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, webSender) )
		
		pos += self.colWidthWeb + self.margin
		l.append( (eListboxPythonMultiContent.TYPE_TEXT,             pos, 0,             size.width()-pos, self.itemHeight,  0, RT_HALIGN_LEFT | RT_VALIGN_CENTER, "", colorYellow) )
		
		return l


class ChannelEditor(Screen, HelpableScreen, ChannelsBase, WebChannels):
	
	skinfile = os.path.join( resolveFilename(SCOPE_PLUGINS), "Extensions/SeriesPlugin/Skins/ChannelEditor.xml" )
	skin = open(skinfile).read()
	
	def __init__(self, session):
		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		ChannelsBase.__init__(self)
		WebChannels.__init__(self)
		
		self.session = session
		
		self.skinName = [ "SeriesPluginChannelEditor" ]
		
		log.debug("ChannelEditor")
		
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
		self["actions_3"] = HelpableActionMap(self, "ChannelSelectBaseActions", {
			"nextBouquet":	(self.nextBouquet, _("Next bouquet")),
			"prevBouquet":	(self.prevBouquet, _("Previous bouquet")),
		}, -1)
		self["actions_4"] = HelpableActionMap(self, "ColorActions", {
			"red"      : (self.keyCancel, _("Cancel and close")),
			"green"    : (self.keySave, _("Save and close")),
			"blue"     : (self.keyRemove, _("Remove channel")),
			"yellow"   : (self.tryToMatchChannels, _("Auto match")),
		}, -2) # higher priority
		
		self.helpList[0][2].sort()

		self["helpActions"] = ActionMap(["HelpActions",], {
			"displayHelp"      : self.showHelp
		}, 0)

		self['list'] = MatchList()
		self['list'].show()

		self.stbChlist = []
		self.webChlist = []
		self.stbToWebChlist = []
		
		self.bouquet = None
		
		self.onLayoutFinish.append(self.readChannels)
		self.onShown.append(self.showMessage)

	def showMessage(self):
		if self.showMessage in self.onShown:
			self.onShown.remove(self.showMessage)
			self.session.open( MessageBox, _("If You are using SD and HD channels in parallel, You have to match both channels separately!"), MessageBox.TYPE_INFO )

	def readChannels(self, bouquet=None):
		self.stbToWebChlist = []
		
		if bouquet is None:
			self.bouquet = config.plugins.seriesplugin.bouquet_main.value
			self.stbChlist = []
		elif bouquet != self.bouquet:
			self.bouquet = bouquet
			self.stbChlist = []
		
		if not self.stbChlist:
			self.loadStbChannels()
		
		if not self.webChlist:
			self.loadWebChannels()
		
		self.showChannels()
	
	def loadStbChannels(self):
		self.setTitle(_("Load STB channels for bouquet") + " " + self.bouquet)
		log.debug("Load STB")
		self.stbChlist = buildSTBchannellist(self.bouquet)
	
	def loadWebChannels(self):
		self.setTitle(_("Load Web channels for bouquet") + " " + self.bouquet)
		log.debug("Load Web channels")
		data = self.getWebChannels()
		if data:
			temp = [ (x,unifyChannel(x)) for x in data]
		else:
			self.setTitle(_("Problem during loading Webchannels"))
			temp = []
		self.webChlist = sorted(temp, key=lambda tup: tup[0])
	
	def getChannelByRef(ref):
		if self.stbChlist:
			for servicename,serviceref,uservicename in self.stbChlist:
				if serviceref == ref:
					return servicename
		return ""
	
	def showChannels(self):
		self.setTitle(_("STB- / Web-Channel for bouquet:") + " " + self.bouquet )
		if len(self.stbChlist) != 0:
			for servicename,serviceref,uservicename in self.stbChlist:
				#log.debug("servicename", servicename, uservicename)
				
				webSender = lookupChannelByReference(serviceref)
				if webSender is not False:
					self.stbToWebChlist.append((servicename, ' / '.join(webSender), serviceref, "1"))
					
				else:
					self.stbToWebChlist.append((servicename, "", serviceref, "0"))
		
		if len(self.stbToWebChlist) != 0:
			self['list'].setList( self.stbToWebChlist )
		else:
			log.debug("Error creating webChlist..")
			self.setTitle(_("Error check log file"))
	
	def tryToMatchChannels(self):
		self.setTitle(_("Channel matching..."))
		self.stbToWebChlist = []
		sequenceMatcher = SequenceMatcher(" ".__eq__, "", "")
		
		if len(self.stbChlist) != 0:
			for servicename,serviceref,uservicename in self.stbChlist:
				#log.debug("servicename", servicename, uservicename)
				
				webSender = lookupChannelByReference(serviceref)
				if webSender is not False:
					self.stbToWebChlist.append((servicename, ' / '.join(webSender), serviceref, "1"))
					
				else:
					if len(self.webChlist) != 0:
						match = ""
						ratio = 0
						for webSender, uwebSender in self.webChlist:
							#log.debug("webSender", webSender, uwebSender)
							if uwebSender in uservicename or uservicename in uwebSender:
								
								sequenceMatcher.set_seqs(uservicename, uwebSender)
								newratio = sequenceMatcher.ratio()
								if newratio > ratio:
									log.debug("possible match", servicename, uservicename, webSender, uwebSender, ratio)
									ratio = newratio
									match = webSender
						
						if ratio > 0:
							log.debug("match", servicename, uservicename, match, ratio)
							self.stbToWebChlist.append((servicename, match, serviceref, "1"))
							self.addChannel(serviceref, servicename, match)
						
						else:
							self.stbToWebChlist.append((servicename, "", serviceref, "0"))
							
					else:
						self.stbToWebChlist.append((servicename, "", serviceref, "0"))
						
		if len(self.stbToWebChlist) != 0:
			self['list'].setList( self.stbToWebChlist )
		else:
			log.debug("Error creating webChlist..")
			self.setTitle(_("Error check log file"))

	def getIndexOfWebSender(self, webSender):
		for pos,webCh in enumerate(self.webChlist):
			if(webCh[0] == webSender):
				return pos
		return 0
	
	def keyAdd(self):
		check = self['list'].getCurrent()
		if check == None:
			log.debug("list empty")
			return
		else:
			idx = 0
			servicename, webSender, serviceref, state = check
			idx = 0
			if webSender:
				idx = self.getIndexOfWebSender(self.webChlist)
			log.debug("keyAdd webSender", webSender, idx)
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
			log.debug("addConfirm skip already set", servicename, serviceref, remote, webSender)
		elif servicename and serviceref and remote and not webSender:
			idx = self.getIndexOfServiceref(serviceref)
			log.debug("addConfirm", servicename, serviceref, remote, idx)
			if idx is not False:
				self.setTitle(_("Channel '- %(servicename)s - %(remote)s -' added.") % {'servicename': servicename, 'remote':remote } )
				self.addChannel(serviceref, servicename, remote)
				self.stbToWebChlist[idx] = (servicename, remote, serviceref, "1")
				self['list'].setList( self.stbToWebChlist )
		elif servicename and serviceref and remote and webSender:
			log.debug("add or replace", servicename, serviceref, remote, webSender)
			self.session.openWithCallback( boundFunction(self.addOrReplace, servicename, serviceref, webSender, remote), MessageBox,_("Add channel (Yes) or replace it (No)"), MessageBox.TYPE_YESNO, default = False)

	def addOrReplace(self, servicename, serviceref, webSender, remote, result):
		idx = self.getIndexOfServiceref(serviceref)
		log.debug("addOrReplace", servicename, serviceref, remote, webSender, idx)
		if idx is False:
			return
		
		if result:
			log.debug("add", servicename, serviceref, remote, webSender)
			self.setTitle(_("Channel '- %(servicename)s - %(remote)s -' added.") % {'servicename': servicename, 'remote':remote } )
			self.addChannel(serviceref, servicename, remote)
			self.stbToWebChlist[idx] = (servicename, webSender+" / "+remote, serviceref, "1")
			
		else:
			log.debug("replace", servicename, serviceref, remote, webSender)
			self.setTitle(_("Channel '- %(servicename)s - %(remote)s -' replaced.") % {'servicename': servicename, 'remote':remote } )
			self.replaceChannel(serviceref, servicename, remote)
			self.stbToWebChlist[idx] = (servicename, remote, serviceref, "1")
			
		self['list'].setList( self.stbToWebChlist )

	def keyRemove(self):
		check = self['list'].getCurrent()
		if check == None:
			log.debug("keyRemove list empty")
			return
		else:
			servicename, webSender, serviceref, state = check
			log.debug("keyRemove", servicename, webSender, serviceref, state)
			if serviceref:
				#TODO handle multiple links/alternatives - show a choicebox
				self.session.openWithCallback( boundFunction(self.removeConfirm, servicename, serviceref), MessageBox, _("Remove '%s'?") % servicename, MessageBox.TYPE_YESNO, default = False)

	def removeConfirm(self, servicename, serviceref, answer):
		if not answer:
			return
		if serviceref:
			idx = self.getIndexOfServiceref(serviceref)
			if idx is not False:
				log.debug("removeConfirm", servicename, serviceref, idx)
				self.setTitle(_("Channel '- %s -' removed.") % servicename)
				self.removeChannel(serviceref)
				self.stbToWebChlist[idx] = (servicename, "", serviceref, "0")
				self['list'].setList( self.stbToWebChlist )

	def keyResetChannelMapping(self):
		self.session.openWithCallback(self.channelReset, MessageBox, _("Reset channel list?"), MessageBox.TYPE_YESNO)

	def channelReset(self, answer):
		if answer:
			log.debug("channel-list reset...")
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
	
	def nextBouquet(self):
		tvbouquets = getTVBouquets()
		next = tvbouquets[0][1]
		for tvbouquet in reversed(tvbouquets):
			if tvbouquet[1] == self.bouquet:
				break
			next = tvbouquet[1]
		self.readChannels(next)
	
	def prevBouquet(self):
		tvbouquets = getTVBouquets()
		prev = tvbouquets[-1][1]
		for tvbouquet in tvbouquets:
			if tvbouquet[1] == self.bouquet:
				break
			prev = tvbouquet[1]
		self.readChannels(prev)
	
	def keySave(self):
		self.close(ChannelsBase.channels_changed)

	def keyCancel(self):
		self.close(False)
