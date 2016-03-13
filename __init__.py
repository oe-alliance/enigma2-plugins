from Components.config import config, ConfigSubsection, ConfigSelection, ConfigEnableDisable, ConfigText, ConfigYesNo

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
config.plugins.seriestofolder.moviesfolder = ConfigText(default="Movies", show_help=False)
config.plugins.seriestofolder.portablenames = ConfigYesNo(default=True)
config.plugins.seriestofolder.showmovebutton = ConfigYesNo(default=True)
config.plugins.seriestofolder.showselmovebutton = ConfigYesNo(default=True)
config.plugins.seriestofolder.striprepeattags = ConfigYesNo(default=False)
config.plugins.seriestofolder.repeatstr = ConfigText(default="[R]", show_help=False)
config.plugins.seriestofolder.auto = ConfigYesNo(default=False)
config.plugins.seriestofolder.autonotifications = ConfigSelection([
    ("all", _("all")),
    ("error+move", _("error and \"moved\"")),
    ("error", _("error")),
    ("none", _("none")),
], default="error")
