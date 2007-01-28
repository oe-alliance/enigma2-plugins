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
config.plugins.Webinterface.enable = ConfigYesNo(default = True)
config.plugins.Webinterface.port = ConfigInteger(80,limits = (1, 999))
config.plugins.Webinterface.includehdd = ConfigYesNo(default = False)
config.plugins.Webinterface.useauth = ConfigYesNo(default = False) # False, because a std. images hasnt a rootpasswd set and so no login. and a login with a empty pwd makes no sense

sessions = [ ]

"""
	define all files in /web to send no  XML-HTTP-Headers here
	all files not listed here will get an Content-Type: application/xhtml+xml charset: UTF-8
"""
files_to_send_normal_http_headers = ['stream.m3u.xml',] 
 
"""
 set DEBUG to True, if twisted should write logoutput to a file.
 in normal console output, twisted will print only the first Traceback.
 is this a bug in twisted or a conflict with enigma2?
 with this option enabled, twisted will print all TB to the logfile
 use tail -f <file> to view this log
"""
			
DEBUG = True
DEBUGFILE= "/tmp/twisted.log"

from twisted.cred.portal import Portal
from twisted.cred import checkers
from twisted.web2.auth import digest, basic, wrapper
from zope.interface import Interface, implements
from twisted.cred import portal
from twisted.cred import credentials, error
from twisted.internet import defer
from zope import interface


def stopWebserver():
	reactor.disconnectAll()

def restartWebserver():
	stopWebserver()
	startWebserver()

def startWebserver():
	if config.plugins.Webinterface.enable.value is not True:
		print "not starting Werbinterface"
		return False
	if DEBUG:
		print "start twisted logfile, writing to %s" % DEBUGFILE 
		import sys
		startLogging(open(DEBUGFILE,'w'))

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
				if self.path.split("/")[-1] in files_to_send_normal_http_headers:
					return http.Response(responsecode.OK,stream=s)
				else:
					return http.Response(responsecode.OK,{'Content-type': http_headers.MimeType('application', 'xhtml+xml', (('charset', 'UTF-8'),))},stream=s)
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
		child_web = ScreenPage(util.sibpath(__file__, "web")) # "/web/*"
		child_webdata = static.File(util.sibpath(__file__, "web-data")) # FIXME: web-data appears as webdata

		def render(self, req):
			fp = open(util.sibpath(__file__, "web-data")+"/index.html")
			s = fp.read()
			fp.close()
			return http.Response(responsecode.OK, {'Content-type': http_headers.MimeType('text', 'html')},stream=s)

	toplevel = Toplevel()
	if config.plugins.Webinterface.includehdd.value:
		toplevel.putChild("hdd",static.File("/hdd"))
	
	if config.plugins.Webinterface.useauth.value is False:
		site = server.Site(toplevel)
	else:
		portal = Portal(HTTPAuthRealm())
		portal.registerChecker(PasswordDatabase())
		root = ModifiedHTTPAuthResource(toplevel,(basic.BasicCredentialFactory('DM7025'),),portal, (IHTTPUser,))
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
		except ImportError,e:
			print "[WebIf] twisted not available, not starting web services",e
			
def openconfig(session, **kwargs):
	session.openWithCallback(configCB,WebIfConfig.WebIfConfigScreen)

def configCB(result):
	if result is True:
		print "[WebIf] config changed"
		restartWebserver()
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
    interface.implements(checkers.ICredentialsChecker)
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
	implements(portal.IRealm)
	def requestAvatar(self, avatarId, mind, *interfaces):
		if IHTTPUser in interfaces:
			return IHTTPUser, HTTPUser()
		raise NotImplementedError("Only IHTTPUser interface is supported")

	
import md5,time,string,crypt
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
	    if not salt:
	    	salt = str(whrandom.choice(DES_SALT)) + str(whrandom.choice(DES_SALT))
	    return crypt.crypt(passwd, salt)
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
        salt = enc_passwd[3:string.find(enc_passwd, '$', 3)]
        return enc_passwd == passcrypt(passwd, salt=salt, method='md5')
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
	salt = repr(int(time.time()))[-8:]
    elif salt[:len(magic)] == magic:
        # remove magic from salt if present
        salt = salt[len(magic):]

    # salt only goes up to first '$'
    salt = string.split(salt, '$')[0]
    # limit length of salt to 8
    salt = salt[:8]

    ctx = md5.new(passwd)
    ctx.update(magic)
    ctx.update(salt)
    
    ctx1 = md5.new(passwd)
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
	ctx1 = md5.new()
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


