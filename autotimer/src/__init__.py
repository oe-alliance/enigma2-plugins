# -*- coding: utf-8 -*-

from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
import os,gettext

def localeInit():
    lang = language.getLanguage()[:2] # getLanguage returns e.g. "fi_FI" for "language_country"
    os.environ["LANGUAGE"] = lang # Enigma doesn't set this (or LC_ALL, LC_MESSAGES, LANG). gettext needs it!
    print "[AutoTimer] set language to ", lang
    gettext.bindtextdomain("AutoTimer", resolveFilename(SCOPE_PLUGINS, "Extensions/AutoTimer/locale"))

def _(txt):
    t = gettext.dgettext("AutoTimer", txt)
    if t == txt:
        print "[AutoTimer] fallback to default translation for", txt
        t = gettext.gettext(txt)
    return t

localeInit()
