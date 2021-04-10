from Plugins.Extensions.WebInterface.WebScreens import WebScreen


class VpsWebScreen(WebScreen):
	def __init__(self, session, request):
		WebScreen.__init__(self, session, request)
		from .WebComponents.Sources.Vps import Vps

		self["TimerList"] = Vps(session, func=Vps.LIST)
		self["TimerAddEventID"] = Vps(session, func=Vps.ADDBYID)
		self["TimerAdd"] = Vps(session, func=Vps.ADD)
		self["TimerChange"] = Vps(session, func=Vps.CHANGE)
