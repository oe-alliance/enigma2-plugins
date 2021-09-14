from __future__ import absolute_import

from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
import gettext

from .skin import loadSkin
loadSkin(resolveFilename(SCOPE_PLUGINS) + "Extensions/AdvancedMovieSelection/skin/skin.xml")

PluginLanguageDomain = "AdvancedMovieSelection"
PluginLanguagePath = "Extensions/AdvancedMovieSelection/locale/"


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
