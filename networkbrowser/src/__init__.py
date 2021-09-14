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
	if gettext.dgettext(PluginLanguageDomain, txt):
		return gettext.dgettext(PluginLanguageDomain, txt)
	else:
		print("[%s] fallback to default translation for %s" % (PluginLanguageDomain, txt))
		return gettext.gettext(txt)


localeInit()
language.addCallback(localeInit)
