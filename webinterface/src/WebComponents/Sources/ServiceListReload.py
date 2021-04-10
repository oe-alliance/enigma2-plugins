from __future__ import print_function
from enigma import eDVBDB
from Components.NimManager import nimmanager
from Components.Sources.Source import Source
import Components.ParentalControl


class ServiceListReload(Source):
	BOTH = 0
	LAMEDB = 1
	USERBOUQUETS = 2
	TRANSPONDERS = 3
	PARENTAL = 4

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
				self.res = (True, _('reloaded both'))
			elif self.cmd is self.LAMEDB:
				self.reloadLameDB()
				self.res = (True, _('reloaded lamedb'))
			elif self.cmd is self.USERBOUQUETS:
				self.reloadUserBouquets()
				self.res = (True, _('reloaded bouquets'))
			elif self.cmd is self.TRANSPONDERS:
				self.reloadTransponders()
				self.res = (True, 'reloaded transponders')
			elif self.cmd is self.PARENTAL:
				Components.ParentalControl.parentalControl.open()
				self.res = (True, 'reloaded parentalcontrol white-/blacklist')
		except Exception as e:
			pass

	def reloadLameDB(self):
		print("[ServiceListReload] reloading lamedb")
		self.eDVBDB.removeServices()
		self.eDVBDB.reloadServicelist()

	def reloadUserBouquets(self):
		print("[ServiceListReload] reloading userbouquets")
		self.eDVBDB.reloadBouquets()

	def reloadTransponders(self):
		print("[ServiceListReload] reloading transponders")
		nimmanager.readTransponders()

	def getResult(self):
		if self.res:
			return self.res
		else:
			return (False, _("missing or wrong parameter mode [%i=both, %i=lamedb only, %i=userbouqets only, %i=transponders, %i=parentalcontrol white-/blacklist]") % (self.BOTH, self.LAMEDB, self.USERBOUQUETS, self.TRANSPONDERS, self.PARENTAL))

	result = property(getResult)
