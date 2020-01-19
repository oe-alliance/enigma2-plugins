from enigma import eServiceReference, iServiceInformation, eServiceCenter
from Components.Sources.Source import Source
from Components.config import config
from ServiceReference import ServiceReference
from Tools.Directories import resolveFilename, SCOPE_HDD, pathExists, fileExists
from Tools.FuzzyDate import FuzzyTime
from os import stat as os_stat
import os

class Movie(Source):
	LIST = 0
	DEL = 1
	MOVE = 2
	DIRS = 3

	def __init__(self, session, movielist, func=LIST):
		Source.__init__(self)
		self.func = func
		self.session = session
		if func != self.DIRS:
			self.tagfilter = []
			self.root = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + resolveFilename(SCOPE_HDD))
			self.movielist = movielist #MovieList(self.root)
		self.res = ( False, _("Missing or Wrong Argument") )

	def handleCommand(self, cmd):
		if cmd is not None:
			func = self.func
			if func is self.LIST:
				if cmd['dirname']:
					self.root = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + cmd['dirname'])
				self.tagfilter = cmd['tag'] and cmd['tag'].split(' ') or []
			elif func is self.DEL:
				self.res = self.delMovie(cmd)
			elif func is self.MOVE:
				self.res = self.moveMovie(cmd)
			elif func is self.DIRS:
				self.dirname = cmd['dirname']

	def delMovie(self, param):
#		print "[WebComponents.delMovie] %s" %param

		if param is None:
			return False, _("Missing Parameter: sRef")

		service = ServiceReference(param)
		result = False

		if service is not None:
			#mostly copied from Screens.MovieSelection
			serviceHandler = eServiceCenter.getInstance()
			offline = serviceHandler.offlineOperations(service.ref)
			info = serviceHandler.info(service.ref)
			name = info and info.getName(service.ref) or _("this recording")

			if offline is not None:
				if not offline.deleteFromDisk(0):
					result = True

			if result == False:
				return ( result, _("Could not delete Movie '%s'") % name )
			else:
				return ( result, _("Movie '%s' deleted") % name )

		return ( result, _("Illegal Parameter Value: sRef - '%s'") % param )

	def moveMovie(self, param):
		import os
		import threading
		if not param['sRef']:
			return False, _("Missing Parameter: sRef")
		elif not param['dirname']:
			return False, _("Missing Paramter: dirname")

		try:
			force = int(param['force']) if 'force' in param else False
		except Exception:
			force = False

		try:
			background = int(param['background']) if 'background' in param else False
		except Exception:
			background = False

		destdir = param['dirname']
		if not destdir[-1] == '/':
			destdir = destdir + '/'
		service = ServiceReference(param['sRef'])
		result = False

		if service is not None:
			serviceHandler = eServiceCenter.getInstance()
			info = serviceHandler.info(service.ref)
			path = service.ref.getPath()
			name = info and info.getName(service.ref) or _("this recording")
			basedir = '/'.join(path.split('/')[:-1]) + '/'
			basename = path.split('/')[-1]

			if basedir == destdir:
				return False, _("Source and destination folders are the same.")
			elif not os.path.exists(path):
				return False, _("'%s' does not exist in source directory.") % name
			elif not force and os.path.exists(destdir + basename):
				return False, _("'%s' already exists in destination directory '%s', set force=1 to move anyway.") % (basename, destdir)
			elif not os.path.exists(destdir):
				return False, _("Destination dir '%s' does not exist.") % destdir

			# remove known movie suffixes
			wasTs = False
			forcedSuffix = None
			if basename.endswith('.ts'):
				wasTs = True
				basename = basename[:-3]
			elif basename.endswith(('.avi', '.mkv', '.mpg', '.mp4', '.m4v', '.flv', '.mov', '.iso', '.vob')):
				forcedSuffix = basename[-4:]
				basename = basename[:-4]
			elif basename.endswith(('.divx', '.mpeg', '.m2ts')):
				forcedSuffix = basename[-5:]
				basename = basename[:-5]
			else:
				suffix = basename.split('.')[-1]
				return False, _("Movie '%s' has unknown suffix '%s'.") % (name, suffix)

			def moveFunc():
				exists = os.path.exists
				move = os.rename
				errorlist = []
				if wasTs:
					suffixes = ".ts.meta", ".ts.cuts", ".ts.ap", ".ts.sc", ".eit", ".ts", ".jpg"
				else:
					suffixes = "%s.ts.meta" % forcedSuffix, "%s.cuts" % forcedSuffix, forcedSuffix, '.jpg', '.eit'

				for suffix in suffixes:
					src = basedir + basename + suffix
					if exists(src):
						try:
							move(src, destdir + basename + suffix)
						except OSError as ose:
							errorlist.append(str(ose))
				return errorlist

			if background:
				class StupidThread(threading.Thread):
					def __init__(self, fnc):
						threading.Thread.__init__(self)
						self.fnc = fnc
						self.start()
					def run(self):
						self.fnc()
				StupidThread(moveFunc)
				return True, _("Moving Movie '%s' to '%s' in background.") % (name, destdir)
			else:
				errlist = moveFunc()
				if not errlist:
					return True, _("Movie '%s' moved to '%s' without errors.") % (name, destdir)
				else:
					return False, _("%d error while moving Movie '%s' to '%s': %s") % (len(errlist), name, destdir, ',\n'.join(errlist))
		return ( result, _("Illegal Parameter Value: sRef - '%s'") % param['sRef'] )

	def getMovieList(self):
		self.movielist.reload(root=self.root, filter_tags=self.tagfilter)
		lst = []
		append = lst.append

		loadLength = config.plugins.Webinterface.loadmovielength.value
		for (serviceref, info, begin, unknown) in self.movielist.list:
			if serviceref.flags & eServiceReference.mustDescent:
				# Skip subdirectories (TODO: Browse?)
				continue
			rtime = info.getInfo(serviceref, iServiceInformation.sTimeCreate)

			if rtime > 0:
				t = FuzzyTime(rtime, inPast=True)
				begin_string = t[0] + ", " + t[1]
			else:
				begin_string = _("undefined")

			if loadLength:
				Len = info.getLength(serviceref)
				if Len > 0:
					Len = "%d:%02d" % (Len / 60, Len % 60)
				else:
					Len = "?:??"
			else:
				Len = _("disabled")

			sourceERef = info.getInfoString(serviceref, iServiceInformation.sServiceref)
			sourceRef = ServiceReference(sourceERef)

			event = info.getEvent(serviceref)
			ext = event and event.getExtendedDescription() or ""

			filename = "/" + "/".join(serviceref.toString().split("/")[1:])
			servicename = ServiceReference(serviceref).getServiceName().replace('\xc2\x86', '').replace('\xc2\x87', '')

			append((
				serviceref.toString(),
				servicename,
				info.getInfoString(serviceref, iServiceInformation.sDescription),
				rtime,
				begin_string,
				Len,
				sourceRef.getServiceName(),
				info.getInfoString(serviceref, iServiceInformation.sTags),
				ext,
				filename,
				os_stat(filename)[6]
			))
		return lst

	def getMovieSubdirs(self):
		if not pathExists(self.dirname):
			return []
		locations = []
		for child in os.listdir(self.dirname):
			sep = "" if self.dirname.endswith("/") else "/"
			ch = "%s%s%s/" % (self.dirname, sep, child)
			if os.path.isdir(ch):
				locations.append(ch)
		return locations

	def checkStreamServerSeek(self):
		streamServerSeekInstalled = "False"
		if fileExists("/usr/lib/enigma2/python/Plugins/Extensions/StreamServerSeek/plugin.pyo"):
			streamServerSeekInstalled = "True"
		print "streamServerSeekInstalled", streamServerSeekInstalled
		return streamServerSeekInstalled

	def getResult(self):
		if self.func is self.DEL:
			return self.res
		elif self.func is self.MOVE:
			return self.res

		return ( False, _("illegal call") )

	result = property(getResult)

	simplelist = property(getMovieSubdirs)
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
