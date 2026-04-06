from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
import gettext

PluginLanguageDomain = "WebBouquetEditor"
PluginLanguagePath = "Extensions/WebBouquetEditor/locale"


def localeInit():
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


def _(txt):
	translated = gettext.dgettext(PluginLanguageDomain, txt)
	if translated == txt:
		translated = gettext.gettext(txt)
	return translated


localeInit()
language.addCallback(localeInit)

__version__ = "1.0"
