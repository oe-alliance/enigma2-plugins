from twisted.internet import reactor
from twisted.web import client

valid_types = ("MP3","PLS") #list of playable mediatypes

def getPage(url, contextFactory=None, *args, **kwargs):
	if hasattr(client, '_parse'):
		scheme, host, port, path = _parse(url)
	else:
			from twisted.web.client import _URI
			uri = _URI.fromBytes(url)
			scheme = uri.scheme
			host = uri.host
			port = uri.port
			path = uri.path
	factory = LimitedHTTPClientFactory(url, *args, **kwargs)
	if scheme == 'https':
		from twisted.internet import ssl 
		if contextFactory is None:
			contextFactory = ssl.ClientContextFactory()
		reactor.connectSSL(host, port, factory, contextFactory)
	else:
		reactor.connectTCP(host, port, factory)
	return factory.deferred

class LimitedHTTPClientFactory(HTTPClientFactory):

	LIMIT = 1024

	protocol = HTTPPageDownloader

	def __init__(self, *args, **kwargs):
		HTTPClientFactory.__init__(self, *args, **kwargs)
		self.curlength = 0
		self.buf = ""

	def buildProtocol(self, addr):
		self.p = HTTPClientFactory.buildProtocol(self, addr)
		return self.p

	def pageStart(self, p):
		pass

	def pagePart(self, d):
		if self.status == '200':
			self.curlength += len(d)
			if self.curlength >= self.LIMIT:
				print "[LimitedHTTPClientFactory] reached limit"
				# XXX: timing out here is pretty hackish imo
				self.p.timeout()
				return
		self.buf += d

	def pageEnd(self):
		if self.waiting:
			self.waiting = 0
			self.deferred.callback(self.buf)

class StreamInterface:
    def __init__(self,session,cbListLoaded=None):
        self.session = session
        self.cbListLoaded = cbListLoaded

        self.list= [] # contains the streams in this iface

    def getList(self):
        #loads a list auf Streams into self.list
        pass

    def getMenuItems(self,selectedStream,generic=False):
        # this return a list of MenuEntries of actions of this iterface
        # list=(("item1",func1),("item2",func2), ... )
        #
        # generic=True indicates, that items of the returned list are services
        # in any context (like saving a stream to the favorites)
        return []

    def OnListLoaded(self):
        # called from the interface, if list was loaded
        if self.cbListLoaded is not None:
            self.cbListLoaded(self.list)

###############################################################################
class Stream:
    isfavorite = False
    def __init__(self,name,description,url,type="mp3"):
        self.name = name
        self.description = description
        self.url = url
        self.type=type
    def getName(self):
        return self.name
    def getDescription(self):
        return self.description
    def setName(self,name):
        self.name = name
    def setDescription(self,description):
        self.description = description
    def setURL(self,url):
        self.url = url
    def getURL(self, callback):
    	self.callback = callback
        if self.type.lower() == "pls":
        	self.getPLSContent()
        else:
            self.callback(self.url)

    def getPLSContent(self):
        print "loading PLS of stream ",self.name,self.url
    	getPage(self.url).addCallback(self._gotPLSContent).addErrback(self._errorPLSContent)

    def _gotPLSContent(self, lines):
		if lines.startswith("ICY "):
			print "[NETcaster] PLS expected, but got ICY stream"
			self.type = "mp3"
			self.callback(self.url)
		else:
			for line in lines.split('\n'):
			    if line.startswith("File"):
			        url = line.split("=")[1].rstrip().strip()
			        self.callback(url)
			        break
			    print "Skipping:", line

    def _errorPLSContent(self, data):
        print "[NETcaster] _errorPLSContent", data
        print "[NETcaster] _errorPLSContent let's assume it's a stream"
        self.type = "mp3"
        self.callback(self.url)

    def setFavorite(self,TrueFalse):
        self.isfavorite = TrueFalse
    def isFavorite(self):
        return self.isfavorite
    def setType(self,type):
        self.type=type
    def getType(self):
        return self.type

