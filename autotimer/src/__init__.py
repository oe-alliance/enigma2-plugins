# -*- coding: utf-8 -*-
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
from os import environ as os_environ
import gettext

# Config
from Components.config import config, ConfigSubsection, ConfigEnableDisable, \
	ConfigNumber, ConfigSelection, ConfigYesNo

config.plugins.autotimer = ConfigSubsection()
config.plugins.autotimer.autopoll = ConfigEnableDisable(default=False)
config.plugins.autotimer.interval = ConfigNumber(default=3)
config.plugins.autotimer.refresh = ConfigSelection(choices=[
		("none", _("None")),
		("auto", _("Only AutoTimers created during this session")),
		("all", _("All non-repeating timers"))
	], default="none"
)
config.plugins.autotimer.try_guessing = ConfigEnableDisable(default=True)
config.plugins.autotimer.editor = ConfigSelection(choices=[
		("plain", _("Classic")),
		("wizard", _("Wizard"))
	], default="wizard"
)
config.plugins.autotimer.addsimilar_on_conflict = ConfigEnableDisable(default=False)
config.plugins.autotimer.add_autotimer_to_tags = ConfigYesNo(default=False)
config.plugins.autotimer.add_name_to_tags = ConfigYesNo(default=False)
config.plugins.autotimer.disabled_on_conflict = ConfigEnableDisable(default=False)
config.plugins.autotimer.show_in_extensionsmenu = ConfigYesNo(default=False)
config.plugins.autotimer.fastscan = ConfigYesNo(default=False)
config.plugins.autotimer.notifconflict = ConfigYesNo(default=True)
config.plugins.autotimer.notifsimilar = ConfigYesNo(default=True)
config.plugins.autotimer.maxdaysinfuture = ConfigNumber(default=0)
config.plugins.autotimer.show_help = ConfigYesNo(default=True)
config.plugins.autotimer.skip_during_records = ConfigYesNo(default=False)

def localeInit():
	lang = language.getLanguage()[:2] # getLanguage returns e.g. "fi_FI" for "language_country"
	os_environ["LANGUAGE"] = lang # Enigma doesn't set this (or LC_ALL, LC_MESSAGES, LANG). gettext needs it!
	gettext.bindtextdomain("AutoTimer", resolveFilename(SCOPE_PLUGINS, "Extensions/AutoTimer/locale"))

def _(txt):
	t = gettext.dgettext("AutoTimer", txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t

localeInit()
language.addCallback(localeInit)

try:
	xrange = xrange
	iteritems = lambda d: d.iteritems()
	itervalues = lambda d: d.itervalues()
except NameError:
	xrange = range
	iteritems = lambda d: d.items()
	itervalues = lambda d: d.values()

__all__ = ['_', 'config', 'iteritems', 'itervalues', 'xrange']
