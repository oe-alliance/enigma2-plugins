# for localized messages
from . import _

# Config
from Components.config import config, ConfigYesNo, ConfigNumber, \
	ConfigSubsection, ConfigClock

# Calculate default begin/end
from time import time, localtime, mktime
now = localtime()
begin = mktime((
	now.tm_year, now.tm_mon, now.tm_mday, 20, 15, \
	0, now.tm_wday, now.tm_yday, now.tm_isdst)
)
end = mktime((
	now.tm_year, now.tm_mon, now.tm_mday, 06, 30, \
	0, now.tm_wday, now.tm_yday, now.tm_isdst)
)

config.plugins.epgrefresh = ConfigSubsection()
config.plugins.epgrefresh.enabled = ConfigYesNo(default = False)
config.plugins.epgrefresh.begin = ConfigClock(default = int(begin))
config.plugins.epgrefresh.end = ConfigClock(default = int(end))
config.plugins.epgrefresh.interval = ConfigNumber(default = 2)
config.plugins.epgrefresh.delay_standby = ConfigNumber(default = 10)
config.plugins.epgrefresh.inherit_autotimer = ConfigYesNo(default = False)
config.plugins.epgrefresh.afterevent = ConfigYesNo(default = False)
config.plugins.epgrefresh.force = ConfigYesNo(default = False)
config.plugins.epgrefresh.wakeup = ConfigYesNo(default = False)
config.plugins.epgrefresh.lastscan = ConfigNumber(default = 0)
config.plugins.epgrefresh.parse_autotimer = ConfigYesNo(default = False)

del now, begin, end

# Plugin
from EPGRefresh import epgrefresh
from EPGRefreshConfiguration import EPGRefreshConfiguration
from EPGRefreshService import EPGRefreshService

# Plugin definition
from Plugins.Plugin import PluginDescriptor

def standbyQuestionCallback(session, res = None):
	if res:
		from Screens.Standby import Standby
		session.open(Standby)

# Autostart
def autostart(reason, **kwargs):
	if config.plugins.epgrefresh.enabled.value and reason == 0 \
		and kwargs.has_key("session"):

		session = kwargs["session"]
		if config.plugins.epgrefresh.wakeup.value:
			now = localtime()
			begin = int(mktime(
				(now.tm_year, now.tm_mon, now.tm_mday,
				config.plugins.epgrefresh.begin.value[0],
				config.plugins.epgrefresh.begin.value[1],
				0, now.tm_wday, now.tm_yday, now.tm_isdst)
			))
			# booted +- 10min from begin of timespan
			if abs(time() - begin) < 600:
				from Screens.MessageBox import MessageBox
				from Tools.Notifications import AddNotificationWithCallback
				from Tools.BoundFunction import boundFunction
				# XXX: we use a notification because this will be suppressed otherwise
				AddNotificationWithCallback(
					boundFunction(standbyQuestionCallback, session),
					MessageBox,
					_("This might have been an automated bootup to refresh the EPG. For this to happen it is recommmended to put the receiver to Standby.\nDo you want to do this now?"),
					timeout = 15
				)

		epgrefresh.start(session)

	elif reason == 1:
		epgrefresh.stop()

def getNextWakeup():
	# Return invalid time if not automatically refreshing
	if not config.plugins.epgrefresh.enabled.value or \
		not config.plugins.epgrefresh.wakeup.value:

		return -1

	now = localtime()
	begin = int(mktime(
		(now.tm_year, now.tm_mon, now.tm_mday,
		config.plugins.epgrefresh.begin.value[0],
		config.plugins.epgrefresh.begin.value[1],
		0, now.tm_wday, now.tm_yday, now.tm_isdst)
	))
	# todays timespan has not yet begun
	if begin > time():
		return begin
	# otherwise add 1 day
	return begin+86400

# Mainfunction
def main(session, **kwargs):
	epgrefresh.stop()
	session.openWithCallback(
		doneConfiguring,
		EPGRefreshConfiguration
	)

def doneConfiguring(session, **kwargs):
	if config.plugins.epgrefresh.enabled.value:
		epgrefresh.start(session)

# Eventinfo
def eventinfo(session, servicelist, **kwargs):
	ref = session.nav.getCurrentlyPlayingServiceReference()
	if not ref:
		return
	sref = ref.toString()
	# strip all after last :
	pos = sref.rfind(':')
	if pos != -1:
		sref = sref[:pos+1]

	epgrefresh.services[0].add(EPGRefreshService(str(sref), None))

def Plugins(**kwargs):
	return [
		PluginDescriptor(
			name = "EPGRefresh",
			where = [
				PluginDescriptor.WHERE_AUTOSTART,
				PluginDescriptor.WHERE_SESSIONSTART
			],
			fnc = autostart,
			wakeupfnc = getNextWakeup
		),
		PluginDescriptor(
			name = "EPGRefresh",
			description = _("Automated EPGRefresher"),
			where = PluginDescriptor.WHERE_PLUGINMENU,
			fnc = main
		),
		PluginDescriptor(
			name = _("Add to EPGRefresh"),
			where = PluginDescriptor.WHERE_EVENTINFO,
			fnc = eventinfo
		),
	]
