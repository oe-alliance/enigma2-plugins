from twisted.web import http, resource
from EPGRefresh import epgrefresh
from EPGRefreshService import EPGRefreshService
from enigma import eServiceReference
from Components.config import config
from Components.SystemInfo import SystemInfo
from time import localtime
from OrderedSet import OrderedSet
from ServiceReference import ServiceReference
from Tools.XMLTools import stringToXML
try:
	from urllib import unquote
	iteritems = lambda d: d.iteritems()
except ImportError as ie:
	from urllib.parse import unquote
	iteritems = lambda d: d.items()

API_VERSION = "1.2"

class EPGRefreshStartRefreshResource(resource.Resource):
	def render(self, req):
		state = False

		if epgrefresh.forceRefresh():
			output = "initiated refresh"
			state = True
		else:
			output = "could not initiate refresh"

		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'application/xhtml+xml')
		req.setHeader('charset', 'UTF-8')

		return """<?xml version=\"1.0\" encoding=\"UTF-8\" ?>
<e2simplexmlresult>
 <e2state>%s</e2state>
 <e2statetext>%s</e2statetext>
</e2simplexmlresult>""" % ('true' if state else 'false', output)

class EPGRefreshAddRemoveServiceResource(resource.Resource):
	TYPE_ADD = 0
	TYPE_DEL = 1

	def __init__(self, type):
		assert(type in (self.TYPE_ADD, self.TYPE_DEL))
		self.type = type

	def render(self, req):
		do_add = self.type == self.TYPE_ADD
		state = False

		if 'multi' in req.args:
			if epgrefresh.services[0]:
				epgrefresh.services[0].clear()
				state = True
			if epgrefresh.services[1]:
				epgrefresh.services[1].clear()
				state = True

		if 'sref' in req.args:
			duration = req.args.get("duration", None)
			try:
				duration = duration and int(duration)
			except ValueError as ve:
				output = 'invalid value for "duration": ' + str(duration)
			else:
				for sref in req.args.get('sref'):
					sref = unquote(sref)
					ref = eServiceReference(sref)
					if not ref.valid():
						output = 'invalid value for "sref": ' + str(sref)
					elif (ref.flags & 7) == 7:
						epgservice = EPGRefreshService(sref, duration)
						# bouquet
						if epgservice in epgrefresh.services[1]:
							if do_add:
								output = "bouquet already in list"
							else:
								epgrefresh.services[1].remove(epgservice)
								output = "bouquet removed from list"
								state = True
						else:
							if do_add:
								epgrefresh.services[1].add(epgservice)
								output = "bouquet added to list"
								state = True
							else:
								output = "bouquet not in list"
					else:
						if not (ref.flags & eServiceReference.isGroup):
							# strip all after last :
							pos = sref.rfind(':')
							if pos != -1:
								if sref[pos-1] == ':':
									pos -= 1
								sref = sref[:pos+1]

						epgservice = EPGRefreshService(sref, duration)
						# assume service
						if epgservice in epgrefresh.services[0]:
							if do_add:
								output = "service already in list"
							else:
								epgrefresh.services[0].remove(epgservice)
								output = "service removed from list"
								state = True
						else:
							if do_add:
								epgrefresh.services[0].add(epgservice)
								output = "service added to list"
								state = True
							else:
								output = "service not in list"

				# save if list changed
				if state:
					epgrefresh.saveConfiguration()
		else:
			output = 'missing argument "sref"'

		if 'multi' in req.args:
			output = 'service restriction changed'

		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'application/xhtml+xml')
		req.setHeader('charset', 'UTF-8')
		
		return """<?xml version=\"1.0\" encoding=\"UTF-8\" ?>
<e2simplexmlresult>
 <e2state>%s</e2state>
 <e2statetext>%s</e2statetext>
</e2simplexmlresult> """ % ('True' if state else 'False', output)

class EPGRefreshListServicesResource(resource.Resource):
	def render(self, req):
		# show xml
		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'application/xhtml+xml')
		req.setHeader('charset', 'UTF-8')
		return ''.join(epgrefresh.buildConfiguration(webif = True))

class EPGRefreshPreviewServicesResource(resource.Resource):
	def render(self, req):
		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'application/xhtml+xml')
		req.setHeader('charset', 'UTF-8')

		if 'sref' in req.args:
			services = OrderedSet()
			bouquets = OrderedSet()
			for sref in req.args.get('sref'):
				sref = unquote(sref)
				ref = eServiceReference(sref)
				if not ref.valid():
					services = bouquets = None
					break
				elif (ref.flags & 7) == 7:
					epgservice = EPGRefreshService(sref, None)
					if epgservice not in bouquets:
						bouquets.add(epgservice)
				else:
					if not (ref.flags & eServiceReference.isGroup):
						# strip all after last :
						pos = sref.rfind(':')
						if pos != -1:
							if sref[pos-1] == ':':
								pos -= 1
							sref = sref[:pos+1]

					epgservice = EPGRefreshService(sref, None)
					if epgservice not in services:
						services.add(epgservice)
			if services is not None and bouquets is not None:
				scanServices = epgrefresh.generateServicelist(services, bouquets)
			else:
				scanServices = []
		else:
			scanServices = epgrefresh.generateServicelist(epgrefresh.services[0], epgrefresh.services[1])

		returnlist = ["<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n<e2servicelist>"]
		extend = returnlist.extend
		for serviceref in scanServices:
			ref = ServiceReference(str(serviceref))
			returnlist.extend((
				' <e2service>\n',
				'  <e2servicereference>', stringToXML(str(serviceref)), '</e2servicereference>\n',
				'  <e2servicename>', stringToXML(ref.getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')), '</e2servicename>\n',
				' </e2service>\n',
			))
		returnlist.append('\n</e2servicelist>')
		return ''.join(returnlist)

class EPGRefreshChangeSettingsResource(resource.Resource):
	def render(self, req):
		statetext = "config changed."
		for key, value in iteritems(req.args):
			value = value[0]
			if key == "enabled":
				config.plugins.epgrefresh.enabled.value = True if value == "true" else False
			elif key == "enablemessage":
				config.plugins.epgrefresh.enablemessage.value = True if value == "true" else False
			elif key == "begin":
				value = int(value)
				if value:
					t = localtime(value)
					config.plugins.epgrefresh.begin.value = [t.tm_hour, t.tm_min]
			elif key == "end":
				value = int(value)
				if value:
					t = localtime(int(value))
					config.plugins.epgrefresh.end.value = [t.tm_hour, t.tm_min]
			elif key == "interval_seconds":
				value = int(value)
				if value:
					config.plugins.epgrefresh.interval_seconds.value = value
			elif key == "delay_standby":
				value = int(value)
				if value:
					config.plugins.epgrefresh.delay_standby.value = value
			elif key == "inherit_autotimer":
				config.plugins.epgrefresh.inherit_autotimer.value = True if value == "true" else False
			elif key == "afterevent":
				config.plugins.epgrefresh.afterevent.value = True if value == "true" else False
			elif key == "force":
				config.plugins.epgrefresh.force.value = True if value == "true" else False
			elif key == "wakeup":
				config.plugins.epgrefresh.wakeup.value = True if value == "true" else False
			elif key == "parse_autotimer":
				config.plugins.epgrefresh.parse_autotimer.value = True if value == "true" else False
			elif key == "adapter":
				if value in config.plugins.epgrefresh.adapter.choices:
					config.plugins.epgrefresh.adapter.value = value

		config.plugins.epgrefresh.save()

		if config.plugins.epgrefresh.enabled.value:
			epgrefresh.start()
		else:
			epgrefresh.stop()

		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'application/xhtml+xml')
		req.setHeader('charset', 'UTF-8')

		return """<?xml version=\"1.0\" encoding=\"UTF-8\" ?>
<e2simplexmlresult>
 <e2state>true</e2state>
 <e2statetext>%s</e2statetext>
</e2simplexmlresult>""" % (statetext,)

class EPGRefreshSettingsResource(resource.Resource):
	def render(self, req):
		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'application/xhtml+xml')
		req.setHeader('charset', 'UTF-8')

		from time import time, localtime, mktime
		now = localtime()
		begin_h = config.plugins.epgrefresh.begin.value
		begin = mktime((
			now.tm_year, now.tm_mon, now.tm_mday, begin_h[0], begin_h[1],
			0, now.tm_wday, now.tm_yday, now.tm_isdst)
		)
		end_h = config.plugins.epgrefresh.end.value
		end = mktime((
			now.tm_year, now.tm_mon, now.tm_mday, end_h[0], end_h[1],
			0, now.tm_wday, now.tm_yday, now.tm_isdst)
		)

		canDoBackgroundRefresh = SystemInfo.get("NumVideoDecoders", 1) > 1
		hasAutoTimer = False
		try:
			from Plugins.Extensions.AutoTimer.AutoTimer import AutoTimer
			hasAutoTimer = True
		except ImportError as ie: pass

		return """<?xml version=\"1.0\" encoding=\"UTF-8\" ?>
<e2settings>
 <e2setting>
  <e2settingname>config.plugins.epgrefresh.enabled</e2settingname>
  <e2settingvalue>%s</e2settingvalue>
 </e2setting>
 <e2setting>
  <e2settingname>config.plugins.epgrefresh.enablemessage</e2settingname>
  <e2settingvalue>%s</e2settingvalue>
 </e2setting>
 <e2setting>
  <e2settingname>config.plugins.epgrefresh.begin</e2settingname>
  <e2settingvalue>%d</e2settingvalue>
 </e2setting>
 <e2setting>
  <e2settingname>config.plugins.epgrefresh.end</e2settingname>
  <e2settingvalue>%d</e2settingvalue>
 </e2setting>
 <e2setting>
  <e2settingname>config.plugins.epgrefresh.interval_seconds</e2settingname>
  <e2settingvalue>%d</e2settingvalue>
 </e2setting>
 <e2setting>
  <e2settingname>config.plugins.epgrefresh.delay_standby</e2settingname>
  <e2settingvalue>%d</e2settingvalue>
 </e2setting>
 <e2setting>
  <e2settingname>config.plugins.epgrefresh.inherit_autotimer</e2settingname>
  <e2settingvalue>%s</e2settingvalue>
 </e2setting>
 <e2setting>
  <e2settingname>config.plugins.epgrefresh.afterevent</e2settingname>
  <e2settingvalue>%s</e2settingvalue>
 </e2setting>
 <e2setting>
  <e2settingname>config.plugins.epgrefresh.force</e2settingname>
  <e2settingvalue>%s</e2settingvalue>
 </e2setting>
 <e2setting>
  <e2settingname>config.plugins.epgrefresh.wakeup</e2settingname>
  <e2settingvalue>%s</e2settingvalue>
 </e2setting>
 <e2setting>
  <e2settingname>config.plugins.epgrefresh.parse_autotimer</e2settingname>
  <e2settingvalue>%s</e2settingvalue>
 </e2setting>
 <e2setting>
  <e2settingname>config.plugins.epgrefresh.lastscan</e2settingname>
  <e2settingvalue>%d</e2settingvalue>
 </e2setting>
 <e2setting>
  <e2settingname>config.plugins.epgrefresh.adapter</e2settingname>
  <e2settingvalue>%s</e2settingvalue>
 </e2setting>
 <e2setting>
  <e2settingname>canDoBackgroundRefresh</e2settingname>
  <e2settingvalue>%s</e2settingvalue>
 </e2setting>
 <e2setting>
  <e2settingname>hasAutoTimer</e2settingname>
  <e2settingvalue>%s</e2settingvalue>
 </e2setting>
 <e2setting>
  <e2settingname>api_version</e2settingname>
  <e2settingvalue>%s</e2settingvalue>
 </e2setting>
</e2settings>""" % (
				config.plugins.epgrefresh.enabled.value,
				config.plugins.epgrefresh.enablemessage.value,
				begin,
				end,
				config.plugins.epgrefresh.interval_seconds.value,
				config.plugins.epgrefresh.delay_standby.value,
				config.plugins.epgrefresh.inherit_autotimer.value,
				config.plugins.epgrefresh.afterevent.value,
				config.plugins.epgrefresh.force.value,
				config.plugins.epgrefresh.wakeup.value,
				config.plugins.epgrefresh.parse_autotimer.value,
				config.plugins.epgrefresh.lastscan.value,
				config.plugins.epgrefresh.adapter.value,
				canDoBackgroundRefresh,
				hasAutoTimer,
				API_VERSION,
			)

