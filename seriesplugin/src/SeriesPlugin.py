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
from Logger import logDebug, initLog, logInfo
from Channels import ChannelsBase
from XMLTVBase import XMLTVBase
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
CompiledRegexpReplaceChars = None
CompiledRegexpReplaceDirChars = re.compile('[^/\w\-_\. ]')

def dump(obj):
	for attr in dir(obj):
		logDebug( " %s = %s" % (attr, getattr(obj, attr)) )


def getInstance():
	global instance
	
	if instance is None:
		
		initLog()
		
		from plugin import VERSION
		
		logDebug(" SERIESPLUGIN NEW INSTANCE " + VERSION)
		
		try:
			from Tools.HardwareInfo import HardwareInfo
			logDebug( " DeviceName " + HardwareInfo().get_device_name().strip() )
		except:
			sys.exc_clear()
		
		try:
			from Components.About import about
			logDebug( " EnigmaVersion " + about.getEnigmaVersionString().strip() )
			logDebug( " ImageVersion " + about.getVersionString().strip() )
		except:
			sys.exc_clear()
		
		try:
			#http://stackoverflow.com/questions/1904394/python-selecting-to-read-the-first-line-only
			logDebug( " dreamboxmodel " + open("/proc/stb/info/model").readline().strip() )
			logDebug( " imageversion " + open("/etc/image-version").readline().strip() )
			logDebug( " imageissue " + open("/etc/issue.net").readline().strip() )
		except:
			sys.exc_clear()
		
		try:
			for key, value in config.plugins.seriesplugin.dict().iteritems():
				logDebug( " config..%s = %s" % (key, str(value.value)) )
		except Exception as e:
			sys.exc_clear()
		
		global CompiledRegexpReplaceChars
		try:
			if config.plugins.seriesplugin.replace_chars.value:
				CompiledRegexpReplaceChars = re.compile('['+config.plugins.seriesplugin.replace_chars.value.replace("\\", "\\\\\\\\")+']')
		except:
			logInfo( " Config option 'Replace Chars' is no valid regular expression" )
			CompiledRegexpReplaceChars = re.compile("[:\!/\\,\(\)'\?]")
		
		instance = SeriesPlugin()
		
		logDebug( " ", strftime("%a, %d %b %Y %H:%M:%S", localtime()) )
	
	return instance

def stopWorker():
	global instance
	if instance is not None:
		logDebug(" SERIESPLUGIN STOP WORKER")
		instance.stop()

def resetInstance():
	if config.plugins.seriesplugin.lookup_counter.isChanged():
		config.plugins.seriesplugin.lookup_counter.save()
	
	global instance
	if instance is not None:
		logDebug(" SERIESPLUGIN INSTANCE STOP")
		instance.stop()
		instance = None
	
	from Cacher import clearCache
	clearCache()


def refactorTitle(org_, data):
	if CompiledRegexpReplaceChars:
		org = CompiledRegexpReplaceChars.sub('', org_)
		logDebug(" refactor title org", org_, org)
	else:
		org = org_
	if data:
		season, episode, title, series = data
		if config.plugins.seriesplugin.pattern_title.value and not config.plugins.seriesplugin.pattern_title.value == "Off" and not config.plugins.seriesplugin.pattern_title.value == "Disabled":
			cust_ = config.plugins.seriesplugin.pattern_title.value.strip().format( **{'org': org, 'season': season, 'episode': episode, 'title': title, 'series': series} )
			cust = cust_.replace('&amp;','&').replace('&apos;',"'").replace('&gt;','>').replace('&lt;','<').replace('&quot;','"').replace('/',' ').replace('  ',' ')
			logDebug(" refactor title", cust_, cust)
			return cust
		else:
			return org
	else:
		return org

def refactorDescription(org_, data):
	if CompiledRegexpReplaceChars:
		org = CompiledRegexpReplaceChars.sub('', org_)
		logDebug(" refactor desc", org_, org)
	else:
		org = org_
	if data:
		season, episode, title, series = data
		if config.plugins.seriesplugin.pattern_description.value and not config.plugins.seriesplugin.pattern_description.value == "Off" and not config.plugins.seriesplugin.pattern_description.value == "Disabled":
			cust_ = config.plugins.seriesplugin.pattern_description.value.strip().format( **{'org': org, 'season': season, 'episode': episode, 'title': title, 'series': series} )
			cust = cust_.replace("\n", " ").replace('&amp;','&').replace('&apos;',"'").replace('&gt;','>').replace('&lt;','<').replace('&quot;','"').replace('/',' ').replace('  ',' ')
			logDebug(" refactor desc", cust_, cust)
			return cust
		else:
			return org
	else:
		return org

def refactorDirectory(org, data):
	dir = org
	if data:
		season, episode, title, series = data
		if config.plugins.seriesplugin.pattern_directory.value and not config.plugins.seriesplugin.pattern_directory.value == "Off" and not config.plugins.seriesplugin.pattern_directory.value == "Disabled":
			cust_ = config.plugins.seriesplugin.pattern_directory.value.strip().format( **{'org': org, 'season': season, 'episode': episode, 'title': title, 'series': series} )
			cust_ = cust_.replace("\n", "").replace('&amp;','&').replace('&apos;',"'").replace('&gt;','>').replace('&lt;','<').replace('&quot;','"').replace("  ", " ").replace("//", "/")
			dir = CompiledRegexpReplaceDirChars.sub(' ', cust_)
			logDebug(" refactor dir", org, cust_, dir)
		if not os.path.exists(dir):
			try:
				os.makedirs(dir)
			except:
				logDebug("makedirs error", dir)
	return dir

def normalizeResult(result):
	if result and len(result) == 4:
		logDebug(" Worker: result callback")
		season, episode, title_, series_ = result
		season = int(CompiledRegexpNonDecimal.sub('', str(season)) or config.plugins.seriesplugin.default_season.value)
		episode = int(CompiledRegexpNonDecimal.sub('', str(episode)) or config.plugins.seriesplugin.default_episode.value)
		title_ = title_.strip()
		series_ = series_.strip()
		if CompiledRegexpReplaceChars:
			title = CompiledRegexpReplaceChars.sub('', title_)
			logDebug(" normalize title", title_, title)
			
			series = CompiledRegexpReplaceChars.sub('', series_)
			logDebug(" normalize serie", series_, series)
		else:
			title = title_
			series = series_
		return (season, episode, title, series)
	else:
		logDebug(" Worker: result failed", str(result))
		return result


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
		
		self.__queue.push(item)
		
		if not self.__running:
			self.__running = True
			self.start() # Start blocking code in Thread
	
	def gotThreadMsg(self, msg=None):
		
		data = self.__messages.pop()
		if callable(self.callback):
			self.callback(data)

	def stop(self):
		self.running = False
		self.__queue = ThreadQueue()
		try:
			self.__pump.recv_msg.get().remove(self.gotThreadMsg)
		except:
			pass
		self.__pump_recv_msg_conn = None
	
	def run(self):
		
		while not self.__queue.empty():
			
			# NOTE: we have to check this here and not using the while to prevent the parser to be started on shutdown
			if not self.__running: break
			
			logDebug('Worker is processing')
			
			item = self.__queue.pop()
			
			result = None
			
			try:
				result = item.identifier.getEpisode(
					item.name, item.begin, item.end, item.service
				)
			except Exception, e:
				logDebug("Worker: Exception:", str(e))
				
				# Exception finish job with error
				result = str(e)
			
			config.plugins.seriesplugin.lookup_counter.value += 1
			
			self.__messages.push( (item.callback, normalizeResult(result)) )
			
			self.__pump.send(0)
		
		logDebug(' Worker: list is emty, done')
		Thread.__init__(self)
		self.__running = False


class SeriesPlugin(Modules, ChannelsBase):

	def __init__(self):
		logDebug("Main: Init")
		self.thread = SeriesPluginWorker(self.gotResult)
		Modules.__init__(self)
		ChannelsBase.__init__(self)
		
		# Because of the same XMLFile base class we intantiate a new object
		self.xmltv = XMLTVBase()
		
		self.serviceHandler = eServiceCenter.getInstance()
		
		#http://bugs.python.org/issue7980
		datetime.strptime('2012-01-01', '%Y-%m-%d')
		
		self.identifier_elapsed = self.instantiateModuleWithName( config.plugins.seriesplugin.identifier_elapsed.value )
		#logDebug(self.identifier_elapsed)
		
		self.identifier_today = self.instantiateModuleWithName( config.plugins.seriesplugin.identifier_today.value )
		#logDebug(self.identifier_today)
		
		self.identifier_future = self.instantiateModuleWithName( config.plugins.seriesplugin.identifier_future.value )
		#logDebug(self.identifier_future)
		
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
	
	def getEpisodeBlocking(self, name, begin, end=None, service=None, future=False, today=False, elapsed=False, rename=False):
		
		return self.getEpisode(None, name, begin, end, service, future, today, elapsed, rename, block=True)

	def getEpisode(self, callback, name, begin_, end_=None, service=None, future=False, today=False, elapsed=False, rename=False, block=False):
		
		if config.plugins.seriesplugin.skip_during_records.value:
			try:
				import NavigationInstance
				if NavigationInstance.instance.RecordTimer.isRecording():
					msg = _("Skip check during running records (Can be disabled)")
					logDebug( msg)
					if callable(callback):
						callback(msg)
					return msg
			except:
				pass
		
		# Check for episode information in title
		match = self.compiledRegexpSeries.match(name)
		if match:
			#logDebug(match.group(0))     # Entire match
			#logDebug(match.group(1))     # First parenthesized subgroup
			if not rename and config.plugins.seriesplugin.skip_pattern_match.value:
				logDebug(" Main: Skip check because of pattern match")
				return
			if match.group(1):
				name = match.group(1)
		
		begin = datetime.fromtimestamp(begin_)
		logDebug(" Main: begin:", begin.strftime('%Y-%m-%d %H:%M:%S'), str(begin_))
		
		end = datetime.fromtimestamp(end_)
		logDebug(" Main: end:", end.strftime('%Y-%m-%d %H:%M:%S'), str(end_))
		
		if elapsed:
			identifier = self.identifier_elapsed
		elif today:
			identifier = self.identifier_today
		elif future:
			identifier = self.identifier_future
		else:
			identifier = None
		
		if not identifier:
			if callable(callback):
				callback( "Error: No identifier available" )
		
		elif self.channelsEmpty():
			if callable(callback):
				callback( "Error: Open setup and channel editor" )
		
		else:
			# Reset title search depth on every new request
			identifier.search_depth = 0;
			
			# Reset the knownids on every new request
			identifier.knownids = []
			
			try:
				serviceref = service.toString()
			except:
				sys.exc_clear()
				serviceref = str(service)
			serviceref = re.sub('::.*', ':', serviceref)

			if block == False:
				
				self.thread.add( ThreadItem(identifier, callback, name, begin, end, serviceref) )
				
				return identifier.getName(not elapsed)
				
			else:
				
				result = None
				
				try:
					result = identifier.getEpisode( name, begin, end, serviceref )
				except Exception, e:
					logDebug(" Worker: Exception:", str(e))
					
					# Exception finish job with error
					result = str(e)
				
				config.plugins.seriesplugin.lookup_counter.value += 1
				
				return normalizeResult(result)

	def gotResult(self, msg):
		logDebug(" Main: Thread: gotResult:", msg)
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
		logDebug(" Main: stop")
		if self.thread:
			self.thread.stop()
		# NOTE: while we don't need to join the thread, we should do so in case it's currently parsing
		#self.thread.join()
		
		self.thread = None
		self.saveXML()
		self.xmltv.writeXMLTVConfig()
