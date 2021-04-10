from __future__ import absolute_import
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
from os import environ
import gettext
from skin import loadSkin
loadSkin(resolveFilename(SCOPE_PLUGINS) + "Extensions/AdvancedMovieSelection/skin/skin.xml")


def localeInit():
    lang = language.getLanguage()
    environ["LANGUAGE"] = lang[:2]
    gettext.bindtextdomain("enigma2", resolveFilename(SCOPE_LANGUAGE))
    gettext.textdomain("enigma2")
    gettext.bindtextdomain("AdvancedMovieSelection", "%s%s" % (resolveFilename(SCOPE_PLUGINS), "Extensions/AdvancedMovieSelection/locale/"))

    ln = language.lang[language.activeLanguage][1]
    from .AboutParser import AboutParser
    AboutParser.setLocale(ln)
    from .MovieDB import tmdb, tvdb
    tmdb.setLocale(ln)
    tvdb.setLocale(ln)


def _(txt):
    t = gettext.dgettext("AdvancedMovieSelection", txt)
    if t == txt:
        t = gettext.gettext(txt)
    return t


localeInit()
language.addCallback(localeInit)
