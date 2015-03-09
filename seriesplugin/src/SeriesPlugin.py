# -*- coding: utf-8 -*-
# by betonme @2012

import re

import os, sys, traceback

from time import localtime, strftime
from datetime import datetime

# Localization
from . import _

from datetime import datetime

from Components.config import config

from enigma import eServiceReference, iServiceInformation, eServiceCenter, ePythonMessagePump
from ServiceReference import ServiceReference

# Plugin framework
from Modules import Modules

# Tools
from Tools.BoundFunction import boundFunction
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Tools.Notifications import AddPopup
from Screens.MessageBox import MessageBox

# Plugin internal
from IdentifierBase import IdentifierBase
from Logger import splog
from Channels import ChannelsBase
from ThreadQueue import ThreadQueue
from threading import Thread, currentThread, _get_ident
#from enigma import ePythonMessagePump


try:
	if(config.plugins.autotimer.timeout.value == 1):
		config.plugins.autotimer.timeout.value = 5
		config.plugins.autotimer.save()
except Exception as e:
	pass


# Constants
AUTOTIMER_PATH  = os.path.join( resolveFilename(SCOPE_PLUGINS), "Extensions/AutoTimer/" )
SERIESPLUGIN_PATH  = os.path.join( resolveFilename(SCOPE_PLUGINS), "Extensions/SeriesPlugin/" )


# Globals
instance = None

CompiledRegexpNonDecimal = re.compile(r'[^\d]+')

def dump(obj):
	for attr in dir(obj):
		splog( "SP: %s = %s" % (attr, getattr(obj, attr)) )


def getInstance():
	global instance
	
	if instance is None:
		
		from plugin import VERSION
		
		splog("SP: SERIESPLUGIN NEW INSTANCE " + VERSION)
		
		try:
			from Tools.HardwareInfo import HardwareInfo
			splog( "SP: DeviceName " + HardwareInfo().get_device_name().strip() )
			#from os import uname
			#uname()[0]'Linux'
			#uname()[1]'dm7080'
			#uname()[2]'3.4-3.0-dm7080'
			#uname()[3]'#13 SMP Thu Dec 4 00:25:51 UTC 2014'
			#uname()[4]'mips'
		except:
			sys.exc_clear()
		
		try:
			from Components.About import about
			splog( "SP: EnigmaVersion " + about.getEnigmaVersionString().strip() )
			splog( "SP: ImageVersion " + about.getVersionString().strip() )
		except:
			sys.exc_clear()
		
		try:
			#http://stackoverflow.com/questions/1904394/python-selecting-to-read-the-first-line-only
			splog( "SP: dreamboxmodel " + open("/proc/stb/info/model").readline().strip() )
			splog( "SP: imageversion " + open("/etc/image-version").readline().strip() )
			splog( "SP: imageissue " + open("/etc/issue.net").readline().strip() )
		except:
			sys.exc_clear()
		
		try:
			for key, value in config.plugins.seriesplugin.dict().iteritems():
				splog( "SP: config..%s = %s" % (key, str(value.value)) )
		except Exception as e:
			sys.exc_clear()
		
		#try:
		#	if os.path.exists(SERIESPLUGIN_PATH):
		#		dirList = os.listdir(SERIESPLUGIN_PATH)
		#		for fname in dirList:
		#			splog( "SP: ", fname, datetime.fromtimestamp( int( os.path.getctime( os.path.join(SERIESPLUGIN_PATH,fname) ) ) ).strftime('%Y-%m-%d %H:%M:%S') )
		#except Exception as e:
		#	sys.exc_clear()
		#try:
		#	if os.path.exists(AUTOTIMER_PATH):
		#		dirList = os.listdir(AUTOTIMER_PATH)
		#		for fname in dirList:
		#			splog( "SP: ", fname, datetime.fromtimestamp( int( os.path.getctime( os.path.join(AUTOTIMER_PATH,fname) ) ) ).strftime('%Y-%m-%d %H:%M:%S') )
		#except Exception as e:
		#	sys.exc_clear()
		
		instance = SeriesPlugin()
		#instance[os.getpid()] = SeriesPlugin()
		splog( "SP: ", strftime("%a, %d %b %Y %H:%M:%S", localtime()) )
	
	return instance

def resetInstance():
	if config.plugins.seriesplugin.lookup_counter.isChanged():
		config.plugins.seriesplugin.lookup_counter.save()
	
	global instance
	if instance is not None:
		splog("SP: SERIESPLUGIN INSTANCE STOP")
		instance.stop()
		instance = None
	
	from Cacher import cache
	global cache
	cache = {}


def refactorTitle(org, data):
	if data:
		season, episode, title, series = data
		if config.plugins.seriesplugin.pattern_title.value and not config.plugins.seriesplugin.pattern_title.value == "Off":
			if config.plugins.seriesplugin.replace_chars.value:
				repl = re.compile('['+config.plugins.seriesplugin.replace_chars.value.replace("\\", "\\\\\\\\")+']')
				splog("SP: refactor org", org)
				org = repl.sub('', org)
				splog("SP: refactor org", org)
				
				splog("SP: refactor title", title)
				title = repl.sub('', title)
				splog("SP: refactor title", title)
				
				splog("SP: refactor series", series)
				series = repl.sub('', series)
				splog("SP: refactor series", series)
			#return config.plugins.seriesplugin.pattern_title.value.strip().format( **{'org': org, 'season': season, 'episode': episode, 'title': title, 'series': series} )
			cust_title = config.plugins.seriesplugin.pattern_title.value.strip().format( **{'org': org, 'season': season, 'episode': episode, 'title': title, 'series': series} )
			return cust_title.replace('&amp;','&').replace('&apos;',"'").replace('&gt;','>').replace('&lt;','<').replace('&quot;','"').replace("\'","").replace('  ',' ')
		else:
			return org
	else:
		return org

def refactorDescription(org, data):
	if data:
		season, episode, title, series = data
		if config.plugins.seriesplugin.pattern_description.value and not config.plugins.seriesplugin.pattern_description.value == "Off":
			##if season == 0 and episode == 0:
			##	description = config.plugins.seriesplugin.pattern_description.value.strip().format( **{'org': org, 'title': title, 'series': series} )
			##else:
			#description = config.plugins.seriesplugin.pattern_description.value.strip().format( **{'org': org, 'season': season, 'episode': episode, 'title': title, 'series': series} )
			#description = description.replace("\n", " ")
			#return description
			cust_plot = config.plugins.seriesplugin.pattern_description.value.strip().format( **{'org': org, 'season': season, 'episode': episode, 'title': title, 'series': series} )
			return cust_plot.replace("\n", " ").replace('&amp;','&').replace('&apos;',"'").replace('&gt;','>').replace('&lt;','<').replace('&quot;','"').replace("\'","").replace('  ',' ')
		else:
			return org
	else:
		return org


class ThreadItem:
	def __init__(self, identifier = None, callback = None, name = None, begin = None, end = None, service = None):
		self.identifier = identifier
		self.callback = callback
		self.name = name
		self.begin = begin
		self.end = end
		self.service = service


class SeriesPluginWorker(Thread):
	
	def __init__(self, callback):
		Thread.__init__(self)
		self.callback = callback
		self.__running = False
		self.__messages = ThreadQueue()
		self.__pump = ePythonMessagePump()
		try:
			self.__pump_recv_msg_conn = self.__pump.recv_msg.connect(self.gotThreadMsg)
		except:
			self.__pump.recv_msg.get().append(self.gotThreadMsg)
		self.__queue = ThreadQueue()

	def empty(self):
		return self.__queue.empty()
	
	def finished(self):
		return not self.__running

	def add(self, item):
		
		from ctypes import CDLL
		SYS_gettid = 4222
		libc = CDLL("libc.so.6")
		tid = libc.syscall(SYS_gettid)
		splog('SP: Worker add from thread: ', currentThread(), _get_ident(), self.ident, os.getpid(), tid )
		
		self.__queue.push(item)
		
		if not self.__running:
			self.__running = True
			self.start() # Start blocking code in Thread
	
	def gotThreadMsg(self, msg=None):
		
		from ctypes import CDLL
		SYS_gettid = 4222
		libc = CDLL("libc.so.6")
		tid = libc.syscall(SYS_gettid)
		splog('SP: Worker got message: ', currentThread(), _get_ident(), self.ident, os.getpid(), tid )
		
		data = self.__messages.pop()
		if callable(self.callback):
			self.callback(data)

	def stop(self):
		self.running = False
		try:
			self.__pump.recv_msg.get().remove(self.gotThreadMsg)
		except:
			pass
		self.__pump_recv_msg_conn = None
	
	def run(self):
		
		from ctypes import CDLL
		SYS_gettid = 4222
		libc = CDLL("libc.so.6")
		tid = libc.syscall(SYS_gettid)
		splog('SP: Worker got message: ', currentThread(), _get_ident(), self.ident, os.getpid(), tid )
		
		while not self.__queue.empty():
			
			# NOTE: we have to check this here and not using the while to prevent the parser to be started on shutdown
			if not self.__running: break
			
			item = self.__queue.pop()
			
			splog('SP: Worker is processing')
			
			result = None
			
			try:
				result = item.identifier.getEpisode(
					item.name, item.begin, item.end, item.service
				)
			except Exception, e:
				splog("SP: Worker: Exception:", str(e))
				
				# Exception finish job with error
				result = str(e)
			
			config.plugins.seriesplugin.lookup_counter.value += 1
			
			splog("SP: Worker: result")
			if result and len(result) == 4:
				season, episode, title, series = result
				season = int(CompiledRegexpNonDecimal.sub('', season))
				episode = int(CompiledRegexpNonDecimal.sub('', episode))
				title = title.strip()
				splog("SP: Worker: result callback")
				self.__messages.push( (item.callback, (season, episode, title, series)) )
			else:
				splog("SP: Worker: result failed")
				self.__messages.push( (item.callback, result) )
			self.__pump.send(0)
			#from twisted.internet import reactor
			#reactor.callFromThread(self.gotThreadMsg)
		
		splog('SP: Worker: list is emty, done')
		Thread.__init__(self)
		self.__running = False


class SeriesPlugin(Modules, ChannelsBase):

	def __init__(self):
		splog("SP: Main: Init")
		self.thread = SeriesPluginWorker(self.gotResult)
		Modules.__init__(self)
		ChannelsBase.__init__(self)
		
		self.serviceHandler = eServiceCenter.getInstance()
		
		#http://bugs.python.org/issue7980
		datetime.strptime('2012-01-01', '%Y-%m-%d')
		
		self.identifier_elapsed = self.instantiateModuleWithName( config.plugins.seriesplugin.identifier_elapsed.value )
		#splog(self.identifier_elapsed)
		
		self.identifier_today = self.instantiateModuleWithName( config.plugins.seriesplugin.identifier_today.value )
		#splog(self.identifier_today)
		
		self.identifier_future = self.instantiateModuleWithName( config.plugins.seriesplugin.identifier_future.value )
		#splog(self.identifier_future)
		
		pattern = config.plugins.seriesplugin.pattern_title.value
		pattern = pattern.replace("{org:s}", "(.+)")
		pattern = re.sub('{season:?\d*d?}', '\d+', pattern)
		pattern = re.sub('{episode:?\d*d?}', '\d+', pattern)
		pattern = pattern.replace("{title:s}", ".+")
		self.compiledRegexpSeries = re.compile(pattern)
	
	################################################
	# Identifier functions
	def getIdentifier(self, future=False, today=False, elapsed=False):
		if elapsed:
			return self.identifier_elapsed and self.identifier_elapsed.getName()
		elif today:
			return self.identifier_today and self.identifier_today.getName()
		elif future:
			return self.identifier_future and self.identifier_future.getName()
		else:
			return None
	
	def getEpisode(self, callback, name, begin, end=None, service=None, future=False, today=False, elapsed=False, rename=False):
		#available = False
		
		if config.plugins.seriesplugin.skip_during_records.value:
			try:
				import NavigationInstance
				if NavigationInstance.instance.RecordTimer.isRecording():
					splog("SP: Main: Skip check during running records")
					return
			except:
				pass
		
		# Check for episode information in title
		match = self.compiledRegexpSeries.match(name)
		if match:
			#splog(match.group(0))     # Entire match
			#splog(match.group(1))     # First parenthesized subgroup
			if not rename and config.plugins.seriesplugin.skip_pattern_match.value:
				splog("SP: Main: Skip check because of pattern match")
				return
			if match.group(1):
				name = match.group(1)
		
		begin = datetime.fromtimestamp(begin)
		splog("SP: Main: begin:", begin.strftime('%Y-%m-%d %H:%M:%S'))
		end = datetime.fromtimestamp(end)
		splog("SP: Main: end:", end.strftime('%Y-%m-%d %H:%M:%S'))
		
		if elapsed:
			identifier = self.identifier_elapsed
		elif today:
			identifier = self.identifier_today
		elif future:
			identifier = self.identifier_future
		else:
			identifier = None
		
		if not identifier:
			callback( "Error: No identifier available" )
		
		elif identifier.channelsEmpty():
			callback( "Error: Open setup and channel editor" )
		
		else:
			# Reset title search depth on every new request
			identifier.search_depth = 0;
			
			# Reset the knownids on every new request
			identifier.knownids = []
			
			#if isinstance(service, eServiceReference):
			try:
				serviceref = service.toString()
			#else:
			except:
				sys.exc_clear()
				serviceref = str(service)
			serviceref = re.sub('::.*', ':', serviceref)

			self.thread.add( ThreadItem(identifier, callback, name, begin, end, serviceref) )
			
			return identifier.getName()

	def getEpisodeBlocking(self, name, begin, end=None, service=None, future=False, today=False, elapsed=False, rename=False):
		#available = False
		
		if config.plugins.seriesplugin.skip_during_records.value:
			try:
				import NavigationInstance
				if NavigationInstance.instance.RecordTimer.isRecording():
					splog("SP: Main: Skip check during running records")
					return
			except:
				pass
		
		# Check for episode information in title
		match = self.compiledRegexpSeries.match(name)
		if match:
			#splog(match.group(0))     # Entire match
			#splog(match.group(1))     # First parenthesized subgroup
			if not rename and config.plugins.seriesplugin.skip_pattern_match.value:
				splog("SP: Main: Skip check because of pattern match")
				return
			if match.group(1):
				name = match.group(1)
		
		begin = datetime.fromtimestamp(begin)
		splog("SP: Main: begin:", begin.strftime('%Y-%m-%d %H:%M:%S'))
		end = datetime.fromtimestamp(end)
		splog("SP: Main: end:", end.strftime('%Y-%m-%d %H:%M:%S'))
		
		if elapsed:
			identifier = self.identifier_elapsed
		elif today:
			identifier = self.identifier_today
		elif future:
			identifier = self.identifier_future
		else:
			identifier = None
		
		if not identifier:
			callback( "Error: No identifier available" )
		
		elif identifier.channelsEmpty():
			callback( "Error: Open setup and channel editor" )
		
		else:
			# Reset title search depth on every new request
			identifier.search_depth = 0;
			
			# Reset the knownids on every new request
			identifier.knownids = []
			
			#if isinstance(service, eServiceReference):
			try:
				serviceref = service.toString()
			#else:
			except:
				sys.exc_clear()
				serviceref = str(service)
			serviceref = re.sub('::.*', ':', serviceref)
			
			result = None
			
			try:
				result = identifier.getEpisode( name, begin, end, serviceref )
			except Exception, e:
				splog("SP: Worker: Exception:", str(e))
				
				# Exception finish job with error
				result = str(e)
			
			config.plugins.seriesplugin.lookup_counter.value += 1
			
			splog("SP: Worker: result")
			if result and len(result) == 4:
				season, episode, title, series = result
				season = int(CompiledRegexpNonDecimal.sub('', season))
				episode = int(CompiledRegexpNonDecimal.sub('', episode))
				title = title.strip()
				splog("SP: Worker: result callback")
				return (season, episode, title, series)
			else:
				splog("SP: Worker: result failed")
				return result

	def gotResult(self, msg):
		splog("SP: Main: Thread: gotResult:", msg)
		callback, data = msg
		if callable(callback):
			callback(data)
		
		if (config.plugins.seriesplugin.lookup_counter.value == 10) \
			or (config.plugins.seriesplugin.lookup_counter.value == 100) \
			or (config.plugins.seriesplugin.lookup_counter.value % 1000 == 0):
			from plugin import ABOUT
			about = ABOUT.format( **{'lookups': config.plugins.seriesplugin.lookup_counter.value} )
			AddPopup(
				about,
				MessageBox.TYPE_INFO,
				-1,
				'SP_PopUp_ID_About'
			)

	def stop(self):
		splog("SP: Main: stop")
		self.thread.stop()
		# NOTE: while we don't need to join the thread, we should do so in case it's currently parsing
		#self.thread.join()
		
		self.thread = None
		self.saveXML()
