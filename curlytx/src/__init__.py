# -*- coding: utf-8 -*-
# CurlyTx translation initialization
# Copyright (C) 2011 Christian Weiske <cweiske@cweiske.de>
# License: GPLv3 or later

from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
from os import environ as os_environ
import os, gettext

def localeInit():
    """ Prepare settings for gettext usage """
    lang = language.getLanguage()[:2] # getLanguage returns e.g. "fi_FI" for "language_country"
    os_environ["LANGUAGE"] = lang # Enigma doesn't set this (or LC_ALL, LC_MESSAGES, LANG). gettext needs it!
    gettext.bindtextdomain("CurlyTx", resolveFilename(SCOPE_PLUGINS, "Extensions/CurlyTx/locale"))

def _(txt):
    """ Custom gettext translation function that uses the CurlyTx domain """
    t = gettext.dgettext("CurlyTx", txt)
    if t == txt:
        #print "[CurlyTx] fallback to default translation for", txt
        t = gettext.gettext(txt)
    return t

localeInit()
language.addCallback(localeInit)
