# -*- coding: utf-8 -*-
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
import os,gettext

def localeInit():
	if os.path.exists(resolveFilename(SCOPE_PLUGINS, os.path.join(PluginLanguagePath, language.getLanguage()))):
		lang = language.getLanguage()
	else:
		lang = language.getLanguage()[:2]
	os.environ["LANGUAGE"] = lang # Enigma doesn't set this (or LC_ALL, LC_MESSAGES, LANG). gettext needs it!
	gettext.bindtextdomain("3DSettings", resolveFilename(SCOPE_PLUGINS, "SystemPlugins/3DSettings/locale"))

def _(txt):
	t = gettext.dgettext("3DSettings", txt)
	if t == txt:
		print "[3DSettings] fallback to default translation for", txt
		t = gettext.gettext(txt)
	return t

localeInit()
language.addCallback(localeInit)
