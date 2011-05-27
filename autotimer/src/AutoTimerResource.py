from AutoTimer import AutoTimer
from Components.config import config
from RecordTimer import AFTEREVENT
from twisted.web import http, resource
try:
	from urllib import unquote
except ImportError as ie:
	from urllib.parse import unquote
from enigma import eServiceReference
from . import _, iteritems
from . import plugin

API_VERSION = "1.0"

class AutoTimerBaseResource(resource.Resource):
	_remove = False
	def getAutoTimerInstance(self):
		if plugin.autotimer is None:
			self._remove = True
			autotimer = AutoTimer()
			try:
				autotimer.readXml()
			except Exception:
				# TODO: proper error handling
				pass
			return autotimer
		self._remove = False
		return plugin.autotimer
	def returnResult(self, req, state, statetext):
		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'application; xhtml+xml')
		req.setHeader('charset', 'UTF-8')

		return """<?xml version=\"1.0\" encoding=\"UTF-8\" ?>
<e2simplexmlresult>
	<e2state>%s</e2state>
	<e2statetext>%s</e2statetext>
</e2simplexmlresult>""" % ('True' if state else 'False', statetext)


class AutoTimerDoParseResource(AutoTimerBaseResource):
	def render(self, req):
		autotimer = self.getAutoTimerInstance()
		ret = autotimer.parseEPG()
		output = _("Found a total of %d matching Events.\n%d Timer were added and %d modified, %d conflicts encountered, %d similars added.") % (ret[0], ret[1], ret[2], len(ret[4]), len(ret[5]))

		if self._remove:
			autotimer.writeXml()

		return self.returnResult(req, True, output)

class AutoTimerListAutoTimerResource(AutoTimerBaseResource):
	def render(self, req):
		autotimer = self.getAutoTimerInstance()

		# show xml
		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'application; xhtml+xml')
		req.setHeader('charset', 'UTF-8')
		return ''.join(autotimer.getXml())

class AutoTimerRemoveAutoTimerResource(AutoTimerBaseResource):
	def render(self, req):
		autotimer = self.getAutoTimerInstance()

		id = req.args.get("id")
		if id:
			autotimer.remove(int(id[0]))
			if self._remove:
				autotimer.writeXml()
			return self.returnResult(req, True, _("AutoTimer was removed"))
		else:
			return self.returnResult(req, False, _("missing parameter \"id\""))

class AutoTimerAddOrEditAutoTimerResource(AutoTimerBaseResource):
	# TODO: recheck if we can modify regular config parser to work on this
	# TODO: allow to edit defaults?
	def render(self, req):
		autotimer = self.getAutoTimerInstance()
		def get(name, default=None):
			ret = req.args.get(name)
			return ret[0] if ret else default

		id = get("id")
		timer = None
		newTimer = True
		if id is None:
			id = autotimer.getUniqueId()
			timer = autotimer.defaultTimer.clone()
			timer.id = id
		else:
			id = int(id)
			for possibleMatch in autotimer.getTimerList():
				if possibleMatch.id == id:
					timer = possibleMatch
					newTimer = False
					break
			if timer is None:
				return self.returnResult(req, False, _("unable to find timer with id %i" % (id,)))

		if id != -1:
			# Match
			timer.match = unquote(get("match", timer.match))
			if not timer.match:
				return self.returnResult(req, False, _("autotimers need a match attribute"))

			# Name
			timer.name = unquote(get("name", timer.name)).strip()
			if not timer.name: timer.name = timer.match

			# Enabled
			enabled = get("enabled")
			if enabled is not None:
				try: enabled = int(enabled)
				except ValueError: enabled = enabled == "yes"
				timer.enabled = enabled

			# Timeframe
			before = get("before")
			after = get("after")
			if before and after:
				timer.timeframe = (int(after), int(before))
			elif before == '' or after == '':
				timer.timeframe = None

		# Encoding
		timer.encoding = get("encoding", timer.encoding)

		# ...
		timer.searchType = get("searchType", timer.searchType)
		timer.searchCase = get("searchCase", timer.searchCase)

		# Alternatives
		timer.overrideAlternatives = int(get("overrideAlternatives", timer.overrideAlternatives))

		# Justplay
		justplay = get("justplay")
		if justplay is not None:
			try: justplay = int(justplay)
			except ValueError: justplay = justplay == "zap"
			timer.justplay = justplay

		# Timespan
		start = get("timespanFrom")
		end = get("timespanTo")
		if start and end:
			start = [int(x) for x in start.split(':')]
			end = [int(x) for x in end.split(':')]
			timer.timespan = (start, end)
		elif start == '' and end == '':
			timer.timespan = None

		# Services
		servicelist = get("services")
		if servicelist is not None:
			servicelist = unquote(servicelist).split(',')
			appendlist = []
			for value in servicelist:
				myref = eServiceReference(str(value))
				if not (myref.flags & eServiceReference.isGroup):
					# strip all after last :
					pos = value.rfind(':')
					if pos != -1:
						if value[pos-1] == ':':
							pos -= 1
						value = value[:pos+1]

				if myref.valid():
					appendlist.append(value)
			timer.services = appendlist

		# Bouquets
		servicelist = get("bouquets")
		if servicelist is not None:
			servicelist = unquote(servicelist).split(',')
			while '' in servicelist: servicelist.remove('')
			timer.bouquets = servicelist

		# Offset
		offset = get("offset")
		if offset:
			offset = offset.split(',')
			if len(offset) == 1:
				before = after = int(offset[0] or 0) * 60
			else:
				before = int(offset[0] or 0) * 60
				after = int(offset[1] or 0) * 60
			timer.offset = (before, after)
		elif offset == '':
			timer.offset = None

		# AfterEvent
		afterevent = get("afterevent")
		if afterevent:
			if afterevent == "default":
				timer.afterevent = []
			else:
				try: afterevent = int(afterevent)
				except ValueError:
					afterevent = {
						"nothing": AFTEREVENT.NONE,
						"deepstandby": AFTEREVENT.DEEPSTANDBY,
						"standby": AFTEREVENT.STANDBY,
						"auto": AFTEREVENT.AUTO
					}.get(afterevent, AFTEREVENT.AUTO)
				# TODO: add afterevent timespan
				timer.afterevent = [(afterevent, None)]

		# Maxduration
		maxduration = get("maxduration")
		if maxduration:
			timer.maxduration = int(maxduration)*60
		elif maxduration == '':
			timer.maxduration = None

		# Includes
		title = req.args.get("title")
		shortdescription = req.args.get("shortdescription")
		description = req.args.get("description")
		dayofweek = req.args.get("dayofweek")
		if title or shortdescription or description or dayofweek:
			includes = timer.include
			title = [unquote(x) for x in title] if title else includes[0]
			shortdescription = [unquote(x) for x in shortdescription] if shortdescription else includes[1]
			description = [unquote(x) for x in description] if description else includes[2]
			dayofweek = [unquote(x) for x in dayofweek] if dayofweek else includes[3]
			while '' in title: title.remove('')
			while '' in shortdescription: shortdescription.remove('')
			while '' in description: description.remove('')
			while '' in dayofweek: dayofweek.remove('')
			timer.include = (title, shortdescription, description, dayofweek)

		# Excludes
		title = req.args.get("!title")
		shortdescription = req.args.get("!shortdescription")
		description = req.args.get("!description")
		dayofweek = req.args.get("!dayofweek")
		if title or shortdescription or description or dayofweek:
			excludes = timer.exclude
			title = [unquote(x) for x in title] if title else excludes[0]
			shortdescription = [unquote(x) for x in shortdescription] if shortdescription else excludes[1]
			description = [unquote(x) for x in description] if description else excludes[2]
			dayofweek = [unquote(x) for x in dayofweek] if dayofweek else excludes[3]
			while '' in title: title.remove('')
			while '' in shortdescription: shortdescription.remove('')
			while '' in description: description.remove('')
			while '' in dayofweek: dayofweek.remove('')
			timer.exclude = (title, shortdescription, description, dayofweek)

		tags = req.args.get("tag")
		if tags:
			while '' in tags: tags.remove('')
			timer.tags = [unquote(x) for x in tags]

		timer.matchCount = int(get("counter", timer.matchCount))
		timer.matchFormatString = get("counterFormat", timer.matchFormatString)
		if id != -1:
			matchLeft = get("left")
			timer.matchLeft = int(matchLeft) if matchLeft else (timer.matchCount if newTimer else timer.matchLeft)
			timer.matchLimit = get("lastActivation", timer.matchLimit)
			timer.lastBegin = int(get("lastBegin", timer.lastBegin))

		timer.avoidDuplicateDescription = int(get("avoidDuplicateDescription", timer.avoidDuplicateDescription))
		timer.destination = get("location", timer.destination) or None

		if newTimer:
			autotimer.add(timer)
			message = _("AutoTimer was added successfully")
		else:
			message = _("AutoTimer was changed successfully")

		# eventually save config
		if self._remove:
			autotimer.writeXml()

		return self.returnResult(req, True, message)

class AutoTimerChangeSettingsResource(AutoTimerBaseResource):
	def render(self, req):
		for key, value in iteritems(req.args):
			value = value[0]
			if key == "autopoll":
				config.plugins.autotimer.autopoll.value = True if value == "true" else False
			elif key == "interval":
				config.plugins.autotimer.interval.value = int(value)
			elif key == "refresh":
				config.plugins.autotimer.refresh.value = value
			elif key == "try_guessing":
				config.plugins.autotimer.try_guessing.value = True if value == "true" else False
			elif key == "editor":
				config.plugins.autotimer.editor.value = value
			elif key == "disabled_on_conflict":
				config.plugins.autotimer.disabled_on_conflict.value = True if value == "true" else False
			elif key == "addsimilar_on_conflict":
				config.plugins.autotimer.addsimilar_on_conflict.value = True if value == "true" else False
			elif key == "show_in_extensionsmenu":
				config.plugins.autotimer.show_in_extensionsmenu.value = True if value == "true" else False
			elif key == "fastscan":
				config.plugins.autotimer.fastscan.value = True if value == "true" else False
			elif key == "notifconflict":
				config.plugins.autotimer.notifconflict.value = True if value == "true" else False
			elif key == "notifsimilar":
				config.plugins.autotimer.notifsimilar.value = True if value == "true" else False

		if config.plugins.autotimer.autopoll.value:
			if plugin.autopoller is None:
				from AutoPoller import AutoPoller
				plugin.autopoller = AutoPoller()
			if plugin.autotimer is None:
				plugin.autotimer = AutoTimer()
			plugin.autopoller.start(initial = False)
		else:
			if plugin.autopoller is not None:
				plugin.autopoller.stop()
				plugin.autopoller = None
			if plugin.autotimer is not None:
				try: plugin.autotimer.readXml()
				except Exception: pass
				else: plugin.autotimer.writeXml()
				plugin.autotimer = None

		return self.returnResult(req, True, _("config changed."))

class AutoTimerSettingsResource(resource.Resource):
	def render(self, req):
		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'application; xhtml+xml')
		req.setHeader('charset', 'UTF-8')

		try:
			from Plugins.SystemPlugins.vps import Vps
		except ImportError as ie:
			hasVps = False
		else:
			hasVps = True

		return """<?xml version=\"1.0\" encoding=\"UTF-8\" ?>
<e2settings>
	<e2setting>
		<e2settingname>config.plugins.autotimer.autopoll</e2settingname>
		<e2settingvalue>%s</e2settingvalue>
	</e2setting>
	<e2setting>
		<e2settingname>config.plugins.autotimer.interval</e2settingname>
		<e2settingvalue>%d</e2settingvalue>
	</e2setting>
	<e2setting>
		<e2settingname>config.plugins.autotimer.refresh</e2settingname>
		<e2settingvalue>%s</e2settingvalue>
	</e2setting>
	<e2setting>
		<e2settingname>config.plugins.autotimer.try_guessing</e2settingname>
		<e2settingvalue>%s</e2settingvalue>
	</e2setting>
	<e2setting>
		<e2settingname>config.plugins.autotimer.editor</e2settingname>
		<e2settingvalue>%s</e2settingvalue>
	</e2setting>
	<e2setting>
		<e2settingname>config.plugins.autotimer.disabled_on_conflict</e2settingname>
		<e2settingvalue>%s</e2settingvalue>
	</e2setting>
	<e2setting>
		<e2settingname>config.plugins.autotimer.addsimilar_on_conflict</e2settingname>
		<e2settingvalue>%s</e2settingvalue>
	</e2setting>
	<e2setting>
		<e2settingname>config.plugins.autotimer.show_in_extensionsmenu</e2settingname>
		<e2settingvalue>%s</e2settingvalue>
	</e2setting>
	<e2setting>
		<e2settingname>config.plugins.autotimer.fastscan</e2settingname>
		<e2settingvalue>%s</e2settingvalue>
	</e2setting>
	<e2setting>
		<e2settingname>config.plugins.autotimer.notifconflict</e2settingname>
		<e2settingvalue>%s</e2settingvalue>
	</e2setting>
	<e2setting>
		<e2settingname>config.plugins.autotimer.notifsimilar</e2settingname>
		<e2settingvalue>%s</e2settingvalue>
	</e2setting>
	<e2setting>
		<e2settingname>hasVps</e2settingname>
		<e2settingvalue>%s</e2settingvalue>
	</e2setting>
</e2settings>""" % (
				config.plugins.autotimer.autopoll.value,
				config.plugins.autotimer.interval.value,
				config.plugins.autotimer.refresh.value,
				config.plugins.autotimer.try_guessing.value,
				config.plugins.autotimer.editor.value,
				config.plugins.autotimer.addsimilar_on_conflict,
				config.plugins.autotimer.disabled_on_conflict.value,
				config.plugins.autotimer.show_in_extensionsmenu.value,
				config.plugins.autotimer.fastscan.value,
				config.plugins.autotimer.notifconflict.value,
				config.plugins.autotimer.notifsimilar.value,
				hasVps,
			)
