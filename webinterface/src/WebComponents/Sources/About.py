# Parts of Code and idea  by Homey
from Components.Sources.Source import Source
from Components.Harddisk import Harddisk
from Components.NimManager import nimmanager
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

#===============================================================================
#        #Get Network Info
#        def ConvertIP(AddStr):
#            retstr = AddStr.replace(', ','.')
#            retstr = retstr.replace('[','')
#            retstr = retstr.replace(']','')
#            return retstr
# 
#        list.append(_("Use DHCP %s") % config.network.dhcp.value)
#        list.append(ConvertIP(_("IP Address %s") % config.network.ip.value))
#        list.append(ConvertIP(_("Netmask %s") % config.network.netmask.value))
#        list.append(ConvertIP(_("Gateway %s") % config.network.gateway.value))
#        list.append(ConvertIP(_("Nameserver %s") % config.network.dns.value))
#===============================================================================

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
        hdddata = Harddisk(0)
        if hdddata.model() != "":
            hddinfo = "\n\t\t\t<model>"+hdddata.model()+"</model>\n"
            hddinfo += "\t\t\t<capacity>"+hdddata.capacity()+"</capacity>\n"
            hddinfo += "\t\t\t<free>"+str(hdddata.free())+" MB</free>"
            
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
        if svinfo is not None:
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
            
        ## webifversion
        list.append(config.plugins.Webinterface.version.value)
        
        #please remove unneeded debugoutpu while commiting #print list
        
        listR = []
        listR.append(list)
        
        return listR

    text = property(command)        
    
    list = property(command)
    lut = {"enigmaVersion": 0
#           ,"lanDHCP": 1
 #          ,"lanIP": 2
  #         ,"lanMask": 3
   #        ,"lanGW": 4
    #       ,"lanDNS": 5
           ,"fpVersion": 1
           ,"tunerInfo": 2
           ,"hddInfo": 3
           ,"serviceName": 4
           ,"serviceProvider": 5
           ,"serviceAspect": 6
           ,"serviceVideosize": 7
           ,"serviceNamespace": 8
           ,"vPID": 9
           ,"aPID": 10
           ,"pcrID": 11
           ,"pmtPID": 12
           ,"txtPID": 13
           ,"tsID": 14
           ,"onID": 15
           ,"sid": 16
           ,"WebIfVersion": 17
           }