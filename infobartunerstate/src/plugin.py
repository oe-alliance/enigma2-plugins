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

# Plugin
from Plugins.Plugin import PluginDescriptor

# MessageBox
from Screens.MessageBox import MessageBox

# Plugin internal
from IBTSConfiguration import InfoBarTunerStateConfiguration
from InfoBarTunerState import InfoBarTunerState, TunerStateInfo


# Contants
NAME = _("InfoBar Tuner State") 
DESCRIPTION = _("Show InfoBar Tuner State")
VERSION = "V0.9.3"
#TODO About


# Globals
gInfoBarTunerState = None


# Config choices
field_choices = [	
									("TypeIcon",								_("Type (Icon)")),
									("TypeText",								_("Type (Text)")),
									("Tuner",										_("Tuner")),
									("TunerType",								_("Tuner Type")),
									("Number",									_("Channel Number")),
									("Channel",									_("Channel Name")),
									("Name",										_("Name")),
									("TimeLeftDuration",				_("Time Left / Duration")),
									("TimeLeft",								_("Time Left")),
									("TimeElapsed",							_("Time Elapsed")),
									("Begin",										_("Begin")),
									("End",											_("End")),
									("Duration",								_("Duration")),
									("TimerProgressGraphical",	_("Timer Progress (Graphical)")),  #TODO howto do for file streams
									("TimerProgressText",				_("Timer Progress (Text)")),  #TODO howto do for file streams
									("TimerDestination",				_("Destination")),		#TODO howto do for file streams
									("StreamClient",						_("Stream Client")),
									("StreamClientPort",				_("Stream Client with Port")),
									("DestinationStreamClient",	_("Destination / Client")),
									#Throughput
									#Overall transfer
									("FileSize",								_("File Size")),
									("FreeSpace",								_("Free Space")),
									("None",										_("None")),
								]

date_choices = [	
									("%H:%M",							_("HH:MM")),
									("%d.%m %H:%M",				_("DD.MM HH:MM")),
									("%m/%d %H:%M",				_("MM/DD HH:MM")),
									("%d.%m.%Y %H:%M",		_("DD.MM.YYYY HH:MM")),
									("%Y/%m/%d %H:%M",		_("YYYY/MM/DD HH:MM")),
									("%H:%M %d.%m",				_("HH:MM DD.MM")),
									("%H:%M %m/%d",				_("HH:MM MM/DD")),
									("%H:%M %d.%m.%Y",		_("HH:MM DD.MM.YYYY")),
									("%H:%M %Y/%m/%d",		_("HH:MM YYYY/MM/DD")),
								]

# Config options
config.infobartunerstate                           = ConfigSubsection()

config.infobartunerstate.about                     = ConfigNothing()
config.infobartunerstate.enabled                   = ConfigEnableDisable(default = True)
config.infobartunerstate.extensions_menu           = ConfigYesNo(default = True)
#config.infobartunerstate.popup_time                = ConfigSelectionNumber(0, 10, 1, default = 5)
#Todo item enabler
#Show records
#Show streams

config.infobartunerstate.show_infobar              = ConfigYesNo(default = True)
config.infobartunerstate.show_events               = ConfigYesNo(default = True)		#TODO Show on start, end, start/end
config.infobartunerstate.show_streams              = ConfigYesNo(default = True)
config.infobartunerstate.show_overwrite            = ConfigYesNo(default = False)		# Show with MoviePlayer only is actually not possible

config.infobartunerstate.time_format               = ConfigSelection(default = "%H:%M", choices = date_choices)
config.infobartunerstate.number_finished_records   = ConfigSelectionNumber(0, 10, 1, default = 5)
config.infobartunerstate.timeout_finished_records  = ConfigSelectionNumber(0, 600, 10, default = 60)

config.infobartunerstate.fields                    = ConfigSubsection()
config.infobartunerstate.fields.a                  = ConfigSelection(default = "TypeIcon", choices = field_choices)
config.infobartunerstate.fields.b                  = ConfigSelection(default = "Tuner", choices = field_choices)
config.infobartunerstate.fields.c                  = ConfigSelection(default = "Number", choices = field_choices)
config.infobartunerstate.fields.d                  = ConfigSelection(default = "Channel", choices = field_choices)
config.infobartunerstate.fields.e                  = ConfigSelection(default = "Name", choices = field_choices)
config.infobartunerstate.fields.f                  = ConfigSelection(default = "TimerProgressGraphical", choices = field_choices)
config.infobartunerstate.fields.g                  = ConfigSelection(default = "TimeLeftDuration", choices = field_choices)
config.infobartunerstate.fields.h                  = ConfigSelection(default = "StreamClient", choices = field_choices)
config.infobartunerstate.fields.i                  = ConfigSelection(default = "None", choices = field_choices)
config.infobartunerstate.fields.j                  = ConfigSelection(default = "None", choices = field_choices)

config.infobartunerstate.offset_horizontal         = ConfigSelectionNumber(-1000, 1000, 1, default = 0)
config.infobartunerstate.offset_vertical           = ConfigSelectionNumber(-1000, 1000, 1, default = 0)
config.infobartunerstate.offset_padding            = ConfigSelectionNumber(-1000, 1000, 1, default = 0)
config.infobartunerstate.offset_spacing            = ConfigSelectionNumber(-1000, 1000, 1, default = 0)

config.infobartunerstate.background_transparency   = ConfigYesNo(default = False)


#######################################################
# Plugin main function
def Plugins(**kwargs):
	#TODO localeInit()
	
	descriptors = []
	
	if config.infobartunerstate.enabled.value:
		# AutoStart and SessionStart
		descriptors.append( PluginDescriptor(where = PluginDescriptor.WHERE_AUTOSTART, fnc = start, needsRestart = False) )
		descriptors.append( PluginDescriptor(where = PluginDescriptor.WHERE_SESSIONSTART, fnc = start, needsRestart = False) )
		if config.infobartunerstate.extensions_menu.value:
			descriptors.append( PluginDescriptor(name = NAME, description = DESCRIPTION, where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc = extension, needsRestart = False) )
	
	#TODO icon
	descriptors.append( PluginDescriptor(name = NAME, description = NAME + " " +_("configuration"), where = PluginDescriptor.WHERE_PLUGINMENU, fnc = setup, needsRestart = False) ) #icon = "/icon.png"

	return descriptors


#######################################################
# Plugin # Plugin configuration
def setup(session, **kwargs):
	#TODO config
	# Overwrite Skin Position
	# Show Live TV Tuners PiP LiveStream FileStream
	# alltime permanent display, needs an dynamic update service
	# Always display at least Nothing running
	# show free tuner with dvb-type
	# Used disk size
	# Event popup timeout
	# Feldbreitenbegrenzung fuer Namen ...
	# Streaming amount of data
	# Display next x timers also if deactivated
	try:
		session.open(InfoBarTunerStateConfiguration)
	except Exception, e:
		print "InfoBarTunerStateMenu exception " + str(e)


#######################################################
# Autostart and Sessionstart
def start(reason, **kwargs):
	#print "InfoBarTunerState autostart "
	#print str(reason)
	#print str(kwargs)
	if reason == 0: # start
		if kwargs.has_key("session"):
			if config.infobartunerstate.enabled.value:
				global gInfoBarTunerState
				session = kwargs["session"]
				gInfoBarTunerState = InfoBarTunerState(session)


#######################################################
# Extension Menu
def extension(session, **kwargs):
	global gInfoBarTunerState
	if gInfoBarTunerState:
		if gInfoBarTunerState.entries:
			# There are active entries
			gInfoBarTunerState.show(True)
		else:
			# No entries available
			gInfoBarTunerState.info = gInfoBarTunerState.session.instantiateDialog( TunerStateInfo, _("Nothing running") )
			gInfoBarTunerState.info.show()
	else:
		# No InfoBarTunerState Instance running
		session.open(MessageBox, _("InfoBarTunerState is disabled"), MessageBox.TYPE_INFO, 3)

