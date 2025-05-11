from __future__ import print_function
from Components.Sources.Source import Source
from Screens.ChannelSelection import service_types_tv, service_types_radio, FLAG_SERVICE_NEW_FOUND, MODE_TV, MODE_RADIO
from enigma import eServiceReference, eServiceCenter
from Components.SystemInfo import BoxInfo
service_types_tv_hd = '1:7:1:0:0:0:0:0:0:0:(type == 17) || (type == 25) || (type == 134) || (type == 195)'


class SatellitesList(Source):
	FETCH = 0

	def __init__(self, func=FETCH):
		Source.__init__(self)
		self.func = func
		self.xml = ""
		self.mode = MODE_TV

	def handleCommand(self, param):
		self.mode = int(param)

	def do_func(self):
		if self.func == self.FETCH:
			func = self.buildList
		else:
			func = self.buildList
		return func(self.mode)

	def buildList(self, mode):
		print("[WebComponents.SatellitesList] buildList with param = %d" % mode)
		if mode == MODE_TV:
			s_type = service_types_tv
		else:
			s_type = service_types_radio
		refstr = '%s FROM SATELLITES ORDER BY satellitePosition' % (s_type)
		ref = eServiceReference(refstr)
		serviceHandler = eServiceCenter.getInstance()
		counter = i = 0
		if BoxInfo.getItem("model") != "dm7025" and mode == MODE_TV:
			counter = 1
		while i <= counter:
			if i:
				refstr = '%s FROM SATELLITES ORDER BY satellitePosition' % (service_types_tv_hd)
				ref = eServiceReference(refstr)
			servicelist = serviceHandler.list(ref)
			if servicelist is not None:
				while True:
					service = servicelist.getNext()
					if not service.valid():  # check if end of list
						break
					unsigned_orbpos = service.getUnsignedData(4) >> 16
					orbpos = service.getData(4) >> 16
					if orbpos < 0:
						orbpos += 3600
					if service.getPath().find("FROM PROVIDER") != -1:
						continue
					elif service.getPath().find("flags == %d" % (FLAG_SERVICE_NEW_FOUND)) != -1:
						service_type = _("New")
					else:
						service_type = _("Services")
					try:
						# why we need this cast?
						service_name = str(nimmanager.getSatDescription(orbpos))
					except:
						if unsigned_orbpos == 0xFFFF:  # Cable
							service_name = _("Cable")
						elif unsigned_orbpos == 0xEEEE:  # Terrestrial
							service_name = _("Terrestrial")
						else:
							if orbpos > 1800:  # west
								orbpos = 3600 - orbpos
								h = _("W")
							else:
								h = _("E")
							service_name = ("%d.%d %s") % (orbpos / 10, orbpos % 10, h)
					if i:
						service_type = "HD %s" % service_type
					service.setName("%s - %s" % (service_name, service_type))
					self.xml += "\t\t<e2service>\n"
					self.xml += "\t\t<e2servicereference>%s</e2servicereference>\n\t\t<e2servicename>%s</e2servicename>\n" % (self.filterXML(service.toString()), self.filterXML(service.getName()))
					self.xml += "\t\t</e2service>\n"
			i += 1
		return self.xml

	def filterXML(self, item):
		item = item.replace("&", "&amp;").replace("<", "&lt;").replace('"', '&quot;').replace(">", "&gt;").replace('\xc2\x86', '').replace('\xc2\x87', '')
		return item

	text = property(do_func)
