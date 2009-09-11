from enigma import eDVBDB
from Components.Sources.Source import Source

class ServiceListReload(Source):
	BOTH = 0
	LAMEDB = 1
	USERBOUQUETS = 2

	def __init__(self, session):
		Source.__init__(self)
		self.session = session
		self.eDVBDB = eDVBDB.getInstance()
		self.res = False

	def handleCommand(self, cmd):
		try:
			self.cmd = int(cmd)
			if self.cmd is self.BOTH:
				self.reloadLameDB()
				self.reloadUserBouquets()
				self.res = ( True, 'reloaded both' )
			elif self.cmd is self.LAMEDB:
				self.res = self.reloadLameDB()
				self.res = ( True, 'reloaded lamedb' )
			elif self.cmd is self.USERBOUQUETS:
				self.res = self.reloadUserBouquets()
				self.res = ( True, 'reloaded bouquets' )
		except Exception, e:
			pass

	def reloadLameDB(self):
		print "[ServiceListReload] reloading lamedb"
		self.eDVBDB.reloadServicelist()

	def reloadUserBouquets(self):
		print "[ServiceListReload] reloading userbouquets"
		self.eDVBDB.reloadBouquets()

	def getResult(self):
		if self.res:
			return self.res
		else:
			return ( False, "missing or wrong parameter mode [%i=both, %i=lamedb only, %i=userbouqets only]" % (self.BOTH, self.LAMEDB, self.USERBOUQUETS) )

	result = property(getResult)
