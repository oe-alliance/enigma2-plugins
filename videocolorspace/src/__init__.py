from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
from os import environ
import gettext

def localeInit():
    lang = language.getLanguage()
    environ["LANGUAGE"] = lang[:2]
    gettext.bindtextdomain("enigma2", resolveFilename(SCOPE_LANGUAGE))
    gettext.textdomain("enigma2")
    gettext.bindtextdomain("VideoColorSpace", resolveFilename(SCOPE_PLUGINS, "SystemPlugins/VideoColorSpace/locale/"))

def _(txt):
    t = gettext.dgettext("VideoColorSpace", txt)
    if t == txt:
        t = gettext.gettext(txt)
    return t

localeInit()
language.addCallback(localeInit)
