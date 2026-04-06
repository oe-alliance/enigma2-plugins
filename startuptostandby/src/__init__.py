from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from gettext import bindtextdomain, dgettext

PluginLanguageDomain = "StartupToStandby"
PluginLanguagePath = "Extensions/StartupToStandby/locale"
__version__ = "1.0"


def localeInit():
	bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


def _(txt):
	translated = dgettext(PluginLanguageDomain, txt)
	if translated == txt:
		return txt
	return translated


localeInit()
language.addCallback(localeInit)
