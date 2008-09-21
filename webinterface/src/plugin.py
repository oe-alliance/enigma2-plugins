Version = '$Header$';
from Plugins.Plugin import PluginDescriptor
from Components.config import config
from Screens.MessageBox import MessageBox
from WebIfConfig import WebIfConfigScreen
from WebChilds.Toplevel import Toplevel
from twisted.internet import reactor, defer
from twisted.internet.error import CannotListenError
from twisted.web2 import server, channel, http
from twisted.web2.auth import digest, basic, wrapper
from twisted.python.log import startLogging
from twisted.cred.portal import Portal, IRealm
from twisted.cred import checkers, credentials, error
from zope.interface import Interface, implements
from socket import gethostname as socket_gethostname
from OpenSSL import SSL
from twisted.internet import reactor, defer, ssl

DEBUG_TO_FILE=False # PLEASE DONT ENABLE LOGGING BY DEFAULT (OR COMMIT TO PLUGIN CVS)

DEBUGFILE= "/tmp/twisted.log"

global running_defered,waiting_shutdown
running_defered = []
waiting_shutdown = 0
server.VERSION = "Enigma2 WebInterface Server $Revision$".replace("$Revi","").replace("sion: ","").replace("$","")

class Closer:
	counter = 0
	def __init__(self,session, callback):
		self.callback = callback
		self.session = session
		
	def stop(self):
		global running_defered
		for d in running_defered:
			print "[Webinterface] stopping interface on ",d.interface," with port",d.port
			x = d.stopListening()
			try:
				x.addCallback(self.isDown)
				self.counter +=1
			except AttributeError:
				pass
		running_defered = []
		if self.counter <1:
			self.callback(self.session)
		
	def isDown(self,s):
		self.counter-=1
		if self.counter <1:
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
	if len(running_defered) >0:
		Closer(session,startWebserver).stop()
	else:
		startWebserver(session)

def startWebserver(session):
	global running_defered
	session.mediaplayer = None
	session.messageboxanswer = None
	
	if config.plugins.Webinterface.enable.value is not True:
		print "not starting Werbinterface"
		return False
	if DEBUG_TO_FILE:
		print "start twisted logfile, writing to %s" % DEBUGFILE 
		startLogging(open(DEBUGFILE,'w'))
	
	for i in range(0, config.plugins.Webinterface.interfacecount.value):
		c = config.plugins.Webinterface.interfaces[i]
		if c.disabled.value is False:
			startServerInstance(session,c.adress.value,c.port.value,c.useauth.value,c.usessl.value)
		else:
			print "[Webinterface] not starting disabled interface on %s:%i"%(c.adress.value,c.port.value)
			
def startServerInstance(session,ipadress,port,useauth=False,usessl=False):
	try:
		toplevel = Toplevel(session)
		if useauth:
			portal = Portal(HTTPAuthRealm())
			portal.registerChecker(PasswordDatabase())
			root = wrapper.HTTPAuthResource(toplevel,(basic.BasicCredentialFactory(socket_gethostname()),),portal, (IHTTPUser,))
			site = server.Site(root)	
		else:
			site = server.Site(toplevel)
		try:
			if usessl:				
				ctx = ssl.DefaultOpenSSLContextFactory('/etc/enigma2/server.pem','/etc/enigma2/cacert.pem',sslmethod=SSL.SSLv23_METHOD)
				d = reactor.listenSSL(port, channel.HTTPFactory(site),ctx,interface=ipadress)
			else:
				d = reactor.listenTCP(port, channel.HTTPFactory(site),interface=ipadress)
			running_defered.append(d)
			print "[Webinterface] started on %s:%i"%(ipadress,port),"auth=",useauth,"ssl=",usessl
		except CannotListenError, e:
			print "[Webinterface] Could not Listen on %s:%i!"%(ipadress,port)
			session.open(MessageBox,'Could not Listen on %s:%i!\n\n%s'%(ipadress,port,str(e)), MessageBox.TYPE_ERROR)
	except Exception,e:
		print "[Webinterface] starting FAILED on %s:%i!"%(ipadress,port),e
		session.open(MessageBox,'starting FAILED on %s:%i!\n\n%s'%(ipadress,port,str(e)), MessageBox.TYPE_ERROR)

def autostart(reason, **kwargs):
	if "session" in kwargs:
		try:
			startWebserver(kwargs["session"])
		except ImportError,e:
			print "[Webinterface] twisted not available, not starting web services",e
			
def openconfig(session, **kwargs):
	session.openWithCallback(configCB,WebIfConfigScreen)

def configCB(result,session):
	if result is True:
		print "[WebIf] config changed"
		restartWebserver(session)
	else:
		print "[WebIf] config not changed"
		

def Plugins(**kwargs):
	return [PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc = autostart),
		    PluginDescriptor(name=_("Webinterface"), description=_("Configuration for the Webinterface"),where = [PluginDescriptor.WHERE_PLUGINMENU], icon="plugin.png",fnc = openconfig)]
	
	
	
class PasswordDatabase:
    """
    	this checks webiflogins agains /etc/passwd
    """
    passwordfile = "/etc/passwd"
    implements(checkers.ICredentialsChecker)
    credentialInterfaces = (credentials.IUsernamePassword,credentials.IUsernameHashedPassword)

    def _cbPasswordMatch(self, matched, username):
        if matched:
            return username
        else:
            return failure.Failure(error.UnauthorizedLogin())

    def requestAvatarId(self, credentials):	
    	if check_passwd(credentials.username,credentials.password,self.passwordfile) is True:
    		return defer.maybeDeferred(credentials.checkPassword,credentials.password).addCallback(self._cbPasswordMatch, str(credentials.username))
    	else:
    		return defer.fail(error.UnauthorizedLogin())

class IHTTPUser(Interface):
	pass

class HTTPUser(object):
	implements(IHTTPUser)
	username = None
	def __init__(self,username):
		self.username = username

class HTTPAuthRealm(object):
	implements(IRealm)
	def requestAvatar(self, avatarId, mind, *interfaces):
		if IHTTPUser in interfaces:
			return IHTTPUser, HTTPUser(avatarId)
		raise NotImplementedError("Only IHTTPUser interface is supported")


from string import find, split	
from md5 import new as md5_new
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

def check_passwd(name, passwd, pwfile=None):
    """Validate given user, passwd pair against password database."""
    
    if not pwfile or type(pwfile) == type(''):
        getuser = lambda x,pwfile=pwfile: getpwnam(x,pwfile)[1]
    else:
        getuser = pwfile.get_passwd

    try:
        enc_passwd = getuser(name)
    except (KeyError, IOError):
        return 0
    if not enc_passwd:
        return 0
    elif len(enc_passwd) >= 3 and enc_passwd[:3] == '$1$':
        salt = enc_passwd[3:find(enc_passwd, '$', 3)]
        return enc_passwd == passcrypt(passwd, salt, 'md5')
       
    else:
        return enc_passwd == passcrypt(passwd, enc_passwd[:2])

def _to64(v, n):
    r = ''
    while (n-1 >= 0):
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
    salt = split(salt, '$')[0]
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
def makeSSLContext(myKey,trustedCA):
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
     fd = open(myKey,'r')
     ss = fd.read()
     theCert = ssl.PrivateCertificate.loadPEM(ss)
     fd.close()
     fd = open(trustedCA,'r')
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



