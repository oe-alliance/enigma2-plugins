# Config
from Components.config import config, ConfigEnableDisable, ConfigNumber, \
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
config.plugins.epgrefresh.enabled = ConfigEnableDisable(default = False)
config.plugins.epgrefresh.begin = ConfigClock(default = int(begin))
config.plugins.epgrefresh.end = ConfigClock(default = int(end))
config.plugins.epgrefresh.interval = ConfigNumber(default = 2)
config.plugins.epgrefresh.delay_standby = ConfigNumber(default = 10)
config.plugins.epgrefresh.inherit_autotimer = ConfigEnableDisable(default = False)
config.plugins.epgrefresh.afterevent = ConfigEnableDisable(default = False)
config.plugins.epgrefresh.force = ConfigEnableDisable(default = False)
config.plugins.epgrefresh.lastscan = ConfigNumber(default = 0)

del now, begin, end

# Plugin
from EPGRefresh import epgrefresh
from EPGRefreshConfiguration import EPGRefreshConfiguration

# Plugin definition
from Plugins.Plugin import PluginDescriptor

# Autostart
def autostart(reason, **kwargs):
	if config.plugins.epgrefresh.enabled.value and reason == 0 \
		and kwargs.has_key("session"):

		epgrefresh.start(kwargs["session"])

	elif reason == 1:
		epgrefresh.stop()

def getNextWakeup():
	# Return invalid time if not automatically refreshing
	if not config.plugins.epgrefresh.enabled.value:
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

def Plugins(**kwargs):
	return [
		PluginDescriptor(
			name="EPGRefresh",
			description = "Automated EPGRefresher",
			where = [
				PluginDescriptor.WHERE_AUTOSTART,
				PluginDescriptor.WHERE_SESSIONSTART
			],
			fnc = autostart,
			wakeupfnc = getNextWakeup
		),
		PluginDescriptor(
			name="EPGRefresh",
			description = "Automated EPGRefresher",
			where = PluginDescriptor.WHERE_PLUGINMENU,
			fnc = main
		)
	]
