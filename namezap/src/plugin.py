# Plugin definition
from Plugins.Plugin import PluginDescriptor

from enigma import eServiceCenter, eServiceReference
from Components.Label import Label
from Screens import InfoBarGenerics
from Screens.InfoBar import InfoBar
from Components.config import config

NumberZap = InfoBarGenerics.NumberZap
class NameZap(NumberZap):
	skin = """<screen name="NameZap" position="center,center" size="300,60" title="Channel">
			<widget name="channel" position="5,15" size="100,25" font="Regular;23" />
			<widget name="name" position="105,15" size="190,25" halign="right" font="Regular;23" />
		</screen>"""

	def __init__(self, *args, **kwargs):
		NumberZap.__init__(self, *args, **kwargs)
		self["name"] = Label("")
		self.serviceHandler = eServiceCenter.getInstance()
		self.updateServiceName(int(self.field))

	def keyNumberGlobal(self, number):
		NumberZap.keyNumberGlobal(self, number)
		self.updateServiceName(int(self.field))

	def searchNumberHelper(self, serviceHandler, num, bouquet):
		servicelist = self.serviceHandler.list(bouquet)
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

	def updateServiceName(self, number):
		bouquet = InfoBar.instance.servicelist.bouquet_root
		service = None
		serviceHandler = self.serviceHandler
		if not config.usage.multibouquet.value:
			service, number = self.searchNumberHelper(serviceHandler, number, bouquet)
		else:
			bouquetlist = serviceHandler.list(bouquet)
			if not bouquetlist is None:
				while number:
					bouquet = bouquetlist.getNext()
					if not bouquet.valid(): #check end of list
						break
					if bouquet.flags & eServiceReference.isDirectory:
						service, number = self.searchNumberHelper(serviceHandler, number, bouquet)
		if service is not None:
			info = serviceHandler.info(service)
			self["name"].setText(info.getName(service).replace('\xc2\x86', '').replace('\xc2\x87', ''))
		else:
			self["name"].setText("??? (%s)" % (self.field,))

def autostart(reason, *args, **kwargs):
	if reason == 0:
		InfoBarGenerics.NumberZap = NameZap

# TODO: allow to disable this :-)

def Plugins(**kwargs):
	return [
		PluginDescriptor(
			where=PluginDescriptor.WHERE_AUTOSTART,
			fnc=autostart,
			needsRestart=False,
		),
	]
