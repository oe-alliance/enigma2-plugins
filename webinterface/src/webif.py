# -*- coding: UTF-8 -*-
Version = '$Header$';

# things to improve:
#	- better error handling
#	- use namespace parser

from Tools.Import import my_import

from Components.config import config
from Components.Converter.Converter import Converter
from Components.Element import Element
from Components.Sources.Source import ObsoleteSource

from xml.sax import make_parser
from xml.sax.handler import ContentHandler, feature_namespaces
from xml.sax.saxutils import escape as escape_xml
from twisted.python import util
from twisted.web import http, resource
from urllib2 import quote
from time import time

#DO NOT REMOVE THIS IMPORT
#It IS used (dynamically)
from WebScreens import *
#DO NOT REMOVE THIS IMPORT

from __init__ import decrypt_block
from os import urandom

# The classes and Function in File handle all ScreenPage-based requests
# ScreenPages use enigma2 standard functionality to bring contents to a webfrontend
#
# Like Skins a ScreenPage can consist of several Elements and Converters

#===============================================================================
# OneTimeElement
#
# This is the Standard Element for Rendering a "standard" WebElement
#===============================================================================
class OneTimeElement(Element):
	def __init__(self, id):
		Element.__init__(self)
		self.source_id = id

	def handleCommand(self, args):
		source = self.source
		source_id = self.source_id
		if ',' in source_id:
			paramlist = source_id.split(",")
			list = {}
			for key in paramlist:
				if key in args:
					list[key] = args[key][0]
				else:
					list[key] = None
			source.handleCommand(list)
		else:
			for c in args.get(source_id, ()):
				source.handleCommand(c)

	def render(self, request):
		request.write(self.source.getHTML(self.source_id))

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

#===============================================================================
# MacroElement
#
# A MacroElement helps using OneTimeElements inside a (Simple)ListFiller Loop
#===============================================================================
class MacroElement(OneTimeElement):
	def __init__(self, id, macro_dict, macro_name):
		OneTimeElement.__init__(self, id)
		self.macro_dict = macro_dict
		self.macro_name = macro_name

	def render(self, request):
		self.macro_dict[self.macro_name] = self.source.getHTML(self.source_id)

#===============================================================================
# StreamingElement
#
# In difference to an OneTimeElement a StreamingElement sends an ongoing Stream
# of Data. The end of the Streaming is usually when the client disconnects
#===============================================================================
class StreamingElement(OneTimeElement):
	def __init__(self, id):
		OneTimeElement.__init__(self, id)
		self.request = None

	def changed(self, what):
		if self.request:
			self.render(self.request)

	def setRequest(self, request):
		self.request = request

#===============================================================================
# ListItem
#
# a to-be-filled list item
#===============================================================================
class ListItem:
	def __init__(self, name, filternum):
		self.name = name
		self.filternum = filternum

#===============================================================================
# ListMacroItem
#
# MacroItem inside a (Simple)ListFiller
#===============================================================================
class ListMacroItem:
	def __init__(self, macrodict, macroname):
		self.macrodict = macrodict
		self.macroname = macroname


#===============================================================================
# TextToHTML
#
# Returns the String as is
#===============================================================================
class TextToHTML(Converter):
	def getHTML(self, id):
		return self.source.text.replace('\xc2\x86', '').replace('\xc2\x87', '').decode("utf-8", "ignore").encode("utf-8") # encode & etc. here!

#===============================================================================
# TextToXML
#
# Escapes the given Text to be XML conform
#===============================================================================
class TextToXML(Converter):
	def getHTML(self, id):
		return escape_xml(self.source.text).replace('\xc2\x86', '').replace('\xc2\x87', '').replace("\x19", "").replace("\x1c", "").replace("\x1e", "").decode("utf-8", "ignore").encode("utf-8")

#===============================================================================
# TextToURL
#
# Escapes the given Text so it can be used inside a URL
#===============================================================================
class TextToURL(Converter):
	def getHTML(self, id):
		return self.source.text.replace(" ", "%20").replace("+", "%2b").replace("&", "%26").replace('\xc2\x86', '').replace('\xc2\x87', '').decode("utf-8", "ignore").encode("utf-8")

#===============================================================================
# ReturnEmptyXML
#
# Returns a XML only consisting of <rootElement />
#===============================================================================
class ReturnEmptyXML(Converter):
	def getHTML(self, id):
		return "<rootElement />"

#===============================================================================
# Null
# Return simply NOTHING
# Useful if you only want to issue a command.
#===============================================================================
class Null(Converter):
	def getHTML(self, id):
		return ""


#===============================================================================
# JavascriptUpdate
#
# Transforms a string into a javascript update pattern
#===============================================================================
class JavascriptUpdate(Converter):
	def getHTML(self, id):
		# 3c5x9, added parent. , this is because the ie loads this in a iframe. an the set is in index.html.xml
		#		 all other will replace this in JS
		return '<script>parent.set("%s", "%s");</script>\n' % (id, self.source.text.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"').replace('\xb0', '&deg;'))

#===============================================================================
# SimpleListFiller
#
# The performant 'one-dimensonial listfiller' engine (podlfe)
#===============================================================================
class SimpleListFiller(Converter):
	def getText(self):
		l = self.source.simplelist
		conv_args = self.converter_arguments

		list = [ ]
		append = list.append
		for element in conv_args:
			if isinstance(element, basestring):
				append((element, None))
			elif isinstance(element, ListItem):
				append((element, element.filternum))
			elif isinstance(element, ListMacroItem):
				append(element.macrodict[element.macroname], None)
			else:
				raise Exception("neither string, ListItem nor ListMacroItem")

		strlist = [ ]
		append = strlist.append
		for item in l:
			if item is None:
				item = ""
			else:
				#filter out "non-displayable" Characters - at the very end, do it the hard way...
				item = str(item)#.replace('\xc2\x86', '').replace('\xc2\x87', '').replace("\x19", "").replace("\x1c", "").replace("\x1e", "").decode("utf-8", "ignore").encode("utf-8")

			for (element, filternum) in list:
				if not filternum:
					append(element)
					continue
				else:
					appendListItem(item, filternum, append)

		return ''.join(strlist)

	text = property(getText)

#===============================================================================
# the performant 'listfiller'-engine (plfe)
#===============================================================================
class ListFiller(Converter):
	def getText(self):
		l = self.source.list
		lut = self.source.lut
		conv_args = self.converter_arguments

		# now build a ["string", 1, "string", 2]-styled list, with indices into the
		# list to avoid lookup of item name for each entry
		lutlist = [ ]
		append = lutlist.append
		for element in conv_args:
			if isinstance(element, basestring):
				append((element, None))
			elif isinstance(element, ListItem):
				append((lut[element.name], element.filternum))
			elif isinstance(element, ListMacroItem):
				append((element.macrodict[element.macroname], None))
			else:
				raise Exception("neither string, ListItem nor ListMacroItem")

		# now, for the huge list, do:
		strlist = [ ]
		append = strlist.append
		for item in l:
			for (element, filternum) in lutlist:
				#None becomes ""
				curitem = ""
				if not filternum:
					if element is None:
						element = ""
					append(element)
					continue
				else:
					curitem = str(item[element])
					appendListItem(curitem, filternum, append)

		return ''.join(strlist)

	text = property(getText)

def appendListItem(item, filternum, append):
	if filternum == webifHandler.FILTER_JAVASCRIPT:
		append(item.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"'))
	elif filternum == webifHandler.FILTER_XML:
		append( escape_xml( item ))
	elif filternum == webifHandler.FILTER_URI:
		append(item.replace("%", "%25").replace("+", "%2B").replace('&', '%26').replace('?', '%3f').replace(' ', '+'))
	elif filternum == webifHandler.FILTER_URLENCODE:
		append(quote(item))
	elif filternum == webifHandler.FILTER_DATE:
		from time import localtime
		time = 0
		try:
			time = int(item)
			t = localtime(time)
			append("%04d-%02d-%02d" % (t.tm_year, t.tm_mon, t.tm_mday))
		except:
			append("---")
	elif filternum == webifHandler.FILTER_TIME:
		from time import localtime
		time = 0
		try:
			time = int(item)
			t = localtime(time)
			append("%02d:%02d" % (t.tm_hour, t.tm_min))
		except:
			append("--:--")
	elif filternum == webifHandler.FILTER_MINUTES:
		time = 0
		try:
			time = int(item)
			append("%d min" % (time / 60))
		except:
			append("-- min")
	elif filternum == webifHandler.FILTER_URI_ATTRIB:
		append(quote(item).replace("\"", "%22"))
	elif filternum == webifHandler.FILTER_HTML:
		if item == "None":
			append("n/a")
		else:
			append(item.replace("\n", "<br />"))
	elif filternum == webifHandler.FILTER_ATTRIBUTE:
		append( item.replace("\"", "&quot;"))
	else:
		append(item)

#===============================================================================
# webifHandler
#
# Handles the Content of a Web-Request
# It looks up the source, instantiates the Element and Calls the Converter
#===============================================================================
class webifHandler(ContentHandler):
	FILTER_NONE = 1
	FILTER_JAVASCRIPT = 2
	FILTER_XML = 3
	FILTER_URI = 4
	FILTER_URLENCODE = 5
	FILTER_DATE = 6
	FILTER_TIME = 7
	FILTER_MINUTES = 8
	FILTER_URI_ATTRIB = 9
	FILTER_HTML = 10
	FILTER_ATTRIBUTE = 11

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
				self.converter = my_import('.'.join(("Components", "Converter", ctype))).__dict__.get(ctype)
			except ImportError:
				self.converter = my_import('.'.join(("Plugins", "Extensions", "WebInterface", "WebComponents", "Converter", ctype))).__dict__.get(ctype)
		self.sub = [ ]

	def end_convert(self):
		sub = self.sub
		if len(sub) == 1:
			sub = sub[0]
		c = self.converter(sub)
		c.connect(self.source)
		self.source = c
		del self.sub

	def parse_item(self, attrs):
		if "name" in attrs:
			filter = {
				""					: webifHandler.FILTER_NONE,
				"javascript_escape"	: webifHandler.FILTER_JAVASCRIPT,
				"xml"				: webifHandler.FILTER_XML,
				"uri"				: webifHandler.FILTER_URI,
				"urlencode"			: webifHandler.FILTER_URLENCODE,
				"date"				: webifHandler.FILTER_DATE,
				"time"				: webifHandler.FILTER_TIME,
				"minutes"			: webifHandler.FILTER_MINUTES,
				"uriAttribute"		: webifHandler.FILTER_URI_ATTRIB,
				"html"				: webifHandler.FILTER_HTML,
				"attribute" 		: webifHandler.FILTER_ATTRIBUTE
			}[attrs.get("filter", "")]
			self.sub.append(ListItem(attrs["name"], filter))
		else:
			assert "macro" in attrs, "e2:item must have a name= or macro= attribute!"
			self.sub.append(ListMacroItem(self.macros, attrs["macro"]))

	def startElement(self, name, attrs):
		if name == "e2:screen":
			if "external_module" in attrs:
				exec "from " + attrs["external_module"] + " import *"
			self.screen = eval(attrs["name"])(self.session, self.request) # fixme
			self.screens.append(self.screen)
			return

		n3 = name[:3]
		if n3 == "e2:":
			self.mode += 1

		tag = '<' + name + ''.join([' %s="%s"' % x for x in attrs.items()]) + '>'
		#tag = tag.encode('utf-8')

		if self.mode == 0:
			self.res.append(tag)
		elif self.mode == 1: # expect "<e2:element>"
			assert name == "e2:element", "found %s instead of e2:element" % name
			self.start_element(attrs)
		elif self.mode == 2: # expect "<e2:convert>"
			if n3 == "e2:":
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

		n3 = name[:3]
		tag = "</" + name + ">"
		if self.mode == 0:
			self.res.append(tag)
		elif self.mode == 2:
			if n3 == "e2:": # closed 'convert' -> sub
				self.end_convert()
			else:
				self.sub.append(tag)
		elif self.mode == 1: # closed 'element'
			self.end_element()
		if n3 == "e2:":
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

#===============================================================================
# renderPage
#
# Creates the Handler for a Request and calls it
# Also ensures that the Handler is finished after the Request is done
#===============================================================================
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

	if config.plugins.Webinterface.anti_hijack.value:
		for screen in handler.screens:
			method = request.method
			if not screen.allow_GET and method == 'GET' and len(request.args) > 0:
				request.setHeader("Allow", "POST")
				request.write(
					resource.ErrorPage(http.NOT_ALLOWED, "Invalid method: GET!", "GET is not allowed here, please use POST").render(request)
				)
				if not request._disconnected:
					request.finish()
				else:
					print "[renderPage] request already finished!"
				return

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

# This is some debug code, i'll leave it for possible later use
#	def requestFinishedTest(nothing, handler, request):
#		print "Request has been cleaned: %s" %request
#		print nothing
#
#	d2 = request.notifyFinish()
#	d2.addBoth(requestFinishedTest, handler, request)
	if finish:
		requestFinish(handler, request)

	else:
		def _requestFinishDeferred(nothing, handler, request):
			from twisted.internet import reactor
			reactor.callLater(0, requestFinish, handler, request, requestAlreadyFinished=True)

		d = request.notifyFinish()
		d.addBoth( _requestFinishDeferred, handler, request )

#===============================================================================
# requestFinish
#
# This has to be/is called at the end of every ScreenPage-based Request
#===============================================================================
def requestFinish(handler, request, requestAlreadyFinished = False):
	handler.cleanup()
	if not requestAlreadyFinished:
		try:
			if not request._disconnected:
				request.finish()
			else:
				print "[requestFinish] request already finished!"
		except:
			pass

	del handler

def validate_certificate(cert, key):
	buf = decrypt_block(cert[8:], key)
	if buf is None:
		return None
	return buf[36:107] + cert[139:196]

def get_random():
	try:
		xor = lambda a,b: ''.join(chr(ord(c)^ord(d)) for c,d in zip(a,b*100))
		random = urandom(8)
		x = str(time())[-8:]
		result = xor(random, x)

		return result
	except:
		return None
