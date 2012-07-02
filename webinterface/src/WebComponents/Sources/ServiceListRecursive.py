from Components.Sources.Source import Source
from Components.Sources.ServiceList import ServiceList
from Screens.ChannelSelection import service_types_tv
from enigma import eServiceReference

class ServiceListRecursive(Source):
	FETCH = 0

	def __init__(self, session, func=FETCH):
		Source.__init__(self)

		self.session = session
		self.func = func
		self.servicelist = {}
		self.xml = ""
		self.command = eServiceReference(service_types_tv + ' FROM BOUQUET "bouquets.tv" ORDER BY bouquet')

	def handleCommand(self, cmd):
		self.command = eServiceReference(cmd)

	def do_func(self):
		if self.func == self.FETCH:
			func = self.buildList
		else:
			func = self.buildList

		return func(self.command)

	def buildList(self, ref):
		self.servicelist = ServiceList(ref, command_func=self.getServiceList, validate_commands=False)
		list = self.servicelist.getServicesAsList()
		for item in list:
			self.servicelist.setRoot(eServiceReference(item[0]))
			sub = self.servicelist.getServicesAsList()

			if sub:
				self.xml += "\t<e2bouquet>\n"
				bouquet = True

				subxml = ""
				for (ref, name) in sub:
					name = name.replace('\xc2\x86', '').replace('\xc2\x87', '')
					subxml += "\t\t\t<e2service>\n"
					subxml += "\t\t\t\t<e2servicereference>%s</e2servicereference>\n\t\t\t\t<e2servicename>%s</e2servicename>\n" % (self.filterXML(ref), self.filterXML(name))
					subxml += "\t\t\t</e2service>\n"

			else:
				self.xml += "\t\t<e2service>\n"
				bouquet = False
			
			self.xml += "\t\t<e2servicereference>%s</e2servicereference>\n\t\t<e2servicename>%s</e2servicename>\n" % (self.filterXML(item[0]), self.filterXML(item[1]))

			if bouquet:
				self.xml += "\t\t<e2servicelist>\n"
				self.xml += subxml
				self.xml += "\t\t</e2servicelist>\n"
				self.xml += "\t</e2bouquet>\n"
			else:
				self.xml += "\t</e2service>\n"

		return self.xml

	def filterXML(self, item):
		item = item.replace("&", "&amp;").replace("<", "&lt;").replace('"', '&quot;').replace(">", "&gt;").replace('\xc2\x86', '').replace('\xc2\x87', '')
		return item

	def getServiceList(self, ref):
		self.servicelist.root = ref

	text = property(do_func)

#	list = property(do_func)
#	lut = {"ServiceReference": 0, "ServiceName": 1 }
