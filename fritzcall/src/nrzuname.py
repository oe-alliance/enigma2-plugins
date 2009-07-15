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

try:
	from . import debug #@UnresolvedImport
	def setDebug(what):
		pass
except ValueError:
	debugVal = True
	def setDebug(what):
		global debugVal
		debugVal = what
	def debug(str):
		if debugVal:
			print str

import htmlentitydefs
def html2unicode(in_html):
#===============================================================================
#	# sanity checks
#	try:
#		in_html = in_html.decode('iso-8859-1')
#		debug("[Callhtml2utf8] Converted from latin1")
#	except:
#		debug("[Callhtml2utf8] lost in translation from latin1")
#		pass
#	try:
#		in_html = in_html.decode('utf-8')
#		debug("[Callhtml2utf8] Converted from utf-8")
#	except:
#		debug("[Callhtml2utf8] lost in translation from utf-8")
#		pass
#===============================================================================

	# first convert some WML codes from hex: e.g. &#xE4 -> &#228
	htmlentityhexnumbermask = re.compile('(&#x(..);)')
	entities = htmlentityhexnumbermask.finditer(in_html)
	for x in entities:
		in_html = in_html.replace(x.group(1), '&#' + str(int(x.group(2),16)) + ';')

	htmlentitynamemask = re.compile('(&(\D{1,5}?);)')
	entitydict = {}
	entities = htmlentitynamemask.finditer(in_html)
	for x in entities:
		# debug("[Callhtml2utf8] mask: found %s" %repr(x.group(2)))
		entitydict[x.group(1)] = x.group(2)
	for key, name in entitydict.items():
		try:
			entitydict[key] = htmlentitydefs.name2codepoint[str(name)]
		except KeyError:
			debug("[Callhtml2utf8] KeyError " + key + "/" + name)

	htmlentitynumbermask = re.compile('(&#(\d{1,5}?);)')
	entities = htmlentitynumbermask.finditer(in_html)
	for x in entities:
		# debug("[Callhtml2utf8] number: found %s" %x.group(1))
		entitydict[x.group(1)] = x.group(2)
	for key, codepoint in entitydict.items():
		try:
			debug("[nrzuname] html2utf8: replace %s with %s" %(repr(key), str(codepoint)))
			in_html = in_html.replace(unicode(key), (unichr(int(codepoint))))
		except ValueError:
			debug("[nrzuname] html2utf8: ValueError " + key + "/" + str(codepoint))
	return in_html

def normalizePhoneNumber(intNo):
	found = re.match('^\+(.*)', intNo)
	if found:
		intNo = '00' + found.group(1)
	intNo = intNo.replace('(', '').replace(')', '').replace(' ', '').replace('/', '').replace('-', '')
	found = re.match('.*?([0-9]+)', intNo)
	if found:
		return found.group(1)
	else:
		return '0'

def out(number, caller):
	debug("[nrzuname] out: %s: %s" %(number, caller))
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

	if len(lines) > 1:
		if len(lines) > 2: # this means, we have street and city
			found = re.match("^(.+) ([-\d]+)$", lines[1], re.S)
			if found:
				strasse = found.group(1)
				hnr = found.group(2)
			else:
				found = re.match("^(\d+) (.+)$", lines[1], re.S)
				if found:
					strasse = found.group(2)
					hnr = found.group(1)
				else:
					strasse = lines[1]
			for i in range(2, len(lines)):
				found = re.match("(\S+)\s+(.+)", lines[i], re.S)
				if found and re.search('\d', found.group(1)):
					plz = found.group(1)
					ort = found.group(2)
					break
		else: # only two lines, the second must be the city...
			ort = lines[1].strip()
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

		if re.match('^\+', self.number):
			self.number = '00' + self.number[1:]

		if self.number[:len(countrycode)] == countrycode:
			self.number = '0' + self.number[len(countrycode):]

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
		def cleanName(text):
			try:
				item = text.replace("&nbsp;"," ").replace("</b>","").replace(","," ").replace('\n',' ').replace('\t',' ')
				item = html2unicode(item).decode('iso-8859-1')
				# item = html2unicode(item)
				newitem = item.replace("  ", " ")
				while newitem != item:
					item = newitem
					newitem = item.replace("  ", " ")
				return newitem.strip()
			except:
				return text
	
		debug("[ReverseLookupAndNotifier] _gotPage")
		found = re.match('.*content=".*?charset=([^"]+)"',page,re.S)
		if found:
			debug("[ReverseLookupAndNotifier] Charset: " + found.group(1))
			page = page.replace("\xa0"," ").decode(found.group(1), "replace")
		else:
			page = page.replace("\xa0"," ").decode("ISO-8859-1", "replace")

		for entry in self.currentWebsite.getElementsByTagName("entry"):
			#
			# for the sites delivering fuzzy matches, we check against the returned number
			#
			pat = self.getPattern(entry, "number")
			if pat:
				pat = ".*?" + pat
				debug("[ReverseLookupAndNotifier] _gotPage: look for number with '''%s'''" %( pat ))
				found = re.match(pat, page, re.S|re.M)
				if found:
					if self.number[:2] == '00':
						number = '0' + self.number[4:]
					else:
						number = self.number
					if number != normalizePhoneNumber(found.group(1)):
						debug("[ReverseLookupAndNotifier] _gotPage: got unequal number '''%s''' for '''%s'''" %(found.group(1),self.number))
						continue
			
			# look for <firstname> and <lastname> match, if not there look for <name>, if not there break
			lastname = ''
			firstname = ''
			pat = self.getPattern(entry, "lastname")
			if pat:
				pat = ".*?" + pat
				debug("[ReverseLookupAndNotifier] _gotPage: look for '''%s''' with '''%s'''" %( "lastname", pat ))
				found = re.match(pat, page, re.S|re.M)
				if found:
					debug("[ReverseLookupAndNotifier] _gotPage: found for '''%s''': '''%s'''" %( "lastname", found.group(1)))
					lastname = cleanName(found.group(1))

					pat = self.getPattern(entry, "firstname")
					if pat:
						pat = ".*?" + pat
						debug("[ReverseLookupAndNotifier] _gotPage: look for '''%s''' with '''%s'''" %( "firstname", pat ))
						found = re.match(pat, page, re.S|re.M)
						if found:
							debug("[ReverseLookupAndNotifier] _gotPage: found for '''%s''': '''%s'''" %( "firstname", found.group(1)))
						firstname = cleanName(found.group(1))

					if firstname:
						name = lastname + ' ' + firstname
					else:
						name = lastname
			else:
				pat = ".*?" + self.getPattern(entry, "name")
				debug("[ReverseLookupAndNotifier] _gotPage: look for '''%s''' with '''%s'''" %( "name", pat ))
				found = re.match(pat, page, re.S|re.M)
				if found:
					debug("[ReverseLookupAndNotifier] _gotPage: found for '''%s''': '''%s'''" %( "name", found.group(1)))
					item = cleanName(found.group(1))
					debug("[ReverseLookupAndNotifier] _gotPage: name: " + item)
					name = item
				else:
					debug("[ReverseLookupAndNotifier] _gotPage: no name found, skipping")
					continue

			address = ""
			if name:
				pat = ".*?" + self.getPattern(entry, "city")
				debug("[ReverseLookupAndNotifier] _gotPage: look for '''%s''' with '''%s'''" %( "city", pat ))
				found = re.match(pat, page, re.S|re.M)
				if found:
					debug("[ReverseLookupAndNotifier] _gotPage: found for '''%s''': '''%s'''" %( "city", found.group(1)))
					item = cleanName(found.group(1))
					debug("[ReverseLookupAndNotifier] _gotPage: city: " + item)
					address = item.strip()

					pat = ".*?" + self.getPattern(entry, "zipcode")
					debug("[ReverseLookupAndNotifier] _gotPage: look for '''%s''' with '''%s'''" %( "zipcode", pat ))
					found = re.match(pat, page, re.S|re.M)
					if found and found.group(1):
						debug("[ReverseLookupAndNotifier] _gotPage: found for '''%s''': '''%s'''" %( "zipcode", found.group(1)))
						item = cleanName(found.group(1))
						debug("[ReverseLookupAndNotifier] _gotPage: zipcode: " + item)
						address = item.strip() + ' ' + address

					pat = ".*?" + self.getPattern(entry, "street")
					debug("[ReverseLookupAndNotifier] _gotPage: look for '''%s''' with '''%s'''" %( "street", pat ))
					found = re.match(pat, page, re.S|re.M)
					if found and found.group(1):
						debug("[ReverseLookupAndNotifier] _gotPage: found for '''%s''': '''%s'''" %( "street", found.group(1)))
						item = cleanName(found.group(1))
						debug("[ReverseLookupAndNotifier] _gotPage: street: " + item)
						address = item.strip() + ', ' + address

				if address:
					debug("[ReverseLookupAndNotifier] _gotPage: Reverse lookup succeeded:\nName: %s\nAddress: %s" %(name, address))
					self.caller = "%s, %s" %(name, address)
				else:
					debug("[ReverseLookupAndNotifier] _gotPage: Reverse lookup succeeded:\nName: %s" %(name))
					self.caller = name

				self.notifyAndReset()
				return True
			else:
				continue
		else:
			self._gotError("[ReverseLookupAndNotifier] _gotPage: Nothing found at %s" %self.currentWebsite.getAttribute("name"))
			return False
			
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
		if len(pat1) == 0:
			return ''
		else:
			if len(pat1) > 1:
				debug("[ReverseLookupAndNotifier] getPattern: Something strange: more than one %s for website %s" %(which, website.getAttribute("name")))
			return pat1[0].childNodes[0].data

	def notifyAndReset(self):
		debug("[ReverseLookupAndNotifier] notifyAndReset: Number: " + self.number + "; Caller: " + self.caller)
		# debug("1: " + repr(self.caller))
		if self.caller:
			try:
				# debug("2: " + repr(self.caller))
				self.caller = self.caller.encode(self.charset, 'replace')
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
