from Components.Sources.Source import Source
from Components.Converter import ServiceName
from Components.config import config
from Screens.InfoBar import InfoBar, MoviePlayer
from enigma import eServiceReference, iPlayableServicePtr

class SwitchService(Source):
	def __init__(self, session):
		Source.__init__(self)
		self.session = session
		self.info = None
		self.res = ( False, _("Obligatory parameter sRef is missing") )

	def handleCommand(self, cmd):
		self.res = self.switchService(cmd)

	def switchService(self, cmd):
		print "[SwitchService] ref=%s" % cmd["sRef"]
		if config.plugins.Webinterface.allowzapping.value:
			from Screens.Standby import inStandby
			if inStandby == None:
				if cmd["sRef"] != None:
					pc = config.ParentalControl.servicepinactive.value
					if pc:
						config.ParentalControl.servicepinactive.value = False

					eref = eServiceReference(cmd["sRef"])

					if cmd["title"] is not None:
						eref.setName(cmd["title"])

					isRec = eref.getPath()
					isRec = isRec and isRec.startswith("/")
					if not isRec:
						# if this is not a recording and the movie player is open, close it
						if isinstance(self.session.current_dialog, MoviePlayer):
							self.session.current_dialog.lastservice = eref
							self.session.current_dialog.close()
						self.session.nav.playService(eref)
					elif isRec:
						# if this is a recording and the infobar is shown, open the movie player
						if isinstance(self.session.current_dialog, InfoBar):
							self.session.open(MoviePlayer, eref)
						# otherwise just play it with no regard for the context
						else:
							self.session.nav.playService(eref)

					if pc:
						config.ParentalControl.servicepinactive.value = pc

					name = cmd["sRef"]
					if cmd["title"] is None:
						service = self.session.nav.getCurrentService()
						info = None
						if isinstance(service, iPlayableServicePtr):
							info = service and service.info()
							ref = None

						if info != None:
							name = ref and info.getName(ref)
							if name is None:
								name = info.getName()
							name.replace('\xc2\x86', '').replace('\xc2\x87', '')
					elif eref.getName() != "":
						name = eref.getName()

					return ( True, _("Active service is now '%s'") %name )
				else:
					return ( False, _("Obligatory parameter 'sRef' is missing") )
			else:
				return ( False, _("Cannot zap while device is in Standby") )
		else:
			return ( False, _("Zapping is disabled in WebInterface Configuration") )

	result = property(lambda self: self.res)
