from Components.Sources.Source import Source
from Components.Converter import ServiceName
from Components.config import config
from enigma import eServiceReference, iPlayableServicePtr

class SwitchService(Source):
	def __init__(self, session):
		Source.__init__(self)
		self.session = session
		self.info = None
		self.res = ( False, "Parameter sRef is missing" )
	
	def handleCommand(self, cmd):		
		self.res = self.switchService(cmd)
		
	def switchService(self, cmd):
		print "[SwitchService] ref=%s" % cmd["sRef"]
		if config.plugins.Webinterface.allowzapping.value:
			from Screens.Standby import inStandby
			if inStandby == None:
				if cmd["sRef"] != None:
					pc = config.ParentalControl.configured.value
					if pc:
						config.ParentalControl.configured.value = False			
					
					eref = eServiceReference(cmd["sRef"])
					
					if cmd["title"] is not None:
						eref.setName(cmd["title"])
					self.session.nav.playService(eref)
						
					if pc:
						config.ParentalControl.configured.value = pc
					
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
					
					return ( True, "Active service is now '%s'" %name )
				else:
					return ( False, "Obligatory Parameter 'sRef' is missing" )
			else:
				return ( False, "Cannot zap while device is in Standby" )			
		else:
			return ( False, "Zapping is disabled in WebInterface Configuration" )
	
	result = property(lambda self: self.res)
	