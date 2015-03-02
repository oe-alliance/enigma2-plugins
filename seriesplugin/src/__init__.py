# -*- coding: utf-8 -*-
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
from os import environ as os_environ
import gettext

def localeInit():
	lang = language.getLanguage()[:2]  # getLanguage returns e.g. "fi_FI" for "language_country"
	os_environ["LANGUAGE"] = lang      # Enigma doesn't set this (or LC_ALL, LC_MESSAGES, LANG). gettext needs it!
	gettext.bindtextdomain("SeriesPlugin", resolveFilename(SCOPE_PLUGINS, "Extensions/SeriesPlugin/locale"))

_ = lambda txt: gettext.dgettext("SeriesPlugin", txt) if txt else ""

localeInit()
language.addCallback(localeInit)
