# -*- coding: utf-8 -*-
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
from os import environ as os_environ
import gettext

PluginLanguageDomain = "EPGBackup"
PluginLanguagePath = "Extensions/EPGBackup/locale"
# Fallback to EN for Code-Strings
DefaultPluginLang = "EN"

def localeInit():
	lang = language.getLanguage()[:2] # getLanguage returns e.g. "fi_FI" for "language_country"
	os_environ["LANGUAGE"] = lang # Enigma doesn't set this (or LC_ALL, LC_MESSAGES, LANG). gettext needs it!
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))

def _(txt):
	t = gettext.dgettext(PluginLanguageDomain, txt)
	if t == txt:
		t = getDefaultTxt(txt)
		if t == txt:
			t = gettext.gettext(txt)
	return t

def getDefaultTxt(txt):
	lang = language.getLanguage()[:2]
	os_environ["LANGUAGE"] = DefaultPluginLang
	t = gettext.dgettext(PluginLanguageDomain, txt)
	os_environ["LANGUAGE"] = lang
	return t

localeInit()
language.addCallback(localeInit)
