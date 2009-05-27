# -*- coding: ISO-8859-1 -*-

from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
import os,gettext
PluginLanguageDomain = "SetPasswd"
PluginLanguagePath = "SystemPlugins/SetPasswd/po"

def localeInit():
        lang = language.getLanguage()[:2] # getLanguage returns e.g. "fi_FI" for "language_country"
        os.environ["LANGUAGE"] = lang # Enigma doesn't set this (or LC_ALL, LC_MESSAGES, LANG). gettext needs it!
        print "[WirelessLan] set language to ", lang
        gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))

def _(txt):
        t = gettext.dgettext(PluginLanguageDomain, txt)
        if t == txt:
                print "[WirelessLan] fallback to default translation for", txt
                t = gettext.gettext(txt)
        return t

localeInit()
language.addCallback(localeInit)

