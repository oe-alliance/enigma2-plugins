#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#
# $Id$
# $Author$
# $Revision$
# $Date$
# -*- coding: utf-8 -*-

import re, sys, os
from xml.dom.minidom import parse
from twisted.web.client import getPage
from twisted.internet import reactor

debug = True
def setDebug(what):
	global debug
	debug = what

def myprint(str):
	if debug:
		print str

def html2utf8(in_html):
	try:
		import htmlentitydefs

		# first convert some WML codes; does not work?!?!
		wmldefs = [
				("&#xDF;", "ß"),
				("&#xE4;", "ä"),
				("&#xF6;", "ö"),
				("&#xFC;", "ü"),
				("&#xC4;", "Ä"),
				("&#xD6;", "Ö"),
				("&#xDC;", "Ü")
				]
		for (a, b)in wmldefs:
			try:
				in_html = in_html.replace(a,b)
			except UnicodeError:
				pass

		htmlentitynamemask = re.compile('(&(\D{1,5}?);)')
		entitydict = {}
		entities = htmlentitynamemask.finditer(in_html)
		for x in entities:
			entitydict[x.group(1)] = x.group(2)
		for key, name in entitydict.items():
			try:
				entitydict[key] = htmlentitydefs.name2codepoint[name]
			except KeyError:
				myprint("[Callhtml2utf8] KeyError " + key + "/" + name)
				pass

		htmlentitynumbermask = re.compile('(&#(\d{1,5}?);)')
		entities = htmlentitynumbermask.finditer(in_html)
		for x in entities:
			entitydict[x.group(1)] = x.group(2)
		for key, codepoint in entitydict.items():
			try:
				in_html = in_html.replace(key, (unichr(int(codepoint)).encode('utf8', "replace")))
			except ValueError:
				myprint("[Callhtml2utf8] ValueError " + key + "/" + str(codepoint))
				pass
	except ImportError:
		try:
			return in_html.replace("&amp;", "&").replace("&szlig;", "ß").replace("&auml;", "ä").replace("&ouml;", "ö").replace("&uuml;", "ü").replace("&Auml;", "Ä").replace("&Ouml;", "Ö").replace("&Uuml;", "Ü")
		except UnicodeDecodeError:
			pass
	return in_html

def out(number, caller):
	name = vorname = strasse = hnr = plz = ort = ""
	lines = caller.split(', ')
	found = re.match("(.+?)\s+(.+)", lines[0])
	if found:
		name = found.group(1)
		vorname = found.group(2)
	else:
		name = lines[0]
	aktuell = 1
	found = re.match("^(.+) (\d+)$", lines[1], re.S)
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
	def __init__(self, number, outputFunction=out, charset="ISO-8859-1"):
		myprint("[ReverseLookupAndNotifier] reverse Lookup for %s!" %number)
		self.number = number
		self.outputFunction = outputFunction
		self.charset = charset
		self.caller = ""
		self.currentWebsite = None
		self.nextWebsiteNo = 0

		global reverselookupMtime
		reverselookupMtimeAct = os.stat(reverseLookupFileName)[8]
		if not countries or reverselookupMtimeAct > reverselookupMtime:
			myprint("[ReverseLookupAndNotifier] (Re-)Reading %s\n" %reverseLookupFileName)
			reverselookupMtime = reverselookupMtimeAct
			dom = parse(reverseLookupFileName)
			for top in dom.getElementsByTagName("reverselookup"):
				for country in top.getElementsByTagName("country"):
					code = country.getAttribute("code").replace("+","00")
					countries[code] = country.getElementsByTagName("website")

		self.countrycode = "0049"

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
				myprint("[ReverseLookupAndNotifier] Country cannot be reverse handled")
				# self.caller = _("UNKNOWN")
				self.notifyAndReset()
				return

		if countries.has_key(self.countrycode):
			myprint("[ReverseLookupAndNotifier] Found website for reverse lookup")
			self.websites = countries[self.countrycode]
			self.nextWebsiteNo = 1
			self.handleWebsite(self.websites[0])
		else:
			myprint("[ReverseLookupAndNotifier] Country cannot be reverse handled")
			# self.caller = _("UNKNOWN")
			self.notifyAndReset()
			return

	def handleWebsite(self, website):
		myprint("[ReverseLookupAndNotifier] handleWebsite: " + website.getAttribute("name"))
		if self.number[:2] == "00":
			number = website.getAttribute("prefix") + self.number.replace(self.countrycode,"")
		else:
			number = self.number

		url = website.getAttribute("url")
		if re.search('$AREACODE',url) or re.search('$PFXAREACODE',url):
			myprint("[ReverseLookupAndNotifier] handleWebsite: (PFX)ARECODE cannot be handled")
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
			myprint("[ReverseLookupAndNotifier] handleWebsite: cannot handle websites with no $NUMBER in url")
			# self.caller = _("UNKNOWN")
			self.notifyAndReset()
			return
		myprint("[ReverseLookupAndNotifier] Url to query: " + url)
		url = url.encode("UTF-8", "replace")
		self.currentWebsite = website
		# I am not sure, whether setting the user-agent works this way
		getPage(url,
			method="GET",
			headers = {
#					"User-Agent" : "User-Agent=Mozilla/5.0 (Windows; U; Windows NT 6.0; de; rv:1.9.0.4) Gecko/2008102920 Firefox/3.0.4"
#					"Connection" : "keep-alive",
#					"Keep-Alive" : "300",
#					"Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#					"Accept-Charset" : "ISO-8859-1,utf-8;q=0.7,*;q=0.7",
##					"Accept-Encoding" : "gzip,deflate"
			}).addCallback(self._gotPage).addErrback(self._gotError)

	def _gotPage(self, page):
		myprint("[ReverseLookupAndNotifier] _gotPage")
		found = re.match('.*content=".*?charset=([^"]+)"',page,re.S)
		if found:
			myprint("[ReverseLookupAndNotifier] Charset: " + found.group(1))
			page = page.replace("\xa0"," ").decode(found.group(1), "replace")
		else:
			page = page.replace("\xa0"," ").decode("ISO-8859-1", "replace")

		for entry in self.currentWebsite.getElementsByTagName("entry"):
			# myprint("[ReverseLookupAndNotifier] _gotPage: try entry")
			details = []
			for what in ["name", "street", "city", "zipcode"]:
				# myprint("[ReverseLookupAndNotifier] _gotPage: look for '''%s''' with '''%s'''" %( what, pat ))
				pat = ".*?" + self.getPattern(entry, what)
				found = re.match(pat, page, re.S|re.M)
				if found:
					# myprint("[ReverseLookupAndNotifier] _gotPage: found for '''%s''': '''%s'''" %( what, found.group(2) ))
					myprint(found.group(1))
					item = found.group(1).replace("&nbsp;"," ").replace("</b>","").replace(","," ")
					item = html2utf8(item)
					newitem = item.replace("  ", " ")
					while newitem != item:
						item = newitem
						newitem = item.replace("  ", " ")
					details.append(item.strip())
				else:
					break

			if len(details) != 4:
				continue
			else:
				name = details[0]
				address =  details[1] + ", " + details[3] + " " + details[2]
				myprint("[ReverseLookupAndNotifier] _gotPage: Reverse lookup succeeded:\nName: %s\nAddress: %s" %(name, address))
				self.caller = "%s, %s" %(name, address)
				# if self.number != 0 and config.plugins.Call.addcallers.value and self.event == "RING":
					# phonebook.add(self.number, self.caller)

				self.caller = self.caller.encode("UTF-8", "replace")
				self.notifyAndReset()
				return True
				break
		else:
			self._gotError("[ReverseLookupAndNotifier] _gotPage: Nothing found at %s" %self.currentWebsite.getAttribute("name"))
			
	def _gotError(self, error = ""):
		myprint("[ReverseLookupAndNotifier] _gotError - Error: %s" %error)
		if self.nextWebsiteNo >= len(self.websites):
			myprint("[ReverseLookupAndNotifier] _gotError: I give up")
			# self.caller = _("UNKNOWN")
			self.notifyAndReset()
			return
		else:
			myprint("[ReverseLookupAndNotifier] _gotError: try next website")
			self.nextWebsiteNo = self.nextWebsiteNo+1
			self.handleWebsite(self.websites[self.nextWebsiteNo-1])

	def getPattern(self, website, which):
		pat1 = website.getElementsByTagName(which)
		if len(pat1) > 1:
			myprint("Something strange: more than one %s for website %s" %(which, website.getAttribute("name")))
		return pat1[0].childNodes[0].data

	def notifyAndReset(self):
		myprint("[ReverseLookupAndNotifier] notifyAndReset: Number: " + self.number + "; Caller: " + self.caller)
		if self.caller:
			self.outputFunction(self.number, self.caller.decode("utf-8").encode(self.charset))
		if __name__ == '__main__':
			reactor.stop()

if __name__ == '__main__':
	cwd = os.path.dirname(sys.argv[0])
	if (len(sys.argv) == 2):
		# nrzuname.py Nummer
		ReverseLookupAndNotifier(sys.argv[1])
		reactor.run()
	elif (len(sys.argv) == 3):
		# nrzuname.py Nummer SimpleOut
		debug = False
		ReverseLookupAndNotifier(sys.argv[1], simpleout)
		reactor.run()
