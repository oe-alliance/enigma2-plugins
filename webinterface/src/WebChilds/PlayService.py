from enigma import eServiceReference
from twisted.web import resource, http, server
from os import path as os_path

class ServiceplayerResource(resource.Resource):
	def __init__(self, session):
		resource.Resource.__init__(self)
		self.session = session
		self.oldservice = None
	
	def render(self, request):
		if 'file' in request.args:
			output = self.playFile(request.args['file'][0])
		elif 'url' in request.args:
			output = self.playURL(request.args['url'][0])
		elif 'stop' in request.args:
			output = self.stopServicePlay()
		else:
			output = True, "unknown command"
			
		request.setResponseCode(http.OK)
		request.write(output[1])
		request.finish()
					
		return server.NOT_DONE_YET

	def playFile(self, path):
		print "[ServiceplayerResource] playing file", path
		if os_path.exists(path) is not True:
			return False, "given path is not existing, %s" % path
		else:
			sref = "4097:0:0:0:0:0:0:0:0:0:%s" % path
			self.startServicePlay(eServiceReference(sref))
			return True, "playing path started, %s" % path

	def playURL(self, url):
		#url= url.replace("%3a",":").replace("%20"," ")
		#print "[ServiceplayerResource] playing url",url
		#sref = "4097:0:0:0:0:0:0:0:0:0:%s"%url
		#self.startServicePlay(eServiceReference(sref))
		return False, "Not implemented"

	def startServicePlay(self, esref):
		print "[ServiceplayerResource] playing sref", esref.toString()
		csref = self.session.nav.getCurrentlyPlayingServiceReference()
		if csref is not None:
			if csref.toString().startswith("4097") is not True:
				self.oldservice = csref.toString(), csref

		self.session.nav.stopService()
		self.session.nav.playService(esref)

	def stopServicePlay(self):
		print "[ServiceplayerResource] stopping service", self.oldservice
		self.session.nav.stopService()
		if self.oldservice is not None:
			self.session.nav.playService(self.oldservice[1])
			return True, "[ServiceplayerResource] stopped, now playing old service, %s" % self.oldservice[0]
		else:
			return True, "[ServiceplayerResource] stopped"

