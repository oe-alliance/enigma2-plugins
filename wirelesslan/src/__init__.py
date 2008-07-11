# -*- coding: ISO-8859-1 -*-
#===============================================================================
# WirelessLan Plugin by Reichi
#                   modified by Mladen Horvat 2008
#
# This is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.
#===============================================================================

from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
import os,gettext
PluginLanguageDomain = "WirelessLan"
PluginLanguagePath = "SystemPlugins/WirelessLan/po"

def localeInit():
	lang = language.getLanguage()[:2] # getLanguage returns e.g. "fi_FI" for "language_country"
	os.environ["LANGUAGE"] = lang # Enigma doesn't set this (or LC_ALL, LC_MESSAGES, LANG). gettext needs it!
	print "[WirelessLan] set language to ", lang
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))

def _(txt):
	t = gettext.dgettext(PluginLanguageDomain, txt)
	if t == txt:
		print "[WirelessLan] fallback to default translation for", txt
		t = gettext.gettext(txt)
	return t
	
localeInit()
language.addCallback(localeInit)