# -*- coding: utf-8 -*-
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_LANGUAGE, SCOPE_PLUGINS, SCOPE_SKIN_IMAGE #@UnresolvedImport
import gettext, os, re
from enigma import eBackgroundFileEraser

lang = language.getLanguage()
os.environ["LANGUAGE"] = lang[:2]
gettext.bindtextdomain("enigma2", resolveFilename(SCOPE_LANGUAGE))
gettext.textdomain("enigma2")
gettext.bindtextdomain("NcidClient", "%s%s" % (resolveFilename(SCOPE_PLUGINS), "Extensions/NcidClient/locale/"))

def _(txt): # pylint: disable-msg=C0103
	td = gettext.dgettext("NcidClient", txt)
	if td == txt:
		print "[NcidClient] fallback to default translation for", txt 
		td = gettext.gettext(txt)
		
	return td

def debug(message):
	print message
