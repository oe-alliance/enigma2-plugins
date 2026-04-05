from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
import gettext

PluginLanguageDomain = "NameZap"
PluginLanguagePath = "Extensions/NameZap/locale"


def localeInit():
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


def _(txt):
	translated = gettext.dgettext(PluginLanguageDomain, txt)
	if translated != txt:
		return translated
	print("[%s] fallback to default translation for %s" % (PluginLanguageDomain, txt))
	return gettext.gettext(txt)


localeInit()
language.addCallback(localeInit)

__version__ = "1.1"
