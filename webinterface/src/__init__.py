import Plugins.Plugin
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
import gettext
from functools import reduce


__version__ = "1.9.0"

PluginLanguageDomain = "WebInterface"
PluginLanguagePath = "Extensions/WebInterface/locale"


def localeInit():
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


def _(txt):
	t = gettext.dgettext(PluginLanguageDomain, txt)
	if t == txt:
		print("[%s] fallback to default translation for %s" % (PluginLanguageDomain, txt))
		t = gettext.gettext(txt)
	return t

localeInit()
language.addCallback(localeInit)
