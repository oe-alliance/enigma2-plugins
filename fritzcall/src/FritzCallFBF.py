# -*- coding: utf-8 -*-
'''
Created on 30.09.2012
$Author: michael $
$Revision: 1 $
$Date: 2012-09-30 13:37:48 +0200 (Sun, 30 Sep 2012) $
$Id: plugin.py 685 2012-09-30 11:37:48Z michael $
'''

from . import _, debug #@UnresolvedImport # pylint: disable=E0611,F0401
from plugin import config, fritzbox, stripCbCPrefix, resolveNumberWithAvon, FBF_IN_CALLS, FBF_OUT_CALLS, FBF_MISSED_CALLS
from Tools import Notifications
from Screens.MessageBox import MessageBox
from twisted.web.client import getPage #@UnresolvedImport
from nrzuname import html2unicode

from urllib import urlencode 
import re, time, hashlib

FBF_boxInfo = 0
FBF_upTime = 1
FBF_ipAddress = 2
FBF_wlanState = 3
FBF_dslState = 4
FBF_tamActive = 5
FBF_dectActive = 6
FBF_faxActive = 7
FBF_rufumlActive = 8

class FritzCallFBF:
	def __init__(self):
		debug("[FritzCallFBF] __init__")
		self._callScreen = None
		self._md5LoginTimestamp = None
		self._md5Sid = '0000000000000000'
		self._callTimestamp = 0
		self._callList = []
		self._callType = config.plugins.FritzCall.fbfCalls.value
		self._phoneBookID = '0'
		self.info = None # (boxInfo, upTime, ipAddress, wlanState, dslState, tamActive, dectActive)
		self.getInfo(None)
		self.blacklist = ([], [])
		self.readBlacklist()
		self.phonebook = None

	def _notify(self, text):
		debug("[FritzCallFBF] notify: " + text)
		self._md5LoginTimestamp = None
		if self._callScreen:
			debug("[FritzCallFBF] notify: try to close callScreen")
			self._callScreen.close()
			self._callScreen = None
		Notifications.AddNotification(MessageBox, text, type=MessageBox.TYPE_ERROR, timeout=config.plugins.FritzCall.timeout.value)
			
	def _login(self, callback=None):
		debug("[FritzCallFBF] _login")
		if self._callScreen:
			self._callScreen.updateStatus(_("login"))
		if self._md5LoginTimestamp and ((time.time() - self._md5LoginTimestamp) < float(9.5*60)) and self._md5Sid != '0000000000000000': # new login after 9.5 minutes inactivity 
			debug("[FritzCallFBF] _login: renew timestamp: " + time.ctime(self._md5LoginTimestamp) + " time: " + time.ctime())
			self._md5LoginTimestamp = time.time()
			callback(None)
		else:
			debug("[FritzCallFBF] _login: not logged in or outdated login")
			# http://fritz.box/cgi-bin/webcm?getpage=../html/login_sid.xml
			parms = urlencode({'getpage':'../html/login_sid.xml'})
			url = "http://%s/cgi-bin/webcm" % (config.plugins.FritzCall.hostname.value)
			debug("[FritzCallFBF] _login: '" + url + "' parms: '" + parms + "'")
			getPage(url,
				method="POST",
				headers={'Content-Type': "application/x-www-form-urlencoded", 'Content-Length': str(len(parms))
						}, postdata=parms).addCallback(lambda x: self._md5Login(callback,x)).addErrback(lambda x:self._oldLogin(callback,x))

	def _oldLogin(self, callback, error): 
		debug("[FritzCallFBF] _oldLogin: " + repr(error))
		self._md5LoginTimestamp = None
		if config.plugins.FritzCall.password.value != "":
			parms = "login:command/password=%s" % (config.plugins.FritzCall.password.value)
			url = "http://%s/cgi-bin/webcm" % (config.plugins.FritzCall.hostname.value)
			debug("[FritzCallFBF] _oldLogin: '" + url + "' parms: '" + parms + "'")
			getPage(url,
				method="POST",
				agent="Mozilla/5.0 (Windows; U; Windows NT 6.0; de; rv:1.9.0.5) Gecko/2008120122 Firefox/3.0.5",
				headers={'Content-Type': "application/x-www-form-urlencoded", 'Content-Length': str(len(parms))
						}, postdata=parms).addCallback(self._gotPageLogin).addCallback(callback).addErrback(self._errorLogin)
		elif callback:
			debug("[FritzCallFBF] _oldLogin: no password, calling " + repr(callback))
			callback(None)

	def _md5Login(self, callback, sidXml):
		def buildResponse(challenge, text):
			debug("[FritzCallFBF] _md5Login7buildResponse: challenge: " + challenge + ' text: ' + text)
			text = (challenge + '-' + text).decode('utf-8','ignore').encode('utf-16-le')
			for i in range(len(text)):
				if ord(text[i]) > 255:
					text[i] = '.'
			md5 = hashlib.md5()
			md5.update(text)
			debug("[FritzCallFBF] md5Login/buildResponse: " + md5.hexdigest())
			return challenge + '-' + md5.hexdigest()

		debug("[FritzCallFBF] _md5Login")
		found = re.match('.*<SID>([^<]*)</SID>', sidXml, re.S)
		if found:
			self._md5Sid = found.group(1)
			debug("[FritzCallFBF] _md5Login: SID "+ self._md5Sid)
		else:
			debug("[FritzCallFBF] _md5Login: no sid! That must be an old firmware.")
			self._oldLogin(callback, 'No error')
			return

		debug("[FritzCallFBF] _md5Login: renew timestamp: " + time.ctime(self._md5LoginTimestamp) + " time: " + time.ctime())
		self._md5LoginTimestamp = time.time()
		if sidXml.find('<iswriteaccess>0</iswriteaccess>') != -1:
			debug("[FritzCallFBF] _md5Login: logging in")
			found = re.match('.*<Challenge>([^<]*)</Challenge>', sidXml, re.S)
			if found:
				challenge = found.group(1)
				debug("[FritzCallFBF] _md5Login: challenge " + challenge)
			else:
				challenge = None
				debug("[FritzCallFBF] _md5Login: login necessary and no challenge! That is terribly wrong.")
			parms = urlencode({
							'getpage':'../html/de/menus/menu2.html', # 'var:pagename':'home', 'var:menu':'home', 
							'login:command/response': buildResponse(challenge, config.plugins.FritzCall.password.value),
							})
			url = "http://%s/cgi-bin/webcm" % (config.plugins.FritzCall.hostname.value)
			debug("[FritzCallFBF] _md5Login: '" + url + "' parms: '" + parms + "'")
			getPage(url,
				method="POST",
				agent="Mozilla/5.0 (Windows; U; Windows NT 6.0; de; rv:1.9.0.5) Gecko/2008120122 Firefox/3.0.5",
				headers={'Content-Type': "application/x-www-form-urlencoded", 'Content-Length': str(len(parms))
						}, postdata=parms).addCallback(self._gotPageLogin).addCallback(callback).addErrback(self._errorLogin)
		elif callback: # we assume value 1 here, no login necessary
			debug("[FritzCallFBF] _md5Login: no login necessary")
			callback(None)

	def _gotPageLogin(self, html):
		if self._callScreen:
			self._callScreen.updateStatus(_("login verification"))
		debug("[FritzCallFBF] _gotPageLogin: verify login")
		start = html.find('<p class="errorMessage">FEHLER:&nbsp;')
		if start != -1:
			start = start + len('<p class="errorMessage">FEHLER:&nbsp;')
			text = _("FRITZ!Box - Error logging in\n\n") + html[start : html.find('</p>', start)]
			self._notify(text)
		else:
			if self._callScreen:
				self._callScreen.updateStatus(_("login ok"))

		found = re.match('.*<input type="hidden" name="sid" value="([^\"]*)"', html, re.S)
		if found:
			self._md5Sid = found.group(1)
			debug("[FritzCallFBF] _gotPageLogin: found sid: " + self._md5Sid)

	def _errorLogin(self, error):
		global fritzbox
		debug("[FritzCallFBF] _errorLogin: %s" % (error))
		text = _("FRITZ!Box - Error logging in: %s\nDisabling plugin.") % error.getErrorMessage()
		# config.plugins.FritzCall.enable.value = False
		fritzbox = None
		self._notify(text)

	def _logout(self):
		if self._md5LoginTimestamp:
			self._md5LoginTimestamp = None
			parms = urlencode({
							'getpage':'../html/de/menus/menu2.html', # 'var:pagename':'home', 'var:menu':'home', 
							'login:command/logout':'bye bye Fritz'
							})
			url = "http://%s/cgi-bin/webcm" % (config.plugins.FritzCall.hostname.value)
			debug("[FritzCallFBF] logout: '" + url + "' parms: '" + parms + "'")
			getPage(url,
				method="POST",
				agent="Mozilla/5.0 (Windows; U; Windows NT 6.0; de; rv:1.9.0.5) Gecko/2008120122 Firefox/3.0.5",
				headers={'Content-Type': "application/x-www-form-urlencoded", 'Content-Length': str(len(parms))
						}, postdata=parms).addErrback(self._errorLogout)

	def _errorLogout(self, error):
		debug("[FritzCallFBF] _errorLogout: %s" % (error))
		text = _("FRITZ!Box - Error logging out: %s") % error.getErrorMessage()
		self._notify(text)

	def loadFritzBoxPhonebook(self, phonebook):
		debug("[FritzCallFBF] loadFritzBoxPhonebook")
		if config.plugins.FritzCall.fritzphonebook.value:
			self.phonebook = phonebook
			self._phoneBookID = '0'
			debug("[FritzCallFBF] loadFritzBoxPhonebook: logging in")
			self._login(self._loadFritzBoxPhonebook)

	def _loadFritzBoxPhonebook(self, html):
		if html:
			#===================================================================
			# found = re.match('.*<p class="errorMessage">FEHLER:&nbsp;([^<]*)</p>', html, re.S)
			# if found:
			#	self._errorLoad('Login: ' + found.group(1))
			#	return
			#===================================================================
			start = html.find('<p class="errorMessage">FEHLER:&nbsp;')
			if start != -1:
				start = start + len('<p class="errorMessage">FEHLER:&nbsp;')
				self._errorLoad('Login: ' + html[start, html.find('</p>', start)])
				return
		parms = urlencode({
						'getpage':'../html/de/menus/menu2.html',
						'var:lang':'de',
						'var:pagename':'fonbuch',
						'var:menu':'fon',
						'sid':self._md5Sid,
						'telcfg:settings/Phonebook/Books/Select':self._phoneBookID, # this selects always the first phonbook first
						})
		url = "http://%s/cgi-bin/webcm" % (config.plugins.FritzCall.hostname.value)
		debug("[FritzCallFBF] _loadFritzBoxPhonebook: '" + url + "' parms: '" + parms + "'")
		getPage(url,
			method="POST",
			agent="Mozilla/5.0 (Windows; U; Windows NT 6.0; de; rv:1.9.0.5) Gecko/2008120122 Firefox/3.0.5",
			headers={'Content-Type': "application/x-www-form-urlencoded", 'Content-Length': str(len(parms))
					}, postdata=parms).addCallback(self._parseFritzBoxPhonebook).addErrback(self._errorLoad)

	def cleanNumber(self, number):
		number = number.replace('(','').replace(')','').replace(' ','').replace('-','')
		if number[0] == '+':
			number = '00' + number[1:]
		if number.startswith(config.plugins.FritzCall.country.value):
			number = '0' + number[len(config.plugins.FritzCall.country.value):]
		return number
			
	def _parseFritzBoxPhonebook(self, html):

		# debug("[FritzCallFBF] _parseFritzBoxPhonebook")

		# first, let us get the charset
		found = re.match('.*<meta http-equiv=content-type content="text/html; charset=([^"]*)">', html, re.S)
		if found:
			charset = found.group(1)
			debug("[FritzCallFBF] _parseFritzBoxPhonebook: found charset: " + charset)
			html = html2unicode(html.replace(chr(0xf6),'').decode(charset)).encode('utf-8')
		else: # this is kind of emergency conversion...
			try:
				debug("[FritzCallFBF] _parseFritzBoxPhonebook: try charset utf-8")
				charset = 'utf-8'
				html = html2unicode(html.decode('utf-8')).encode('utf-8') # this looks silly, but has to be
			except UnicodeDecodeError:
				debug("[FritzCallFBF] _parseFritzBoxPhonebook: try charset iso-8859-1")
				charset = 'iso-8859-1'
				html = html2unicode(html.decode('iso-8859-1')).encode('utf-8') # this looks silly, but has to be

		# if re.search('document.write\(TrFon1\(\)', html):
		if html.find('document.write(TrFon1()') != -1:
			#===============================================================================
			#				 New Style: 7270 (FW 54.04.58, 54.04.63-11941, 54.04.70, 54.04.74-14371, 54.04.76, PHONE Labor 54.04.80-16624)
			#							7170 (FW 29.04.70) 22.03.2009
			#							7141 (FW 40.04.68) 22.03.2009
			#  We expect one line with
			#   TrFonName(Entry umber, Name, ???, Path to picture)
			#  followed by several lines with
			#	TrFonNr(Type,Number,Shortcut,Vanity), which all belong to the name in TrFonName.
			# 
			#  Photo could be fetched with http://192.168.0.1/lua/photo.lua?photo=<Path to picture[7:]&sid=????
			#===============================================================================
			debug("[FritzCallFBF] _parseFritzBoxPhonebook: discovered newer firmware")
			found = re.match('.*<input type="hidden" name="telcfg:settings/Phonebook/Books/Name\d+" value="[Dd]reambox" id="uiPostPhonebookName\d+" disabled>\s*<input type="hidden" name="telcfg:settings/Phonebook/Books/Id\d+" value="(\d+)" id="uiPostPhonebookId\d+" disabled>', html, re.S)
			if found:
				phoneBookID = found.group(1)
				debug("[FritzCallFBF] _parseFritzBoxPhonebook: found dreambox phonebook with id: " + phoneBookID)
				if self._phoneBookID != phoneBookID:
					self._phoneBookID = phoneBookID
					debug("[FritzCallFBF] _parseFritzBoxPhonebook: reload phonebook")
					self._loadFritzBoxPhonebook(None) # reload with dreambox phonebook
					return

			entrymask = re.compile('(TrFonName\("[^"]+", "[^"]+", "[^"]*"(?:, "[^"]*")?\);.*?)document.write\(TrFon1\(\)', re.S)
			entries = entrymask.finditer(html)
			for entry in entries:
				# TrFonName (id, name, category)
				# TODO: replace re.match?
				found = re.match('TrFonName\("[^"]*", "([^"]+)", "[^"]*"(?:, "[^"]*")?\);', entry.group(1))
				if found:
					# debug("[FritzCallFBF] _parseFritzBoxPhonebook: name: %s" %found.group(1))
					name = found.group(1).replace(',','').strip()
				else:
					debug("[FritzCallFBF] _parseFritzBoxPhonebook: could not find name")
					continue
				# TrFonNr (type, rufnr, code, vanity)
				detailmask = re.compile('TrFonNr\("([^"]*)", "([^"]*)", "([^"]*)", "([^"]*)"\);', re.S)
				details = detailmask.finditer(entry.group(1))
				for found in details:
					thisnumber = found.group(2).strip()
					if not thisnumber:
						debug("[FritzCallFBF] Ignoring entry with empty number for '''%s'''" % (name))
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

						thisnumber = self.cleanNumber(thisnumber)
						# Beware: strings in phonebook.phonebook have to be in utf-8!
						if not self.phonebook.phonebook.has_key(thisnumber):
							debug("[FritzCallFBF] Adding '''%s''' with '''%s''' from FRITZ!Box Phonebook!" % (thisname.strip(), thisnumber))
							self.phonebook.phonebook[thisnumber] = thisname
						else:
							debug("[FritzCallFBF] Ignoring '''%s''' with '''%s''' from FRITZ!Box Phonebook!" % (thisname.strip(), thisnumber))

		# elif re.search('document.write\(TrFon\(', html):
		elif html.find('document.write(TrFon(') != -1:
			#===============================================================================
			#				Old Style: 7050 (FW 14.04.33)
			#	We expect one line with TrFon(No,Name,Number,Shortcut,Vanity)
			#   Encoding should be plain Ascii...
			#===============================================================================				
			entrymask = re.compile('TrFon\("[^"]*", "([^"]*)", "([^"]*)", "([^"]*)", "([^"]*)"\)', re.S)
			entries = entrymask.finditer(html)
			for found in entries:
				name = found.group(1).strip().replace(',','')
				# debug("[FritzCallFBF] pos: %s name: %s" %(found.group(0),name))
				thisnumber = found.group(2).strip()
				if config.plugins.FritzCall.showShortcut.value and found.group(3):
					name = name + ", " + _("Shortcut") + ": " + found.group(3)
				if config.plugins.FritzCall.showVanity.value and found.group(4):
					name = name + ", " + _("Vanity") + ": " + found.group(4)
				if thisnumber:
					# name = name.encode('utf-8')
					# Beware: strings in phonebook.phonebook have to be in utf-8!
					if not self.phonebook.phonebook.has_key(thisnumber):
						debug("[FritzCallFBF] Adding '''%s''' with '''%s''' from FRITZ!Box Phonebook!" % (name, thisnumber))
						self.phonebook.phonebook[thisnumber] = name
					else:
						debug("[FritzCallFBF] Ignoring '''%s''' with '''%s''' from FRITZ!Box Phonebook!" % (name, thisnumber))
				else:
					debug("[FritzCallFBF] ignoring empty number for %s" % name)
				continue
		elif self._md5Sid == '0000000000000000': # retry, it could be a race condition
			debug("[FritzCallFBF] _parseFritzBoxPhonebook: retry loading phonebook")
			self.loadFritzBoxPhonebook(self.phonebook)
		else:
			debug("[FritzCallFBF] _parseFritzBoxPhonebook: try loading new format phonebook...")
			self._loadFritzBoxPhonebookNew()

	def _loadFritzBoxPhonebookNew(self):
		# http://192.168.178.1/fon_num/fonbook_list.lua?sid=2faec13b0000f3a2
		parms = urlencode({
						'sid':self._md5Sid,
						})
		url = "http://%s/fon_num/fonbook_list.lua" % (config.plugins.FritzCall.hostname.value)
		debug("[FritzCallFBF] _loadFritzBoxPhonebookNew: '" + url + "' parms: '" + parms + "'")
		getPage(url,
			method="POST",
			agent="Mozilla/5.0 (Windows; U; Windows NT 6.0; de; rv:1.9.0.5) Gecko/2008120122 Firefox/3.0.5",
			headers={'Content-Type': "application/x-www-form-urlencoded", 'Content-Length': str(len(parms))
					}, postdata=parms).addCallback(self._parseFritzBoxPhonebookNew).addErrback(self._errorLoad)

	def _parseFritzBoxPhonebookNew(self, html):
		debug("[FritzCallFBF] _parseFritzBoxPhonebookNew")
		#=======================================================================
		# found = re.match('.*<input type="hidden" name="telcfg:settings/Phonebook/Books/Name\d+" value="[Dd]reambox" id="uiPostPhonebookName\d+" disabled>\s*<input type="hidden" name="telcfg:settings/Phonebook/Books/Id\d+" value="(\d+)" id="uiPostPhonebookId\d+" disabled>', html, re.S)
		# if found:
		#	phoneBookID = found.group(1)
		#	debug("[FritzCallFBF] _parseFritzBoxPhonebookNew: found dreambox phonebook with id: " + phoneBookID)
		#	if self._phoneBookID != phoneBookID:
		#		self._phoneBookID = phoneBookID
		#		debug("[FritzCallFBF] _parseFritzBoxPhonebookNew: reload phonebook")
		#		self._loadFritzBoxPhonebook(None) # reload with dreambox phonebook
		#		return
		#=======================================================================

		# first, let us get the charset
		found = re.match('.*<meta http-equiv=content-type content="text/html; charset=([^"]*)">', html, re.S)
		if found:
			charset = found.group(1)
			debug("[FritzCallFBF] _parseFritzBoxPhonebookNew: found charset: " + charset)
			html = html2unicode(html.replace(chr(0xf6),'').decode(charset)).encode('utf-8')
		else: # this is kind of emergency conversion...
			try:
				debug("[FritzCallFBF] _parseFritzBoxPhonebookNew: try charset utf-8")
				charset = 'utf-8'
				html = html2unicode(html.decode('utf-8')).encode('utf-8') # this looks silly, but has to be
			except UnicodeDecodeError:
				debug("[FritzCallFBF] _parseFritzBoxPhonebookNew: try charset iso-8859-1")
				charset = 'iso-8859-1'
				html = html2unicode(html.decode('iso-8859-1')).encode('utf-8') # this looks silly, but has to be

		#=======================================================================
		# linkP = open("/tmp/FritzCall_Phonebook.htm", "w")
		# linkP.write(html)
		# linkP.close()
		#=======================================================================

		if html.find('class="zebra_reverse"') != -1:
			debug("[FritzCallFBF] Found new 7390 firmware")
			# <td class="tname">Mama</td><td class="tnum">03602191620<br>015228924783<br>03602181567</td><td class="ttype">geschäftl.<br>mobil<br>privat</td><td class="tcode"><br>**701<br></td><td class="tvanity"><br>1<br></td>
			entrymask = re.compile('<td class="tname">([^<]*)</td><td class="tnum">([^<]+(?:<br>[^<]+)*)</td><td class="ttype">([^<]+(?:<br>[^<]+)*)</td><td class="tcode">([^<]*(?:<br>[^<]*)*)</td><td class="tvanity">([^<]*(?:<br>[^<]*)*)</td>', re.S)
			entries = entrymask.finditer(html)
			for found in entries:
				# debug("[FritzCallFBF] _parseFritzBoxPhonebookNew: processing entry for '''%s'''" % (found.group(1)))
				name = found.group(1)
				thisnumbers = found.group(2).split("<br>")
				thistypes = found.group(3).split("<br>")
				thiscodes = found.group(4).split("<br>")
				thisvanitys = found.group(5).split("<br>")
				for i in range(len(thisnumbers)):
					thisnumber = self.cleanNumber(thisnumbers[i])
					if self.phonebook.phonebook.has_key(thisnumber):
						debug("[FritzCallFBF] Ignoring '''%s''' with '''%s''' from FRITZ!Box Phonebook!" % (name, thisnumber))
						continue

					if not thisnumbers[i]:
						debug("[FritzCallFBF] _parseFritzBoxPhonebookNew: Ignoring entry with empty number for '''%s'''" % (name))
						continue
					else:
						thisname = name
						if config.plugins.FritzCall.showType.value and thistypes[i]:
							thisname = thisname + " (" + thistypes[i] + ")"
						if config.plugins.FritzCall.showShortcut.value and thiscodes[i]:
							thisname = thisname + ", " + _("Shortcut") + ": " + thiscodes[i]
						if config.plugins.FritzCall.showVanity.value and thisvanitys[i]:
							thisname = thisname + ", " + _("Vanity") + ": " + thisvanitys[i]
	
						debug("[FritzCallFBF] _parseFritzBoxPhonebookNew: Adding '''%s''' with '''%s''' from FRITZ!Box Phonebook!" % (thisname.strip(), thisnumber))
						# Beware: strings in phonebook.phonebook have to be in utf-8!
						self.phonebook.phonebook[thisnumber] = thisname
		else:
			self._notify(_("Could not parse FRITZ!Box Phonebook entry"))

	def _errorLoad(self, error):
		debug("[FritzCallFBF] _errorLoad: %s" % (error))
		text = _("FRITZ!Box - Could not load phonebook: %s") % error.getErrorMessage()
		self._notify(text)

	def getCalls(self, callScreen, callback, callType):
		#
		# call sequence must be:
		# - login
		# - getPage -> _gotPageLogin
		# - loginCallback (_getCalls)
		# - getPage -> _getCalls1
		debug("[FritzCallFBF] getCalls")
		self._callScreen = callScreen
		self._callType = callType
		if (time.time() - self._callTimestamp) > 180: 
			debug("[FritzCallFBF] getCalls: outdated data, login and get new ones: " + time.ctime(self._callTimestamp) + " time: " + time.ctime())
			self._callTimestamp = time.time()
			self._login(lambda x:self._getCalls(callback, x))
		elif not self._callList:
			debug("[FritzCallFBF] getCalls: time is ok, but no callList")
			self._getCalls1(callback)
		else:
			debug("[FritzCallFBF] getCalls: time is ok, callList is ok")
			self._gotPageCalls(callback)

	def _getCalls(self, callback, html):
		if html:
			#===================================================================
			# found = re.match('.*<p class="errorMessage">FEHLER:&nbsp;([^<]*)</p>', html, re.S)
			# if found:
			#	self._errorCalls('Login: ' + found.group(1))
			#	return
			#===================================================================
			start = html.find('<p class="errorMessage">FEHLER:&nbsp;')
			if start != -1:
				start = start + len('<p class="errorMessage">FEHLER:&nbsp;')
				self._errorCalls('Login: ' + html[start, html.find('</p>', start)])
				return
		#
		# we need this to fill Anrufliste.csv
		# http://repeater1/cgi-bin/webcm?getpage=../html/de/menus/menu2.html&var:lang=de&var:menu=fon&var:pagename=foncalls
		#
		debug("[FritzCallFBF] _getCalls")
		if html:
			#===================================================================
			# found = re.match('.*<p class="errorMessage">FEHLER:&nbsp;([^<]*)</p>', html, re.S)
			# if found:
			#	text = _("FRITZ!Box - Error logging in: %s") + found.group(1)
			#	self._notify(text)
			#	return
			#===================================================================
			start = html.find('<p class="errorMessage">FEHLER:&nbsp;')
			if start != -1:
				start = start + len('<p class="errorMessage">FEHLER:&nbsp;')
				self._notify(_("FRITZ!Box - Error logging in: %s") + html[start, html.find('</p>', start)])
				return

		if self._callScreen:
			self._callScreen.updateStatus(_("preparing"))
		parms = urlencode({'getpage':'../html/de/menus/menu2.html', 'var:lang':'de', 'var:pagename':'foncalls', 'var:menu':'fon', 'sid':self._md5Sid})
		url = "http://%s/cgi-bin/webcm?%s" % (config.plugins.FritzCall.hostname.value, parms)
		getPage(url).addCallback(lambda x:self._getCalls1(callback)).addErrback(self._errorCalls) #@UnusedVariable # pylint: disable=W0613

	def _getCalls1(self, callback):
		#
		# finally we should have successfully lgged in and filled the csv
		#
		debug("[FritzCallFBF] _getCalls1")
		if self._callScreen:
			self._callScreen.updateStatus(_("finishing"))
		parms = urlencode({'getpage':'../html/de/FRITZ!Box_Anrufliste.csv', 'sid':self._md5Sid})
		url = "http://%s/cgi-bin/webcm?%s" % (config.plugins.FritzCall.hostname.value, parms)
		getPage(url).addCallback(lambda x:self._gotPageCalls(callback, x)).addErrback(self._errorCalls)

	def resolveNumber(self, number, default=None):
		if number.isdigit():
			if config.plugins.FritzCall.internal.value and len(number) > 3 and number[0] == "0":
				number = number[1:]
			# strip CbC prefix
			number = stripCbCPrefix(number, config.plugins.FritzCall.country.value)
			if config.plugins.FritzCall.prefix.value and number and number[0] != '0':		# should only happen for outgoing
				number = config.plugins.FritzCall.prefix.value + number
			name = None
			if self.phonebook:
				name = self.phonebook.search(number)
			if name:
				#===========================================================
				# found = re.match('(.*?)\n.*', name)
				# if found:
				#	name = found.group(1)
				#===========================================================
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

	def _gotPageCalls(self, callback, csv=""):

		if csv:
			debug("[FritzCallFBF] _gotPageCalls: got csv, setting callList")
			if self._callScreen:
				self._callScreen.updateStatus(_("done"))
			if csv.find('Melden Sie sich mit dem Kennwort der FRITZ!Box an') != -1:
				text = _("You need to set the password of the FRITZ!Box\nin the configuration dialog to display calls\n\nIt could be a communication issue, just try again.")
				# self.session.open(MessageBox, text, MessageBox.TYPE_ERROR, timeout=config.plugins.FritzCall.timeout.value)
				self._notify(text)
				return

			csv = csv.decode('iso-8859-1', 'replace').encode('utf-8', 'replace')
			lines = csv.splitlines()
			self._callList = lines
		elif self._callList:
			debug("[FritzCallFBF] _gotPageCalls: got no csv, but have callList")
			if self._callScreen:
				self._callScreen.updateStatus(_("done, using last list"))
			lines = self._callList
		else:
			debug("[FritzCallFBF] _gotPageCalls: got no csv, no callList, trying newer FW")
			self._getCalls1New(callback)
			return
			
		callListL = []
		if config.plugins.FritzCall.filter.value and config.plugins.FritzCall.filterCallList.value:
			filtermsns = map(lambda x: x.strip(), config.plugins.FritzCall.filtermsn.value.split(","))
			debug("[FritzCallFBF] _gotPageCalls: filtermsns %s" % (repr(filtermsns)))

		# Typ;Datum;Name;Rufnummer;Nebenstelle;Eigene Rufnummer;Dauer
		# 0  ;1	   ;2   ;3		  ;4		  ;5			   ;6
		lines = map(lambda line: line.split(';'), lines)
		lines = filter(lambda line: (len(line)==7 and (line[0]=="Typ" or self._callType == '.' or line[0] == self._callType)), lines)

		for line in lines:
			# debug("[FritzCallFBF] _gotPageCalls: line %s" % (line))
			direct = line[0]
			date = line[1]
			length = line[6]
			if config.plugins.FritzCall.phonebook.value and line[2]:
				remote = self.resolveNumber(line[3], line[2] + " (FBF)")
			else:
				remote = self.resolveNumber(line[3], line[2])
			here = line[5]
			start = here.find('Internet: ')
			if start != -1:
				start += len('Internet: ')
				here = here[start:]
			else:
				here = line[5]
			if direct != "Typ" and config.plugins.FritzCall.filter.value and config.plugins.FritzCall.filterCallList.value:
				# debug("[FritzCallFBF] _gotPageCalls: check %s" % (here))
				if here not in filtermsns:
					# debug("[FritzCallFBF] _gotPageCalls: skip %s" % (here))
					continue
			here = self.resolveNumber(here, line[4])

			number = stripCbCPrefix(line[3], config.plugins.FritzCall.country.value)
			if config.plugins.FritzCall.prefix.value and number and number[0] != '0':		# should only happen for outgoing
				number = config.plugins.FritzCall.prefix.value + number
			callListL.append((number, date, direct, remote, length, here))

		if callback:
			# debug("[FritzCallFBF] _gotPageCalls call callback with\n" + text
			callback(callListL)
		self._callScreen = None

	def _getCalls1New(self, callback):
		#
		# finally we should have successfully lgged in and filled the csv
		#
		debug("[FritzCallFBF] _getCalls1New")
		if self._callScreen:
			self._callScreen.updateStatus(_("finishing"))
		# http://192.168.178.1/fon_num/foncalls_list.lua?sid=da78ab0797197dc7
		parms = urlencode({'sid':self._md5Sid})
		url = "http://%s/fon_num/foncalls_list.lua?%s" % (config.plugins.FritzCall.hostname.value, parms)
		getPage(url).addCallback(lambda x:self._gotPageCallsNew(callback, x)).addErrback(self._errorCalls)

	def _gotPageCallsNew(self, callback, html=""):

		debug("[FritzCallFBF] _gotPageCallsNew")
		if self._callScreen:
			self._callScreen.updateStatus(_("preparing"))

		callListL = []
		if config.plugins.FritzCall.filter.value and config.plugins.FritzCall.filterCallList.value:
			filtermsns = map(lambda x: x.strip(), config.plugins.FritzCall.filtermsn.value.split(","))
			debug("[FritzCallFBF] _gotPageCallsNew: filtermsns %s" % (repr(filtermsns)))

		#=======================================================================
		# linkP = open("/tmp/FritzCall_Calllist.htm", "w")
		# linkP.write(html)
		# linkP.close()
		#=======================================================================

		#===============================================================================
		# <td class="call_in" title="ankommender Anruf"></td>
		# <td>28.09.12 17:24</td>
		# <td title="Thomas (privat) = 03602181904">(<a href=" " onclick="return onDial('03602181904');">)?Thomas (privat)(</a>)?</td>
		# <td>fritz!phone 2</td>
		# <td title="81567 (Internet)">81567</td>
		# <td>0:05</td>
		#===============================================================================
		# 1: direct; 2: date; 3: Name + " = " oder leer; 4: Rufnummer; 5: Name; 6: Nebenstelle; 7: Eigene Rufnummer lang; 8: Eigene Rufnummer; 9: Dauer
		entrymask = re.compile('<td class="([^"]*)" title="[^"]*"></td>\s*<td>([^"]*)</td>\s*<td title="([^\d]*)([\d]*)">(?:<a href=[^>]*>)?([^<]*)(?:</a>)?</td>\s*<td>([^<]*)</td>\s*<td title="([^"]*)">([^<]*)</td>\s*<td>([^<]*)</td>', re.S)
		entries = entrymask.finditer(html)
		for found in entries:
			if found.group(1) == "call_in":
				direct = FBF_IN_CALLS
			elif found.group(1) == "call_out":
				direct = FBF_OUT_CALLS
			elif found.group(1) == "call_in_fail":
				direct = FBF_MISSED_CALLS
			# debug("[FritzCallFBF] _gotPageCallsNew: direct: " + direct)
			if direct != self._callType and "." != self._callType:
				continue

			date = found.group(2)
			# debug("[FritzCallFBF] _gotPageCallsNew: date: " + date)
			length = found.group(9)
			# debug("[FritzCallFBF] _gotPageCallsNew: len: " + length)
			if config.plugins.FritzCall.phonebook.value and found.group(3):
				remote = self.resolveNumber(found.group(4), found.group(5) + " (FBF)")
			else:
				remote = self.resolveNumber(found.group(4), found.group(5))
			# debug("[FritzCallFBF] _gotPageCallsNew: remote. " + remote)
			here = found.group(8)
			#===================================================================
			# start = here.find('Internet: ')
			# if start != -1:
			#	start += len('Internet: ')
			#	here = here[start:]
			# else:
			#	here = line[5]
			#===================================================================
			if config.plugins.FritzCall.filter.value and config.plugins.FritzCall.filterCallList.value:
				# debug("[FritzCallFBF] _gotPageCalls: check %s" % (here))
				if here not in filtermsns:
					# debug("[FritzCallFBF] _gotPageCalls: skip %s" % (here))
					continue
			here = self.resolveNumber(here, found.group(6))
			# debug("[FritzCallFBF] _gotPageCallsNew: here: " + here)

			number = stripCbCPrefix(found.group(4), config.plugins.FritzCall.country.value)
			if config.plugins.FritzCall.prefix.value and number and number[0] != '0':		# should only happen for outgoing
				number = config.plugins.FritzCall.prefix.value + number
			# debug("[FritzCallFBF] _gotPageCallsNew: number: " + number)
			debug("[FritzCallFBF] _gotPageCallsNew: append: %s" % repr((number, date, direct, remote, length, here)) )
			callListL.append((number, date, direct, remote, length, here))

		if callback:
			# debug("[FritzCallFBF] _gotPageCalls call callback with\n" + text
			callback(callListL)
		self._callScreen = None

	def _errorCalls(self, error):
		debug("[FritzCallFBF] _errorCalls: %s" % (error))
		text = _("FRITZ!Box - Could not load calls: %s") % error.getErrorMessage()
		self._notify(text)

	def dial(self, number):
		''' initiate a call to number '''
		self._login(lambda x: self._dial(number, x))
		
	def _dial(self, number, html):
		if html:
			#===================================================================
			# found = re.match('.*<p class="errorMessage">FEHLER:&nbsp;([^<]*)</p>', html, re.S)
			# if found:
			#	self._errorDial('Login: ' + found.group(1))
			#	return
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
		debug("[FritzCallFBF] dial url: '" + url + "' parms: '" + parms + "'")
		getPage(url,
			method="POST",
			agent="Mozilla/5.0 (Windows; U; Windows NT 6.0; de; rv:1.9.0.5) Gecko/2008120122 Firefox/3.0.5",
			headers={
					'Content-Type': "application/x-www-form-urlencoded",
					'Content-Length': str(len(parms))},
			postdata=parms).addCallback(self._okDial).addErrback(self._errorDial)

	def _okDial(self, html): #@UnusedVariable # pylint: disable=W0613
		debug("[FritzCallFBF] okDial")

	def _errorDial(self, error):
		debug("[FritzCallFBF] errorDial: $s" % error)
		text = _("FRITZ!Box - Dialling failed: %s") % error.getErrorMessage()
		self._notify(text)

	def changeWLAN(self, statusWLAN):
		''' get status info from FBF '''
		debug("[FritzCallFBF] changeWLAN start")
		if not statusWLAN or (statusWLAN != '1' and statusWLAN != '0'):
			return
		self._login(lambda x: self._changeWLAN(statusWLAN, x))
		
	def _changeWLAN(self, statusWLAN, html):
		if html:
			#===================================================================
			# found = re.match('.*<p class="errorMessage">FEHLER:&nbsp;([^<]*)</p>', html, re.S)
			# if found:
			#	self._errorChangeWLAN('Login: ' + found.group(1))
			#	return
			#===================================================================
			start = html.find('<p class="errorMessage">FEHLER:&nbsp;')
			if start != -1:
				start = start + len('<p class="errorMessage">FEHLER:&nbsp;')
				self._errorChangeWLAN('Login: ' + html[start, html.find('</p>', start)])
				return
		url = "http://%s/cgi-bin/webcm" % config.plugins.FritzCall.hostname.value
		parms = urlencode({
			'getpage':'../html/de/menus/menu2.html',
			'var:lang':'de',
			'var:pagename':'wlan',
			'var:menu':'wlan',
			'wlan:settings/ap_enabled':str(statusWLAN),
			'sid':self._md5Sid
			})
		debug("[FritzCallFBF] changeWLAN url: '" + url + "' parms: '" + parms + "'")
		getPage(url,
			method="POST",
			agent="Mozilla/5.0 (Windows; U; Windows NT 6.0; de; rv:1.9.0.5) Gecko/2008120122 Firefox/3.0.5",
			headers={
					'Content-Type': "application/x-www-form-urlencoded",
					'Content-Length': str(len(parms))},
			postdata=parms).addCallback(self._okChangeWLAN).addErrback(self._errorChangeWLAN)

	def _okChangeWLAN(self, html): #@UnusedVariable # pylint: disable=W0613
		debug("[FritzCallFBF] _okChangeWLAN")

	def _errorChangeWLAN(self, error):
		debug("[FritzCallFBF] _errorChangeWLAN: $s" % error)
		text = _("FRITZ!Box - Failed changing WLAN: %s") % error.getErrorMessage()
		self._notify(text)

	def changeMailbox(self, whichMailbox):
		''' switch mailbox on/off '''
		debug("[FritzCallFBF] changeMailbox start: " + str(whichMailbox))
		self._login(lambda x: self._changeMailbox(whichMailbox, x))

	def _changeMailbox(self, whichMailbox, html):
		if html:
			#===================================================================
			# found = re.match('.*<p class="errorMessage">FEHLER:&nbsp;([^<]*)</p>', html, re.S)
			# if found:
			#	self._errorChangeMailbox('Login: ' + found.group(1))
			#	return
			#===================================================================
			start = html.find('<p class="errorMessage">FEHLER:&nbsp;')
			if start != -1:
				start = start + len('<p class="errorMessage">FEHLER:&nbsp;')
				self._errorChangeMailbox('Login: ' + html[start, html.find('</p>', start)])
				return
		debug("[FritzCallFBF] _changeMailbox")
		url = "http://%s/cgi-bin/webcm" % config.plugins.FritzCall.hostname.value
		if whichMailbox == -1:
			for i in range(5):
				if self.info[FBF_tamActive][i+1]:
					state = '0'
				else:
					state = '1'
				parms = urlencode({
					'tam:settings/TAM'+str(i)+'/Active':state,
					'sid':self._md5Sid
					})
				debug("[FritzCallFBF] changeMailbox url: '" + url + "' parms: '" + parms + "'")
				getPage(url,
					method="POST",
					agent="Mozilla/5.0 (Windows; U; Windows NT 6.0; de; rv:1.9.0.5) Gecko/2008120122 Firefox/3.0.5",
					headers={
							'Content-Type': "application/x-www-form-urlencoded",
							'Content-Length': str(len(parms))},
					postdata=parms).addCallback(self._okChangeMailbox).addErrback(self._errorChangeMailbox)
		elif whichMailbox > 4:
			debug("[FritzCallFBF] changeMailbox invalid mailbox number")
		else:
			if self.info[FBF_tamActive][whichMailbox+1]:
				state = '0'
			else:
				state = '1'
			parms = urlencode({
				'tam:settings/TAM'+str(whichMailbox)+'/Active':state,
				'sid':self._md5Sid
				})
			debug("[FritzCallFBF] changeMailbox url: '" + url + "' parms: '" + parms + "'")
			getPage(url,
				method="POST",
				agent="Mozilla/5.0 (Windows; U; Windows NT 6.0; de; rv:1.9.0.5) Gecko/2008120122 Firefox/3.0.5",
				headers={
						'Content-Type': "application/x-www-form-urlencoded",
						'Content-Length': str(len(parms))},
				postdata=parms).addCallback(self._okChangeMailbox).addErrback(self._errorChangeMailbox)

	def _okChangeMailbox(self, html): #@UnusedVariable # pylint: disable=W0613
		debug("[FritzCallFBF] _okChangeMailbox")

	def _errorChangeMailbox(self, error):
		debug("[FritzCallFBF] _errorChangeMailbox: $s" % error)
		text = _("FRITZ!Box - Failed changing Mailbox: %s") % error.getErrorMessage()
		self._notify(text)

	def getInfo(self, callback):
		''' get status info from FBF '''
		debug("[FritzCallFBF] getInfo")
		self._login(lambda x:self._getInfo(callback, x))
		
	def _getInfo(self, callback, html):
		# http://192.168.178.1/cgi-bin/webcm?getpage=../html/de/menus/menu2.html&var:lang=de&var:pagename=home&var:menu=home
		debug("[FritzCallFBF] _getInfo: verify login")
		if html:
			#===================================================================
			# found = re.match('.*<p class="errorMessage">FEHLER:&nbsp;([^<]*)</p>', html, re.S)
			# if found:
			#	self._errorGetInfo('Login: ' + found.group(1))
			#	return
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
		debug("[FritzCallFBF] _getInfo url: '" + url + "' parms: '" + parms + "'")
		getPage(url,
			method="POST",
			agent="Mozilla/5.0 (Windows; U; Windows NT 6.0; de; rv:1.9.0.5) Gecko/2008120122 Firefox/3.0.5",
			headers={
					'Content-Type': "application/x-www-form-urlencoded",
					'Content-Length': str(len(parms))},
			postdata=parms).addCallback(lambda x:self._okGetInfo(callback,x)).addErrback(self._errorGetInfo)

	def _okGetInfo(self, callback, html):
		def readInfo(html):
			if self.info:
				(boxInfo, upTime, ipAddress, wlanState, dslState, tamActive, dectActive, faxActive, rufumlActive) = self.info
			else:
				(boxInfo, upTime, ipAddress, wlanState, dslState, tamActive, dectActive, faxActive, rufumlActive) = (None, None, None, None, None, None, None, None, None)

			debug("[FritzCallFBF] _okGetInfo/readinfo")
			found = re.match('.*<table class="tborder" id="tProdukt">\s*<tr>\s*<td style="padding-top:2px;">([^<]*)</td>\s*<td style="padding-top:2px;text-align:right;">\s*([^\s]*)\s*</td>', html, re.S)
			if found:
				boxInfo = found.group(1)+ ', ' + found.group(2)
				boxInfo = boxInfo.replace('&nbsp;',' ')
				# debug("[FritzCallFBF] _okGetInfo Boxinfo: " + boxInfo)
			else:
				found = re.match('.*<p class="ac">([^<]*)</p>', html, re.S)
				if found:
					# debug("[FritzCallFBF] _okGetInfo Boxinfo: " + found.group(1))
					boxInfo = found.group(1)

			if html.find('home_coninf.txt') != -1:
				url = "http://%s/cgi-bin/webcm" % config.plugins.FritzCall.hostname.value
				parms = urlencode({
					'getpage':'../html/de/home/home_coninf.txt',
					'sid':self._md5Sid
					})
				# debug("[FritzCallFBF] get coninfo: url: '" + url + "' parms: '" + parms + "'")
				getPage(url,
					method="POST",
					agent="Mozilla/5.0 (Windows; U; Windows NT 6.0; de; rv:1.9.0.5) Gecko/2008120122 Firefox/3.0.5",
					headers={
							'Content-Type': "application/x-www-form-urlencoded",
							'Content-Length': str(len(parms))},
					postdata=parms).addCallback(lambda x:self._okSetConInfo(callback,x)).addErrback(self._errorGetInfo)
			else:
				found = re.match('.*if \(isNaN\(jetzt\)\)\s*return "";\s*var str = "([^"]*)";', html, re.S)
				if found:
					# debug("[FritzCallFBF] _okGetInfo Uptime: " + found.group(1))
					upTime = found.group(1)
				else:
					found = re.match('.*str = g_pppSeit \+"([^<]*)<br>"\+mldIpAdr;', html, re.S)
					if found:
						# debug("[FritzCallFBF] _okGetInfo Uptime: " + found.group(1))
						upTime = found.group(1)
	
				found = re.match(".*IpAdrDisplay\('([.\d]+)'\)", html, re.S)
				if found:
					# debug("[FritzCallFBF] _okGetInfo IpAdrDisplay: " + found.group(1))
					ipAddress = found.group(1)

			if html.find('g_tamActive') != -1:
				entries = re.compile('if \("(\d)" == "1"\) {\s*g_tamActive \+= 1;\s*}', re.S).finditer(html)
				tamActive = [0, False, False, False, False, False]
				i = 1
				for entry in entries:
					state = entry.group(1)
					if state == '1':
						tamActive[0] += 1
						tamActive[i] = True
					i += 1
				# debug("[FritzCallFBF] _okGetInfo tamActive: " + str(tamActive))
		
			if html.find('home_dect.txt') != -1:
				url = "http://%s/cgi-bin/webcm" % config.plugins.FritzCall.hostname.value
				parms = urlencode({
					'getpage':'../html/de/home/home_dect.txt',
					'sid':self._md5Sid
					})
				# debug("[FritzCallFBF] get coninfo: url: '" + url + "' parms: '" + parms + "'")
				getPage(url,
					method="POST",
					agent="Mozilla/5.0 (Windows; U; Windows NT 6.0; de; rv:1.9.0.5) Gecko/2008120122 Firefox/3.0.5",
					headers={
							'Content-Type': "application/x-www-form-urlencoded",
							'Content-Length': str(len(parms))},
					postdata=parms).addCallback(lambda x:self._okSetDect(callback,x)).addErrback(self._errorGetInfo)
			else:
				if html.find('countDect2') != -1:
					entries = re.compile('if \("1" == "1"\) countDect2\+\+;', re.S).findall(html)
					dectActive = len(entries)
					# debug("[FritzCallFBF] _okGetInfo dectActive: " + str(dectActive))

			found = re.match('.*var g_intFaxActive = "0";\s*if \("1" != ""\) {\s*g_intFaxActive = "1";\s*}\s*', html, re.S)
			if found:
				faxActive = True
				# debug("[FritzCallFBF] _okGetInfo faxActive")

			if html.find('cntRufumleitung') != -1:
				entries = re.compile('mode = "1";\s*ziel = "[^"]+";\s*if \(mode == "1" \|\| ziel != ""\)\s*{\s*g_RufumleitungAktiv = true;', re.S).findall(html)
				rufumlActive = len(entries)
				entries = re.compile('if \("([^"]*)"=="([^"]*)"\) isAllIncoming\+\+;', re.S).finditer(html)
				isAllIncoming = 0
				for entry in entries:
					# debug("[FritzCallFBF] _okGetInfo rufumlActive add isAllIncoming")
					if entry.group(1) == entry.group(2):
						isAllIncoming += 1
				if isAllIncoming == 2 and rufumlActive > 0:
					rufumlActive -= 1
				# debug("[FritzCallFBF] _okGetInfo rufumlActive: " + str(rufumlActive))

			# /cgi-bin/webcm?getpage=../html/de/home/home_dsl.txt
			# alternative through: fritz.box/cgi-bin/webcm?getpage=../html/de/menus/menu2.html&var:menu=internet&var:pagename=overview
			# { "dsl_carrier_state": "5", "umts_enabled": "0", "ata_mode": "0", "isusbgsm": "", "dsl_ds_nrate": "3130", "dsl_us_nrate": "448", "hint_dsl_no_cable": "0", "wds_enabled": "0", "wds_hop": "0", "isata": "" } 
			if html.find('home_dsl.txt') != -1:
				url = "http://%s/cgi-bin/webcm" % config.plugins.FritzCall.hostname.value
				parms = urlencode({
					'getpage':'../html/de/home/home_dsl.txt',
					'sid':self._md5Sid
					})
				# debug("[FritzCallFBF] get dsl state: url: '" + url + "' parms: '" + parms + "'")
				getPage(url,
					method="POST",
					agent="Mozilla/5.0 (Windows; U; Windows NT 6.0; de; rv:1.9.0.5) Gecko/2008120122 Firefox/3.0.5",
					headers={
							'Content-Type': "application/x-www-form-urlencoded",
							'Content-Length': str(len(parms))},
					postdata=parms).addCallback(lambda x:self._okSetDslState(callback,x)).addErrback(self._errorGetInfo)
			else:
				found = re.match('.*function DslStateDisplay \(state\){\s*var state = "(\d+)";', html, re.S)
				if found:
					# debug("[FritzCallFBF] _okGetInfo DslState: " + found.group(1))
					dslState = [ found.group(1), None ] # state, speed
					found = re.match('.*function DslStateDisplay \(state\){\s*var state = "\d+";.*?if \("3130" != "0"\) str = "([^"]*)";', html, re.S)
					if found:
						# debug("[FritzCallFBF] _okGetInfo DslSpeed: " + found.group(1).strip())
						dslState[1] = found.group(1).strip()
		
			# /cgi-bin/webcm?getpage=../html/de/home/home_wlan.txt
			# { "ap_enabled": "1", "active_stations": "0", "encryption": "4", "wireless_stickandsurf_enabled": "0", "is_macfilter_active": "0", "wmm_enabled": "1", "wlan_state": [ "end" ] }
			if html.find('home_wlan.txt') != -1:
				url = "http://%s/cgi-bin/webcm" % config.plugins.FritzCall.hostname.value
				parms = urlencode({
					'getpage':'../html/de/home/home_wlan.txt',
					'sid':self._md5Sid
					})
				# debug("[FritzCallFBF] get wlan state: url: '" + url + "' parms: '" + parms + "'")
				getPage(url,
					method="POST",
					agent="Mozilla/5.0 (Windows; U; Windows NT 6.0; de; rv:1.9.0.5) Gecko/2008120122 Firefox/3.0.5",
					headers={
							'Content-Type': "application/x-www-form-urlencoded",
							'Content-Length': str(len(parms))},
					postdata=parms).addCallback(lambda x:self._okSetWlanState(callback,x)).addErrback(self._errorGetInfo)
			else:
				found = re.match('.*function WlanStateLed \(state\){.*?return StateLed\("(\d+)"\);\s*}', html, re.S)
				if found:
					# debug("[FritzCallFBF] _okGetInfo WlanState: " + found.group(1))
					wlanState = [ found.group(1), 0, 0 ] # state, encryption, number of devices
					found = re.match('.*var (?:g_)?encryption = "(\d+)";', html, re.S)
					if found:
						# debug("[FritzCallFBF] _okGetInfo WlanEncrypt: " + found.group(1))
						wlanState[1] = found.group(1)

			return (boxInfo, upTime, ipAddress, wlanState, dslState, tamActive, dectActive, faxActive, rufumlActive)

		debug("[FritzCallFBF] _okGetInfo")
		info = readInfo(html)
		debug("[FritzCallFBF] _okGetInfo info: " + str(info))
		self.info = info
		if callback:
			callback(info)

	def _okSetDect(self, callback, html):
		# debug("[FritzCallFBF] _okSetDect: " + html)
		# found = re.match('.*"connection_status":"(\d+)".*"connection_ip":"([.\d]+)".*"connection_detail":"([^"]+)".*"connection_uptime":"([^"]+)"', html, re.S)
		if html.find('"dect_enabled": "1"') != -1:
			# debug("[FritzCallFBF] _okSetDect: dect_enabled")
			found = re.match('.*"dect_device_list":.*\[([^\]]*)\]', html, re.S)
			if found:
				# debug("[FritzCallFBF] _okSetDect: dect_device_list: %s" %(found.group(1)))
				entries = re.compile('"1"', re.S).findall(found.group(1))
				dectActive = len(entries)
				(boxInfo, upTime, ipAddress, wlanState, dslState, tamActive, dummy, faxActive, rufumlActive) = self.info
				self.info = (boxInfo, upTime, ipAddress, wlanState, dslState, tamActive, dectActive, faxActive, rufumlActive)
				debug("[FritzCallFBF] _okSetDect info: " + str(self.info))
		if callback:
			callback(self.info)

	def _okSetConInfo(self, callback, html):
		# debug("[FritzCallFBF] _okSetConInfo: " + html)
		# found = re.match('.*"connection_status":"(\d+)".*"connection_ip":"([.\d]+)".*"connection_detail":"([^"]+)".*"connection_uptime":"([^"]+)"', html, re.S)
		found = re.match('.*"connection_ip": "([.\d]+)".*"connection_uptime": "([^"]+)"', html, re.S)
		if found:
			# debug("[FritzCallFBF] _okSetConInfo: connection_ip: %s upTime: %s" %( found.group(1), found.group(2)))
			ipAddress = found.group(1)
			upTime = found.group(2)
			(boxInfo, dummy, dummy, wlanState, dslState, tamActive, dectActive, faxActive, rufumlActive) = self.info
			self.info = (boxInfo, upTime, ipAddress, wlanState, dslState, tamActive, dectActive, faxActive, rufumlActive)
			debug("[FritzCallFBF] _okSetWlanState info: " + str(self.info))
		else:
			found = re.match('.*_ip": "([.\d]+)".*"connection_uptime": "([^"]+)"', html, re.S)
			if found:
				# debug("[FritzCallFBF] _okSetConInfo: _ip: %s upTime: %s" %( found.group(1), found.group(2)))
				ipAddress = found.group(1)
				upTime = found.group(2)
				(boxInfo, dummy, dummy, wlanState, dslState, tamActive, dectActive, faxActive, rufumlActive) = self.info
				self.info = (boxInfo, upTime, ipAddress, wlanState, dslState, tamActive, dectActive, faxActive, rufumlActive)
				debug("[FritzCallFBF] _okSetWlanState info: " + str(self.info))
		if callback:
			callback(self.info)

	def _okSetWlanState(self, callback, html):
		# debug("[FritzCallFBF] _okSetWlanState: " + html)
		found = re.match('.*"ap_enabled": "(\d+)"', html, re.S)
		if found:
			# debug("[FritzCallFBF] _okSetWlanState: ap_enabled: " + found.group(1))
			wlanState = [ found.group(1), None, None ]
			found = re.match('.*"encryption": "(\d+)"', html, re.S)
			if found:
				# debug("[FritzCallFBF] _okSetWlanState: encryption: " + found.group(1))
				wlanState[1] = found.group(1)
			found = re.match('.*"active_stations": "(\d+)"', html, re.S)
			if found:
				# debug("[FritzCallFBF] _okSetWlanState: active_stations: " + found.group(1))
				wlanState[2] = found.group(1)
			(boxInfo, upTime, ipAddress, dummy, dslState, tamActive, dectActive, faxActive, rufumlActive) = self.info
			self.info = (boxInfo, upTime, ipAddress, wlanState, dslState, tamActive, dectActive, faxActive, rufumlActive)
			debug("[FritzCallFBF] _okSetWlanState info: " + str(self.info))
		if callback:
			callback(self.info)

	def _okSetDslState(self, callback, html):
		# debug("[FritzCallFBF] _okSetDslState: " + html)
		found = re.match('.*"dsl_carrier_state": "(\d+)"', html, re.S)
		if found:
			# debug("[FritzCallFBF] _okSetDslState: dsl_carrier_state: " + found.group(1))
			dslState = [ found.group(1), "" ]
			found = re.match('.*"dsl_ds_nrate": "(\d+)"', html, re.S)
			if found:
				# debug("[FritzCallFBF] _okSetDslState: dsl_ds_nrate: " + found.group(1))
				dslState[1] = found.group(1)
			found = re.match('.*"dsl_us_nrate": "(\d+)"', html, re.S)
			if found:
				# debug("[FritzCallFBF] _okSetDslState: dsl_us_nrate: " + found.group(1))
				dslState[1] = dslState[1] + '/' + found.group(1)
			(boxInfo, upTime, ipAddress, wlanState, dummy, tamActive, dectActive, faxActive, rufumlActive) = self.info
			self.info = (boxInfo, upTime, ipAddress, wlanState, dslState, tamActive, dectActive, faxActive, rufumlActive)
			debug("[FritzCallFBF] _okSetDslState info: " + str(self.info))
		if callback:
			callback(self.info)

	def _errorGetInfo(self, error):
		debug("[FritzCallFBF] _errorGetInfo: %s" % (error))
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
			# found = re.match('.*<p class="errorMessage">FEHLER:&nbsp;([^<]*)</p>', html, re.S)
			# if found:
			#	self._errorReset('Login: ' + found.group(1))
			#	return
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
		debug("[FritzCallFBF] _reset url: '" + url + "' parms: '" + parms + "'")
		getPage(url,
			method="POST",
			agent="Mozilla/5.0 (Windows; U; Windows NT 6.0; de; rv:1.9.0.5) Gecko/2008120122 Firefox/3.0.5",
			headers={
					'Content-Type': "application/x-www-form-urlencoded",
					'Content-Length': str(len(parms))},
			postdata=parms)

	def _okReset(self, html): #@UnusedVariable # pylint: disable=W0613
		debug("[FritzCallFBF] _okReset")

	def _errorReset(self, error):
		debug("[FritzCallFBF] _errorReset: %s" % (error))
		text = _("FRITZ!Box - Error resetting: %s") % error.getErrorMessage()
		self._notify(text)

	def readBlacklist(self):
		self._login(self._readBlacklist)
		
	def _readBlacklist(self, html):
		if html:
			#===================================================================
			# found = re.match('.*<p class="errorMessage">FEHLER:&nbsp;([^<]*)</p>', html, re.S)
			# if found:
			#	self._errorBlacklist('Login: ' + found.group(1))
			#	return
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
		debug("[FritzCallFBF] _readBlacklist url: '" + url + "' parms: '" + parms + "'")
		getPage(url,
			method="POST",
			agent="Mozilla/5.0 (Windows; U; Windows NT 6.0; de; rv:1.9.0.5) Gecko/2008120122 Firefox/3.0.5",
			headers={
					'Content-Type': "application/x-www-form-urlencoded",
					'Content-Length': str(len(parms))},
			postdata=parms).addCallback(self._okBlacklist).addErrback(self._errorBlacklist)

	def _okBlacklist(self, html):
		debug("[FritzCallFBF] _okBlacklist")
		entries = re.compile('<script type="text/javascript">document.write\(Tr(Out|In)\("\d+", "(\d+)", "\w*"\)\);</script>', re.S).finditer(html)
		self.blacklist = ([], [])
		for entry in entries:
			if entry.group(1) == "In":
				self.blacklist[0].append(entry.group(2))
			else:
				self.blacklist[1].append(entry.group(2))
		debug("[FritzCallFBF] _okBlacklist: %s" % repr(self.blacklist))

	def _errorBlacklist(self, error):
		debug("[FritzCallFBF] _errorBlacklist: %s" % (error))
		text = _("FRITZ!Box - Error getting blacklist: %s") % error.getErrorMessage()
		self._notify(text)

#===============================================================================
#	def hangup(self):
#		''' hangup call on port; not used for now '''
#		url = "http://%s/cgi-bin/webcm" % config.plugins.FritzCall.hostname.value
#		parms = urlencode({
#			'id':'uiPostForm',
#			'name':'uiPostForm',
#			'login:command/password': config.plugins.FritzCall.password.value,
#			'telcfg:settings/UseClickToDial':'1',
#			'telcfg:settings/DialPort':config.plugins.FritzCall.extension.value,
#			'telcfg:command/Hangup':'',
#			'sid':self._md5Sid
#			})
#		debug("[FritzCallFBF] hangup url: '" + url + "' parms: '" + parms + "'")
#		getPage(url,
#			method="POST",
#			headers={
#					'Content-Type': "application/x-www-form-urlencoded",
#					'Content-Length': str(len(parms))},
#			postdata=parms)
#===============================================================================
