# -*- coding: utf-8 -*-

from enigma import eTimer, eConsoleAppContainer, getBestPlayableServiceReference, eServiceReference, eEPGCache
from time import time, strftime, localtime
from Components.config import config
from timer import TimerEntry
from Tools import Notifications
from Screens.MessageBox import MessageBox
from os import access, chmod, X_OK
from RecordTimer import RecordTimerEntry, parseEvent
from ServiceReference import ServiceReference
from Components.TimerSanityCheck import TimerSanityCheck
import NavigationInstance

vps_exe = "/usr/lib/enigma2/python/Plugins/SystemPlugins/vps/vps"
if not access(vps_exe, X_OK):
	chmod(vps_exe, 493)

class vps_timer:
	def __init__(self, timer, session):
		self.timer = timer
		self.session = session
		self.program = eConsoleAppContainer()
		self.program.dataAvail.append(self.program_dataAvail)
		self.program.appClosed.append(self.program_closed)
		self.program_running = False
		self.program_try_search_running = False
		self.last_overwrite_enabled = False
		self.activated_auto_increase = False
		self.simulate_recordService = None
		self.demux = -1
		self.rec_ref = None
		self.found_pdc = False
		self.dont_restart_program = False
		self.org_timer_end = 0
		self.org_timer_begin = 0
		self.next_events = [ ]
		
		self.program_seek_vps_multiple = eConsoleAppContainer()
		self.program_seek_vps_multiple.dataAvail.append(self.program_seek_vps_multiple_dataAvail)
		self.program_seek_vps_multiple.appClosed.append(self.program_seek_vps_multiple_closed)
		self.program_seek_vps_multiple_started = 0
		self.found_vps_multiple = [ ]
	
	def program_closed(self, retval):
		#print "[VPS-Plugin] Programm hat sich beendet"
		self.timer.log(0, "[VPS] stop monitoring (process terminated)")
		if self.program_running or self.program_try_search_running:
			self.program_running = False
			self.program_try_search_running = False
			self.stop_simulation()
	
	def program_dataAvail(self, str):
		#print "[VPS-Plugin] received: "+ str
		#try:
		if self.timer is None or self.timer.state == TimerEntry.StateEnded or self.timer.cancelled:
			self.program_abort()
			self.stop_simulation()
			return
		if self.timer.vpsplugin_enabled == False or config.plugins.vps.enabled.value == False:
			if self.activated_auto_increase:
				self.timer.autoincrease = False
			self.program_abort()
			self.stop_simulation()
			return
		
		lines = str.split("\n")
		for line in lines:
			data = line.split()
			if len(data) < 2:
				continue
			
			self.timer.log(0, "[VPS] "+ " ".join(data))
			
			if data[1] == "RUNNING_STATUS":
				if data[2] == "1": # not running
					# Wenn der Eintrag im Following (Section_Number = 1) ist, dann nicht beenden (Sendung begann noch gar nicht)
					if data[3] == "FOLLOWING":
						if not self.activated_auto_increase and self.timer.state == TimerEntry.StateRunning:
							self.activate_autoincrease()
					else:
						if self.timer.state == TimerEntry.StateRunning and not self.set_next_event():
							self.activated_auto_increase = False
							self.timer.autoincrease = False
							
							if self.timer.vpsplugin_overwrite:
								# sofortiger Stopp
								self.timer.abort()
								self.session.nav.RecordTimer.doActivate(self.timer)
								self.stop_simulation()
							
							self.dont_restart_program = True
							self.program_abort()
				
				elif data[2] == "2": # starts in a few seconds
					if self.timer.state == TimerEntry.StateWaiting:
						self.session.nav.RecordTimer.doActivate(self.timer)
				
				elif data[2] == "3": # pausing
					if self.timer.state == TimerEntry.StateRunning:
						if not self.activated_auto_increase:
							self.activate_autoincrease()
				
				elif data[2] == "4": # running
					if self.timer.state == TimerEntry.StateRunning:
						if not self.timer.vpsplugin_overwrite and (time() - self.timer.begin) < 60:
							self.program_abort()
							self.stop_simulation()
						elif not self.activated_auto_increase:
							self.activate_autoincrease()
					
					elif self.timer.state == TimerEntry.StateWaiting or self.timer.state == TimerEntry.StatePrepared:
						# setze Startzeit auf jetzt
						self.timer.begin = int(time())
						self.session.nav.RecordTimer.timeChanged(self.timer)
						
						if self.timer.vpsplugin_overwrite:
							self.activate_autoincrease()
							self.program_abort()
							self.stop_simulation()
							vps_timers.checksoon(2000) # Programm neu starten
						else:
							self.program_abort()
							self.stop_simulation()
			
			elif data[1] == "EVENT_ENDED":
				if not self.set_next_event():
					if self.timer.state == TimerEntry.StateRunning:
						self.activated_auto_increase = False
						self.timer.autoincrease = False
						
						if self.timer.vpsplugin_overwrite:
							# sofortiger Stopp
							self.timer.abort()
							self.session.nav.RecordTimer.doActivate(self.timer)
							self.stop_simulation()
	
							
					self.program_abort()
					self.stop_simulation()
			
			elif data[1] == "OTHER_TS_RUNNING_STATUS":
				if self.timer.state == TimerEntry.StateWaiting:
					self.timer.start_prepare = int(time())
					#self.session.nav.RecordTimer.calcNextActivation()
					self.session.nav.RecordTimer.doActivate(self.timer)
				
				self.program_abort()
				self.stop_simulation()
				#self.check()
				vps_timers.checksoon(2000)
			
			# PDC
			elif data[1] == "PDC_FOUND_EVENT_ID":
				self.found_pdc = True
				self.timer.eit = int(data[2])
				epgcache = eEPGCache.getInstance()
				evt = epgcache.lookupEventId(self.rec_ref, self.timer.eit)
				if evt:
					self.timer.name = evt.getEventName()
					self.timer.description = evt.getShortDescription()
				self.program_abort()
				vps_timers.checksoon(500)
			
			# Fehler
			elif data[1] == "DMX_ERROR_TIMEOUT" or data[1] == "DMX_SET_FILTER_ERROR":
				self.program_abort()
			
			elif data[1] == "EVENT_CURRENTLY_NOT_FOUND" and self.timer.state == TimerEntry.StateRunning:
				self.set_next_event()

		#except:
		#	pass
	
	def activate_autoincrease(self):
		self.activated_auto_increase = True
		self.timer.autoincrease = True
		self.timer.autoincreasetime = 60
		if self.org_timer_end == 0:
			self.org_timer_end = self.timer.end
		self.timer.log(0, "[VPS] enable autoincrease")
	
	# Noch ein Event aufnehmen?
	def set_next_event(self):
		if not self.timer.vpsplugin_overwrite and len(self.next_events) > 0:
			if not self.activated_auto_increase:
				self.activate_autoincrease()
			
			neweventid = self.next_events[0]
			self.timer.eit = neweventid
			self.dont_restart_program = False
			self.next_events.remove(neweventid)
			self.timer.log(0, "[VPS] record now event_id "+ str(neweventid))
			self.program_start()
			return True
		else:
			return False
	
	def program_abort(self):
		if self.program_running or self.program_try_search_running:
			#self.program.sendCtrlC()
			self.program.kill()
			self.program_running = False
			self.program_try_search_running = False
			self.timer.log(0, "[VPS] stop monitoring")
	
	def stop_simulation(self):
		if self.simulate_recordService:
			NavigationInstance.instance.stopRecordService(self.simulate_recordService)
			self.simulate_recordService = None
			self.timer.log(0, "[VPS] stop RecordService (simulation)")
	
	
	def program_seek_vps_multiple_closed(self, retval):
		self.program_seek_vps_multiple_started = -1
		
		self.found_vps_multiple = sorted(self.found_vps_multiple)
		
		for evt_begin, evt_id, evt in self.found_vps_multiple:
			# eigenen Timer überprüfen, wenn Zeiten nicht überschrieben werden dürfen
			if not self.timer.vpsplugin_overwrite and evt_begin <= self.timer.end:
				self.next_events.append(evt_id)
				self.timer.log(0, "[VPS] add event_id "+ str(evt_id))
			
			else:
				canbeadded = True
				evt_begin += 60
				evt_end = evt.getBeginTime() + evt.getDuration() - 60
				now = time()
				
				for checktimer in self.session.nav.RecordTimer.timer_list:
					if checktimer == self.timer:
						continue
					if (checktimer.begin - now) > 3600*24:
						break
					if checktimer.service_ref.ref.toCompareString() == self.timer.service_ref.ref.toCompareString() or checktimer.service_ref.ref.toCompareString() == self.rec_ref.toCompareString():	
						if checktimer.begin <= evt_begin and checktimer.end >= evt_end:
							if not checktimer.vpsplugin_enabled or not checktimer.vpsplugin_overwrite:
								canbeadded = False
							
							# manuell angelegter Timer mit VPS
							if checktimer.vpsplugin_enabled and checktimer.name == "" and checktimer.vpsplugin_time is not None:
								checktimer.eit = evt_id
								checktimer.name = evt.getEventName()
								checktimer.description = evt.getShortDescription()
								checktimer.vpsplugin_time = None
								checktimer.log(0, "[VPS] changed timer (found same PDC-Time as in other VPS-recording)")
								canbeadded = False
								break

				
				if canbeadded:
					newevent_data = parseEvent(evt)
					newEntry = RecordTimerEntry(ServiceReference(self.rec_ref), *newevent_data)
					newEntry.vpsplugin_enabled = True
					newEntry.vpsplugin_overwrite = True
					newEntry.log(0, "[VPS] added this timer (found same PDC-Time as in other VPS-recording)")
					
					# Wenn kein Timer-Konflikt auftritt, wird der Timer angelegt.
					NavigationInstance.instance.RecordTimer.record(newEntry)
				
	
	def program_seek_vps_multiple_dataAvail(self, str):
		lines = str.split("\n")
		for line in lines:
			data = line.split()
			if len(data) < 2:
				continue
			
			self.timer.log(0, "[VPS] "+ " ".join(data))
			
			if data[1] == "PDC_MULTIPLE_FOUND_EVENT":
				neweventid = int(data[2])
				epgcache = eEPGCache.getInstance()
				evt = epgcache.lookupEventId(self.rec_ref, neweventid)
				
				if evt:
					evt_begin = evt.getBeginTime() + 60
					evt_end = evt.getBeginTime() + evt.getDuration() - 60
					
					if evt_begin > self.timer.begin:
						canbeadded = True
						now = time()
						for checktimer in self.session.nav.RecordTimer.timer_list:
							if checktimer == self.timer:
								continue
							if (checktimer.begin - now) > 3600*24:
								break
							if checktimer.service_ref.ref.toCompareString() == self.timer.service_ref.ref.toCompareString() or checktimer.service_ref.ref.toCompareString() == self.rec_ref.toCompareString():	
								if checktimer.eit == neweventid:
									canbeadded = False
									break
								
								if checktimer.begin <= evt_begin and checktimer.end >= evt_end:
									if checktimer.vpsplugin_enabled is None or checktimer.vpsplugin_enabled == False:
										canbeadded = False
										break
										
						
						if canbeadded:
							self.found_vps_multiple.append((evt_begin-60, neweventid, evt))

	
	# Suche nach weiteren Events mit selber VPS-Zeit
	def program_seek_vps_multiple_start(self):
		if self.program_seek_vps_multiple_started == 0:
			self.program_seek_vps_multiple_started = time()
			
			self.rec_ref = self.timer.service_ref and self.timer.service_ref.ref
			if self.rec_ref and self.rec_ref.flags & eServiceReference.isGroup:
				self.rec_ref = getBestPlayableServiceReference(self.rec_ref, eServiceReference())
			elif self.rec_ref is None:
				self.program_seek_vps_multiple_started = -1
				return
			
			if self.demux == -1:
				stream = self.timer.record_service.stream()
				if stream:
					streamdata = stream.getStreamingData()
					if (streamdata and ('demux' in streamdata)):
						self.demux = streamdata['demux']
					else:
						self.program_seek_vps_multiple_started = -1
						return
			
			sid = self.rec_ref.getData(1)
			tsid = self.rec_ref.getData(2)
			onid = self.rec_ref.getData(3)
			demux = "/dev/dvb/adapter0/demux" + str(self.demux)
			
			if self.timer.vpsplugin_time is not None and self.found_pdc:
				day = strftime("%d", localtime(self.timer.vpsplugin_time))
				month = strftime("%m", localtime(self.timer.vpsplugin_time))
				hour = strftime("%H", localtime(self.timer.vpsplugin_time))
				minute = strftime("%M", localtime(self.timer.vpsplugin_time))
				cmd = vps_exe + " "+ demux +" 4 "+ str(onid) +" "+ str(tsid) +" "+ str(sid) +" "+ str(self.timer.eit) +" 0 "+ day +" "+ month +" "+ hour +" "+ minute
			else:
				cmd = vps_exe + " "+ demux +" 5 "+ str(onid) +" "+ str(tsid) +" "+ str(sid) +" "+ str(self.timer.eit) +" 0"
			
			self.program_seek_vps_multiple.execute(cmd)
			
			self.timer.log(0, "[VPS] seek another events with same PDC-Time")
	
	def program_seek_vps_multiple_abort(self):
		if self.program_seek_vps_multiple_started > 0:
			self.program_seek_vps_multiple.kill()
			self.program_seek_vps_multiple_started = -1
			self.timer.log(0, "[VPS] abort seeking other pdc-events")
	
	# startet den Hintergrundprozess
	def program_do_start(self, mode):
		if self.program_running or self.program_try_search_running:
			self.program_abort()
		
		if mode == 1:
			self.demux = 0
			self.program_try_search_running = True
			self.program_running = False
			mode_program = 1
		else:
			self.program_try_search_running = False
			self.program_running = True
			mode_program = 0
		
		sid = self.rec_ref.getData(1)
		tsid = self.rec_ref.getData(2)
		onid = self.rec_ref.getData(3)
		demux = "/dev/dvb/adapter0/demux" + str(self.demux)
		
		#print "[VPS-Plugin] starte Hintergrundprozess"
		
		# PDC-Zeit?
		if self.timer.name == "" and self.timer.vpsplugin_time is not None and not self.found_pdc:
			mode_program += 2
			day = strftime("%d", localtime(self.timer.vpsplugin_time))
			month = strftime("%m", localtime(self.timer.vpsplugin_time))
			hour = strftime("%H", localtime(self.timer.vpsplugin_time))
			minute = strftime("%M", localtime(self.timer.vpsplugin_time))
			cmd = vps_exe + " "+ demux +" "+ str(mode_program) +" "+ str(onid) +" "+ str(tsid) +" "+ str(sid) +" 0 0 "+ day +" "+ month +" "+ hour +" "+ minute
			#print "[VPS-Plugin] "+ cmd
			self.timer.log(0, "[VPS] seek PDC-Time")
			self.program.execute(cmd)
			return
		
		cmd = vps_exe + " "+ demux +" "+ str(mode_program) +" "+ str(onid) +" "+ str(tsid) +" "+ str(sid) +" "+ str(self.timer.eit) +" 0"
		#print "[VPS-Plugin] "+ cmd
		self.timer.log(0, "[VPS] start monitoring running-status")
		self.program.execute(cmd)
	
	
	def program_start(self):
		self.demux = -1
		
		if self.dont_restart_program:
			return
		
		self.rec_ref = self.timer.service_ref and self.timer.service_ref.ref
		if self.rec_ref and self.rec_ref.flags & eServiceReference.isGroup:
			self.rec_ref = getBestPlayableServiceReference(self.rec_ref, eServiceReference())
		
		# recordService (Simulation) ggf. starten
		if self.timer.state == TimerEntry.StateWaiting:
			if self.simulate_recordService is None:
				if self.rec_ref:
					self.simulate_recordService = NavigationInstance.instance.recordService(self.rec_ref, True)
					if self.simulate_recordService:
						res = self.simulate_recordService.start()
						#print "[VPS-Plugin] starte Simulation, res: "+ str(res)
						self.timer.log(0, "[VPS] start recordService (simulation)")
						if res != 0 and res != -1:
							# Fehler aufgetreten (kein Tuner frei?)
							NavigationInstance.instance.stopRecordService(self.simulate_recordService)
							self.simulate_recordService = None
							
							# in einer Minute ggf. nochmal versuchen
							if 60 < self.nextExecution:
								self.nextExecution = 60
							
							# Bei Overwrite versuchen ohne Fragen auf Sender zu schalten
							if self.timer.vpsplugin_overwrite == True:
								cur_ref = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
								if cur_ref and not cur_ref.getPath():
									self.timer.log(9, "[VPS-Plugin] zap without asking (simulation)")
									Notifications.AddNotification(MessageBox, _("In order to record a timer, the TV was switched to the recording service!\n"), type=MessageBox.TYPE_INFO, timeout=20)
									NavigationInstance.instance.playService(self.rec_ref)
									if 3 < self.nextExecution:
										self.nextExecution = 3
							else:
								# ansonsten versuchen auf dem aktuellen Transponder/Kanal nach Infos zu suchen
								if not self.program_try_search_running:
									self.program_do_start(1)
						else: # Simulation hat geklappt
							if 1 < self.nextExecution:
								self.nextExecution = 1
			else: # Simulation läuft schon
				# hole Demux
				stream = self.simulate_recordService.stream()
				if stream:
					streamdata = stream.getStreamingData()
					if (streamdata and ('demux' in streamdata)):
						self.demux = streamdata['demux']
				
				if self.demux == -1:
					# ist noch nicht soweit(?), in einer Sekunde erneut versuchen
					if 1 < self.nextExecution:
						self.nextExecution = 1
				else:
					self.program_do_start(0)
					
		
		elif self.timer.state == TimerEntry.StatePrepared or self.timer.state == TimerEntry.StateRunning:
			stream = self.timer.record_service.stream()
			if stream:
				streamdata = stream.getStreamingData()
				if (streamdata and ('demux' in streamdata)):
					self.demux = streamdata['demux']
			if self.demux != -1:
				self.program_do_start(0)
	
	
	# überprüft, ob etwas zu tun ist und gibt die Sekunden zurück, bis die Funktion
	# spätestens wieder aufgerufen werden sollte
	# oder -1, um vps_timer löschen zu lassen
	def check(self):
		# Simulation ggf. stoppen
		if self.timer.state > TimerEntry.StateWaiting and self.simulate_recordService and self.timer.vpsplugin_overwrite == False:
			self.stop_simulation()
		
		# VPS wurde wieder deaktiviert oder Timer wurde beendet
		if self.timer is None or self.timer.state == TimerEntry.StateEnded or self.timer.cancelled:
			self.program_abort()
			self.stop_simulation()
			#print "[VPS-Plugin] Timer wurde beendet"
			return -1
		
		if self.timer.vpsplugin_enabled == False or config.plugins.vps.enabled.value == False:
			if self.activated_auto_increase:
				self.timer.autoincrease = False
			self.program_abort()
			self.stop_simulation()
			#print "[VPS-Plugin] VPS wurde bei Timer wieder deaktiviert"
			return -1
		
		self.nextExecution = 180
		
		if self.timer.vpsplugin_overwrite == True:
			if config.plugins.vps.allow_overwrite.value == True:
				self.nextExecution = 60
				if self.timer.state == TimerEntry.StateWaiting or self.timer.state == TimerEntry.StatePrepared:
					# Startzeit verschieben
					if (self.timer.begin - 60) < time():
						if self.org_timer_begin == 0:
							self.org_timer_begin = self.timer.begin
						elif (self.org_timer_begin + (6*3600)) < time():
							# Sendung begann immer noch nicht -> abbrechen
							self.timer.abort()
							self.session.nav.RecordTimer.doActivate(self.timer)
							self.program_abort()
							self.stop_simulation()
							self.timer.log(0, "[VPS] abort timer, waited hours to find Event-ID")
							return -1
						
						self.timer.begin += 60
						if (self.timer.end - self.timer.begin) < 300:
							self.timer.end += 180
							# auf Timer-Konflikt prüfen
							timersanitycheck = TimerSanityCheck(self.session.nav.RecordTimer.timer_list, self.timer)
							if not timersanitycheck.check():
								self.timer.abort()
								self.session.nav.RecordTimer.doActivate(self.timer)
								self.program_abort()
								self.stop_simulation()
								self.timer.log(0, "[VPS] abort timer due to TimerSanityCheck")
								return -1
							
						self.timer.timeChanged()
						#print "[VPS-Plugin] verschiebe Startzeit des Timers (overwrite)"
					
					if 30 < self.nextExecution:
						self.nextExecution = 30
				
				if self.last_overwrite_enabled == False:
					self.last_overwrite_enabled = True
				
				# Programm wird auch bei laufendem Timer gestartet
				# mind. 2 Minuten Vorlaufzeit bekommen die VPS-Timer hier
				if self.program_running == False and (config.plugins.vps.initial_time.value < 2 or self.timer.state == TimerEntry.StateRunning):
					if (self.timer.begin - 120) <= time():
						self.program_start()
					else:
						n = self.timer.begin - 120 - time()
						if n < self.nextExecution:
							self.nextExecution = n
			else:
				self.timer.vpsplugin_overwrite = False
		
		# Wurde Overwrite deaktiviert?
		if self.timer.vpsplugin_overwrite == False and self.last_overwrite_enabled == True:
			self.last_overwrite_enabled = False
			# Wenn der Timer eh schon kurz vor Ende ist, dann Programm nicht beenden.
			#if self.program_running == True and (self.timer.end - 180) > time():
			self.program_abort()
		
		# Vorlaufzeit zur Prüfung
		if (self.timer.state == TimerEntry.StateWaiting or self.timer.state == TimerEntry.StatePrepared) and self.program_running == False and config.plugins.vps.initial_time.value > 0:
			if (self.timer.begin - (config.plugins.vps.initial_time.value * 60)) <= time():
				self.program_start()
			else:
				n = self.timer.begin - (config.plugins.vps.initial_time.value * 60) - time()
				if n < self.nextExecution:
					self.nextExecution = n
		
		# kurz vor (eigentlichem) Ende der Aufnahme Programm starten
		if self.timer.state == TimerEntry.StateRunning:
			if self.program_running == False:
				if (self.timer.end - 120) <= time():
					self.program_start()
				else:
					n = self.timer.end - 120 - time()
					if n < self.nextExecution:
						self.nextExecution = n
			elif self.program_running == True and (self.timer.end - 120) > time() and self.timer.vpsplugin_overwrite == False:
				self.program_abort()
			
			if self.activated_auto_increase and self.org_timer_end != 0 and (self.org_timer_end + (4*3600)) < time():
				# Aufnahme läuft seit 4 Stunden im Autoincrease -> abbrechen
				self.timer.autoincrease = False
				self.activated_auto_increase = False
				self.dont_restart_program = True
				self.program_abort()
				self.stop_simulation()
				self.timer.log(0, "[VPS] stop recording, too much autoincrease")
		
			# suche nach weiteren Sendungen mit der VPS-Zeit
			if self.program_seek_vps_multiple_started == 0 and config.plugins.vps.allow_seeking_multiple_pdc.value == True:
				self.program_seek_vps_multiple_start()
			elif self.program_seek_vps_multiple_started > 0 and ((time() - self.program_seek_vps_multiple_started) > 60):
				self.program_seek_vps_multiple_abort()
		
		return self.nextExecution

class vps:
	def __init__(self):
		self.timer = eTimer()
		self.timer.callback.append(self.checkTimer)

		self.vpstimers = [ ]
		self.current_timers_list = [ ]
		self.max_activation = 900
	
	def checkTimer(self):
		nextExecution = self.max_activation
		
		# nach den Timern schauen und ggf. zur Liste hinzufügen
		if config.plugins.vps.enabled.value == True:
			now = time()
			try:
				for timer in self.session.nav.RecordTimer.timer_list:
					n = timer.begin - now - (config.plugins.vps.initial_time.value * 60) - 120
					if n <= self.max_activation:
						if timer.vpsplugin_enabled == True and timer not in self.current_timers_list and not timer.justplay and not timer.repeated and not timer.disabled:
							self.addTimerToList(timer)
							#print "[VPS-Plugin] neuen VPS-Timer gefunden"
					else:
						break
			except AttributeError:
				print "[VPS-Plugin] AttributeError in Vps.py"
				return
		else:
			nextExecution = 14400
		
		# eigene Timer-Liste durchgehen
		for o_timer in self.vpstimers[:]:
			newtime = int(o_timer.check())
			if newtime == -1:
				self.current_timers_list.remove(o_timer.timer)
				self.vpstimers.remove(o_timer)
			elif newtime < nextExecution:
				nextExecution = newtime
		
		if nextExecution <= 0:
			nextExecution = 1
		
		self.timer.startLongTimer(nextExecution)
		print "[VPS-Plugin] next execution in "+ str(nextExecution) +" sec" 
	
	def addTimerToList(self, timer):
		self.vpstimers.append(vps_timer(timer, self.session))
		self.current_timers_list.append(timer)
	
	def checksoon(self, newstart = 3000):
		self.timer.start(newstart, True)
	
	def shutdown(self):
		for o_timer in self.vpstimers:
			o_timer.program_abort()
			o_timer.stop_simulation()
			o_timer.program_seek_vps_multiple_abort()
	
	def NextWakeup(self):
		if config.plugins.vps.enabled.value == False or config.plugins.vps.allow_wakeup.value == False:
			return -1
		
		try:
			for timer in self.session.nav.RecordTimer.timer_list:
				if timer.vpsplugin_enabled == True and timer.state == TimerEntry.StateWaiting and not timer.justplay and not timer.repeated and not timer.disabled:
					if config.plugins.vps.initial_time.value < 2 and timer.vpsplugin_overwrite:
						return (timer.begin - 180)
					
					return (timer.begin - (config.plugins.vps.initial_time.value * 60) - 60)
		except:
			pass
		
		return -1

vps_timers = vps()