# Parts of Code and idea  by Homey
from enigma import *

from Components.Sources.Source import Source
from Components.Harddisk import Harddisk
from Components.NimManager import nimmanager
from Components.About import about

from Tools.DreamboxHardware import getFPVersion

from ServiceReference import ServiceReference
from enigma import iServiceInformation

from Components.config import config, getConfigListEntry

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
            niminfo += "<e2nim>"+nim[0]+"</e2nim>"
        list.append(niminfo)

        #Get HDD Info
        hdddata = Harddisk(0)
        if hdddata.model() != "":
            hddinfo = "<model>"+hdddata.model()+"</model>"
            hddinfo += "<capacity>"+hdddata.capacity()+"</capacity>"
            hddinfo += "<free>"+str(hdddata.free())+" MB</free>"
            
        else:            
            hddinfo = "no harddisc detected"
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
            list.append(svinfo.getInfo(iServiceInformation.sAspect))
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
           ,"serviceNamespace": 7
           ,"vPID": 8
           ,"aPID": 9
           ,"pcrID": 10
           ,"pmtPID": 11
           ,"txtPID": 12
           ,"tsID": 13
           ,"onID": 14
           ,"sid": 15
           }

