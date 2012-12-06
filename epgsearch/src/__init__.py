# -*- coding: utf-8 -*-
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
import os, gettext

# Config
from Components.config import config, ConfigSet, ConfigSubsection, ConfigSelection, ConfigNumber, ConfigYesNo

config.plugins.epgsearch = ConfigSubsection()
config.plugins.epgsearch.showinplugins = ConfigYesNo(default = False)
config.plugins.epgsearch.history = ConfigSet(choices = [])
# XXX: configtext is more flexible but we cannot use this for a (not yet created) gui config
config.plugins.epgsearch.encoding = ConfigSelection(choices = ['UTF-8', 'ISO8859-15'], default = 'ISO8859-15')
config.plugins.epgsearch.history_length = ConfigNumber(default = 10)
config.plugins.epgsearch.add_search_to_epg = ConfigYesNo(default = True)

PluginLanguageDomain = "EPGSearch"
PluginLanguagePath = "Extensions/EPGSearch/locale"

def localeInit():
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))

def _(txt):
	if gettext.dgettext(PluginLanguageDomain, txt):
		return gettext.dgettext(PluginLanguageDomain, txt)
	else:
		print "[" + PluginLanguageDomain + "] fallback to default translation for " + txt
		return gettext.gettext(txt)

language.addCallback(localeInit())
