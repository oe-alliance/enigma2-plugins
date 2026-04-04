# -*- coding: utf-8 -*-

from Components.config import config
from time import localtime
from traceback import format_exc

# for localized messages
from . import _, __version__


def debugOut(outtxt, outfile=None, fmode="a", forced=False, outPrefix="[EPGBackup]"):
	try:  # fails if called too early during Enigma startup
		if config.plugins.epgbackup.enable_debug.value or forced:
			ltim = localtime()
			headerstr = "[%04d%02d%02d %02d:%02d:%02d V%s] " % (ltim[0], ltim[1], ltim[2], ltim[3], ltim[4], ltim[5], __version__)
			outtxt = headerstr + outtxt
			outfile = _getLogFilename(outfile)
			if outfile is not None:
				with open(outfile, fmode, encoding="utf-8", errors="replace") as deb:
					deb.write("%s %s\n" % (outPrefix, outtxt))
			print("%s %s" % (outPrefix, outtxt))
	except Exception:
		pass


def _getLogFilename(outfile=None):
	if outfile is None:
		if config.plugins.epgbackup.plugin_debug_in_file.value:
			if config.plugins.epgbackup.enable_debug.value:
				ltim = localtime()
				outfile = config.plugins.epgbackup.backup_log_dir.getValue() \
				+ "/EPGBackup.log.%04d%02d%02d" % (ltim[0], ltim[1], ltim[2])
			else:
				outfile = "/tmp/EPGBackup.log"
	return outfile


# Notification-Domain
EPGBACKUP_NOTIFICATIONDOMAIN = "EPGBackup"
from Tools import Notifications
try:
	Notifications.notificationQueue.registerDomain(EPGBACKUP_NOTIFICATIONDOMAIN, _("EPGBACKUP_NOTIFICATION_DOMAIN"), deferred_callable=True)
except Exception:
	debugOut("Register-Notification-Domain-Error:\n" + str(format_exc()), forced=True)
