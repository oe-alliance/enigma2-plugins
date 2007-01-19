from Plugins.Plugin import PluginDescriptor

from twisted.internet import reactor
from twisted.web2 import server, channel, static, resource, stream, http_headers, responsecode, http
from twisted.python import util
import webif

sessions = [ ]

# set DEBUG to True, if twisted should write logoutput to a file.
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
	class ScreenPage(resource.Resource):
		def __init__(self, path):
			self.path = path
			
		def render(self, req):
			global sessions
			if sessions == [ ]:
				return http.Response(200, stream="please wait until enigma has booted")

			class myProducerStream(stream.ProducerStream):
				closed_callback = None

				def close(self):
					if self.closed_callback:
						self.closed_callback()
					stream.ProducerStream.close(self)

			s = myProducerStream()
			webif.renderPage(s, self.path, req, sessions[0])  # login?

			return http.Response(stream=s)

		def locateChild(self, request, segments):
			path = '/'.join(["web"] + segments)
			if path[-1:] == "/":
				path += "index.html"

			path += ".xml"
			return ScreenPage(path), ()

	class Toplevel(resource.Resource):
		addSlash = True

		def render(self, req):
			return http.Response(responsecode.OK, {'Content-type': http_headers.MimeType('text', 'html')},
				stream='Hello! You want go to <a href="/web/">OSD</a> instead.')

		child_web = ScreenPage("/") # "/web"
		child_hdd = static.File("/hdd")
		child_webdata = static.File(util.sibpath(__file__, "web-data")) # FIXME: web-data appears as webdata

	if PASSWORDPROTECTION is False:
		site = server.Site(Toplevel())
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
		root = wrapper.HTTPAuthResource(Toplevel(),
                                        (basic.BasicCredentialFactory('DM7025'),digest.DigestCredentialFactory(PASSWORDPROTECTION_mode,'DM7025')),
                                        portal, (IHTTPUser,))
		site = server.Site(root)
	reactor.listenTCP(80, channel.HTTPFactory(site))

# start classes for PASSWORDPROTECTION
# end  classes for PASSWORDPROTECTION

def autostart(reason, **kwargs):
	if "session" in kwargs:
		global sessions
		sessions.append(kwargs["session"])
		return

	if reason == 0:
		try:
			"""
			 in normal console output, twisted will print only the first Traceback.
			 is this a bug in twisted or a conflict with enigma2?
			 with this option enabled, twisted will print all TB to the logfile
			 use tail -f <file> to view this log
			"""
			if DEBUG:
				from twisted.python.log import startLogging
				print "start twisted logfile, writing to %s" % DEBUGFILE 
				startLogging(open(DEBUGFILE,'w'))
			
			startWebserver()
		except ImportError:
			print "twisted not available, not starting web services"

def Plugins(**kwargs):
	return PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc = autostart)
