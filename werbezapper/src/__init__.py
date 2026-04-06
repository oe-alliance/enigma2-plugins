from Components.Language import language
from Tools.Directories import SCOPE_PLUGINS, resolveFilename
import gettext

PluginLanguageDomain = "WerbeZapper"
PluginLanguagePath = "Extensions/WerbeZapper/locale"


def localeInit():
    gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


def _(txt):
    translated = gettext.dgettext(PluginLanguageDomain, txt)
    if translated:
        return translated

    print("[%s] fallback to default translation for %s" % (PluginLanguageDomain, txt))
    return gettext.gettext(txt)


localeInit()
language.addCallback(localeInit)

__version__ = "1.1"
