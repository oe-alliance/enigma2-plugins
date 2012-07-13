#
# InternetRadio E2
#
# Coded by Dr.Best (c) 2012
# Support: www.dreambox-tools.info
# E-Mail: dr.best@dreambox-tools.info
#
# This plugin is open source but it is NOT free software.
#
# This plugin may only be distributed to and executed on hardware which
# is licensed by Dream Multimedia GmbH.
# In other words:
# It's NOT allowed to distribute any parts of this plugin or its source code in ANY way
# to hardware which is NOT licensed by Dream Multimedia GmbH.
# It's NOT allowed to execute this plugin and its source code or even parts of it in ANY way
# on hardware which is NOT licensed by Dream Multimedia GmbH.
#
# If you want to use or modify the code or parts of it,
# you have to keep MY license and inform me about the modifications by mail.
#

from Screens.InfoBarGenerics import NumberZap
from Components.ActionMap import ActionMap, NumberActionMap
from enigma import eServiceCenter, getBestPlayableServiceReference, eServiceReference, getDesktop, eEPGCache
from Components.VideoWindow import VideoWindow
from ServiceReference import ServiceReference
from Screens.EpgSelection import EPGSelection
from Screens.EventView import  EventViewEPGSelect
from Components.config import config

# PiPServiceRelation installed?
try:
	from Plugins.SystemPlugins.PiPServiceRelation.plugin import getRelationDict, CONFIG_FILE
	plugin_PiPServiceRelation_installed = True
except:
	plugin_PiPServiceRelation_installed = False


class InternetRadioPiPTVPlayer(object):
	def __init__(self, session, currService, closePlayerCallBack):
		self.session = session
		self["video"] = VideoWindow(fb_width = getDesktop(0).size().width(), fb_height = getDesktop(0).size().height())
		self["numberActions"] = NumberActionMap(["NumberActions"],
		{
			"1": self.keyNumberGlobal,
			"2": self.keyNumberGlobal,
			"3": self.keyNumberGlobal,
			"4": self.keyNumberGlobal,
			"5": self.keyNumberGlobal,
			"6": self.keyNumberGlobal,
			"7": self.keyNumberGlobal,
			"8": self.keyNumberGlobal,
			"9": self.keyNumberGlobal,
		}, -1)
		self["numberActions"].setEnabled(False)
		self["zapActions"] = ActionMap(["OkCancelActions", "DirectionActions", "ChannelSelectBaseActions", "ChannelSelectEPGActions"], 
		{
			"cancel": self.disablePiPPlayer,
			"ok": self.disablePiPPlayer,
			"right": self.nextService,
			"left": self.prevService,
			"nextBouquet": self.nextBouquet,
			"prevBouquet": self.prevBouquet,
			"showEPGList": self.openEventView,

		}, -1)
		self["zapActions"].setEnabled(False)
		self.currService = currService
		from Screens.InfoBar import InfoBar # late binding
		self.servicelist = InfoBar.instance.servicelist
		self.closePlayerCallBack = closePlayerCallBack
		self.epgcache = eEPGCache.getInstance()

		# if PiPServiceRelation is installed, get relation dict
		if plugin_PiPServiceRelation_installed:
			self.pipServiceRelation = getRelationDict()
		else:
			self.pipServiceRelation = {}

	def setPiPTVPlayerEnabled(self, value):
		self["numberActions"].setEnabled(value)
		self["zapActions"].setEnabled(value)
		if value:
			self.playService(self.currService)
#			self["video"].instance.show()

		else:
			self.pipservice = None
#			self["video"].instance.hide()

	def disablePiPPlayer(self):
		self.setPiPTVPlayerEnabled(False)
		if self.closePlayerCallBack is not None:
			self.closePlayerCallBack(False) # emit

	def keyNumberGlobal(self, number):
		self.session.openWithCallback(self.numberEntered, NumberZap, number)

	def numberEntered(self, retval):
		if retval > 0:
			self.zapToNumber(retval)

	def searchNumberHelper(self, serviceHandler, num, bouquet):
		servicelist = serviceHandler.list(bouquet)
		if not servicelist is None:
			while num:
				serviceIterator = servicelist.getNext()
				if not serviceIterator.valid(): #check end of list
					break
				playable = not (serviceIterator.flags & (eServiceReference.isMarker|eServiceReference.isDirectory))
				if playable:
					num -= 1;
			if not num: #found service with searched number ?
				return serviceIterator, 0
		return None, num

	def zapToNumber(self, number):
		bouquet = self.servicelist.bouquet_root
		service = None
		serviceHandler = eServiceCenter.getInstance()
		bouquetlist = serviceHandler.list(bouquet)
		if not bouquetlist is None:
			while number:
				bouquet = bouquetlist.getNext()
				if not bouquet.valid(): #check end of list
					break
				if bouquet.flags & eServiceReference.isDirectory:
					service, number = self.searchNumberHelper(serviceHandler, number, bouquet)
		if not service is None:
			if self.servicelist.getRoot() != bouquet: #already in correct bouquet?
				self.servicelist.clearPath()
				if self.servicelist.bouquet_root != bouquet:
					self.servicelist.enterPath(self.servicelist.bouquet_root)
				self.servicelist.enterPath(bouquet)
			self.servicelist.setCurrentSelection(service) #select the service in servicelist
		# update infos, no matter if service is none or not
		current = ServiceReference(self.servicelist.getCurrentSelection())
		self.playService(current.ref)

	def nextService(self):
		if self.servicelist is not None:
			# get next service
			if self.servicelist.inBouquet():
				prev = self.servicelist.getCurrentSelection()
				if prev:
					prev = prev.toString()
					while True:
						if config.usage.quickzap_bouquet_change.value and self.servicelist.atEnd():
							self.servicelist.nextBouquet()
						else:
							self.servicelist.moveDown()
						cur = self.servicelist.getCurrentSelection()
						if not cur or (not (cur.flags & 64)) or cur.toString() == prev:
							break
			else:
				self.servicelist.moveDown()
			if self.isPlayable():
				current = ServiceReference(self.servicelist.getCurrentSelection())
				self.playService(current.ref)
			else:
				self.nextService()

	def prevService(self):
		if self.servicelist is not None:
			# get previous service
			if self.servicelist.inBouquet():
				prev = self.servicelist.getCurrentSelection()
				if prev:
					prev = prev.toString()
					while True:
						if config.usage.quickzap_bouquet_change.value:
							if self.servicelist.atBegin():
								self.servicelist.prevBouquet()
						self.servicelist.moveUp()
						cur = self.servicelist.getCurrentSelection()
						if not cur or (not (cur.flags & 64)) or cur.toString() == prev:
							break
			else:
				self.servicelist.moveUp()
			if self.isPlayable():
				current = ServiceReference(self.servicelist.getCurrentSelection())
				self.playService(current.ref)
			else:
				self.prevService()

	def isPlayable(self):
		# check if service is playable
		current = ServiceReference(self.servicelist.getCurrentSelection())
		return not (current.ref.flags & (eServiceReference.isMarker|eServiceReference.isDirectory))

	def nextBouquet(self):
		if self.servicelist is not None:
			# next bouquet with first service
			if config.usage.multibouquet.value:
				self.servicelist.nextBouquet()
				current = ServiceReference(self.servicelist.getCurrentSelection())
				self.playService(current.ref)

	def prevBouquet(self):
		if self.servicelist is not None:
			# previous bouquet with first service
			if config.usage.multibouquet.value:
				self.servicelist.prevBouquet()
				current = ServiceReference(self.servicelist.getCurrentSelection())
				self.playService(current.ref)

	def openSingleServiceEPG(self):
		# show EPGList
		current = ServiceReference(self.servicelist.getCurrentSelection())
		self.session.open(EPGSelection, current.ref)

	def openEventView(self):
		# show EPG Event
		epglist = [ ]
		self.epglist = epglist
		service = ServiceReference(self.servicelist.getCurrentSelection())
		ref = service.ref
		evt = self.epgcache.lookupEventTime(ref, -1)
		if evt:
			epglist.append(evt)
		evt = self.epgcache.lookupEventTime(ref, -1, 1)
		if evt:
			epglist.append(evt)
		if epglist:
			self.session.open(EventViewEPGSelect, epglist[0], service, self.eventViewCallback, self.openSingleServiceEPG, self.openMultiServiceEPG, self.openSimilarList)

	def eventViewCallback(self, setEvent, setService, val):
		epglist = self.epglist
		if len(epglist) > 1:
			tmp = epglist[0]
			epglist[0] = epglist[1]
			epglist[1] = tmp
			setEvent(epglist[0])

	def openMultiServiceEPG(self):
		# not supported
		pass

	def openSimilarList(self, eventid, refstr):
		self.session.open(EPGSelection, refstr, None, eventid)

	def playService(self, service):
		# PiPServiceRelation support
		piprelationservice = self.pipServiceRelation.get(service.toString(),None)
		if piprelationservice is not None:
			 service = eServiceReference(piprelationservice)
		if service and (service.flags & eServiceReference.isGroup):
			ref = getBestPlayableServiceReference(service, eServiceReference())
		else:
			ref = service
		self.pipservice = eServiceCenter.getInstance().play(ref)
		if self.pipservice and not self.pipservice.setTarget(1):
			self.pipservice.start()
			self.currService = ref
		
