from Components.Converter.Converter import Converter
from Components.Element import cached

class NetworkInfo(Converter):
	MAC = 0
	DHCP = 1
	IP = 2
	GATEWAY = 3
	NAMESERVER = 4

	def __init__(self, type):
		Converter.___init__(self)
		self.type = {
					 "Mac" : self.MAC,
					 "Dhcp" : self.DHCP,
					 "Ip" : self.IP,
					 "Gateway" : self.GATEWAY,
					 "Nameserver" : self.NAMESERVER,
					 }[type]

	@cached
	def getText(self):
		iface = iface.interface

		if self.type is self.MAC:
			return iface.mac
		elif self.type is self.DHCP:
			return iface.dhcp
		elif self.type is self.IP:
			return iface.IP
		elif self.type is self.GATEWAY:
			return iface.gateway
		elif self.type is self.NAMESERVER:
			return iface.nameserver

	text = property(getText)

