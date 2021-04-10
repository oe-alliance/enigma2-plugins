from __future__ import absolute_import
#
#  Birthday Reminder E2 Plugin
#
#  $Id: plugin.py,v 1.0 2011-08-29 00:00:00 Shaderman Exp $
#
#  Coded by Shaderman (c) 2011
#  plugin.png by Sakartvelo with images from BazaarDesigns.com
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


# OWN IMPORTS
from .BirthdayReminder import BirthdayReminder, BirthdayReminderSettings
from .BirthdayTimer import BirthdayTimer

# ENIGMA IMPORTS
from Components.config import config, ConfigSubsection, ConfigText, ConfigSelection, ConfigYesNo, NoSave, ConfigClock, ConfigInteger
from Components.PluginComponent import plugins
from Plugins.Plugin import PluginDescriptor

# for localized messages
from . import _


config.plugins.birthdayreminder = ConfigSubsection()
config.plugins.birthdayreminder.file = ConfigText(default="/etc/enigma2/birthdayreminder")
config.plugins.birthdayreminder.dateFormat = ConfigSelection(default="ddmmyyyy", choices=[("ddmmyyyy", "DD.MM.YYYY"), ("mmddyyyy", "MM/DD/YYYY")])
config.plugins.birthdayreminder.broadcasts = ConfigYesNo(default=True)
config.plugins.birthdayreminder.preremind = ConfigSelection(default="7", choices=[("-1", _("Disabled")), ("1", _("1 day")), ("3", _("3 days")), ("7", _("1 week"))])
config.plugins.birthdayreminder.preremindChanged = NoSave(ConfigYesNo(default=False))
config.plugins.birthdayreminder.notificationTime = ConfigClock(default=64800) # 19:00
config.plugins.birthdayreminder.notificationTimeChanged = NoSave(ConfigYesNo(default=False))
config.plugins.birthdayreminder.sortby = ConfigSelection(default="1", choices=[
				("1", _("Name")),
				("2", _("Next birthday")),
				("3", _("Age"))
				])
config.plugins.birthdayreminder.showInExtensions = ConfigYesNo(default=False)
config.plugins.birthdayreminder.broadcastPort = ConfigInteger(default=7374, limits=(1024, 49151))


birthdaytimer = BirthdayTimer()


def settings(session, **kwargs):
	session.open(BirthdayReminderSettings, birthdaytimer)
	

def autostart(reason, **kwargs):
	if reason == 1:
		birthdaytimer.stop()
		

def main(session, **kwargs):
	session.open(BirthdayReminder, birthdaytimer)
	

def Plugins(**kwargs):
	list = []
	list.append(PluginDescriptor(where=[PluginDescriptor.WHERE_AUTOSTART, PluginDescriptor.WHERE_SESSIONSTART], fnc=autostart))
	list.append(PluginDescriptor(name="Birthday Reminder", description=_("Helps to remind of birthdays"), where=PluginDescriptor.WHERE_PLUGINMENU, icon="plugin.png", fnc=settings))
	if config.plugins.birthdayreminder.showInExtensions.value:
            list.append(PluginDescriptor(name="Birthday Reminder", description=_("Helps to remind of birthdays"), where=[PluginDescriptor.WHERE_EXTENSIONSMENU, PluginDescriptor.WHERE_EVENTINFO], fnc=main))
	return list
	
