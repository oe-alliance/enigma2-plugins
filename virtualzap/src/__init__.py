# -*- coding: utf-8 -*-
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
from os import environ as os_environ
import gettext

def localeInit():
	if os.path.exists(resolveFilename(SCOPE_PLUGINS, os.path.join(PluginLanguagePath, language.getLanguage()))):
		lang = language.getLanguage()
	else:
		lang = language.getLanguage()[:2]
	os_environ["LANGUAGE"] = lang # Enigma doesn't set this (or LC_ALL, LC_MESSAGES, LANG). gettext needs it!
	gettext.bindtextdomain("VirtualZap", resolveFilename(SCOPE_PLUGINS, "Extensions/VirtualZap/locale"))

def _(txt):
	t = gettext.dgettext("VirtualZap", txt)
	if t == txt:
		print "[VirtualZap] fallback to default translation for", txt
		t = gettext.gettext(txt)
	return t

localeInit()
language.addCallback(localeInit)

