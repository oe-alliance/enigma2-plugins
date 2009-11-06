from twisted.web import http, resource
from AutoTimer import AutoTimer
from . import _

class AutoTimerBaseResource(resource.Resource):
	def getAutoTimerInstance(self):
		from plugin import autotimer
		if autotimer is None:
			self._remove = True
			return AutoTimer()
		self._remove = False
		return autotimer

class AutoTimerDoParseResource(AutoTimerBaseResource):
	def render(self, req):
		autotimer = self.getAutoTimerInstance()
		ret = autotimer.parseEPG()
		output = _("Found a total of %d matching Events.\n%d Timer were added and %d modified.") % (ret[0], ret[1], ret[2])

		if self._remove:
			autotimer.writeXml()

		result = """<?xml version=\"1.0\" encoding=\"UTF-8\" ?>
			<e2simplexmlresult>
				<e2state>true</e2state>
				<e2statetext>%s</e2statetext>
			</e2simplexmlresult>
			""" % (output)
	
		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'application; xhtml+xml')
		req.setHeader('charset', 'UTF-8')
		
		return result

class AutoTimerListAutoTimerResource(AutoTimerBaseResource):
	def render(self, req):
		autotimer = self.getAutoTimerInstance()

		# show xml
		req.setResponseCode(http.OK)
		req.setHeader('Content-type', 'application; xhtml+xml')
		req.setHeader('charset', 'UTF-8')
		return ''.join(autotimer.getXml())

