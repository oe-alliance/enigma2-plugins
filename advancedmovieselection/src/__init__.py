#from Source.LocaleInit import _

# Andy Blackburn: [Translation] begin
# -*- coding: utf-8 -*-
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
import os, gettext

from skin import loadSkin
loadSkin(resolveFilename(SCOPE_PLUGINS) + "Extensions/AdvancedMovieSelection/skin/skin.xml")

PluginLanguageDomain = "AdvancedMovieSelection"
PluginLanguagePath = "Extensions/AdvancedMovieSelection/locale/"

def localeInit():
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))

def _(txt):
	if gettext.dgettext(PluginLanguageDomain, txt):
		return gettext.dgettext(PluginLanguageDomain, txt)
	else:
		print "[" + PluginLanguageDomain + "] fallback to default translation for " + txt
		return gettext.gettext(txt)

language.addCallback(localeInit())
# Andy Blackburn: [Translation] end
