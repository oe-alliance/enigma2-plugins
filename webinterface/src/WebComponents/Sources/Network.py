from Components.Sources.Source import Source
from Components.Network import iNetwork
#from Components.Element import cached


class Network(Source):
    LAN = 0
    WLAN = 1
    
    def __init__(self, device = LAN):
        Source.__init__(self)
        if device is self.LAN:
            self.iface = "eth0"
        elif device is self.WLAN:
            self.iface = "ath0"
            
            
            #Get Network Info
    def ConvertIP(self, list):
        if(len(list) == 4):
            retstr = "%s.%s.%s.%s" %(list[0], list[1], list[2], list[3])
        else:
            retstr = "0.0.0.0"
        return retstr
#    @cached        
    def getInterface(self):
        self.mac =  iNetwork.getAdapterAttribute(self.iface, "mac")
        self.dhcp = iNetwork.getAdapterAttribute(self.iface, "dhcp")
        self.ip = self.ConvertIP(iNetwork.getAdapterAttribute(self.iface, "ip"))
        self.netmask = self.ConvertIP(iNetwork.getAdapterAttribute(self.iface, "netmask"))
        self.gateway = self.ConvertIP(iNetwork.getAdapterAttribute(self.iface, "gateway"))
        
        return self
        
    interface = property(getInterface)
    
    def destroy(self):
        Source.destroy(self)