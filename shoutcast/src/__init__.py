# -*- coding: utf-8 -*-
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
import gettext

def localeInit():
	gettext.bindtextdomain("SHOUTcast", resolveFilename(SCOPE_PLUGINS, "Extensions/SHOUTcast/locale"))

def _(txt):
	t = gettext.dgettext("SHOUTcast", txt)
	if t == txt:
		# print "[SHOUTcast] fallback to default translation for", txt
		t = gettext.gettext(txt)
	return t

localeInit()
language.addCallback(localeInit)

