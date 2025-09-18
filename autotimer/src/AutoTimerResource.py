from __future__ import absolute_import
# -*- coding: UTF-8 -*-
from .AutoTimer import AutoTimer
from .AutoTimerConfiguration import CURRENT_CONFIG_VERSION
from RecordTimer import AFTEREVENT
from twisted.internet import reactor
from twisted.web import http, resource, server
import threading
import six
from six.moves.urllib.parse import unquote
from ServiceReference import ServiceReference
from Tools.XMLTools import stringToXML
from enigma import eServiceReference
from . import _, config, iteritems, plugin
from .plugin import autotimer, AUTOTIMER_VERSION

from .AutoTimerSettings import getAutoTimerSettingsDefinitions

from .AutoTimerEditor import CheckREList

API_VERSION = "1.7"


class AutoTimerBaseResource(resource.Resource):

	def _get(self, req, name, default=None):
		name = six.ensure_binary(name)
		ret = req.args.get(name)
		return six.ensure_str(ret[0]) if ret else default

	def returnResult(self, req, state, statetext, stateid=""):
		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'application/xhtml+xml')
		req.setHeader('charset', 'UTF-8')

		return six.ensure_binary("""<?xml version=\"1.0\" encoding=\"UTF-8\" ?>
<e2simplexmlresult>
	<e2state>%s</e2state>
	<e2statetext>%s</e2statetext>
	<e2id>%s</e2id>
</e2simplexmlresult>\n""" % ('True' if state else 'False', statetext, stateid))


class AutoTimerDoParseResource(AutoTimerBaseResource):
	def parsecallback(self, ret):
		rets = self.renderBackground(self.req, ret)
		self.req.write(six.ensure_binary(rets))
		self.req.finish()

	def render(self, req):
		self.req = req
		# todo timeout / error handling
		id = self._get(req, "id")
		if id:
			id = int(id)
		autotimer.parseEPG(callback=self.parsecallback, uniqueId=id)
		return server.NOT_DONE_YET

	def renderBackground(self, req, ret):
		output = _("Found a total of %d matching Events.\n%d Timer were added and\n%d modified,\n%d conflicts encountered,\n%d unchanged,\n%d similars added.") % (ret[0], ret[1], ret[2], len(ret[4]), len(ret[6]), len(ret[5]))
		return self.returnResult(req, True, output)


class AutoTimerSimulateResource(AutoTimerBaseResource):
	def parsecallback(self, timers, skipped):
		rets = self.renderBackground(self.req, timers, skipped)
		self.req.write(six.ensure_binary(rets))
		self.req.finish()

	def render(self, req):
		self.req = req
		# todo timeout / error handling
		id = self._get(req, "id")
		if id:
			id = int(id)
		autotimer.parseEPG(simulateOnly=True, uniqueId=id, callback=self.parsecallback)
		return server.NOT_DONE_YET

	def renderBackground(self, req, timers, skipped):

		returnlist = ["<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n<e2autotimersimulate api_version=\"", str(API_VERSION), "\">\n"]
		extend = returnlist.extend

		for (name, begin, end, serviceref, autotimername) in timers:
			ref = ServiceReference(str(serviceref))
			extend((
				'<e2simulatedtimer>\n'
				'   <e2servicereference>', stringToXML(serviceref), '</e2servicereference>\n',
				'   <e2servicename>', stringToXML(ref.getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')), '</e2servicename>\n',
				'   <e2name>', stringToXML(name), '</e2name>\n',
				'   <e2timebegin>', str(begin), '</e2timebegin>\n',
				'   <e2timeend>', str(end), '</e2timeend>\n',
				'   <e2autotimername>', stringToXML(autotimername), '</e2autotimername>\n'
				'</e2simulatedtimer>\n'
			))

		if skipped:
			for (name, begin, end, serviceref, autotimername, message) in skipped:
				ref = ServiceReference(str(serviceref))
				extend((
					'<e2simulatedtimer>\n'
					'   <e2servicereference>', stringToXML(serviceref), '</e2servicereference>\n',
					'   <e2servicename>', stringToXML(ref.getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')), '</e2servicename>\n',
					'   <e2name>', stringToXML(name), '</e2name>\n',
					'   <e2timebegin>', str(begin), '</e2timebegin>\n',
					'   <e2timeend>', str(end), '</e2timeend>\n',
					'   <e2autotimername>', stringToXML(autotimername), '</e2autotimername>\n',
					'   <e2state>Skip</e2state>\n'
					'   <e2message>', stringToXML(message), '</e2message>\n'
					'</e2simulatedtimer>\n'
				))

		returnlist.append('</e2autotimersimulate>')

		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'application/xhtml+xml')
		req.setHeader('charset', 'UTF-8')
		return ''.join(returnlist)


class AutoTimerTestResource(AutoTimerBaseResource):
	def parsecallback(self, timers, skipped):
		rets = self.renderBackground(self.req, timers, skipped)
		self.req.write(six.ensure_binary(rets))
		self.req.finish()

	def render(self, req):

		self.req = req
		# todo timeout / error handling
		id = self._get(req, "id")
		if id:
			id = int(id)

		autotimer.parseEPG(simulateOnly=True, uniqueId=id, callback=self.parsecallback)

		return server.NOT_DONE_YET

	def renderBackground(self, req, timers, skipped):

		returnlist = ["<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n<e2autotimersimulate api_version=\"", str(API_VERSION), "\">\n"]
		extend = returnlist.extend

		for (name, begin, end, serviceref, autotimername) in timers:
			ref = ServiceReference(str(serviceref))
			extend((
				'<e2simulatedtimer>\n'
				'   <e2servicereference>', stringToXML(serviceref), '</e2servicereference>\n',
				'   <e2servicename>', stringToXML(ref.getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')), '</e2servicename>\n',
				'   <e2name>', stringToXML(name), '</e2name>\n',
				'   <e2timebegin>', str(begin), '</e2timebegin>\n',
				'   <e2timeend>', str(end), '</e2timeend>\n',
				'   <e2autotimername>', stringToXML(autotimername), '</e2autotimername>\n',
				'   <e2state>OK</e2state>\n'
				'</e2simulatedtimer>\n'
			))

		if skipped:
			for (name, begin, end, serviceref, autotimername, message) in skipped:
				ref = ServiceReference(str(serviceref))
				extend((
					'<e2simulatedtimer>\n'
					'   <e2servicereference>', stringToXML(serviceref), '</e2servicereference>\n',
					'   <e2servicename>', stringToXML(ref.getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')), '</e2servicename>\n',
					'   <e2name>', stringToXML(name), '</e2name>\n',
					'   <e2timebegin>', str(begin), '</e2timebegin>\n',
					'   <e2timeend>', str(end), '</e2timeend>\n',
					'   <e2autotimername>', stringToXML(autotimername), '</e2autotimername>\n',
					'   <e2state>Skip</e2state>\n'
					'   <e2message>', stringToXML(message), '</e2message>\n'
					'</e2simulatedtimer>\n'
				))

		returnlist.append('</e2autotimersimulate>')

		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'application/xhtml+xml')
		req.setHeader('charset', 'UTF-8')
		return ''.join(returnlist)


class AutoTimerListAutoTimerResource(AutoTimerBaseResource):
	def render(self, req):
		# We re-read the config so we won't display empty or wrong information
		try:
			autotimer.readXml()
		except Exception as e:
			return self.returnResult(req, False, _("Couldn't load config file!") + '\n' + str(e))
		webif = True
		p = req.args.get(b'webif')
		if p:
			webif = not (p[0] == b"false")
		# show xml
		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'application/xhtml+xml')
		req.setHeader('charset', 'UTF-8')
		return six.ensure_binary(''.join(autotimer.getXml(webif)))


class AutoTimerRemoveAutoTimerResource(AutoTimerBaseResource):
	def render(self, req):
		id = req.args.get(b"id")
		if id:
			autotimer.remove(int(id[0]))
			if config.plugins.autotimer.always_write_config.value:
				autotimer.writeXml()
			return self.returnResult(req, True, _("AutoTimer was removed"))
		else:
			return self.returnResult(req, False, _("missing parameter \"id\""))


class AutoTimerAddXMLAutoTimerResource(AutoTimerBaseResource):
	def render_POST(self, req):
		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'application/xhtml+xml;')
		req.setHeader('charset', 'UTF-8')
		autotimer.readXmlTimer(six.ensure_str(req.args[b'xml'][0]))
		if config.plugins.autotimer.always_write_config.value:
			autotimer.writeXml()
		return self.returnResult(req, True, _("AutoTimer was added successfully"))


class AutoTimerUploadXMLConfigurationAutoTimerResource(AutoTimerBaseResource):
	def render_POST(self, req):
		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'application/xhtml+xml;')
		req.setHeader('charset', 'UTF-8')
		autotimer.readXml(xml_string=six.ensure_str(req.args[b'xml'][0]))
		if config.plugins.autotimer.always_write_config.value:
			autotimer.writeXml()
		return self.returnResult(req, True, _("AutoTimers were changed successfully."))


class AutoTimerAddOrEditAutoTimerResource(AutoTimerBaseResource):
	# TODO: recheck if we can modify regular config parser to work on this
	# TODO: allow to edit defaults?
	def render(self, req):
		def get(name, default=None):
			name = six.ensure_binary(name)
			ret = req.args.get(name)
			return six.ensure_str(ret[0]) if ret else default

		def getA(name, default=None):
			name = six.ensure_binary(name)
			ret = req.args.get(name)
			return [six.ensure_str(x) for x in ret] if ret else default

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
			if not timer.name:
				timer.name = timer.match

			# Enabled
			enabled = get("enabled")
			if enabled is not None:
				try:
					enabled = int(enabled)
				except ValueError:
					enabled = enabled == "yes"
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
			try:
				justplay = int(justplay)
			except ValueError:
				justplay = justplay == "zap"
			timer.justplay = justplay
		setEndtime = get("setEndtime")
		if setEndtime is not None:
			timer.setEndtime = int(setEndtime)

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
						if value[pos - 1] == ':':
							pos -= 1
							value = value[:pos + 1]

				if myref.valid():
					appendlist.append(value)
			timer.services = appendlist

		# Bouquets
		servicelist = get("bouquets")
		if servicelist is not None:
			servicelist = unquote(servicelist).split(',')
			while '' in servicelist:
				servicelist.remove('')
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
				try:
					afterevent = int(afterevent)
				except ValueError:
					afterevent = {
						"nothing": AFTEREVENT.NONE,
						"deepstandby": AFTEREVENT.DEEPSTANDBY,
						"standby": AFTEREVENT.STANDBY,
						"auto": AFTEREVENT.AUTO
					}.get(afterevent, AFTEREVENT.AUTO)
				start = get("aftereventFrom")
				end = get("aftereventTo")
				if start and end:
					start = [int(x) for x in start.split(':')]
					end = [int(x) for x in end.split(':')]
					timer.afterevent = [(afterevent, (start, end))]
				else:
					timer.afterevent = [(afterevent, None)]

		# Maxduration
		maxduration = get("maxduration")
		if maxduration:
			timer.maxduration = int(maxduration) * 60
		elif maxduration == '':
			timer.maxduration = None

		# Includes
		title = getA("title")
		shortdescription = getA("shortdescription")
		description = getA("description")
		dayofweek = getA("dayofweek")
		if title or shortdescription or description or dayofweek:
			includes = timer.include
			title = [unquote(x) for x in title] if title else includes[0]
			shortdescription = [unquote(x) for x in shortdescription] if shortdescription else includes[1]
			description = [unquote(x) for x in description] if description else includes[2]
			dayofweek = [unquote(x) for x in dayofweek] if dayofweek else includes[3]
			while '' in title:
				title.remove('')
			while '' in shortdescription:
				shortdescription.remove('')
			while '' in description:
				description.remove('')
			while '' in dayofweek:
				dayofweek.remove('')
# These must be valid regexes
			errm = CheckREList(title + shortdescription + description)
			if errm != "":
				return self.returnResult(req, False, errm)
			timer.include = (title, shortdescription, description, dayofweek)

		# Excludes
		title = getA("!title")
		shortdescription = getA("!shortdescription")
		description = getA("!description")
		dayofweek = getA("!dayofweek")
		if title or shortdescription or description or dayofweek:
			excludes = timer.exclude
			title = [unquote(x) for x in title] if title else excludes[0]
			shortdescription = [unquote(x) for x in shortdescription] if shortdescription else excludes[1]
			description = [unquote(x) for x in description] if description else excludes[2]
			dayofweek = [unquote(x) for x in dayofweek] if dayofweek else excludes[3]
			while '' in title:
				title.remove('')
			while '' in shortdescription:
				shortdescription.remove('')
			while '' in description:
				description.remove('')
			while '' in dayofweek:
				dayofweek.remove('')
# These must be valid regexes
			errm = CheckREList(title + shortdescription + description)
			if errm != "":
				return self.returnResult(req, False, errm)
			timer.exclude = (title, shortdescription, description, dayofweek)

		tags = getA("tag")
		if tags:
			while '' in tags:
				tags.remove('')
			timer.tags = [unquote(x) for x in tags]

		timer.matchCount = int(get("counter", timer.matchCount))
		timer.matchFormatString = get("counterFormat", timer.matchFormatString)
		if id != -1:
			matchLeft = get("left")
			timer.matchLeft = int(matchLeft) if matchLeft else (timer.matchCount if newTimer else timer.matchLeft)
			timer.matchLimit = get("lastActivation", timer.matchLimit)
			timer.lastBegin = int(get("lastBegin", timer.lastBegin))

		timer.avoidDuplicateDescription = int(get("avoidDuplicateDescription", timer.avoidDuplicateDescription))
		timer.searchForDuplicateDescription = int(get("searchForDuplicateDescription", timer.searchForDuplicateDescription))
		timer.destination = get("location", timer.destination) or None

		# vps
		enabled = get("vps_enabled")
		if enabled is not None:
			try:
				enabled = int(enabled)
			except ValueError:
				enabled = enabled == "yes"
			timer.vps_enabled = enabled
		vps_overwrite = get("vps_overwrite")
		if vps_overwrite is not None:
			try:
				vps_overwrite = int(vps_overwrite)
			except ValueError:
				vps_overwrite = vps_overwrite == "yes"
			timer.vps_overwrite = vps_overwrite
		if not timer.vps_enabled and timer.vps_overwrite:
			timer.vps_overwrite = False

		# SeriesPlugin
		series_labeling = get("series_labeling")
		if series_labeling is not None:
			try:
				series_labeling = int(series_labeling)
			except ValueError:
				series_labeling = series_labeling == "yes"
			timer.series_labeling = series_labeling

		# Always zap
		if hasattr(timer, 'always_zap'):
			timer.always_zap = int(get("always_zap", "0"))
			if timer.always_zap:
				timer.justplay = False  # force justplay to false

		if newTimer:
			autotimer.add(timer)
			message = _("AutoTimer was added successfully")
		else:
			message = _("AutoTimer was changed successfully")

		if config.plugins.autotimer.always_write_config.value:
			autotimer.writeXml()

		resultid = str(timer.id)

		return self.returnResult(req, True, message, resultid)


class AutoTimerChangeResource(AutoTimerBaseResource):
	def render(self, req):
		def get(name, default=None):
			name = six.ensure_binary(name)
			ret = req.args.get(name)
			return six.ensure_str(ret[0]) if ret else default

		id = get("id")
		timer = None
		if id is not None:
			id = int(id)
			for possibleMatch in autotimer.getTimerList():
				if possibleMatch.id == id:
					timer = possibleMatch
					break

		if timer is None:
			return self.returnResult(req, False, _("unable to find timer with id %i" % (id,)))

		# Name
		name = get("name")
		if name is not None:
			timer.name = unquote(name).strip()

		# Enabled
		enabled = get("enabled")
		if enabled is not None:
			try:
				enabled = int(enabled)
			except ValueError:
				enabled = enabled == "yes"
			timer.enabled = enabled

		message = _("AutoTimer was changed successfully")

		if config.plugins.autotimer.always_write_config.value:
			autotimer.writeXml()

		return self.returnResult(req, True, message)


class AutoTimerChangeSettingsResource(AutoTimerBaseResource):
	def render(self, req):
		for key, value in six.iteritems(req.args):
			key = six.ensure_str(key)
			if value:
				value = value[0]
				value = six.ensure_str(value)
			if key == "autopoll":
				config.plugins.autotimer.autopoll.value = True if value == "true" else False
			elif key == "unit":
				config.plugins.autotimer.unit.value = value == "hour" and "hour" or "minute"
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
			elif key == "show_in_plugins":
				config.plugins.autotimer.show_in_plugins.value = True if value == "true" else False
			elif key == "show_in_extensionsmenu":
				config.plugins.autotimer.show_in_extensionsmenu.value = True if value == "true" else False
			elif key == "fastscan":
				config.plugins.autotimer.fastscan.value = True if value == "true" else False
			elif key == "notifconflict":
				config.plugins.autotimer.notifconflict.value = True if value == "true" else False
			elif key == "notifsimilar":
				config.plugins.autotimer.notifsimilar.value = True if value == "true" else False
			elif key == "maxdaysinfuture":
				config.plugins.autotimer.maxdaysinfuture.value = int(value)
			elif key == "add_autotimer_to_tags":
				config.plugins.autotimer.add_autotimer_to_tags.value = True if value == "true" else False
			elif key == "add_name_to_tags":
				config.plugins.autotimer.add_name_to_tags.value = True if value == "true" else False
			elif key == "timeout":
				config.plugins.autotimer.timeout.value = int(value)
			elif key == "popup_timeout":
				config.plugins.autotimer.popup_timeout.value = int(value)
			elif key == "delay":
				config.plugins.autotimer.delay.value = int(value)
			elif key == "editdelay":
				config.plugins.autotimer.editdelay.value = int(value)
			elif key == "skip_during_records":
				config.plugins.autotimer.skip_during_records.value = True if value == "true" else False
			elif key == "skip_during_epgrefresh":
				config.plugins.autotimer.skip_during_epgrefresh.value = True if value == "true" else False
			elif key == "check_eit_and_remove":
				config.plugins.autotimer.check_eit_and_remove.value = True if value == "true" else False
			elif key == "always_write_config":
				config.plugins.autotimer.always_write_config.value,
			elif key == "onlyinstandby":
				config.plugins.autotimer.onlyinstandby.value = True if value == "true" else False

		if config.plugins.autotimer.autopoll.value:
			if plugin.autopoller is None:
				from .AutoPoller import AutoPoller
				plugin.autopoller = AutoPoller()
			plugin.autopoller.start()
		else:
			if plugin.autopoller is not None:
				plugin.autopoller.stop()
				plugin.autopoller = None

		return self.returnResult(req, True, _("config changed."))


class AutoTimerSettingsResource(resource.Resource):
	def render(self, req):
		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'application/xhtml+xml')
		req.setHeader('charset', 'UTF-8')

		try:
			from Plugins.SystemPlugins.vps import Vps
		except ImportError as ie:
			hasVps = False
		else:
			hasVps = True

		try:
			from Plugins.Extensions.SeriesPlugin.plugin import Plugins
		except ImportError as ie:
			hasSeriesPlugin = False
		else:
			hasSeriesPlugin = True

		defs = getAutoTimerSettingsDefinitions()

		resultstr = """<?xml version=\"1.0\" encoding=\"UTF-8\" ?><e2settings>"""

		for (title, cfg, key, description) in defs:
			resultstr += """<e2setting>
				<e2settingname>config.plugins.autotimer.%s</e2settingname>
				<e2settingvalue>%s</e2settingvalue>
				<e2settingtitle>%s</e2settingtitle>
				<e2settingdescription>%s</e2settingdescription>
			</e2setting>""" % (key, cfg.value, title, description)

		resultstr += """<e2setting>
				<e2settingname>hasVps</e2settingname>
				<e2settingvalue>%s</e2settingvalue>
				</e2setting>
				<e2setting>
					<e2settingname>hasSeriesPlugin</e2settingname>
					<e2settingvalue>%s</e2settingvalue>
				</e2setting>
				<e2setting>
					<e2settingname>version</e2settingname>
					<e2settingvalue>%s</e2settingvalue>
				</e2setting>
				<e2setting>
					<e2settingname>api_version</e2settingname>
					<e2settingvalue>%s</e2settingvalue>
				</e2setting>
				<e2setting>
					<e2settingname>autotimer_version</e2settingname>
					<e2settingvalue>%s</e2settingvalue>
				</e2setting>
			</e2settings>""" % (hasVps, hasSeriesPlugin, CURRENT_CONFIG_VERSION, API_VERSION, AUTOTIMER_VERSION)

		return six.ensure_binary(resultstr)
