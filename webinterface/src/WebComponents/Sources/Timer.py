from __future__ import print_function
Version = '$Header$'

from enigma import eServiceReference, eEPGCache
from Components.config import config
from Components.Sources.Source import Source
from Components.TimerSanityCheck import TimerSanityCheck
from Components.UsageConfig import preferredInstantRecordPath, preferredTimerPath
from ServiceReference import ServiceReference
from RecordTimer import RecordTimerEntry, RecordTimer, AFTEREVENT, parseEvent

from xml.sax.saxutils import unescape
from time import time, strftime, localtime, mktime

class Timer(Source):
	LIST = 0
	ADDBYID = 1
	ADD = 2
	DEL = 3
	TVBROWSER = 4
	CHANGE = 5
	WRITE = 6
	RECNOW = 7
	CLEANUP = 8

	def __init__(self, session, func=LIST):
		self.func = func
		Source.__init__(self)
		self.session = session
		self.recordtimer = session.nav.RecordTimer
		self.epgcache = eEPGCache.getInstance()
		self.res = ( False, "unknown command" )

	def handleCommand(self, cmd):
		if self.func is self.ADDBYID:
			self.res = self.addTimerByEventID(cmd)
			self.writeTimerList()

		elif self.func is self.ADD:
			self.res = self.editTimer(cmd)
			self.writeTimerList()

		elif self.func is self.TVBROWSER:
			self.res = self.tvBrowser(cmd)
			self.writeTimerList()

		elif self.func is self.DEL:
			self.res = self.delTimer(cmd)
			self.writeTimerList()

		elif self.func is self.CHANGE:
			self.res = self.editTimer(cmd)
			self.writeTimerList()

		elif self.func is self.WRITE:
			self.res = self.writeTimerList(force=True)

		elif self.func is self.RECNOW:
			self.res = self.recordNow(cmd)

		elif self.func is self.CLEANUP:
			self.res = self.cleanupTimer()

		else:
			self.res = ( False, _("Unknown function: '%s'") % (self.func) )

	def cleanupTimer(self):
		print("[WebComponents.Timer] cleanupTimer")

		self.session.nav.RecordTimer.cleanup()
		return ( True, _("List of Timers has been cleaned") )


	def delTimer(self, param):
		print("[WebComponents.Timer] delTimer")

		if 'sRef' in param:
			service_ref = ServiceReference(param['sRef'])
		else:
			return ( False, _("Missing Parameter: sRef") )

		if 'begin' in param:
			begin = int(float(param['begin']))
		else:
			return ( False, _("Missing Parameter: begin") )

		if 'end' in param:
			end = int(float(param['end']))
		else:
			return ( False, _("Missing Parameter: end") )

		try:
			for timer in self.recordtimer.timer_list + self.recordtimer.processed_timers:
				if str(timer.service_ref) == str(service_ref) and int(timer.begin) == begin and int(timer.end) == end:
					self.recordtimer.removeEntry(timer)
					return True, _("The timer '%s' has been deleted successfully") % (timer.name)
		except Exception:
			return ( False, _("The timer has NOT been deleted") )

		return False, "No matching Timer found"

	def tvBrowser(self, param):
		""" The URL's for the tvBrowser-Capture-Driver are:

			http://dreambox/web/tvbrowser? +

		To add something:
			&command=add&&year={year}&month={month}&day={day}&shour={start_hour}&smin={start_minute}&ehour={end_hour}&emin={end_minute}&sRef={urlencode(channel_name_external, "utf8")}&name={urlencode(title, "utf8")}&description={urlencode(descr, "utf8")}&dirname={dirname}&tags={urlencode("tag1 tag2...", "utf8")}&afterevent=0&eit=&disabled=0&justplay=0&repeated=0

		to zap for some time:
			&command=add&&year={year}&month={month}&day={day}&shour={start_hour}&smin={start_minute}&ehour={end_hour}&emin={end_minute}&sRef={urlencode(channel_name_external, "utf8")}&name={urlencode(title, "utf8")}&description={urlencode(descr, "utf8")}&dirname={dirname}&tags={urlencode("tag1 tag2...", "utf8")}&afterevent=0&eit=&disabled=0&justplay=1&repeated=0

		to delete something:
			&command=del&&year={year}&month={month}&day={day}&shour={start_hour}&smin={start_minute}&ehour={end_hour}&emin={end_minute}&sRef={urlencode(channel_name_external, "utf8")}
		"""
		print("[WebComponents.Timer] tvbrowser")

		listDate = ('year', 'month', 'day', 'shour', 'smin', 'ehour', 'emin')
		for element in listDate:
			if param[element] is None:
				if param['s' + element] is None:
					return ( False, "%s missing" % element )
				else:
					param[element] = int(param['s' + element])
			else:
				param[element] = int(param[element])
		param['begin'] = int(mktime((param['year'], param['month'], param['day'], param['shour'], param['smin'], 0, 0, 0, -1)))
		param['end']	 = int(mktime((param['year'], param['month'], param['day'], param['ehour'], param['emin'], 0, 0, 0, -1)))
		if param['end'] < param['begin']:
			param['end'] += 86400
		for element in listDate:
			del param[element]

		if param['sRef'] is None:
			return ( False, "Missing Parameter: sRef" )
		else:
			takeApart = param['sRef'].split('|')
			if len(takeApart) > 1:
				param['sRef'] = takeApart[1]

		repeated = int(param.get('repeated') or 0)
		if repeated == 0:
			for element in ("mo", "tu", "we", "th", "fr", "sa", "su", "ms", "mf"):
				if element in param:
					number = param[element] or 0
					del param[element]
					repeated = repeated + int(number)
			if repeated > 127:
				repeated = 127
		param['repeated'] = repeated

		if param['command'] == "add":
			del param['command']
			return self.editTimer(param)
		elif param['command'] == "del":
			del param['command']
			return self.delTimer(param)
		elif param['command'] == "change":
			del param['command']
			return self.editTimer(param)
		else:
			return ( False, "Unknown command: '%s'" % param['command'] )

	def recordNow(self, param):
		limitEvent = True
		if param == "undefinitely" or param == "infinite":
			ret = (True, "Infinite Instant recording started")
			limitEvent = False
		else:
			ret = ( True, "Instant record for current Event started" )

		serviceref = ServiceReference(self.session.nav.getCurrentlyPlayingServiceReference().toString())

		event = None

		try:
			service = self.session.nav.getCurrentService()
			event = service.info().getEvent(0)
		except Exception:
			print("[Webcomponents.Timer] recordNow Exception!")

		begin = time()
		end = begin + 3600 * 10
		name = "instant record"
		description = ""
		eventid = 0

		if event is not None:
			curEvent = parseEvent(event)
			name = curEvent[2]
			description = curEvent[3]
			eventid = curEvent[4]
			if limitEvent:
				end = curEvent[1]
		else:
			if limitEvent:
				ret = ( False, "No event found! Not recording!" )

		if ret[0]:
			location = preferredInstantRecordPath()
			timer = RecordTimerEntry(serviceref, begin, end, name, description, eventid, False, False, 0, dirname=location)
			timer.dontSave = True
			recRet = self.recordtimer.record(timer)
			if recRet is not None:
				# a conflict is rather unlikely, but this can also indicate a non-recordable service
				ret = (False, "Timer conflict detected! Not recording!" )

		return ret


#===============================================================================
# This Function can add a new or edit an exisiting Timer.
# When the Parameter "deleteOldOnSave" is not set, a new Timer will be added.
# Otherwise, and if the parameters channelOld, beginOld and endOld are set,
# an existing timer with corresponding values will be changed.
#===============================================================================
	def editTimer(self, param):
		print("[WebComponents.Timer] editTimer")

		#OK first we need to parse all of your Parameters
		#For some of them (like afterEvent or justplay) we can use default values
		#for others (the serviceReference or the Begin/End time of the timer
		#we have to quit if they are not set/have illegal values

		if 'sRef' not in param:
			return ( False, _("Missing Parameter: sRef") )
		service_ref = ServiceReference(param['sRef'])

		repeated = int(param.get('repeated') or 0)

		if 'begin' not in param:
			return ( False, _("Missing Parameter: begin") )
		begin = int(float(param['begin']))

		if 'end' not in param:
			return ( False, _("Missing Parameter: end") )
		end = int(float(param['end']))

		tm = int( time() )
		if tm <= begin:
			pass
		elif tm > begin and tm < end and repeated == 0:
			pass
		elif repeated == 0:
			return ( False, _("Illegal Parameter value for Parameter begin : '%s'") % begin )

		if 'applyMargin' in param:
			if param['applyMargin'] == "1":
				begin -= config.recording.margin_before.value * 60
				end += config.recording.margin_after.value * 60

		if 'name' not in param:
			return ( False, _("Missing Parameter: name") )
		name = param['name']

		if 'description' not in param:
			return ( False, _("Missing Parameter: description") )
		description = param['description'].replace("\n", " ")

		eit = param.get("eit", None)
		if eit is None or eit.strip() == "":
			eit = 0
		else:
			try:
				eit = int(eit)
			except ValueError:
				return ( False, _("Illegal Parameter value for Parameter eit : '%s'") % eit )

		print("[WebComponents.Sources.Timer]: eit=%d" %eit)
		if eit != 0:
			#check if the given event exists, if it doesn't the timer may be already running
			epgcache = eEPGCache.getInstance()
			event = epgcache.lookupEventId(eServiceReference(param['sRef']), eit)
			if event:
				eit = event.getEventId()
				#TODO add some subservice handling
			else:
				print("[WebComponents.Sources.Timer] event not found, will be ignored")

		disabled = False #Default to: Enabled
		if 'disabled' in param:
			if param['disabled'] == "1":
				disabled = True
			else:
				#TODO - maybe we can give the user some useful hint here
				pass

		justplay = False #Default to: Record
		if 'justplay' in param:
			if param['justplay'] == "1":
				justplay = True

		afterEvent = 3 #Default to Afterevent: Auto
		if 'afterevent' in param:
			if (param['afterevent'] == "0") or (param['afterevent'] == "1") or (param['afterevent'] == "2"):
				afterEvent = int(param['afterevent'])

		dirname = preferredTimerPath()
		if 'dirname' in param and param['dirname']:
			dirname = param['dirname']

		tags = []
		if 'tags' in param and param['tags']:
			tags = unescape(param['tags']).split(' ')

		delold = 0
		if 'deleteOldOnSave' in param:
			delold = int(param['deleteOldOnSave'])

		#Try to edit an existing Timer
		if delold:
			if 'channelOld' in param and param['channelOld']:
				channelOld = ServiceReference(param['channelOld'])
			else:
				return ( False, _("Missing Parameter: channelOld") )
			# We do need all of the following Parameters, too, for being able of finding the Timer.
			# Therefore so we can neither use default values in this part nor can we
			# continue if a parameter is missing
			if 'beginOld' not in param:
				return ( False, _("Missing Parameter: beginOld") )
			beginOld = int(param['beginOld'])

			if 'endOld' not in param:
				return ( False, _("Missing Parameter: endOld") )
			endOld = int(param['endOld'])

			#let's try to find the timer
			try:
				for timer in self.recordtimer.timer_list + self.recordtimer.processed_timers:
					if str(timer.service_ref) == str(channelOld):
						if int(timer.begin) == beginOld:
							if int(timer.end) == endOld: #we've found the timer we've been searching for
								#set the new data
								timer.service_ref = service_ref
								timer.begin = begin
								timer.end = end
								timer.name = name
								timer.description = description
								timer.eit = eit
								timer.disabled = disabled
								timer.justplay = justplay
								timer.afterEvent = afterEvent
								timer.dirname = dirname
								timer.tags = tags
								timer.repeated = repeated
								timer.processRepeated()

								#sanity check
								timersanitycheck = TimerSanityCheck(self.session.nav.RecordTimer.timer_list, timer)
								conflicts = None
								if not timersanitycheck.check():
									conflicts = timersanitycheck.getSimulTimerList()
									if conflicts is not None:
										for x in conflicts:
											if x.setAutoincreaseEnd(entry):
												self.session.nav.RecordTimer.timeChanged(x)
										if not timersanitycheck.check():
											conflicts = timersanitycheck.getSimulTimerList()

								if conflicts is None:
									self.recordtimer.timeChanged(timer) #go and save it
									print("[WebComponents.Timer] editTimer: Timer changed!")
									return ( True, "Timer '%s' changed" %(timer.name) )
								else:
									print("[WebComponents.Timer] editTimer conflicting Timers: %s" %(conflicts))
									msg = ""
									for t in conflicts:
										msg = "%s / %s" %(msg, t.name)

									return (False, _("Conflicting Timer(s) detected! %s") %(msg))

			except Exception as e:
				#obviously some value was not good, return an error
				import traceback
				print(traceback.format_exc())
				return ( False, _("Changing the timer for '%s' failed!") % name )


			return ( False, _("Could not find timer '%s' with given start and end time!") % name )

		#Try adding a new Timer

		try:
			#Create a new instance of recordtimerentry
			timer = RecordTimerEntry(service_ref, begin, end, name, description, eit, disabled, justplay, afterEvent, dirname=dirname, tags=tags)
			timer.repeated = repeated
			#add the new timer
			conflicts = self.recordtimer.record(timer)
			if conflicts is None:
				return ( True, _("Timer '%s' added") %(timer.name) )
			else:
				print("[WebComponents.Timer] editTimer conflicting Timers: %s" %(conflicts))
				msg = ""
				for timer in conflicts:
					msg = "%s / %s" %(msg, timer.name)

				return (False, _("Conflicting Timer(s) detected! %s") %(msg))

		except Exception as e:
			#something went wrong, most possibly one of the given paramater-values was wrong
			print("[WebComponents.Timer] editTimer exception: %s" %(e))
			return ( False, _("Could not add timer '%s'!") % name )

		return ( False, "Unexpected Error" )

	def addTimerByEventID(self, param):
		print("[WebComponents.Timer] addTimerByEventID", param)
		if param['sRef'] is None:
			return ( False, _("Missing Parameter: sRef") )
		if param['eventid'] is None:
			return ( False, _("Missing Parameter: eventid") )

		justplay = False
		if param['justplay'] is not None:
			if param['justplay'] == "1":
				justplay = True

		location = preferredTimerPath()
		if 'dirname' in param and param['dirname']:
			location = param['dirname']

		tags = []
		if 'tags' in param and param['tags']:
			tags = unescape(param['tags']).split(' ')

		epgcache = eEPGCache.getInstance()
		event = epgcache.lookupEventId(eServiceReference(param['sRef']), int(param['eventid']))
		if event is None:
			return ( False, _("EventId not found") )

		(begin, end, name, description, eit) = parseEvent(event)

		timer = RecordTimerEntry(ServiceReference(param['sRef']), begin, end, name, description, eit, False, justplay, AFTEREVENT.AUTO, dirname=location, tags=tags)

		conflicts = self.recordtimer.record(timer)
		if conflicts is None:
			return ( True, _("Timer '%s' added") %(timer.name) )
		else:
			print("[WebComponents.Timer] editTimer conflicting Timers: %s" %(conflicts))
			msg = ""
			for timer in conflicts:
				msg = "%s / %s" %(msg, timer.name)

			return (False, _("Conflicting Timer(s) detected! %s") %(msg))


	def writeTimerList(self, force=False):
		# is there an easier and better way? :\
		if config.plugins.Webinterface.autowritetimer.value or force:
			print("Timer.py writing timer to flash")
			self.session.nav.RecordTimer.saveTimer()
			return ( True, _("TimerList has been saved") )
		else:
			return ( False, _("TimerList has not been saved") )


	def getResult(self):
		return self.res

	result = property(getResult)

	## part for listfiller requests
	def getList(self):
		timerlist = []

		for item in self.recordtimer.timer_list + self.recordtimer.processed_timers:
			try:
				filename = item.Filename
			except AttributeError:
				filename = ""

			try:
				next_activation = item.next_activation
			except AttributeError:
				next_activation = ""

			if item.eit is not None:
				event = self.epgcache.lookupEvent(['EX', ("%s" % item.service_ref, 2, item.eit)])
				if event and event[0][0] is not None:
					extdesc = event[0][0]
				else:
					extdesc = "N/A"
			else:
				extdesc = "N/A"

			#toggleDisabled
			if item.disabled:
				disabled = "1"
				toggleDisabled = "0"
				toggleDisabledImg = "on"
			else:
				disabled = "0"
				toggleDisabled = "1"
				toggleDisabledImg = "off"

			timerlist.append((
				item.service_ref,
				item.service_ref.getServiceName(),
				item.eit,
				item.name,
				item.description,
				disabled,
				item.begin,
				item.end,
				item.end - item.begin,
				item.start_prepare,
				1 if item.justplay else 0,
				item.afterEvent,
				item.dirname,
				" ".join(item.tags),
				item.log_entries,
				item.backoff,
				item.first_try_prepare,
				item.state,
				item.repeated,
				1 if item.dontSave else 0,
				item.cancelled,
				filename,
				next_activation,
				extdesc,
				toggleDisabled,
				toggleDisabledImg,
			))

		return timerlist

	list = property(getList)
	lut = {
				"ServiceReference": 0,
				"ServiceName": 1,
				"EIT": 2,
				"Name": 3,
				"Description": 4,
				"Disabled": 5,
				"TimeBegin": 6,
				"TimeEnd": 7,
				"Duration": 8,
				"startPrepare": 9,
				"justPlay": 10,
				"afterEvent": 11,
				"Location": 12,
				"Tags": 13,
				"LogEntries": 14,
				"Backoff": 15,
				"firstTryPrepare": 16,
				"State": 17,
				"Repeated": 18,
				"dontSave": 19,
				"Cancled": 20,
				"Filename": 21,
				"nextActivation": 22,
				"DescriptionExtended": 23,
				"toggleDisabled": 24,
				"toggleDisabledIMG": 25,
			}
