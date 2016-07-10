# -*- coding: utf-8 -*-
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
from boxbranding import getImageDistro
import os, gettext

# Config
from Components.config import config, ConfigSet, ConfigSubsection, ConfigSelection, ConfigNumber, ConfigYesNo

config.plugins.epgsearch = ConfigSubsection()
config.plugins.epgsearch.showinplugins = ConfigYesNo(default = False)
__searchDefaultScope = "currentbouquet" if getImageDistro() in ("easy-gui-aus", "beyonwiz") else "all"
config.plugins.epgsearch.scope = ConfigSelection(choices=[("all", _("all services")), ("allbouquets", _("all bouquets")), ("currentbouquet", _("current bouquet")), ("currentservice", _("current service")), ("ask", _("ask user"))], default=__searchDefaultScope)
config.plugins.epgsearch.defaultscope = ConfigSelection(choices=[("all", _("all services")), ("allbouquets", _("all bouquets")), ("currentbouquet", _("current bouquet")), ("currentservice", _("current service"))], default=__searchDefaultScope)
config.plugins.epgsearch.history = ConfigSet(choices = [])
# XXX: configtext is more flexible but we cannot use this for a (not yet created) gui config
config.plugins.epgsearch.encoding = ConfigSelection(choices = ['UTF-8', 'ISO8859-15'], default = 'UTF-8')
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
