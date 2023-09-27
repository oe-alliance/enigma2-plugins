# PYTHON IMPORTS
from gettext import bindtextdomain, dgettext, gettext
from os.path import join

# ENIGMA IMPORTS
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

PLUGINPATH = resolveFilename(SCOPE_PLUGINS, "Extensions/EPGExport/")


def localeInit():
    bindtextdomain("EPGExport", join(PLUGINPATH, "locale"))


def _(txt):
    t = dgettext("EPGExport", txt)
    if t == txt:
        t = gettext(txt)
    return t


localeInit()
language.addCallback(localeInit)
