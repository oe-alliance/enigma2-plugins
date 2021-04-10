# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import absolute_import
import os
import sys
import traceback

# Localization
from . import _

from Components.config import config

# Plugin internal
from .Logger import log


#######################################################
# Override ChannelContextMenu
ChannelContextMenu__init__ = None
def SPChannelContextMenuInit():
	print("[SeriesPlugin] override ChannelContextMenu.__init__")
	global ChannelContextMenu__init__
	if ChannelContextMenu__init__ is None:
		from Screens.ChannelSelection import ChannelContextMenu
		ChannelContextMenu__init__ = ChannelContextMenu.__init__
		ChannelContextMenu.__init__ = SPChannelContextMenu__init__
		ChannelContextMenu.SPchannelShowSeriesInfo = channelShowSeriesInfo
		ChannelContextMenu.SPcloseafterfinish = closeafterfinish

def SPChannelContextMenuUndo():
	print("[SeriesPlugin] override ChannelContextMenu.__init__")
	global ChannelContextMenu__init__
	if ChannelContextMenu__init__:
		from Screens.ChannelSelection import ChannelContextMenu
		ChannelContextMenu.__init__ = ChannelContextMenu__init__
		ChannelContextMenu__init__ = None

def SPChannelContextMenu__init__(self, session, csel):
	from Components.ChoiceList import ChoiceEntryComponent
	from Screens.ChannelSelection import MODE_TV
	from Tools.BoundFunction import boundFunction
	from enigma import eServiceReference
	ChannelContextMenu__init__(self, session, csel)
	current = csel.getCurrentSelection()
	current_sel_path = current.getPath()
	current_sel_flags = current.flags
	if csel.mode == MODE_TV and not (current_sel_path or current_sel_flags & (eServiceReference.isDirectory | eServiceReference.isMarker)):
		from Plugins.Extensions.SeriesPlugin.plugin import SHOWINFO
		self["menu"].list.insert(0, ChoiceEntryComponent(text=(SHOWINFO, boundFunction(self.SPchannelShowSeriesInfo))))

def channelShowSeriesInfo(self):
	log.debug("[SeriesPlugin] channelShowSeriesInfo ")
	if config.plugins.seriesplugin.enabled.value:
		try:
			from enigma import eServiceCenter
			service = self.csel.servicelist.getCurrent()
			info = eServiceCenter.getInstance().info(service)
			event = info.getEvent(service)
			from Plugins.Extensions.SeriesPlugin.SeriesPluginInfoScreen import SeriesPluginInfoScreen
			self.session.openWithCallback(self.SPcloseafterfinish, SeriesPluginInfoScreen, service, event)
		except Exception as e:
			log.debug(_("SeriesPlugin info exception ") + str(e))

def closeafterfinish(self, retval=None):
	self.close()

