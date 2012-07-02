# -*- coding: utf-8 -*-
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
from os import environ as os_environ
import gettext

def localeInit():
	lang = language.getLanguage()[:2] # getLanguage returns e.g. "de_DE" for "language_country"
	os_environ["LANGUAGE"] = lang # Enigma doesn't set this (or LC_ALL, LC_MESSAGES, LANG). gettext needs it!
	gettext.bindtextdomain("SerienFilm", resolveFilename(SCOPE_PLUGINS, "Extensions/SerienFilm/locale"))


def _x(txt):
	t = gettext.dgettext("SerienFilm", txt)
	if t == txt:
		t = gettext.gettext(txt)
#		print "[SF-Plugin] gettext >%s< = >%s<" % (txt, t)
	return t

localeInit()
language.addCallback(localeInit)

