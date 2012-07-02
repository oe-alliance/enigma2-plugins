from Components.Sources.Source import Source
from Components.Network import iNetwork

class Interface:
	def __init__(self, name):
		self.name = name
		self.mac = None
		self.dhcp = None
		self.ip = None
		self.netmask = None
		self.gateway = None

class Network(Source):
	LAN = 0
	WLAN = 1

	def __init__(self, device=LAN):
		Source.__init__(self)
		if device is self.LAN:
			self.iface = "eth0"
		elif device is self.WLAN:
			self.iface = "ath0"

	ConvertIP = lambda self, l: "%s.%s.%s.%s" % tuple(l) if l and len(l) == 4 else "0.0.0.0"

	def getInterface(self):
		iface = Interface(self.iface)
		iface.mac = iNetwork.getAdapterAttribute(self.iface, "mac")
		iface.dhcp = iNetwork.getAdapterAttribute(self.iface, "dhcp")
		iface.ip = self.ConvertIP(iNetwork.getAdapterAttribute(self.iface, "ip"))
		iface.netmask = self.ConvertIP(iNetwork.getAdapterAttribute(self.iface, "netmask"))
		iface.gateway = self.ConvertIP(iNetwork.getAdapterAttribute(self.iface, "gateway"))

		return iface

	interface = property(getInterface)

	def getList(self):
		return [
			(
					ifname,
					iNetwork.getAdapterAttribute(ifname, "mac"),
					iNetwork.getAdapterAttribute(ifname, "dhcp"),
					self.ConvertIP(iNetwork.getAdapterAttribute(ifname, "ip")),
					self.ConvertIP(iNetwork.getAdapterAttribute(ifname, "netmask")),
					self.ConvertIP(iNetwork.getAdapterAttribute(ifname, "gateway"))
			)
			for ifname in iNetwork.getConfiguredAdapters()
		]

	list = property(getList)

	lut = {
			"Name": 0,
			"Mac" : 1,
			"Dhcp" : 2,
			"Ip" : 3,
			"Netmask" : 4,
			"Gateway" : 5,
		   }

