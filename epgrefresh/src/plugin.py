# Config
from Components.config import config, ConfigEnableDisable, ConfigInteger, ConfigSubsection, ConfigClock

# Calculate default begin/end
from time import time, localtime, mktime
now = [x for x in localtime()]
now[3] = 20
now[4] = 15
begin = mktime(now)
now[3] = 06
now[4] = 30
end = mktime(now)

config.plugins.epgrefresh = ConfigSubsection()
config.plugins.epgrefresh.enabled = ConfigEnableDisable(default = False)
config.plugins.epgrefresh.begin = ConfigClock(default = begin)
config.plugins.epgrefresh.end = ConfigClock(default = end)
config.plugins.epgrefresh.interval = ConfigInteger(default = 2, limits=(1, 10))
config.plugins.epgrefresh.delay_timespan = ConfigInteger(default = 60, limits=(5, 300))
config.plugins.epgrefresh.delay_standby = ConfigInteger(default = 10, limits=(1, 60))
config.plugins.epgrefresh.inherit_autotimer = ConfigEnableDisable(default = False)
config.plugins.epgrefresh.afterevent = ConfigEnableDisable(default = False)
config.plugins.epgrefresh.force = ConfigEnableDisable(default = False)
config.plugins.epgrefresh.lastscan = ConfigInteger(default = 0)

# Plugin
from EPGRefresh import epgrefresh
from EPGRefreshConfiguration import EPGRefreshConfiguration

# Plugin definition
from Plugins.Plugin import PluginDescriptor

# Autostart
def autostart(reason, **kwargs):
	if config.plugins.epgrefresh.enabled.value and reason == 0 and kwargs.has_key("session"):
		epgrefresh.start(kwargs["session"])

	elif reason == 1:
		epgrefresh.stop()

def getNextWakeup():
	# Return invalid time if not automatically refreshing
	if not config.plugins.epgrefresh.enabled.value:
		return -1
	now = localtime()
	begin = mktime(
		(now.tm_year, now.tm_mon, now.tm_mday,
		config.plugins.epgrefresh.begin.value[0],
		config.plugins.epgrefresh.begin.value[1],
		0, now.tm_wday, now.tm_yday, now.tm_isdst)
	)
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
		PluginDescriptor(name="EPGRefresh", description = "Automated EPGRefresher", where = [PluginDescriptor.WHERE_AUTOSTART, PluginDescriptor.WHERE_SESSIONSTART], fnc = autostart, wakeupfnc = getNextWakeup),
		PluginDescriptor(name="EPGRefresh", description = "Automated EPGRefresher", where = PluginDescriptor.WHERE_PLUGINMENU, fnc = main)
	]
