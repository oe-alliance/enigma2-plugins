#
#  Partnerbox E2
#
#  $Id$
#
#  Coded by Dr.Best (c) 2009
#  Support: www.dreambox-tools.info
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#

from Components.Sources.Source import Source
from Components.Sources.ServiceList import ServiceList
from Screens.ChannelSelection import service_types_tv
from enigma import eServiceReference, eEPGCache


class E2EPGListAllData:
	def __init__(self, servicereference = "", servicename = "", eventid = 0, eventstart = 0, eventduration = 0, eventtitle = "", eventdescription = "", eventdescriptionextended = ""):
		self.servicereference = servicereference
		self.servicename = servicename
		self.eventid = eventid
		self.eventstart = eventstart
		self.eventduration = eventduration
		self.eventtitle = eventtitle
		self.eventdescription = eventdescription
		self.eventdescriptionextended = eventdescriptionextended

class E2ServiceList:
	def __init__(self, servicereference = "", servicename = ""):
		self.servicereference = servicereference
		self.servicename = servicename

class Services( Source ):
	def __init__(self, session):
		Source.__init__(self)
		self.session = session
		self.servicelist = {}
		self.epgcache = eEPGCache.getInstance()
	
	def buildList(self, ref, epg):
		self.servicelist = ServiceList(ref, command_func = self.getServiceList, validate_commands=False)
		list = self.servicelist.getServicesAsList()
		E2List = [] 
		for index in range(len(list)): 
			item = list[index]
			servicereference = item[0]
			servicename = item[1]
			eventstart = 0
			eventduration = 0
			eventtitle = ""
			eventid = 0
			eventdescription = ""
			eventdescriptionextended = ""
			if epg:
				epgref = item[0]
				events = self.epgcache.lookupEvent(['IBDTSERNX', (epgref, 0, -1)])
				if events:
					if events[0][0] is not None:
						eventid =  events[0][0]
					if events[0][1] is not None:
						eventstart =  events[0][1]
					if events[0][2] is not None:
						eventduration =  events[0][2]
					if events[0][3] is not None:
						eventtitle = events[0][3]
					if events[0][4] is not None:
						eventdescription= events[0][4]
					if events[0][5] is not None:
						eventdescriptionextended= events[0][5]
				E2List.append(E2EPGListAllData(servicereference = servicereference, servicename = servicename, eventstart = eventstart, eventduration = eventduration, eventtitle = eventtitle, eventid = eventid, eventdescription= eventdescription, eventdescriptionextended = eventdescriptionextended))
			else:
					E2List.append(E2ServiceList(servicereference = item[0], servicename = item[1]))
		return E2List

	def buildEPGList(self, ref):
		E2List = [] 
		events = self.epgcache.lookupEvent(['IBDTSERN', (ref, 0, -1, -1)]);
		if events:
			for item in events:
				servicereference = ""
				servicename = ""
				eventstart = 0
				eventduration = 0
				eventtitle = ""
				eventid = 0
				eventdescription = ""
				eventdescriptionextended = ""
				if item[6] is not None:
					servicereference = item[6]
				if item[7] is not None:
					servicename = item[7]
				if item[1] is not None:
					eventstart = item[1]
				if item[2] is not None:
					eventduration = item[2]
				if item[3] is not None:
					eventtitle = item[3]
				if item[0] is not None:
					eventid = item[0]
				if item[4] is not None:
					eventdescription = item[4]
				if item[5] is not None:
					eventdescriptionextended = item[5]
				if eventstart != 0:
					E2List.append(E2EPGListAllData(servicereference = servicereference, servicename = servicename, eventstart = eventstart, eventduration = eventduration, eventtitle = eventtitle, eventid = eventid, eventdescription= eventdescription, eventdescriptionextended = eventdescriptionextended))
		return E2List
	
	def getServiceList(self, ref):
		self.servicelist.root = ref
