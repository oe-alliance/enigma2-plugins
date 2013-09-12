# -*- coding: utf-8 -*-
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
from os import environ as os_environ
import gettext

# Config
from Components.config import config, ConfigSet, ConfigSubsection, ConfigText, ConfigNumber, ConfigYesNo

config.plugins.epgsearch = ConfigSubsection()
config.plugins.epgsearch.history = ConfigSet(choices = [])
# XXX: configtext is more flexible but we cannot use this for a (not yet created) gui config
config.plugins.epgsearch.encoding = ConfigText(default = 'ISO8859-15', fixed_size = False)
config.plugins.epgsearch.history_length = ConfigNumber(default = 10)
config.plugins.epgsearch.add_search_to_epg = ConfigYesNo(default = True)

def localeInit():
	lang = language.getLanguage()[:2] # getLanguage returns e.g. "fi_FI" for "language_country"
	os_environ["LANGUAGE"] = lang # Enigma doesn't set this (or LC_ALL, LC_MESSAGES, LANG). gettext needs it!
	gettext.bindtextdomain("EPGSearch", resolveFilename(SCOPE_PLUGINS, "Extensions/EPGSearch/locale"))

def _(txt):
	t = gettext.dgettext("EPGSearch", txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t

localeInit()
language.addCallback(localeInit)

