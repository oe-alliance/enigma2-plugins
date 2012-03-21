#######################################################################
#
#    Push Service for Enigma-2
#    Coded by betonme (c) 2012 <glaserfrank(at)gmail.com>
#    Support: http://www.i-have-a-dreambox.com/wbb2/thread.php?threadid=167779
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

# Plugin
from Plugins.Plugin import PluginDescriptor

# Config
from Components.config import *

# Default encoding
#from Components.Language import language

# Plugin internal
from __init__ import *
from PushService import PushService
from PushServiceConfigScreen import PushServiceConfigScreen
#from PluginBase import PluginBase
#from ConfigDirectorySelection import ConfigDirectorySelection


# Constants
NAME = "PushService"
VERSION = "0.1.2"
SUPPORT = "http://www.i-have-a-dreambox.com/wbb2/thread.php?threadid=167779"
DONATE = "http://bit.ly/pspaypal"
ABOUT = "\n  " + NAME + " " + VERSION + "\n\n" \
				+ _("  (C) 2012 by betonme @ IHAD \n\n") \
				+ _("  If You like this plugin and want to support it,\n") \
				+ _("  or if just want to say ''thanks'',\n") \
				+ _("  feel free to donate via PayPal. \n\n") \
				+ _("  Thanks a lot ! \n\n  PayPal: ") + DONATE


# Globals
gPushService = None


# Config options
config.pushservice                           = ConfigSubsection()

config.pushservice.about                     = ConfigNothing()

config.pushservice.enable                    = ConfigEnableDisable(default = True)

config.pushservice.boxname                   = ConfigText(default = "Dreambox", fixed_size = False)
config.pushservice.xmlpath                   = ConfigText(default = "/etc/enigma2/pushservice.xml", fixed_size = False)

config.pushservice.time                      = ConfigClock(default = 0)
config.pushservice.period                    = ConfigSelectionNumber(0, 1000, 1, default = 24)
config.pushservice.runonboot                 = ConfigEnableDisable(default = True)

config.pushservice.smtpserver                = ConfigText(default="smtp.server.com", fixed_size = False)
config.pushservice.smtpport                  = ConfigNumber(default = 587)
config.pushservice.smtpssl                   = ConfigEnableDisable(default = True)
config.pushservice.smtptls                   = ConfigEnableDisable(default = True)

config.pushservice.username                  = ConfigText(fixed_size = False)
config.pushservice.password                  = ConfigPassword()

config.pushservice.mailfrom                  = ConfigText(default = "abc@provider.com", fixed_size = False)
config.pushservice.mailto                    = ConfigText(fixed_size = False)


#######################################################
# Plugin main function
def Plugins(**kwargs):
	localeInit()
	
	descriptors = []
	
	if config.pushservice.enable.value:
		# AutoStart
		descriptors.append( PluginDescriptor(where = PluginDescriptor.WHERE_AUTOSTART, fnc = autostart, needsRestart = False) )
		
	#TODO icon
	descriptors.append( PluginDescriptor(name = NAME, description = NAME + " " +_("configuration"), where = PluginDescriptor.WHERE_PLUGINMENU, fnc = setup, needsRestart = False) ) #icon = "/icon.png"

	return descriptors


#######################################################
# Plugin configuration
def setup(session, **kwargs):
	session.open(PushServiceConfigScreen)


#######################################################
# Autostart
def autostart(reason, **kwargs):
	if reason == 0:  # start
		if config.pushservice.enable.value:
			global gPushService
			gPushService = PushService()
			#TODO gPushService.load()
			state = None
			if config.pushservice.runonboot.value:
				state = "Boot"
			gPushService.start(state) #with load

