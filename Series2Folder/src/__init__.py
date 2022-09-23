from Components.config import config, ConfigSubsection, ConfigSelection, ConfigEnableDisable, ConfigText, ConfigYesNo, ConfigInteger
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
import gettext

PluginLanguageDomain = "Series2Folder"
PluginLanguagePath = "Extensions/Series2Folder/locale"


def localeInit():
    gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


def _(txt):
    trans = gettext.dgettext(PluginLanguageDomain, txt)
    if trans:
        return trans
    else:
        print("[%s] fallback to default translation for %s" % (PluginLanguageDomain, txt))
        return gettext.gettext(txt)


def ngettext(singular, plural, n):
    trans = gettext.dngettext(PluginLanguageDomain, singular, plural, n)
    if trans:
        return trans
    else:
        print("[%s] fallback to default translation for %s, %s" % (PluginLanguageDomain, singular, plural))
        return gettext.ngettext(singular, plural, n)


localeInit()
language.addCallback(localeInit)

config.plugins.seriestofolder = ConfigSubsection()
config.plugins.seriestofolder.autofolder = ConfigSelection([
    ("0", _("no autocreate")),
    ("1", _("1 recording")),
    ("2", _("2 recordings")),
    ("3", _("3 recordings")),
    ("4", _("4 recordings")),
    ("5", _("5 recordings")),
    ("6", _("6 recordings")),
    ("7", _("7 recordings")),
    ("8", _("8 recordings")),
    ("9", _("9 recordings")),
    ("10", _("10 recordings")),
], default="2")
config.plugins.seriestofolder.movies = ConfigEnableDisable(default=False)
# Some images don't support a show_help parameter for ConfigText
__defaultMoviesStr = "Movies"
try:
    config.plugins.seriestofolder.moviesfolder = ConfigText(default=__defaultMoviesStr, show_help=False)
except TypeError:
    config.plugins.seriestofolder.moviesfolder = ConfigText(default=__defaultMoviesStr)
config.plugins.seriestofolder.portablenames = ConfigYesNo(default=True)
config.plugins.seriestofolder.showmovebutton = ConfigYesNo(default=False)
config.plugins.seriestofolder.showselmovebutton = ConfigYesNo(default=False)
config.plugins.seriestofolder.striprepeattags = ConfigYesNo(default=False)
__defaultRepeatStr = "[R]"
try:
    config.plugins.seriestofolder.repeatstr = ConfigText(default=__defaultRepeatStr, show_help=False)
except TypeError:
    config.plugins.seriestofolder.repeatstr = ConfigText(default=__defaultRepeatStr)
config.plugins.seriestofolder.auto = ConfigYesNo(default=False)
config.plugins.seriestofolder.autonotifications = ConfigSelection([
    ("all", _("all")),
    ("error+move", _("error and \"moved\"")),
    ("error", _("error")),
    ("none", _("none")),
], default="error")
config.plugins.seriestofolder.autoreminder = ConfigInteger(default=5)


def onAutoChange(conf):
    if conf.value and config.plugins.seriestofolder.autoreminder.value:
        config.plugins.seriestofolder.autoreminder.value = 0
        config.plugins.seriestofolder.autoreminder.save()


config.plugins.seriestofolder.auto.addNotifier(onAutoChange, immediate_feedback=False)
