Version = '$Header$';
from Plugins.Plugin import PluginDescriptor
from Components.config import config, ConfigSubsection, ConfigInteger, ConfigYesNo, ConfigText, ConfigSubList
from Screens.MessageBox import MessageBox
from WebIfConfig import WebIfConfigScreen, initConfig, updateConfig
from WebChilds.Toplevel import getToplevel

from twisted.internet import reactor, ssl
from twisted.web import server, http, util, static, resource
from twisted.python.log import startLogging

from zope.interface import Interface, implements
from socket import gethostname as socket_gethostname
from OpenSSL import SSL

from __init__ import _, __version__

DEBUG_TO_FILE = False # PLEASE DONT ENABLE LOGGING BY DEFAULT (OR COMMIT TO PLUGIN CVS)

DEBUGFILE = "/tmp/twisted.log"

#CONFIG INIT

#init the config
config.plugins.Webinterface = ConfigSubsection()
config.plugins.Webinterface.enable = ConfigYesNo(default=True)
config.plugins.Webinterface.allowzapping = ConfigYesNo(default=True)
config.plugins.Webinterface.includemedia = ConfigYesNo(default=False)
config.plugins.Webinterface.autowritetimer = ConfigYesNo(default=False)
config.plugins.Webinterface.loadmovielength = ConfigYesNo(default=False)
config.plugins.Webinterface.version = ConfigText(__version__) # used to make the versioninfo accessible enigma2-wide, not confgurable in GUI.
config.plugins.Webinterface.interfacecount = ConfigInteger(0)
config.plugins.Webinterface.interfaces = ConfigSubList()
initConfig()
config.plugins.Webinterface.warningsslsend = ConfigYesNo(default=False)

global running_defered, waiting_shutdown
running_defered = []
waiting_shutdown = 0
server.VERSION = "Enigma2 WebInterface Server $Revision$".replace("$Revi", "").replace("sion: ", "").replace("$", "")

class Closer:
	counter = 0
	def __init__(self, session, callback=None):
		self.callback = callback
		self.session = session

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
				self.callback(self.session)

	def isDown(self, s):
		self.counter -= 1
		if self.counter < 1:
			if self.callback is not None:
				self.callback(self.session)

def restartWebserver(session):
	try:
		del session.mediaplayer
		del session.messageboxanswer
	except NameError:
		pass
	except AttributeError:
		pass

	global running_defered
	if len(running_defered) > 0:
		Closer(session, startWebserver).stop()
	else:
		startWebserver(session)

def startWebserver(session):
	global running_defered
	session.mediaplayer = None
	session.messageboxanswer = None

	if config.plugins.Webinterface.enable.value is not True:
		print "[Webinterface] is disabled!"
		return False
	if DEBUG_TO_FILE:
		print "[Webinterface] start twisted logfile, writing to %s" % DEBUGFILE
		startLogging(open(DEBUGFILE, 'w'))

	for c in config.plugins.Webinterface.interfaces:
		if c.disabled.value is False:
			startServerInstance(session, c.address.value, c.port.value, c.useauth.value, c.usessl.value)
		else:
			print "[Webinterface] not starting disabled interface on %s:%i" % (c.address.value, c.port.value)

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

def startServerInstance(session, ipaddress, port, useauth=False, usessl=False):
	try:
		toplevel = getToplevel(session)
		if useauth:
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
		print "[Webinterface] started on %s:%i" % (ipaddress, port), "auth=", useauth, "ssl=", usessl
	
	except Exception, e:
		print "[Webinterface] starting FAILED on %s:%i!" % (ipaddress, port), e
		session.open(MessageBox, 'starting FAILED on %s:%i!\n\n%s' % (ipaddress, port, str(e)), MessageBox.TYPE_ERROR)
	
class HTTPAuthResource(resource.Resource):
	def __init__(self, res, realm):
		resource.Resource.__init__(self)
		self.resource = res
		self.realm = realm
		self.authorized = False
		self.tries = 0
		self.unauthorizedResource = UnauthorizedResource(self.realm)		
	
	def unautorized(self, request):
		print "[Webinterface] Unauthorized!"
		request.setResponseCode(http.UNAUTHORIZED)
		request.setHeader('WWW-authenticate', 'basic realm="%s"' % self.realm)

		return self.unauthorizedResource
	
	def isAuthenticated(self, request):
		# get the Session from the Request
		sessionNs = request.getSession().sessionNamespaces
		
		# if the auth-information has not yet been stored to the session
		if not sessionNs.has_key('authenticated'):
			sessionNs['authenticated'] = check_passwd(request.getUser(), request.getPassword())
		
		#if the auth-information already is in the session				
		else:
			if sessionNs['authenticated'] is False:
				sessionNs['authenticated'] = check_passwd(request.getUser(), request.getPassword() )
		
		#return the current authentication status						
		return sessionNs['authenticated']
													
													
	def render(self, request):			
		if self.isAuthenticated(request) is True:	
			return self.resource.render(request)
		
		else:
			return self.unautorized(request)
	
	
	def getChildWithDefault(self, path, request):
		if self.isAuthenticated(request) is True:
			return self.resource.getChildWithDefault(path, request)
		
		else:
			return self.unautorized(request)

class UnauthorizedResource(resource.Resource):
	def __init__(self, realm):
		resource.Resource.__init__(self)
		self.realm = realm
		self.errorpage = static.Data('<html><body>Access Denied.</body></html>', 'text/html')
		
	def render(self, request):	
		return self.errorpage.render(request)

from hashlib import md5 as md5_new
from crypt import crypt

DES_SALT = list('./0123456789' 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' 'abcdefghijklmnopqrstuvwxyz')
def getpwnam(name, pwfile=None):
	"""Return pasword database entry for the given user name.

	Example from the Python Library Reference.
	"""

	if not pwfile:
		pwfile = '/etc/passwd'

	f = open(pwfile)
	while 1:
		line = f.readline()
		if not line:
			f.close()
			raise KeyError, name
		entry = tuple(line.strip().split(':', 6))
		if entry[0] == name:
			f.close()
			return entry

def passcrypt(passwd, salt=None, method='des', magic='$1$'):
	"""Encrypt a string according to rules in crypt(3)."""
	if method.lower() == 'des':
		return crypt(passwd, salt)
	elif method.lower() == 'md5':
		return passcrypt_md5(passwd, salt, magic)
	elif method.lower() == 'clear':
		return passwd

def check_passwd(name, passwd, pwfile='/etc/passwd'):
	"""Validate given user, passwd pair against password database."""

	if not pwfile or type(pwfile) == type(''):
		getuser = lambda x, pwfile = pwfile: getpwnam(x, pwfile)[1]
	else:
		getuser = pwfile.get_passwd

	try:
		enc_passwd = getuser(name)
	except (KeyError, IOError):
		print "!!! EXCEPT"
		return False
	if not enc_passwd:
		"!!! NOT ENC_PASSWD"
		return False
	elif len(enc_passwd) >= 3 and enc_passwd[:3] == '$1$':
		salt = enc_passwd[3:enc_passwd.find('$', 3)]
		return enc_passwd == passcrypt(passwd, salt, 'md5')
	else:
		return enc_passwd == passcrypt(passwd, enc_passwd[:2])

def _to64(v, n):
	r = ''
	while (n - 1 >= 0):
		r = r + DES_SALT[v & 0x3F]
		v = v >> 6
		n = n - 1
	return r

def passcrypt_md5(passwd, salt=None, magic='$1$'):
	"""Encrypt passwd with MD5 algorithm."""

	if not salt:
		pass
	elif salt[:len(magic)] == magic:
		# remove magic from salt if present
		salt = salt[len(magic):]

	# salt only goes up to first '$'
	salt = salt.split('$')[0]
	# limit length of salt to 8
	salt = salt[:8]

	ctx = md5_new(passwd)
	ctx.update(magic)
	ctx.update(salt)

	ctx1 = md5_new(passwd)
	ctx1.update(salt)
	ctx1.update(passwd)

	final = ctx1.digest()

	for i in range(len(passwd), 0 , -16):
		if i > 16:
			ctx.update(final)
		else:
			ctx.update(final[:i])

	i = len(passwd)
	while i:
		if i & 1:
			ctx.update('\0')
		else:
			ctx.update(passwd[:1])
		i = i >> 1
	final = ctx.digest()

	for i in range(1000):
		ctx1 = md5_new()
		if i & 1:
			ctx1.update(passwd)
		else:
			ctx1.update(final)
		if i % 3: ctx1.update(salt)
		if i % 7: ctx1.update(passwd)
		if i & 1:
			ctx1.update(final)
		else:
			ctx1.update(passwd)
		final = ctx1.digest()

	rv = magic + salt + '$'
	final = map(ord, final)
	l = (final[0] << 16) + (final[6] << 8) + final[12]
	rv = rv + _to64(l, 4)
	l = (final[1] << 16) + (final[7] << 8) + final[13]
	rv = rv + _to64(l, 4)
	l = (final[2] << 16) + (final[8] << 8) + final[14]
	rv = rv + _to64(l, 4)
	l = (final[3] << 16) + (final[9] << 8) + final[15]
	rv = rv + _to64(l, 4)
	l = (final[4] << 16) + (final[10] << 8) + final[5]
	rv = rv + _to64(l, 4)
	l = final[11]
	rv = rv + _to64(l, 2)

	return rv

#### stuff for SSL Support
def makeSSLContext(myKey, trustedCA):
	 '''Returns an ssl Context Object
	@param myKey a pem formated key and certifcate with for my current host
			the other end of this connection must have the cert from the CA
			that signed this key
	@param trustedCA a pem formated certificat from a CA you trust
			you will only allow connections from clients signed by this CA
			and you will only allow connections to a server signed by this CA
	 '''

	 # our goal in here is to make a SSLContext object to pass to connectSSL
	 # or listenSSL

	 # Why these functioins... Not sure...
	 fd = open(myKey, 'r')
	 ss = fd.read()
	 theCert = ssl.PrivateCertificate.loadPEM(ss)
	 fd.close()
	 fd = open(trustedCA, 'r')
	 theCA = ssl.Certificate.loadPEM(fd.read())
	 fd.close()
	 #ctx = theCert.options(theCA)
	 ctx = theCert.options()

	 # Now the options you can set look like Standard OpenSSL Library options

	 # The SSL protocol to use, one of SSLv23_METHOD, SSLv2_METHOD,
	 # SSLv3_METHOD, TLSv1_METHOD. Defaults to TLSv1_METHOD.
	 ctx.method = ssl.SSL.TLSv1_METHOD

	 # If True, verify certificates received from the peer and fail
	 # the handshake if verification fails. Otherwise, allow anonymous
	 # sessions and sessions with certificates which fail validation.
	 ctx.verify = True

	 # Depth in certificate chain down to which to verify.
	 ctx.verifyDepth = 1

	 # If True, do not allow anonymous sessions.
	 ctx.requireCertification = True

	 # If True, do not re-verify the certificate on session resumption.
	 ctx.verifyOnce = True

	 # If True, generate a new key whenever ephemeral DH parameters are used
	 # to prevent small subgroup attacks.
	 ctx.enableSingleUseKeys = True

	 # If True, set a session ID on each context. This allows a shortened
	 # handshake to be used when a known client reconnects.
	 ctx.enableSessions = True

	 # If True, enable various non-spec protocol fixes for broken
	 # SSL implementations.
	 ctx.fixBrokenPeers = False

	 return ctx

global_session = None

def sessionstart(reason, session):
	global global_session
	global_session = session

def autostart(reason, **kwargs):
	if reason is True:
#		try:
		updateConfig()
		startWebserver(global_session)
#		except ImportError, e:
#			print "[Webinterface] twisted not available, not starting web services", e
	elif reason is False:
		stopWebserver(global_session)

def openconfig(session, **kwargs):
	session.openWithCallback(configCB, WebIfConfigScreen)

def configCB(result, session):
	if result is True:
		print "[WebIf] config changed"
		restartWebserver(session)
	else:
		print "[WebIf] config not changed"

def Plugins(**kwargs):
	return [PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=sessionstart),
			PluginDescriptor(where=[PluginDescriptor.WHERE_NETWORKCONFIG_READ], fnc=autostart),
			PluginDescriptor(name=_("Webinterface"), description=_("Configuration for the Webinterface"),
							where=[PluginDescriptor.WHERE_PLUGINMENU], icon="plugin.png", fnc=openconfig)]
