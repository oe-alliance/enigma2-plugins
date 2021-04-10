from __future__ import print_function
from Plugins.Extensions.WebInterface.WebComponents.Sources.Timer import Timer
from Plugins.SystemPlugins.vps.Vps import vps_timers
import time


class Vps(Timer):
	def addTimerByEventID(self, param):
		state, statetext = Timer.addTimerByEventID(self, param)
		if state:
			sRef = param['sRef']
			eit = int(param['eventid'])
			vpsplugin_enabled = None
			if 'vpsplugin_enabled' in param:
				vpsplugin_enabled = True if param['vpsplugin_enabled'] == '1' else False
			vpsplugin_overwrite = None
			if 'vpsplugin_overwrite' in param:
				vpsplugin_overwrite = True if param['vpsplugin_overwrite'] == '1' else False
			vpsplugin_time = None
			if 'vpsplugin_time' in param:
				vpsplugin_time = int(float(param['vpsplugin_time']))
				if vpsplugin_time == -1:
					vpsplugin_time = None
			for timer in self.recordtimer.timer_list + self.recordtimer.processed_timers:
				if sRef == str(timer.service_ref) and eit == timer.eit:
					print("[WebComponents.Vps] addTimerByEventID: Found new timer, changing!")
					timer.vpsplugin_enabled = vpsplugin_enabled
					timer.vpsplugin_overwrite = vpsplugin_overwrite
					timer.vpsplugin_time = vpsplugin_time

					now = int(time.time())
					if vpsplugin_enabled and timer.begin <= now + 900 and now <= timer.end:
						vps_timers.checksoon()
					break
		return state, statetext

	def editTimer(self, param):
		state, statetext = Timer.editTimer(self, param)
		if state:
			# find the timer and assign vps settings
			sRef = param['sRef']
			begin = int(float(param['begin']))
			end = int(float(param['end']))
			name = param['name']
			description = param['description']
			vpsplugin_enabled = None
			if 'vpsplugin_enabled' in param:
				vpsplugin_enabled = True if param['vpsplugin_enabled'] == '1' else False
			vpsplugin_overwrite = None
			if 'vpsplugin_overwrite' in param:
				vpsplugin_overwrite = True if param['vpsplugin_overwrite'] == '1' else False
			vpsplugin_time = None
			if 'vpsplugin_time' in param:
				vpsplugin_time = int(float(param['vpsplugin_time']))
				if vpsplugin_time == -1:
					vpsplugin_time = None
			for timer in self.recordtimer.timer_list + self.recordtimer.processed_timers:
				if sRef == str(timer.service_ref) and begin == int(timer.begin) \
						and end == int(timer.end) and name == timer.name \
						and description == timer.description:
					print("[WebComponents.Vps] editTimer: Timer changed!")
					timer.vpsplugin_enabled = vpsplugin_enabled
					timer.vpsplugin_overwrite = vpsplugin_overwrite
					timer.vpsplugin_time = vpsplugin_time

					now = int(time.time())
					if vpsplugin_enabled and begin <= now + 900 and now <= end:
						vps_timers.checksoon()
					break
		return state, statetext

	def getList(self):
		# walk timers again, append the three vps values to the previous tuple
		timerlist = Timer.getList(self)
		newlist = []
		append = newlist.append
		i = 0
		for item in self.recordtimer.timer_list + self.recordtimer.processed_timers:
			curlist = list(timerlist[i])
			curappend = curlist.append
			curappend(True if item.vpsplugin_enabled else False)
			curappend(True if item.vpsplugin_overwrite else False)
			curappend(item.vpsplugin_time or -1)
			append(curlist)
			i += 1
		print(newlist)
		return newlist
	list = property(getList)


# build new lut
tempLut = Timer.lut.copy()
maxVal = max(tempLut.values())
tempLut["vpsplugin_enabled"] = maxVal + 1
tempLut["vpsplugin_overwrite"] = maxVal + 2
tempLut["vpsplugin_time"] = maxVal + 3
Vps.lut = tempLut

del tempLut, maxVal
