from Plugins.Plugin import PluginDescriptor

from twisted.internet import reactor
from twisted.web2 import server, channel, static, resource, stream, http_headers, responsecode, http
from twisted.python import util
from twisted.python.log import startLogging,discardLogs

import webif
import WebIfConfig  
import os

from Components.config import config, ConfigSubsection, ConfigInteger,ConfigYesNo

config.plugins.Webinterface = ConfigSubsection()
config.plugins.Webinterface.enable = ConfigYesNo(default = False)
config.plugins.Webinterface.port = ConfigInteger(80,limits = (1, 999))
config.plugins.Webinterface.includehdd = ConfigYesNo(default = False)

sessions = [ ]

 
"""
 set DEBUG to True, if twisted should write logoutput to a file.
 in normal console output, twisted will print only the first Traceback.
 is this a bug in twisted or a conflict with enigma2?
 with this option enabled, twisted will print all TB to the logfile
 use tail -f <file> to view this log
"""
			
DEBUG = False
DEBUGFILE= "/tmp/twisted.log"

# Passwordprotection Test
# set it only to True, if you have a patched wrapper.py
# see http://twistedmatrix.com/trac/ticket/2041
# in /usr/lib/python2.4/site-packages/twisted/web2/auth/wrapper.py
# The solution is to change this line
#	
#	return self.authenticate(req), seg[1:]
# into this
#	return self.authenticate(req), seg
PASSWORDPROTECTION = False
PASSWORDPROTECTION_pwd = "root"
PASSWORDPROTECTION_mode = "sha"; 
# twisted supports more than sha ('md5','md5-sess','sha')
# but only sha works for me, but IE 
# sha, Firefox=ok, Opera=ok, wget=ok, ie=not ok
# md5-sess, firefox=not ok, opera=not ok,wget=ok, ie=not ok
# md5 same as md5-sess 

def startWebserver():
	if config.plugins.Webinterface.enable.value is not True:
		print "not starting Werbinterface"
		return False
	if DEBUG:
		print "start twisted logfile, writing to %s" % DEBUGFILE 
		import sys
		startLogging(sys.stdout,0)
		#startLogging(open(DEBUGFILE,'w'))

	class ScreenPage(resource.Resource):
		def __init__(self, path):
			self.path = path
			
			
		def render(self, req):
			global sessions
			if sessions == [ ]:
				return http.Response(responsecode.OK, stream="please wait until enigma has booted")

			class myProducerStream(stream.ProducerStream):
				closed_callback = None

				def close(self):
					if self.closed_callback:
						self.closed_callback()
					stream.ProducerStream.close(self)

			if os.path.isfile(self.path):
				s=myProducerStream()
				webif.renderPage(s, self.path, req, sessions[0])  # login?
				return http.Response(responsecode.OK,stream=s)
			else:
				return http.Response(responsecode.NOT_FOUND)
			
		def locateChild(self, request, segments):
			path = self.path+'/'+'/'.join(segments)
			if path[-1:] == "/":
				path += "index.html"
			path +=".xml"
			return ScreenPage(path), ()
 		
	class Toplevel(resource.Resource):
		addSlash = True

		def render(self, req):
			fp = open(util.sibpath(__file__, "web-data")+"/index.html")
			s = fp.read()
			fp.close()
			return http.Response(responsecode.OK, {'Content-type': http_headers.MimeType('text', 'html')},stream=s)

		child_web = ScreenPage(util.sibpath(__file__, "web")) # "/web/*"
		child_webdata = static.File(util.sibpath(__file__, "web-data")) # FIXME: web-data appears as webdata

	toplevel = Toplevel()
	if config.plugins.Webinterface.includehdd.value:
		toplevel.putChild("hdd",static.File("/hdd"))
	
	if PASSWORDPROTECTION is False:
		site = server.Site(toplevel)
	else:
		from twisted.cred.portal import Portal
		from twisted.cred import checkers
		from twisted.web2.auth import digest, basic, wrapper
		from zope.interface import Interface, implements
		from twisted.cred import portal
		class IHTTPUser(Interface):
			pass

		class HTTPUser(object):
			implements(IHTTPUser)

		class HTTPAuthRealm(object):
			implements(portal.IRealm)
			def requestAvatar(self, avatarId, mind, *interfaces):
				if IHTTPUser in interfaces:
					return IHTTPUser, HTTPUser()
				raise NotImplementedError("Only IHTTPUser interface is supported")

		portal = Portal(HTTPAuthRealm())
		checker = checkers.InMemoryUsernamePasswordDatabaseDontUse(root=PASSWORDPROTECTION_pwd)
		portal.registerChecker(checker)
		root = wrapper.HTTPAuthResource(toplevel,
                                        (basic.BasicCredentialFactory('DM7025'),digest.DigestCredentialFactory(PASSWORDPROTECTION_mode,'DM7025')),
                                        portal, (IHTTPUser,))
		site = server.Site(root)
	print "[WebIf] starting Webinterface on port",config.plugins.Webinterface.port.value
	reactor.listenTCP(config.plugins.Webinterface.port.value, channel.HTTPFactory(site))

	
def autostart(reason, **kwargs):
	if "session" in kwargs:
		global sessions
		sessions.append(kwargs["session"])
		return
	if reason == 0:
		try:
			startWebserver()
		except ImportError:
			print "[WebIf] twisted not available, not starting web services"
			
def openconfig(session, **kwargs):
	session.openWithCallback(configCB,WebIfConfig.WebIfConfigScreen)

def configCB(result):
	if result is True:
		print "[WebIf] config changed"
		# add some code here to restart twisted. ut you are warned, this ist not easy, i´ve tried it ;)
	else:
		print "[WebIf] config not changed"
		

def Plugins(**kwargs):
	return [PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc = autostart),
		    PluginDescriptor(name=_("Webinterface"), description=_("Configuration for the Webinterface"),where = [PluginDescriptor.WHERE_PLUGINMENU], icon="plugin.png",fnc = openconfig)]
