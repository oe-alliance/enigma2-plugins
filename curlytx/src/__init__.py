# -*- coding: utf-8 -*-
# CurlyTx translation initialization
# Copyright (C) 2011 Christian Weiske <cweiske@cweiske.de>
# License: GPLv3 or later

from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
import os, gettext

PluginLanguageDomain = "CurlyTx"
PluginLanguagePath = "Extensions/CurlyTx/locale"
 
def localeInit():
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))

def _(txt):
	if gettext.dgettext(PluginLanguageDomain, txt):
		return gettext.dgettext(PluginLanguageDomain, txt)
	else:
		print "[" + PluginLanguageDomain + "] fallback to default translation for " + txt
		return gettext.gettext(txt)

language.addCallback(localeInit())
