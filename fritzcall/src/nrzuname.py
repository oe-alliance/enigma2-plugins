#!/usr/bin/python
# -*- coding: UTF-8 -*-
'''
$Id: nrzuname.py 800 2013-07-21 12:34:08Z michael $
$Author: michael $
$Revision: 800 $
$Date: 2013-07-21 14:34:08 +0200 (Sun, 21 Jul 2013) $
'''

# W0603 (global statement); W0141 (map, filter, etc.)
# pylint: disable=W0603,W0141

import re, sys, os
from xml.dom.minidom import parse
from twisted.web.client import getPage #@UnresolvedImport
from twisted.internet import reactor #@UnresolvedImport

try:
	from . import debug #@UnresolvedImport # pylint: disable=W0613,F0401
	def setDebug(what): # pylint: disable=W0613
		pass
except ValueError:
	debugVal = True
	def setDebug(what):
		global debugVal
		debugVal = what
	def debug(message):
		if debugVal:
			print message

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
		in_html = in_html.replace(x.group(1), '&#' + str(int(x.group(2), 16)) + ';')

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
			uml = unichr(int(codepoint))
			debug("[nrzuname] html2utf8: replace %s with %s in %s" %(repr(key), repr(uml), repr(in_html[0:20]+'...')))
			in_html = in_html.replace(key, uml)
		except ValueError, e:
			debug("[nrzuname] html2utf8: ValueError " + repr(key) + ":" + repr(codepoint) + " (" + str(e) + ")")
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
	found = re.match("NA: ([^;]*);VN: ([^;]*);STR: ([^;]*);HNR: ([^;]*);PLZ: ([^;]*);ORT: ([^;]*)", caller)
	if not found:
		return
	( name, vorname, strasse, hnr, plz, ort ) = (found.group(1),
											found.group(2),
											found.group(3),
											found.group(4),
											found.group(5),
											found.group(6)
											)
	if vorname:
		name += ' ' + vorname
	if strasse or hnr or plz or ort:
		name += ', '
	if strasse:
		name += strasse
	if hnr:
		name += ' ' + hnr
	if (strasse or hnr) and (plz or ort):
		name += ', '
	if plz and ort:
		name += plz + ' ' + ort
	elif plz:
		name += plz
	elif ort:
		name += ort

	print(name)

def simpleout(number, caller): #@UnusedVariable # pylint: disable=W0613
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
		if re.search('$AREACODE', url) or re.search('$PFXAREACODE', url):
			debug("[ReverseLookupAndNotifier] handleWebsite: (PFX)ARECODE cannot be handled")
			# self.caller = _("UNKNOWN")
			self.notifyAndReset()
			return
		#
		# Apparently, there is no attribute called (pfx)areacode anymore
		# So, this below will not work.
		#
		if re.search('\\$AREACODE', url) and website.hasAttribute("areacode"):
			areaCodeLen = int(website.getAttribute("areacode"))
			url = url.replace("$AREACODE", number[:areaCodeLen]).replace("$NUMBER", number[areaCodeLen:])
		elif re.search('\\$PFXAREACODE', url) and website.hasAttribute("pfxareacode"):
			areaCodeLen = int(website.getAttribute("pfxareacode"))
			url = url.replace("$PFXAREACODE","%(pfxareacode)s").replace("$NUMBER", "%(number)s")
			url = url % { 'pfxareacode': number[:areaCodeLen], 'number': number[areaCodeLen:] }
		elif re.search('\\$NUMBER', url): 
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
			item = text.replace("%20"," ").replace("&nbsp;"," ").replace("</b>","").replace(","," ").replace('\n',' ').replace('\t',' ')

			item = html2unicode(item)
			#===================================================================
			# try: # this works under Windows
			#	item = item.encode('iso-8859-1')
			# except UnicodeEncodeError:
			#	debug("[ReverseLookupAndNotifier] cleanName: encoding problem with iso8859")
			#	try: # this works under Enigma2
			#		item = item.encode('utf-8')
			#	except UnicodeEncodeError:
			#		debug("[ReverseLookupAndNotifier] cleanName: encoding problem with utf-8")
			#		try: # fall back
			#			item = item.encode(self.charset)
			#		except UnicodeEncodeError:
			#			# debug("[ReverseLookupAndNotifier] cleanName: " + traceback.format_exc())
			#			debug("[ReverseLookupAndNotifier] cleanName: encoding problem")
			#===================================================================

			newitem = item.replace("  ", " ")
			while newitem != item:
				item = newitem
				newitem = item.replace("  ", " ")
			return newitem.strip()
	
		debug("[ReverseLookupAndNotifier] _gotPage")

		#=======================================================================
		# userDesktop = os.path.join(os.environ['USERPROFILE'], "Desktop")
		# linkP =  open(os.path.join(userDesktop, "page.htm"), "w")
		# linkP.write(page)
		# linkP.close()
		#=======================================================================

		found = re.match('.*<meta http-equiv="Content-Type" content="(?:application/xhtml\+xml|text/html); charset=([^"]+)" />', page, re.S)
		if found:
			debug("[ReverseLookupAndNotifier] Charset: " + found.group(1))
			page = page.replace("\xa0"," ").decode(found.group(1), "replace")
		else:
			debug("[ReverseLookupAndNotifier] Default Charset: iso-8859-1")
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
						debug("[ReverseLookupAndNotifier] _gotPage: got unequal number '''%s''' for '''%s'''" %(found.group(1), self.number))
						continue
			
			# look for <firstname> and <lastname> match, if not there look for <name>, if not there break
			name = ''
			firstname = ''
			street = ''
			streetno = ''
			city = ''
			zipcode = ''
			pat = self.getPattern(entry, "lastname")
			if pat:
				pat = ".*?" + pat
				debug("[ReverseLookupAndNotifier] _gotPage: look for '''%s''' with '''%s'''" %( "lastname", pat ))
				found = re.match(pat, page, re.S|re.M)
				if found:
					debug("[ReverseLookupAndNotifier] _gotPage: found for '''%s''': '''%s'''" %( "lastname", found.group(1)))
					name = cleanName(found.group(1))

					pat = self.getPattern(entry, "firstname")
					if pat:
						pat = ".*?" + pat
						debug("[ReverseLookupAndNotifier] _gotPage: look for '''%s''' with '''%s'''" %( "firstname", pat ))
						found = re.match(pat, page, re.S|re.M)
						if found:
							debug("[ReverseLookupAndNotifier] _gotPage: found for '''%s''': '''%s'''" %( "firstname", found.group(1)))
						firstname = cleanName(found.group(1)).strip()

			else:
				pat = ".*?" + self.getPattern(entry, "name")
				debug("[ReverseLookupAndNotifier] _gotPage: look for '''%s''' with '''%s'''" %( "name", pat ))
				found = re.match(pat, page, re.S|re.M)
				if found:
					debug("[ReverseLookupAndNotifier] _gotPage: found for '''%s''': '''%s'''" %( "name", found.group(1)))
					item = cleanName(found.group(1))
					# debug("[ReverseLookupAndNotifier] _gotPage: name: " + item)
					name = item.strip()
					firstNameFirst = entry.getElementsByTagName('name')[0].getAttribute('swapFirstAndLastName')
					# debug("[ReverseLookupAndNotifier] _gotPage: swapFirstAndLastName: " + firstNameFirst)
					if firstNameFirst == 'true': # that means, the name is of the form "firstname lastname"
						found = re.match('(.*?)\s+(.*)', name)
						if found:
							firstname = found.group(1)
							name = found.group(2)
				else:
					debug("[ReverseLookupAndNotifier] _gotPage: no name found, skipping")
					continue

			if not name:
				continue

			pat = ".*?" + self.getPattern(entry, "city")
			debug("[ReverseLookupAndNotifier] _gotPage: look for '''%s''' with '''%s'''" %( "city", pat ))
			found = re.match(pat, page, re.S|re.M)
			if found:
				debug("[ReverseLookupAndNotifier] _gotPage: found for '''%s''': '''%s'''" %( "city", found.group(1)))
				item = cleanName(found.group(1))
				debug("[ReverseLookupAndNotifier] _gotPage: city: " + item)
				city = item.strip()

			if not city:
				continue

			pat = ".*?" + self.getPattern(entry, "zipcode")
			debug("[ReverseLookupAndNotifier] _gotPage: look for '''%s''' with '''%s'''" %( "zipcode", pat ))
			found = re.match(pat, page, re.S|re.M)
			if found and found.group(1):
				debug("[ReverseLookupAndNotifier] _gotPage: found for '''%s''': '''%s'''" %( "zipcode", found.group(1)))
				item = cleanName(found.group(1))
				debug("[ReverseLookupAndNotifier] _gotPage: zipcode: " + item)
				zipcode = item.strip()

			pat = ".*?" + self.getPattern(entry, "street")
			debug("[ReverseLookupAndNotifier] _gotPage: look for '''%s''' with '''%s'''" %( "street", pat ))
			found = re.match(pat, page, re.S|re.M)
			if found and found.group(1):
				debug("[ReverseLookupAndNotifier] _gotPage: found for '''%s''': '''%s'''" %( "street", found.group(1)))
				item = cleanName(found.group(1))
				debug("[ReverseLookupAndNotifier] _gotPage: street: " + item)
				street = item.strip()
				streetno = ''
				found = re.match("^(.+) ([-\d]+)$", street, re.S)
				if found:
					street = found.group(1)
					streetno = found.group(2)
				#===============================================================
				# else:
				#	found = re.match("^(\d+) (.+)$", street, re.S)
				#	if found:
				#		street = found.group(2)
				#		streetno = found.group(1)
				#===============================================================

			self.caller = "NA: %s;VN: %s;STR: %s;HNR: %s;PLZ: %s;ORT: %s" % ( name, firstname, street, streetno, zipcode, city )
			debug("[ReverseLookupAndNotifier] _gotPage: Reverse lookup succeeded:\nName: %s" %(self.caller))

			self.notifyAndReset()
			return True
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
				debug("2: " + repr(self.caller))
				self.caller = self.caller.encode(self.charset, 'replace')
				debug("3: " + repr(self.caller))
			except UnicodeDecodeError:
				debug("[ReverseLookupAndNotifier] cannot encode?!?!")
			# self.caller = unicode(self.caller)
			# debug("4: " + repr(self.caller))
			self.outputFunction(self.number, self.caller)
		else:
			self.outputFunction(self.number, "")
		if __name__ == '__main__':
			reactor.stop() #@UndefinedVariable # pylint: disable=E1101

if __name__ == '__main__':
	cwd = os.path.dirname(sys.argv[0])
	if (len(sys.argv) == 2):
		# nrzuname.py Nummer
		ReverseLookupAndNotifier(sys.argv[1], simpleout)
		reactor.run() #@UndefinedVariable # pylint: disable=E1101
	elif (len(sys.argv) == 3):
		# nrzuname.py Nummer Charset
		setDebug(False)
		ReverseLookupAndNotifier(sys.argv[1], out, sys.argv[2])
		reactor.run() #@UndefinedVariable # pylint: disable=E1101
