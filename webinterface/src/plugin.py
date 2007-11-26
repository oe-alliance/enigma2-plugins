Version = '$Header$';
__version__ = "Beta 0.98.5"
from Plugins.Plugin import PluginDescriptor
from Components.config import config, ConfigSubsection, ConfigInteger,ConfigYesNo,ConfigText
from Components.Network import Network

from twisted.internet import reactor, defer
from twisted.web2 import server, channel, http
from twisted.web2.auth import digest, basic, wrapper
#from twisted.python import util
from twisted.python.log import startLogging
from twisted.cred.portal import Portal, IRealm
from twisted.cred import checkers, credentials, error
from zope.interface import Interface, implements

from WebIfConfig import WebIfConfigScreen

from WebChilds.Toplevel import Toplevel

config.plugins.Webinterface = ConfigSubsection()
config.plugins.Webinterface.enable = ConfigYesNo(default = True)
config.plugins.Webinterface.port = ConfigInteger(80,limits = (1, 65536))
config.plugins.Webinterface.includehdd = ConfigYesNo(default = False)
config.plugins.Webinterface.useauth = ConfigYesNo(default = False) # False, because a std. images hasnt a rootpasswd set and so no login. and a login with a empty pwd makes no sense
config.plugins.Webinterface.autowritetimer = ConfigYesNo(default = False)
config.plugins.Webinterface.loadmovielength = ConfigYesNo(default = False)
config.plugins.Webinterface.version = ConfigText(__version__) # used to make the versioninfo accessible enigma2-wide, not confgurable in GUI. 


"""
 set DEBUG to True, if twisted should write logoutput to a file.
 in normal console output, twisted will print only the first Traceback.
 is this a bug in twisted or a conflict with enigma2?
 with this option enabled, twisted will print all TB to the logfile
 use tail -f <file> to view this log
"""

# PLEASE DONT ENABLE LOGGING BY DEFAULT (OR COMMIT TO PLUGIN CVS)
# AND DONT ADD CONFIG OPTIONS WHICH HELPS NORMAL USERS TO ENABLE
# THIS KIND OF LOGGING !!!!!!!!!!!!! 
# Twisted logging can't handle UTF8 correct,
# and enigma2 internal completely use UTF8 (for debug messages too)             
# so the twisted logging code self generates frequently blue screens 
# at various places in enigma2(not only in Webif) and the reason 
# of this crashes is NOT visible in the normal enigma2 crashlogs 
# We have spent much time into debugging this		Ghost 2007/11/15

DEBUG_TO_FILE=False

DEBUGFILE= "/tmp/twisted.log"

global running_defered,waiting_shutdown
running_defered = []
waiting_shutdown = 0

class Closer:
	counter = 0
	def __init__(self,session, callback):
		self.callback = callback
		self.session = session
		
	def stop(self):
		global running_defered
		for d in running_defered:
			print "[WebIf] STOPPING reactor on interface ",d.interface," with port",d.port
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
	try:
		# variables, that are needed in the process
		session.mediaplayer = None
		session.messageboxanswer = None
		
		if config.plugins.Webinterface.enable.value is not True:
			print "not starting Werbinterface"
			return False
		if DEBUG_TO_FILE:
			print "start twisted logfile, writing to %s" % DEBUGFILE 
			startLogging(open(DEBUGFILE,'w'))
	
		toplevel = Toplevel(session)
		if config.plugins.Webinterface.useauth.value is False:
			site = server.Site(toplevel)
		else:
			portal = Portal(HTTPAuthRealm())
			portal.registerChecker(PasswordDatabase())
			root = ModifiedHTTPAuthResource(toplevel,(basic.BasicCredentialFactory('DM7025'),),portal, (IHTTPUser,))
			site = server.Site(root)
		
		# here we start the Toplevel without any username or password
		# this allows access to all request over the iface 127.0.0.1 without any auth
		localsite = server.Site(toplevel)
		d = reactor.listenTCP(config.plugins.Webinterface.port.value, channel.HTTPFactory(localsite),interface='127.0.0.1')
		running_defered.append(d)
		# and here we make the Toplevel public to our external ifaces
		# it depends on the config, if this is with auth support
		# keep in mind, if we have a second external ip (like a wlan device), we have to do it in the same way for this iface too
		nw = Network()
		for adaptername in nw.ifaces:
			extip = nw.ifaces[adaptername]['ip']
			if nw.ifaces[adaptername]['up'] is True:
				extip = "%i.%i.%i.%i"%(extip[0],extip[1],extip[2],extip[3])
				print "[WebIf] starting Webinterface on port %s on interface %s with address %s"%(str(config.plugins.Webinterface.port.value),adaptername,extip)
				try:
					d = reactor.listenTCP(config.plugins.Webinterface.port.value, channel.HTTPFactory(site),interface=extip)
					running_defered.append(d)
				except Exception,e:
					print "[WebIf] Error starting Webinterface on port %s on interface %s with address %s,because \n%s"%(str(config.plugins.Webinterface.port.value),adaptername,extip,e)
			else:
				print "[WebIf] found configured interface %s, but it is not running. so not starting a server on it ..." % adaptername
	except Exception,e:
		print "\n\nSomething went wrong on starting the webif. May the following Line can help to find the error:\n",e,"\n\n"
####		
def autostart(reason, **kwargs):
	if "session" in kwargs:
		try:
			startWebserver(kwargs["session"])
		except ImportError,e:
			print "[WebIf] twisted not available, not starting web services",e
			
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
	
	
class ModifiedHTTPAuthResource(wrapper.HTTPAuthResource):
	"""
		set it only to True, if you have a patched wrapper.py
		see http://twistedmatrix.com/trac/ticket/2041
		so, the solution for us is to make a new class an override ne faulty func
	"""

	def locateChild(self, req, seg):
		return self.authenticate(req), seg
	
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

class HTTPAuthRealm(object):
	implements(IRealm)
	def requestAvatar(self, avatarId, mind, *interfaces):
		if IHTTPUser in interfaces:
			return IHTTPUser, HTTPUser()
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


