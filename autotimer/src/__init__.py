# -*- coding: utf-8 -*-
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
import os, gettext

from boxbranding import getImageDistro

# Config
from Components.config import config, ConfigSubsection, ConfigEnableDisable, \
	ConfigNumber, ConfigSelection, ConfigYesNo

PluginLanguageDomain = "AutoTimer"
PluginLanguagePath = "Extensions/AutoTimer/locale"
 
def localeInit():
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))

def _(txt):
	if gettext.dgettext(PluginLanguageDomain, txt):
		return gettext.dgettext(PluginLanguageDomain, txt)
	else:
		print "[" + PluginLanguageDomain + "] fallback to default translation for " + txt
		return gettext.gettext(txt)

language.addCallback(localeInit())

config.plugins.autotimer = ConfigSubsection()
config.plugins.autotimer.autopoll = ConfigEnableDisable(default=True)
config.plugins.autotimer.onlyinstandby = ConfigEnableDisable(default=False)
config.plugins.autotimer.delay = ConfigNumber(default=3)
if getImageDistro() in ('openmips', 'openatv'):
	config.plugins.autotimer.interval = ConfigNumber(default=240)
else:
	config.plugins.autotimer.interval = ConfigNumber(default=30)
config.plugins.autotimer.refresh = ConfigSelection(choices=[
		("none", _("None")),
		("auto", _("Only AutoTimers created during this session")),
		("all", _("All non-repeating timers"))
	], default = "all"
)
config.plugins.autotimer.try_guessing = ConfigEnableDisable(default=True)
config.plugins.autotimer.editor = ConfigSelection(choices=[
		("plain", _("Classic")),
		("wizard", _("Wizard"))
	], default = "plain"
)
config.plugins.autotimer.addsimilar_on_conflict = ConfigEnableDisable(default=False)
config.plugins.autotimer.add_autotimer_to_tags = ConfigYesNo(default=False)
config.plugins.autotimer.add_name_to_tags = ConfigYesNo(default=False)
config.plugins.autotimer.disabled_on_conflict = ConfigEnableDisable(default=False)
config.plugins.autotimer.show_in_plugins = ConfigYesNo(default=False)
config.plugins.autotimer.show_in_extensionsmenu = ConfigYesNo(default=False)
config.plugins.autotimer.fastscan = ConfigYesNo(default=False)
config.plugins.autotimer.notifconflict = ConfigYesNo(default=True)
config.plugins.autotimer.notifsimilar = ConfigYesNo(default=True)
config.plugins.autotimer.maxdaysinfuture = ConfigNumber(default=0)
config.plugins.autotimer.show_help = ConfigYesNo(default=True)
config.plugins.autotimer.skip_during_records = ConfigYesNo(default=False)

try:
	xrange = xrange
	iteritems = lambda d: d.iteritems()
	itervalues = lambda d: d.itervalues()
except NameError:
	xrange = range
	iteritems = lambda d: d.items()
	itervalues = lambda d: d.values()

__all__ = ['_', 'config', 'iteritems', 'itervalues', 'xrange']
