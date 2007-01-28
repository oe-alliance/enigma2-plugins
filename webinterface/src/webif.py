#
# OK, this is more than a proof of concept
# things to improve:
#  - nicer code
#  - screens need to be defined somehow else. 
#    I don't know how, yet. Probably each in an own file.
#  - more components, like the channellist
#  - better error handling
#  - use namespace parser

from Screens.Screen import Screen
from Tools.Import import my_import

# for our testscreen
from Screens.InfoBarGenerics import InfoBarServiceName, InfoBarEvent, InfoBarTuner

from Components.Sources.Clock import Clock
from Components.Sources.ServiceList import ServiceList
from WebComponents.Sources.Volume import Volume
from WebComponents.Sources.EPG import EPG
from WebComponents.Sources.Timer import Timer
from WebComponents.Sources.Movie import Movie
from WebComponents.Sources.Message import Message
from WebComponents.Sources.RequestData import RequestData
from Components.Sources.FrontendStatus import FrontendStatus

from Components.Converter.Converter import Converter

from Components.Element import Element

from xml.sax import make_parser
from xml.sax.handler import ContentHandler, feature_namespaces
from twisted.python import util
import sys
import time
 
# prototype of the new web frontend template system.

class WebScreen(Screen):
	def __init__(self, session,request):
		Screen.__init__(self, session)
		self.stand_alone = True
		self.request = request
# a test screen
class TestScreen(InfoBarServiceName, InfoBarEvent,InfoBarTuner, WebScreen):
	def __init__(self, session,request):
		WebScreen.__init__(self, session,request)
		InfoBarServiceName.__init__(self)
		InfoBarEvent.__init__(self)
		InfoBarTuner.__init__(self)
		self["CurrentTime"] = Clock()
#		self["TVSystem"] = Config(config.av.tvsystem)
#		self["OSDLanguage"] = Config(config.osd.language)
#		self["FirstRun"] = Config(config.misc.firstrun)
		from enigma import eServiceReference
		fav = eServiceReference('1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 195) || (type == 25) FROM BOUQUET "bouquets.tv" ORDER BY bouquet')
		self["ServiceList"] = ServiceList(fav, command_func = self.zapTo, validate_commands=False)
		self["ServiceListBrowse"] = ServiceList(fav, command_func = self.browseTo, validate_commands=False)
		self["Volume"] = Volume(session)
		self["EPGTITLE"] = EPG(session,func=EPG.TITLE)
		self["EPGSERVICE"] = EPG(session,func=EPG.SERVICE)
		self["EPGNOW"] = EPG(session,func=EPG.NOW)
		self["TimerList"] = Timer(session,func = Timer.LIST)
		self["TimerAddEventID"] = Timer(session,func = Timer.ADDBYID)
		self["TimerAdd"] = Timer(session,func = Timer.ADD)
		self["TimerDel"] = Timer(session,func = Timer.DEL)
		self["MovieList"] = Movie(session)
		self["Volume"] = Volume(session)
		self["Message"] = Message(session)

	def browseTo(self, reftobrowse):
		self["ServiceListBrowse"].root = reftobrowse

	def zapTo(self, reftozap):
		self.session.nav.playService(reftozap)

# TODO: (really.) put screens into own files.
class Streaming(WebScreen):
	def __init__(self, session,request):
		WebScreen.__init__(self, session,request)
		from Components.Sources.StreamService import StreamService
		self["StreamService"] = StreamService(self.session.nav)

class StreamingM3U(WebScreen):
	def __init__(self, session,request):
		WebScreen.__init__(self, session,request)
		from Components.Sources.StaticText import StaticText
		from Components.Sources.Config import Config
		from Components.config import config
		self["ref"] = StaticText()
		self["localip"] = RequestData(request,what=RequestData.HOST)

# implements the 'render'-call.
# this will act as a downstream_element, like a renderer.
class OneTimeElement(Element):
	def __init__(self, id):
		Element.__init__(self)
		self.source_id = id

	# CHECKME: is this ok performance-wise?
	def handleCommand(self, args):
		if self.source_id.find(",") >=0:
			paramlist = self.source_id.split(",")
			list={}
			for key in paramlist:
				arg = args.get(key, [])
				if len(arg) == 0:
					list[key] = None	
				elif len(arg) == 1:
					list[key] = "".join(arg)	
				elif len(arg) == 2:
					list[key] = arg[0]
			self.source.handleCommand(list)
		else:
			for c in args.get(self.source_id, []):
				self.source.handleCommand(c)
		
	def render(self, stream):
		t = self.source.getHTML(self.source_id)
		stream.write(t)

	def execBegin(self):
		pass
	
	def execEnd(self):
		pass
	
	def onShow(self):
		pass

	def onHide(self):
		pass
	
	def destroy(self):
		pass

class StreamingElement(OneTimeElement):
	def __init__(self, id):
		OneTimeElement.__init__(self, id)
		self.stream = None

	def changed(self, what):
		if self.stream:
			self.render(self.stream)

	def setStream(self, stream):
		self.stream = stream

# a to-be-filled list item
class ListItem:
	def __init__(self, name, filternum):
		self.name = name
		self.filternum = filternum
	
class TextToHTML(Converter):
	def __init__(self, arg):
		Converter.__init__(self, arg)

	def getHTML(self, id):
		return self.source.text # encode & etc. here!

# a null-output. Useful if you only want to issue a command.
class Null(Converter):
	def __init__(self, arg):
		Converter.__init__(self, arg)

	def getHTML(self, id):
		return ""

class JavascriptUpdate(Converter):
	def __init__(self, arg):
		Converter.__init__(self, arg)

	def getHTML(self, id):
		# 3c5x9, added parent. , this is because the ie loads this in a iframe. an the set is in index.html.xml
		#		 all other will replace this in JS
		return '<script>parent.set("%s", "%s");</script>\n'%(id, self.source.text.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"'))

# the performant 'listfiller'-engine (plfe)
class ListFiller(Converter):
	def __init__(self, arg):
		Converter.__init__(self, arg)

	def getText(self):
		l = self.source.list
		lut = self.source.lut
		conv_args = self.converter_arguments

		# now build a ["string", 1, "string", 2]-styled list, with indices into the
		# list to avoid lookup of item name for each entry
		lutlist = [ isinstance(element, basestring) and (element, None) or (lut[element.name], element.filternum) for element in conv_args ]

		# now, for the huge list, do:
		strlist = [ ]
		append = strlist.append
		for item in l:
			for (element, filternum) in lutlist:
				if not filternum:
					append(element)
				elif filternum == 2:
					append(str(item[element]).replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"'))
				elif filternum == 3:
					append(str(item[element]).replace("&", "&amp;").replace("<", "&lt;").replace('"', '&quot;').replace(">", "&gt;"))
				elif filternum == 4:
					append(str(item[element]).replace("%", "%25").replace("+", "%2B").replace('&', '%26').replace('?', '%3f').replace(' ', '+'))
				else:
					append(str(item[element]))
		# (this will be done in c++ later!)
		return ''.join(strlist)

	text = property(getText)

class webifHandler(ContentHandler):
	def __init__(self, session,request):
		self.res = [ ]
		self.mode = 0
		self.screen = None
		self.session = session
		self.screens = [ ]
		self.request = request
	
	def startElement(self, name, attrs):
		if name == "e2:screen":
			self.screen = eval(attrs["name"])(self.session,self.request) # fixme
			self.screens.append(self.screen)
			return
	
		if name[:3] == "e2:":
			self.mode += 1

		tag = [' %s="%s"' %(key,val) for (key, val) in attrs.items()]
		tag.insert(0, name)
		tag.insert(0, '<')
		tag.append('>')
		tag = ''.join(tag)#.encode('utf-8')

		if self.mode == 0:
			self.res.append(tag)
		elif self.mode == 1: # expect "<e2:element>"
			assert name == "e2:element", "found %s instead of e2:element" % name
			source = attrs["source"]
			self.source_id = str(attrs.get("id", source))
			self.source = self.screen[source]
			self.is_streaming = "streaming" in attrs
		elif self.mode == 2: # expect "<e2:convert>"
			if name[:3] == "e2:":
				assert name == "e2:convert"
				
				ctype = attrs["type"]
				
					# TODO: we need something better here
				if ctype[:4] == "web:": # for now
					self.converter = eval(ctype[4:])
				else:
					try:
						self.converter = my_import('.'.join(["Components", "Converter", ctype])).__dict__.get(ctype)
					except ImportError:
						self.converter = my_import('.'.join(["Plugins", "Extensions", "WebInterface", "WebComponents", "Converter", ctype])).__dict__.get(ctype)
				self.sub = [ ]
			else:
				self.sub.append(tag)
		elif self.mode == 3:
			assert name == "e2:item", "found %s instead of e2:item!" % name
			assert "name" in attrs, "e2:item must have a name= attribute!"
			filter = {"": 1, "javascript_escape": 2, "xml": 3, "uri": 4}[attrs.get("filter", "")]
			self.sub.append(ListItem(attrs["name"], filter))

	def endElement(self, name):
		if name == "e2:screen":
			self.screen = None
			return

		tag = "</" + name + ">"
		if self.mode == 0:
			self.res.append(tag)
		elif self.mode == 2 and name[:3] != "e2:":
			self.sub.append(tag)
		elif self.mode == 2: # closed 'convert' -> sub
			if len(self.sub) == 1:
				self.sub = self.sub[0]
			c = self.converter(self.sub)
			c.connect(self.source)
			self.source = c
			del self.sub
		elif self.mode == 1: # closed 'element'
			# instatiate either a StreamingElement or a OneTimeElement, depending on what's required.
			if not self.is_streaming:
				c = OneTimeElement(self.source_id)
			else:
				c = StreamingElement(self.source_id)
			
			c.connect(self.source)
			self.res.append(c)
			self.screen.renderer.append(c)
			del self.source

		if name[:3] == "e2:":
			self.mode -= 1

	def processingInstruction(self, target, data):
		self.res.append('<?' + target + ' ' + data + '>')
	
	def characters(self, ch):
		ch = ch.encode('utf-8')
		if self.mode == 0:
			self.res.append(ch)
		elif self.mode == 2:
			self.sub.append(ch)
	
	def startEntity(self, name):
		self.res.append('&' + name + ';');

	def execBegin(self):
		for screen in self.screens:
			screen.execBegin()

	def cleanup(self):
		print "screen cleanup!"
		for screen in self.screens:
			screen.execEnd()
			screen.doClose()
		self.screens = [ ]

def renderPage(stream, path, req, session):
	
	# read in the template, create required screens
	# we don't have persistense yet.
	# if we had, this first part would only be done once.
	handler = webifHandler(session,req)
	parser = make_parser()
	parser.setFeature(feature_namespaces, 0)
	parser.setContentHandler(handler)
	parser.parse(open(util.sibpath(__file__, path)))
	
	# by default, we have non-streaming pages
	finish = True
	
	# first, apply "commands" (aka. URL argument)
	for x in handler.res:
		if isinstance(x, Element):
			x.handleCommand(req.args)

	handler.execBegin()

	# now, we have a list with static texts mixed
	# with non-static Elements.
	# flatten this list, write into the stream.
	for x in handler.res:
		if isinstance(x, Element):
			if isinstance(x, StreamingElement):
				finish = False
				x.setStream(stream)
			x.render(stream)
		else:
			stream.write(str(x))

	def ping(s):
		from twisted.internet import reactor
		s.write("\n");
		reactor.callLater(3, ping, s)

	# if we met a "StreamingElement", there is at least one
	# element which wants to output data more than once,
	# i.e. on host-originated changes.
	# in this case, don't finish yet, don't cleanup yet,
	# but instead do that when the client disconnects.
	if finish:
		handler.cleanup()
		stream.finish()
	else:
		# ok.
		# you *need* something which constantly sends something in a regular interval,
		# in order to detect disconnected clients.
		# i agree that this "ping" sucks terrible, so better be sure to have something 
		# similar. A "CurrentTime" is fine. Or anything that creates *some* output.
		ping(stream)
		stream.closed_callback = lambda: handler.cleanup()
