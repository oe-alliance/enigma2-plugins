from Components.Sources.Source import Source
from Components.Network import iNetwork
from Components.Element import cached


class Network(Source):
    LAN = 0
    WLAN = 1
    
    def __init__(self, device = LAN):
        Source.__init__(self)
        if device is self.LAN:
            self.iface = "eth0"
        elif device is self.WLAN:
            self.iface = "ath0"
    @cached        
    def getInterface(self):
        self.mac =  iNetwork.getAdapterAttribute(self.iface, "mac")
        self.dhcp = iNetwork.getAdapterAttribute(self.iface, "dhcp")
        self.ip = ConvertIP(iNetwork.getAdapterAttribute(self.iface, "ip"))
        self.netmask = ConvertIP(iNetwork.getAdapterAttribute(self.iface, "netmask"))
        self.gateway = ConvertIP(iNetwork.getAdapterAttribute(self.iface, "gateway"))
        
    interface = property(getInterface)
    
    def destroy(self):
        Source.destroy(self)