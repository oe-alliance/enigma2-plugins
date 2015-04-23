# for localized messages
from . import _

# Plugin definition
from Plugins.Plugin import PluginDescriptor

from enigma import eServiceCenter, eServiceReference
from Components.Label import Label
from Screens import InfoBarGenerics
from Screens.InfoBar import InfoBar
from Components.config import config, ConfigSubsection, ConfigSelection

from NamezapSetup import NamezapSetup
from boxbranding import getImageDistro

config.plugins.namezap = ConfigSubsection()
config.plugins.namezap.style = ConfigSelection(choices = [
		("number", _("Only Number")),
		("name", _("Service Name")),
		("both", _("Number and Name"))
	], default = "both"
)

NumberZap = InfoBarGenerics.NumberZap
class NameZap(NumberZap):
	STYLE_NUMBER = 0
	STYLE_NAME = 1
	STYLE_BOTH = 2

	skin = """<screen name="NameZap" position="center,center" size="270,60" title="Channel">
			<widget name="name" position="3,15" size="264,25" halign="left" font="Regular;23" />
		</screen>"""

	def __init__(self, *args, **kwargs):
		NumberZap.__init__(self, *args, **kwargs)
		if InfoBar.instance is None:
			self.style = self.STYLE_NUMBER
		else:
			self.style = {"number": self.STYLE_NUMBER, "name": self.STYLE_NAME, "both": self.STYLE_BOTH}[config.plugins.namezap.style.value]

		if self.style == self.STYLE_NUMBER:
			self.skinName = "NumberZap"

		self["name"] = Label("")
		self.serviceHandler = eServiceCenter.getInstance()
		if self.style != self.STYLE_NUMBER:
			self.updateServiceName(int(self.field))

	def keyNumberGlobal(self, number):
		NumberZap.keyNumberGlobal(self, number)
		if self.style != self.STYLE_NUMBER:
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

			sname = info.getName(service).replace('\xc2\x86', '').replace('\xc2\x87', '')
			if self.style == self.STYLE_BOTH:
				self["name"].setText("%s. %s" % (self.field, sname))
			else:
				self["name"].setText(sname)
		else:
			sname = _("Unknown Service")
			if self.style == self.STYLE_BOTH:
				self["name"].setText("%s. %s" % (self.field, sname))
			else:
				self["name"].setText("%s (%s)" % (sname, self.field))

def autostart(reason, *args, **kwargs):
	if reason == 0:
		InfoBarGenerics.NumberZap = NameZap

def main(session, *args, **kwargs):
	session.open(NamezapSetup)

def menu(menuid):
	if getImageDistro() in ('openmips'):
		if menuid != "ui_menu":
			return [ ]
	elif getImageDistro() in ('openhdf'):
		if menuid != "gui_menu":
			return [ ]
	else:
		if menuid != "system":
			return []
	return [(_("NameZAP Setup"), main, "namezap_setup", None)]

def Plugins(**kwargs):
	return [
		PluginDescriptor(
			where=PluginDescriptor.WHERE_AUTOSTART,
			fnc=autostart,
			needsRestart=False,
		),
		PluginDescriptor(
			where=PluginDescriptor.WHERE_MENU,
			fnc=menu,
			needsRestart=False,
		),
	]
