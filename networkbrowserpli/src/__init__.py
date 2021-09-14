#===============================================================================
# NetworkBrowser and MountManager Plugin by acid-burn
# netscan lib by Nix_niX
# for further License informations see the corresponding License files
# or SourceCodes
#
#===============================================================================
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
import gettext
PluginLanguageDomain = "NetworkBrowser"
PluginLanguagePath = "SystemPlugins/NetworkBrowser/locale"


def localeInit():
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


def _(txt):
	t = gettext.dgettext(PluginLanguageDomain, txt)
	if t == txt:
		print("[NetworkBrowser] fallback to default translation for %s" % txt)
		t = gettext.gettext(txt)
	return t


localeInit()
language.addCallback(localeInit)
