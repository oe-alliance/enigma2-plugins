from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
import gettext

PluginLanguageDomain = "EPGBackup"
PluginLanguagePath = "Extensions/EPGBackup/locale"
DefaultPluginLang = "en"


def localeInit():
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


def _(txt):
	t = gettext.dgettext(PluginLanguageDomain, txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t


localeInit()
language.addCallback(localeInit)

__version__ = "1.1.2"
