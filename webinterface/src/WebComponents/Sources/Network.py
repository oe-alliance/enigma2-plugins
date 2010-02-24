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

	def ConvertIP(self, list):
		retstr = None
		
		if list != None:
			if(len(list) == 4):
				retstr = "%s.%s.%s.%s" % (list[0], list[1], list[2], list[3])
		
		if retstr is None:
			retstr = "0.0.0.0"
			
		return retstr

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

