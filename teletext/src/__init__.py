from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
import gettext

PluginLanguageDomain = "TeleText"
PluginLanguagePath = "Extensions/TeleText/locale"


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


def _log(message):
  print("[TeleText]", message)


def _debug(message):
  d = open("/tmp/dbttcp.log", "a")
  d.write("[TeleText] %s\n" % message)
  d.close()
