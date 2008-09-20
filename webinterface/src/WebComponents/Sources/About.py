# Parts of Code and idea  by Homey
from Components.Sources.Source import Source
from Components.Harddisk import HarddiskManager
from Components.NimManager import nimmanager
from Components.Network import iNetwork
from Components.About import about

from Tools.DreamboxHardware import getFPVersion

from ServiceReference import ServiceReference
from enigma import iServiceInformation

from Components.config import config

class About( Source):
    
    def __init__(self, session):
        Source.__init__(self)
        self.session = session
    
    def handleCommand(self,cmd):
        self.result = False,"unknown command"
        
    def command(self):
        list = []
        list.append(about.getVersionString()) 


        #Get Network Info
        def ConvertIP(list):
            if(len(list) == 4):
                retstr = "%s.%s.%s.%s" %(list[0], list[1], list[2], list[3])
            else:
                retstr = "0.0.0.0"
            return retstr

        iface = "eth0"
        list.append(iNetwork.getAdapterAttribute(iface, "dhcp"))
        list.append(ConvertIP(iNetwork.getAdapterAttribute(iface, "ip")))
        list.append(ConvertIP(iNetwork.getAdapterAttribute(iface, "netmask")))
        list.append(ConvertIP(iNetwork.getAdapterAttribute(iface, "gateway")))


        #Get FrontProcessor Version
        fp_version = getFPVersion()
        if fp_version is None:
            fp_version = "?"
        else:
            fp_version = str(fp_version)
        list.append(fp_version)

        #Get Tuner Info
        niminfo = ""
        for nim in nimmanager.nimList():
            info = nim.split(":")
            
            niminfo += "\n\t\t\t<e2nim>\n"
            niminfo += "\t\t\t\t<name>%s</name>\n" %(info[0])
            niminfo += "\t\t\t\t<type>%s</type>\n" %(info[1])
            niminfo += "\t\t\t</e2nim>"
            
        list.append(niminfo)

        #Get HDD Info
        hddmgr = HarddiskManager()
        if len(hddmgr.hdd):
            hdddata = hddmgr.hdd[0] # TODO, list more than the first harddisc if there are more than one. but this requires many changes in the way the webif generates the responses
            hddinfo = "\n\t\t\t<model>"+hdddata.model()+"</model>\n"
            hddinfo += "\t\t\t<capacity>"+hdddata.capacity()+"</capacity>\n"
            hddinfo += "\t\t\t<free>"+str(hdddata.free())+" MB</free>"
            list.append(hddinfo)
        else:            
            hddinfo = "\n\t\t\t<model>N/A</model>\n"
            hddinfo += "\t\t\t<capacity>-</capacity>\n"
            hddinfo += "\t\t\t<free>-</free>"
            list.append(hddinfo)

        #Get Service Info
        service = self.session.nav.getCurrentService()

        if self.session.nav.getCurrentlyPlayingServiceReference() is not None:
            Name = ServiceReference(self.session.nav.getCurrentlyPlayingServiceReference()).getServiceName()
        else:
            Name = "N/A"
        list.append(Name)

        if service is not None:
            svinfo = service.info()
            svfeinfo = service.frontendInfo()
        else:
            svinfo = None
            svfeinfo = None

        # Get Service Info
        if self.session.nav.getCurrentlyPlayingServiceReference() is not None:
            list.append(svinfo.getInfoString(iServiceInformation.sProvider))
            
            aspect = svinfo.getInfo(iServiceInformation.sAspect)
            if aspect in ( 1, 2, 5, 6, 9, 0xA, 0xD, 0xE ):
                aspect = "4:3"
            else:
                aspect = "16:9"
            list.append(aspect)

            width = svinfo and svinfo.getInfo(iServiceInformation.sVideoWidth) or -1
            height = svinfo and svinfo.getInfo(iServiceInformation.sVideoHeight) or -1
            videosize = "%dx%d" %(width, height)
            list.append(videosize)
            
            list.append(hex(svinfo.getInfo(iServiceInformation.sNamespace)))

            # Get PIDs
            list.append(svinfo.getInfo(iServiceInformation.sVideoPID))
            list.append(svinfo.getInfo(iServiceInformation.sAudioPID))
            list.append(svinfo.getInfo(iServiceInformation.sPCRPID))
            list.append(svinfo.getInfo(iServiceInformation.sPMTPID))
            list.append(svinfo.getInfo(iServiceInformation.sTXTPID))
            list.append(svinfo.getInfo(iServiceInformation.sTSID))
            list.append(svinfo.getInfo(iServiceInformation.sONID))
            list.append(svinfo.getInfo(iServiceInformation.sSID))
        else:
            list.append("N/A")
            list.append("N/A")
            list.append("N/A")
            list.append("N/A")
            list.append("N/A")
            list.append("N/A")
            list.append("N/A")
            list.append("N/A")
            list.append("N/A")
            list.append("N/A")
            list.append("N/A")
            list.append("N/A")
            
        ## webifversion
        list.append(config.plugins.Webinterface.version.value)
        
        #please remove unneeded debugoutpu while commiting #print list
        
        listR = []
        listR.append(list)
        
        return listR

    text = property(command)        
    
    list = property(command)
    lut = {"enigmaVersion": 0
           ,"lanDHCP": 1
           ,"lanIP": 2
           ,"lanMask": 3
           ,"lanGW": 4
           ,"fpVersion": 5
           ,"tunerInfo": 6
           ,"hddInfo": 7
           ,"serviceName": 8
           ,"serviceProvider": 9
           ,"serviceAspect": 10
           ,"serviceVideosize": 11
           ,"serviceNamespace": 12
           ,"vPID": 13
           ,"aPID": 14
           ,"pcrID": 15
           ,"pmtPID": 16
           ,"txtPID": 17
           ,"tsID": 18
           ,"onID": 19
           ,"sid": 20
           ,"WebIfVersion": 21
           }