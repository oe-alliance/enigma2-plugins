# -*- coding: utf-8 -*-
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
import os,gettext

def localeInit():
	lang = language.getLanguage()[:2] # getLanguage returns e.g. "fi_FI" for "language_country"
	os.environ["LANGUAGE"] = lang # Enigma doesn't set this (or LC_ALL, LC_MESSAGES, LANG). gettext needs it!
	gettext.bindtextdomain("WeatherPlugin", resolveFilename(SCOPE_PLUGINS, "Extensions/WeatherPlugin/locale"))

def _(txt):
	t = gettext.dgettext("WeatherPlugin", txt)
	if t == txt:
		print "[WeatherPlugin] fallback to default translation for", txt
		t = gettext.gettext(txt)
	return t

localeInit()
language.addCallback(localeInit)
