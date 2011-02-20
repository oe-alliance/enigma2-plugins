from twisted.web import http, resource
from AutoTimer import AutoTimer
from RecordTimer import AFTEREVENT
from urllib import unquote
from . import _

class AutoTimerBaseResource(resource.Resource):
	_remove = False
	def getAutoTimerInstance(self):
		from plugin import autotimer
		if autotimer is None:
			self._remove = True
			return AutoTimer()
		self._remove = False
		return autotimer
	def returnResult(self, req, state, statetext):
		result = """<?xml version=\"1.0\" encoding=\"UTF-8\" ?>
			<e2simplexmlresult>
				<e2state>%s</e2state>
				<e2statetext>%s</e2statetext>
			</e2simplexmlresult>
			""" % ('true' if state else 'false', statetext)

		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'application; xhtml+xml')
		req.setHeader('charset', 'UTF-8')
		return result


class AutoTimerDoParseResource(AutoTimerBaseResource):
	def render(self, req):
		autotimer = self.getAutoTimerInstance()
		ret = autotimer.parseEPG()
		output = _("Found a total of %d matching Events.\n%d Timer were added and %d modified.") % (ret[0], ret[1], ret[2])

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
			timer = autotimer.defaultTimer.clone()
			timer.id = autotimer.getUniqueId()
		else:
			id = int(id)
			for possibleMatch in autotimer.getTimerList():
				if possibleMatch.id == id:
					timer = possibleMatch
					newTimer = False
					break
			if timer is None:
				return self.returnResult(req, False, _("unable to find timer with id %i" % (id,)))

		# Match
		timer.match = unquote(get("match", timer.match))
		if not timer.match:
			return self.returnResult(req, False, _("autotimers need a match attribute"))

		# Name
		timer.name = unquote(get("name", timer.name)).strip()
		if not timer.name: timer.name = timer.match

		# Encoding
		timer.encoding = get("encoding", timer.encoding)

		# ...
		timer.searchType = get("searchType", timer.searchType)
		timer.searchCase = get("searchCase", timer.searchCase)

		# Alternatives
		timer.overrideAlternatives = int(get("overrideAlternatives", timer.overrideAlternatives))

		# Enabled
		enabled = get("enabled")
		if enabled is not None:
			try: enabled = int(enabled)
			except ValueError: enabled = enabled == "yes"
			timer.enabled = enabled

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

				appendlist.append(value)
			timer.services = appendlist

		# Bouquets
		servicelist = get("bouquets")
		if servicelist is not None:
			servicelist = unquote(servicelist).split(',')
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

		# TODO: implement in-/excludes, counter, tags

		timer.avoidDuplicateDescription = int(get("avoidDuplicateDescription", timer.avoidDuplicateDescription))
		timer.destination = get("location", "") or None

		# eventually save config
		if self._remove:
			autotimer.writeXml()

		if newTimer:
			autotimer.add(timer)
			message = _("AutoTimer was added successfully")
		else:
			message = _("AutoTimer was changed successfully")
		return self.returnResult(req, True, message)
