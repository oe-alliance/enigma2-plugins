#
#  StartUpService E2
#
#  $Id$
#
#  Coded by Dr.Best (c) 2009
#  Support: www.dreambox-tools.info
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#

from Plugins.Plugin import PluginDescriptor
from Components.config import config, ConfigSubsection, ConfigText
from Screens.Screen import Screen
from Screens.ChannelSelection import ChannelContextMenu
from enigma import eServiceReference
from Components.ChoiceList import ChoiceEntryComponent
from Screens.MessageBox import MessageBox

# for localized messages
from . import _

#config for lastservice
config.startupservice = ConfigSubsection()
config.startupservice.lastservice = ConfigText(default = "")
config.startupservice.lastroot = ConfigText(default = "")
config.startupservice.lastmode = ConfigText(default = "tv")

def main(session, **kwargs):
	# copy startupservice data to config.tv or config.radio if available
	if config.startupservice.lastservice.value != "" and config.startupservice.lastroot.value != "":
		config.servicelist = ConfigSubsection()
		config.servicelist.lastmode = ConfigText(default = "tv")
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
	try: startUpServiceInit()
	except: pass

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
	ChannelContextMenu.newStartUpServiceSelected = newStartUpServiceSelected
	ChannelContextMenu.resetStartUpService = resetStartUpService

def startUpService__init__(self, session, csel):
	baseChannelContextMenu__init__(self, session, csel)
	current = csel.getCurrentSelection()
	current_root = csel.getRoot()
	inBouquetRootList = current_root and current_root.getPath().find('FROM BOUQUET "bouquets.') != -1 #FIXME HACK
	if csel.bouquet_mark_edit == 0 and not csel.movemode:
		if not inBouquetRootList:
			if not (current.flags & (eServiceReference.isMarker|eServiceReference.isDirectory)):
				self["menu"].list.insert(1, ChoiceEntryComponent(text = (_("set as startup service"), self.newStartUpServiceSelected)))
				self["menu"].list.insert(2, ChoiceEntryComponent(text = (_("reset startup service"), self.resetStartUpService)))

def newStartUpServiceSelected(self):
	current = self.csel.getCurrentSelection()
	path = ''
	for i in self.csel.servicePath:
		 path += i.toString()
		 path += ';'
	if path:
		if current.type == eServiceReference.idDVB and current.getData(0) in (2, 10):	
			config.startupservice.lastroot.value = path
			config.startupservice.lastmode.value = "radio"
		else:
			config.startupservice.lastroot.value = path
			config.startupservice.lastmode.value = "tv"
		config.startupservice.lastservice.value = current.toString()
		config.startupservice.save()
		self.close()
	else:
		 self.session.openWithCallback(self.close, MessageBox, _("If you see this message, please switch to the service you want to mark as startservice and try again."), MessageBox.TYPE_ERROR)

def resetStartUpService(self):
	config.startupservice.lastroot.value = ""
	config.startupservice.lastmode.value = "tv"
	config.startupservice.lastservice.value = ""
	config.startupservice.save()
	self.close()

def Plugins(**kwargs):
	return [PluginDescriptor(name="StartUpService", description="set startup service", where = PluginDescriptor.WHERE_SESSIONSTART, fnc=main)]

