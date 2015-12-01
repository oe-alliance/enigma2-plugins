# -*- coding: utf-8 -*-

from Components.config import config, ConfigSubsection, ConfigOnOff, ConfigNumber, ConfigSelection, ConfigYesNo, ConfigText, ConfigSelectionNumber
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
from os import environ as os_environ
import gettext


#######################################################
# Initialize Configuration
config.plugins.seriesplugin = ConfigSubsection()

config.plugins.seriesplugin.enabled                   = ConfigOnOff(default = False)

config.plugins.seriesplugin.menu_info                 = ConfigYesNo(default = True)
config.plugins.seriesplugin.menu_extensions           = ConfigYesNo(default = False)
config.plugins.seriesplugin.menu_epg                  = ConfigYesNo(default = False)
config.plugins.seriesplugin.menu_channel              = ConfigYesNo(default = True)
config.plugins.seriesplugin.menu_movie_info           = ConfigYesNo(default = True)
config.plugins.seriesplugin.menu_movie_rename         = ConfigYesNo(default = True)

config.plugins.seriesplugin.identifier_elapsed        = ConfigText(default = "", fixed_size = False)
config.plugins.seriesplugin.identifier_today          = ConfigText(default = "", fixed_size = False)
config.plugins.seriesplugin.identifier_future         = ConfigText(default = "", fixed_size = False)

#config.plugins.seriesplugin.manager                   = ConfigSelection(choices = [("", "")], default = "")
#config.plugins.seriesplugin.guide                     = ConfigSelection(choices = [("", "")], default = "")

config.plugins.seriesplugin.pattern_file              = ConfigText(default = "/etc/enigma2/seriesplugin_patterns.json", fixed_size = False)
config.plugins.seriesplugin.pattern_title             = ConfigText(default = "{org:s} S{season:02d}E{episode:02d} {title:s}", fixed_size = False)
config.plugins.seriesplugin.pattern_description       = ConfigText(default = "S{season:02d}E{episode:02d} {title:s} {org:s}", fixed_size = False)
#config.plugins.seriesplugin.pattern_record            = ConfigText(default = "{org:s} S{season:02d}E{episode:02d} {title:s}", fixed_size = False)
config.plugins.seriesplugin.pattern_file_directories  = ConfigText(default = "/etc/enigma2/seriesplugin_patterns_directories.json", fixed_size = False)
config.plugins.seriesplugin.pattern_directory         = ConfigText(default = "Disabled", fixed_size = False)

config.plugins.seriesplugin.default_season            = ConfigSelectionNumber(0, 1, 1, default = 1)
config.plugins.seriesplugin.default_episode           = ConfigSelectionNumber(0, 1, 1, default = 1)

config.plugins.seriesplugin.replace_chars             = ConfigText(default = ":\!/\\,\(\)'\?", fixed_size = False)

config.plugins.seriesplugin.channel_file              = ConfigText(default = "/etc/enigma2/seriesplugin_channels.xml", fixed_size = False)

config.plugins.seriesplugin.bouquet_main              = ConfigText(default = "", fixed_size = False)

config.plugins.seriesplugin.rename_file               = ConfigYesNo(default = True)
config.plugins.seriesplugin.rename_tidy               = ConfigYesNo(default = False)
config.plugins.seriesplugin.rename_legacy             = ConfigYesNo(default = False)
config.plugins.seriesplugin.rename_existing_files     = ConfigYesNo(default = False)
config.plugins.seriesplugin.rename_popups             = ConfigYesNo(default = True)
config.plugins.seriesplugin.rename_popups_success     = ConfigYesNo(default = False)
config.plugins.seriesplugin.rename_popups_timeout     = ConfigSelectionNumber(-1, 20, 1, default = 3)

config.plugins.seriesplugin.max_time_drift            = ConfigSelectionNumber(0, 600, 1, default = 15)
config.plugins.seriesplugin.search_depths             = ConfigSelectionNumber(0, 10, 1, default = 0)

config.plugins.seriesplugin.skip_during_records       = ConfigYesNo(default=False)
config.plugins.seriesplugin.skip_pattern_match        = ConfigYesNo(default=True)

config.plugins.seriesplugin.autotimer_independent     = ConfigYesNo(default = False)
config.plugins.seriesplugin.independent_cycle         = ConfigSelectionNumber(5, 24*60, 5, default = 60)
config.plugins.seriesplugin.independent_retry         = ConfigYesNo(default = False)

config.plugins.seriesplugin.check_timer_list          = ConfigYesNo(default = False)

config.plugins.seriesplugin.timer_eit_check           = ConfigYesNo(default = True)
config.plugins.seriesplugin.timer_popups              = ConfigYesNo(default = True)
config.plugins.seriesplugin.timer_popups_success      = ConfigYesNo(default = False)
config.plugins.seriesplugin.timer_popups_timeout      = ConfigSelectionNumber(-1, 20, 1, default = 3)

config.plugins.seriesplugin.socket_timeout            = ConfigSelectionNumber(0, 600, 1, default = 30)

config.plugins.seriesplugin.caching                   = ConfigYesNo(default = True)
config.plugins.seriesplugin.caching_expiration        = ConfigSelectionNumber(0, 48, 1, default = 6)

config.plugins.seriesplugin.debug_prints              = ConfigYesNo(default = False)
config.plugins.seriesplugin.write_log                 = ConfigYesNo(default = False)
config.plugins.seriesplugin.log_file                  = ConfigText(default = "/tmp/seriesplugin.log", fixed_size = False)
config.plugins.seriesplugin.log_reply_user            = ConfigText(default = "Dreambox User", fixed_size = False)
config.plugins.seriesplugin.log_reply_mail            = ConfigText(default = "myemail@home.com", fixed_size = False)

# Internal
config.plugins.seriesplugin.lookup_counter            = ConfigNumber(default = 0)
#config.plugins.seriesplugin.uid                       = ConfigText(default = str(time()), fixed_size = False)


def localeInit():
	lang = language.getLanguage()[:2]  # getLanguage returns e.g. "fi_FI" for "language_country"
	os_environ["LANGUAGE"] = lang      # Enigma doesn't set this (or LC_ALL, LC_MESSAGES, LANG). gettext needs it!
	gettext.bindtextdomain("SeriesPlugin", resolveFilename(SCOPE_PLUGINS, "Extensions/SeriesPlugin/locale"))

_ = lambda txt: gettext.dgettext("SeriesPlugin", txt) if txt else ""

localeInit()
language.addCallback(localeInit)
