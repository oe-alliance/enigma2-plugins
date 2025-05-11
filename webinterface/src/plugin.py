# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import absolute_import
Version = '$Header$'

from enigma import eConsoleAppContainer
from Plugins.Plugin import PluginDescriptor

from Components.config import config, ConfigBoolean, ConfigSubsection, ConfigInteger, ConfigYesNo, ConfigText, ConfigEnableDisable
from Components.Network import iNetwork
from Screens.MessageBox import MessageBox
from Components.SystemInfo import BoxInfo
from .WebIfConfig import WebIfConfigScreen
from .WebChilds.Toplevel import getToplevel


from Tools.Directories import copyfile, resolveFilename, SCOPE_PLUGINS, SCOPE_CONFIG, fileExists
from Tools.IO import saveFile

from twisted.internet import reactor, ssl
from twisted.internet.error import CannotListenError
from twisted.web import server, http, util, static, resource
from twisted import version

from socket import gethostname as socket_gethostname, has_ipv6
from OpenSSL import SSL, crypto
from time import gmtime
from os.path import isfile as os_isfile, exists as os_exists

from .__init__ import _, __version__, decrypt_block
from .webif import get_random, validate_certificate

import random
import uuid
import time
import hashlib
import six

try:
	from enigma import eTPM
	tpm = eTPM()
except ImportError:
	tpm = None

rootkey = ['\x9f', '|', '\xe4', 'G', '\xc9', '\xb4', '\xf4', '#', '&', '\xce', '\xb3', '\xfe', '\xda', '\xc9', 'U', '`', '\xd8', '\x8c', 's', 'o', '\x90', '\x9b', '\\', 'b', '\xc0', '\x89', '\xd1', '\x8c', '\x9e', 'J', 'T', '\xc5', 'X', '\xa1', '\xb8', '\x13', '5', 'E', '\x02', '\xc9', '\xb2', '\xe6', 't', '\x89', '\xde', '\xcd', '\x9d', '\x11', '\xdd', '\xc7', '\xf4', '\xe4', '\xe4', '\xbc', '\xdb', '\x9c', '\xea', '}', '\xad', '\xda', 't', 'r', '\x9b', '\xdc', '\xbc', '\x18', '3', '\xe7', '\xaf', '|', '\xae', '\x0c', '\xe3', '\xb5', '\x84', '\x8d', '\r', '\x8d', '\x9d', '2', '\xd0', '\xce', '\xd5', 'q', '\t', '\x84', 'c', '\xa8', ')', '\x99', '\xdc', '<', '"', 'x', '\xe8', '\x87', '\x8f', '\x02', ';', 'S', 'm', '\xd5', '\xf0', '\xa3', '_', '\xb7', 'T', '\t', '\xde', '\xa7', '\xf1', '\xc9', '\xae', '\x8a', '\xd7', '\xd2', '\xcf', '\xb2', '.', '\x13', '\xfb', '\xac', 'j', '\xdf', '\xb1', '\x1d', ':', '?']
hw = BoxInfo.getItem("model")
#CONFIG INIT

#init the config
config.plugins.Webinterface = ConfigSubsection()
config.plugins.Webinterface.enabled = ConfigYesNo(default=True)
config.plugins.Webinterface.show_in_extensionsmenu = ConfigYesNo(default=False)
config.plugins.Webinterface.allowzapping = ConfigYesNo(default=True)
config.plugins.Webinterface.includemedia = ConfigYesNo(default=False)
config.plugins.Webinterface.autowritetimer = ConfigYesNo(default=False)
config.plugins.Webinterface.loadmovielength = ConfigYesNo(default=True)
config.plugins.Webinterface.version = ConfigText(__version__)  # used to make the versioninfo accessible enigma2-wide, not confgurable in GUI.

config.plugins.Webinterface.http = ConfigSubsection()
config.plugins.Webinterface.http.enabled = ConfigYesNo(default=True)
config.plugins.Webinterface.http.port = ConfigInteger(default=81, limits=(1, 65535))
config.plugins.Webinterface.http.auth = ConfigYesNo(default=False)

config.plugins.Webinterface.https = ConfigSubsection()
config.plugins.Webinterface.https.enabled = ConfigYesNo(default=True)
config.plugins.Webinterface.https.port = ConfigInteger(default=443, limits=(1, 65535))
config.plugins.Webinterface.https.auth = ConfigYesNo(default=True)

config.plugins.Webinterface.streamauth = ConfigYesNo(default=False)

config.plugins.Webinterface.anti_hijack = ConfigEnableDisable(default=False)
config.plugins.Webinterface.extended_security = ConfigEnableDisable(default=False)

global running_defered, waiting_shutdown, toplevel

running_defered = []
waiting_shutdown = 0
toplevel = None
server.VERSION = "Enigma2 WebInterface Server $Revision$".replace("$Revi", "").replace("sion: ", "").replace("$", "")

KEY_FILE = resolveFilename(SCOPE_CONFIG, "key.pem")
CERT_FILE = resolveFilename(SCOPE_CONFIG, "cert.pem")

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
			print("[Webinterface] stopping interface on ", d.interface, " with port", d.port)
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


def installCertificates(session):
	if not os_exists(CERT_FILE) \
			or not os_exists(KEY_FILE):
		print("[Webinterface].installCertificates :: Generating SSL key pair and CACert")
		# create a key pair
		k = crypto.PKey()
		k.generate_key(crypto.TYPE_RSA, 1024)

		# create a self-signed cert
		cert = crypto.X509()
		cert.get_subject().C = "DE"
		cert.get_subject().ST = "Home"
		cert.get_subject().L = "Home"
		cert.get_subject().O = "Dreambox"
		cert.get_subject().OU = "STB"
		cert.get_subject().CN = socket_gethostname()
		cert.set_serial_number(random.randint(1000000, 1000000000))
		cert.set_notBefore(b"20120101000000Z")
		cert.set_notAfter(b"20301231235900Z")
		cert.set_issuer(cert.get_subject())
		cert.set_pubkey(k)
		print("[Webinterface].installCertificates :: Signing SSL key pair with new CACert")
		cert.sign(k, 'sha1')

		try:
			print("[Webinterface].installCertificates ::  Installing newly generated certificate and key pair")
			saveFile(CERT_FILE, crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
			saveFile(KEY_FILE, crypto.dump_privatekey(crypto.FILETYPE_PEM, k))
		except IOError as e:
			#Disable https
			config.plugins.Webinterface.https.enabled.value = False
			config.plugins.Webinterface.https.enabled.save()
			#Inform the user
			session.open(MessageBox, "Couldn't install generated SSL-Certifactes for https access\nHttps access is disabled!", MessageBox.TYPE_ERROR)


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
		print("[Webinterface] is disabled!")

	else:
		# IF SSL is enabled we need to check for the certs first
		# If they're not there we'll exit via return here
		# and get called after Certificates are installed properly
		if config.plugins.Webinterface.https.enabled.value:
			installCertificates(session)

		# Listen on all Interfaces
		ip = "0.0.0.0"
		#HTTP
		if config.plugins.Webinterface.http.enabled.value is True:
			ret = startServerInstance(session, ip, config.plugins.Webinterface.http.port.value, config.plugins.Webinterface.http.auth.value, l2k)
			if ret is False:
				errors = "%s%s:%i\n" % (errors, ip, config.plugins.Webinterface.http.port.value)
			else:
				registerBonjourService('http', config.plugins.Webinterface.http.port.value)

		#Streaming requires listening on 127.0.0.1:80 no matter what, ensure it its available
		#if config.plugins.Webinterface.http.port.value != 80 or not config.plugins.Webinterface.http.enabled.value:
		#	#LOCAL HTTP Connections (Streamproxy)
		#	ret = startServerInstance(session, '127.0.0.1', 80, config.plugins.Webinterface.http.auth.value, l2k)
		#	if ret == False:
		#		errors = "%s%s:%i\n" %(errors, '127.0.0.1', 80)
		#
		#	if errors != "":
		#		session.open(MessageBox, "Webinterface - Couldn't listen on:\n %s" % (errors), type=MessageBox.TYPE_ERROR, timeout=30)

		#HTTPS
		if config.plugins.Webinterface.https.enabled.value is True:
			ret = startServerInstance(session, ip, config.plugins.Webinterface.https.port.value, config.plugins.Webinterface.https.auth.value, l2k, True)
			if ret is False:
				errors = "%s%s:%i\n" % (errors, ip, config.plugins.Webinterface.https.port.value)
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
	if hw.get_device_name().lower() != "dm7025" and tpm is not None:
		l3k = None
		l3c = tpm.getData(eTPM.DT_LEVEL3_CERT)

		if l3c is None:
			return False

		l3k = validate_certificate(l3c, l2k)
		if l3k is None:
			return False

		random = get_random()
		if random is None:
			return False

		value = tpm.computeSignature(random)
		result = decrypt_block(value, l3k)

		if result is None:
			return False
		else:
			if result[80:88] != random:
				return False

	if useauth:
# HTTPAuthResource handles the authentication for every Resource you want it to
		root = HTTPAuthResource(toplevel, "Enigma2 WebInterface")
		site = server.Site(root)
	else:
		root = HTTPRootResource(toplevel)
		site = server.Site(root)

	if has_ipv6 and fileExists('/proc/net/if_inet6') and version.major >= 12:
		if ipaddress == '0.0.0.0':
			ipaddress = '::'
		elif ipaddress == '127.0.0.1':
			ipaddress = '::1'

	if usessl:
		ctx = ChainedOpenSSLContextFactory(KEY_FILE, CERT_FILE)
		try:
			d = reactor.listenSSL(port, site, ctx, interface=ipaddress)
		except CannotListenError:
			print("[Webinterface] FAILED to listen on %s:%i auth=%s ssl=%s" % (ipaddress, port, useauth, usessl))
			return False
	else:
		try:
			d = reactor.listenTCP(port, site, interface=ipaddress)
			if ipaddress == '::1':
				d = reactor.listenTCP(port, site, interface='::ffff:127.0.0.1')
		except CannotListenError:
			print("[Webinterface] FAILED to listen on %s:%i auth=%s ssl=%s" % (ipaddress, port, useauth, usessl))
			return False

	running_defered.append(d)
	print("[Webinterface] started on %s:%i auth=%s ssl=%s" % (ipaddress, port, useauth, usessl))
	return True

	#except Exception, e:
		#print "[Webinterface] starting FAILED on %s:%i!" % (ipaddress, port), e
		#return False


class ChainedOpenSSLContextFactory(ssl.DefaultOpenSSLContextFactory):
	def __init__(self, privateKeyFileName, certificateChainFileName, sslmethod=SSL.TLSv1_2_METHOD):
		self.privateKeyFileName = privateKeyFileName
		self.certificateChainFileName = certificateChainFileName
		self.sslmethod = sslmethod
		self.cacheContext()

	def cacheContext(self):
		ctx = SSL.Context(self.sslmethod)
		ctx.use_certificate_chain_file(self.certificateChainFileName)
		ctx.use_privatekey_file(self.privateKeyFileName)
		self._context = ctx


class SimpleSession(object):
	def __init__(self, expires=0):
		self._id = "0"
		self._expires = time.time() + expires if expires > 0 else 0

	def _generateId(self):
		if config.plugins.Webinterface.extended_security.value:
			self._id = str(uuid.uuid4())
		else:
			self._id = "0"

	def _getId(self):
		if self.expired():
			self._generateId()
		return self._id

	def expired(self):
		expired = False
		if config.plugins.Webinterface.extended_security.value:
			expired = self._expires > 0 and self._expires < time.time()
			expired = expired or self._id == "0"
		else:
			expired = self._id != "0"
		return expired

	id = property(_getId)

#Every request made will pass this Resource (as it is the root resource)
#Any "global" checks should be done here


class HTTPRootResource(resource.Resource):
	SESSION_PROTECTED_PATHS = [b'/web/', b'/opkg', b'/ipkg']
	SESSION_EXCEPTIONS = [
		b'/web/epgsearch.rss', b'/web/movielist.m3u', b'/web/movielist.rss', b'/web/services.m3u', b'/web/session',
		b'/web/stream.m3u', b'/web/stream', b'/web/streamcurrent.m3u', b'/web/strings.js', b'/web/ts.m3u']

	def __init__(self, res):
		print("[HTTPRootResource}.__init__")
		resource.Resource.__init__(self)
		self.resource = res
		self.sessionInvalidResource = resource.ErrorPage(http.PRECONDITION_FAILED, "Precondition failed!", "sessionid is missing, invalid or expired!")
		self._sessions = {}

	def getClientToken(self, request):
		ip = request.getClientIP()
		ua = request.getHeader("User-Agent") or "Default UA"
		return hashlib.sha1(six.ensure_binary("%s/%s" % (ip, ua))).hexdigest()

	def isSessionValid(self, request):
		session = self._sessions.get(self.getClientToken(request), None)
		if session is None or session.expired():
			session = SimpleSession()
			key = self.getClientToken(request)
			print("[HTTPRootResource].isSessionValid :: created session with id '%s' for client with token '%s'" % (session.id, key))
			self._sessions[key] = session

		request.enigma2_session = session

		if config.plugins.Webinterface.extended_security.value and request.path not in self.SESSION_EXCEPTIONS:
			protected = False
			for path in self.SESSION_PROTECTED_PATHS:
				if request.path.startswith(path):
					protected = True

			if protected:
				rsid = request.args.get('sessionid', None)
				if rsid:
					rsid = rsid[0]
				return session and session.id == rsid

		return True

	def render(self, request):
		#enable SAMEORIGIN policy for iframes
		if config.plugins.Webinterface.anti_hijack.value:
			request.setHeader("X-Frame-Options", "SAMEORIGIN")

		if self.isSessionValid(request):
			return self.resource.render(request)
		else:
			return self.sessionInvalidResource.render(request)

	def getChildWithDefault(self, path, request):
		#enable SAMEORIGIN policy for iframes
		if config.plugins.Webinterface.anti_hijack.value:
			request.setHeader("X-Frame-Options", "SAMEORIGIN")

		if self.isSessionValid(request):
			return self.resource.getChildWithDefault(path, request)
		else:
			print("[Webinterface.HTTPRootResource.render] !!! session invalid !!!")
			return self.sessionInvalidResource

#===============================================================================
# HTTPAuthResource
# Handles HTTP Authorization for a given Resource
#===============================================================================


class HTTPAuthResource(HTTPRootResource):
	def __init__(self, res, realm):
		HTTPRootResource.__init__(self, res)
		self.realm = realm
		self.authorized = False
		self.unauthorizedResource = resource.ErrorPage(http.UNAUTHORIZED, "Access denied", "Authentication credentials invalid!")

	def unauthorized(self, request):
		request.setHeader('WWW-authenticate', 'Basic realm="%s"' % self.realm)
		request.setResponseCode(http.UNAUTHORIZED)
		return self.unauthorizedResource

	def isAuthenticated(self, request):
		host = request.getHost().host
		#If streamauth is disabled allow all acces from localhost
		if not config.plugins.Webinterface.streamauth.value:
			if (host == "::ffff:127.0.0.1" or host == "127.0.0.1" or host == "localhost"):
				print("[WebInterface.plugin.isAuthenticated] Streaming auth is disabled bypassing authcheck because host is '%s'" % host)
				return True

		# get the Session from the Request
		http_session = request.getSession().sessionNamespaces

		# if the auth-information has not yet been stored to the http_session
		if 'authenticated' not in http_session:
			if request.getUser() != '':
				http_session['authenticated'] = check_passwd(request.getUser(), request.getPassword())
			else:
				http_session['authenticated'] = False

		#if the auth-information already is in the http_session
		else:
			if http_session['authenticated'] is False:
				http_session['authenticated'] = check_passwd(request.getUser(), request.getPassword())

		#return the current authentication status
		return http_session['authenticated']

#===============================================================================
# Call render of self.resource (if authenticated)
#===============================================================================
	def render(self, request):
		if self.isAuthenticated(request) is True:
			return HTTPRootResource.render(self, request)
		else:
			print("[Webinterface.HTTPAuthResource.render] !!! unauthorized !!!")
			return self.unauthorized(request).render(request)

#===============================================================================
# Override to call getChildWithDefault of self.resource (if authenticated)
#===============================================================================
	def getChildWithDefault(self, path, request):
		if self.isAuthenticated(request) is True:
			return HTTPRootResource.getChildWithDefault(self, path, request)
		else:
			print("[Webinterface.HTTPAuthResource.getChildWithDefault] !!! unauthorized !!!")
			return self.unauthorized(request)


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

	#shadowed or not, that's the questions here
	if cryptedpass == 'x' or cryptedpass == '*':
		try:
			cryptedpass = getspnam(name)[1]
		except:
			return False

	if cryptedpass == '':
		return True

	return crypt(passwd, cryptedpass) == cryptedpass


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
		print("[WebInterface.registerBonjourService] Service for protocol '%s' with port '%i' registered!" % (protocol, port))
		return True

	except ImportError as e:
		print("[WebInterface.registerBonjourService] %s" % e)
		return False


def unregisterBonjourService(protocol):
	try:
		from Plugins.Extensions.Bonjour.Bonjour import bonjour

		bonjour.unregisterService(protocol)
		print("[WebInterface.unregisterBonjourService] Service for protocol '%s' unregistered!" % (protocol))
		return True

	except ImportError as e:
		print("[WebInterface.unregisterBonjourService] %s" % e)
		return False


def checkBonjour():
	if (not config.plugins.Webinterface.http.enabled.value) or (not config.plugins.Webinterface.enabled.value):
		unregisterBonjourService('http')
	if (not config.plugins.Webinterface.https.enabled.value) or (not config.plugins.Webinterface.enabled.value):
		unregisterBonjourService('https')

#===============================================================================
# networkstart
# Actions to take place after Network is up (startup the Webserver)
#===============================================================================
#def networkstart(reason, **kwargs):


def networkstart(reason, session):
	l2r = False
	l2k = None
	if hw.get_device_name().lower() != "dm7025" and tpm is not None:
		l2c = tpm.getData(eTPM.DT_LEVEL2_CERT)

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
	if hw.get_device_name().lower() != "dm7025" and tpm is not None:
		l2c = tpm.getData(eTPM.DT_LEVEL2_CERT)

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
			print("[WebIf] config changed")
			restartWebserver(session, l2k)
			checkBonjour()
		else:
			print("[WebIf] config not changed")


def Plugins(**kwargs):
	p = PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=sessionstart)
	p.weight = 100  # webif should start as last plugin
	list = [p,
#			PluginDescriptor(where=[PluginDescriptor.WHERE_NETWORKCONFIG_READ], fnc=networkstart),
			PluginDescriptor(name=_("Webinterface"), description=_("Configuration for the Webinterface"),
							where=[PluginDescriptor.WHERE_PLUGINMENU], icon="plugin.png", fnc=openconfig)]
	if config.plugins.Webinterface.show_in_extensionsmenu.value:
		list.append(PluginDescriptor(name="Webinterface", description=_("Configuration for the Webinterface"),
			where=PluginDescriptor.WHERE_EXTENSIONSMENU, icon="plugin.png", fnc=openconfig))
	return list
