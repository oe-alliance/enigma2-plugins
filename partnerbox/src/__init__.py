# -*- coding: utf-8 -*-
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from os import environ as os_environ
from gettext import bindtextdomain, gettext, dgettext


def localeInit():
    bindtextdomain("Partnerbox", resolveFilename(SCOPE_PLUGINS, "Extensions/Partnerbox/locale"))


def _(txt):
    t = dgettext("Partnerbox", txt)
    if t == txt:
        # print "[Partnerbox] fallback to default translation for", txt
        t = gettext(txt)
    return t


localeInit()
language.addCallback(localeInit)
