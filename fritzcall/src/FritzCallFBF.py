# -*- coding: utf-8 -*-
'''
Created on 30.09.2012
$Author: michael $
$Revision: 1386 $
$Date: 2017-01-19 18:16:38 +0100 (Thu, 19 Jan 2017) $
$Id: FritzCallFBF.py 1386 2017-01-19 17:16:38Z michael $
'''

# C0111 (Missing docstring)
# C0103 (Invalid name)
# C0301 (line too long)
# W0603 (global statement)
# W0141 (map, filter, etc.)
# W0110 lambda with map,filter
# W0403 Relative import
# W1401 Anomalous backslash in string
# W0110 deprecated-lambda
# C0302 too-many-lines
# C0410 multiple-imports
# pylint: disable=C0111,C0103,C0301,W0603,W0403,C0302

from urllib import urlencode
import re, time, hashlib, logging, StringIO, csv
import json
import xml.etree.ElementTree as ET


from Tools import Notifications
from Screens.MessageBox import MessageBox
from twisted.web.client import getPage  # @UnresolvedImport

from plugin import config, stripCbCPrefix, resolveNumberWithAvon, FBF_IN_CALLS, FBF_OUT_CALLS, FBF_MISSED_CALLS, FBF_BLOCKED_CALLS, decode
from nrzuname import html2unicode
from . import _, __  # @UnresolvedImport # pylint: disable=W0611,F0401
# debug = logging.getLogger(__name__ + "XXX").debug
# debug = logging.getLogger(__name__).debug

FBF_boxInfo = 0
FBF_upTime = 1
FBF_ipAddress = 2
FBF_wlanState = 3
FBF_dslState = 4
FBF_tamActive = 5
FBF_dectActive = 6
FBF_faxActive = 7
FBF_rufumlActive = 8

USERAGENT = "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"


def resolveNumber(number, default=None, phonebook=None):
	if number.isdigit():
		if config.plugins.FritzCall.internal.value and len(number) > 3 and number[0] == "0":
			number = number[1:]
		# strip CbC prefix
		number = stripCbCPrefix(number, config.plugins.FritzCall.country.value)
		if config.plugins.FritzCall.prefix.value and number and number[0] != '0':  # should only happen for outgoing
			number = config.plugins.FritzCall.prefix.value + number
		name = None
		if phonebook:
			name = phonebook.search(number, default)
		if name:
			#
			# found = re.match(r'(.*?)\n.*', name)
			# if found:
			# 	name = found.group(1)
			#
			end = name.find('\n')
			if end != -1:
				name = name[:end]
			number = name
		elif default:
			number = default
		else:
			name = resolveNumberWithAvon(number, config.plugins.FritzCall.country.value)
			if name:
				number = number + ' ' + name
	elif number == "":
		number = _("UNKNOWN")
	# if len(number) > 20: number = number[:20]
	return number

def cleanNumber(number):
	# self.debug("[FritzCallFBF] " + number)
	number = re.sub("<.*?>", "", number)
	newNumber = (" ".join(re.findall(r"[+0-9*#ABCD]*", number))).replace(" ", "")
	if len(newNumber) == 0:
		return number
	else:
		number = newNumber
	if number[0] == '+':
		number = '00' + number[1:]
	elif number[0] != '0':
		number = config.plugins.FritzCall.prefix.value + number
	if config.plugins.FritzCall.country.value and number.startswith(config.plugins.FritzCall.country.value):
		number = '0' + number[len(config.plugins.FritzCall.country.value):]
	return number

class FritzCallFBF(object):
	logger = logging.getLogger("FritzCallFBF.old")
	debug = logger.debug

	def __init__(self):
		self.debug("")
		self._callScreen = None
		self._md5LoginTimestamp = None
		self._md5Sid = '0000000000000000'
		self._callTimestamp = 0
		self._callList = []
		self._callType = config.plugins.FritzCall.fbfCalls.value
		self.password = decode(config.plugins.FritzCall.password.value)
		self.information = (None, None, None, None, None, [False, False, False, False, False, False], None, None, None, None)
		self.getInfo(None)
		self.blacklist = ([], [])
		self.readBlacklist()
		self.phonebook = None
		self._phoneBookID = 0
		self.phonebooksFBF = []

	def _notify(self, text):
		self.debug(text)
		self._md5LoginTimestamp = None
		if self._callScreen:
			self.debug("try to close callScreen")
			self._callScreen.close()
			self._callScreen = None
		Notifications.AddNotification(MessageBox, text, type=MessageBox.TYPE_ERROR, timeout=config.plugins.FritzCall.timeout.value)

	def _login(self, callback=None):
		self.debug("")
		if self._callScreen:
			self._callScreen.updateStatus(_("login"))
		if self._md5LoginTimestamp and ((time.time() - self._md5LoginTimestamp) < float(9.5 * 60)) and self._md5Sid != '0000000000000000':  # new login after 9.5 minutes inactivity
			self.debug("[FritzCallFBF] renew timestamp: " + time.ctime(self._md5LoginTimestamp) + " time: " + time.ctime())
			self._md5LoginTimestamp = time.time()
			callback(None)
		else:
			self.debug("not logged in or outdated login")
			# http://fritz.box/cgi-bin/webcm?getpage=../html/login_sid.xml
			parms = urlencode({'getpage': '../html/login_sid.xml'})
			url = "http://%s/cgi-bin/webcm" % (config.plugins.FritzCall.hostname.value)
			self.debug("'" + url + "' parms: '" + parms + "'")
			getPage(url,
				method="POST",
				headers={'Content-Type': "application/x-www-form-urlencoded", 'Content-Length': str(len(parms))},
				postdata=parms).addCallback(lambda x: self._md5Login(callback, x)).addErrback(lambda x: self._oldLogin(callback, x))

	def _oldLogin(self, callback, error):
		self.debug(repr(error))
		self._md5LoginTimestamp = None
		if self.password != "":
			parms = "login:command/password=%s" % self.password
			url = "http://%s/cgi-bin/webcm" % (config.plugins.FritzCall.hostname.value)
			self.debug("'" + url + "' parms: '" + parms + "'")
			getPage(url,
				method="POST",
				agent=USERAGENT,
				headers={'Content-Type': "application/x-www-form-urlencoded", 'Content-Length': str(len(parms))},
				postdata=parms).addCallback(self._gotPageLogin).addCallback(callback).addErrback(self._errorLogin)
		elif callback:
			self.debug("no password, calling " + repr(callback))
			callback(None)

	def _md5Login(self, callback, sidXml):
		def buildResponse(challenge, text):
			self.debug("_md5Login: challenge: " + challenge + ' text: ' + __(text))
			text = (challenge + '-' + text).decode('utf-8', 'ignore').encode('utf-16-le')
			for i in range(len(text)):  # consider-using-enumerate # pylint: disable=
				if ord(text[i]) > 255:
					text[i] = '.'
			md5 = hashlib.md5()
			md5.update(text)  # pylint: disable=E1101
			self.debug("md5Login: " + md5.hexdigest())
			return challenge + '-' + md5.hexdigest()

		self.debug("")
		found = re.match(r'.*<SID>([^<]*)</SID>', sidXml, re.S)
		if found:
			self._md5Sid = found.group(1)
			self.debug("SID " + self._md5Sid)
		else:
			self.debug("no sid! That must be an old firmware.")
			self._oldLogin(callback, 'No error')
			return

		self.debug("renew timestamp: " + time.ctime(self._md5LoginTimestamp) + " time: " + time.ctime())
		self._md5LoginTimestamp = time.time()
		if sidXml.find('<iswriteaccess>0</iswriteaccess>') != -1:
			self.debug("logging in")
			found = re.match(r'.*<Challenge>([^<]*)</Challenge>', sidXml, re.S)
			if found:
				challenge = found.group(1)
				self.debug("challenge " + challenge)
			else:
				challenge = None
				self.debug("login necessary and no challenge! That is terribly wrong.")
			parms = urlencode({
							'getpage': '../html/de/menus/menu2.html',  # 'var:pagename':'home', 'var:menu':'home',
							'login:command/response': buildResponse(challenge, decode(config.plugins.FritzCall.password.value)),
							})
			url = "http://%s/cgi-bin/webcm" % (config.plugins.FritzCall.hostname.value)
			self.debug("'" + url + "' parms: '" + parms + "'")
			getPage(url,
				method="POST",
				agent=USERAGENT,
				headers={'Content-Type': "application/x-www-form-urlencoded", 'Content-Length': str(len(parms))},
				postdata=parms).addCallback(self._gotPageLogin).addCallback(callback).addErrback(self._errorLogin)
		elif callback:  # we assume value 1 here, no login necessary
			self.debug("no login necessary")
			callback(None)

	def _gotPageLogin(self, html):
		if self._callScreen:
			self._callScreen.updateStatus(_("login verification"))
		self.debug("verify login")
		start = html.find('<p class="errorMessage">FEHLER:&nbsp;')
		if start != -1:
			start = start + len('<p class="errorMessage">FEHLER:&nbsp;')
			text = _("FRITZ!Box - Error logging in\n\n") + html[start: html.find('</p>', start)]
			self._notify(text)
		else:
			if self._callScreen:
				self._callScreen.updateStatus(_("login ok"))

		found = re.match(r'.*<input type="hidden" name="sid" value="([^\"]*)"', html, re.S)
		if found:
			self._md5Sid = found.group(1)
			self.debug("found sid: " + self._md5Sid)

	def _errorLogin(self, error):
		global fritzbox  # global-variable-undefined # pylint: disable=W0601
		self.debug(error)
		text = _("FRITZ!Box - Error logging in: %s\nDisabling plugin.") % error.getErrorMessage()
		fritzbox = None
		self._notify(text)

	def _logout(self):
		if self._md5LoginTimestamp:
			self._md5LoginTimestamp = None
			parms = urlencode({
							'getpage': '../html/de/menus/menu2.html',  # 'var:pagename':'home', 'var:menu':'home',
							'login:command/logout': 'bye bye Fritz'
							})
			url = "http://%s/cgi-bin/webcm" % (config.plugins.FritzCall.hostname.value)
			self.debug("'" + url + "' parms: '" + parms + "'")
			getPage(url,
				method="POST",
				agent=USERAGENT,
				headers={'Content-Type': "application/x-www-form-urlencoded", 'Content-Length': str(len(parms))},
				postdata=parms).addErrback(self._errorLogout)

	def _errorLogout(self, error):
		self.debug(error)
		text = _("FRITZ!Box - Error logging out: %s") % error.getErrorMessage()
		self._notify(text)

	def loadFritzBoxPhonebook(self, phonebook):
		self.debug("")
		if config.plugins.FritzCall.fritzphonebook.value:
			self.phonebook = phonebook
			self._phoneBookID = '0'
			self.debug("logging in")
			self._login(self._loadFritzBoxPhonebook)

	def _loadFritzBoxPhonebook(self, html):
		if html:
			#===================================================================
			# found = re.match(r'.*<p class="errorMessage">FEHLER:&nbsp;([^<]*)</p>', html, re.S)
			# if found:
			# 	self._errorLoad('Login: ' + found.group(1))
			# 	return
			#===================================================================
			start = html.find('<p class="errorMessage">FEHLER:&nbsp;')
			if start != -1:
				start = start + len('<p class="errorMessage">FEHLER:&nbsp;')
				self._notify('Login: ' + html[start, html.find('</p>', start)])
				return
		parms = urlencode({
						'getpage': '../html/de/menus/menu2.html',
						'var:lang': 'de',
						'var:pagename': 'fonbuch',
						'var:menu': 'fon',
						'sid': self._md5Sid,
						'telcfg:settings/Phonebook/Books/Select': self._phoneBookID,  # this selects always the first phonbook first
						})
		url = "http://%s/cgi-bin/webcm" % (config.plugins.FritzCall.hostname.value)
		self.debug("'" + url + "' parms: '" + parms + "'")
		getPage(url,
			method="POST",
			agent=USERAGENT,
			headers={'Content-Type': "application/x-www-form-urlencoded", 'Content-Length': str(len(parms))},
			postdata=parms).addCallback(self._parseFritzBoxPhonebook).addErrback(self._errorLoad)

	def _parseFritzBoxPhonebook(self, html):

		# self.debug("")

		# first, let us get the charset
		found = re.match(r'.*<meta http-equiv=content-type content="text/html; charset=([^"]*)">', html, re.S)
		if found:
			charset = found.group(1)
			self.debug("found charset: " + charset)
			html = html2unicode(html.replace(chr(0xf6), '').decode(charset)).encode('utf-8')
		else:  # this is kind of emergency conversion...
			try:
				self.debug("try charset utf-8")
				charset = 'utf-8'
				html = html2unicode(html.decode('utf-8')).encode('utf-8')  # this looks silly, but has to be
			except UnicodeDecodeError:
				self.debug("try charset iso-8859-1")
				charset = 'iso-8859-1'
				html = html2unicode(html.decode('iso-8859-1')).encode('utf-8')  # this looks silly, but has to be

		# if re.search('document.write\(TrFon1\(\)', html):
		if html.find('document.write(TrFon1()') != -1:
			#===============================================================================
			# 				 New Style: 7270 (FW 54.04.58, 54.04.63-11941, 54.04.70, 54.04.74-14371, 54.04.76, PHONE Labor 54.04.80-16624)
			# 							7170 (FW 29.04.70) 22.03.2009
			# 							7141 (FW 40.04.68) 22.03.2009
			#  We expect one line with
			#   TrFonName(Entry umber, Name, ???, Path to picture)
			#  followed by several lines with
			# 	TrFonNr(Type,Number,Shortcut,Vanity), which all belong to the name in TrFonName.
			#
			#  Photo could be fetched with http://192.168.0.1/lua/photo.lua?photo=<Path to picture[7:]&sid=????
			#===============================================================================
			self.debug("discovered newer firmware")
			found = re.match(r'.*<input type="hidden" name="telcfg:settings/Phonebook/Books/Name\d+" value="(?:' + config.plugins.FritzCall.fritzphonebookName.value + r')" id="uiPostPhonebookName\d+" disabled>\s*<input type="hidden" name="telcfg:settings/Phonebook/Books/Id\d+" value="(\d+)" id="uiPostPhonebookId\d+" disabled>', html, re.S)
			if found:
				phoneBookID = found.group(1)
				self.debug("found dreambox phonebook with id: " + phoneBookID)
				if self._phoneBookID != phoneBookID:
					self._phoneBookID = phoneBookID
					self.debug("reload phonebook")
					self._loadFritzBoxPhonebook(None)  # reload with dreambox phonebook
					return

			entrymask = re.compile(r'(TrFonName\("[^"]+", "[^"]+", "[^"]*"(?:, "[^"]*")?\);.*?)document.write\(TrFon1\(\)', re.S)
			entries = entrymask.finditer(html)
			for entry in entries:
				# TrFonName (id, name, category)
				found = re.match(r'TrFonName\("[^"]*", "([^"]+)", "[^"]*"(?:, "[^"]*")?\);', entry.group(1))
				if found:
					# self.debug("name: %s" %found.group(1))
					name = found.group(1).replace(',', '').strip()
				else:
					self.debug("could not find name")
					continue
				# TrFonNr (type, rufnr, code, vanity)
				detailmask = re.compile(r'TrFonNr\("([^"]*)", "([^"]*)", "([^"]*)", "([^"]*)"\);', re.S)
				details = detailmask.finditer(entry.group(1))
				for found in details:
					thisnumber = found.group(2).strip()
					if not thisnumber:
						self.debug("Ignoring entry with empty number for '''%s'''", __(name))
						continue
					else:
						thisname = name
						callType = found.group(1)
						if config.plugins.FritzCall.showType.value:
							if callType == "mobile":
								thisname = thisname + " (" + _("mobile") + ")"
							elif callType == "home":
								thisname = thisname + " (" + _("home") + ")"
							elif callType == "work":
								thisname = thisname + " (" + _("work") + ")"

						if config.plugins.FritzCall.showShortcut.value and found.group(3):
							thisname = thisname + ", " + _("Shortcut") + ": " + found.group(3)
						if config.plugins.FritzCall.showVanity.value and found.group(4):
							thisname = thisname + ", " + _("Vanity") + ": " + found.group(4)

						thisnumber = cleanNumber(thisnumber)
						# Beware: strings in phonebook.phonebook have to be in utf-8!
						if thisnumber in self.phonebook.phonebook:
							pass
							# self.debug("Ignoring '''%s''' with '''%s'''" % (thisname.strip(), thisnumber))
						else:
							# self.debug("Adding '''%s''' with '''%s'''" % (__(thisname.strip()), __(thisnumber, False)))
							self.phonebook.phonebook[thisnumber] = thisname

		# elif re.search('document.write\(TrFon\(', html):
		elif html.find('document.write(TrFon(') != -1:
			#===============================================================================
			# 				Old Style: 7050 (FW 14.04.33)
			# 	We expect one line with TrFon(No,Name,Number,Shortcut,Vanity)
			#   Encoding should be plain Ascii...
			#===============================================================================
			entrymask = re.compile(r'TrFon\("[^"]*", "([^"]*)", "([^"]*)", "([^"]*)", "([^"]*)"\)', re.S)
			entries = entrymask.finditer(html)
			for found in entries:
				name = found.group(1).strip().replace(',', '')
				# self.debug("pos: %s name: %s" %(found.group(0),name))
				thisnumber = found.group(2).strip()
				if config.plugins.FritzCall.showShortcut.value and found.group(3):
					name = name + ", " + _("Shortcut") + ": " + found.group(3)
				if config.plugins.FritzCall.showVanity.value and found.group(4):
					name = name + ", " + _("Vanity") + ": " + found.group(4)
				if thisnumber:
					# name = name.encode('utf-8')
					# Beware: strings in phonebook.phonebook have to be in utf-8!
					if thisnumber in self.phonebook.phonebook:
						self.debug("Ignoring '''%s''' with '''%s'''", __(name), __(thisnumber))
					else:
						# self.debug("Adding '''%s''' with '''%s'''" % (name, __(thisnumber)))
						self.phonebook.phonebook[thisnumber] = name
				else:
					self.debug("ignoring empty number for %s", name)
				continue
		elif self._md5Sid == '0000000000000000':  # retry, it could be a race condition
			self.debug("retry loading phonebook")
			self.loadFritzBoxPhonebook(self.phonebook)
		else:
			self.debug("could not read FBF phonebook; wrong version?")
			self._notify(_("Could not read FRITZ!Box phonebook; wrong version?"))

	def _errorLoad(self, error):
		self.debug(error)
		text = _("FRITZ!Box - ") + _("Could not load phonebook: %s") % error.getErrorMessage()
		self._notify(text)

	def getCalls(self, callScreen, callback, callType):
		#
		# call sequence must be:
		# - login
		# - getPage -> _gotPageLogin
		# - loginCallback (_getCalls)
		# - getPage -> _getCalls1
		self.debug("")
		self._callScreen = callScreen
		self._callType = callType
		if (time.time() - self._callTimestamp) > 180:
			self.debug("outdated data, login and get new ones: " + time.ctime(self._callTimestamp) + " time: " + time.ctime())
			self._callTimestamp = time.time()
			self._login(lambda x: self._getCalls(callback, x))
		elif not self._callList:
			self.debug("time is ok, but no callList")
			self._getCalls1(callback)
		else:
			self.debug("time is ok, callList is ok")
			self._gotPageCalls(callback)

	def _getCalls(self, callback, html):
		if html:
			#===================================================================
			# found = re.match(r'.*<p class="errorMessage">FEHLER:&nbsp;([^<]*)</p>', html, re.S)
			# if found:
			# 	self._errorCalls('Login: ' + found.group(1))
			# 	return
			#===================================================================
			start = html.find('<p class="errorMessage">FEHLER:&nbsp;')
			if start != -1:
				start = start + len('<p class="errorMessage">FEHLER:&nbsp;')
				self._notify('Login: ' + html[start, html.find('</p>', start)])
				return
		#
		# we need this to fill Anrufliste.csv
		# http://repeater1/cgi-bin/webcm?getpage=../html/de/menus/menu2.html&var:lang=de&var:menu=fon&var:pagename=foncalls
		#
		self.debug("")
		if html:
			#===================================================================
			# found = re.match(r'.*<p class="errorMessage">FEHLER:&nbsp;([^<]*)</p>', html, re.S)
			# if found:
			# 	text = _("FRITZ!Box - Error logging in: %s") + found.group(1)
			# 	self._notify(text)
			# 	return
			#===================================================================
			start = html.find('<p class="errorMessage">FEHLER:&nbsp;')
			if start != -1:
				start = start + len('<p class="errorMessage">FEHLER:&nbsp;')
				self._notify(_("FRITZ!Box - Error logging in: %s") + html[start, html.find('</p>', start)])
				return

		if self._callScreen:
			self._callScreen.updateStatus(_("preparing"))
		parms = urlencode({'getpage': '../html/de/menus/menu2.html', 'var:lang': 'de', 'var:pagename': 'foncalls', 'var:menu': 'fon', 'sid': self._md5Sid})
		url = "http://%s/cgi-bin/webcm?%s" % (config.plugins.FritzCall.hostname.value, parms)
		getPage(url).addCallback(lambda x: self._getCalls1(callback)).addErrback(self._errorCalls)  # @UnusedVariable # pylint: disable=W0613

	def _getCalls1(self, callback):
		#
		# finally we should have successfully lgged in and filled the csv
		#
		self.debug("")
		if self._callScreen:
			self._callScreen.updateStatus(_("finishing"))
		parms = urlencode({'getpage': '../html/de/FRITZ!Box_Anrufliste.csv', 'sid': self._md5Sid})
		url = "http://%s/cgi-bin/webcm?%s" % (config.plugins.FritzCall.hostname.value, parms)
		getPage(url).addCallback(lambda x: self._gotPageCalls(callback, x)).addErrback(self._errorCalls)

	def _gotPageCalls(self, callback, csvIn=""):

		if csvIn:
			self.debug("got csv, setting callList")
			if self._callScreen:
				self._callScreen.updateStatus(_("done"))
			if csvIn.find('Melden Sie sich mit dem Kennwort der FRITZ!Box an') != -1:
				text = _("You need to set the password of the FRITZ!Box\nin the configuration dialog to display calls\n\nIt could be a communication issue, just try again.")
				# self.session.open(MessageBox, text, MessageBox.TYPE_ERROR, timeout=config.plugins.FritzCall.timeout.value)
				self._notify(text)
				return

			csvIn = csvIn.decode('iso-8859-1', 'replace').encode('utf-8', 'replace')
			lines = csvIn.splitlines()
			self._callList = lines
		elif self._callList:
			self.debug("got no csv, but have callList")
			if self._callScreen:
				self._callScreen.updateStatus(_("done, using last list"))
			lines = self._callList
		else:
			self.debug("Could not get call list; wrong version?")
			self._notify(_("Could not get call list; wrong version?"))
			return

		callListL = []
		if config.plugins.FritzCall.filter.value and config.plugins.FritzCall.filterCallList.value:
			filtermsns = [x.strip() for x in config.plugins.FritzCall.filtermsn.value.split(",")]
			self.debug("filtermsns %s", repr(map(__, filtermsns)))

		# Typ;Datum;Name;Rufnummer;Nebenstelle;Eigene Rufnummer;Dauer
		# 0  ;1	   ;2   ;3		  ;4		  ;5			   ;6
		lines = [line.split(';') for line in lines]
		lines = [line for line in lines if len(line) == 7 and (line[0] == "Typ" or self._callType == '.' or line[0] == self._callType)]
		# lines = filter(lambda line: (len(line) == 7 and (line[0] == "Typ" or self._callType == '.' or line[0] == self._callType)), lines)

		for line in lines:
			# self.debug("line %s" % (line))
			direct = line[0]
			date = line[1]
			length = line[6]
			if config.plugins.FritzCall.phonebook.value and line[2]:
				remote = resolveNumber(line[3], line[2] + " (FBF)", self.phonebook)
			else:
				remote = resolveNumber(line[3], line[2], self.phonebook)
			here = line[5]
			start = here.find('Internet: ')
			if start != -1:
				start += len('Internet: ')
				here = here[start:]
			else:
				here = line[5]
			if direct != "Typ" and config.plugins.FritzCall.filter.value and config.plugins.FritzCall.filterCallList.value:
				# self.debug("check %s" % (here))
				if here not in filtermsns:
					# self.debug("skip %s" % (here))
					continue
			here = resolveNumber(here, line[4], self.phonebook)

			number = stripCbCPrefix(line[3], config.plugins.FritzCall.country.value)
			if config.plugins.FritzCall.prefix.value and number and number[0] != '0':  # should only happen for outgoing
				number = config.plugins.FritzCall.prefix.value + number
			callListL.append((number, date, direct, remote, length, here))

		if callback:
			# self.debug("call callback with\n" + repr(callListL))
			callback(callListL)
		self._callScreen = None

	def _errorCalls(self, error):
		self.debug(error)
		text = _("FRITZ!Box - Could not load calls: %s") % error.getErrorMessage()
		self._notify(text)

	def dial(self, number):
		''' initiate a call to number '''
		self._login(lambda x: self._dial(number, x))

	def _dial(self, number, html):
		if html:
			#===================================================================
			# found = re.match(r'.*<p class="errorMessage">FEHLER:&nbsp;([^<]*)</p>', html, re.S)
			# if found:
			# 	self._errorDial('Login: ' + found.group(1))
			# 	return
			#===================================================================
			start = html.find('<p class="errorMessage">FEHLER:&nbsp;')
			if start != -1:
				start = start + len('<p class="errorMessage">FEHLER:&nbsp;')
				self._errorDial('Login: ' + html[start, html.find('</p>', start)])
				return
		url = "http://%s/cgi-bin/webcm" % config.plugins.FritzCall.hostname.value
		parms = urlencode({
			'getpage': '../html/de/menus/menu2.html',
			'var:pagename': 'fonbuch',
			'var:menu': 'home',
			'telcfg:settings/UseClickToDial': '1',
			'telcfg:settings/DialPort': config.plugins.FritzCall.extension.value,
			'telcfg:command/Dial': number,
			'sid': self._md5Sid
			})
		self.debug("url: '" + url + "' parms: '" + parms + "'")
		getPage(url,
			method="POST",
			agent=USERAGENT,
			headers={
					'Content-Type': "application/x-www-form-urlencoded",
					'Content-Length': str(len(parms))},
			postdata=parms).addCallback(self._okDial).addErrback(self._errorDial)

	def _okDial(self, html):  # @UnusedVariable # pylint: disable=W0613
		self.debug("")

	def _errorDial(self, error):
		self.debug(error)
		text = _("FRITZ!Box - Dialling failed: %s") % error.getErrorMessage()
		self._notify(text)

	def changeWLAN(self, statusWLAN, callback):
		''' get status information from FBF '''
		self.debug("")
		if not statusWLAN or (statusWLAN != '1' and statusWLAN != '0'):
			return
		self._login(lambda x: self._changeWLAN(statusWLAN, callback, x))

	def _changeWLAN(self, statusWLAN, callback, html):
		if html:
			#===================================================================
			# found = re.match(r'.*<p class="errorMessage">FEHLER:&nbsp;([^<]*)</p>', html, re.S)
			# if found:
			# 	self._errorChangeWLAN('Login: ' + found.group(1))
			# 	return
			#===================================================================
			start = html.find('<p class="errorMessage">FEHLER:&nbsp;')
			if start != -1:
				start = start + len('<p class="errorMessage">FEHLER:&nbsp;')
				self._errorChangeWLAN(callback, 'Login: ' + html[start, html.find('</p>', start)])
				return
		url = "http://%s/cgi-bin/webcm" % config.plugins.FritzCall.hostname.value
		parms = urlencode({
			'getpage': '../html/de/menus/menu2.html',
			'var:lang': 'de',
			'var:pagename': 'wlan',
			'var:menu': 'wlan',
			'wlan:settings/ap_enabled': str(statusWLAN),
			'sid': self._md5Sid
			})
		self.debug("url: '" + url + "' parms: '" + parms + "'")
		getPage(url,
			method="POST",
			agent=USERAGENT,
			headers={
					'Content-Type': "application/x-www-form-urlencoded",
					'Content-Length': str(len(parms))},
			postdata=parms).addCallback(self._okChangeWLAN, callback).addErrback(self._errorChangeWLAN, callback)

	def _okChangeWLAN(self, callback, html):  # @UnusedVariable # pylint: disable=W0613
		self.debug("")
		callback()

	def _errorChangeWLAN(self, callback, error):
		self.debug(error)
		text = _("FRITZ!Box - Failed changing WLAN: %s") % error.getErrorMessage()
		self._notify(text)
		callback()

	def changeMailbox(self, whichMailbox, callback):
		''' switch mailbox on/off '''
		self.debug("start: " + str(whichMailbox))
		self._login(lambda x: self._changeMailbox(whichMailbox, callback, x))

	def _changeMailbox(self, whichMailbox, callback, html):
		if html:
			#===================================================================
			# found = re.match(r'.*<p class="errorMessage">FEHLER:&nbsp;([^<]*)</p>', html, re.S)
			# if found:
			# 	self._errorChangeMailbox('Login: ' + found.group(1))
			# 	return
			#===================================================================
			start = html.find('<p class="errorMessage">FEHLER:&nbsp;')
			if start != -1:
				start = start + len('<p class="errorMessage">FEHLER:&nbsp;')
				self._errorChangeMailbox(callback, 'Login: ' + html[start, html.find('</p>', start)])
				return
		self.debug("")
		url = "http://%s/cgi-bin/webcm" % config.plugins.FritzCall.hostname.value
		if whichMailbox == -1:
			for i in range(5):
				if self.information[FBF_tamActive][i + 1]:
					state = '0'
				else:
					state = '1'
				parms = urlencode({
					'tam:settings/TAM' + str(i) + '/Active': state,
					'sid': self._md5Sid
					})
				self.debug("url: '" + url + "' parms: '" + parms + "'")
				getPage(url,
					method="POST",
					agent=USERAGENT,
					headers={
							'Content-Type': "application/x-www-form-urlencoded",
							'Content-Length': str(len(parms))},
					postdata=parms).addCallback(self._okChangeMailbox, callback).addErrback(self._errorChangeMailbox, callback)
		elif whichMailbox > 4:
			self.debug("invalid mailbox number")
		else:
			if self.information[FBF_tamActive][whichMailbox + 1]:
				state = '0'
			else:
				state = '1'
			parms = urlencode({
				'tam:settings/TAM' + str(whichMailbox) + '/Active': state,
				'sid': self._md5Sid
				})
			self.debug("url: '" + url + "' parms: '" + parms + "'")
			getPage(url,
				method="POST",
				agent=USERAGENT,
				headers={
						'Content-Type': "application/x-www-form-urlencoded",
						'Content-Length': str(len(parms))},
				postdata=parms).addCallback(self._okChangeMailbox, callback).addErrback(self._errorChangeMailbox, callback)

	def _okChangeMailbox(self, callback, html):  # @UnusedVariable # pylint: disable=W0613
		self.debug("")
		callback()

	def _errorChangeMailbox(self, callback, error):
		self.debug(error)
		text = _("FRITZ!Box - Failed changing Mailbox: %s") % error.getErrorMessage()
		self._notify(text)
		callback()

	def getInfo(self, callback):
		''' get status information from FBF '''
		self.debug("")
		self._login(lambda x: self._getInfo(callback, x))

	def _getInfo(self, callback, html):
		# http://192.168.178.1/cgi-bin/webcm?getpage=../html/de/menus/menu2.html&var:lang=de&var:pagename=home&var:menu=home
		self.debug("verify login")
		if html:
			#===================================================================
			# found = re.match(r'.*<p class="errorMessage">FEHLER:&nbsp;([^<]*)</p>', html, re.S)
			# if found:
			# 	self._errorGetInfo('Login: ' + found.group(1))
			# 	return
			#===================================================================
			start = html.find('<p class="errorMessage">FEHLER:&nbsp;')
			if start != -1:
				start = start + len('<p class="errorMessage">FEHLER:&nbsp;')
				self._errorGetInfo('Login: ' + html[start, html.find('</p>', start)])
				return

		url = "http://%s/cgi-bin/webcm" % config.plugins.FritzCall.hostname.value
		parms = urlencode({
			'getpage':'../html/de/menus/menu2.html',
			'var:lang':'de',
			'var:pagename':'home',
			'var:menu':'home',
			'sid':self._md5Sid
			})
		self.debug("url: '" + url + "' parms: '" + parms + "'")
		getPage(url,
			method="POST",
			agent=USERAGENT,
			headers={
					'Content-Type': "application/x-www-form-urlencoded",
					'Content-Length': str(len(parms))},
			postdata=parms).addCallback(lambda x:self._okGetInfo(callback, x)).addErrback(self._errorGetInfo)

	def _okGetInfo(self, callback, html):
		def readInfo(html):
			if self.information:
				(boxInfo, upTime, ipAddress, wlanState, dslState, tamActive, dectActive, faxActive, rufumlActive, guestAccess) = self.information
			else:
				(boxInfo, upTime, ipAddress, wlanState, dslState, tamActive, dectActive, faxActive, rufumlActive, guestAccess) = (None, None, None, None, None, None, None, None, None, None)

			self.debug("_okGetInfo")
			found = re.match(r'.*<table class="tborder" id="tProdukt">\s*<tr>\s*<td style="padding-top:2px;">([^<]*)</td>\s*<td style="padding-top:2px;text-align:right;">\s*([^\s]*)\s*</td>', html, re.S)
			if found:
				boxInfo = found.group(1) + '\n' + found.group(2)
				boxInfo = boxInfo.replace('&nbsp;', ' ')
				# self.debug("Boxinfo: " + boxInfo)
			else:
				found = re.match(r'.*<p class="ac">([^<]*)</p>', html, re.S)
				if found:
					# self.debug("Boxinfo: " + found.group(1))
					boxInfo = found.group(1)

			if html.find('home_coninf.txt') != -1:
				url = "http://%s/cgi-bin/webcm" % config.plugins.FritzCall.hostname.value
				parms = urlencode({
					'getpage':'../html/de/home/home_coninf.txt',
					'sid':self._md5Sid
					})
				# self.debug("get coninfo: url: '" + url + "' parms: '" + parms + "'")
				getPage(url,
					method = "POST",
					agent = USERAGENT,
					headers = {
							'Content-Type': "application/x-www-form-urlencoded",
							'Content-Length': str(len(parms))},
					postdata = parms).addCallback(lambda x:self._okSetConInfo(callback, x)).addErrback(self._errorGetInfo)
			else:
				found = re.match(r'.*if \(isNaN\(jetzt\)\)\s*return "";\s*var str = "([^"]*)";', html, re.S)
				if found:
					# self.debug("Uptime: " + found.group(1))
					upTime = found.group(1)
				else:
					found = re.match(r'.*str = g_pppSeit \+"([^<]*)<br>"\+mldIpAdr;', html, re.S)
					if found:
						# self.debug("Uptime: " + found.group(1))
						upTime = found.group(1)

				found = re.match(r".*IpAdrDisplay\('([.\d]+)'\)", html, re.S)
				if found:
					# self.debug("IpAdrDisplay: " + found.group(1))
					ipAddress = found.group(1)

			if html.find('g_tamActive') != -1:
				entries = re.compile(r'if \("(\d)" == "1"\) {\s*g_tamActive \+= 1;\s*}', re.S).finditer(html)
				tamActive = [0, False, False, False, False, False]
				i = 1
				for entry in entries:
					state = entry.group(1)
					if state == '1':
						tamActive[0] += 1
						tamActive[i] = True
					i += 1
				# self.debug("tamActive: " + str(tamActive))

			if html.find('home_dect.txt') != -1:
				url = "http://%s/cgi-bin/webcm" % config.plugins.FritzCall.hostname.value
				parms = urlencode({
					'getpage':'../html/de/home/home_dect.txt',
					'sid':self._md5Sid
					})
				# self.debug("get coninfo: url: '" + url + "' parms: '" + parms + "'")
				getPage(url,
					method = "POST",
					agent = USERAGENT,
					headers = {
							'Content-Type': "application/x-www-form-urlencoded",
							'Content-Length': str(len(parms))},
					postdata = parms).addCallback(lambda x:self._okSetDect(callback, x)).addErrback(self._errorGetInfo)
			else:
				if html.find('countDect2') != -1:
					entries = re.compile(r'if \("1" == "1"\) countDect2\+\+;', re.S).findall(html)
					dectActive = len(entries)
					# self.debug("dectActive: " + str(dectActive))

			found = re.match(r'.*var g_intFaxActive = "0";\s*if \("1" != ""\) {\s*g_intFaxActive = "1";\s*}\s*', html, re.S)
			if found:
				faxActive = True
				# self.debug("faxActive")

			if html.find('cntRufumleitung') != -1:
				entries = re.compile(r'mode = "1";\s*ziel = "[^"]+";\s*if \(mode == "1" \|\| ziel != ""\)\s*{\s*g_RufumleitungAktiv = true;', re.S).findall(html)
				rufumlActive = len(entries)
				entries = re.compile(r'if \("([^"]*)"=="([^"]*)"\) isAllIncoming\+\+;', re.S).finditer(html)
				isAllIncoming = 0
				for entry in entries:
					# self.debug("rufumlActive add isAllIncoming")
					if entry.group(1) == entry.group(2):
						isAllIncoming += 1
				if isAllIncoming == 2 and rufumlActive > 0:
					rufumlActive -= 1
				# self.debug("rufumlActive: " + str(rufumlActive))

			# /cgi-bin/webcm?getpage=../html/de/home/home_dsl.txt
			# alternative through: fritz.box/cgi-bin/webcm?getpage=../html/de/menus/menu2.html&var:menu=internet&var:pagename=overview
			# { "dsl_carrier_state": "5", "umts_enabled": "0", "ata_mode": "0", "isusbgsm": "", "dsl_ds_nrate": "3130", "dsl_us_nrate": "448", "hint_dsl_no_cable": "0", "wds_enabled": "0", "wds_hop": "0", "isata": "" }
			if html.find('home_dsl.txt') != -1:
				url = "http://%s/cgi-bin/webcm" % config.plugins.FritzCall.hostname.value
				parms = urlencode({
					'getpage':'../html/de/home/home_dsl.txt',
					'sid':self._md5Sid
					})
				# self.debug("get dsl state: url: '" + url + "' parms: '" + parms + "'")
				getPage(url,
					method = "POST",
					agent = USERAGENT,
					headers = {
							'Content-Type': "application/x-www-form-urlencoded",
							'Content-Length': str(len(parms))},
					postdata = parms).addCallback(lambda x:self._okSetDslState(callback, x)).addErrback(self._errorGetInfo)
			else:
				found = re.match(r'.*function DslStateDisplay \(state\){\s*var state = "(\d+)";', html, re.S)
				if found:
					# self.debug("DslState: " + found.group(1))
					dslState = [found.group(1), None, None]  # state, speed
					found = re.match(r'.*function DslStateDisplay \(state\){\s*var state = "\d+";.*?if \("3130" != "0"\) str = "([^"]*)";', html, re.S)
					if found:
						# self.debug("DslSpeed: " + found.group(1).strip())
						dslState[1] = found.group(1).strip()

			# /cgi-bin/webcm?getpage=../html/de/home/home_wlan.txt
			# { "ap_enabled": "1", "active_stations": "0", "encryption": "4", "wireless_stickandsurf_enabled": "0", "is_macfilter_active": "0", "wmm_enabled": "1", "wlan_state": [ "end" ] }
			if html.find('home_wlan.txt') != -1:
				url = "http://%s/cgi-bin/webcm" % config.plugins.FritzCall.hostname.value
				parms = urlencode({
					'getpage':'../html/de/home/home_wlan.txt',
					'sid':self._md5Sid
					})
				# self.debug("get wlan state: url: '" + url + "' parms: '" + parms + "'")
				getPage(url,
					method = "POST",
					agent = USERAGENT,
					headers = {
							'Content-Type': "application/x-www-form-urlencoded",
							'Content-Length': str(len(parms))},
					postdata = parms).addCallback(lambda x:self._okSetWlanState(callback, x)).addErrback(self._errorGetInfo)
			else:
				found = re.match(r'.*function WlanStateLed \(state\){.*?return StateLed\("(\d+)"\);\s*}', html, re.S)
				if found:
					# self.debug("WlanState: " + found.group(1))
					wlanState = [found.group(1), 0, 0]  # state, encryption, number of devices
					found = re.match(r'.*var (?:g_)?encryption = "(\d+)";', html, re.S)
					if found:
						# self.debug("WlanEncrypt: " + found.group(1))
						wlanState[1] = found.group(1)

			return (boxInfo, upTime, ipAddress, wlanState, dslState, tamActive, dectActive, faxActive, rufumlActive, guestAccess)

		self.debug("")
		info = readInfo(html)
		self.debug("information: " + str(info))
		self.information = info
		if callback:
			callback(info)

	def _okSetDect(self, callback, html):
		# self.debug(html)
		# found = re.match(r'.*"connection_status":"(\d+)".*"connection_ip":"([.\d]+)".*"connection_detail":"([^"]+)".*"connection_uptime":"([^"]+)"', html, re.S)
		if html.find('"dect_enabled": "1"') != -1:
			# self.debug("dect_enabled")
			found = re.match(r'.*"dect_device_list":.*\[([^\]]*)\]', html, re.S)
			if found:
				# self.debug("dect_device_list: %s" %(found.group(1)))
				entries = re.compile(r'"1"', re.S).findall(found.group(1))
				dectActive = len(entries)
				(boxInfo, upTime, ipAddress, wlanState, dslState, tamActive, dummy, faxActive, rufumlActive, guestAccess) = self.information
				self.information = (boxInfo, upTime, ipAddress, wlanState, dslState, tamActive, dectActive, faxActive, rufumlActive, guestAccess)
				self.debug("information: " + str(self.information))
		if callback:
			callback(self.information)

	def _okSetConInfo(self, callback, html):
		# self.debug(html)
		# found = re.match(r'.*"connection_status":"(\d+)".*"connection_ip":"([.\d]+)".*"connection_detail":"([^"]+)".*"connection_uptime":"([^"]+)"', html, re.S)
		found = re.match(r'.*"connection_ip": "([.\d]+)".*"connection_uptime": "([^"]+)"', html, re.S)
		if found:
			# self.debug("connection_ip: %s upTime: %s" %( found.group(1), found.group(2)))
			ipAddress = found.group(1)
			upTime = found.group(2)
			(boxInfo, dummy, dummy, wlanState, dslState, tamActive, dectActive, faxActive, rufumlActive, guestAccess) = self.information
			self.information = (boxInfo, upTime, ipAddress, wlanState, dslState, tamActive, dectActive, faxActive, rufumlActive, guestAccess)
			self.debug("[FritzCallFBF] _okSetWlanState information: " + str(self.information))
		else:
			found = re.match(r'.*_ip": "([.\d]+)".*"connection_uptime": "([^"]+)"', html, re.S)
			if found:
				# self.debug("_ip: %s upTime: %s" %( found.group(1), found.group(2)))
				ipAddress = found.group(1)
				upTime = found.group(2)
				(boxInfo, dummy, dummy, wlanState, dslState, tamActive, dectActive, faxActive, rufumlActive, guestAccess) = self.information
				self.information = (boxInfo, upTime, ipAddress, wlanState, dslState, tamActive, dectActive, faxActive, rufumlActive, guestAccess)
				self.debug("information: " + str(self.information))
		if callback:
			callback(self.information)

	def _okSetWlanState(self, callback, html):
		# self.debug(html)
		found = re.match(r'.*"ap_enabled": "(\d+)"', html, re.S)
		if found:
			# self.debug("ap_enabled: " + found.group(1))
			wlanState = [found.group(1), None, None]
			found = re.match(r'.*"encryption": "(\d+)"', html, re.S)
			if found:
				# self.debug("encryption: " + found.group(1))
				wlanState[1] = found.group(1)
			found = re.match(r'.*"active_stations": "(\d+)"', html, re.S)
			if found:
				# self.debug("active_stations: " + found.group(1))
				wlanState[2] = found.group(1)
			(boxInfo, upTime, ipAddress, dummy, dslState, tamActive, dectActive, faxActive, rufumlActive, guestAccess) = self.information
			self.information = (boxInfo, upTime, ipAddress, wlanState, dslState, tamActive, dectActive, faxActive, rufumlActive, guestAccess)
			self.debug("information: " + str(self.information))
		if callback:
			callback(self.information)

	def _okSetDslState(self, callback, html):
		# self.debug(html)
		found = re.match(r'.*"dsl_carrier_state": "(\d+)"', html, re.S)
		if found:
			# self.debug("dsl_carrier_state: " + found.group(1))
			dslState = [found.group(1), "", None]
			found = re.match(r'.*"dsl_ds_nrate": "(\d+)"', html, re.S)
			if found:
				# self.debug("dsl_ds_nrate: " + found.group(1))
				dslState[1] = found.group(1)
			found = re.match(r'.*"dsl_us_nrate": "(\d+)"', html, re.S)
			if found:
				# self.debug("dsl_us_nrate: " + found.group(1))
				dslState[1] = dslState[1] + '/' + found.group(1)
			(boxInfo, upTime, ipAddress, wlanState, dummy, tamActive, dectActive, faxActive, rufumlActive, guestAccess) = self.information
			self.information = (boxInfo, upTime, ipAddress, wlanState, dslState, tamActive, dectActive, faxActive, rufumlActive, guestAccess)
			self.debug("information: " + str(self.information))
		if callback:
			callback(self.information)

	def _errorGetInfo(self, error):
		self.debug(error)
		text = _("FRITZ!Box - Error getting status: %s") % error.getErrorMessage()
		self._notify(text)
		# linkP = open("/tmp/FritzCall_errorGetInfo.htm", "w")
		# linkP.write(error)
		# linkP.close()

	def reset(self):
		self._login(self._reset)

	def _reset(self, html):
		# POSTDATA=getpage=../html/reboot.html&errorpage=../html/de/menus/menu2.html&var:lang=de&var:pagename=home&var:errorpagename=home&var:menu=home&var:pagemaster=&time:settings/time=1242207340%2C-120&var:tabReset=0&logic:command/reboot=../gateway/commands/saveconfig.html
		if html:
			#===================================================================
			# found = re.match(r'.*<p class="errorMessage">FEHLER:&nbsp;([^<]*)</p>', html, re.S)
			# if found:
			# 	self._errorReset('Login: ' + found.group(1))
			# 	return
			#===================================================================
			start = html.find('<p class="errorMessage">FEHLER:&nbsp;')
			if start != -1:
				start = start + len('<p class="errorMessage">FEHLER:&nbsp;')
				self._errorReset('Login: ' + html[start, html.find('</p>', start)])
				return
		if self._callScreen:
			self._callScreen.close()
		url = "http://%s/cgi-bin/webcm" % config.plugins.FritzCall.hostname.value
		parms = urlencode({
			'getpage':'../html/reboot.html',
			'var:lang':'de',
			'var:pagename':'reset',
			'var:menu':'system',
			'logic:command/reboot':'../gateway/commands/saveconfig.html',
			'sid':self._md5Sid
			})
		self.debug("url: '" + url + "' parms: '" + parms + "'")
		getPage(url,
			method = "POST",
			agent = USERAGENT,
			headers = {
					'Content-Type': "application/x-www-form-urlencoded",
					'Content-Length': str(len(parms))},
			postdata = parms)

	def _okReset(self, html):  # @UnusedVariable # pylint: disable=W0613
		self.debug("")

	def _errorReset(self, error):
		self.debug(error)
		text = _("FRITZ!Box - Error resetting: %s") % error.getErrorMessage()
		self._notify(text)

	def readBlacklist(self):
		self._login(self._readBlacklist)

	def _readBlacklist(self, html):
		if html:
			#===================================================================
			# found = re.match(r'.*<p class="errorMessage">FEHLER:&nbsp;([^<]*)</p>', html, re.S)
			# if found:
			# 	self._errorBlacklist('Login: ' + found.group(1))
			# 	return
			#===================================================================
			start = html.find('<p class="errorMessage">FEHLER:&nbsp;')
			if start != -1:
				start = start + len('<p class="errorMessage">FEHLER:&nbsp;')
				self._errorBlacklist('Login: ' + html[start, html.find('</p>', start)])
				return
		# http://fritz.box/cgi-bin/webcm?getpage=../html/de/menus/menu2.html&var:lang=de&var:menu=fon&var:pagename=sperre
		url = "http://%s/cgi-bin/webcm" % config.plugins.FritzCall.hostname.value
		parms = urlencode({
			'getpage':'../html/de/menus/menu2.html',
			'var:lang':'de',
			'var:pagename':'sperre',
			'var:menu':'fon',
			'sid':self._md5Sid
			})
		self.debug("url: '" + url + "' parms: '" + parms + "'")
		getPage(url,
			method = "POST",
			agent = USERAGENT,
			headers = {
					'Content-Type': "application/x-www-form-urlencoded",
					'Content-Length': str(len(parms))},
			postdata = parms).addCallback(self._okBlacklist).addErrback(self._errorBlacklist)

	def _okBlacklist(self, html):
		self.debug("")
		entries = re.compile(r'<script type="text/javascript">document.write\(Tr(Out|In)\("\d+", "(\d+)", "\w*"\)\);</script>', re.S).finditer(html)
		self.blacklist = ([], [])
		for entry in entries:
			if entry.group(1) == "In":
				self.blacklist[0].append(entry.group(2))
			else:
				self.blacklist[1].append(entry.group(2))
		self.debug(repr(self.blacklist))

	def _errorBlacklist(self, error):
		self.debug(error)
		text = _("FRITZ!Box - Error getting blacklist: %s") % error.getErrorMessage()
		self._notify(text)

class FritzCallFBF_05_27(object):
	logger = logging.getLogger("FritzCall.FBF_05_27")
	debug = logger.debug

	def __init__(self):
		self.debug("[FritzCallFBF_05_27] __init__")
		self._callScreen = None
		self._md5LoginTimestamp = None
		self._md5Sid = '0000000000000000'
		self._callTimestamp = 0
		self._callList = []
		self._callType = config.plugins.FritzCall.fbfCalls.value
		self.password = decode(config.plugins.FritzCall.password.value)
		self._phoneBookID = '0'
		self._loginCallbacks = []
		self.blacklist = ([], [])
		self.information = (None, None, None, None, None, None, None, None, None, None)  # (boxInfo, upTime, ipAddress, wlanState, dslState, tamActive, dectActive, guestAccess)
		self.phonebook = None
		self.getInfo(None)
		# self.readBlacklist() now in getInfo
		self.phonebooksFBF = []

	def _notify(self, text):
		self.debug("[FritzCallFBF_05_27] notify: " + text)
		self._md5LoginTimestamp = None
		if self._callScreen:
			self.debug("[FritzCallFBF_05_27] notify: try to close callScreen")
			self._callScreen.close()
			self._callScreen = None
		Notifications.AddNotification(MessageBox, text, type = MessageBox.TYPE_ERROR, timeout = config.plugins.FritzCall.timeout.value)

	def _login(self, callback = None):
		self.debug("[FritzCallFBF_05_27] _login: " + time.ctime())
		if callback:
			self.debug("[FritzCallFBF_05_27] _login: add callback " + callback.__name__)
			if self._loginCallbacks:
				# if login in process just add callback to _loginCallbacks
				self._loginCallbacks.append(callback)
				self.debug("[FritzCallFBF_05_27] _login: login in progress: leave")
				return
			else:
				self._loginCallbacks.append(callback)

		if self._callScreen:
			self._callScreen.updateStatus(_("login"))
		if self._md5LoginTimestamp and ((time.time() - self._md5LoginTimestamp) < float(9.5 * 60)) and self._md5Sid != '0000000000000000':  # new login after 9.5 minutes inactivity
			self.debug("[FritzCallFBF_05_27] _login: renew timestamp: " + time.ctime(self._md5LoginTimestamp) + " time: " + time.ctime())
			self._md5LoginTimestamp = time.time()
			for callback in self._loginCallbacks:
				self.debug("[FritzCallFBF_05_27] _login: calling " + callback.__name__)
				callback(None)
			self._loginCallbacks = []
		else:
			self.debug("[FritzCallFBF_05_27] _login: not logged in or outdated login")
			# http://fritz.box/cgi-bin/webcm?getpage=../html/login_sid.xml
			parms = urlencode({'getpage':'../html/login_sid.xml'})
			url = "http://%s/cgi-bin/webcm" % (config.plugins.FritzCall.hostname.value)
			self.debug("[FritzCallFBF_05_27] _login: '" + url + "?" + parms + "'")
			getPage(url,
				method = "POST",
				headers = {'Content-Type': "application/x-www-form-urlencoded", 'Content-Length': str(len(parms))},
				postdata = parms).addCallback(self._md5Login).addErrback(self._errorLogin)

	def _md5Login(self, sidXml):
		def buildResponse(challenge, text):
			self.debug("[FritzCallFBF_05_27] _md5Login7buildResponse: challenge: " + challenge + ' text: ' + __(text))
			text = (challenge + '-' + text).decode('utf-8', 'ignore').encode('utf-16-le')
			for i in range(len(text)):  # consider-using-enumerate # pylint: disable=
				if ord(text[i]) > 255:
					text[i] = '.'
			md5 = hashlib.md5()
			md5.update(text)  # pylint: disable=e1101
			self.debug("[FritzCallFBF_05_27] md5Login/buildResponse: " + md5.hexdigest())
			return challenge + '-' + md5.hexdigest()

		self.debug("[FritzCallFBF_05_27] _md5Login")
		found = re.match(r'.*<SID>([^<]*)</SID>', sidXml, re.S)
		if found:
			self._md5Sid = found.group(1)
			self.debug("[FritzCallFBF_05_27] _md5Login: SID " + self._md5Sid)
		else:
			self.debug("[FritzCallFBF_05_27] _md5Login: no sid! That must be an old firmware.")
			self._errorLogin('No sid?!?')
			return

		self.debug("[FritzCallFBF_05_27] _md5Login: renew timestamp: " + time.ctime(self._md5LoginTimestamp) + " time: " + time.ctime())
		self._md5LoginTimestamp = time.time()
		if sidXml.find('<iswriteaccess>0</iswriteaccess>') != -1:
			self.debug("[FritzCallFBF_05_27] _md5Login: logging in")
			found = re.match(r'.*<Challenge>([^<]*)</Challenge>', sidXml, re.S)
			if found:
				challenge = found.group(1)
				self.debug("[FritzCallFBF_05_27] _md5Login: challenge " + challenge)
			else:
				challenge = None
				self.debug("[FritzCallFBF_05_27] _md5Login: login necessary and no challenge! That is terribly wrong.")
			parms = urlencode({
							'getpage':'../html/de/menus/menu2.html',  # 'var:pagename':'home', 'var:menu':'home',
							'login:command/response': buildResponse(challenge, self.password),
							})
			url = "http://%s/cgi-bin/webcm" % (config.plugins.FritzCall.hostname.value)
			self.debug("[FritzCallFBF_05_27] _md5Login: '" + url + "?" + parms + "'")
			getPage(url,
				method = "POST",
				agent = USERAGENT,
				headers = {'Content-Type': "application/x-www-form-urlencoded", 'Content-Length': str(len(parms))},
				postdata = parms).addCallback(self._gotPageLogin).addErrback(self._errorLogin)
		else:
			for callback in self._loginCallbacks:
				self.debug("[FritzCallFBF_05_27] _md5Login: calling " + callback.__name__)
				callback(None)
			self._loginCallbacks = []

	def _gotPageLogin(self, html):
		if self._callScreen:
			self._callScreen.updateStatus(_("login verification"))
		self.debug("[FritzCallFBF_05_27] _gotPageLogin: verify login")
		start = html.find('<p class="errorMessage">FEHLER:&nbsp;')
		if start != -1:
			start = start + len('<p class="errorMessage">FEHLER:&nbsp;')
			text = _("FRITZ!Box - Error logging in\n\n") + html[start: html.find('</p>', start)]
			self._notify(text)
		else:
			if self._callScreen:
				self._callScreen.updateStatus(_("login ok"))

		found = re.match(r'.*<input type="hidden" name="sid" value="([^\"]*)"', html, re.S)
		if found:
			self._md5Sid = found.group(1)
			self.debug("[FritzCallFBF_05_27] _gotPageLogin: found sid: " + self._md5Sid)

		for callback in self._loginCallbacks:
			self.debug("[FritzCallFBF_05_27] _gotPageLogin: calling " + callback.__name__)
			callback(None)
		self._loginCallbacks = []

	def _errorLogin(self, error):
		global fritzbox  # global-variable-undefined # pylint: disable=W0601
		self.debug("[FritzCallFBF_05_27] _errorLogin: %s", error)
		if isinstance(error, str):
			error = error.getErrorMessage()
		text = _("FRITZ!Box - Error logging in: %s\nDisabling plugin.") % error
		fritzbox = None
		self._notify(text)

	def _logout(self):
		if self._md5LoginTimestamp:
			self._md5LoginTimestamp = None
			parms = urlencode({
							'getpage':'../html/de/menus/menu2.html',  # 'var:pagename':'home', 'var:menu':'home',
							'login:command/logout':'bye bye Fritz'
							})
			url = "http://%s/cgi-bin/webcm" % (config.plugins.FritzCall.hostname.value)
			self.debug("[FritzCallFBF_05_27] logout: '" + url + "' parms: '" + parms + "'")
			getPage(url,
				method = "POST",
				agent = USERAGENT,
				headers = {'Content-Type': "application/x-www-form-urlencoded", 'Content-Length': str(len(parms))},
				postdata = parms).addErrback(self._errorLogout)

	def _errorLogout(self, error):
		self.debug("[FritzCallFBF_05_27] _errorLogout: %s", error)
		text = _("FRITZ!Box - Error logging out: %s") % error.getErrorMessage()
		self._notify(text)

	def loadFritzBoxPhonebook(self, phonebook):
		self.phonebook = phonebook
		self._login(self._selectFritzBoxPhonebook)

	def _selectFritzBoxPhonebook(self, html):
		# first check for login error
		if html:
			start = html.find('<p class="errorMessage">FEHLER:&nbsp;')
			if start != -1:
				start = start + len('<p class="errorMessage">FEHLER:&nbsp;')
				self._errorLoad('Login: ' + html[start, html.find('</p>', start)])
				return
		# look for phonebook called dreambox or Dreambox
		parms = urlencode({
						'sid':self._md5Sid,
						})
		url = "http://%s/fon_num/fonbook_select.lua" % (config.plugins.FritzCall.hostname.value)
		self.debug("[FritzCallFBF_05_27] _selectPhonebook: '" + url + "' parms: '" + parms + "'")
		getPage(url,
			method = "POST",
			agent = USERAGENT,
			headers = {'Content-Type': "application/x-www-form-urlencoded", 'Content-Length': str(len(parms))},
			postdata = parms).addCallback(self._loadFritzBoxPhonebook).addErrback(self._errorLoad)

	def _loadFritzBoxPhonebook(self, html):
		# Firmware 05.27 onwards
		# look for phonebook called [dD]reambox and get bookid
		found = re.match(r'.*<label for="uiBookid:([\d]+)">' + config.plugins.FritzCall.fritzphonebookName.value, html, re.S)
		if found:
			bookid = found.group(1)
			self.debug("[FritzCallFBF_05_27] _loadFritzBoxPhonebook: found dreambox phonebook %s", bookid)
		else:
			bookid = 1
		# http://192.168.178.1/fon_num/fonbook_list.lua?sid=2faec13b0000f3a2
		parms = urlencode({
						'bookid':bookid,
						'sid':self._md5Sid,
						})
		url = "http://%s/fon_num/fonbook_list.lua" % (config.plugins.FritzCall.hostname.value)
		self.debug("[FritzCallFBF_05_27] _loadFritzBoxPhonebookNew: '" + url + "' parms: '" + parms + "'")
		getPage(url,
			method = "POST",
			agent = USERAGENT,
			headers = {'Content-Type': "application/x-www-form-urlencoded", 'Content-Length': str(len(parms))},
			postdata = parms).addCallback(self._parseFritzBoxPhonebook).addErrback(self._errorLoad)

	def _parseFritzBoxPhonebook(self, html):
		self.debug("[FritzCallFBF_05_27] _parseFritzBoxPhonebookNew")
		found = re.match(r'.*<input type="hidden" name="telcfg:settings/Phonebook/Books/Name\d+" value="' + config.plugins.FritzCall.fritzphonebookName.value + r'" id="uiPostPhonebookName\d+" disabled>\s*<input type="hidden" name="telcfg:settings/Phonebook/Books/Id\d+" value="(\d+)" id="uiPostPhonebookId\d+" disabled>', html, re.S)
		if found:
			phoneBookID = found.group(1)
			self.debug("[FritzCallFBF_05_27] _parseFritzBoxPhonebookNew: found dreambox phonebook with id: " + phoneBookID)
			if self._phoneBookID != phoneBookID:
				self._phoneBookID = phoneBookID
				self.debug("[FritzCallFBF_05_27] _parseFritzBoxPhonebookNew: reload phonebook")
				self._loadFritzBoxPhonebook(None)  # reload with dreambox phonebook
				return

		# first, let us get the charset
		found = re.match(r'.*<meta http-equiv=content-type content="text/html; charset=([^"]*)">', html, re.S)
		if found:
			charset = found.group(1)
			self.debug("[FritzCallFBF_05_27] _parseFritzBoxPhonebookNew: found charset: " + charset)
			html = html2unicode(html.replace(chr(0xf6), '').decode(charset)).encode('utf-8')
		else:  # this is kind of emergency conversion...
			try:
				self.debug("[FritzCallFBF_05_27] _parseFritzBoxPhonebookNew: try charset utf-8")
				charset = 'utf-8'
				html = html2unicode(html.decode('utf-8')).encode('utf-8')  # this looks silly, but has to be
			except UnicodeDecodeError:
				self.debug("[FritzCallFBF_05_27] _parseFritzBoxPhonebookNew: try charset iso-8859-1")
				charset = 'iso-8859-1'
				html = html2unicode(html.decode('iso-8859-1')).encode('utf-8')  # this looks silly, but has to be

		# cleanout hrefs
		html = re.sub("<a href[^>]*>", "", html)
		html = re.sub("</a>", "", html)
		#=======================================================================
		# linkP = open("/tmp/FritzCall_Phonebook.htm", "w")
		# linkP.write(html)
		# linkP.close()
		#=======================================================================

		if html.find('class="zebra_reverse"') != -1:
			self.debug("[FritzCallFBF_05_27] Found new 7390 firmware")
			# <td class="tname">Mama</td><td class="tnum">03602191620<br>015228924783<br>03602181567</td><td class="ttype">geschäftl.<br>mobil<br>privat</td><td class="tcode"><br>**701<br></td><td class="tvanity"><br>1<br></td>
			entrymask = re.compile(r'<td class="tname">([^<]*)</td><td class="tnum">([^<]+(?:<br>[^<]+)*)</td><td class="ttype">([^<]+(?:<br>[^<]+)*)</td><td class="tcode">([^<]*(?:<br>[^<]*)*)</td><td class="tvanity">([^<]*(?:<br>[^<]*)*)</td>', re.S)
			entries = entrymask.finditer(html)
			for found in entries:
				# self.debug("[FritzCallFBF_05_27] _parseFritzBoxPhonebookNew: processing entry for '''%s'''" % (found.group(1)))
				name = found.group(1)
				thisnumbers = found.group(2).split("<br>")
				thistypes = found.group(3).split("<br>")
				thiscodes = found.group(4).split("<br>")
				thisvanitys = found.group(5).split("<br>")
				for i in range(len(thisnumbers)):  # consider-using-enumerate # pylint: disable=
					thisnumber = cleanNumber(thisnumbers[i])
					if thisnumber in self.phonebook.phonebook:
						self.debug("[FritzCallFBF_05_27] Ignoring '''%s''' with '''%s''' from FRITZ!Box Phonebook!", name, __(thisnumber))
						continue

					if not thisnumbers[i]:
						self.debug("[FritzCallFBF_05_27] _parseFritzBoxPhonebookNew: Ignoring entry with empty number for '''%s'''", name)
						continue
					else:
						thisname = name
						if config.plugins.FritzCall.showType.value and thistypes[i]:
							thisname = thisname + " (" + thistypes[i] + ")"
						if config.plugins.FritzCall.showShortcut.value and thiscodes[i]:
							thisname = thisname + ", " + _("Shortcut") + ": " + thiscodes[i]
						if config.plugins.FritzCall.showVanity.value and thisvanitys[i]:
							thisname = thisname + ", " + _("Vanity") + ": " + thisvanitys[i]

						# self.debug("[FritzCallFBF_05_27] _parseFritzBoxPhonebookNew: Adding '''%s''' with '''%s''' from FRITZ!Box Phonebook!" % (thisname.strip(), thisnumber))
						# Beware: strings in phonebook.phonebook have to be in utf-8!
						self.phonebook.phonebook[thisnumber] = thisname
		else:
			self._notify(_("Could not parse FRITZ!Box Phonebook entry"))

	def _errorLoad(self, error):
		self.debug("[FritzCallFBF_05_27] _errorLoad: %s", error)
		text = _("FRITZ!Box - ") + _("Could not load phonebook: %s") % error.getErrorMessage()
		self._notify(text)

	def getCalls(self, callScreen, callback, callType):
		#
		# FW 05.27 onwards
		#
		self._callScreen = callScreen
		self._callType = callType
		self.debug("[FritzCallFBF_05_27] _getCalls1New")
		if self._callScreen:
			self._callScreen.updateStatus(_("finishing"))
		# http://192.168.178.1/fon_num/foncalls_list.lua?sid=da78ab0797197dc7
		parms = urlencode({'sid':self._md5Sid})
		url = "http://%s/fon_num/foncalls_list.lua?%s" % (config.plugins.FritzCall.hostname.value, parms)
		getPage(url).addCallback(lambda x:self._gotPageCalls(callback, x)).addErrback(self._errorCalls)

	def _gotPageCalls(self, callback, html = ""):

		self.debug("[FritzCallFBF_05_27] _gotPageCalls")
		if self._callScreen:
			self._callScreen.updateStatus(_("preparing"))

		callListL = []
		if config.plugins.FritzCall.filter.value and config.plugins.FritzCall.filterCallList.value:
			filtermsns = [x.strip() for x in config.plugins.FritzCall.filtermsn.value.split(",")]
			self.debug("[FritzCallFBF_05_27] _gotPageCalls: filtermsns %s", repr(map(__, filtermsns)))

		#=======================================================================
		# linkP = open("/tmp/FritzCall_Calllist.htm", "w")
		# linkP.write(html)
		# linkP.close()
		#=======================================================================

		# 1: direct; 2: date; 3: Rufnummer; 4: Name; 5: Nebenstelle; 6: Eigene Rufnumme lang; 7: Eigene Rufnummer; 8: Dauer
		entrymask = re.compile(r'<td class="([^"]*)" title="[^"]*"></td>\s*<td>([^<]*)</td>\s*<td(?: title="[^\d]*)?([\d]*)(?:[">]+)?(?:<a href=[^>]*>)?([^<]*)(?:</a>)?</td>\s*<td>([^<]*)</td>\s*<td title="([^"]*)">([\d]*)</td>\s*<td>([^<]*)</td>', re.S)
		entries = entrymask.finditer(html)
		for found in entries:
			if found.group(1) == "call_in":
				direct = FBF_IN_CALLS
			elif found.group(1) == "call_out":
				direct = FBF_OUT_CALLS
			elif found.group(1) == "call_in_fail":
				direct = FBF_MISSED_CALLS
			# self.debug("[FritzCallFBF_05_27] _gotPageCallsNew: direct: " + direct)
			if direct != self._callType and self._callType != ".":
				continue

			date = found.group(2)
			# self.debug("[FritzCallFBF_05_27] _gotPageCallsNew: date: " + date)
			length = found.group(8)
			# self.debug("[FritzCallFBF_05_27] _gotPageCallsNew: len: " + length)
			remote = found.group(4)
			if config.plugins.FritzCall.phonebook.value:
				if remote and not remote.isdigit():
					remote = resolveNumber(found.group(3), remote + " (FBF)", self.phonebook)
				else:
					remote = resolveNumber(found.group(3), "", self.phonebook)
			# self.debug("[FritzCallFBF_05_27] _gotPageCallsNew: remote. " + remote)
			here = found.group(7)
			#===================================================================
			# start = here.find('Internet: ')
			# if start != -1:
			# 	start += len('Internet: ')
			# 	here = here[start:]
			# else:
			# 	here = line[5]
			#===================================================================
			if config.plugins.FritzCall.filter.value and config.plugins.FritzCall.filterCallList.value:
				# self.debug("[FritzCallFBF_05_27] _gotPageCalls: check %s" % (here))
				if here not in filtermsns:
					# self.debug("[FritzCallFBF_05_27] _gotPageCalls: skip %s" % (here))
					continue
			here = resolveNumber(here, found.group(6), self.phonebook)
			# self.debug("[FritzCallFBF_05_27] _gotPageCallsNew: here: " + here)

			number = stripCbCPrefix(found.group(3), config.plugins.FritzCall.country.value)
			if config.plugins.FritzCall.prefix.value and number and number[0] != '0':  # should only happen for outgoing
				number = config.plugins.FritzCall.prefix.value + number
			# self.debug("[FritzCallFBF_05_27] _gotPageCallsNew: number: " + number)
			self.debug("[FritzCallFBF_05_27] _gotPageCallsNew: append: %s", repr((number, date, direct, remote, length, here)))
			callListL.append((number, date, direct, remote, length, here))

		if callback:
			# self.debug("[FritzCallFBF_05_27] _gotPageCalls call callback with\n" + text
			callback(callListL)
		self._callScreen = None

	def _errorCalls(self, error):
		self.debug("[FritzCallFBF_05_27] _errorCalls: %s", error)
		text = _("FRITZ!Box - Could not load calls: %s") % error.getErrorMessage()
		self._notify(text)

	def dial(self, number):
		''' initiate a call to number '''
		self._login(lambda x: self._dial(number, x))

	def _dial(self, number, html):
		if html:
			#===================================================================
			# found = re.match(r'.*<p class="errorMessage">FEHLER:&nbsp;([^<]*)</p>', html, re.S)
			# if found:
			# 	self._errorDial('Login: ' + found.group(1))
			# 	return
			#===================================================================
			start = html.find('<p class="errorMessage">FEHLER:&nbsp;')
			if start != -1:
				start = start + len('<p class="errorMessage">FEHLER:&nbsp;')
				self._errorDial('Login: ' + html[start, html.find('</p>', start)])
				return
		url = "http://%s/cgi-bin/webcm" % config.plugins.FritzCall.hostname.value
		parms = urlencode({
			'getpage':'../html/de/menus/menu2.html',
			'var:pagename':'fonbuch',
			'var:menu':'home',
			'telcfg:settings/UseClickToDial':'1',
			'telcfg:settings/DialPort':config.plugins.FritzCall.extension.value,
			'telcfg:command/Dial':number,
			'sid':self._md5Sid
			})
		self.debug("[FritzCallFBF_05_27] dial url: '" + url + "' parms: '" + parms + "'")
		getPage(url,
			method = "POST",
			agent = USERAGENT,
			headers = {
					'Content-Type': "application/x-www-form-urlencoded",
					'Content-Length': str(len(parms))},
			postdata = parms).addCallback(self._okDial).addErrback(self._errorDial)

	def _okDial(self, html):  # @UnusedVariable # pylint: disable=W0613
		self.debug("[FritzCallFBF_05_27] okDial")

	def _errorDial(self, error):
		self.debug("[FritzCallFBF_05_27] errorDial: %s", error)
		text = _("FRITZ!Box - Dialling failed: %s") % error.getErrorMessage()
		self._notify(text)

	def changeWLAN(self, statusWLAN, callback):  # @UnusedVariable # pylint: disable=W0613
		''' get status information from FBF '''
		self.debug("[FritzCallFBF_05_27] changeWLAN start")
		Notifications.AddNotification(MessageBox, _("not available with this firmware version"), type = MessageBox.TYPE_ERROR, timeout = config.plugins.FritzCall.timeout.value)
		return

	def _changeWLAN(self, statusWLAN, callback, html):
		if html:
			#===================================================================
			# found = re.match(r'.*<p class="errorMessage">FEHLER:&nbsp;([^<]*)</p>', html, re.S)
			# if found:
			# 	self._errorChangeWLAN('Login: ' + found.group(1))
			# 	return
			#===================================================================
			start = html.find('<p class="errorMessage">FEHLER:&nbsp;')
			if start != -1:
				start = start + len('<p class="errorMessage">FEHLER:&nbsp;')
				self._errorChangeWLAN(callback, 'Login: ' + html[start, html.find('</p>', start)])
				return

		if statusWLAN == '0':
			statusWLAN = 'off'
		else:
			statusWLAN = 'off'

		url = "http://%s//wlan/wlan_settings.lua" % config.plugins.FritzCall.hostname.value
		parms = urlencode({
			'active':str(statusWLAN),
			'sid':self._md5Sid
			})
		self.debug("[FritzCallFBF] changeWLAN url: '" + url + "' parms: '" + parms + "'")
		getPage(url,
			method = "POST",
			agent = USERAGENT,
			headers = {
					'Content-Type': "application/x-www-form-urlencoded",
					'Content-Length': str(len(parms))},
			postdata = parms).addCallback(self._okChangeWLAN, callback).addErrback(self._errorChangeWLAN, callback)

	def _okChangeWLAN(self, callback, html):  # @UnusedVariable # pylint: disable=W0613
		self.debug("[FritzCallFBF] _okChangeWLAN")
		callback()

	def _errorChangeWLAN(self, callback, error):
		self.debug("[FritzCallFBF] _errorChangeWLAN: %s", error)
		text = _("FRITZ!Box - Failed changing WLAN: %s") % error.getErrorMessage()
		self._notify(text)
		callback()

	def changeMailbox(self, whichMailbox, callback):  # @UnusedVariable # pylint: disable=W0613
		''' switch mailbox on/off '''
		self.debug("[FritzCallFBF_05_27] changeMailbox start: " + str(whichMailbox))
		Notifications.AddNotification(MessageBox, _("not available with this firmware version"), type = MessageBox.TYPE_ERROR, timeout = config.plugins.FritzCall.timeout.value)

	def _changeMailbox(self, whichMailbox, html):  # pylint: disable=W0613
		return

	def _okChangeMailbox(self, html):  # @UnusedVariable # pylint: disable=W0613
		self.debug("[FritzCallFBF_05_27] _okChangeMailbox")

	def _errorChangeMailbox(self, error):
		self.debug("[FritzCallFBF_05_27] _errorChangeMailbox: %s", error)
		text = _("FRITZ!Box - Failed changing Mailbox: %s") % error.getErrorMessage()
		self._notify(text)

	def getInfo(self, callback):
		''' get status information from FBF '''
		self.debug("[FritzCallFBF_05_27] getInfo")
		self._login(lambda x:self._getInfo(callback, x))

	def _getInfo(self, callback, html):
		self.debug("[FritzCallFBF_05_27] _getInfo: verify login")
		if html:
			start = html.find('<p class="errorMessage">FEHLER:&nbsp;')
			if start != -1:
				start = start + len('<p class="errorMessage">FEHLER:&nbsp;')
				self._errorGetInfo('Login: ' + html[start, html.find('</p>', start)])
				return

		self._readBlacklist()

		url = "http://%s/home/home.lua" % config.plugins.FritzCall.hostname.value
		parms = urlencode({
			'sid':self._md5Sid
			})
		self.debug("[FritzCallFBF_05_27] _getInfo url: '" + url + "' parms: '" + parms + "'")
		getPage(url,
			method = "POST",
			agent = USERAGENT,
			headers = {
					'Content-Type': "application/x-www-form-urlencoded",
					'Content-Length': str(len(parms))},
			postdata = parms).addCallback(lambda x:self._okGetInfo(callback, x)).addErrback(self._errorGetInfo)

	def _okGetInfo(self, callback, html):

		self.debug("[FritzCallFBF_05_27] _okGetInfo")

		#=======================================================================
		# linkP = open("/tmp/FritzCallInfo.htm", "w")
		# linkP.write(html)
		# linkP.close()
		#=======================================================================

		if self.information:
			(boxInfo, upTime, ipAddress, wlanState, dslState, tamActive, dectActive, faxActive, rufumlActive, guestAccess) = self.information
		else:
			(boxInfo, upTime, ipAddress, wlanState, dslState, tamActive, dectActive, faxActive, rufumlActive, guestAccess) = (None, None, None, None, None, None, None, None, None, None)

		found = re.match(r'.*<table id="tProdukt" class="tborder"> <tr> <td style="[^"]*" >([^<]*)</td> <td style="[^"]*" class="td_right">([^<]*)<a target="[^"]*" onclick="[^"]*" href="[^"]*">([^<]*)</a></td> ', html, re.S)
		if found:
			boxInfo = found.group(1) + '\n' + found.group(2) + found.group(3)
			boxInfo = boxInfo.replace('&nbsp;', ' ')
			self.debug("[FritzCallFBF_05_27] _okGetInfo Boxinfo: " + boxInfo)

		found = re.match(r'.*<div id=\'ipv4_info\'><span class="[^"]*">verbunden seit ([^<]*)</span>', html, re.S)
		if found:
			upTime = found.group(1)
			self.debug("[FritzCallFBF_05_27] _okGetInfo upTime: " + upTime)

		found = re.match(r'.*IP-Adresse: ([^<]*)</span>', html, re.S)
		if found:
			ipAddress = found.group(1)
			self.debug("[FritzCallFBF_05_27] _okGetInfo ipAddress: " + ipAddress)

		# wlanstate = [ active, encrypted, no of devices ]
		found = re.match(r'.*<tr id="uiTrWlan"><td class="(led_gray|led_green|led_red)"></td><td><a href="[^"]*">WLAN</a></td><td>(aus|an)(|, gesichert)</td>', html, re.S)
		if found:
			if found.group(1) == "led_green":
				if found.group(2):
					wlanState = ['1', '1', '']
				else:
					wlanState = ['1', '0', '']
			else:
				wlanState = ['0', '0', '0']
			self.debug("[FritzCallFBF_05_27] _okGetInfo wlanState: " + repr(wlanState))

		found = re.match(r'.*<tr id="uiTrDsl"><td class="(led_gray|led_green|led_red)">', html, re.S)
		if found:
			if found.group(1) == "led_green":
				dslState = ['5', None, None]
				found = re.match(r'.*<a href="[^"]*">DSL</a></td><td >bereit, ([^<]*)<img src=\'[^\']*\' height=\'[^\']*\'>&nbsp;([^<]*)<img src=\'[^\']*\' height=\'[^\']*\'></td></tr>', html, re.S)
				if found:
					dslState[1] = found.group(1) + "/" + found.group(2)
			else:
				dslState = ['0', None, None]
		self.debug("[FritzCallFBF_05_27] _okGetInfo dslState: " + repr(dslState))

		found = re.match(r'.*<tr id="trTam" style=""><td><a href="[^"]*">Anrufbeantworter</a></td><td title=\'[^\']*\'>([\d]+) aktiv([^<]*)</td></tr>', html, re.S)
		if found:
			# found.group(2) could be ', neue Nachrichten vorhanden'; ignore for now
			tamActive = [found.group(1), False, False, False, False, False]
		self.debug("[FritzCallFBF_05_27] _okGetInfo tamActive: " + repr(tamActive))

		found = re.match(r'.*<tr id="uiTrDect"><td class="led_green"></td><td><a href="[^"]*">DECT</a></td><td>an, (ein|\d*) Schnurlostelefon', html, re.S)
		if found:
			dectActive = found.group(1)
		self.debug("[FritzCallFBF_05_27] _okGetInfo dectActive: " + repr(dectActive))

		found = re.match(r'.*<td>Integriertes Fax aktiv</td>', html, re.S)
		if found:
			faxActive = True
		self.debug("[FritzCallFBF_05_27] _okGetInfo faxActive: " + repr(faxActive))

		found = re.match(r'.* <tr style=""><td><a href="[^"]*">Rufumleitung</a></td><td>deaktiviert</td></tr>', html, re.S)
		if found:
			rufumlActive = False
		else:
			rufumlActive = True
		self.debug("[FritzCallFBF_05_27] _okGetInfo rufumlActive: " + repr(rufumlActive))

		info = (boxInfo, upTime, ipAddress, wlanState, dslState, tamActive, dectActive, faxActive, rufumlActive, guestAccess)
		self.debug("[FritzCallFBF_05_27] _okGetInfo information: " + str(info))
		self.information = info
		if callback:
			callback(info)

	def _okSetDect(self, callback, html):  # pylint: disable=W0613
		return

	def _okSetConInfo(self, callback, html):  # pylint: disable=W0613
		return

	def _okSetWlanState(self, callback, html):  # pylint: disable=W0613
		return

	def _okSetDslState(self, callback, html):  # pylint: disable=W0613
		return

	def _errorGetInfo(self, error):
		self.debug("[FritzCallFBF_05_27] _errorGetInfo: %s", error)
		text = _("FRITZ!Box - Error getting status: %s") % error.getErrorMessage()
		self._notify(text)
		return

	def reset(self):
		self._login(self._reset)

	def _reset(self, html):
		# POSTDATA=getpage=../html/reboot.html&errorpage=../html/de/menus/menu2.html&var:lang=de&var:pagename=home&var:errorpagename=home&var:menu=home&var:pagemaster=&time:settings/time=1242207340%2C-120&var:tabReset=0&logic:command/reboot=../gateway/commands/saveconfig.html
		if html:
			#===================================================================
			# found = re.match(r'.*<p class="errorMessage">FEHLER:&nbsp;([^<]*)</p>', html, re.S)
			# if found:
			# 	self._errorReset('Login: ' + found.group(1))
			# 	return
			#===================================================================
			start = html.find('<p class="errorMessage">FEHLER:&nbsp;')
			if start != -1:
				start = start + len('<p class="errorMessage">FEHLER:&nbsp;')
				self._errorReset('Login: ' + html[start, html.find('</p>', start)])
				return
		if self._callScreen:
			self._callScreen.close()
		url = "http://%s/cgi-bin/webcm" % config.plugins.FritzCall.hostname.value
		parms = urlencode({
			'getpage':'../html/reboot.html',
			'var:lang':'de',
			'var:pagename':'reset',
			'var:menu':'system',
			'logic:command/reboot':'../gateway/commands/saveconfig.html',
			'sid':self._md5Sid
			})
		self.debug("[FritzCallFBF_05_27] _reset url: '" + url + "' parms: '" + parms + "'")
		getPage(url,
			method = "POST",
			agent = USERAGENT,
			headers = {
					'Content-Type': "application/x-www-form-urlencoded",
					'Content-Length': str(len(parms))},
			postdata = parms)

	def _okReset(self, html):  # @UnusedVariable # pylint: disable=W0613
		self.debug("[FritzCallFBF_05_27] _okReset")

	def _errorReset(self, error):
		self.debug("[FritzCallFBF_05_27] _errorReset: %s", error)
		text = _("FRITZ!Box - Error resetting: %s") % error.getErrorMessage()
		self._notify(text)

	def _readBlacklist(self):
		# http://fritz.box/cgi-bin/webcm?getpage=../html/de/menus/menu2.html&var:lang=de&var:menu=fon&var:pagename=sperre
		url = "http://%s/fon_num/sperre.lua" % config.plugins.FritzCall.hostname.value
		parms = urlencode({
			'sid':self._md5Sid
			})
		self.debug("[FritzCallFBF_05_27] _readBlacklist url: '" + url + "' parms: '" + parms + "'")
		getPage(url,
			method = "POST",
			agent = USERAGENT,
			headers = {
					'Content-Type': "application/x-www-form-urlencoded",
					'Content-Length': str(len(parms))},
			postdata = parms).addCallback(self._okBlacklist).addErrback(self._errorBlacklist)

	def _okBlacklist(self, html):
		self.debug("[FritzCallFBF_05_27] _okBlacklist")
		#=======================================================================
		# linkP = open("/tmp/FritzCallBlacklist.htm", "w")
		# linkP.write(html)
		# linkP.close()
		#=======================================================================
		entries = re.compile(r'<span title="(?:Ankommende|Ausgehende) Rufe">(Ankommende|Ausgehende) Rufe</span></nobr></td><td><nobr><span title="[\d]+">([\d]+)</span>', re.S).finditer(html)
		self.blacklist = ([], [])
		for entry in entries:
			if entry.group(1) == "Ankommende":
				self.blacklist[0].append(entry.group(2))
			else:
				self.blacklist[1].append(entry.group(2))
		self.debug("[FritzCallFBF_05_27] _okBlacklist: %s", repr(self.blacklist))

	def _errorBlacklist(self, error):
		self.debug("[FritzCallFBF_05_27] _errorBlacklist: %s", error)
		text = _("FRITZ!Box - Error getting blacklist: %s") % error.getErrorMessage()
		self._notify(text)

class FritzCallFBF_05_50(object):
	logger = logging.getLogger("FritzCall.FBF_05_50")
	debug = logger.debug
	info = logger.info
	warn = logger.warn
	error = logger.error
	exception = logger.exception

	def __init__(self):
		self.debug("")
		self._callScreen = None
		self._callType = config.plugins.FritzCall.fbfCalls.value
		self.password = decode(config.plugins.FritzCall.password.value)
		self.guestPassword = decode(config.plugins.FritzCall.guestPassword.value)
		self._phoneBookID = '0'
		self.blacklist = ([], [])
		self.information = None  # (boxInfo, upTime, ipAddress, wlanState, dslState, tamActive, dectActive, guestAccess)
		self.phonebook = None
		self.getInfo(None)
		# self.readBlacklist() now in getInfo

	def _notify(self, text):
		self.debug(text)
		if self._callScreen:
			self.debug("try to close callScreen")
			self._callScreen.close()
			self._callScreen = None
		Notifications.AddNotification(MessageBox, text, type = MessageBox.TYPE_ERROR, timeout = config.plugins.FritzCall.timeout.value)

	def _login(self, callback = None):
		# http://fritz.box/login_lua.xml
		url = "http://%s/login_sid.lua" % (config.plugins.FritzCall.hostname.value)
		self.debug(time.ctime() + " :" + url)
		getPage(url,
			method = "GET",
			headers = {'Content-Type': "application/x-www-form-urlencoded"}).addCallback(self._md5Login, callback).addErrback(self._errorLogin)

	def _md5Login(self, sidXml, callback):
		def buildResponse(challenge, text):
			self.debug("challenge: " + challenge + ' text: ' + __(text))
			text = (challenge + '-' + text).decode('utf-8', 'ignore').encode('utf-16-le')
			for i in range(len(text)):  # consider-using-enumerate # pylint: disable=
				if ord(text[i]) > 255:
					text[i] = '.'
			md5 = hashlib.md5()
			md5.update(text)  # pylint: disable=e1101
			self.debug(md5.hexdigest())
			return challenge + '-' + md5.hexdigest()

		#=======================================================================
		# linkP = open("/tmp/FritzDebug_sid.xml", "w")
		# linkP.write(sidXml)
		# linkP.close()
		#=======================================================================

		self.debug("")
		sidX = ET.fromstring(sidXml)
	#===========================================================================
	# 	self._md5Sid = sidX.find("SID").text
	# 	if self._md5Sid:
	# 		self.debug("SID "+ self._md5Sid)
	# 	else:
	# 		self.debug("no sid! That must be an old firmware.")
	# 		self._notify(_("FRITZ!Box - Error logging in\n\n") + _("wrong firmware version?"))
	# 		return
	#
	# 	if self._md5Sid != "0000000000000000":
	# 		self.debug("SID "+ self._md5Sid)
	# 		for callback in self._loginCallbacks:
	# 			self.debug("calling " + callback.__name__)
	# 			callback(None)
	# 		self._loginCallbacks = []
	# 		return
	#===========================================================================

		challenge = sidX.find("Challenge").text
		if challenge:
			self.debug("challenge " + challenge)
		else:
			self.error("login necessary and no challenge! That is terribly wrong.")

		parms = urlencode({
						'username': config.plugins.FritzCall.username.value,
						'response': buildResponse(challenge, self.password),
						})
		url = "http://%s/login_sid.lua" % (config.plugins.FritzCall.hostname.value)
		self.debug(url + "?" + parms)
		getPage(url,
			method = "POST",
			agent = USERAGENT,
			headers = {'Content-Type': "application/x-www-form-urlencoded", 'Content-Length': str(len(parms))},
			postdata = parms).addCallback(self._gotPageLogin, callback).addErrback(self._errorLogin)

	def _gotPageLogin(self, sidXml, callback):
		if self._callScreen:
			self._callScreen.updateStatus(_("login verification"))

		#=======================================================================
		# linkP = open("/tmp/sid.xml", "w")
		# linkP.write(sidXml)
		# linkP.close()
		#=======================================================================

		sidX = ET.fromstring(sidXml)
		md5Sid = sidX.find("SID").text
		if md5Sid and md5Sid != "0000000000000000":
			self.logger.debug("found sid: " + md5Sid)
		else:
			self.error("found no sid")
			self._notify(_("FRITZ!Box - Error logging in\n\n") + _("wrong user or password?"))
			return

		if self._callScreen:
			self._callScreen.updateStatus(_("login ok"))

		self.debug("calling " + callback.__name__)
		callback(md5Sid)

	def _errorLogin(self, error):
		global fritzbox  # global-variable-undefined # pylint: disable=W0601
		if type(error).__name__ == "str":
			text = error
		else:
			text = error.getErrorMessage()
		text = _("FRITZ!Box - Error logging in: %s\nDisabling plugin.") % text
		fritzbox = None
		self.exception(error)
		self._notify(text)

	def _logout(self, md5Sid, what):
		parms = urlencode({
						'sid':md5Sid,
						'logout':'bye bye Fritz'
						})
		url = "http://%s/login_sid.lua" % (config.plugins.FritzCall.hostname.value)
		self.debug("(" + what + ") " + time.ctime() + ": " + url + "?" + parms)
		getPage(url,
			method = "POST",
			agent = USERAGENT,
			headers = {'Content-Type': "application/x-www-form-urlencoded", 'Content-Length': str(len(parms))},
			postdata = parms).addErrback(self._errorLogout)

	def _errorLogout(self, error):
		self.exception(error)
		text = _("FRITZ!Box - Error logging out: %s") % error.getErrorMessage()
		self._notify(text)

	def loadFritzBoxPhonebook(self, phonebook):
		self.phonebook = phonebook
		self._login(self._selectFritzBoxPhonebook)

	def _selectFritzBoxPhonebook(self, md5Sid, html = None):  # pylint: disable=W0613
		parms = urlencode({
						'sid':md5Sid,
						})
		url = "http://%s/fon_num/fonbook_select.lua" % (config.plugins.FritzCall.hostname.value)
		self.debug(url + "?" + parms)
		getPage(url,
			method = "POST",
			agent = USERAGENT,
			headers = {'Content-Type': "application/x-www-form-urlencoded", 'Content-Length': str(len(parms))},
			postdata = parms).addCallback(self._loadFritzBoxPhonebook, md5Sid).addErrback(self._errorLoad, md5Sid)

	def _loadFritzBoxPhonebook(self, html, md5Sid):
		# Firmware 05.27 onwards
		# look for phonebook called [dD]reambox and get bookid
		found = re.match(r'.*<label for="uiBookid:([\d]+)">' + config.plugins.FritzCall.fritzphonebookName.value, html, re.S)
		if found:
			bookid = found.group(1)
		else:
			bookid = 1
		self.debug("phonebook %s", bookid)

		# http://192.168.178.1/fon_num/fonbook_list.lua?sid=2faec13b0000f3a2
		parms = urlencode({
						'bookid':bookid,
						'sid':md5Sid,
						'cancel':'',
						'apply':'uiApply',
						})
		url = "http://%s/fon_num/fonbook_select.lua" % (config.plugins.FritzCall.hostname.value)
		self.debug(url + "?" + parms)
		getPage(url,
			method = "POST",
			agent = USERAGENT,
			headers = {'Content-Type': "application/x-www-form-urlencoded", 'Content-Length': str(len(parms))},
			postdata = parms).addCallback(self._parseFritzBoxPhonebook, md5Sid).addErrback(self._errorLoad, md5Sid)

	def _parseFritzBoxPhonebook(self, html, md5Sid):
		self.debug("")
		# first, let us get the charset
		found = re.match(r'.*<meta http-equiv=content-type content="text/html; charset=([^"]*)">', html, re.S)
		if found:
			charset = found.group(1)
			self.debug("found charset: " + charset)
			if charset != 'utf-8':
				html = html2unicode(html.replace(chr(0xf6), '').decode(charset)).encode('utf-8')
		else:  # this is kind of emergency conversion...
			try:
				self.debug("try charset utf-8")
				charset = 'utf-8'
				html = html2unicode(html.decode('utf-8')).encode('utf-8')  # this looks silly, but has to be
			except UnicodeDecodeError:
				self.debug("try charset iso-8859-1")
				charset = 'iso-8859-1'
				html = html2unicode(html.decode('iso-8859-1')).encode('utf-8')  # this looks silly, but has to be

		# cleanout hrefs
		html = re.sub("<a href[^>]*>", "", html)
		html = re.sub("</a>", "", html)

		#=======================================================================
		# linkP = open("/tmp/FritzCall_Phonebook.htm", "w")
		# linkP.write(html)
		# linkP.close()
		#=======================================================================

		if html.find('class="zebra_reverse"') != -1:
			entrymask = re.compile(r'<td class="tname" title="([^"]*)">[^<]*</td><td class="tnum"(?: datalabel="[^"]*")?>([^<]+(?:<br>[^<]+)*)</td><td class="ttype">([^<]+(?:<br>[^<]+)*)</td><td class="tcode"(?: datalabel="[^"]*")?>([^<]*(?:<br>[^<]*)*)</td><td class="tvanity"(?: datalabel="[^"]*")?>([^<]*(?:<br>[^<]*)*)</td>', re.S)
			entries = entrymask.finditer(html)
			for found in entries:
				# self.info("processing entry for '''%s'''" % repr(found.groups()))
				name = html2unicode(re.sub(",", "", found.group(1)))
				thisnumbers = found.group(2).split("<br>")
				thistypes = found.group(3).split("<br>")
				thiscodes = found.group(4).split("<br>")
				thisvanitys = found.group(5).split("<br>")
				for i in range(len(thisnumbers)):  # consider-using-enumerate # pylint: disable=
					if len(thisnumbers[i]) == 0:
						continue
					thisnumber = cleanNumber(thisnumbers[i])
					if thisnumber in self.phonebook.phonebook:
						# self.debug("Ignoring '%s' ('%s') with %s' ( have: '%s')" % (name, thistypes[i], __(thisnumber), self.phonebook.phonebook[thisnumber]))
						continue

					if not thisnumbers[i]:
						# self.debug("Ignoring entry with empty number for '''%s'''" % (__(name)))
						continue
					else:
						thisname = name.decode('utf-8')
						if config.plugins.FritzCall.showType.value and thistypes[i]:
							thisname = thisname + " (" + thistypes[i].decode('utf-8') + ")"
						if config.plugins.FritzCall.showShortcut.value and thiscodes[i]:
							thisname = thisname + ", " + _("Shortcut") + ": " + thiscodes[i]
						if config.plugins.FritzCall.showVanity.value and thisvanitys[i]:
							thisname = thisname + ", " + _("Vanity") + ": " + thisvanitys[i]

						# self.debug("Adding '''%s''' with '''%s'''" % (__(thisname.strip()), __(thisnumber, False)))
						# self.debug("Adding '''%s''' with '''%s'''" % (thisname.strip(), thisnumber))
						# Beware: strings in phonebook.phonebook have to be in utf-8!
						self.phonebook.phonebook[thisnumber] = thisname.encode('utf-8')
		else:
			self._notify(_("Could not parse FRITZ!Box Phonebook entry"))
		self._logout(md5Sid, "_parseFritzBoxPhonebook")

	def _errorLoad(self, error, md5Sid):
		self.exception(error)
		text = _("FRITZ!Box - ") + _("Could not load phonebook: %s") % error.getErrorMessage()
		self._notify(text)
		self._logout(md5Sid, "_errorLoad")

	def getCalls(self, callScreen, callback, callType):
		#
		# FW 05.27 onwards
		#
		self.debug("")
		self._callScreen = callScreen
		self._callType = callType
		self._login(lambda md5Sid:self._getCalls(callback, md5Sid))

	def _getCalls(self, callback, md5Sid):  # pylint: disable=W0613
		self.debug("")
		if self._callScreen:
			self._callScreen.updateStatus(_("preparing"))
		# besser csv mit: https://fritz.box/fon_num/foncalls_list.lua?sid=dea373c2d0257a41&csv=
		parms = urlencode({'sid':md5Sid, 'csv':''})
		url = "http://%s/fon_num/foncalls_list.lua?%s" % (config.plugins.FritzCall.hostname.value, parms)
		getPage(url).addCallback(lambda x:self._gotPageCalls(callback, x, md5Sid)).addErrback(self._errorCalls, md5Sid)

	def _gotPageCalls(self, callback, csvString = "", md5Sid = ""):

		self.debug("")
		if self._callScreen:
			self._callScreen.updateStatus(_("finishing"))

		callListL = []
		if config.plugins.FritzCall.filter.value and config.plugins.FritzCall.filterCallList.value:
			filtermsns = [x.strip() for x in config.plugins.FritzCall.filtermsn.value.split(",")]
			self.info("filtermsns %s", repr(map(__, filtermsns)))
		else:
			filtermsns = None

		#=======================================================================
		# linkP = open("/tmp/FritzCalls.csv", "w")
		# linkP.write(csvString)
		# linkP.close()
		#=======================================================================

		# 0: direct; 1: date; 2: Name; 3: Nummer; 4: Nebenstelle; 5: Eigene Rufnumme; 6: Dauer
		calls = csv.reader(StringIO.StringIO(csvString), delimiter = ';')
		calls.next()  # skip sep
		calls.next()  # skip header line
		for call in calls:
			if len(call) != 7:
				self.warn("skip %s len: %s", repr(call), str(len(call)))
				continue
			direct = call[0]
			if direct == '1':
				direct = FBF_IN_CALLS
			elif direct == '4':
				direct = FBF_OUT_CALLS
			elif direct == '2':
				direct = FBF_MISSED_CALLS
			elif direct == '3':
				direct = FBF_BLOCKED_CALLS
			if self._callType != '.' and self._callType != direct:
				continue

			date = call[1]
			length = call[6]

			here = call[5]
			start = here.find('Internet: ')
			if start != -1:
				start += len('Internet: ')
				here = here[start:]

			if filtermsns and here not in filtermsns:
				# self.debug("skip %s" % (here))
				continue

			if call[4]:
				here = resolveNumber(here, call[4] + " (" + here + ")", self.phonebook)
			else:
				here = resolveNumber(here, "", self.phonebook)
			# self.debug("here: " + here)

			number = stripCbCPrefix(call[3], config.plugins.FritzCall.country.value)
			if config.plugins.FritzCall.prefix.value and number and number[0] != '0':  # should only happen for outgoing
				number = config.plugins.FritzCall.prefix.value + number
			# self.debug("number: " + number)

			found = re.match(r"\d+ \((\d+)\)", call[2])
			if found:
				remote = resolveNumber(number, resolveNumber(found.group(1), None, self.phonebook), self.phonebook)
			else:
				remote = resolveNumber(number, re.sub(",", "", call[2]), self.phonebook)
			# self.debug("remote. " + remote)

			# self.debug("append: %s" % repr((__(number, False), date, direct, __(remote), length, __(here))))
			# self.debug("append: %s" % repr((number, date, direct, remote, length, here)))
			callListL.append((number, date, direct, remote, length, here))

		if callback:
			# self.debug("call callback with\n" + text
			callback(callListL)
		self._callScreen = None
		self._logout(md5Sid, "_gotPageCalls")

	def _errorCalls(self, error, md5Sid):
		self.exception(error)
		text = _("FRITZ!Box - Could not load calls: %s") % error.getErrorMessage()
		self._notify(text)
		self._logout(md5Sid, "_errorCalls")

	def dial(self, number):
		''' initiate a call to number '''
		self._login(lambda md5Sid: self._dial(number, md5Sid))

	def _dial(self, number, md5Sid):
		url = "http://%s/cgi-bin/webcm" % config.plugins.FritzCall.hostname.value
		parms = urlencode({
			'getpage':'../html/de/menus/menu2.html',
			'var:pagename':'fonbuch',
			'var:menu':'home',
			'telcfg:settings/UseClickToDial':'1',
			'telcfg:settings/DialPort':config.plugins.FritzCall.extension.value,
			'telcfg:command/Dial':number,
			'sid':md5Sid
			})
		self.info("url: " + url + "?" + parms)
		getPage(url,
			method = "POST",
			agent = USERAGENT,
			headers = {
					'Content-Type': "application/x-www-form-urlencoded",
					'Content-Length': str(len(parms))},
			postdata = parms).addCallback(self._okDial, md5Sid).addErrback(self._errorDial, md5Sid)

	def _okDial(self, html, md5Sid):  # @UnusedVariable # pylint: disable=W0613
		self.debug("")
		if html:
			found = re.match(r'.*<p class="ErrorMsg">([^<]*)</p>', html, re.S)
			if found:
				self._notify(found.group(1))
		self._logout(md5Sid, "_okDial")

	def _errorDial(self, error, md5Sid):
		self.exception(error)
		text = _("FRITZ!Box - Dialling failed: %s") % error.getErrorMessage()
		self._notify(text)
		self._logout(md5Sid, "_errorDial")

	def changeWLAN(self, statusWLAN, callback):
		''' get status information from FBF '''
		self.debug("")
		#=======================================================================
		# Notifications.AddNotification(MessageBox, _("not available with this firmware version"), type=MessageBox.TYPE_ERROR, timeout=config.plugins.FritzCall.timeout.value)
		# return
		#=======================================================================

		if not statusWLAN or (statusWLAN != '1' and statusWLAN != '0'):
			return
		self._login(lambda md5Sid: self._changeWLAN(statusWLAN, callback, md5Sid))

	def _changeWLAN(self, statusWLAN, callback, md5Sid):
		if statusWLAN == '0':
			parms = urlencode({
				'sid':md5Sid,
				'apply':'',
				'cancel':'',
				'btn_refresh':''
				})
		else:
			parms = urlencode({
				'sid':md5Sid,
				'active':'on',
				'active_24':'on',
				'active_5':'on',
				'hidden_ssid':'on',
				'apply':'',
				'cancel':'',
				'btn_refresh':''
				})

		url = "http://%s//wlan/wlan_settings.lua" % config.plugins.FritzCall.hostname.value
		self.debug("url: " + url + "?" + parms)
		getPage(url,
			method = "POST",
			agent = USERAGENT,
			headers = {
					'Content-Type': "application/x-www-form-urlencoded"},
			postdata = parms).addCallback(self._okChangeWLAN, callback, md5Sid).addErrback(self._errorChangeWLAN, md5Sid)

	def _okChangeWLAN(self, html, callback, md5Sid):  # @UnusedVariable # pylint: disable=W0613
		self.debug("")
		if html:
			found = re.match(r'.*<p class="ErrorMsg">([^<]*)</p>', html, re.S)
			if found:
				self._notify(found.group(1))
		callback()
		self._logout(md5Sid, "_okChangeWLAN")

	def _errorChangeWLAN(self, error, md5Sid):
		self.exception(error)
		text = _("FRITZ!Box - Failed changing WLAN: %s") % error.getErrorMessage()
		self._notify(text)
		self._logout(md5Sid, "_errorChangeWLAN")

	def changeGuestAccess(self, statusGuestAccess, callback):
		self.debug("")
# 		if not statusGuestAccess:
# 			return
		self._login(lambda md5Sid: self._changeGuestAccessWLAN(statusGuestAccess, callback, md5Sid))

	def _changeGuestAccessWLAN(self, statusGuestAccess, callback, md5Sid):
		parms = {
				'sid':md5Sid,
				'autoupdate':'on',
				'btnSave':'',
				'btnChancel':''
		}
		if statusGuestAccess.find('WLAN') != -1:
			parms.update({
					'print':'',
			})
		else:
			parms.update({
					'activate_guest_access':'on',
					'guest_ssid':config.plugins.FritzCall.guestSSID.value,
					'disconnect_guest_access':'on',
					})
			if config.plugins.FritzCall.guestUptime.value:
				parms.update({
							'down_time_activ':'on',
							'down_time_value':config.plugins.FritzCall.guestUptime.value,
							'disconnect_guest_access':'on',
					})
			if config.plugins.FritzCall.guestSecure.value:
				parms.update({
							'sec_mode':'4',
							'wpa_key': self.guestPassword,
							})
			else:
				parms.update({
							'sec_mode':'5',
							})
		parms = urlencode(parms)

		url = "http://%s/wlan/guest_access.lua" % config.plugins.FritzCall.hostname.value
		self.debug("url: " + url + "?" + parms)
		getPage(url,
			method = "POST",
			agent = USERAGENT,
			headers = {
					'Content-Type': "application/x-www-form-urlencoded"},
			postdata = parms).addCallback(self._okChangeGuestAccess, callback, md5Sid).addErrback(self._errorChangeGuestAccess, md5Sid)

	def _okChangeGuestAccess(self, html, callback, md5Sid):  # @UnusedVariable # pylint: disable=W0613
		self.debug("")
		if html:
			found = re.match(r'.*<p class="ErrorMsg">([^<]*)</p>', html, re.S)
			if found:
				self._notify(found.group(1))
		callback()
		self._logout(md5Sid, "_okChangeGuestAccess")

	def _errorChangeGuestAccess(self, error, md5Sid):
		self.exception(error)
		text = _("FRITZ!Box - Failed changing GuestAccess: %s") % error.getErrorMessage()
		self._notify(text)
		self._logout(md5Sid, "_errorChangeGuestAccess")

	def changeMailbox(self, whichMailbox, callback):  # @UnusedVariable # pylint: disable=W0613
		''' switch mailbox on/off '''
		self.debug("start: " + str(whichMailbox))
		Notifications.AddNotification(MessageBox, _("not available with this firmware version"), type = MessageBox.TYPE_ERROR, timeout = config.plugins.FritzCall.timeout.value)

	def getInfo(self, callback):
		''' get status information from FBF '''
		self.debug("")
		self._login(lambda md5Sid: self._getInfo(callback, md5Sid))

	def _getInfo(self, callback, md5Sid):
		self.debug("verify login")

		self._login(self._readBlacklist)

		url = "http://%s/home/home.lua" % config.plugins.FritzCall.hostname.value
		parms = urlencode({
			'sid':md5Sid
			})
		self.debug("url: " + url + "?" + parms)
		getPage(url,
			method = "POST",
			agent = USERAGENT,
			headers = {
					'Content-Type': "application/x-www-form-urlencoded",
					'Content-Length': str(len(parms))},
			postdata = parms).addCallback(lambda x:self._okGetInfo(callback, x, md5Sid)).addErrback(self._errorGetInfo, md5Sid)

	def _okGetInfo(self, callback, html, md5Sid):

		self.debug("")

		#=======================================================================
		# linkP = open("/tmp/FritzCallInfo.htm", "w")
		# linkP.write(html)
		# linkP.close()
		#=======================================================================

		(boxInfo, upTime, ipAddress, wlanState, dslState, tamActive, dectActive, faxActive, rufumlActive, guestAccess) = (None, None, None, None, None, None, None, None, None, None)  # @UnusedVariable # pylint: disable=W0613

		found = re.match(r'.*<table id="tProdukt" class="tborder"> <tr> <td style="[^"]*" >([^<]*)</td> <td style="[^"]*" class="td_right">([^<]*)<a target="[^"]*" onclick="[^"]*" href="[^"]*">([^<]*)</a></td> ', html, re.S)
		if found:
			boxInfo = found.group(1) + '\n' + found.group(2) + found.group(3)
			boxInfo = boxInfo.replace('&nbsp;', ' ')
			self.info("Boxinfo: " + boxInfo)

		found = re.match(r'.*<div id=\'ipv._info\'><span class="[^"]*">verbunden seit ([^<]*)</span>', html, re.S)
		if found:
			upTime = found.group(1)
			self.info("upTime: " + upTime)

		ipAddress = ""
		found = re.match(r'.*IP-Adresse: ([^<]*)</span>', html, re.S)
		if found:
			ipAddress = found.group(1)
			self.info("ipAddress v4: " + ipAddress)
		found = re.match(r'.*IPv6-Präfix: ([^<]*)</span>', html, re.S)
		if found:
			if ipAddress:
				ipAddress = ipAddress + ' / ' + found.group(1)
			else:
				ipAddress = found.group(1)
			self.info("ipAddress v6: " + ipAddress)

		# dslState = [ state, information, unused ]; state == '5' means up, everything else down
		found = re.match(r'.*<tr id="uiTrDsl"><td class="(led_gray|led_green|led_red)">', html, re.S)
		if found:
			if found.group(1) == "led_green":
				dslState = ['5', None, None]
				found = re.match(r'.*<a href="[^"]*">(DSL|Kabel)</a></td><td(?: )?>(?:bereit|verbunden), ([^<]*)<img src=\'[^\']*\' height=\'[^\']*\'>&nbsp;([^<]*)<img src=\'[^\']*\' height=\'[^\']*\'></td></tr>', html, re.S)
				if found:
					dslState[1] = found.group(2) + " / " + found.group(3)
					dslState[2] = found.group(1)
			else:
				dslState = ['0', None, None]
		self.info("dslState: " + repr(dslState))

		# wlanstate = [ active, encrypted, no of devices ]
		# encrypted == 2 means unknown
		#                                      <tr id="uiTrWlan"><td class="led_green"></td><td><a href="/wlan/wlan_settings.lua?sid=9c824da3ecfc7168">WLAN</a></td><td title="an
		# <tr id="uiTrWlan"><td class="led_green"></td><td><a href="/wlan/wlan_settings.lua?sid=af3b8ddd6a9176da">WLAN</a></td><td title="an">an, Funknetz: mms</td></tr>
		found = re.match(r'.*<tr id="uiTrWlan"><td class="(led_gray|led_green|led_red)"></td><td><a href="[^"]*">WLAN</a></td><td title="(aus|an[^"]*)">([^<]*)</td>', html, re.S)
		if found:
			if found.group(1) == "led_green":
				if found.group(2):
					wlanState = ['1', '2', '', '']
					found1 = re.match(r'.*an, ([^"]+)', found.group(2), re.S)
					if not found1:
						found1 = re.match(r'.*an, ([^"]+)', found.group(3), re.S)
					if found1:
						wlans = found1.group(1)
					else:
						wlanState = ['0', '0', '', '']
					found = re.match(r'.*Funknetz: ([^,"]*)', wlans, re.S)
					if found:
						wlanState[3] = found.group(1)
					found = re.match(r'.*Funknetz \(2,4 GHz\): ([^,"]*)', wlans, re.S)
					if found:
						wlanState[3] = "2,4Ghz: " + found.group(1)
					found = re.match(r'.*Funknetz \(5 GHz\): ([^,"]*)', wlans, re.S)
					if found:
						if wlanState[3]:
							wlanState[3] = wlanState[3] + " 5Ghz: " + found.group(1)
						else:
							wlanState[3] = "5Ghz: " + found.group(1)
				else:
					# das ist wahrscheinlich alles falsch hier...
					if found.group(3) and found.group(3).find(", gesichert") != -1:
						wlanState = ['1', '1', '']
					else:
						wlanState = ['1', '0', '']
			else:
				wlanState = ['0', '0', '0']
			self.info("wlanState: " + repr(wlanState))

		#=======================================================================
		# found = re.match(r'.*<tr id="trTam" style=""><td><a href="[^"]*">Anrufbeantworter</a></td><td title=\'[^\']*\'>([\d]+) aktiv([^<]*)</td></tr>', html, re.S)
		# if found:
		# 	# found.group(2) could be ', neue Nachrichten vorhanden'; ignore for now
		# 	tamActive = [ found.group(1), False, False, False, False, False]
		# self.debug("tamActive: " + repr(tamActive))
		#=======================================================================

		found = re.match(r'.*<tr id="uiTrDect"><td class="(led_gray|led_green|led_red)"></td><td><a href="[^"]*">DECT</a></td><td>(?:aus|an, (ein|\d*) Schnurlostelefon)', html, re.S)
		if found:
			self.debug("dectActive: " + repr(found.groups()))
			if found.group(1) == "led_green":
				dectActive = found.group(2)
				self.info("dectActive: " + repr(dectActive))

		found = re.match(r'.*<tr (?:style="")?><td><a href="[^"]*">Faxfunktion</a></td><td>Integriertes Fax aktiv</td>', html, re.S)
		if found:
			faxActive = True
			self.info("faxActive: " + repr(faxActive))

		found = re.match(r'.*Rufumleitung</a></td><td>aktiv</td>', html, re.S)
		if found:
			rufumlActive = -1  # means no number available
			self.info("rufumlActive: " + repr(rufumlActive))

		guestAccess = ""
# 		found = re.match(r'.*WLAN-Gastzugang</a></td><td title="[^"]*">aktiv ([^<]*)</td>', html, re.S)
# 		if found:
# 			# guestAccess =  "WLAN " + found.group(1)
# 			if found.group(1).find(", gesichert"):
# 				guestAccess =  "WLAN (gesichert)"
# 			else:
# 				guestAccess =  "WLAN (ungesichert)"
# 			self.debug("guestAccess WLAN: " + repr(guestAccess))
# 		found = re.match(r'.*LAN-Gastzugang</a></td><td title="aktiv">aktiv</td>', html, re.S)
# 		if found:
# 			if guestAccess:
# 				guestAccess =  guestAccess + ", LAN"
# 			else:
# 				guestAccess = "LAN"
# 			self.debug("guestAccess LAN: " + repr(guestAccess))
		# WLAN-Gastzugang</a></td><td title="aktiv (2,4 GHz), gesichert, 29 Minuten verbleiben, 0 Geräte">aktiv (2,4 GHz), gesichert, 29 Minuten verbleiben, 0 Geräte</td>
		# found = re.match(r'.*linktxt": "WLAN-Gastzugang",\s*"details": "aktiv \(([^\)]+)\)(, (ungesichert|gesichert))?,( (\d+) (Minuten|Stunden) verbleiben,)? (\d+ Geräte), ([^"]+)",\s*"link": "wGuest"', html, re.S)
		found = re.match(r'.*WLAN-Gastzugang</a></td><td title="[^"]*">aktiv \(([^\)]+)\)(, (ungesichert|gesichert))?,( (\d+) (Minuten|Stunden) verbleiben,)? (\d+ Gerät(?:e)?)(, (?:Funknetz: )?([^<]+))?</td>', html, re.S)
		if found:
			# guestAccess =  "WLAN " + found.group(1)
			if found.group(2):
				if found.group(3).find('ungesichert') != -1:
					guestAccess = "WLAN (unges.)"
				else:
					guestAccess = "WLAN (ges.)"
			else:
				guestAccess = "WLAN"
# 			if found.group(1):
# 				guestAccess = guestAccess + ', ' + found.group(1).replace('\\', '')
			if found.group(4):
				if found.group(6) == 'Minuten':
					guestAccess = guestAccess + ', ' + found.group(5) + ' Min.'  # n Minuten verbleiben
				else:
					guestAccess = guestAccess + ', ' + found.group(5) + ' Std.'  # n Stunden verbleiben
			if found.group(7):
				guestAccess = guestAccess + ', ' + found.group(7)  # Geräte
			if found.group(8):
				guestAccess = guestAccess + ', ' + found.group(9)  # WLAN Name
			self.info("guestAccess WLAN: " + repr(guestAccess))

		info = (boxInfo, upTime, ipAddress, wlanState, dslState, tamActive, dectActive, faxActive, rufumlActive, guestAccess)
		self.info("Information: " + str(info))
		self.information = info
		if callback:
			callback(info)
		self._logout(md5Sid, "_okGetInfo")

	def _errorGetInfo(self, error, md5Sid):
		self.exception(error)
		text = _("FRITZ!Box - Error getting status: %s") % error.getErrorMessage()
		self._notify(text)
		self._logout(md5Sid, "_errorGetInfo")

	def reset(self):
		self._login(self._reset)

	def _reset(self, md5Sid):
		if self._callScreen:
			self._callScreen.close()

		url = "http://%s/system/reboot.lua" % config.plugins.FritzCall.hostname.value
		parms = urlencode({
			'reboot':'',
			'sid':md5Sid
			})
		self.debug("url: " + url + "?" + parms)
		getPage(url,
			method = "POST",
			agent = USERAGENT,
			headers = {
					'Content-Type': "application/x-www-form-urlencoded"},
			postdata = parms).addCallback(self._okReset, md5Sid).addErrback(self._errorReset, md5Sid)

	def _okReset(self, html, md5Sid):  # @UnusedVariable # pylint: disable=W0613
		self.debug("")
		#=======================================================================
		# linkP = open("/tmp/_okReset.htm", "w")
		# linkP.write(html)
		# linkP.close()
		#=======================================================================
		if html:
			found = re.match(r'.*<p class="ErrorMsg">([^<]*)</p>', html, re.S)
			if found:
				self._notify(found.group(1))
		self._logout(md5Sid, "_okReset")

	def _errorReset(self, error, md5Sid):
		self.exception(error)
		text = _("FRITZ!Box - Error resetting: %s") % error.getErrorMessage()
		self._notify(text)
		self._logout(md5Sid, "_errorReset")

	def _readBlacklist(self, md5Sid):
		# http://fritz.box/cgi-bin/webcm?getpage=../html/de/menus/menu2.html&var:lang=de&var:menu=fon&var:pagename=sperre
		url = "http://%s/fon_num/sperre.lua" % config.plugins.FritzCall.hostname.value
		parms = urlencode({
			'sid':md5Sid
			})
		self.debug("url: " + url + "?" + parms)
		getPage(url,
			method = "POST",
			agent = USERAGENT,
			headers = {
					'Content-Type': "application/x-www-form-urlencoded",
					'Content-Length': str(len(parms))},
			postdata = parms).addCallback(self._okBlacklist, md5Sid).addErrback(self._errorBlacklist, md5Sid)

	def _okBlacklist(self, html, md5Sid):
		self.debug("")
		#=======================================================================
		# linkP = open("/tmp/FritzCallBlacklist.htm", "w")
		# linkP.write(html)
		# linkP.close()
		#=======================================================================
		entries = re.compile(r'<span title="(?:Ankommende|Ausgehende) Rufe">(Ankommende|Ausgehende) Rufe</span></nobr></td><td><nobr><span title="[\d]+">([\d]+)</span>', re.S).finditer(html)
		self.blacklist = ([], [])
		for entry in entries:
			if entry.group(1) == "Ankommende":
				self.blacklist[0].append(entry.group(2))
			else:
				self.blacklist[1].append(entry.group(2))
		entries = re.compile(r'<tr><td>(Ankommende|Ausgehende) Rufe</td><td>([\d]+)</td>', re.S).finditer(html)
		for entry in entries:
			if entry.group(1) == "Ankommende":
				self.blacklist[0].append(entry.group(2))
			else:
				self.blacklist[1].append(entry.group(2))
		entries = re.compile(r'<TD>(Ankommende|Ausgehende) Rufe</TD>\s+<TD>([\d]+)</TD>', re.S).finditer(html)
		for entry in entries:
			if entry.group(1) == "Ankommende":
				self.blacklist[0].append(entry.group(2))
			else:
				self.blacklist[1].append(entry.group(2))
		self.debug(repr(self.blacklist))
		self._logout(md5Sid, "_okBlacklist")

	def _errorBlacklist(self, error, md5Sid):
		self.exception(error)
		text = _("FRITZ!Box - Error getting blacklist: %s") % error.getErrorMessage()
		self._notify(text)
		self._logout(md5Sid, "_errorBlacklist")

class FritzCallFBF_06_35(object):
	logger = logging.getLogger("FritzCall.FBF_06_35")
	debug = logger.debug
	info = logger.info
	warn = logger.warn
	error = logger.error
	exception = logger.exception

	def __init__(self):
		self.debug("")
		self._callScreen = None
		self._callType = config.plugins.FritzCall.fbfCalls.value
		self.password = decode(config.plugins.FritzCall.password.value)
		self.guestPassword = decode(config.plugins.FritzCall.guestPassword.value)
		self._phoneBookID = '0'
		self.blacklist = ([], [])
		self.information = None  # (boxInfo, upTime, ipAddress, wlanState, dslState, tamActive, dectActive, guestAccess)
		self.phonebook = None
		self.getInfo(None)
		# self.readBlacklist() now in getInfo

	def _notify(self, text):
		self.info(text)
		if self._callScreen:
			self.debug("try to close callScreen")
			self._callScreen.close()
			self._callScreen = None
		Notifications.AddNotification(MessageBox, text, type = MessageBox.TYPE_ERROR, timeout = config.plugins.FritzCall.timeout.value)

	def _login(self, callback = None):
		# http://fritz.box/login_lua.xml
		url = "http://%s/login_sid.lua" % (config.plugins.FritzCall.hostname.value)
		self.debug(time.ctime() + " :" + url)
		getPage(url,
			method = "GET",
			headers = {'Content-Type': "application/x-www-form-urlencoded"}).addCallback(self._md5Login, callback).addErrback(self._errorLogin)

	def _md5Login(self, sidXml, callback):
		def buildResponse(challenge, text):
			self.debug("_md5Login: challenge: " + challenge + ' text: ' + __(text))
			text = (challenge + '-' + text).decode('utf-8', 'ignore').encode('utf-16-le')
			for i in range(len(text)):  # consider-using-enumerate # pylint: disable=
				if ord(text[i]) > 255:
					text[i] = '.'
			md5 = hashlib.md5()
			md5.update(text)  # pylint: disable=e1101
			self.debug("_md5Login: " + md5.hexdigest())
			return challenge + '-' + md5.hexdigest()

		#=======================================================================
		# linkP = open("/tmp/FritzDebug_sid.xml", "w")
		# linkP.write(sidXml)
		# linkP.close()
		#=======================================================================

		self.debug("")
		sidX = ET.fromstring(sidXml)
	#===========================================================================
	# 	self._md5Sid = sidX.find("SID").text
	# 	if self._md5Sid:
	# 		self.debug("SID "+ self._md5Sid)
	# 	else:
	# 		self.debug("no sid! That must be an old firmware.")
	# 		self._notify(_("FRITZ!Box - Error logging in\n\n") + _("wrong firmware version?"))
	# 		return
	#
	# 	if self._md5Sid != "0000000000000000":
	# 		self.debug("SID "+ self._md5Sid)
	# 		for callback in self._loginCallbacks:
	# 			self.debug("calling " + callback.__name__)
	# 			callback(None)
	# 		self._loginCallbacks = []
	# 		return
	#===========================================================================

		challenge = sidX.find("Challenge").text
		if challenge:
			self.debug("challenge " + challenge)
		else:
			self.error("login necessary and no challenge! That is terribly wrong.")

		parms = urlencode({
						'username': config.plugins.FritzCall.username.value,
						'response': buildResponse(challenge, self.password),
						})
		url = "http://%s/login_sid.lua" % (config.plugins.FritzCall.hostname.value)
		self.debug(url + "?" + parms)
		getPage(url,
			method = "POST",
			agent = USERAGENT,
			headers = {'Content-Type': "application/x-www-form-urlencoded", 'Content-Length': str(len(parms))},
			postdata = parms).addCallback(self._gotPageLogin, callback).addErrback(self._errorLogin)

	def _gotPageLogin(self, sidXml, callback):
		if self._callScreen:
			self._callScreen.updateStatus(_("login verification"))

		#=======================================================================
		# linkP = open("/tmp/sid.xml", "w")
		# linkP.write(sidXml)
		# linkP.close()
		#=======================================================================

		sidX = ET.fromstring(sidXml)
		md5Sid = sidX.find("SID").text
		if md5Sid and md5Sid != "0000000000000000":
			self.debug("found sid: " + md5Sid)
		else:
			self.error("found no sid")
			self._notify(_("FRITZ!Box - Error logging in\n\n") + _("wrong user or password?"))
			return

		if self._callScreen:
			self._callScreen.updateStatus(_("login ok"))

		self.info("calling " + callback.__name__)
		callback(md5Sid)

	def _errorLogin(self, error):
		global fritzbox  # global-variable-undefined # pylint: disable=W0601
		if type(error).__name__ == "str":
			text = error
		else:
			text = error.getErrorMessage()
		text = _("FRITZ!Box - Error logging in: %s\nDisabling plugin.") % text
		fritzbox = None
		self.exception(error)
		self._notify(text)

	def _logout(self, md5Sid, what):
		parms = urlencode({
						'sid':md5Sid,
						'logout':'bye bye Fritz'
						})
		url = "http://%s/login_sid.lua" % (config.plugins.FritzCall.hostname.value)
		self.debug("(" + what + ") " + time.ctime() + ": " + url + "?" + parms)
		getPage(url,
			method = "POST",
			agent = USERAGENT,
			headers = {'Content-Type': "application/x-www-form-urlencoded", 'Content-Length': str(len(parms))},
			postdata = parms).addErrback(self._errorLogout)

	def _errorLogout(self, error):
		text = _("FRITZ!Box - Error logging out: %s") % error.getErrorMessage()
		self.exception(error)
		self._notify(text)

	def loadFritzBoxPhonebook(self, phonebook):
		self.phonebook = phonebook
		self._login(self._loadFritzBoxPhonebook)

	def _loadFritzBoxPhonebook(self, md5Sid):

		parms = urlencode({
						'sid':md5Sid,
						'page':'bookLi'
						})
		url = "http://%s/data.lua" % (config.plugins.FritzCall.hostname.value)
		self.debug(url + "?" + parms)
		getPage(url,
			method = "POST",
			agent = USERAGENT,
			headers = {'Content-Type': "application/x-www-form-urlencoded", 'Content-Length': str(len(parms))},
			postdata = parms).addCallback(self._parseFritzBoxPhonebook, md5Sid).addErrback(self._errorLoad, md5Sid)

	def _parseFritzBoxPhonebook(self, html, md5Sid):
		self.debug("")
		# first, let us get the charset
		try:
			self.debug("try charset utf-8")
			html = html2unicode(html.decode('utf-8')).encode('utf-8')  # this looks silly, but has to be
		except UnicodeDecodeError:
			self.debug("try charset iso-8859-1")
			html = html2unicode(html.decode('iso-8859-1')).encode('utf-8')  # this looks silly, but has to be

		# cleanout hrefs
		html = re.sub("<a href[^>]*>", "", html)
		html = re.sub("</a>", "", html)

		if self.logger.getEffectiveLevel() == logging.DEBUG:
			linkP = open("/tmp/FritzCall_Phonebook.htm", "w")
			linkP.write(html)
			linkP.close()

		entrymask = re.compile(r'<td class="tname" title="([^"]*)">[^<]*</td><td class="tnum"(?: datalabel="[^"]*")?>((?:<a class="print"[^>]+>)?[^<]+(?:<br>(?:<a class="print"[^>]+>)?[^<]+)*)</td><td class="ttype"(?: datalabel="[^"]*")?>([^<]*(?:<br>[^<]*)*)</td><td class="tcode"(?: datalabel="[^"]*")?>([^<]*(?:<br>[^<]*)*)</td><td class="tvanity"(?: datalabel="[^"]*")?>([^<]*(?:<br>[^<]*)*)</td>', re.S)
		entries = entrymask.finditer(html)
		for found in entries:
			# self.debug("processing entry for '''%s'''" % repr(found.groups()))
			name = html2unicode(re.sub(",", "", found.group(1)))
			thisnumbers = found.group(2).split("<br>")
			thistypes = found.group(3).split("<br>")
			thiscodes = found.group(4).split("<br>")
			thisvanitys = found.group(5).split("<br>")
			for i in range(len(thisnumbers)):  # consider-using-enumerate # pylint: disable=
				if len(thisnumbers[i]) == 0:
					continue
				thisnumber = cleanNumber(thisnumbers[i])
				if thisnumber in self.phonebook.phonebook:
					# self.debug("Ignoring '%s' ('%s') with %s' ( have: '%s')" % (name, thistypes[i], __(thisnumber), self.phonebook.phonebook[thisnumber]))
					continue

				if not thisnumbers[i]:
					# self.debug("Ignoring entry with empty number for '''%s'''" % (__(name)))
					continue
				else:
					thisname = name.decode('utf-8')
					if config.plugins.FritzCall.showType.value and thistypes[i]:
						thisname = thisname + " (" + thistypes[i].decode('utf-8') + ")"
					if config.plugins.FritzCall.showShortcut.value and thiscodes[i]:
						thisname = thisname + ", " + _("Shortcut") + ": " + thiscodes[i]
					if config.plugins.FritzCall.showVanity.value and thisvanitys[i]:
						thisname = thisname + ", " + _("Vanity") + ": " + thisvanitys[i]

					# self.debug("Adding '''%s''' with '''%s'''" % (__(thisname.strip()), __(thisnumber, False)))
					# self.debug("Adding '''%s''' with '''%s'''" % (thisname.strip(), thisnumber))
					# Beware: strings in phonebook.phonebook have to be in utf-8!
					self.phonebook.phonebook[thisnumber] = thisname.encode('utf-8')

		self._logout(md5Sid, "_parseFritzBoxPhonebook")

	def _errorLoad(self, error, md5Sid):
		text = _("FRITZ!Box - ") + _("Could not load phonebook: %s") % error.getErrorMessage()
		self.exception(error)
		self._notify(text)
		self._logout(md5Sid, "_errorLoad")

	def getCalls(self, callScreen, callback, callType):
		self.debug("")
		self._callScreen = callScreen
		self._callType = callType
		self._login(lambda md5Sid:self._getCalls(callback, md5Sid))

	def _getCalls(self, callback, md5Sid):  # pylint: disable=W0613
		self.debug("")
		if self._callScreen:
			self._callScreen.updateStatus(_("preparing"))
		# besser csv mit: https://fritz.box/fon_num/foncalls_list.lua?sid=dea373c2d0257a41&csv=
		parms = urlencode({'sid':md5Sid, 'csv':''})
		url = "http://%s/fon_num/foncalls_list.lua?%s" % (config.plugins.FritzCall.hostname.value, parms)
		getPage(url).addCallback(lambda x:self._gotPageCalls(callback, x, md5Sid)).addErrback(self._errorCalls, md5Sid)

	def _gotPageCalls(self, callback, csvString = "", md5Sid = ""):

		self.debug("")
		if self._callScreen:
			self._callScreen.updateStatus(_("finishing"))

		callListL = []
		if config.plugins.FritzCall.filter.value and config.plugins.FritzCall.filterCallList.value:
			filtermsns = [x.strip() for x in config.plugins.FritzCall.filtermsn.value.split(",")]
			self.info("filtermsns %s", repr(map(__, filtermsns)))
		else:
			filtermsns = None

		#=======================================================================
		# linkP = open("/tmp/FritzCalls.csv", "w")
		# linkP.write(csvString)
		# linkP.close()
		#=======================================================================

		# 0: direct; 1: date; 2: Name; 3: Nummer; 4: Nebenstelle; 5: Eigene Rufnumme; 6: Dauer
		calls = csv.reader(StringIO.StringIO(csvString), delimiter = ';')
		calls.next()  # skip sep
		calls.next()  # skip header line

		for call in calls:
			if len(call) != 7:
				self.warn("skip %s len: %s", repr(call), str(len(call)))
				continue
			direct = call[0]
			if direct == '1':
				direct = FBF_IN_CALLS
			elif direct == '4':
				direct = FBF_OUT_CALLS
			elif direct == '2':
				direct = FBF_MISSED_CALLS
			elif direct == '3':
				direct = FBF_BLOCKED_CALLS
			if self._callType != '.' and self._callType != direct:
				continue
			date = call[1]
			length = call[6]

			here = call[5]
			start = here.find('Internet: ')
			if start != -1:
				start += len('Internet: ')
				here = here[start:]

			if filtermsns and here not in filtermsns:
				# self.debug("skip %s" % (here))
				continue

			if call[4]:
				here = resolveNumber(here, call[4] + " (" + here + ")", self.phonebook)
			else:
				here = resolveNumber(here, "", self.phonebook)
			# self.debug("here: " + here)

			number = stripCbCPrefix(call[3], config.plugins.FritzCall.country.value)
			if config.plugins.FritzCall.prefix.value and number and number[0] != '0':  # should only happen for outgoing
				number = config.plugins.FritzCall.prefix.value + number
			# self.debug("number: " + number)

			found = re.match(r"\d+ \((\d+)\)", call[2])
			if found:
				remote = resolveNumber(number, resolveNumber(found.group(1), None, self.phonebook), self.phonebook)
			else:
				remote = resolveNumber(number, re.sub(",", "", call[2]), self.phonebook)
			# self.debug("remote. " + remote)

			# self.debug("append: %s" % repr((__(number, False), date, direct, __(remote), length, __(here))))
			# self.debug("ppend: %s" % repr((number, date, direct, remote, length, here)))
			callListL.append((number, date, direct, remote, length, here))

		if callback:
			# self.debug("call callback with\n" + text
			callback(callListL)
		self._callScreen = None
		self._logout(md5Sid, "_gotPageCalls")

	def _errorCalls(self, error, md5Sid):
		text = _("FRITZ!Box - Could not load calls: %s") % error.getErrorMessage()
		self.exception(error)
		self._notify(text)
		self._logout(md5Sid, "_errorCalls")

	def dial(self, number):  # @UnusedVariable # pylint: disable=W0613
		'''
		Dial a number on extension config.plugins.FritzCall.extension.value

		@param number: number to dial
		@type number: string
		'''
		self.debug("")
		Notifications.AddNotification(MessageBox, _("not available with this firmware version"), type = MessageBox.TYPE_ERROR, timeout = config.plugins.FritzCall.timeout.value)

	def changeWLAN(self, statusWLAN, callback):
		'''
		Change the status of the WLAN

		@param state: '0' means: turn off, '1' turn on
		@type state: string
		'''
		self.debug("")
		#=======================================================================
		# Notifications.AddNotification(MessageBox, _("not available with this firmware version"), type=MessageBox.TYPE_ERROR, timeout=config.plugins.FritzCall.timeout.value)
		# return
		#=======================================================================

		if not statusWLAN or (statusWLAN != '1' and statusWLAN != '0'):
			return
		self._login(lambda md5Sid: self._changeWLAN(statusWLAN, callback, md5Sid))

	def _changeWLAN(self, statusWLAN, callback, md5Sid):
		if statusWLAN == '0':
			parms = urlencode({
				'sid':md5Sid,
				'apply':'',
				'cancel':'',
				'btn_refresh':''
				})
		else:
			parms = urlencode({
				'sid':md5Sid,
				'active':'on',
				'active_24':'on',
				'active_5':'on',
				'hidden_ssid':'on',
				'apply':'',
				'cancel':'',
				'btn_refresh':''
				})

		url = "http://%s//wlan/wlan_settings.lua" % config.plugins.FritzCall.hostname.value
		self.debug("url: " + url + "?" + parms)
		getPage(url,
			method = "POST",
			agent = USERAGENT,
			headers = {
					'Content-Type': "application/x-www-form-urlencoded"},
			postdata = parms).addCallback(self._okChangeWLAN, callback, md5Sid).addErrback(self._errorChangeWLAN, md5Sid)

	def _okChangeWLAN(self, html, callback, md5Sid):  # @UnusedVariable # pylint: disable=W0613
		self.debug("")
		if html:
			found = re.match(r'.*<p class="ErrorMsg">([^<]*)</p>', html, re.S)
			if found:
				self._notify(found.group(1))
		callback()
		self._logout(md5Sid, "_okChangeWLAN")

	def _errorChangeWLAN(self, error, md5Sid):
		text = _("FRITZ!Box - Failed changing WLAN: %s") % error.getErrorMessage()
		self.exception(error)
		self._notify(text)
		self._logout(md5Sid, "_errorChangeWLAN")

	def changeGuestAccess(self, statusGuestAccess, callback):
		'''
		Change the status of the WLAN guest access

		@param statusGuestAccess: 'WLAN', 'WLAN, LAN' or 'LAN'
		@type statusGuestAccess: string
		'''
		self.debug("")
# 		if not statusGuestAccess:
# 			return
		self._login(lambda md5Sid: self._changeGuestAccessWLAN(statusGuestAccess, callback, md5Sid))

	def _changeGuestAccessWLAN(self, statusGuestAccess, callback, md5Sid):
		parms = {
			'sid':md5Sid,
			'autoupdate':'on',
			'apply':'',
			'oldpage':'/wlan/guest_access.lua',
			}

		if statusGuestAccess.find('WLAN') != -1:
			parms.update({
				'print':'',
				})
		else:
			parms.update({
				'activate_guest_access':'on',
				'guest_ssid':config.plugins.FritzCall.guestSSID.value,
				})
			if config.plugins.FritzCall.guestUptime.value:
				parms.update({
							'down_time_activ': 'on',
							'down_time_value': config.plugins.FritzCall.guestUptime.value,
							'disconnect_guest_access': 'on',
							})
			if config.plugins.FritzCall.guestSecure.value:
				parms.update({
					'sec_mode':'3',
					'wpa_key': self.guestPassword,
					})
			else:
				parms.update({
					'sec_mode':'5',
					})
		parms = urlencode(parms)

		url = "http://%s/data.lua" % config.plugins.FritzCall.hostname.value
		self.debug("url: " + url + "?" + parms)
		getPage(url,
			method = "POST",
			agent = USERAGENT,
			headers = {
					'Content-Type': "application/x-www-form-urlencoded"},
			postdata = parms).addCallback(self._okChangeGuestAccess, callback, md5Sid).addErrback(self._errorChangeGuestAccess, md5Sid)

	def _okChangeGuestAccess(self, html, callback, md5Sid):  # @UnusedVariable # pylint: disable=W0613
		self.debug("")
		if html:
			found = re.match(r'.*<p class="ErrorMsg">([^<]*)</p>', html, re.S)
			if found:
				self._notify(found.group(1))
		callback()
		self._logout(md5Sid, "_okChangeGuestAccess")

	def _errorChangeGuestAccess(self, error, md5Sid):
		text = _("FRITZ!Box - Failed changing GuestAccess: %s") % error.getErrorMessage()
		self.exception(error)
		self._notify(text)
		self._logout(md5Sid, "_errorChangeGuestAccess")

	def changeMailbox(self, whichMailbox, callback):  # @UnusedVariable # pylint: disable=W0613
		'''
		Toggle mailbox status

		@param which: number, which mailbox to toggle; '-1' means all
		@type which: string
		'''
		self.debug("")
		Notifications.AddNotification(MessageBox, _("not available with this firmware version"), type = MessageBox.TYPE_ERROR, timeout = config.plugins.FritzCall.timeout.value)

	def getInfo(self, callback):
		'''
		Retrieve information from box and fill in self.information and self.blacklist
		'''
		self.debug("")
		self._login(lambda md5Sid: self._getInfo(callback, md5Sid))

	def _getInfo(self, callback, md5Sid):
		self.debug("verify login")

		self._login(self._readBlacklist)

		url = "http://%s/data.lua" % config.plugins.FritzCall.hostname.value
		parms = urlencode({
			'sid':md5Sid,
			'page':'overview',
			'type':'all'
			})
		self.debug("url: " + url + "?" + parms)
		getPage(url,
			method = "POST",
			agent = USERAGENT,
			headers = {
					'Content-Type': "application/x-www-form-urlencoded",
					'Content-Length': str(len(parms))},
			postdata = parms).addCallback(lambda x:self._okGetInfo(callback, x, md5Sid)).addErrback(self._errorGetInfo, md5Sid)

	def _okGetInfo(self, callback, html, md5Sid):

		self.debug("")

		if self.logger.getEffectiveLevel() == logging.DEBUG:
			linkP = open("/tmp/FritzCallGetInfo.lua", "w")
			linkP.write(html)
			linkP.close()

		(boxInfo, upTime, ipAddress, wlanState, dslState, tamActive, dectActive, faxActive, rufumlActive, guestAccess) = (None, None, None, None, None, None, None, None, None, None)  # @UnusedVariable # pylint: disable=W0613

		boxData = json.loads(html)["data"]

		fritzOs = boxData["fritzos"]
		if fritzOs["Productname"]:
			boxInfo = fritzOs["Productname"]
			if fritzOs["nspver"]:
				boxInfo = boxInfo + " FRITZ!OS: " + fritzOs["nspver"]
			if fritzOs["isLabor"] and fritzOs["isLabor"] == "true":
				boxInfo = boxInfo + " Labor"
			if fritzOs["isUpdateAvail"]:
				boxInfo = boxInfo + " (" + _("Update available") + ")"

			boxInfo1 = ""
			if fritzOs["fb_name"]:
				boxInfo1 = "Name: " + fritzOs["fb_name"]
			if boxData["fonnum"] and boxData["fonnum"]["txt"]:
				boxInfo1 = boxInfo1 + (", " if boxInfo1 else "") + boxData["fonnum"]["txt"]
			if boxData["tamcalls"] and boxData["tamcalls"]["count"]:
				boxInfo1 = boxInfo1 + (", " if boxInfo1 else "") + str(boxData["tamcalls"]["count"]) + " " + _("calls in mailbox")
			if boxInfo1:
				boxInfo = boxInfo + "\n" + boxInfo1

		boxInfo = boxInfo.encode("utf-8")

		self.info("Boxinfo: " + repr(boxInfo))

		provider = None
		if "ipv4" in boxData and "txt" in boxData["ipv4"]:
			for item in boxData["ipv4"]["txt"]:
				item = item.encode("utf-8")
				found = re.match(r'.*verbunden seit (.*)', item, re.S)
				if found:
					upTime = found.group(1)
				found = re.match(r'\s*Anbieter: (.*)', item, re.S)
				if found:
					provider = found.group(1)
				found = re.match(r'IP(?:v4)?-Adresse: (.*)', item, re.S)
				if found:
					ipAddress = found.group(1)

		self.info("upTime: " + repr(upTime))
		self.info("provider: " + repr(provider))
		self.info("ipAddress: " + repr(ipAddress))

		if "ipv6" in boxData and "txt" in boxData["ipv6"]:
			upTime6 = None
			provider6 = None
			ipAddress6 = None
			for item in boxData["ipv6"]["txt"]:
				found = re.match(r'.*verbunden seit (.*)', item, re.S)
				if found:
					upTime6 = found.group(1).encode("utf-8")
				found = re.match(r'\s*Anbieter: (.*)', item, re.S)
				if found:
					provider6 = found.group(1).encode("utf-8")
				found = re.match(r'IP(?:v6)?-(?:Adresse|Prefix): (.*)', item, re.S)
				if found:
					ipAddress6 = found.group(1).encode("utf-8")

			self.info("upTime6: " + repr(upTime6))
			self.info("provider6: " + repr(provider6))
			self.info("ipAddress6: " + repr(ipAddress6))

			if upTime6:
				if upTime and upTime.find(upTime6) == -1:
					upTime = upTime + '/' + upTime6
				else:
					upTime = upTime6

			if provider6:
				if provider and provider.find(provider6) == -1:
					provider = provider + '/' + provider6
				else:
					provider = provider6

			if ipAddress6:
				if ipAddress:
					ipAddress = ipAddress + '/' + ipAddress6
				else:
					ipAddress = ipAddress6

		if provider:
			if upTime:
				upTime = upTime + ' mit ' + provider

		self.info("upTime final: " + repr(upTime))
		self.info("provider final: " + repr(provider))
		self.info("ipAddress final: " + repr(ipAddress))

		if "dsl" in boxData or "docsis" in boxData or "cable" in boxData:
			if "dsl" in boxData:
				connData = boxData["dsl"]
			elif "cable" in boxData:
				connData = boxData["cable"]
			else:
				connData = boxData["docsis"]
			if connData["led"] == "led_green":
				dslState = ['5', None, None]
				dslState[1] = connData["down"].encode("utf-8") + " / " + connData["up"].encode("utf-8")
				dslState[1] = dslState[1].replace('\\', '').encode("utf-8")
				dslState[2] = connData["title"].encode("utf-8")
		self.info("dslState: " + repr(dslState))

		if "wlan24" in boxData:
			wlan24 = boxData["wlan24"]
			if wlan24:
				netName = re.sub(r".*: ", "", wlan24["txt"]).encode("utf-8")
				if wlan24["led"] == "led_green":
					wlanState = ['1', '', '', "2,4GHz an: " + netName]
				else:
					wlanState = ['0', '', '', "2,4GHz aus: " + netName]
		self.info("wlanState24: " + repr(wlanState))

		if "wlan5" in boxData:
			wlan5 = boxData["wlan5"]
			if wlan5:
				netName = re.sub(r".*: ", "", wlan5["txt"]).encode("utf-8")
				if not wlanState:
					if wlan5["led"] == "led_green":
						wlanState = ['1', '', '', "5GHz an: " + netName]
					else:
						wlanState = ['0', '', '', "5GHz aus: " + netName]
				else:
					if wlan5["led"] == "led_green":
						wlanState[0] = '1'
						wlanState[3] = wlanState[3] + ", 5GHz an: " + netName
		self.info("wlanState5: " + repr(wlanState))

		if "dect" in boxData:
			dect = boxData["dect"]
			if dect and dect["led"] == "led_green":
				found = re.match(r'an, ([\d+]+|ein) Schnurlostelefon(?:e)? angemeldet', dect["txt"].encode("utf-8"), re.S)
				if found:
					dectActive = found.group(1)
		self.info("dectActive: " + repr(dectActive))

		self.debug("comfort")
		if "comfort" in boxData and "func" in boxData["comfort"]:
			comfortFuncs = boxData["comfort"]["func"]
			guestAccess = ""
			for fun in comfortFuncs:
				if "linktxt" in fun:
					if fun["linktxt"] == "Faxfunktion" and fun["details"] == "Integriertes Fax aktiv":
						faxActive = True
					elif fun["linktxt"] == "Rufumleitung" and fun["details"]:
						if fun["details"] != "deaktiviert":
							found = re.match(r'.*(?:(\d+) )?aktiv', fun["details"].encode("utf-8"), re.S)
							if found and found.group(1):
								rufumlActive = int(found.group(1))
							else:
								rufumlActive = -1  # means no number available
					elif fun["linktxt"] == "WLAN-Gastzugang" and fun["details"]:
						found = re.match(r'.*aktiv \([^\)]+\)(?:, (ungesichert|gesichert))?,(?: (\d+) (Minuten|Stunden) verbleiben,)? (\d+ Geräte), (.+)', fun["details"].encode("utf-8"), re.S)
						if found:
							if found.group(1):
								if found.group().find('ungesichert') != -1:
									guestAccess = "WLAN (unges.)"
								else:
									guestAccess = "WLAN (ges.)"
							else:
								guestAccess = "WLAN"
							if found.group(3):
								if found.group(3) == 'Minuten':
									guestAccess = guestAccess + ', ' + found.group(2) + ' Min.'  # n Minuten verbleiben
								else:
									guestAccess = guestAccess + ', ' + found.group(2) + ' Std.'  # n Stunden verbleiben
							if found.group(4):
								guestAccess = guestAccess + ', ' + found.group(4)  # Geräte
							if found.group(5):
								guestAccess = guestAccess + ', ' + found.group(5)  # WLAN Name
					elif fun["linktxt"] == "LAN-Gastzugang" and fun["details"]:
						if fun["details"] == "aktiv":
							if guestAccess:
								guestAccess = 'LAN, ' + guestAccess
							else:
								guestAccess = "LAN"

		self.info("faxActive: " + repr(faxActive))
		self.info("rufumlActive: " + repr(rufumlActive))
		self.info("guestAccess: " + repr(guestAccess))

		info = (boxInfo, upTime, ipAddress, wlanState, dslState, tamActive, dectActive, faxActive, rufumlActive, guestAccess)
		self.info("information: " + str(info))
		self.information = info
		if callback:
			callback(info)
		self._logout(md5Sid, "_okGetInfo")

	def _errorGetInfo(self, error, md5Sid):
		text = _("FRITZ!Box - Error getting status: %s") % error.getErrorMessage()
		self.exception(error)
		self._notify(text)
		self._logout(md5Sid, "_errorGetInfo")

	def reset(self):
		self._login(self._reset)

	def _reset(self, md5Sid):
		if self._callScreen:
			self._callScreen.close()

		url = "http://%s/system/reboot.lua" % config.plugins.FritzCall.hostname.value
		parms = urlencode({
			'reboot':'',
			'sid':md5Sid
			})
		self.debug("url: " + url + "?" + parms)
		getPage(url,
			method = "POST",
			agent = USERAGENT,
			headers = {
					'Content-Type': "application/x-www-form-urlencoded"},
			postdata = parms).addCallback(self._okReset, md5Sid).addErrback(self._errorReset, md5Sid)

	def _okReset(self, html, md5Sid):  # @UnusedVariable # pylint: disable=W0613
		self.debug("")
		#=======================================================================
		# linkP = open("/tmp/_okReset.htm", "w")
		# linkP.write(html)
		# linkP.close()
		#=======================================================================
		if html:
			found = re.match(r'.*<p class="ErrorMsg">([^<]*)</p>', html, re.S)
			if found:
				self._notify(found.group(1))
		self._logout(md5Sid, "_okReset")

	def _errorReset(self, error, md5Sid):
		text = _("FRITZ!Box - Error resetting: %s") % error.getErrorMessage()
		self.exception(error)
		self._notify(text)
		self._logout(md5Sid, "_errorReset")

	def _readBlacklist(self, md5Sid):
		# http://fritz.box/cgi-bin/webcm?getpage=../html/de/menus/menu2.html&var:lang=de&var:menu=fon&var:pagename=sperre
		# https://217.245.196.140:699/data.lua?xhr=1&sid=e8fcf4f9a9186070&lang=de&no_sidrenew=&page=callLock
		url = "http://%s/data.lua" % config.plugins.FritzCall.hostname.value
		parms = urlencode({
			'sid':md5Sid,
			'page':'callLock'
			})
		self.debug("url: " + url + "?" + parms)
		getPage(url,
			method = "POST",
			agent = USERAGENT,
			headers = {
					'Content-Type': "application/x-www-form-urlencoded",
					'Content-Length': str(len(parms))},
			postdata = parms).addCallback(self._okBlacklist, md5Sid).addErrback(self._errorBlacklist, md5Sid)

	def _okBlacklist(self, html, md5Sid):
		self.debug("")
# 		linkP = open("/tmp/FritzCallBlacklist.htm", "w")
# 		linkP.write(html)
# 		linkP.close()
		# entries = re.compile(r'<span title="(?:Ankommende|Ausgehende) Rufe">(Ankommende|Ausgehende) Rufe</span></nobr></td><td><nobr><span title="[\d]+">([\d]+)</span>', re.S).finditer(html)
		entries = re.compile(r'<tr><td(?: [^>]*)?>(Ankommende|Ausgehende) Rufe</td><td(?: datalabel="[^"]*")?>([\d]+)</td>', re.S).finditer(html)
		self.blacklist = ([], [])
		for entry in entries:
			if entry.group(1) == "Ankommende":
				self.blacklist[0].append(entry.group(2))
			else:
				self.blacklist[1].append(entry.group(2))
		entries = re.compile(r'<tr><td>(Ankommende|Ausgehende) Rufe</td><td>([\d]+)</td>', re.S).finditer(html)
		for entry in entries:
			if entry.group(1) == "Ankommende":
				self.blacklist[0].append(entry.group(2))
			else:
				self.blacklist[1].append(entry.group(2))
		entries = re.compile(r'<TD>(Ankommende|Ausgehende) Rufe</TD>\s+<TD>([\d]+)</TD>', re.S).finditer(html)
		for entry in entries:
			if entry.group(1) == "Ankommende":
				self.blacklist[0].append(entry.group(2))
			else:
				self.blacklist[1].append(entry.group(2))
		self.debug(repr(self.blacklist))
		self._logout(md5Sid, "_okBlacklist")

	def _errorBlacklist(self, error, md5Sid):
		text = _("FRITZ!Box - Error getting blacklist: %s") % error.getErrorMessage()
		self.exception(error)
		self._notify(text)
		self._logout(md5Sid, "_errorBlacklist")

class FritzCallFBF_dummy(object):
	logger = logging.getLogger("FritzCall.FBF_dummy")
	debug = logger.debug

	def __init__(self):
		'''

		'''
		self.debug("")
		self.password = decode(config.plugins.FritzCall.password.value)
		# self.information contains basic information about the (FBF) device:
		# (boxInfo, upTime, ipAddress, wlanState, dslState, tamActive, dectActive)
		# ('FRITZ!Box Fon WLAN 7390, FRITZ!OS 06.01', '21.01.2014, 05:02 Uhr', '87.185.104.85', ['0', '0', '0'], ['5', '6,7 Mbit/s / 667 kbit/s', None], None, '2', True, None)
		# boxinfo: basic information like type, fw version
		# uptime: up since when
		# ipAddress: external ip address
		# wlanState: status of WLAN: [ active, encrypted, no of devices active ]; active == '1' means active, encrypted == '0' means not encrypted
		# dslState: whether connected via DSL or not: [ state, information, unused ]; state == '5' means up, everything else down
		# tamActive: is a mailbox active: [ number of active mailboxes, infos, ... ]
		# dectActive: is a dect device registered: if dect is active set to the number of connected dect devices
		self.information = None

		# numbers, which are blacklisted in the FBF and calls from them should also not be shown
		self.blacklist = None

	def getCalls(self, callback, which):  # @UnusedVariable # pylint: disable=W0613
		'''
		Get list of recent calls in direction which (FBF_ALL_CALLS, FBF_IN_CALLS, FBF_MISSED_CALLS, FBF_OUT_CALLS)

		@param callback: function to be called with list of (number, date, direction, remote, length, here) entries
		@param which: direction of calls to be grabbed
		'''
		self.debug("")
		Notifications.AddNotification(MessageBox, _("not yet implemented"), type = MessageBox.TYPE_ERROR, timeout = config.plugins.FritzCall.timeout.value)

	def getInfo(self):
		'''
		Retrieve information from box and fill in self.information and self.blacklist
		'''
		self.debug("")
		Notifications.AddNotification(MessageBox, _("not yet implemented"), type = MessageBox.TYPE_ERROR, timeout = config.plugins.FritzCall.timeout.value)

	def loadFritzBoxPhonebook(self, phonebook):   # @UnusedVariable # pylint: disable=W0613
		'''
		Load phonebook from device and add it to the phonebook

		@param phonebook: phonebook to be amended
		@type phonebook: dictionary of number, information
		'''
		self.debug("")
		Notifications.AddNotification(MessageBox, _("not yet implemented"), type = MessageBox.TYPE_ERROR, timeout = config.plugins.FritzCall.timeout.value)

	def changeWLAN(self, state, callback):  # @UnusedVariable # pylint: disable=W0613
		'''
		Change the status of the WLAN

		@param state: '0' means: turn off, '1' turn on
		@type state: string
		'''
		self.debug("")
		Notifications.AddNotification(MessageBox, _("not yet implemented"), type = MessageBox.TYPE_ERROR, timeout = config.plugins.FritzCall.timeout.value)

	def changeGuestAccess(self, statusGuestAccess, callback):  # @UnusedVariable # pylint: disable=W0613
		'''
		Change the status of the WLAN guest access

		@param statusGuestAccess: 'WLAN', 'WLAN, LAN' or 'LAN'
		@type statusGuestAccess: string
		'''
		self.debug("")
		Notifications.AddNotification(MessageBox, _("not yet implemented"), type = MessageBox.TYPE_ERROR, timeout = config.plugins.FritzCall.timeout.value)

	def changeMailbox(self, which, callback):  # @UnusedVariable # pylint: disable=W0613
		'''
		Toggle mailbox status

		@param which: number, which mailbox to toggle; '-1' means all
		@type which: string
		'''
		self.debug("")
		Notifications.AddNotification(MessageBox, _("not yet implemented"), type = MessageBox.TYPE_ERROR, timeout = config.plugins.FritzCall.timeout.value)

	def dial(self, number):  # @UnusedVariable # pylint: disable=W0613
		'''
		Dial a number on extension config.plugins.FritzCall.extension.value

		@param number: number to dial
		@type number: string
		'''
		self.debug("")
		Notifications.AddNotification(MessageBox, _("not yet implemented"), type = MessageBox.TYPE_ERROR, timeout = config.plugins.FritzCall.timeout.value)

	def reset(self):
		'''
		Reset box
		'''
		self.debug("")
		Notifications.AddNotification(MessageBox, _("not yet implemented"), type = MessageBox.TYPE_ERROR, timeout = config.plugins.FritzCall.timeout.value)
