##
## ORF.at streaming modules
## by AliAbdul
##
from ORFIPTV import ORFMain as ORFIPTVMain
from ORFonDemand import ORFMain as ORFonDemandMain
from Plugins.Plugin import PluginDescriptor

####################################################

def main(session, **kwargs):
	session.open(ORFIPTVMain)

def Plugins(**kwargs):
	return PluginDescriptor(name="ORF.at IPTV", description="IPTV-Sendungen von ORF.at anschauen", where=[PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_PLUGINMENU], icon="orf.png", fnc=main)
