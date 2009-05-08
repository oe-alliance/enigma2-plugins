# Parts of Code and idea by Homey
from Components.Sources.Source import Source
from Components.Harddisk import harddiskmanager
from Components.NimManager import nimmanager
from Components.Network import iNetwork
from Components.About import about

from Tools.DreamboxHardware import getFPVersion

from ServiceReference import ServiceReference
from enigma import iServiceInformation

from Components.config import config

class About(Source):
	def __init__(self, session):
		Source.__init__(self)
		self.session = session

	def handleCommand(self, cmd):
		self.result = False, "unknown command"

	def command(self):
		def ConvertIP(list):
			if(len(list) == 4):
				retstr = "%s.%s.%s.%s" % (list[0], list[1], list[2], list[3])
			else:
				retstr = "0.0.0.0"
			return retstr
		
		list = []

		if iNetwork.getNumberOfAdapters > 0:
			iface = iNetwork.getAdapterList()[0]
			print "[WebComponents.About] iface: %s" % iface
			list.append(iNetwork.getAdapterAttribute(iface, "mac"))
			list.append(iNetwork.getAdapterAttribute(iface, "dhcp"))
			list.append(ConvertIP(iNetwork.getAdapterAttribute(iface, "ip")))
			list.append(ConvertIP(iNetwork.getAdapterAttribute(iface, "netmask")))
			list.append(ConvertIP(iNetwork.getAdapterAttribute(iface, "gateway")))
		else:
			print "[WebComponents.About] no network iface configured!"
			list.append("N/A")
			list.append("N/A")
			list.append("N/A")
			list.append("N/A")
			list.append("N/A")

		return [list]
	
	list = property(command)
	lut = { "lanMac": 0
			, "lanDHCP": 1
			, "lanIP": 2
			, "lanMask": 3
			, "lanGW": 4
		}
