# -*- coding: UTF-8 -*-
from Components.Sources.Source import Source
from enigma import eServiceCenter, eServiceReference, eEPGCache

class EPG(Source):
	BOUQUETNOW = 0
	BOUQUETNEXT = 1
	SERVICENOW = 2
	SERVICENEXT = 3
	SERVICE = 4
	SEARCH = 5
	BOUQUET = 6
	MULTI = 7
	SEARCHSIMILAR = 8
	BOUQUETNOWNEXT = 9

	def __init__(self, navcore, func=BOUQUETNOW, endtm=False):
		self.func = func
		Source.__init__(self)
		self.navcore = navcore
		self.epgcache = eEPGCache.getInstance()
		self.command = None
		self.endtime = endtm
		self.search = False
		self.isBouquet = False

	def handleCommand(self, cmd):
		print "[WebComponents.EPG] setting command to '%s' " %cmd
		self.command = cmd

	def do_func(self):
		if not self.command is None:
			self.isBouquet = False
			if self.func is self.SEARCHSIMILAR:
				func = self.searchSimilarEvent
			elif self.func is self.SEARCH:
				func = self.searchEvent
			elif self.func is self.SERVICE:
				func = self.getEPGofService
			elif self.func is self.BOUQUETNOW:
				func = self.getBouquetEPGNow
			elif self.func is self.BOUQUETNEXT:
				func = self.getBouquetEPGNext
			elif self.func is self.BOUQUETNOWNEXT:
				func = self.getBouquetEPGNowNext
			elif self.func is self.BOUQUET:
				func = self.getEPGofBouquet
			elif self.func is self.MULTI:
				func = self.getBouquetEPGMulti
			elif self.func is self.SERVICENOW:
				func = self.getServiceEPGNow
			elif self.func is self.SERVICENEXT:
				func = self.getServiceEPGNext

			return func(self.command)
		return ()

	def getBouquetEPGNowNext(self, ref):
		return self.getEPGNowNext(ref, -1)

	def getBouquetEPGNow(self, ref):
		return self.getEPGNowNext(ref, 0)

	def getBouquetEPGNext(self, ref):
		return self.getEPGNowNext(ref, 1)

	def getServiceEPGNow(self, ref):
		return self.getEPGNowNext(ref, 0, True)

	def getServiceEPGNext(self, ref):
		return self.getEPGNowNext(ref, 1, True)

	def getBouquetEPGMulti(self, ref):
		return self.getEPGofBouquet(ref,  True)

	def getEPGNowNext(self, ref, type, service=False):
		print "[WebComponents.EPG] getting EPG NOW/NEXT", ref

		if service:
			events = self.epgcache.lookupEvent(['IBDCTSERNX', (ref, type, -1)])
		else:
			serviceHandler = eServiceCenter.getInstance()
			lst = serviceHandler.list(eServiceReference(ref))
			services = lst and lst.getContent('S', True)
			search = ['IBDCTSERNX']

			if services: # It's a Bouquet
				self.isBouquet = True
				if type == -1: #Now AND Next at once!
					append = search.append
					for service in services:
						append((service, 0, -1))
						append((service, 1, -1))
				else:
					search.extend([(service, type, -1) for service in services])
			events = self.epgcache.lookupEvent(search)

		if self.isBouquet:
			evts = []
			for event in events:
				event = list(event)
				event.append(ref)
				evts.append(event)
			return evts
		return events or ()

	def getEPGofService(self, param, options='IBDCTSERN'):
		print "[WebComponents.EPG] getEPGofService param: ", param

		if "sRef" in param:
			service = param["sRef"]
		else:
			return ()

		time = -1
		endtime = -1

		if "time" in param:
			if not param["time"] is None:
				time = int(float(param["time"]))
				if time < 0:
					time = -1

		if "endTime" in param:
			if not param["endTime"] is None:
				endtime = int( float(param["endTime"]) )
				if endtime < 0:
					endtime = -1

		events = self.epgcache.lookupEvent([options , (service, 0, time, endtime)]);

		if events:
			if self.endtime:
				list = self.insertEndTime(events)
				return list

			return events
		return ()

	def insertEndTime(self, events):
		list = []
		for event in events:
			i = 0
			evt = []
			end = event[1] + event[2]
			for item in event:
				if i == 3:
					evt.append(end)
					i += 1

				evt.append(item)
				i += 1

			list.append(evt)

		return list

	def getEPGofBouquet(self, param, multi = False):
		print "[WebComponents.EPG] getting EPG for Bouquet", param

		if 'bRef' not in param:
			return ()

		time = -1
		endtime = -1
		if "time" in param:
			if not param["time"] is None:
				time = int(float(param["time"]))
				if time < 0:
					time = -1

		if "endTime" in param:
			if not param["endTime"] is None:
				endtime = int( float(param["endTime"]) )
				if endtime < 0:
					endtime = -1

		bRef = param['bRef']
		if bRef is None:
			return ()

		serviceHandler = eServiceCenter.getInstance()
		sl = serviceHandler.list(eServiceReference(bRef))
		services = sl and sl.getContent('S', True)

		search = ['IBDCTSERN']

		if multi:
			search.extend([(service, 0, time, endtime) for service in services])
		else:
			search.extend([(service, 0, time) for service in services])
		events = self.epgcache.lookupEvent(search)

		if events:
			return events
		return ()

	def searchEvent(self, needle):
		print "[WebComponents.EPG] searching EPG: ", needle

		self.search = True

		events = self.epgcache.search(('IBDTSERN', 256, eEPGCache.PARTIAL_TITLE_SEARCH, needle, 1));
		if events:
			return events
		return ()

	def searchSimilarEvent(self, needle):
		print "[WebComponents.EPG] searching similar eventid: ",needle

		events = self.epgcache.search(('IBDCTSERN', 256, eEPGCache.SIMILAR_BROADCASTINGS_SEARCH, needle['sRef'], int(needle['eventid'])));
		if events:
			return events
		return ()

	def getLut(self):
		#No Current-Time on EPGSEARCH
		if self.search:
			if self.endtime:
				lut = {
						"EventID": 0,
						"TimeStart": 1,
						"Duration": 2,
						"TimeEnd": 3,
						"Title": 4,
						"Description": 5,
						"DescriptionExtended": 6,
						"ServiceReference": 7,
						"ServiceName": 8
					}
				return lut
			else:
				lut = {
					"EventID": 0,
					"TimeStart": 1,
					"Duration": 2,
					"Title": 3,
					"Description": 4,
					"DescriptionExtended": 5,
					"ServiceReference": 6,
					"ServiceName": 7
				}
		else:

			if self.endtime:
				lut = {
						"EventID": 0,
						"TimeStart": 1,
						"Duration": 2,
						"TimeEnd": 3,
						"CurrentTime": 4,
						"Title": 5,
						"Description": 6,
						"DescriptionExtended": 7,
						"ServiceReference": 8,
						"ServiceName": 9
					}
				return lut
			else:
				lut = {
					"EventID": 0,
					"TimeStart": 1,
					"Duration": 2,
					"CurrentTime": 3,
					"Title": 4,
					"Description": 5,
					"DescriptionExtended": 6,
					"ServiceReference": 7,
					"ServiceName": 8
				}
		if self.isBouquet:
			lut["BouquetReference"] = len(lut)
		return lut

	list = property(do_func)

	lut = property(getLut)
