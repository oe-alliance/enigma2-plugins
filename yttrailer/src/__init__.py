from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
import gettext
from functools import reduce


PluginLanguageDomain = "YTTrailer"
PluginLanguagePath = "Extensions/YTTrailer/locale"


def localeInit():
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


def _(txt):
	if gettext.dgettext(PluginLanguageDomain, txt):
		return gettext.dgettext(PluginLanguageDomain, txt)
	else:
		print("[%s] fallback to default translation for %s" % (PluginLanguageDomain, txt))
		return gettext.gettext(txt)


localeInit()
language.addCallback(localeInit)


def read_random():
	fd = open("/dev/urandom", "r")
	buf = fd.read(8)
	fd.close()
	return buf


__version__ = "1.0"
