#!/usr/bin/python
# -*- coding: UTF-8 -*-
# $Id$
# $Author$
# $Revision$
# $Date$

import re, sys, os
from xml.dom.minidom import parse
from twisted.web.client import getPage #@UnresolvedImport
from twisted.internet import reactor #@UnresolvedImport

debugSetting = True
def setDebug(what):
	global debugSetting
	debugSetting = what

def debug(str):
	if debugSetting:
		print str

import htmlentitydefs
def html2unicode(in_html):
	# sanity checks
	try:
		in_html = in_html.decode('iso-8859-1')
		debug("[Callhtml2utf8] Converted from latin1")
	except:
		debug("[Callhtml2utf8] lost in translation from latin1")
		pass
	try:
		in_html = in_html.decode('utf-8')
		debug("[Callhtml2utf8] Converted from utf-8")
	except:
		debug("[Callhtml2utf8] lost in translation from utf-8")
		pass

	# first convert some WML codes from hex: e.g. &#xE4 -> &#228
	htmlentityhexnumbermask = re.compile('(&#x(..);)')
	entities = htmlentityhexnumbermask.finditer(in_html)
	for x in entities:
		in_html = in_html.replace(x.group(1), '&#' + str(int(x.group(2),16)) + ';')

	entitydict = {}
	# catch &uuml; and colleagues here
	htmlentitynamemask = re.compile('(&(\D{1,5}?);)')
	entities = htmlentitynamemask.finditer(in_html)
	for x in entities:
		# debug("[Callhtml2utf8] mask: found %s" %repr(x.group(2)))
		entitydict[x.group(1)] = htmlentitydefs.name2codepoint[str(x.group(2))]

	# this is for &#288 and other numbers
	htmlentitynumbermask = re.compile('(&#(\d{1,5}?);)')
	entities = htmlentitynumbermask.finditer(in_html)
	for x in entities:
		# debug("[Callhtml2utf8] number: found %s" %x.group(1))
		entitydict[x.group(1)] = x.group(2)
		
	# no go and replace all occurrences
	for key, codepoint in entitydict.items():
		try:
			debug("[Callhtml2utf8] replace %s with %s" %(repr(key), unichr(int(codepoint))))
			in_html = in_html.replace(unicode(key), (unichr(int(codepoint))))
			# in_html = in_html.replace(unicode(key), (unichr(int(codepoint))).decode('cp1252').encode('utf-8'))
		except ValueError:
			debug("[Callhtml2utf8] ValueError " + key + "/" + str(codepoint))
			pass
	return in_html

def out(number, caller):
	debug("[out] %s: %s" %(number, caller))
	if not caller:
		return
	name = vorname = strasse = hnr = plz = ort = ""
	lines = caller.split(', ')
	found = re.match("(.+?)\s+(.+)", lines[0])
	if found:
		name = found.group(1)
		vorname = found.group(2)
	else:
		name = lines[0]
	aktuell = 1
	found = re.match("^(.+) ([-\d]+)$", lines[1], re.S)
	if found:
		strasse = found.group(1)
		hnr = found.group(2)
		aktuell = 2
	else:
		found = re.match("^(\d+) (.+)$", lines[1], re.S)
		if found:
			strasse = found.group(2)
			hnr = found.group(1)
		else:
			strasse = lines[1]
		aktuell = 2
	for i in range(aktuell, len(lines)):
		found = re.match("(\S+)\s+(.+)", lines[i], re.S)
		if found:
			plz = found.group(1)
			ort = found.group(2)
			break
	else:
		ort = lines[aktuell].strip()
	print "NA: %s;VN: %s;STR: %s;HNR: %s;PLZ: %s;ORT: %s" %( name,vorname,strasse,hnr,plz,ort )

def simpleout(number, caller):
	print caller

try:
	from Tools.Directories import resolveFilename, SCOPE_PLUGINS
	reverseLookupFileName = resolveFilename(SCOPE_PLUGINS, "Extensions/FritzCall/reverselookup.xml")
except ImportError:
	reverseLookupFileName = "reverselookup.xml"

countries = { }
reverselookupMtime = 0

class ReverseLookupAndNotifier:
	def __init__(self, number, outputFunction=out, charset="cp1252", countrycode = "0049"):
		debug("[ReverseLookupAndNotifier] reverse Lookup for %s!" %number)
		self.number = number
		self.outputFunction = outputFunction
		self.caller = ""
		self.currentWebsite = None
		self.nextWebsiteNo = 0
#===============================================================================
# sorry does not work at all
#		if not charset:
#			charset = sys.getdefaultencoding()
#			debug("[ReverseLookupAndNotifier] set charset from system: %s!" %charset)
#===============================================================================
		self.charset = charset

		global reverselookupMtime
		reverselookupMtimeAct = os.stat(reverseLookupFileName)[8]
		if not countries or reverselookupMtimeAct > reverselookupMtime:
			debug("[ReverseLookupAndNotifier] (Re-)Reading %s\n" %reverseLookupFileName)
			reverselookupMtime = reverselookupMtimeAct
			dom = parse(reverseLookupFileName)
			for top in dom.getElementsByTagName("reverselookup"):
				for country in top.getElementsByTagName("country"):
					code = country.getAttribute("code").replace("+","00")
					countries[code] = country.getElementsByTagName("website")

		self.countrycode = countrycode

		if number[0] != "0":
			# self.caller = _("UNKNOWN")
			self.notifyAndReset()
			return

		if self.number[:2] == "00":
			if countries.has_key(self.number[:3]):	 #	e.g. USA
				self.countrycode = self.number[:3]
			elif countries.has_key(self.number[:4]):
				self.countrycode = self.number[:4]
			elif countries.has_key(self.number[:5]):
				self.countrycode = self.number[:5]
			else:
				debug("[ReverseLookupAndNotifier] Country cannot be reverse handled")
				# self.caller = _("UNKNOWN")
				self.notifyAndReset()
				return

		if countries.has_key(self.countrycode):
			debug("[ReverseLookupAndNotifier] Found website for reverse lookup")
			self.websites = countries[self.countrycode]
			self.nextWebsiteNo = 1
			self.handleWebsite(self.websites[0])
		else:
			debug("[ReverseLookupAndNotifier] Country cannot be reverse handled")
			# self.caller = _("UNKNOWN")
			self.notifyAndReset()
			return

	def handleWebsite(self, website):
		debug("[ReverseLookupAndNotifier] handleWebsite: " + website.getAttribute("name"))
		if self.number[:2] == "00":
			number = website.getAttribute("prefix") + self.number.replace(self.countrycode,"")
		else:
			number = self.number

		url = website.getAttribute("url")
		if re.search('$AREACODE',url) or re.search('$PFXAREACODE',url):
			debug("[ReverseLookupAndNotifier] handleWebsite: (PFX)ARECODE cannot be handled")
			# self.caller = _("UNKNOWN")
			self.notifyAndReset()
			return
		#
		# Apparently, there is no attribute called (pfx)areacode anymore
		# So, this below will not work.
		#
		if re.search('\\$AREACODE',url) and website.hasAttribute("areacode"):
			areaCodeLen = int(website.getAttribute("areacode"))
			url = url.replace("$AREACODE","%(areacode)s").replace("$NUMBER","%(number)s")
			url = url %{ 'areacode':number[:areaCodeLen], 'number':number[areaCodeLen:] }
		elif re.search('\\$PFXAREACODE',url) and website.hasAttribute("pfxareacode"):
			areaCodeLen = int(website.getAttribute("pfxareacode"))
			url = url.replace("$PFXAREACODE","%(pfxareacode)s").replace("$NUMBER","%(number)s")
			url = url %{ 'pfxareacode':number[:areaCodeLen], 'number':number[areaCodeLen:] }
		elif re.search('\\$NUMBER',url): 
			url = url.replace("$NUMBER","%s") %number
		else:
			debug("[ReverseLookupAndNotifier] handleWebsite: cannot handle websites with no $NUMBER in url")
			# self.caller = _("UNKNOWN")
			self.notifyAndReset()
			return
		debug("[ReverseLookupAndNotifier] Url to query: " + url)
		url = url.encode("UTF-8", "replace")
		self.currentWebsite = website
		getPage(url,
			agent="Mozilla/5.0 (Windows; U; Windows NT 6.0; de; rv:1.9.0.5) Gecko/2008120122 Firefox/3.0.5"
			).addCallback(self._gotPage).addErrback(self._gotError)


	def _gotPage(self, page):
		debug("[ReverseLookupAndNotifier] _gotPage")
		found = re.match('.*content=".*?charset=([^"]+)"',page,re.S)
		if found:
			debug("[ReverseLookupAndNotifier] Charset: " + found.group(1))
			page = page.replace("\xa0"," ").decode(found.group(1), "replace")
		else:
			page = page.replace("\xa0"," ").decode("ISO-8859-1", "replace")

		for entry in self.currentWebsite.getElementsByTagName("entry"):
			# debug("[ReverseLookupAndNotifier] _gotPage: try entry")
			details = []
			for what in ["name", "street", "city", "zipcode"]:
				pat = ".*?" + self.getPattern(entry, what)
				debug("[ReverseLookupAndNotifier] _gotPage: look for '''%s''' with '''%s'''" %( what, pat ))
				found = re.match(pat, page, re.S|re.M)
				if found:
					debug("[ReverseLookupAndNotifier] _gotPage: found for '''%s''': '''%s'''" %( what, repr(found.group(1)) ))
					item = found.group(1).replace("&nbsp;"," ").replace("</b>","").replace(","," ")
					item = html2unicode(item)
					newitem = item.replace("  ", " ")
					while newitem != item:
						item = newitem
						newitem = item.replace("  ", " ")
					debug("[ReverseLookupAndNotifier] _gotPage: add to details: " + repr(item))
					details.append(item.strip())
				else:
					break

			if len(details) != 4:
				continue
			else:
				name = details[0]
				address =  details[1] + ", " + details[3] + " " + details[2]
				debug("[ReverseLookupAndNotifier] _gotPage: Reverse lookup succeeded:\nName: %s\nAddress: %s" %(name, address))
				self.caller = "%s, %s" %(name, address)
				# if self.number != 0 and config.plugins.Call.addcallers.value and self.event == "RING":
					# phonebook.add(self.number, self.caller)

				self.notifyAndReset()
				return True
		else:
			self._gotError("[ReverseLookupAndNotifier] _gotPage: Nothing found at %s" %self.currentWebsite.getAttribute("name"))
			
	def _gotError(self, error = ""):
		debug("[ReverseLookupAndNotifier] _gotError - Error: %s" %error)
		if self.nextWebsiteNo >= len(self.websites):
			debug("[ReverseLookupAndNotifier] _gotError: I give up")
			# self.caller = _("UNKNOWN")
			self.notifyAndReset()
			return
		else:
			debug("[ReverseLookupAndNotifier] _gotError: try next website")
			self.nextWebsiteNo = self.nextWebsiteNo+1
			self.handleWebsite(self.websites[self.nextWebsiteNo-1])

	def getPattern(self, website, which):
		pat1 = website.getElementsByTagName(which)
		if len(pat1) > 1:
			debug("[ReverseLookupAndNotifier] getPattern: Something strange: more than one %s for website %s" %(which, website.getAttribute("name")))
		return pat1[0].childNodes[0].data

	def notifyAndReset(self):
		debug("[ReverseLookupAndNotifier] notifyAndReset: Number: " + self.number + "; Caller: " + self.caller)
		# debug("1: " + repr(self.caller))
		if self.caller:
			try:
				# debug("2: " + repr(self.caller))
				self.caller = self.caller.encode(self.charset)
				# debug("3: " + repr(self.caller))
			except:
				debug("[ReverseLookupAndNotifier] cannot encode?!?!")
				pass
			# self.caller = unicode(self.caller)
			# debug("4: " + repr(self.caller))
			self.outputFunction(self.number, self.caller)
		else:
			self.outputFunction(self.number, "")
		if __name__ == '__main__':
			reactor.stop() #@UndefinedVariable

if __name__ == '__main__':
	cwd = os.path.dirname(sys.argv[0])
	if (len(sys.argv) == 2):
		# nrzuname.py Nummer
		ReverseLookupAndNotifier(sys.argv[1])
		reactor.run() #@UndefinedVariable
	elif (len(sys.argv) == 3):
		# nrzuname.py Nummer Charset
		setDebug(False)
		ReverseLookupAndNotifier(sys.argv[1], simpleout, sys.argv[2])
		reactor.run() #@UndefinedVariable
