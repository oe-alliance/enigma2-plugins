from Components.Converter.Converter import Converter
from Components.Element import cached, ElementError
from enigma import iServiceInformation, eServiceReference


class ServiceTime(Converter, object):
	STARTTIME = 0
	ENDTIME = 1
	DURATION = 2

	def __init__(self, type):
#		print("ServiceTimeSF init: (%s, %s)" %(sstr(self), type))
		Converter.__init__(self, type)
		if type == "EndTime":
			self.type = self.ENDTIME
		elif type == "StartTime":
			self.type = self.STARTTIME
		elif type == "Duration":
			self.type = self.DURATION
		else:
			raise ElementError("'%s' is not <StartTime|EndTime|Duration> for ServiceTime converter" % type)

	@cached
	def getTime(self):
#		print("ServiceTimeSF.getTime %x, self=%s" % (id(self.getTime), sstr(self)))
		service = self.source.service
		info = self.source.info

		if not info or not service:
			return None

		if self.type == self.STARTTIME:
			return info.getInfo(service, iServiceInformation.sTimeCreate)
		elif self.type == self.ENDTIME:
			begin = info.getInfo(service, iServiceInformation.sTimeCreate)
			len = info.getLength(service)
			return begin + len
		elif self.type == self.DURATION:
			da = info.getLength(service)
#			print "[SF-Plugin] ServiceTimeSF.getTime srv=%x,%x, getLength = %d -- %s" % (service.type, service.flags, da, sstr(self))
			if da == -1 and service.type == (eServiceReference.idUser | eServiceReference.idDVB):
				return None		# otherwise -1:59
			return info.getLength(service)

	time = property(getTime)
