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
# Override EPGSelection enterDateTime
EPGSelection_enterDateTime = None
#EPGSelection_openOutdatedEPGSelection = None


def SPEPGSelectionInit():
	print("[SeriesPlugin] override EPGSelection")
	global EPGSelection_enterDateTime  # , EPGSelection_openOutdatedEPGSelection
	if EPGSelection_enterDateTime is None:  # and EPGSelection_openOutdatedEPGSelection is None:
		from Screens.EpgSelection import EPGSelection
		EPGSelection_enterDateTime = EPGSelection.enterDateTime
		EPGSelection.enterDateTime = enterDateTime
		#EPGSelection_openOutdatedEPGSelection = EPGSelection.openOutdatedEPGSelection
		#EPGSelection.openOutdatedEPGSelection = openOutdatedEPGSelection
		EPGSelection.SPcloseafterfinish = closeafterfinish


def SPEPGSelectionUndo():
	print("[SeriesPlugin] undo override EPGSelection")
	global EPGSelection_enterDateTime  # , EPGSelection_openOutdatedEPGSelection
	if EPGSelection_enterDateTime:  # and EPGSelection_openOutdatedEPGSelection:
		from Screens.EpgSelection import EPGSelection
		EPGSelection.enterDateTime = EPGSelection_enterDateTime
		EPGSelection_enterDateTime = None
		#EPGSelection.openOutdatedEPGSelection = EPGSelection_openOutdatedEPGSelection
		#EPGSelection_openOutdatedEPGSelection = None


def enterDateTime(self):
	from Screens.EpgSelection import EPG_TYPE_SINGLE, EPG_TYPE_MULTI, EPG_TYPE_SIMILAR
	event = self["Event"].event
	if self.type == EPG_TYPE_SINGLE:
		service = self.currentService
	elif self.type == EPG_TYPE_MULTI:
		service = self.services
	elif self.type == EPG_TYPE_SIMILAR:
		service = self.currentService
	if service and event:
		from Plugins.Extensions.SeriesPlugin.SeriesPluginInfoScreen import SeriesPluginInfoScreen
		self.session.openWithCallback(self.SPcloseafterfinish, SeriesPluginInfoScreen, service, event)
		return
	EPGSelection_enterDateTime(self)

#def openOutdatedEPGSelection(self, reason=None):
#	if reason == 1:
#		EPGSelection_enterDateTime(self)


def closeafterfinish(self, retval=None):
	self.close()
