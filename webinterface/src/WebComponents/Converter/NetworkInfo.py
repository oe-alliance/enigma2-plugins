from Components.Converter.Converter import Converter
from Components.Element import cached

class NetworkInfo(Converter, object):
	MAC = 0
	DHCP = 1
	IP = 2
	GATEWAY = 3
	NETMASK = 4

	def __init__(self, type):
		Converter.__init__(self, type)
		self.type = {
					 "Mac" : self.MAC,
					 "Dhcp" : self.DHCP,
					 "Ip" : self.IP,
					 "Gateway" : self.GATEWAY,
					 "Netmask" : self.NETMASK,
					 }[type]

	@cached
	def getText(self):
		iface = self.source.interface

		if self.type is self.MAC:
			return iface.mac
		elif self.type is self.DHCP:
			return iface.dhcp
		elif self.type is self.IP:
			return iface.ip
		elif self.type is self.GATEWAY:
			return iface.gateway
		elif self.type is self.NETMASK:
			return iface.netmask
		else:
			return _("N/A")

	text = property(getText)

