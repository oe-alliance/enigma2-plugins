from Components.Converter.Converter import Converter
from Components.Element import cached

class NetworkInfo(Converter, object):
	NAME = 0
	MAC = 1
	DHCP = 2
	IP = 3
	GATEWAY = 4
	NETMASK = 5
	
	
	def __init__(self, type):
		Converter.__init__(self, type)
		self.type = {
					 "Name" : self.NAME, 				 
					 "Mac" : self.MAC,
					 "Dhcp" : self.DHCP,
					 "Ip" : self.IP,
					 "Gateway" : self.GATEWAY,
					 "Netmask" : self.NETMASK, 					 
					 }[type]
	
	@cached
	def getText(self):
		iface = self.source.interface
		
		if self.type is self.NAME:
			return iface.name		
		elif self.type is self.MAC:
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
	
