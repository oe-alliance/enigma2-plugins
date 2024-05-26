__version__ = "1.0"

from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from gettext import bindtextdomain, gettext, dgettext


def localeInit():
    bindtextdomain("Partnerbox", resolveFilename(SCOPE_PLUGINS, "Extensions/Partnerbox/locale"))


def _(txt):
    t = dgettext("Partnerbox", txt)
    if t == txt:
        t = gettext(txt)
    return t


def __(txt):
    return gettext(txt)


localeInit()
language.addCallback(localeInit)
