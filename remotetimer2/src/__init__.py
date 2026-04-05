from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from gettext import bindtextdomain, dgettext

PluginLanguageDomain = "remoteTimer"
PluginLanguagePath = "Extensions/remoteTimer/locale"


def localeInit():
	bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


def _(txt):
	t = dgettext(PluginLanguageDomain, txt)
	if t == txt:
		return txt
	return t


localeInit()
language.addCallback(localeInit)

__version__ = "1.0"
