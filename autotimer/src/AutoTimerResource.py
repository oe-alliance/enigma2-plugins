from twisted.web2 import resource, responsecode, http
from AutoTimer import AutoTimer
from plugin import autotimer
from . import _

# pretty basic resource which is just present to have a way to start a
# forced run through the webif
class AutoTimerResource(resource.Resource):
	def __init__(self):
		resource.Resource.__init__(self)

	def render(self, req):
		remove = False
		if autotimer is None:
			autotimer = AutoTimer()
			remove = True

		if req.args.has_key("parse"):
			ret = autotimer.parseEPG()
			output = _("Found a total of %d matching Events.\n%d Timer were added and %d modified.") % (ret[0], ret[1], ret[2])
		else:
			output = "unknown command"

		if remove:
			autotimer = None
		return http.Response(responsecode.OK ,stream = output)

