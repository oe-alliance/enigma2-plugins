Version = '$Header$';

# OK, this is more than a proof of concept
# things to improve:
#  - nicer code
#  - screens need to be defined somehow else. 
#    I don't know how, yet. Probably each in an own file.
#  - more components, like the channellist
#  - better error handling
#  - use namespace parser
from enigma import eServiceReference

from Screens.Screen import Screen
from Tools.Import import my_import

from Screens.InfoBarGenerics import InfoBarServiceName, InfoBarEvent, InfoBarTuner

from Components.Sources.Clock import Clock
from Components.Sources.ServiceList import ServiceList

from WebComponents.Sources.ServiceListRecursive import ServiceListRecursive
from WebComponents.Sources.Volume import Volume
from WebComponents.Sources.EPG import EPG
from WebComponents.Sources.Timer import Timer
from WebComponents.Sources.Movie import Movie
from WebComponents.Sources.Message import Message
from WebComponents.Sources.PowerState import PowerState
from WebComponents.Sources.RemoteControl import RemoteControl
from WebComponents.Sources.Settings import Settings
from WebComponents.Sources.SubServices import SubServices
from WebComponents.Sources.ParentControl import ParentControl
from WebComponents.Sources.About import About
from WebComponents.Sources.RequestData import RequestData
from WebComponents.Sources.AudioTracks import AudioTracks
from WebComponents.Sources.WAPfunctions import WAPfunctions

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
	def __init__(self, session, request):
		Screen.__init__(self, session)
		self.stand_alone = True
		self.request = request
		self.instance = None
		
class DummyWebScreen(WebScreen):
	#use it, if you dont need any source, just to can do a static file with an xml-file
	def __init__(self, session,request):
		WebScreen.__init__(self, session,request)

class UpdateWebScreen(InfoBarServiceName, InfoBarEvent,InfoBarTuner,WebScreen):
	def __init__(self, session,request):
		WebScreen.__init__(self, session,request)
		InfoBarServiceName.__init__(self)
		InfoBarEvent.__init__(self)
		InfoBarTuner.__init__(self)
		self["CurrentTime"] = Clock()
		fav = eServiceReference('1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 195) || (type == 25) FROM BOUQUET "bouquets.tv" ORDER BY bouquet')
		#CurrentService
		#Event_Now
		#Event_Next
		#FrontendStatus
		
class MessageWebScreen(WebScreen):
	def __init__(self, session,request):
		WebScreen.__init__(self, session,request)
		self["Message"] = Message(session)

class AudioWebScreen(WebScreen):
	def __init__(self, session,request):
		WebScreen.__init__(self, session,request)
		self["AudioTracks"] = AudioTracks(session)		

class AboutWebScreen(WebScreen):
	def __init__(self, session,request):
		WebScreen.__init__(self, session,request)
		self["About"] = About(session)
		
class VolumeWebScreen(WebScreen):
	def __init__(self, session,request):
		WebScreen.__init__(self, session,request)
		self["Volume"] = Volume(session)

class SettingsWebScreen(WebScreen):
	def __init__(self, session,request):
		WebScreen.__init__(self, session,request)
		self["Settings"] = Settings(session)

class SubServiceWebScreen(WebScreen):
	def __init__(self, session,request):
		WebScreen.__init__(self, session,request)
		self["SubServices"] = SubServices(session)

class ServiceWebScreen(WebScreen):
	def __init__(self, session,request):
		WebScreen.__init__(self, session,request)
		fav = eServiceReference('1:7:1:0:0:0:0:0:0:0:(type == 1) || (type == 17) || (type == 195) || (type == 25) FROM BOUQUET "bouquets.tv" ORDER BY bouquet')
		self["SwitchService"] = ServiceList(fav, command_func = self.zapTo, validate_commands=False)
		self["ServiceList"] = ServiceList(fav, command_func = self.getServiceList, validate_commands=False)
		self["ServiceListRecursive"] = ServiceListRecursive(session, func=ServiceListRecursive.FETCH)

	def getServiceList(self, sRef):
		self["ServiceList"].root = sRef

	def zapTo(self, reftozap):
		from Components.config import config
		pc = config.ParentalControl.configured.value
		if pc:
			config.ParentalControl.configured.value = False
		self.session.nav.playService(reftozap)
		if pc:
			config.ParentalControl.configured.value = pc
		"""
		switching config.ParentalControl.configured.value
		ugly, but necessary :(
		"""

class EPGWebScreen(WebScreen):
	def __init__(self, session,request):
		WebScreen.__init__(self, session,request)
		self["EPGTITLE"] = EPG(session,func=EPG.TITLE)
		self["EPGSERVICE"] = EPG(session,func=EPG.SERVICE)
		self["EPGNOW"] = EPG(session,func=EPG.NOW)

class MovieWebScreen(WebScreen):
	def __init__(self, session,request):
		WebScreen.__init__(self, session,request)
		from Components.MovieList import MovieList
		from Tools.Directories import resolveFilename,SCOPE_HDD
		movielist = MovieList(eServiceReference("2:0:1:0:0:0:0:0:0:0:" + resolveFilename(SCOPE_HDD)))
		self["MovieList"] = Movie(session,movielist,func = Movie.LIST)
		self["MovieFileDel"] = Movie(session,movielist,func = Movie.DEL)
		self["MovieTags"] = Movie(session,movielist,func = Movie.TAGS)

		
class TimerWebScreen(WebScreen):
	def __init__(self, session,request):
		WebScreen.__init__(self, session,request)
		self["TimerList"] = Timer(session,func = Timer.LIST)
		self["TimerAddEventID"] = Timer(session,func = Timer.ADDBYID)
		self["TimerAdd"] = Timer(session,func = Timer.ADD)
		self["TimerDel"] = Timer(session,func = Timer.DEL)
		self["TimerChange"] = Timer(session,func = Timer.CHANGE)
		self["TimerListWrite"] = Timer(session,func = Timer.WRITE)
		self["TVBrowser"] = Timer(session,func = Timer.TVBROWSER)
		self["RecordNow"] = Timer(session,func = Timer.RECNOW)

class RemoteWebScreen(WebScreen):
	def __init__(self, session,request):
		WebScreen.__init__(self, session,request)
		self["RemoteControl"] = RemoteControl(session)

class PowerWebScreen(WebScreen):
	def __init__(self, session,request):
		WebScreen.__init__(self, session,request)
		self["PowerState"] = PowerState(session)

class ParentControlWebScreen(WebScreen):
	def __init__(self, session,request):
		WebScreen.__init__(self, session,request)
		self["ParentControlList"] = ParentControl(session)
				
class WAPWebScreen(WebScreen):
	def __init__(self, session,request):
		WebScreen.__init__(self, session,request)
		self["WAPFillOptionListSyear"] = WAPfunctions(session,func = WAPfunctions.LISTTIME)
		self["WAPFillOptionListSday"] = WAPfunctions(session,func = WAPfunctions.LISTTIME)
		self["WAPFillOptionListSmonth"] = WAPfunctions(session,func = WAPfunctions.LISTTIME)
		self["WAPFillOptionListShour"] = WAPfunctions(session,func = WAPfunctions.LISTTIME)
		self["WAPFillOptionListSmin"] = WAPfunctions(session,func = WAPfunctions.LISTTIME)
		
		self["WAPFillOptionListEyear"] = WAPfunctions(session,func = WAPfunctions.LISTTIME)
		self["WAPFillOptionListEday"] = WAPfunctions(session,func = WAPfunctions.LISTTIME)
		self["WAPFillOptionListEmonth"] = WAPfunctions(session,func = WAPfunctions.LISTTIME)
		self["WAPFillOptionListEhour"] = WAPfunctions(session,func = WAPfunctions.LISTTIME)
		self["WAPFillOptionListEmin"] = WAPfunctions(session,func = WAPfunctions.LISTTIME)
		
		self["WAPFillOptionListRecord"] = WAPfunctions(session,func = WAPfunctions.OPTIONLIST)
		self["WAPFillOptionListAfterEvent"] = WAPfunctions(session,func = WAPfunctions.OPTIONLIST)
		
		self["WAPFillValueName"] = WAPfunctions(session,func = WAPfunctions.FILLVALUE)
		self["WAPFillValueDescr"] = WAPfunctions(session,func = WAPfunctions.FILLVALUE)

		self["WAPFillOptionListRepeated"] = WAPfunctions(session,func = WAPfunctions.REPEATED)
		self["WAPServiceList"] = WAPfunctions(session, func = WAPfunctions.SERVICELIST)

		self["WAPdeleteOldOnSave"] = WAPfunctions(session,func = WAPfunctions.DELETEOLD)
	
class StreamingWebScreen(WebScreen):
	def __init__(self, session,request):
		WebScreen.__init__(self, session,request)
		from Components.Sources.StreamService import StreamService
		self["StreamService"] = StreamService(self.session.nav)

class M3UStreamingWebScreen(WebScreen):
	def __init__(self, session,request):
		WebScreen.__init__(self, session,request)
		from Components.Sources.StaticText import StaticText
		from Components.Sources.Config import Config
		from Components.config import config
		self["ref"] = StaticText()
		self["localip"] = RequestData(request,what=RequestData.HOST)

class TsM3U(WebScreen):
	def __init__(self, session,request):
		WebScreen.__init__(self, session,request)
		from Components.Sources.StaticText import StaticText
		from Components.Sources.Config import Config
		from Components.config import config
		self["file"] = StaticText()
		self["localip"] = RequestData(request,what=RequestData.HOST)

class RestartWebScreen(WebScreen):
	def __init__(self, session,request):
		WebScreen.__init__(self, session,request)
		import plugin
		plugin.restartWebserver()
		
class GetPid(WebScreen):
      def __init__(self, session,request):
         WebScreen.__init__(self, session,request)
         from Components.Sources.StaticText import StaticText
         from enigma import iServiceInformation
         pids = self.session.nav.getCurrentService()
         if pids is not None:
                 pidinfo = pids.info()
                 VPID = hex(pidinfo.getInfo(iServiceInformation.sVideoPID))
                 APID = hex(pidinfo.getInfo(iServiceInformation.sAudioPID))
                 PPID = hex(pidinfo.getInfo(iServiceInformation.sPMTPID))
         self["pids"] = StaticText("%s,%s,%s"%(PPID.lstrip("0x"),VPID.lstrip("0x"),APID.lstrip("0x")))
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

class TextToURL(Converter):
	def __init__(self, arg):
		Converter.__init__(self, arg)

	def getHTML(self, id):
		return self.source.text.replace(" ","%20")

class ReturnEmptyXML(Converter):
	def __init__(self, arg):
		Converter.__init__(self, arg)
		
	def getHTML(self, id):
		return "<rootElement></rootElement>"

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
		return '<script>parent.set("%s", "%s");</script>\n'%(id, self.source.text.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"').replace('\xb0', '&deg;'))

# the performant 'listfiller'-engine (plfe)
class ListFiller(Converter):
	def __init__(self, arg):
		Converter.__init__(self, arg)
#		print "ListFiller-arg: ",arg

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
