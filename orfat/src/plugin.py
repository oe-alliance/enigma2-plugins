##
## ORF.at streaming modules
## by AliAbdul
##
from ORFIPTV import ORFMain as ORFIPTVMain
from ORFonDemand import ORFMain as ORFonDemandMain
from Plugins.Plugin import PluginDescriptor

####################################################

def mainORFIPTV(session, **kwargs):
	session.open(ORFIPTVMain)

def mainORFonDemand(session, **kwargs):
	session.open(ORFonDemandMain)

def Plugins(**kwargs):
	return [
		PluginDescriptor(name="IPTV-Sendungen von ORF.at anschauen", where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=mainORFIPTV),
		PluginDescriptor(name="onDemand-Sendungen von ORF.at anschauen", where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=mainORFonDemand)]
