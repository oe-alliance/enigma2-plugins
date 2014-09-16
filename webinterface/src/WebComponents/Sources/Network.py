from Components.Sources.Source import Source
from Components.Network import iNetwork
from Tools.Directories import fileExists
from twisted.web import version
from socket import has_ipv6, AF_INET6, inet_ntop, inet_pton

def normalize_ipv6(orig):
	net = []

	if '/' in orig:
		net = orig.split('/')
		if net[1] == "128":
			del net[1]
	else:
		net.append(orig)

	addr = net[0]

	addr = inet_ntop(AF_INET6, inet_pton(AF_INET6, addr))

	if len(net) == 2:
		addr += "/" + net[1]

	return (addr)

def getAdapterIPv6(interface):
	addr = _("IPv4-only kernel")
	
	if fileExists('/proc/net/if_inet6'):
		addr = _("IPv4-only Python/Twisted")

		if has_ipv6 and version.major >= 12:
			proc = '/proc/net/if_inet6'
			tempaddrs = []
			for line in file(proc).readlines():
				if line.startswith('fe80'):
					continue

				tmpaddr = ""
				tmp = line.split()
				if interface == tmp[5]:
					tmpaddr = ":".join([ tmp[0][i:i+4] for i in range(0,len(tmp[0]),4) ])

					if tmp[2].lower() != "ff":
						tmpaddr = "%s/%s" % (tmpaddr, int(tmp[2].lower(), 16))

					tempaddrs.append(normalize_ipv6(tmpaddr))

			if len(tempaddrs) > 1:
				tempaddrs.sort()
				addr = ', '.join(tempaddrs)
			elif len(tempaddrs) == 1:
				addr = tempaddrs[0]
			elif len(tempaddrs) == 0:
				addr = _("none/IPv4-only network")

	return (addr)


class Interface:
	def __init__(self, name):
		self.name = name
		self.mac = None
		self.dhcp = None
		self.ip = None
		self.netmask = None
		self.gateway = None
		self.ipv6 = None

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
		iface.ipv6 = getAdapterIPv6(self.iface)

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
					self.ConvertIP(iNetwork.getAdapterAttribute(ifname, "gateway")),
					getAdapterIPv6(ifname)
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
			"Ipv6" : 6,
		   }

