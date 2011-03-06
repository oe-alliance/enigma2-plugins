Version = '$Header$';

from enigma import eConsoleAppContainer, eTPM
from Plugins.Plugin import PluginDescriptor

from Components.config import config, ConfigBoolean, ConfigSubsection, ConfigInteger, ConfigYesNo, ConfigText
from Components.Network import iNetwork
from Screens.MessageBox import MessageBox
from WebIfConfig import WebIfConfigScreen
from WebChilds.Toplevel import getToplevel
from Tools.HardwareInfo import HardwareInfo

from Tools.Directories import copyfile, resolveFilename, SCOPE_PLUGINS, SCOPE_CONFIG

from twisted.internet import reactor, ssl
from twisted.web import server, http, util, static, resource

from zope.interface import Interface, implements
from socket import gethostname as socket_gethostname
from OpenSSL import SSL

from os.path import isfile as os_isfile
from __init__ import _, __version__, decrypt_block
from webif import get_random, validate_certificate

#CONFIG INIT

#init the config
config.plugins.Webinterface = ConfigSubsection()
config.plugins.Webinterface.enabled = ConfigYesNo(default=True)
config.plugins.Webinterface.allowzapping = ConfigYesNo(default=True)
config.plugins.Webinterface.includemedia = ConfigYesNo(default=False)
config.plugins.Webinterface.autowritetimer = ConfigYesNo(default=False)
config.plugins.Webinterface.loadmovielength = ConfigYesNo(default=True)
config.plugins.Webinterface.version = ConfigText(__version__) # used to make the versioninfo accessible enigma2-wide, not confgurable in GUI.

config.plugins.Webinterface.http = ConfigSubsection()
config.plugins.Webinterface.http.enabled = ConfigYesNo(default=True)
config.plugins.Webinterface.http.port = ConfigInteger(default = 80, limits=(1, 65535) )
config.plugins.Webinterface.http.auth = ConfigYesNo(default=False)

config.plugins.Webinterface.https = ConfigSubsection()
config.plugins.Webinterface.https.enabled = ConfigYesNo(default=False)
config.plugins.Webinterface.https.port = ConfigInteger(default = 443, limits=(1, 65535) )
config.plugins.Webinterface.https.auth = ConfigYesNo(default=True)

config.plugins.Webinterface.streamauth = ConfigYesNo(default=False)

global running_defered, waiting_shutdown, toplevel

running_defered = []
waiting_shutdown = 0
toplevel = None
server.VERSION = "Enigma2 WebInterface Server $Revision$".replace("$Revi", "").replace("sion: ", "").replace("$", "")

#===============================================================================
# Helperclass to close running Instances of the Webinterface
#===============================================================================
class Closer:
	counter = 0
	def __init__(self, session, callback=None, l2k=None):
		self.callback = callback
		self.session = session
		self.l2k = l2k
#===============================================================================
# Closes all running Instances of the Webinterface
#===============================================================================
	def stop(self):
		global running_defered
		for d in running_defered:
			print "[Webinterface] stopping interface on ", d.interface, " with port", d.port
			x = d.stopListening()
			
			try:
				x.addCallback(self.isDown)
				self.counter += 1
			except AttributeError:
				pass
		running_defered = []
		if self.counter < 1:
			if self.callback is not None:
				self.callback(self.session, self.l2k)

#===============================================================================
# #Is it already down?
#===============================================================================
	def isDown(self, s):
		self.counter -= 1
		if self.counter < 1:
			if self.callback is not None:
				self.callback(self.session, self.l2k)

def checkCertificates():
	print "[WebInterface] checking for SSL Certificates"
	srvcert = '%sserver.pem' %resolveFilename(SCOPE_CONFIG) 
	cacert = '%scacert.pem' %resolveFilename(SCOPE_CONFIG)

	# Check whether there are regular certificates, if not copy the default ones over
	if not os_isfile(srvcert) or not os_isfile(cacert):
		return False
	
	else:
		return True
		
def installCertificates(session, callback = None, l2k = None):
	print "[WebInterface] Installing SSL Certificates to %s" %resolveFilename(SCOPE_CONFIG)
	
	srvcert = '%sserver.pem' %resolveFilename(SCOPE_CONFIG) 
	cacert = '%scacert.pem' %resolveFilename(SCOPE_CONFIG)	
	scope_webif = '%sExtensions/WebInterface/' %resolveFilename(SCOPE_PLUGINS)
	
	source = '%setc/server.pem' %scope_webif
	target = srvcert
	ret = copyfile(source, target)
	
	if ret == 0:
		source = '%setc/cacert.pem' %scope_webif
		target = cacert
		ret = copyfile(source, target)
		
		if ret == 0 and callback != None:
			callback(session, l2k)
	
	if ret < 0:
		config.plugins.Webinterface.https.enabled.value = False
		config.plugins.Webinterface.https.enabled.save()
		
		# Start without https
		callback(session, l2k)
		
		#Inform the user
		session.open(MessageBox, "Couldn't install SSL-Certifactes for https access\nHttps access is now disabled!", MessageBox.TYPE_ERROR)
	
#===============================================================================
# restart the Webinterface for all configured Interfaces
#===============================================================================
def restartWebserver(session, l2k):
	try:
		del session.mediaplayer
		del session.messageboxanswer
	except NameError:
		pass
	except AttributeError:
		pass

	global running_defered
	if len(running_defered) > 0:
		Closer(session, startWebserver, l2k).stop()
	else:
		startWebserver(session, l2k)
	
#===============================================================================
# start the Webinterface for all configured Interfaces
#===============================================================================
def startWebserver(session, l2k):
	global running_defered
	global toplevel
	
	session.mediaplayer = None
	session.messageboxanswer = None
	if toplevel is None:
		toplevel = getToplevel(session)
	
	errors = ""
	
	if config.plugins.Webinterface.enabled.value is not True:
		print "[Webinterface] is disabled!"
	
	else:
		# IF SSL is enabled we need to check for the certs first
		# If they're not there we'll exit via return here 
		# and get called after Certificates are installed properly
		if config.plugins.Webinterface.https.enabled.value:
			if not checkCertificates():
				print "[Webinterface] Installing Webserver Certificates for SSL encryption"
				installCertificates(session, startWebserver, l2k)
				return
		# Listen on all Interfaces
		ip = "0.0.0.0"
		#HTTP
		if config.plugins.Webinterface.http.enabled.value is True:
			ret = startServerInstance(session, ip, config.plugins.Webinterface.http.port.value, config.plugins.Webinterface.http.auth.value, l2k)
			if ret == False:
				errors = "%s%s:%i\n" %(errors, ip, config.plugins.Webinterface.http.port.value)
			else:
				registerBonjourService('http', config.plugins.Webinterface.http.port.value)
			
		#Streaming requires listening on 127.0.0.1:80 no matter what, ensure it its available
		if config.plugins.Webinterface.http.port.value != 80 or not config.plugins.Webinterface.http.enabled.value:
			#LOCAL HTTP Connections (Streamproxy)
			ret = startServerInstance(session, '127.0.0.1', 80, config.plugins.Webinterface.http.auth.value, l2k)			
			if ret == False:
				errors = "%s%s:%i\n" %(errors, '127.0.0.1', 80)
			
			if errors != "":
				session.open(MessageBox, "Webinterface - Couldn't listen on:\n %s" % (errors), type=MessageBox.TYPE_ERROR, timeout=30)
				
		#HTTPS		
		if config.plugins.Webinterface.https.enabled.value is True:					
			ret = startServerInstance(session, ip, config.plugins.Webinterface.https.port.value, config.plugins.Webinterface.https.auth.value, l2k, True)
			if ret == False:
				errors = "%s%s:%i\n" %(errors, ip, config.plugins.Webinterface.https.port.value)
			else:
				registerBonjourService('https', config.plugins.Webinterface.https.port.value)
		
#===============================================================================
# stop the Webinterface for all configured Interfaces
#===============================================================================
def stopWebserver(session):
	try:
		del session.mediaplayer
		del session.messageboxanswer
	except NameError:
		pass
	except AttributeError:
		pass

	global running_defered
	if len(running_defered) > 0:
		Closer(session).stop()

#===============================================================================
# startServerInstance
# Starts an Instance of the Webinterface
# on given ipaddress, port, w/o auth, w/o ssl
#===============================================================================
def startServerInstance(session, ipaddress, port, useauth=False, l2k=None, usessl=False):
	if False:
		l3k = None		
		l3c = tpm.getCert(eTPM.TPMD_DT_LEVEL3_CERT)
		
		if l3c is None:
			return False			
		
		l3k = validate_certificate(l3c, l2k)
		if l3k is None:			
			return False
		
		random = get_random()
		if random is None:
			return False
	
		value = tpm.challenge(random)
		result = decrypt_block(value, l3k)
		
		if result is None:
			return False
		else:
			if result [80:88] != random:		
				return False
		
	if useauth:
# HTTPAuthResource handles the authentication for every Resource you want it to			
		root = HTTPAuthResource(toplevel, "Enigma2 WebInterface")
		site = server.Site(root)			
	else:
		site = server.Site(toplevel)

	if usessl:
		
		ctx = ssl.DefaultOpenSSLContextFactory('/etc/enigma2/server.pem', '/etc/enigma2/cacert.pem', sslmethod=SSL.SSLv23_METHOD)
		d = reactor.listenSSL(port, site, ctx, interface=ipaddress)
	else:
		d = reactor.listenTCP(port, site, interface=ipaddress)
	running_defered.append(d)		
	print "[Webinterface] started on %s:%i auth=%s ssl=%s" % (ipaddress, port, useauth, usessl)
	return True
	
	#except Exception, e:
		#print "[Webinterface] starting FAILED on %s:%i!" % (ipaddress, port), e		
		#return False
#===============================================================================
# HTTPAuthResource
# Handles HTTP Authorization for a given Resource
#===============================================================================
class HTTPAuthResource(resource.Resource):
	def __init__(self, res, realm):
		resource.Resource.__init__(self)
		self.resource = res
		self.realm = realm
		self.authorized = False
		self.tries = 0
		self.unauthorizedResource = UnauthorizedResource(self.realm)
	
	def unautorized(self, request):
		request.setResponseCode(http.UNAUTHORIZED)
		request.setHeader('WWW-authenticate', 'basic realm="%s"' % self.realm)

		return self.unauthorizedResource
	
	def isAuthenticated(self, request):		
		host = request.getHost().host
		#If streamauth is disabled allow all acces from localhost
		if not config.plugins.Webinterface.streamauth.value:			
			if( host == "127.0.0.1" or host == "localhost" ):
				print "[WebInterface.plugin.isAuthenticated] Streaming auth is disabled bypassing authcheck because host is '%s'" %host
				return True
					
		# get the Session from the Request
		sessionNs = request.getSession().sessionNamespaces
		
		# if the auth-information has not yet been stored to the session
		if not sessionNs.has_key('authenticated'):
			if request.getUser() != '':
				sessionNs['authenticated'] = check_passwd(request.getUser(), request.getPassword())
			else:
				sessionNs['authenticated'] = False
		
		#if the auth-information already is in the session				
		else:
			if sessionNs['authenticated'] is False:
				sessionNs['authenticated'] = check_passwd(request.getUser(), request.getPassword() )
		
		#return the current authentication status						
		return sessionNs['authenticated']
													
#===============================================================================
# Call render of self.resource (if authenticated)													
#===============================================================================
	def render(self, request):			
		if self.isAuthenticated(request) is True:	
			return self.resource.render(request)
		
		else:
			print "[Webinterface.HTTPAuthResource.render] !!! unauthorized !!!"
			return self.unautorized(request).render(request)

#===============================================================================
# Override to call getChildWithDefault of self.resource (if authenticated)	
#===============================================================================
	def getChildWithDefault(self, path, request):
		if self.isAuthenticated(request) is True:
			return self.resource.getChildWithDefault(path, request)
		
		else:
			print "[Webinterface.HTTPAuthResource.render] !!! unauthorized !!!"
			return self.unautorized(request)

#===============================================================================
# UnauthorizedResource
# Returns a simple html-ified "Access Denied"
#===============================================================================
class UnauthorizedResource(resource.Resource):
	def __init__(self, realm):
		resource.Resource.__init__(self)
		self.realm = realm
		self.errorpage = static.Data('<html><body>Access Denied.</body></html>', 'text/html')
	
	def getChild(self, path, request):
		return self.errorpage
		
	def render(self, request):	
		return self.errorpage.render(request)



# Password verfication stuff
from crypt import crypt
from pwd import getpwnam
from spwd import getspnam


def check_passwd(name, passwd):
	cryptedpass = None
	try:
		cryptedpass = getpwnam(name)[1]
	except:
		return False
	
	if cryptedpass:
		#shadowed or not, that's the questions here
		if cryptedpass == 'x' or cryptedpass == '*':
			try:
				cryptedpass = getspnam(name)[1]
			except:
				return False			
				
		return crypt(passwd, cryptedpass) == cryptedpass
	return False

global_session = None

#===============================================================================
# sessionstart
# Actions to take place on Session start 
#===============================================================================
def sessionstart(reason, session):
	global global_session
	global_session = session
	networkstart(True, session)


def registerBonjourService(protocol, port):	
	try:
		from Plugins.Extensions.Bonjour.Bonjour import bonjour
				
		service = bonjour.buildService(protocol, port)
		bonjour.registerService(service, True)
		print "[WebInterface.registerBonjourService] Service for protocol '%s' with port '%i' registered!" %(protocol, port) 
		return True
		
	except ImportError, e:
		print "[WebInterface.registerBonjourService] %s" %e
		return False

def unregisterBonjourService(protocol):	
	try:
		from Plugins.Extensions.Bonjour.Bonjour import bonjour
						
		bonjour.unregisterService(protocol)
		print "[WebInterface.unregisterBonjourService] Service for protocol '%s' unregistered!" %(protocol) 
		return True
		
	except ImportError, e:
		print "[WebInterface.unregisterBonjourService] %s" %e
		return False
	
def checkBonjour():
	if ( not config.plugins.Webinterface.http.enabled.value ) or ( not config.plugins.Webinterface.enabled.value ):
		unregisterBonjourService('http')
	if ( not config.plugins.Webinterface.https.enabled.value ) or ( not config.plugins.Webinterface.enabled.value ):
		unregisterBonjourService('https')
		
#===============================================================================
# networkstart
# Actions to take place after Network is up (startup the Webserver)
#===============================================================================
#def networkstart(reason, **kwargs):
def networkstart(reason, session):
	l2r = False
	l2k = None
	if False:
		l2c = tpm.getCert(eTPM.TPMD_DT_LEVEL2_CERT)
		
		if l2c is None:
			return
		
		l2k = validate_certificate(l2c, rootkey)
		if l2k is None:
			return
			
		l2r = True
	else:
		l2r = True
		
	if l2r:	
		if reason is True:
			startWebserver(session, l2k)
			checkBonjour()
			
		elif reason is False:
			stopWebserver(session)
			checkBonjour()
		
def openconfig(session, **kwargs):
	session.openWithCallback(configCB, WebIfConfigScreen)

def configCB(result, session):
	l2r = False
	l2k = None
	if False:
		l2c = tpm.getCert(eTPM.TPMD_DT_LEVEL2_CERT)
		
		if l2c is None:
			return
		
		l2k = validate_certificate(l2c, rootkey)
		if l2k is None:
			return
			
		l2r = True
	else:
		l2r = True
		
	if l2r:	
		if result:
			print "[WebIf] config changed"
			restartWebserver(session, l2k)
			checkBonjour()
		else:
			print "[WebIf] config not changed"

def Plugins(**kwargs):
	p = PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=sessionstart)
	p.weight = 100 #webif should start as last plugin
	return [p,
#			PluginDescriptor(where=[PluginDescriptor.WHERE_NETWORKCONFIG_READ], fnc=networkstart),
			PluginDescriptor(name=_("Webinterface"), description=_("Configuration for the Webinterface"),
							where=[PluginDescriptor.WHERE_PLUGINMENU], icon="plugin.png", fnc=openconfig)]
