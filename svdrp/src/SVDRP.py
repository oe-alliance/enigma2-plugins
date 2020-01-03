# -*- coding: utf-8 -*-
from __future__ import print_function

from twisted.internet.defer import Deferred
from twisted.internet.protocol import ClientFactory, ServerFactory
from twisted.internet import reactor
from twisted.protocols.basic import LineReceiver
from Screens.InfoBar import InfoBar
from enigma import eEPGCache, eDVBVolumecontrol, eServiceCenter, eServiceReference, iServiceInformation
from ServiceReference import ServiceReference
from Components.TimerSanityCheck import TimerSanityCheck
from RecordTimer import RecordTimerEntry

from Screens.MessageBox import MessageBox
from Tools import Notifications
from time import localtime, mktime, strftime, strptime
from os import uname

VERSION = '0.1'
SVDRP_TCP_PORT = 6419
NOTIFICATIONID = 'SVDRPNotification'

CODE_HELP = 214
CODE_EPG = 215
CODE_IMAGE = 216
CODE_HELO = 220
CODE_BYE = 221
CODE_OK = 250
CODE_EPG_START = 354 
CODE_ERR_LOCAL = 451
CODE_UNK = 500
CODE_SYNTAX = 501 
CODE_IMP_FUNC = 502
CODE_IMP_PARAM = 504
CODE_NOK = 550
CODE_ERR = 554
class SimpleVDRProtocol(LineReceiver):
	def __init__(self, client = False):
		self.client = client
		self._channelList = []
		from Components.MovieList import MovieList
		from Tools.Directories import resolveFilename, SCOPE_HDD
		self.movielist = MovieList(eServiceReference("2:0:1:0:0:0:0:0:0:0:" + resolveFilename(SCOPE_HDD)))

	def getChannelList(self):
		if not self._channelList:
			from Components.Sources.ServiceList import ServiceList
			bouquet = eServiceReference('1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.favourites.tv" ORDER BY bouquet')
			slist = ServiceList(bouquet, validate_commands=False)
			services = slist.getServicesAsList(format="S")
			self._channelList = services[:]
		return self._channelList

	def setChannelList(self, channelList):
		self._channelList = channelList

	channelList = property(getChannelList, setChannelList)

	def connectionMade(self):
		self.factory.addClient(self)
		now = strftime('%a %b %d %H:%M:%S %Y', localtime())
		payload = "%d %s SVDRP VideoDiskRecorder (Enigma 2-Plugin %s); %s" % (CODE_HELO, uname()[1], VERSION, now)
		self.sendLine(payload)

	def connectionLost(self, reason):
		self.factory.removeClient(self)

	def stop(self, *args):
		payload = "%d %s closing connection" % (CODE_BYE, uname()[1])
		self.sendLine(payload)
		self.transport.loseConnection()

	def NOT_IMPLEMENTED(self, args):
		print("[SVDRP] command not implemented.")
		payload = "%d command not implemented." % (CODE_IMP_FUNC,)
		self.sendLine(payload)

	def CHAN(self, args):
		# allowed parameters: [ + | - | <number> | <name> | <id> ]
		if args == '+':
			InfoBar.instance.zapDown()
			payload = "%d channel changed" % (CODE_OK,)
		elif args == '-':
			InfoBar.instance.zapUp()
			payload = "%d channel changed" % (CODE_OK,)
		else:
			# can be number, name or id
			payload = "%d parameter not implemented" % (CODE_IMP_PARAM,)

		self.sendLine(payload)

	def LSTC(self, args):
		if args:
			payload = "%d parameter not implemented" % (CODE_IMP_PARAM,)
			return self.sendLine(payload)
		from Components.Sources.ServiceList import ServiceList
		bouquet = eServiceReference('1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.favourites.tv" ORDER BY bouquet')
		slist = ServiceList(bouquet, validate_commands=False)
		services = slist.getServicesAsList(format="SNn")
		if services:
			def getServiceInfoValue(info, sref, what):
				if info is None: return ""
				v = info.getInfo(sref.ref, what)
				if v == -2: return info.getInfoString(sref.ref, what)
				elif v == -1: return "N/A"
				return v
			def sendServiceLine(service, counter, last=False):
				if service[0][:5] == '1:64:':
					# format for markers:  ":Name"
					line = "%d%s:%s" % (CODE_OK, '-' if not last else ' ', service[1])
				else:
					# <id> <full name>,<short name>;<provider>:<freq>:<parameters>:<source>:<srate>:<vpid>:<apid>:<tpid>:<conditional access>:<:sid>:<nid>:<tid>:<:rid>
					# e.g. 5  RTL Television,RTL:12188:h:S19.2E:27500:163:104:105:0:12003:1:1089:0
					sref = ServiceReference(service[0])
					info = sref.info()
					# XXX: how to get this?! o0
					feinfo = None #sref.ref.frontendInfo()
					fedata = feinfo.getAll(True) if feinfo else {}
					prov = getServiceInfoValue(info, sref, iServiceInformation.sProvider)
					frequency = fedata.get("frequency", 0)/1000
					param = -1
					source = '-1'
					srate = -1
					vpid = '-1'
					apid = '-1'
					tpid = -1
					ca = '-1'
					sid = -1
					nid = -1
					tid = -1
					rid = -1
					# TODO: support full format, these are only the important fields ;)
					line = "%d%s%d %s,%s;%s:%d:%s:%s:%d:%s:%s:%d:%s:%d:%d:%d:%d" % (CODE_OK, '-' if not last else ' ', counter, service[1], service[2], prov, frequency, param, source, srate, vpid, apid, tpid, ca, sid, nid, tid, rid)
				self.sendLine(line)

			self.channelList = [x[0] for x in services] # always refresh cache b/c this is what the user works with from now on
			lastItem = services.pop()
			idx = 1
			for service in services:
				sendServiceLine(service, idx)
				idx += 1
			sendServiceLine(lastItem, idx, last=True)
		else:
			payload = "%d no services found" % (CODE_ERR_LOCAL,)
			self.sendLine(payload)

	def sendTimerLine(self, timer, counter, last=False):
		# <number> <flags>:<channel id>:<YYYY-MM-DD>:<HHMM>:<HHMM>:<priority>:<lifetime>:<name>:<auxiliary>
		flags = 0
		if not timer.disabled: flags |= 1
		if timer.state == timer.StateRunning: flags |= 8
		try:
			channelid = self.channelList.index(str(timer.service_ref)) + 1
		except ValueError as e:
			# XXX: ignore timers on channels that are not in our favourite bouquet
			return False
		else:
			datestring = strftime('%Y-%m-%d', localtime(timer.begin))
			beginstring = strftime('%H%M', localtime(timer.begin))
			endstring = strftime('%H%M', localtime(timer.end))
			line = "%d%s%d %d:%d:%s:%s:%s:%d:%d:%s:%s" % (CODE_OK, '-' if not last else ' ', counter, flags, channelid, datestring, beginstring, endstring, 1, 1, timer.name, timer.description)
			self.sendLine(line)
			return True

	def getTimerList(self):
		import NavigationInstance
		list = []
		recordTimer = NavigationInstance.instance.RecordTimer
		list.extend(recordTimer.timer_list)
		list.extend(recordTimer.processed_timers)
		list.sort(key=attrgetter('begin'))
		return list

	def LSTT(self, args):
		list = self.getTimerList()
		lastItem = list.pop()
		idx = 1
		for timer in list:
			self.sendTimerLine(timer, idx)
			idx += 1
		if not self.sendTimerLine(lastItem, idx, last=True):
			# send error if last item failed to send, else the other end might get stuck
			payload = "%d data inconsistency error." % (CODE_ERR_LOCAL,)
			self.sendLine(payload)

	def UPDT(self, args):
		# <id> <settings>
		args = args.split(None, 1)
		if len(args) != 2:
			payload = "%d argument error" % (CODE_SYNTAX,)
			return self.sendLine(payload)

		try:
			timerId = int(args[0])
		except ValueError:
			payload = "%d argument error" % (CODE_SYNTAX,)
			return self.sendLine(payload)

		list = self.getTimerList()

		if timerId < 1:
			payload = "%d argument error" % (CODE_SYNTAX,)
			return self.sendLine(payload)

		if len(list) >= timerId: oldTimer = list[timerId - 1]
		else: oldTimer = None

		try:
			flags, channelid, datestring, beginstring, endstring, priority, lifetime, name, description = args[1].split(':')
			flags = int(flags)
			service_ref = ServiceReference(self.channelList[int(channelid)-1])
			datestruct = strptime(datestring, '%Y-%m-%d')
			timestruct = strptime(beginstring, '%H%M')
			begin = mktime((datestruct.tm_year, datestruct.tm_mon, datestruct.tm_mday, timestruct.tm_hour, timestruct.tm_min, 0, datestruct.tm_wday, datestruct.tm_yday, -1))
			timestruct = strptime(endstring, '%H%M')
			end = mktime((datestruct.tm_year, datestruct.tm_mon, datestruct.tm_mday, timestruct.tm_hour, timestruct.tm_min, 0, datestruct.tm_wday, datestruct.tm_yday, -1))
			del datestruct, timestruct
		except ValueError as e:
			payload = "%d argument error" % (CODE_SYNTAX,)
			return self.sendLine(payload)
		except KeyError as e:
			payload = "%d argument error" % (CODE_SYNTAX,)
			return self.sendLine(payload)

		if end < begin: end += 86400 # Add 1 day, beware - this is evil and might not work correctly due to dst
		timer = RecordTimerEntry(service_ref, begin, end, name, description, 0, disabled=flags & 1 == 0)
		if oldTimer:
			recordTimer.removeEntry(oldTimer)
			timer.justplay = oldTimer.justplay
			timer.afterEvent = oldTimer.afterEvent
			timer.dirname = oldTimer.dirname
			timer.tags = oldTimer.tags
			timer.log_entries = oldTimer.log_entries

		conflict = recordTimer.record(timer)
		if conflict is None:
			return self.sendTimerLine(timer, timerId, last=True)
		else:
			payload = "%d timer conflict detected, original timer lost." % (CODE_ERR_LOCAL,)
			return self.sendLine(payload)

	def NEWT(self, args):
		self.UPDT("999999999 " + args)

	def MODT(self, args):
		# <id> on | off | <settings>
		args = args.split(None, 1)
		if len(args) != 2:
			payload = "%d argument error" % (CODE_SYNTAX,)
			return self.sendLine(payload)

		if args[1] in ('on', 'off'):
			try:
				timerId = int(args[0])
			except ValueError:
				payload = "%d argument error" % (CODE_SYNTAX,)
				return self.sendLine(payload)

			list = self.getTimerList()

			if timerId < 1 or len(list) < timerId:
				payload = "%d argument error" % (CODE_SYNTAX,)
				return self.sendLine(payload)

			timer = list[timerId - 1]
			disable = args[1] == 'off'
			if disable and timer.isRunning():
				payload = "%d timer is running, not disabling." % (CODE_ERR_LOCAL,)
				return self.sendLine(payload)
			else:
				if timer.disabled and not disable:
					timer.enable()
					tsc = TimerSanityCheck(recordTimer.timer_list, timer)
					if not timersanitycheck.check():
						timer.disable()
						payload = "%d timer conflict detected, aborting." % (CODE_ERR_LOCAL,)
						return self.sendLine(payload)
					else:
						if timersanitycheck.doubleCheck(): timer.disable()
				elif not timer.disabled and disable:
					timer.disable()
				recordTimer.timeChanged(timer)
				sef.sendTimerLine(timer, timerId, last=True)
		else:
			self.UPDT(' '.join(args))

	def DELT(self, args):
		try:
			timerId = int(args)
		except ValueError:
			payload = "%d argument error" % (CODE_SYNTAX,)
			return self.sendLine(payload)

		list = self.getTimerList()

		if timerId < 1 or len(list) < timerId:
			payload = "%d argument error" % (CODE_SYNTAX,)
			return self.sendLine(payload)

		timer = list[timerId - 1]
		recordTimer.removeEntry(timer)
		payload = '%d Timer "%d" deleted' % (CODE_OK, timerId)
		self.sendLine(payload)

	def MESG(self, data):
		if not data:
			payload = "%d parameter not implemented" % (CODE_IMP_PARAM,)
			return self.sendLine(payload)

		Notifications.AddNotificationWithID(
			NOTIFICATIONID,
			MessageBox,
			text = data,
			type = MessageBox.TYPE_INFO,
			timeout = 5,
			close_on_any_key = True,
		)
		payload = "%d Message queued" % (CODE_OK,)
		self.sendLine(payload)

	def VOLU(self, args):
		volctrl = eDVBVolumecontrol.getInstance()
		if args == "mute":
			from Components.VolumeControl import VolumeControl
			VolumeControl.instance.volMute()
		elif args == "+":
			from Components.VolumeControl import VolumeControl
			VolumeControl.instance.volUp()
		elif args == "-":
			from Components.VolumeControl import VolumeControl
			VolumeControl.instance.volDown()
		elif args:
			try:
				num = int(args) / 2.55
			except ValueError:
				payload = "%d %s" % (CODE_SYNTAX, str(e).replace('\n', ' ').replace('\r', ''))
				return self.sendLine(payload)
			else:
				volctr.setVolume(num, num)

		if volctrl.isMuted():
			payload = "%d Audio is mute" % (CODE_OK,)
		else:
			payload = "%d Audio volume is %d." % (CODE_OK, volctrl.getVolume()*2.55)
		self.sendLine(payload)

	def HELP(self, args):
		if not len(args) == 2:
			payload = "%d data inconsistency error." % (CODE_ERR_LOCAL,)
			return self.sendLine(payload)
		funcs, args = args
		if not args:
			funcnames = sorted(funcs.keys())
			payload = "%d-This is Enigma2 VDR-Plugin version %s" % (CODE_HELP, VERSION)
			self.sendLine(payload)
			payload = "%d-Topics:" % (CODE_HELP,)
			x = 5
			for func in funcnames:
				if x == 5:
					self.sendLine(payload)
					payload = "%d-    %s" % (CODE_HELP, func)
					x = 1
				else:
					payload +=  "      %s" % (func,)
					x += 1
			self.sendLine(payload)
			payload = "%d-To report bugs in the implementation send email to" % (CODE_HELP,)
			self.sendLine(payload)
			payload = "%d-    svdrp AT ritzmo DOT de" % (CODE_HELP,)
			self.sendLine(payload)
			payload = "%d End of HELP info" % (CODE_HELP,)
			self.sendLine(payload)
		else:
			payload = "%d parameter not implemented" % (CODE_IMP_PARAM,)
			return self.sendLine(payload)

	def LSTR(self, args):
		if args:
			payload = "%d parameter not implemented" % (CODE_IMP_PARAM,)
			return self.sendLine(payload)

		self.movielist.reload()

		def sendMovieLine(sref, info, begin, counter, last=False):
			# <number> <date> <begin> <name>
			ctime = info.getInfo(serviceref, iServiceInformation.sTimeCreate) # XXX: difference to begin? just copied this from webif ;-)
			datestring = strftime('%d.%m.%y', localtime(ctime))
			beginstring = strftime('%H:%M', localtime(ctime))
			servicename = ServiceReference(sref).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')
			line = "%d%s%d %s %s %s" % (CODE_OK, '-' if not last else ' ', counter, datestring, beginstring, servicename)
			self.sendLine(line)

		list = self.movielist.list[:]
		lastItem = list.pop()
		idx = 1
		for serviceref, info, begin, unknown in list:
			sendMovieLine(serviceref, info, begin, idx)
			idx += 1
		sendMovieLine(lastItem[0], lastItem[1], lastItem[2], idx, last=True)

	def DELR(self, args):
		try:
			movieId = int(args)
		except ValueError:
			payload = "%d argument error" % (CODE_SYNTAX,)
			return self.sendLine(payload)

		sref = self.movielist.list[movieId-1][0]
		serviceHandler = eServiceCenter.getInstance()
		offline = serviceHandler.offlineOperations(sref)

		if offline is not None:
			if not offline.deleteFromDisk(0):
				payload = '%d Movie "%d" deleted' % (CODE_OK, movieId)
				return self.sendLine(payload)

		payload = "%d data inconsistency error." % (CODE_ERR_LOCAL,)
		self.sendLine(payload)

	def LSTE(self, args):
		args = args.split()
		first = args and args.pop(0)
		#TODO: find out format of "at <time>"
		if not first or first in ('now', 'next', 'at') or args and args[1] == "at":
			# XXX: "parameter not implemented" might be weird to say in case of no parameters, but who cares :-)
			payload = "%d parameter not implemented" % (CODE_IMP_PARAM,)
			return self.sendLine(payload)
		try:
			channelId = int(first)-1
			service = self.channelList[channelId]
		except ValueError:
			# XXX: add support for sref
			payload = "%d parameter not implemented" % (CODE_IMP_PARAM,)
			return self.sendLine(payload)

		# handle additional parametes "now" and "next"
		type = 0
		time = -1
		endtime = -1
		options = "IBDTSERN"
		if args:
			options = "IBDTSERNX"
			if args[0] == "now":
				type = 0
				endtime = None
			elif args[0] == "next":
				type = 1
				endtime = None

		# fetch data
		epgcache = eEPGCache.getInstance()
		if endtime is None:
			params = (service, type, time)
		else:
			params = (service, type, time, endtime)
		events = epgcache.lookupEvent([options , params])
		if not events:
			return self.sendLine("550 No schedule found")

		# process data
		def sendEventLine(eit, begin, duration, title, description, extended, sref, sname):
			payload = "%d-E %d %d %d 0" % (CODE_EPG, eit, begin, duration)
			self.sendLine(payload)
			payload = "%d-T %s" % (CODE_EPG, title)
			self.sendLine(payload)
			payload = "%d-S %s" % (CODE_EPG, description)
			self.sendLine(payload)
			payload = "%d-D %s" % (CODE_EPG, extended.replace('\xc2\x8a', '|'))
			self.sendLine(payload)
			payload = "%d-e" % (CODE_EPG,)
			self.sendLine(payload)
		lastItem = events.pop()
		payload = "%d-C %s %s" % (CODE_EPG, lastItem[-2], lastItem[-1])
		self.sendLine(payload)
		for event in events:
			sendEventLine(*event)
		sendEventLine(*lastItem)
		payload = "%d-c" % (CODE_EPG,)
		self.sendLine(payload)
		payload = "%d End of EPG data" % (CODE_EPG,)
		self.sendLine(payload)

	def lineReceived(self, data):
		if self.client or not self.transport or not data:
			return

		print("[SVDRP] incoming message:", data)
		list = data.split(' ', 1)
		command = list.pop(0).upper()
		args = list[0] if list else ''

		# still possible: grab, (partially) hitk, (theoretically) movc, next? (dunno what this does), play, stat and completion of existing commands
		funcs = {
			'CHAN': self.CHAN,
			'DELR': self.DELR,
			'DELT': self.DELT,
			'HELP': self.HELP,
			'LSTC': self.LSTC,
			'LSTE': self.LSTE,
			'LSTT': self.LSTT,
			'LSTR': self.LSTR,
			'MESG': self.MESG,
			'MODT': self.MODT,
			'NEWT': self.NEWT,
			'UPDT': self.UPDT,
			'QUIT': self.stop,
			'VOLU': self.VOLU,
		}
		if command == "HELP":
			args = (funcs, args)
		call = funcs.get(command, self.NOT_IMPLEMENTED)

		try:
			call(args)
		except Exception as e:
			import traceback, sys
			traceback.print_exc(file=sys.stdout)
			payload = "%d exception occured: %s" % (CODE_ERR, str(e).replace('\n', ' ').replace('\r', ''))
			self.sendLine(payload)

class SimpleVDRProtocolServerFactory(ServerFactory):
	protocol = SimpleVDRProtocol

	def __init__(self):
		self.clients = []

	def addClient(self, client):
		self.clients.append(client)

	def removeClient(self, client):
		self.clients.remove(client)

	def stopFactory(self):
		for client in self.clients:
			client.stop()

class SimpleVDRProtocolAbstraction:
	serverPort = None
	pending = 0

	def __init__(self):
		self.serverFactory = SimpleVDRProtocolServerFactory()
		self.serverPort = reactor.listenTCP(SVDRP_TCP_PORT, self.serverFactory)
		self.pending += 1

	def maybeClose(self, resOrFail, defer = None):
		self.pending -= 1
		if self.pending == 0:
			if defer:
				defer.callback(True)

	def stop(self):
		defer = Deferred()
		if self.serverPort:
			d = self.serverPort.stopListening()
			if d:
				d.addBoth(self.maybeClose, defer = defer)
			else:
				self.pending -= 1

		if self.pending == 0:
			reactor.callLater(1, defer.callback, True)
		return defer

