from Components.Sources.Source import Source
from Components.config import config
from enigma import eServiceReference

class SwitchService(Source):
	def __init__(self, session):
		Source.__init__(self)
		self.session = session
		self.res = ( False, "Parameter sRef is missing" )
	
	def handleCommand(self, cmd):		
		self.res = self.switchService(cmd)
		
	def switchService(self, cmd):
		print "[SwitchService] ref=%s" %cmd["sRef"]
		
		pc = config.ParentalControl.configured.value

		"""
		#HACK
		switching config.ParentalControl.configured.value
		"""		
		if pc:
			config.ParentalControl.configured.value = False
		if config.plugins.Webinterface.allowzapping.value:
			eref= eServiceReference(cmd["sRef"])
			if cmd["title"] is not None:
				eref.setName(cmd["title"])
			self.session.nav.playService(eref)	
			if pc:
				config.ParentalControl.configured.value = pc
			
			return ( True, "Active service switched to %s" %cmd["sRef"] )
		
		else:
			return ( False, "Zapping is disabled in WebInterface Configuration" )
	
	result = property(lambda self: self.res)
	