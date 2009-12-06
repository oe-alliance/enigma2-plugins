from enigma import eServiceReference, iServiceInformation, eServiceCenter
from Components.Sources.Source import Source
from Components.config import config
from ServiceReference import ServiceReference
from Tools.Directories import resolveFilename, SCOPE_HDD
from Tools.FuzzyDate import FuzzyTime

from os import stat as os_stat

class Movie(Source):
	LIST = 0
	DEL = 1
	TAGS = 2

	def __init__(self, session, movielist, func=LIST):
		Source.__init__(self)
		self.func = func
		self.session = session
		self.tagfilter = []
		self.root = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + resolveFilename(SCOPE_HDD))
		self.movielist = movielist #MovieList(self.root)
		self.movielist.load(self.root, None)
		self.cmd = ""
		self.res = ( False, "Missing or Wrong Argument" )

	def handleCommand(self, cmd):
		if cmd is not None:
			self.cmd = cmd
			if self.func is self.DEL:
				self.res = self.delMovie(cmd)
			elif self.func is self.LIST:
				if cmd['dirname']:
					self.root = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + cmd['dirname'])
				self.tagfilter = cmd['tag'] and [cmd['tag']] or []

	def delMovie(self, param):
#		print "[WebComponents.delMovie] %s" %param

		if param is None:
			return False, "Missing Parameter: sRef"

		service = ServiceReference(param)
		result = False

		if service is not None:
			#mostly copied from Screens.MovieSelection
			serviceHandler = eServiceCenter.getInstance()
			offline = serviceHandler.offlineOperations(service.ref)
			info = serviceHandler.info(service.ref)
			name = info and info.getName(service.ref) or "this recording"

			if offline is not None:
				if not offline.deleteFromDisk(0):
					result = True

			if result == False:
				return ( result, "Could not delete Movie '%s'" % name )
			else:
				return ( result, "Movie '%s' deleted" % name )

		return ( result, "Illegal Parameter Value: sRef - '%s'" % param )

	def getMovieList(self):
		self.movielist.reload(root=self.root, filter_tags=self.tagfilter)
		list = []

		tag = self.cmd['tag']
		tag = tag and tag.lower()
		for (serviceref, info, begin, unknown) in self.movielist.list:
			rtime = info.getInfo(serviceref, iServiceInformation.sTimeCreate)

			if rtime > 0:
				t = FuzzyTime(rtime)
				begin_string = t[0] + ", " + t[1]
			else:
				begin_string = "undefined"

			if config.plugins.Webinterface.loadmovielength.value:
				len = info.getLength(serviceref)
				if len > 0:
					len = "%d:%02d" % (len / 60, len % 60)
				else:
					len = "?:??"
			else:
				len = "disabled"

			sourceERef = info.getInfoString(serviceref, iServiceInformation.sServiceref)
			sourceRef = ServiceReference(sourceERef)

			event = info.getEvent(serviceref)
			ext = event and event.getExtendedDescription() or ""

			filename = "/" + "/".join(serviceref.toString().split("/")[1:])
			servicename = ServiceReference(serviceref).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')
			
			if not tag or tag in info.getInfoString(serviceref, iServiceInformation.sTags).lower():
				""" add movie only to list, if a given tag is applied to the movie """
				list.append((
					serviceref.toString(),
					servicename,
					info.getInfoString(serviceref, iServiceInformation.sDescription),
					rtime,
					begin_string,
					len,
					sourceRef.getServiceName(),
					info.getInfoString(serviceref, iServiceInformation.sTags),
					ext,
					filename,
					os_stat(filename)[6]
				))
		return list

	def getResult(self):
		if self.func is self.DEL:
			return self.res

		return ( False, "illegal call" )

	result = property(getResult)

	list = property(getMovieList)
	lut = {"ServiceReference": 0
			, "Title": 1
			, "Description": 2
			, "Time": 3
			, "TimeString": 4
			, "Length": 5
			, "ServiceName": 6
			, "Tags": 7
			, "DescriptionExtended": 8
			, "Filename": 9
			, "Filesize": 10
		}
