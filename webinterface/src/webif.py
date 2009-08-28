# -*- coding: UTF-8 -*-
Version = '$Header$';

# things to improve:
#	- nicer code
#	- screens need to be defined somehow else.
#	  I don't know how, yet. Probably each in an own file.
#	- better error handling
#	- use namespace parser

from Tools.Import import my_import

from Components.Sources.Source import ObsoleteSource
from Components.Converter.Converter import Converter
from Components.Element import Element

from xml.sax import make_parser
from xml.sax.handler import ContentHandler, feature_namespaces
from xml.sax.saxutils import escape as escape_xml
from twisted.python import util
from urllib2 import quote

#DO NOT REMOVE THIS IMPORT
#It IS used (dynamically)
from WebScreens import *
#DO NOT REMOVE THIS IMPORT
		
# implements the 'render'-call.
# this will act as a downstream_element, like a renderer.
class OneTimeElement(Element):
	def __init__(self, id):
		Element.__init__(self)
		self.source_id = id

	# CHECKME: is this ok performance-wise?
	def handleCommand(self, args):
		if self.source_id.find(",") >= 0:
			paramlist = self.source_id.split(",")
			list = {}
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

	def render(self, request):
		t = self.source.getHTML(self.source_id)
		request.write(t)

	def execBegin(self):
		self.suspended = False

	def execEnd(self):
		self.suspended = True

	def onShow(self):
		pass

	def onHide(self):
		pass

	def destroy(self):
		pass

class MacroElement(OneTimeElement):
	def __init__(self, id, macro_dict, macro_name):
		OneTimeElement.__init__(self, id)
		self.macro_dict = macro_dict
		self.macro_name = macro_name

	def render(self, request):
		self.macro_dict[self.macro_name] = self.source.getHTML(self.source_id)

class StreamingElement(OneTimeElement):
	def __init__(self, id):
		OneTimeElement.__init__(self, id)
		self.request = None

	def changed(self, what):
		if self.request:
			self.render(self.request)

	def setRequest(self, request):
		self.request = request

# a to-be-filled list item
class ListItem:
	def __init__(self, name, filternum):
		self.name = name
		self.filternum = filternum

class ListMacroItem:
	def __init__(self, macrodict, macroname):
		self.macrodict = macrodict
		self.macroname = macroname

class TextToHTML(Converter):
	def __init__(self, arg):
		Converter.__init__(self, arg)

	def getHTML(self, id):
		return self.source.text # encode & etc. here!

class TextToXML(Converter):
	def __init__(self, arg):
		Converter.__init__(self, arg)

	def getHTML(self, id):
		return escape_xml(self.source.text).replace("\x19", "").replace("\x1c", "").replace("\x1e", "")

class TextToURL(Converter):
	def __init__(self, arg):
		Converter.__init__(self, arg)

	def getHTML(self, id):
		return self.source.text.replace(" ", "%20")

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
		return '<script>parent.set("%s", "%s");</script>\n' % (id, self.source.text.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"').replace('\xb0', '&deg;'))

# the performant 'one-dimensonial listfiller' engine (podlfe)
class SimpleListFiller(Converter):
	def __init__(self, arg):
		Converter.__init__(self, arg)
		
	def getText(self):
		l = self.source.simplelist
		conv_args = self.converter_arguments		
		
		list = [ ]
		for element in conv_args:
			if isinstance(element, basestring):
				list.append((element, None))
			elif isinstance(element, ListItem):
				list.append((element, element.filternum))
			elif isinstance(element, ListMacroItem):
				list.append(element.macrodict[element.macroname], None)
			else:
				raise Exception("neither string, ListItem nor ListMacroItem")
			
		strlist = [ ]
		append = strlist.append
		for item in l:
			if item is None:
				item = ""
				
			for (element, filternum) in list:
				if not filternum:
					append(element)
				elif filternum == 2:
					append(str(item).replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"'))
				elif filternum == 3:					
					append(escape_xml(str(item)))
				elif filternum == 4:
					append(str(item).replace("%", "%25").replace("+", "%2B").replace('&', '%26').replace('?', '%3f').replace(' ', '+'))
				elif filternum == 5:
					append(quote(str(item)))
				elif filternum == 6:
					time = parseint(item) or 0
					t = localtime(time)
					append("%02d:%02d" % (t.tm_hour, t.tm_min))
				elif filternum == 7:
					time = parseint(item) or 0
					t = localtime(time)
					append("%d min" % (time / 60))
				else:
					append(str(item))
		# (this will be done in c++ later!)

		return ''.join(strlist)		
	
	text = property(getText)
		
				

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
		lutlist = [ ]
		for element in conv_args:
			if isinstance(element, basestring):
				lutlist.append((element, None))
			elif isinstance(element, ListItem):
				lutlist.append((lut[element.name], element.filternum))
			elif isinstance(element, ListMacroItem):
				lutlist.append((element.macrodict[element.macroname], None))
			else:
				raise Exception("neither string, ListItem nor ListMacroItem")

		# now, for the huge list, do:
		strlist = [ ]
		append = strlist.append
		for item in l:
			for (element, filternum) in lutlist:			
				#None becomes ""
				curitem = ""
				if filternum:
					curitem = item[element]
					if curitem is None:
						curitem = ""
				else:
					if element is None:
						element = ""
						
				if not filternum:
					append(element)
				elif filternum == 2:
					append(str(curitem).replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"'))
				elif filternum == 3:
					append(escape_xml(str(curitem)))
				elif filternum == 4:
					append(str(curitem).replace("%", "%25").replace("+", "%2B").replace('&', '%26').replace('?', '%3f').replace(' ', '+'))
				elif filternum == 5:
					append(quote(str(curitem)))
				elif filternum == 6:
					from time import localtime
					time = int(float(curitem)) or 0
					t = localtime(time)
					append("%02d:%02d" % (t.tm_hour, t.tm_min))
				elif filternum == 7:
					from time import localtime
					time = int(float(curitem)) or 0
					t = localtime(time)
					append("%d min" % (time / 60))					
				else:
					append(str(curitem))
		# (this will be done in c++ later!)

		return ''.join(strlist)

	text = property(getText)

class webifHandler(ContentHandler):
	def __init__(self, session, request):
		self.res = [ ]
		self.mode = 0
		self.screen = None
		self.session = session
		self.screens = [ ]
		self.request = request
		self.macros = { }

	def start_element(self, attrs):
		scr = self.screen

		wsource = attrs["source"]

		path = wsource.split('.')
		while len(path) > 1:
			scr = self.screen.getRelatedScreen(path[0])
			if scr is None:
				print "[webif.py] Parent Screen not found!"
				print wsource
			path = path[1:]

		source = scr.get(path[0])

		if isinstance(source, ObsoleteSource):
			# however, if we found an "obsolete source", issue warning, and resolve the real source.
			print "WARNING: WEBIF '%s' USES OBSOLETE SOURCE '%s', USE '%s' INSTEAD!" % (name, wsource, source.new_source)
			print "OBSOLETE SOURCE WILL BE REMOVED %s, PLEASE UPDATE!" % (source.removal_date)
			if source.description:
				print source.description

			wsource = source.new_source
		else:
			pass
			# otherwise, use that source.

		self.source = source
		self.source_id = str(attrs.get("id", wsource))
		self.is_streaming = "streaming" in attrs
		self.macro_name = attrs.get("macro") or None

	def end_element(self):
		# instatiate either a StreamingElement or a OneTimeElement, depending on what's required.
		if not self.is_streaming:
			if self.macro_name is None:
				c = OneTimeElement(self.source_id)
			else:
				c = MacroElement(self.source_id, self.macros, self.macro_name)
		else:
			assert self.macro_name is None
			c = StreamingElement(self.source_id)

		c.connect(self.source)
		self.res.append(c)
		self.screen.renderer.append(c)
		del self.source

	def start_convert(self, attrs):
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

	def end_convert(self):
		if len(self.sub) == 1:
			self.sub = self.sub[0]
		c = self.converter(self.sub)
		c.connect(self.source)
		self.source = c
		del self.sub

	def parse_item(self, attrs):
		if "name" in attrs:
			filter = {"": 1, "javascript_escape": 2, "xml": 3, "uri": 4, "urlencode": 5, "time": 6, "minutes": 7}[attrs.get("filter", "")]
			self.sub.append(ListItem(attrs["name"], filter))
		else:
			assert "macro" in attrs, "e2:item must have a name= or macro= attribute!"
			self.sub.append(ListMacroItem(self.macros, attrs["macro"]))

	def startElement(self, name, attrs):
		if name == "e2:screen":
			self.screen = eval(attrs["name"])(self.session, self.request) # fixme
			self.screens.append(self.screen)
			return

		if name[:3] == "e2:":
			self.mode += 1

		tag = [' %s="%s"' % (key, val) for (key, val) in attrs.items()]
		tag.insert(0, name)
		tag.insert(0, '<')
		tag.append('>')
		tag = ''.join(tag)#.encode('utf-8')

		if self.mode == 0:
			self.res.append(tag)
		elif self.mode == 1: # expect "<e2:element>"
			assert name == "e2:element", "found %s instead of e2:element" % name
			self.start_element(attrs)
		elif self.mode == 2: # expect "<e2:convert>"
			if name[:3] == "e2:":
				assert name == "e2:convert"
				self.start_convert(attrs)
			else:
				self.sub.append(tag)
		elif self.mode == 3:
			assert name == "e2:item", "found %s instead of e2:item!" % name

			self.parse_item(attrs)

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
			self.end_convert()
		elif self.mode == 1: # closed 'element'
			self.end_element()
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

def renderPage(request, path, session):
	# read in the template, create required screens
	# we don't have persistense yet.
	# if we had, this first part would only be done once.
	handler = webifHandler(session, request)
	parser = make_parser()
	parser.setFeature(feature_namespaces, 0)
	parser.setContentHandler(handler)
	parser.parse(open(util.sibpath(__file__, path)))

	# by default, we have non-streaming pages
	finish = True

	# first, apply "commands" (aka. URL argument)
	for x in handler.res:
		if isinstance(x, Element):
			x.handleCommand(request.args)

	handler.execBegin()

	# now, we have a list with static texts mixed
	# with non-static Elements.
	# flatten this list, write into the request.
	for x in handler.res:
		if isinstance(x, Element):
			if isinstance(x, StreamingElement):
				finish = False
				x.setRequest(request)
			x.render(request)
		else:
			request.write(str(x))

	# if we met a "StreamingElement", there is at least one
	# element which wants to output data more than once,
	# i.e. on host-originated changes.
	# in this case, don't finish yet, don't cleanup yet,
	# but instead do that when the client disconnects.
	if finish:
		requestFinish(handler, request)
	
	else:	
		def requestFinishDeferred(nothing, handler, request):
			from twisted.internet import reactor
			reactor.callLater(1, requestFinish, handler, request)				
		
		d = request.notifyFinish()

		d.addErrback( requestFinishDeferred, handler, request )
		d.addCallback( requestFinishDeferred, handler, request )
							
		
def requestFinish(handler, request):
	handler.cleanup()
	request.finish()	
	
	del handler