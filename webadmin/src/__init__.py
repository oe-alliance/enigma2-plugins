from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
import gettext

__version__ = "1.6.6"

PluginLanguageDomain = "WebAdmin"
PluginLanguagePath = "Extensions/WebAdmin/locale"


def localeInit():
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


def _(txt):
	t = gettext.dgettext(PluginLanguageDomain, txt)
	if t == txt:
		print("[%s] fallback to default translation for %s" % (PluginLanguageDomain, txt))
		t = gettext.gettext(txt)
	return t


def bin2long(s):
	if isinstance(s, str):
		s = s.encode("latin-1")
	return int.from_bytes(s, "big")


def long2bin(l):
	return int(l).to_bytes(128, "big")


def rsa_pub1024(src, mod):
	return long2bin(pow(bin2long(src), 65537, bin2long(mod)))


def decrypt_block(src, mod):
	# Legacy helper kept for compatibility; unused in WebAdmin.
	return None


localeInit()
language.addCallback(localeInit)
