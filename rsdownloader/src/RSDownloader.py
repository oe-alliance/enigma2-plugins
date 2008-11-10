##
## RS Downloader
## by AliAbdul
##
from base64 import encodestring
from twisted.internet import reactor
from twisted.web.client import HTTPDownloader
from urlparse import urlparse, urlunparse
import urllib2, re

##############################################################################

def _parse(url):
	url = url.strip()
	parsed = urlparse(url)
	scheme = parsed[0]
	path = urlunparse(('','') + parsed[2:])
	
	host, port = parsed[1], 80
	
	if '@' in host:
		username, host = host.split('@')
		if ':' in username:
			username, password = username.split(':')
		else:
			password = ""
	else:
		username = ""
		password = ""
	
	if ':' in host:
		host, port = host.split(':')
		port = int(port)
	
	if path == "":
		path = "/"
	
	return scheme, host, port, path, username, password

def downloadPage(url, file, contextFactory=None, *args, **kwargs):
	scheme, host, port, path, username, password = _parse(url)
	
	if username and password:
		url = scheme + '://' + host + ':' + str(port) + path
		basicAuth = encodestring("%s:%s" % (username, password))
		authHeader = "Basic " + basicAuth.strip()
		AuthHeaders = {"Authorization": authHeader}
		
		if kwargs.has_key("headers"):
			kwargs["headers"].update(AuthHeaders)
		else:
			kwargs["headers"] = AuthHeaders
	
	factory = HTTPDownloader(url, file, *args, **kwargs)
	reactor.connectTCP(host, port, factory)
	return factory.deferred

##############################################################################

def GET(url):
	try:
		data = urllib2.urlopen(url)
		return data.read()
	except:
		return ""
   
def POST(url, data):
	try:
		return urllib2.urlopen(url, data).read()
	except:
		return ""

def matchGet(rex, string):
	ret = False
	
	try:
		match = re.search(rex, string)
		if match:
			if len(match.groups()) == 0:
				return string[match.span()[0]:match.span()[1]]
			if len(match.groups()) == 1:
				return match.groups()[0]
		else:
			return match.groups()
	except:
		pass
	
	return ret

