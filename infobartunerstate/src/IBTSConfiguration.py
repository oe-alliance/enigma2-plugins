#######################################################################
#
#    InfoBar Tuner State for Enigma-2
#    Coded by betonme (c) 2011 <glaserfrank(at)gmail.com>
#    Support: http://www.i-have-a-dreambox.com/wbb2/thread.php?threadid=162629
#
#    This program is free software; you can redistribute it and/or
#    modify it under the terms of the GNU General Public License
#    as published by the Free Software Foundation; either version 2
#    of the License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#######################################################################

# for localized messages
from . import _

# Config
from Components.config import *
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText

from Components.ActionMap import ActionMap
from Screens.Screen import Screen

from Screens.Setup import SetupSummary

# Plugin internal
from InfoBarTunerState import InfoBarTunerState, addExtension, removeExtension, overwriteInfoBar, recoverInfoBar


#######################################################
# Configuration screen
class InfoBarTunerStateConfiguration(Screen, ConfigListScreen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = [ "InfoBarTunerStateConfiguration", "Setup" ]
		
		# Summary
		from Plugins.Extensions.InfoBarTunerState.plugin import NAME, VERSION
		self.setup_title = NAME + " " + _("Configuration") + " " + VERSION
		self.onChangedEntry = []
		
		# Buttons
		self["key_red"] = StaticText(_("Cancel"))
		self["key_green"] = StaticText(_("OK"))
		
		# Define Actions
		self["custom_actions"] = ActionMap(["SetupActions", "ChannelSelectBaseActions"],
		{
			"cancel":				self.keyCancel,
			"save":					self.keySave,
			"nextBouquet":	self.pageUp,
			"prevBouquet":	self.pageDown,
		}, -2) # higher priority
		
		# Initialize Configuration part
		self.list = []
		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changed)
		
		self.config = []
		self.defineConfig()
		self.createConfig()
		
		# Trigger change
		self.changed()

		self.onLayoutFinish.append(self.layoutFinished)

	def defineConfig(self):
		
		separator = "".ljust(250,"-")
		separatorE2Usage = "- E2 "+_("Usage")+" "
		separatorE2Usage = separatorE2Usage.ljust(250-len(separatorE2Usage),"-")
		
#         _config list entry
#         _                                                     , config element
		self.config = [
			#(  _("About")                                             , config.infobartunerstate.about ),
			
			(  _("Enable InfoBarTunerState")                          , config.infobartunerstate.enabled ),
			(  separator                                              , config.infobartunerstate.about ),
			(  _("Add to extension menu")                             , config.infobartunerstate.extensions_menu ),
#			(  _("Pop-Up time in seconds")                            , config.infobartunerstate.popup_time ),
			(  _("Show and hide with InfoBar")                        , config.infobartunerstate.show_infobar ),
			(  _("Show on events")                                    , config.infobartunerstate.show_events ),
			(  _("Show streams")                                      , config.infobartunerstate.show_streams ),
			
			(  _("MoviePlayer integration")                           , config.infobartunerstate.show_overwrite ),
			(  _("Time format")                                       , config.infobartunerstate.time_format ),
			(  _("Number of finished records in list")                , config.infobartunerstate.number_finished_records ),
			(  _("Number of seconds for displaying finished records") , config.infobartunerstate.timeout_finished_records ),
			(  separator                                              , config.infobartunerstate.about ),
		]
		
		for i, configinfobartunerstatefield in enumerate( config.infobartunerstate.fields.dict().itervalues() ):
			self.config.append(
			(  _("Field %d content") % (i)                            , configinfobartunerstatefield )
			)
		
		self.config.extend( [
			(  separator                                              , config.infobartunerstate.about ),
			(  _("Horizontal offset in pixel")                        , config.infobartunerstate.offset_horizontal ),
			(  _("Vertical offset in pixel")                          , config.infobartunerstate.offset_vertical ),
			(  _("Text padding offset in pixel")                      , config.infobartunerstate.offset_padding ),
			(  _("Text spacing offset in pixel")                      , config.infobartunerstate.offset_spacing ),
			(  _("Background transparency")                           , config.infobartunerstate.background_transparency ),
		] )
		
		self.config.extend( [
			(  separatorE2Usage                                       , config.infobartunerstate.about ),
			(  _("Infobar timeout")                                   , config.usage.infobar_timeout ),
			(  _("Show Message when Recording starts")                , config.usage.show_message_when_recording_starts ),
		] )

	def createConfig(self):
		list = []
		for conf in self.config:
			# 0 entry text
			# 1 variable
			# 2 validation
			list.append( getConfigListEntry( conf[0], conf[1]) )
		self.list = list
		self["config"].setList(self.list)

	def layoutFinished(self):
		self.setTitle(self.setup_title)

	def changed(self):
		for x in self.onChangedEntry:
			x()
		#self.createConfig()

	def close(self):
		# Check field configuration
		fieldicon = []
		fieldprogress = []
		text = ""
		for i, c in enumerate( config.infobartunerstate.fields.dict().itervalues() ):
			if c.value == "TypeIcon":
				fieldicon.append( i )
			if c.value == "TimerProgressGraphical":
				fieldprogress.append( i )
		
		if len(fieldicon) > 1:
			text += _("Only one Icon field allowed:") + "\n" \
							+ "\n".join(["Field " + (str(f)) for f in fieldicon])
		
		if len(fieldprogress) > 1:
			if text: text += "\n\n"
			text += _("Only one Graphical Progress field allowed:") + "\n" \
							+ "\n".join(["Field " + (str(f)) for f in fieldprogress])
		
		if text:
			self.session.open(MessageBox, text, MessageBox.TYPE_ERROR, 3)
			return
		
		# Overwrite Screen close function to handle new config
		from Plugins.Extensions.InfoBarTunerState.plugin import gInfoBarTunerState
		global gInfoBarTunerState
		if config.infobartunerstate.enabled.value:
			# Plugin should be enabled
			#TODO use a separate init function similar to the close
			if not gInfoBarTunerState:
				# Plugin is not active - enable it
				gInfoBarTunerState = InfoBarTunerState(self.session)
			
			if gInfoBarTunerState:
				
				# Handle InfoBar overwrite
				if config.infobartunerstate.show_overwrite.value:
					overwriteInfoBar()
				else:
					recoverInfoBar()
				
				# Handle extension menu integration
				if config.infobartunerstate.extensions_menu.value:
					# Add to extension menu
					addExtension()
				else:
					# Remove from extension menu
					removeExtension()
				
				# Handle show with InfoBar
				if config.infobartunerstate.show_infobar.value:
					gInfoBarTunerState.bindInfoBar()
				else:
					gInfoBarTunerState.unbindInfoBar()
				
				#TODO actually not possible to do this, because these events provides the relevant information
				#if config.infobartunerstate.show_events.value:
				#	gInfoBarTunerState.appendEvents()
				#else:
				#	gInfoBarTunerState.removeEvents()
				
				# Remove and append because of show streams handling
				gInfoBarTunerState.removeEvents()
				gInfoBarTunerState.appendEvents()
				
				# Check for actual events
				gInfoBarTunerState.updateRecordTimer()
				if config.infobartunerstate.show_streams.value:
					gInfoBarTunerState.updateStreams()
		else:
			# Plugin should be disabled
			if gInfoBarTunerState:
				# Plugin is active, disable it
				gInfoBarTunerState.close()
		
		# Call baseclass function
		Screen.close(self)

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		return SetupSummary

	def pageUp(self):
		self["config"].instance.moveSelection(self["config"].instance.pageUp)

	def pageDown(self):
		self["config"].instance.moveSelection(self["config"].instance.pageDown)

