from Tools.Directories import resolveFilename, SCOPE_LANGUAGE, SCOPE_PLUGINS, SCOPE_SKIN_IMAGE
from Components.Language import language
import os, gettext

lang = language.getLanguage()
os.environ["LANGUAGE"] = lang[:2]
gettext.bindtextdomain("enigma2", resolveFilename(SCOPE_LANGUAGE))
gettext.textdomain("enigma2")
gettext.bindtextdomain("EmailClient", "%s%s" % (resolveFilename(SCOPE_PLUGINS), "Extensions/EmailClient/locale/"))

def _(txt):
	t = gettext.dgettext("EmailClient", txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t
