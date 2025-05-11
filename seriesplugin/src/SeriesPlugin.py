# -*- coding: utf-8 -*-
# by betonme @2012

from __future__ import absolute_import
import re

import os
import sys

from time import localtime, strftime
from datetime import datetime

# Localization
from . import _

from datetime import datetime

from Components.config import config

from enigma import eServiceCenter, ePythonMessagePump

# Plugin framework
from .Modules import Modules

# Tools
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Tools.Notifications import AddPopup
from Screens.MessageBox import MessageBox

# Plugin internal
from .Logger import log
from .Channels import ChannelsBase
from .XMLTVBase import XMLTVBase
from .ThreadQueue import ThreadQueue
from threading import Thread

import six


#from enigma import ePythonMessagePump


try:
	if (config.plugins.autotimer.timeout.value == 1):
		config.plugins.autotimer.timeout.value = 5
		config.plugins.autotimer.save()
except Exception as e:
	pass


# Constants
AUTOTIMER_PATH = os.path.join(resolveFilename(SCOPE_PLUGINS), "Extensions/AutoTimer/")
SERIESPLUGIN_PATH = os.path.join(resolveFilename(SCOPE_PLUGINS), "Extensions/SeriesPlugin/")

# Globals
instance = None

CompiledRegexpNonDecimal = re.compile(r'[^\d]')
CompiledRegexpReplaceChars = None
CompiledRegexpReplaceDirChars = re.compile(r'[^/\wäöüß\-_\. ]')


def dump(obj):
	for attr in dir(obj):
		log.debug(" %s = %s" % (attr, getattr(obj, attr)))


def getInstance():
	global instance

	if instance is None:

		log.reinit()

		from .plugin import VERSION

		log.debug(" SERIESPLUGIN NEW INSTANCE " + VERSION)
		log.debug(" ", strftime("%a, %d %b %Y %H:%M:%S", localtime()))

		try:
			from Components.SystemInfo import BoxInfo
			log.debug(" DeviceName " + BoxInfo.getItem("model"))
		except:
			sys.exc_clear()

		try:
			from Components.About import about
			log.debug(" EnigmaVersion " + about.getEnigmaVersionString().strip())
			log.debug(" ImageVersion " + about.getVersionString().strip())
		except:
			sys.exc_clear()

		try:
			#http://stackoverflow.com/questions/1904394/python-selecting-to-read-the-first-line-only
			log.debug(" dreamboxmodel " + open("/proc/stb/info/model").readline().strip())
			log.debug(" imageversion " + open("/etc/image-version").readline().strip())
			log.debug(" imageissue " + open("/etc/issue.net").readline().strip())
		except:
			sys.exc_clear()

		try:
			for key, value in six.iteritems(config.plugins.seriesplugin.dict()):
				log.debug(" config..%s = %s" % (key, str(value.value)))
		except Exception as e:
			sys.exc_clear()

		global CompiledRegexpReplaceChars
		try:
			if config.plugins.seriesplugin.replace_chars.value:
				CompiledRegexpReplaceChars = re.compile('[' + config.plugins.seriesplugin.replace_chars.value.replace("\\", "\\\\\\\\") + ']')
		except:
			log.exception(" Config option 'Replace Chars' is no valid regular expression")
			CompiledRegexpReplaceChars = re.compile(r"[:\!/\\,\(\)'\?]")

		# Check autotimer
		try:
			from Plugins.Extensions.AutoTimer.plugin import autotimer
			deprecated = False
			try:
				from Plugins.Extensions.AutoTimer.plugin import AUTOTIMER_VERSION
				if int(AUTOTIMER_VERSION[0]) < 4:
					deprecated = True
			except ImportError:
				AUTOTIMER_VERSION = "deprecated"
				deprecated = True
			log.debug(" AutoTimer: " + AUTOTIMER_VERSION)
			if deprecated:
				log.warning(_("Your autotimer is deprecated") + "\n" + _("Please update it"))
		except ImportError:
			log.debug(" AutoTimer: Not found")

		# Check dependencies
		start = True
		import importlib.util
		dependencies = ["difflib", "json", "re", "xml", "xmlrpc"]
		for dependency in dependencies:
			try:
				spec = importlib.util.find_spec(dependency)
				if spec is None:
					log.error(f"Module {dependency} not found")
			except ImportError:
				start = False
				log.error("Error missing dependency\npython3-" + dependency + "\n\nPlease install the missing python package manually")
		if start:
			instance = SeriesPlugin()

	return instance


def stopWorker():
	global instance
	if instance is not None:
		log.debug(" SERIESPLUGIN STOP WORKER")
		instance.stop()


def resetInstance():
	if config.plugins.seriesplugin.lookup_counter.isChanged():
		config.plugins.seriesplugin.lookup_counter.save()

	global instance
	if instance is not None:
		log.debug(" SERIESPLUGIN INSTANCE STOP")
		instance.stop()
		instance = None

	from .Cacher import clearCache
	clearCache()


def refactorTitle(org_, data):
	if CompiledRegexpReplaceChars:
		org = CompiledRegexpReplaceChars.sub('', org_)
		log.debug(" refactor title org", org_, org)
	else:
		org = org_
	if data:
		if config.plugins.seriesplugin.pattern_title.value and not config.plugins.seriesplugin.pattern_title.value == "Off" and not config.plugins.seriesplugin.pattern_title.value == "Disabled":
			data["org"] = org
			cust_ = config.plugins.seriesplugin.pattern_title.value.strip().format(**data)
			cust = cust_.replace('&amp;', '&').replace('&apos;', "'").replace('&gt;', '>').replace('&lt;', '<').replace('&quot;', '"').replace('  ', ' ')
			log.debug(" refactor title", cust_, cust)
			#check if new title already exist in org on use org in pattern to avoid rename loop
			if "{org:s}" in config.plugins.seriesplugin.pattern_title.value:
				data["org"] = ""
				cust1_ = config.plugins.seriesplugin.pattern_title.value.strip().format(**data)
				cust1 = cust1_.replace('&amp;', '&').replace('&apos;', "'").replace('&gt;', '>').replace('&lt;', '<').replace('&quot;', '"').replace('  ', ' ')
				log.debug(" refactor title without org", cust1)
				if cust1 in org:
					cust = org
			return cust
		else:
			return org
	else:
		return org


def checkIfTitleExistInDescription(org, data):
	#check if use 'org' and 'title' in pattern and series-title already exist in org-description, then remove from org
	if ("{org:s}" in config.plugins.seriesplugin.pattern_description.value) and ("{title:s}" in config.plugins.seriesplugin.pattern_description.value):
		if isinstance(org, str) and isinstance(data["title"], unicode):
			#convert org to unicode for compare with data["title"] if data["title"] has umlauts
			org = unicode(org)
		if data["title"].upper() in org.upper():
			title_str = re.compile(data["title"], re.IGNORECASE)
			org = title_str.sub("", org)
	return org


def refactorDescription(org_, data):
	if CompiledRegexpReplaceChars:
		org = CompiledRegexpReplaceChars.sub('', org_)
		log.debug(" refactor desc org_, org", org_, org)
	else:
		org = org_
	if data:
		if config.plugins.seriesplugin.pattern_description.value and not config.plugins.seriesplugin.pattern_description.value == "Off" and not config.plugins.seriesplugin.pattern_description.value == "Disabled":
			data["org"] = checkIfTitleExistInDescription(org, data)
			cust_ = config.plugins.seriesplugin.pattern_description.value.strip().format(**data)
			cust = cust_.replace("\n", " ").replace('&amp;', '&').replace('&apos;', "'").replace('&gt;', '>').replace('&lt;', '<').replace('&quot;', '"').replace('  ', ' ')
			log.debug(" refactor desc cust_, cust", cust_, cust)
			#check if new description already exist in org on use org in pattern to avoid rename loop
			if "{org:s}" in config.plugins.seriesplugin.pattern_description.value:
				data["org"] = ""
				cust1_ = config.plugins.seriesplugin.pattern_description.value.strip().format(**data)
				cust1 = cust1_.replace("\n", " ").replace('&amp;', '&').replace('&apos;', "'").replace('&gt;', '>').replace('&lt;', '<').replace('&quot;', '"').replace('  ', ' ')
				log.debug(" refactor desc without org", cust1)
				if cust1 in org:
					cust = org
			return cust
		else:
			return org
	else:
		return org


def refactorDirectory(org, data):
	dir = org
	if data:
		if config.plugins.seriesplugin.pattern_directory.value and not config.plugins.seriesplugin.pattern_directory.value == "Off" and not config.plugins.seriesplugin.pattern_directory.value == "Disabled":
			data["org"] = org
			data["home"] = "/media/hdd/movie"
			cust_ = config.plugins.seriesplugin.pattern_directory.value.strip().format(**data)
			cust_ = cust_.replace("\n", "").replace('&amp;', '&').replace('&apos;', "'").replace('&gt;', '>').replace('&lt;', '<').replace('&quot;', '"').replace("  ", " ").replace("//", "/")
			dir = CompiledRegexpReplaceDirChars.sub(' ', cust_)
			log.debug(" refactor dir", org, cust_, dir)
		if dir and not os.path.exists(dir):
			try:
				os.makedirs(dir)
			except:
				log.exception("makedirs exception", dir)
	return dir


def normalizeResult(result):
	if result and isinstance(result, dict):
		log.debug("normalize result")
		title_ = result['title'].strip()
		series_ = result['series'].strip()
		season_ = result['season']
		episode_ = result['episode']

		if config.plugins.seriesplugin.cut_series_title.value and " - " in series_:
			series_, sub_series_title = series_.split(" - ", 1)
		result['rawseason'] = season_ or config.plugins.seriesplugin.default_season.value
		result['rawepisode'] = episode_ or config.plugins.seriesplugin.default_episode.value
		if season_:
			result['season'] = int(CompiledRegexpNonDecimal.sub('', str(season_)) or config.plugins.seriesplugin.default_season.value or "0")
		else:
			result['season'] = int(config.plugins.seriesplugin.default_season.value) or 0
		if episode_:
			result['episode'] = int(CompiledRegexpNonDecimal.sub('', str(episode_)) or config.plugins.seriesplugin.default_episode.value or "0")
		else:
			result['episode'] = int(config.plugins.seriesplugin.default_episode.value) or 0

		if CompiledRegexpReplaceChars:
			title = CompiledRegexpReplaceChars.sub('', title_)
			#log.debug(" normalize title", title_, title)
			series = CompiledRegexpReplaceChars.sub('', series_)
			#log.debug(" normalize series", series_, series)
		else:
			title = title_
			series = series_
		result['title'] = title
		result['series'] = series
		result['date'] = strftime("%d.%m.%Y", localtime(result['begin']))
		result['time'] = strftime("%H:%M:%S", localtime(result['begin']))
		return result
	else:
		log.debug("normalize result failed", str(result))
		return result


class ThreadItem:
	def __init__(self, identifier=None, callback=None, name=None, begin=None, end=None, service=None):
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
			self.start()  # Start blocking code in Thread

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
			if not self.__running:
				break

			log.debug('Worker is processing')

			item = self.__queue.pop()

			result = None

			try:
				result = item.identifier.getEpisode(
					item.name, item.begin, item.end, item.service
				)
			except Exception as e:
				log.debug("Worker: Exception:", str(e))

				# Exception finish job with error
				result = str(e)

			config.plugins.seriesplugin.lookup_counter.value += 1

			self.__messages.push((item.callback, normalizeResult(result)))

			self.__pump.send(0)

		log.debug(' Worker: list is emty, done')
		Thread.__init__(self)
		self.__running = False


class SeriesPlugin(Modules, ChannelsBase):

	def __init__(self):
		log.debug("Main: Init")
		Modules.__init__(self)
		ChannelsBase.__init__(self)

		self.thread = SeriesPluginWorker(self.gotResult)

		# Because of the same XMLFile base class we intantiate a new object
		self.xmltv = XMLTVBase()

		self.serviceHandler = eServiceCenter.getInstance()

		#http://bugs.python.org/issue7980
		datetime.strptime('2012-01-01', '%Y-%m-%d')

		self.identifier_elapsed = self.instantiateModuleWithName(config.plugins.seriesplugin.identifier_elapsed.value)
		#log.debug(self.identifier_elapsed)

		self.identifier_today = self.instantiateModuleWithName(config.plugins.seriesplugin.identifier_today.value)
		#log.debug(self.identifier_today)

		self.identifier_future = self.instantiateModuleWithName(config.plugins.seriesplugin.identifier_future.value)
		#log.debug(self.identifier_future)

		pattern = config.plugins.seriesplugin.pattern_title.value
		pattern = pattern.replace("{org:s}", "(.+)")
		pattern = re.sub(r'{season:?\d*d?}', r'\\d+', pattern)
		pattern = re.sub(r'{episode:?\d*d?}', r'\\d+', pattern)
		pattern = re.sub(r'{rawseason:s}', r'.+', pattern)
		pattern = pattern.replace("{title:s}", ".+")
		self.compiledRegexpSeries = re.compile(pattern)

	################################################
	# Identifier functions
	def getLogo(self, future=False, today=False, elapsed=False):
		if elapsed:
			return self.identifier_elapsed and self.identifier_elapsed.getLogo(future, today, elapsed)
		elif today:
			return self.identifier_today and self.identifier_today.getLogo(future, today, elapsed)
		elif future:
			return self.identifier_future and self.identifier_future.getLogo(future, today, elapsed)
		else:
			return None

	def getEpisode(self, callback, name, begin, end=None, service=None, future=False, today=False, elapsed=False, block=False, rename=False):

		if config.plugins.seriesplugin.skip_during_records.value:
			try:
				import NavigationInstance
				if NavigationInstance.instance.RecordTimer.isRecording():
					msg = _("Skip check during running records") + "\n\n" + _("Can be configured within the setup")
					log.warning(msg)
					if callable(callback):
						callback(msg)
					return msg
			except:
				pass

		# Check for episode information in title
		match = self.compiledRegexpSeries.match(name)
		if match:
			#log.debug(match.group(0))     # Entire match
			#log.debug(match.group(1))     # First parenthesized subgroup
			if not rename and config.plugins.seriesplugin.skip_pattern_match.value:
				msg = _("Skip check because of pattern match") + "\n" + name + "\n\n" + _("Can be configured within the setup")
				log.warning(msg)
				if callable(callback):
					callback(msg)
				return msg
			if match.group(1):
				name = match.group(1)

		if elapsed:
			identifier = self.identifier_elapsed
		elif today:
			identifier = self.identifier_today
		elif future:
			identifier = self.identifier_future
		else:
			identifier = self.modules and self.instantiateModule(next(six.itervalues(self.modules)))

		if not identifier:
			msg = _("No identifier available") + "\n\n" + _("Please check Your installation")
			log.error(msg)
			if callable(callback):
				callback(msg)
			return msg

		elif self.channelsEmpty():
			msg = _("Channels are not matched") + "\n\n" + _("Please open the channel editor (setup) and match them")
			log.error(msg)
			if callable(callback):
				callback(msg)
			return msg

		else:
			# Reset title search depth on every new request
			identifier.search_depth = 0

			# Reset the knownids on every new request
			identifier.knownids = []

			try:
				serviceref = service.toString()
			except:
				sys.exc_clear()
				serviceref = str(service)
			serviceref = re.sub('::.*', ':', serviceref)

			if block is False:

				self.thread.add(ThreadItem(identifier, callback, name, begin, end, serviceref))

			else:

				result = None

				try:
					result = identifier.getEpisode(name, begin, end, serviceref)
				except Exception as e:
					log.exception("Worker:", str(e))

					# Exception finish job with error
					result = str(e)

				config.plugins.seriesplugin.lookup_counter.value += 1

				data = normalizeResult(result)

				if callable(callback):
					callback(data)

				return data

	def gotResult(self, msg):
		log.debug(" Main: Thread: gotResult:", msg)
		callback, data = msg
		if callable(callback):
			callback(data)

		if (config.plugins.seriesplugin.lookup_counter.value == 10) \
			or (config.plugins.seriesplugin.lookup_counter.value == 100) \
			or (config.plugins.seriesplugin.lookup_counter.value % 1000 == 0):
			from .plugin import ABOUT
			about = ABOUT.format(**{'lookups': config.plugins.seriesplugin.lookup_counter.value})
			AddPopup(
				about,
				MessageBox.TYPE_INFO,
				-1,
				'SP_PopUp_ID_About'
			)

	def stop(self):
		log.debug(" Main: stop")
		if self.thread:
			self.thread.stop()
		# NOTE: while we don't need to join the thread, we should do so in case it's currently parsing
		#self.thread.join()

		self.thread = None
		self.saveXML()
		self.xmltv.writeXMLTVConfig()
