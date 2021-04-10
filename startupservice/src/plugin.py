#
#  StartUpService E2
#
#  $Id$
#
#  Coded by Dr.Best (c) 2009
#  Support: www.dreambox-tools.info
#
#  This plugin is licensed under the Creative Commons 
#  Attribution-NonCommercial-ShareAlike 3.0 Unported 
#  License. To view a copy of this license, visit
#  http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative
#  Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  Alternatively, this plugin may be distributed and executed on hardware which
#  is licensed by Dream Multimedia GmbH.

#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially 
#  distributed other than under the conditions noted above.
#

from Plugins.Plugin import PluginDescriptor
from Components.config import config, ConfigSubsection, ConfigText
from Screens.Screen import Screen
from Screens.ChannelSelection import ChannelContextMenu
from Screens.ChoiceBox import ChoiceBox
from enigma import eServiceReference
from Components.ChoiceList import ChoiceEntryComponent
from Screens.MessageBox import MessageBox
from Tools.BoundFunction import boundFunction

# for localized messages
from . import _

#config for lastservice
config.startupservice = ConfigSubsection()
config.startupservice.lastservice = ConfigText(default="")
config.startupservice.lastroot = ConfigText(default="")
config.startupservice.lastmode = ConfigText(default="tv")
config.startupserviceleavingstandbymode = ConfigSubsection()
config.startupserviceleavingstandbymode.lastservice = ConfigText(default="")
config.startupserviceleavingstandbymode.lastroot = ConfigText(default="")
config.startupserviceleavingstandbymode.lastmode = ConfigText(default="tv")

def leaveStandby():
	if config.startupserviceleavingstandbymode.lastservice.value != "" and config.startupserviceleavingstandbymode.lastroot.value != "":
		from Screens.InfoBar import InfoBar
		if config.startupservice.lastmode.value == "tv":
			InfoBar.instance.servicelist.setModeTv()
		else:
			InfoBar.instance.servicelist.setModeRadio()

def standbyCounterChanged(configElement):
	if config.startupserviceleavingstandbymode.lastservice.value != "" and config.startupserviceleavingstandbymode.lastroot.value != "":
		from Screens.Standby import inStandby
		if inStandby.prev_running_service and (inStandby.prev_running_service.getPath() == "" or inStandby.prev_running_service.getPath()[0] != "/"):
			inStandby.prev_running_service = eServiceReference(config.startupserviceleavingstandbymode.lastservice.value)
			if config.startupserviceleavingstandbymode.lastmode.value == "tv":
				config_last = config.tv
			else:
				config_last = config.radio
			config_last.lastservice.value = config.startupserviceleavingstandbymode.lastservice.value
			config_last.lastroot.value = config.startupserviceleavingstandbymode.lastroot.value
			config_last.save()
			inStandby.onClose.append(leaveStandby)

def main(session, **kwargs):
	# copy startupservice data to config.tv or config.radio if available
	if config.startupservice.lastservice.value != "" and config.startupservice.lastroot.value != "":
		config.servicelist = ConfigSubsection()
		config.servicelist.lastmode = ConfigText(default="tv")
		config.servicelist.lastmode.value = config.startupservice.lastmode.value
		config.servicelist.lastmode.save()
		if config.startupservice.lastmode.value == "tv":
			config.tv = ConfigSubsection()
			config.tv.lastservice = ConfigText()
			config.tv.lastroot = ConfigText()
			config.tv.lastservice.value = config.startupservice.lastservice.value
			config.tv.lastroot.value = config.startupservice.lastroot.value
			config.tv.save()
		else:
			config.radio = ConfigSubsection()
			config.radio.lastservice = ConfigText()
			config.radio.lastroot = ConfigText()
			config.radio.lastservice.value = config.startupservice.lastservice.value
			config.radio.lastroot.value = config.startupservice.lastroot.value
			config.radio.save()
	try:
		startUpServiceInit()
	except:
		pass
	config.misc.standbyCounter.addNotifier(standbyCounterChanged, initial_call=False)

###########################################
# ChannelContextMenu
###########################################
baseChannelContextMenu__init__ = None
def startUpServiceInit():
	global baseChannelContextMenu__init__
	if baseChannelContextMenu__init__ is None:
		baseChannelContextMenu__init__ = ChannelContextMenu.__init__
	ChannelContextMenu.__init__ = startUpService__init__
	# new methods
	ChannelContextMenu.startUpServiceContextMenuCallback = startUpServiceContextMenuCallback
	ChannelContextMenu.startUpServiceMenuCallback = startUpServiceMenuCallback
	ChannelContextMenu.setStartUpService = setStartUpService
	ChannelContextMenu.resetStartUpService = resetStartUpService

def startUpService__init__(self, session, csel):
	baseChannelContextMenu__init__(self, session, csel)
	current = csel.getCurrentSelection()
	current_root = csel.getRoot()
	inBouquetRootList = current_root and current_root.getPath().find('FROM BOUQUET "bouquets.') != -1 #FIXME HACK
	if csel.bouquet_mark_edit == 0 and not csel.movemode:
		if not inBouquetRootList:
			if not (current.flags & (eServiceReference.isMarker|eServiceReference.isDirectory)):
				self["menu"].list.insert(1, ChoiceEntryComponent(text=(_("set as startup service"), boundFunction(self.startUpServiceContextMenuCallback, True))))
				self["menu"].list.insert(2, ChoiceEntryComponent(text=(_("reset startup service"), boundFunction(self.startUpServiceContextMenuCallback, False))))

def startUpServiceContextMenuCallback(self, add):
	if add:
		options = [
				(_("set as startup service after booting..."), boundFunction(self.setStartUpService, config.startupservice)),
				(_("set as startup service after leaving standby mode..."), boundFunction(self.setStartUpService, config.startupserviceleavingstandbymode)),
			]
	else:
		options = [
				(_("reset startup service for booting..."), boundFunction(self.resetStartUpService, config.startupservice)),
				(_("reset startup service for leaving standby mode..."), boundFunction(self.resetStartUpService, config.startupserviceleavingstandbymode)),
			]
	self.session.openWithCallback(self.startUpServiceMenuCallback, ChoiceBox, list=options)

def startUpServiceMenuCallback(self, ret):
	ret and ret[1]()


def setStartUpService(self, configElement):
	current = self.csel.getCurrentSelection()
	path = ''
	for i in self.csel.servicePath:
		 path += i.toString()
		 path += ';'
	if path:
		if current.type == eServiceReference.idDVB and current.getData(0) in (2, 10):	
			configElement.lastroot.value = path
			configElement.lastmode.value = "radio"
		else:
			configElement.lastroot.value = path
			configElement.lastmode.value = "tv"
		configElement.lastservice.value = current.toString()
		configElement.save()
		self.close()
	else:
		 self.session.openWithCallback(self.close, MessageBox, _("If you see this message, please switch to the service you want to mark as startservice and try again."), MessageBox.TYPE_ERROR)

def resetStartUpService(self, configElement):
	configElement.lastroot.value = ""
	configElement.lastmode.value = "tv"
	configElement.lastservice.value = ""
	configElement.save()
	self.close()

def Plugins(**kwargs):
	return [PluginDescriptor(name="StartUpService", description="set startup service", where=PluginDescriptor.WHERE_SESSIONSTART, fnc=main)]

