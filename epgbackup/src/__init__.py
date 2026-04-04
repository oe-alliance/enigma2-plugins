from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from os import environ as os_environ
import gettext

PluginLanguageDomain = "EPGBackup"
PluginLanguagePath = "Extensions/EPGBackup/locale"
DefaultPluginLang = "en"


def localeInit():
    lang = language.getLanguage()[:2]
    os_environ["LANGUAGE"] = lang
    gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


def getDefaultTxt(txt):
    lang = language.getLanguage()[:2]
    os_environ["LANGUAGE"] = DefaultPluginLang
    t = gettext.dgettext(PluginLanguageDomain, txt)
    os_environ["LANGUAGE"] = lang
    return t


def _(txt):
    t = gettext.dgettext(PluginLanguageDomain, txt)
    if t == txt:
        t = getDefaultTxt(txt)
        if t == txt:
            t = gettext.gettext(txt)
    return t


localeInit()
language.addCallback(localeInit)

__version__ = "1.1.2"
