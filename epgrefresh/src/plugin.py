# Config
from Components.config import config, ConfigEnableDisable, ConfigInteger, ConfigSubsection, ConfigClock

# Calculate default begin/end
from time import localtime, mktime
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

		# Remove a fake timer we might have created at last shutdown
		for record in kwargs["session"].nav.RecordTimer.timer_list:
			if record.name == "EPGRefresh Help Timer":
				kwargs["session"].nav.RecordTimer.removeEntry(record)
				break
	elif reason == 1:
		epgrefresh.stop()
		if config.plugins.epgrefresh.enabled.value:
			# Workaround until a better solution comes up:
			# add a fake zap-timer if the box might not be up when our timespan begins

			#get next record timer start time
			nextRecordingTime = session.nav.RecordTimer.getNextRecordingTime()
			#get next zap timer start time
			nextZapTime = session.nav.RecordTimer.getNextZapTime()
		 	if nextZapTime != -1 and nextRecordingTime != -1:
		 		startTime = nextZapTime < nextRecordingTime and nextZapTime or nextRecordingTime
		 	else:
		 		startTime = nextZapTime != -1 and nextZapTime or nextRecordingTime

		 	now = localtime()
		 	begin = mktime(
				(now.tm_year, now.tm_mon, now.tm_mday,
				config.plugins.epgrefresh.begin.value[0],
				config.plugins.epgrefresh.begin.value[1],
				0, now.tm_wday, now.tm_yday, now.tm_isdst)
			)

			# If no recording scheduled or next scheduled recording after begin of timespan
		 	if startTime == -1 or startTime > begin:
		 		from RecordTimer import RecordTimerEntry
		 		from ServiceReference import ServiceReference
		 		import NavigationInstance
		 		fakeEntry = RecordTimerEntry(
					ServiceReference(
						NavigationInstance.instance.getCurrentlyPlayingServiceReference()
					),
					begin,
					begin,
					"EPGRefresh Help Timer",
					"EPGRefresh Help Timer",
					-1,
					justplay = True
				)
		 		NavigationInstance.instance.RecordTimer.record(fakeEntry)

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
		PluginDescriptor(name="EPGRefresh", description = "Automated EPGRefresher", where = [PluginDescriptor.WHERE_AUTOSTART, PluginDescriptor.WHERE_SESSIONSTART], fnc = autostart),
		PluginDescriptor(name="EPGRefresh", description = "Automated EPGRefresher", where = PluginDescriptor.WHERE_PLUGINMENU, fnc = main)
	]
