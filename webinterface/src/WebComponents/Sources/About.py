# Parts of Code and idea by Homey
from Components.Sources.Source import Source
from Components.Network import iNetwork

class About(Source):
	def __init__(self, session):
		Source.__init__(self)
		self.session = session

	def handleCommand(self, cmd):
		self.result = False, "unknown command"

	def command(self):
		ConvertIP = lambda l: "%s.%s.%s.%s" % tuple(l) if len(l) == 4 else "0.0.0.0"

		if iNetwork.getNumberOfAdapters > 0:
			iface = "eth0" # iNetwork.getAdapterList()[0]
			# print "[WebComponents.About] iface: %s" % iface
			l = (
				iNetwork.getAdapterAttribute(iface, "mac"),
				iNetwork.getAdapterAttribute(iface, "dhcp"),
				ConvertIP(iNetwork.getAdapterAttribute(iface, "ip")),
				ConvertIP(iNetwork.getAdapterAttribute(iface, "netmask")),
				ConvertIP(iNetwork.getAdapterAttribute(iface, "gateway")),
			)
		else:
			print "[WebComponents.About] no network iface configured!"
			l = (
				"N/A",
				"N/A",
				"N/A",
				"N/A",
				"N/A",
			)

		return (l,)

	list = property(command)
	lut = { "lanMac": 0
			, "lanDHCP": 1
			, "lanIP": 2
			, "lanMask": 3
			, "lanGW": 4
		}
