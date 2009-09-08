from twisted.web import http, resource
from EPGRefresh import epgrefresh
from EPGRefreshService import EPGRefreshService
from enigma import eServiceReference
from Components.config import config

class EPGRefreshStartRefreshResource(resource.Resource):
	def render(self, req):
		state = False

		if epgrefresh.forceRefresh():
			output = "initiated refresh"
			state = True
		else:
			output = "could not initiate refresh"

		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'application; xhtml+xml')
		req.setHeader('charset', 'UTF-8')

		return """<?xml version=\"1.0\" encoding=\"UTF-8\" ?>
			<e2simplexmlresult>
				<e2state>%s</e2state>
				<e2statetext>%s</e2statetext>
			</e2simplexmlresult>
			""" % ('true' if state else 'false', output)

class EPGRefreshAddRemoveServiceResource(resource.Resource):
	TYPE_ADD = 0
	TYPE_DEL = 1

	def __init__(self, type):
		assert(type in (self.TYPE_ADD, self.TYPE_DEL))
		self.type = type

	def render(self, req):
		do_add = self.type == self.TYPE_ADD
		state = False

		if 'sref' in req.args:
			sref = req.args["sref"][0]
			if do_add:
				# strip all after last : (custom name)
				pos = sref.rfind(':')
				if pos != -1:
					sref = sref[:pos+1]

			duration = req.args.get("duration", None)
			try:
				duration = duration and int(duration)
			except ValueError, ve:
				output = 'invalid value for "duration": ' + str(duration)
			else:
				epgservice = EPGRefreshService(sref, duration)

				if sref:
					ref = eServiceReference(str(sref))
					if not ref.valid():
						output = 'invalid value for "sref": ' + str(sref)
					elif (ref.flags & 7) == 7:
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
					output = 'invalid value for "sref": ' + str(sref)
		else:
			output = 'missing argument "sref"'

		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'application; xhtml+xml')
		req.setHeader('charset', 'UTF-8')
		
		return """<?xml version=\"1.0\" encoding=\"UTF-8\" ?>
			<e2simplexmlresult>
				<e2state>%s</e2state>
				<e2statetext>%s</e2statetext>
			</e2simplexmlresult>
			""" % ('true' if state else 'false', output)

class EPGRefreshListServicesResource(resource.Resource):
	def render(self, req):
		# show xml
		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'application; xhtml+xml')
		req.setHeader('charset', 'UTF-8')
		return ''.join(epgrefresh.buildConfiguration(webif = True))

class EPGRefreshChangeSettingsResource(resource.Resource):
	def render(self, req):
		for key, value in req.args.iteritems():
			value = value[0]
			if key == "enabled":
				config.plugins.epgrefresh.enabled.value = True if value == "true" else False
			elif key == "begin":
				config.plugins.epgrefresh.begin.value = int(value)
			elif key == "end":
				config.plugins.epgrefresh.end.value = int(value)
			elif key == "interval":
				config.plugins.epgrefresh.interval.value = int(value)
			elif key == "delay_standby":
				config.plugins.epgrefresh.delay_standby.value = int(value)
			elif key == "inherit_autotimer":
				config.plugins.epgrefresh.inherit_autotimer.value = True if value == "true" else False
			elif key == "afterevent":
				config.plugins.epgrefresh.afterevent.value = True if value == "true" else False
			elif key == "force":
				config.plugins.epgrefresh.force.value = True if value == "true" else False
			elif key == "wakeup":
				config.plugins.epgrefresh.wakeup.value = True if value == "true" else False
			elif key == "pase_autotimer":
				config.plugins.epgrefresh.parse_autotimer.value = True if value == "true" else False

		config.plugins.epgrefresh.save()

		if config.plugins.epgrefresh.enabled.value:
			epgrefresh.start()
		else:
			epgrefresh.stop()

		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'application; xhtml+xml')
		req.setHeader('charset', 'UTF-8')

		return """<?xml version=\"1.0\" encoding=\"UTF-8\" ?>
			<e2simplexmlresult>
				<e2state>true</e2state>
				<e2statetext>config changed.</e2statetext>
			</e2simplexmlresult>
			"""

class EPGRefreshSettingsResource(resource.Resource):
	def render(self, req):
		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'application; xhtml+xml')
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

		return """<?xml version=\"1.0\" encoding=\"UTF-8\" ?>
			<e2settings>
				<e2setting>
					<e2settingname>config.plugins.epgrefresh.enabled</e2settingname>
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
					<e2settingname>config.plugins.epgrefresh.interval</e2settingname>
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
			</e2settings>
			""" % (
				config.plugins.epgrefresh.enabled.value,
				begin,
				end,
				config.plugins.epgrefresh.interval.value,
				config.plugins.epgrefresh.delay_standby.value,
				config.plugins.epgrefresh.inherit_autotimer.value,
				config.plugins.epgrefresh.afterevent.value,
				config.plugins.epgrefresh.force.value,
				config.plugins.epgrefresh.wakeup.value,
				config.plugins.epgrefresh.parse_autotimer.value,
			)

