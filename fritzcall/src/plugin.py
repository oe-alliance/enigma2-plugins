# -*- coding: utf-8 -*-
#===============================================================================
# $Author$
# $Revision$
# $Date$
# $Id$
#==============================
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.NumericalTextInputHelpDialog import NumericalTextInputHelpDialog
from Screens.InputBox import InputBox
from Screens import Standby
from Screens.HelpMenu import HelpableScreen

from enigma import eTimer #@UnresolvedImport
from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_HALIGN_RIGHT

from Components.MenuList import MenuList
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Button import Button
from Components.Pixmap import Pixmap
from Components.config import config, ConfigSubsection, ConfigSelection, ConfigEnableDisable, getConfigListEntry, ConfigText, ConfigInteger
try:
	from Components.config import ConfigPassword
except ImportError:
	ConfigPassword = ConfigText
from Components.ConfigList import ConfigListScreen
from Components.Harddisk import harddiskmanager

from Plugins.Plugin import PluginDescriptor
from Tools import Notifications
from Tools.NumericalTextInput import NumericalTextInput
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_SKIN_IMAGE
from Tools.LoadPixmap import LoadPixmap

from twisted.internet import reactor #@UnresolvedImport
from twisted.internet.protocol import ReconnectingClientFactory #@UnresolvedImport
from twisted.protocols.basic import LineReceiver #@UnresolvedImport
from twisted.web.client import getPage #@UnresolvedImport

from urllib import urlencode 
import re, time, os, hashlib, traceback

from nrzuname import ReverseLookupAndNotifier, html2unicode
import FritzOutlookCSV, FritzLDIF
from . import _, debug #@UnresolvedImport

from enigma import getDesktop
DESKTOP_WIDTH = getDesktop(0).size().width()
DESKTOP_HEIGHT = getDesktop(0).size().height()
DESKTOP_SKIN = config.skin.primary_skin.value.replace("/skin.xml", "")
XXX = 0 # TODO: Platzhalter für fullscreen SD skin
#
# this is pure magic.
# It returns the first value, if HD (1280x720),
# the second if SD (720x576),
# else something scaled accordingly
# if one of the parameters is -1, scale proportionally
#
def scaleH(y2, y1):
	if y2 == -1:
		y2 = y1*1280/720
	elif y1 == -1:
		y1 = y2*720/1280
	return scale(y2, y1, 1280, 720, DESKTOP_WIDTH)
def scaleV(y2, y1):
	if y2 == -1:
		y2 = y1*720/576
	elif y1 == -1:
		y1 = y2*576/720
	return scale(y2, y1, 720, 576, DESKTOP_HEIGHT)
def scale(y2, y1, x2, x1, x):
	return (y2 - y1) * (x - x1) / (x2 - x1) + y1

my_global_session = None


config.plugins.FritzCall = ConfigSubsection()
config.plugins.FritzCall.debug = ConfigEnableDisable(default=False)
config.plugins.FritzCall.muteOnCall = ConfigEnableDisable(default=False)
config.plugins.FritzCall.hostname = ConfigText(default="fritz.box", fixed_size=False)
config.plugins.FritzCall.afterStandby = ConfigSelection(choices=[("none", _("show nothing")), ("inList", _("show as list")), ("each", _("show each call"))])
config.plugins.FritzCall.filter = ConfigEnableDisable(default=False)
config.plugins.FritzCall.filtermsn = ConfigText(default="", fixed_size=False)
config.plugins.FritzCall.filtermsn.setUseableChars('0123456789,')
config.plugins.FritzCall.showOutgoing = ConfigEnableDisable(default=False)
config.plugins.FritzCall.timeout = ConfigInteger(default=15, limits=(0, 60))
config.plugins.FritzCall.lookup = ConfigEnableDisable(default=False)
config.plugins.FritzCall.internal = ConfigEnableDisable(default=False)
config.plugins.FritzCall.fritzphonebook = ConfigEnableDisable(default=False)
config.plugins.FritzCall.phonebook = ConfigEnableDisable(default=False)
config.plugins.FritzCall.addcallers = ConfigEnableDisable(default=False)
config.plugins.FritzCall.enable = ConfigEnableDisable(default=False)
config.plugins.FritzCall.password = ConfigPassword(default="", fixed_size=False)
config.plugins.FritzCall.extension = ConfigText(default='1', fixed_size=False)
config.plugins.FritzCall.extension.setUseableChars('0123456789')
config.plugins.FritzCall.showType = ConfigEnableDisable(default=True)
config.plugins.FritzCall.showShortcut = ConfigEnableDisable(default=False)
config.plugins.FritzCall.showVanity = ConfigEnableDisable(default=False)
config.plugins.FritzCall.prefix = ConfigText(default="", fixed_size=False)
config.plugins.FritzCall.prefix.setUseableChars('0123456789')
config.plugins.FritzCall.fullscreen = ConfigEnableDisable(default=False)

mountedDevs= [("/etc/enigma2", _("Flash"))]
for p in harddiskmanager.getMountedPartitions(True):
	mp = p.mountpoint[:-1]
	if p.description:
		mountedDevs.append((mp, _(p.description)+ ' (' + mp + ')'))
	else:
		mountedDevs.append((mp, mp))
config.plugins.FritzCall.phonebookLocation = ConfigSelection(choices=mountedDevs)

countryCodes = [
	("0049", _("Germany")),
	("0031", _("The Netherlands")),
	("0033", _("France")),
	("0039", _("Italy")),
	("0041", _("Switzerland")),
	("0043", _("Austria"))
	]
config.plugins.FritzCall.country = ConfigSelection(choices=countryCodes)

FBF_ALL_CALLS = "."
FBF_IN_CALLS = "1"
FBF_MISSED_CALLS = "2"
FBF_OUT_CALLS = "3"
fbfCallsChoices = {FBF_ALL_CALLS: _("All calls"),
				   FBF_IN_CALLS: _("Incoming calls"),
				   FBF_MISSED_CALLS: _("Missed calls"),
				   FBF_OUT_CALLS: _("Outgoing calls")
				   }
config.plugins.FritzCall.fbfCalls = ConfigSelection(choices=fbfCallsChoices)

config.plugins.FritzCall.name = ConfigText(default="", fixed_size=False)
config.plugins.FritzCall.number = ConfigText(default="", fixed_size=False)
config.plugins.FritzCall.number.setUseableChars('0123456789')

phonebook = None
fritzbox = None

def initDebug():
	try:
		os.remove("/tmp/FritzDebug.log")
	except:
		pass

class FritzAbout(Screen):

	def __init__(self, session):
		textFieldWidth = scaleV(350,250)
		width = 5 + 150 + 20 + textFieldWidth + 5 + 175 + 5
		height = 5 + 175 + 5 + 25 + 5
		# TRANSLATORS: this is a window title. Avoid the use of non ascii chars
		self.skin = """
			<screen name="FritzAbout" position="%d,%d" size="%d,%d" title="%s" >
				<widget name="text" position="175,%d" size="%d,%d" font="Regular;%d" />
				<ePixmap position="5,37" size="150,110" pixmap="%s" transparent="1" alphatest="blend" />
				<ePixmap position="%d,5" size="175,175" pixmap="%s" transparent="1" alphatest="blend" />
				<widget name="url" position="20,185" size="%d,25" font="Regular;%d" />
			</screen>""" % (
							(DESKTOP_WIDTH - width) / 2, (DESKTOP_HEIGHT - height) / 2, # position
							width, height, # size
							_("About FritzCall"), # title
							(height-scaleV(150,130)) / 2, # text vertical position
							textFieldWidth,
							scaleV(150,130), # text height
							scaleV(24,21), # text font size
							resolveFilename(SCOPE_PLUGINS, "Extensions/FritzCall/images/fritz.png"), # 150x110
							5 + 150 + 5 + textFieldWidth + 5, # qr code horizontal offset
							resolveFilename(SCOPE_PLUGINS, "Extensions/FritzCall/images/website.png"), # 175x175
							width-40, # url width
							scaleV(24,21) # url font size
							)
		Screen.__init__(self, session)
		self["aboutActions"] = ActionMap(["OkCancelActions"],
		{
		"cancel": self.exit,
		"ok": self.exit,
		}, -2)
		self["text"] = Label(
							"FritzCall Plugin" + "\n\n" +
							"$Author$"[1:-2] + "\n" +
							"$Revision$"[1:-2] + "\n" + 
							"$Date$"[1:23] + "\n"
							)
		self["url"] = Label("http://wiki.blue-panel.com/index.php/FritzCall")
		
	def exit(self):
		self.close()

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
		self.info = None # (boxInfo, upTime, ipAddress, wlanState, dslState, tamActive, dectActive)
		self.getInfo(None)

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
		if self._md5LoginTimestamp and((time.time() - self._md5LoginTimestamp) < float(9.5*60)) and self._md5Sid != '0000000000000000': # new login after 9.5 minutes inactivity 
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
			m = hashlib.md5()
			m.update(text)
			debug("[FritzCallFBF] md5Login/buildResponse: " + m.hexdigest())
			return challenge + '-' + m.hexdigest()

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
		found = re.match('.*<p class="errorMessage">FEHLER:&nbsp;([^<]*)</p>', html, re.S)
		if found:
			text = _("FRITZ!Box - Error logging in: %s") + found.group(1)
			self._notify(text)
		else:
			if self._callScreen:
				self._callScreen.updateStatus(_("login ok"))

		found = re.match('.*<input type="hidden" name="sid" value="([^\"]*)"', html, re.S)
		if found:
			self._md5Sid = found.group(1)
			debug("[FritzCallFBF] _gotPageLogin: found sid: " + self._md5Sid)

	def _errorLogin(self, error):
		debug("[FritzCallFBF] _errorLogin: %s" % (error))
		text = _("FRITZ!Box - Error logging in: %s") % error
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
		text = _("FRITZ!Box - Error logging out: %s") % error
		self._notify(text)

	def loadFritzBoxPhonebook(self):
		debug("[FritzCallFBF] loadFritzBoxPhonebook")
		if config.plugins.FritzCall.fritzphonebook.value:
			self._phoneBookID = '0'
			debug("[FritzCallFBF] loadFritzBoxPhonebook: logging in")
			self._login(self._loadFritzBoxPhonebook)

	def _loadFritzBoxPhonebook(self, html):
		if html:
			found = re.match('.*<p class="errorMessage">FEHLER:&nbsp;([^<]*)</p>', html, re.S)
			if found:
				self._errorLoad('Login: ' + found.group(1))
				return
		parms = urlencode({
						'getpage':'../html/de/menus/menu2.html',
						'var:lang':'de',
						'var:pagename':'fonbuch',
						'var:menu':'fon',
						'sid':self._md5Sid,
						'telcfg:settings/Phonebook/Books/Select':self._phoneBookID, # this selects always the first phonbook
						})
		url = "http://%s/cgi-bin/webcm" % (config.plugins.FritzCall.hostname.value)
		debug("[FritzCallFBF] _loadFritzBoxPhonebook: '" + url + "' parms: '" + parms + "'")
		getPage(url,
			method="POST",
			agent="Mozilla/5.0 (Windows; U; Windows NT 6.0; de; rv:1.9.0.5) Gecko/2008120122 Firefox/3.0.5",
			headers={'Content-Type': "application/x-www-form-urlencoded", 'Content-Length': str(len(parms))
					}, postdata=parms).addCallback(self._parseFritzBoxPhonebook).addErrback(self._errorLoad)

	def _parseFritzBoxPhonebook(self, html):
		debug("[FritzCallFBF] _parseFritzBoxPhonebook")
		if re.search('TrFonName', html):
			#===============================================================================
			#				 New Style: 7270 (FW 54.04.58, 54.04.63-11941, 54.04.70, 54.04.74-14371, 54.04.76)
			#							7170 (FW 29.04.70) 22.03.2009
			#							7141 (FW 40.04.68) 22.03.2009
			#	We expect one line with TrFonName followed by several lines with
			#	TrFonNr(Type,Number,Shortcut,Vanity), which all belong to the name in TrFonName.
			#===============================================================================
			found = re.match('.*<input type="hidden" name="telcfg:settings/Phonebook/Books/Name(\d+)" value="[Dd]reambox" id="uiPostPhonebookName\d+" disabled>', html, re.S)
			if found:
				phoneBookID = found.group(1)
				debug("[FritzCallFBF] _parseFritzBoxPhonebook: found dreambox phonebook with id: " + phoneBookID)
				if self._phoneBookID != phoneBookID:
					self._phoneBookID = phoneBookID
					debug("[FritzCallFBF] _parseFritzBoxPhonebook: reload phonebook")
					self._loadFritzBoxPhonebook(self._phoneBookID) # reload with dreambox phonebook
					return

			found = re.match('.*<meta http-equiv=content-type content="text/html; charset=([^"]*)">', html, re.S)
			if found:
				charset = found.group(1)
				debug("[FritzCallFBF] _parseFritzBoxPhonebook: found charset: " + charset)
				html = html2unicode(html.decode(charset)).encode('utf-8') # this looks silly, but has to be
			else: # this is kind of emergency conversion...
				try:
					html = html2unicode(html.decode('utf-8')).encode('utf-8') # this looks silly, but has to be
				except UnicodeDecodeError:
					html = html2unicode(html.decode('iso-8859-1')).encode('utf-8') # this looks silly, but has to be
			entrymask = re.compile('(TrFonName\("[^"]+", "[^"]+", "[^"]*"\);.*?)TrFon1\(\)', re.S)
			entries = entrymask.finditer(html)
			for entry in entries:
				# debug(entry.group(1)
				# TrFonName (id, name, category)
				found = re.match('TrFonName\("[^"]*", "([^"]+)", "[^"]*"\);', entry.group(1))
				if found:
					name = found.group(1).replace(',','').strip()
				else:
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
						type = found.group(1)
						if config.plugins.FritzCall.showType.value:
							if type == "mobile":
								thisname = thisname + " (" + _("mobile") + ")"
							elif type == "home":
								thisname = thisname + " (" + _("home") + ")"
							elif type == "work":
								thisname = thisname + " (" + _("work") + ")"

						if config.plugins.FritzCall.showShortcut.value and found.group(3):
							thisname = thisname + ", " + _("Shortcut") + ": " + found.group(3)
						if config.plugins.FritzCall.showVanity.value and found.group(4):
							thisname = thisname + ", " + _("Vanity") + ": " + found.group(4)

						debug("[FritzCallFBF] Adding '''%s''' with '''%s''' from FRITZ!Box Phonebook!" % (thisname.strip(), thisnumber))
						# Beware: strings in phonebook.phonebook have to be in utf-8!
						phonebook.phonebook[thisnumber] = thisname

		elif re.search('TrFon', html):
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
					name = html2unicode(unicode(name)).encode('utf-8')
					debug("[FritzCallFBF] Adding '''%s''' with '''%s''' from FRITZ!Box Phonebook!" % (name, thisnumber))
					# Beware: strings in phonebook.phonebook have to be in utf-8!
					phonebook.phonebook[thisnumber] = name
				else:
					debug("[FritzCallFBF] ignoring empty number for %s" % name)
				continue
		elif self._md5Sid=='0000000000000000': # retry, it could be a race condition
			debug("[FritzCallFBF] _parseFritzBoxPhonebook: retry loading phonebook")
			self.loadFritzBoxPhonebook()
		else:
			self._notify(_("Could not parse FRITZ!Box Phonebook entry"))

	def _errorLoad(self, error):
		debug("[FritzCallFBF] _errorLoad: %s" % (error))
		text = _("FRITZ!Box - Could not load phonebook: %s") % error
		self._notify(text)

	def getCalls(self, callScreen, callback, type):
		#
		# call sequence must be:
		# - login
		# - getPage -> _gotPageLogin
		# - loginCallback (_getCalls)
		# - getPage -> _getCalls1
		debug("[FritzCallFBF] getCalls")
		self._callScreen = callScreen
		self._callType = type
		if (time.time() - self._callTimestamp) > 180: 
			debug("[FritzCallFBF] getCalls: outdated data, login and get new ones: " + time.ctime(self._callTimestamp) + " time: " + time.ctime())
			self._callTimestamp = time.time()
			self._login(lambda x:self._getCalls(callback,x))
		elif not self._callList:
			debug("[FritzCallFBF] getCalls: time is ok, but no callList")
			self._getCalls1(callback)
		else:
			debug("[FritzCallFBF] getCalls: time is ok, callList is ok")
			self._gotPageCalls(callback)

	def _getCalls(self, callback, html):
		if html:
			found = re.match('.*<p class="errorMessage">FEHLER:&nbsp;([^<]*)</p>', html, re.S)
			if found:
				self._errorCalls('Login: ' + found.group(1))
				return
		#
		# we need this to fill Anrufliste.csv
		# http://repeater1/cgi-bin/webcm?getpage=../html/de/menus/menu2.html&var:lang=de&var:menu=fon&var:pagename=foncalls
		#
		debug("[FritzCallFBF] _getCalls")
		if html:
			found = re.match('.*<p class="errorMessage">FEHLER:&nbsp;([^<]*)</p>', html, re.S)
			if found:
				text = _("FRITZ!Box - Error logging in: %s") + found.group(1)
				self._notify(text)
				return

		if self._callScreen:
			self._callScreen.updateStatus(_("preparing"))
		parms = urlencode({'getpage':'../html/de/menus/menu2.html', 'var:lang':'de', 'var:pagename':'foncalls', 'var:menu':'fon', 'sid':self._md5Sid})
		url = "http://%s/cgi-bin/webcm?%s" % (config.plugins.FritzCall.hostname.value, parms)
		getPage(url).addCallback(lambda x:self._getCalls1(callback)).addErrback(self._errorCalls)

	def _getCalls1(self, callback):
		#
		# finally we should have successfully lgged in and filled the csv
		#
		debug("[FritzCallFBF] _getCalls1")
		if self._callScreen:
			self._callScreen.updateStatus(_("finishing"))
		parms = urlencode({'getpage':'../html/de/FRITZ!Box_Anrufliste.csv', 'sid':self._md5Sid})
		url = "http://%s/cgi-bin/webcm?%s" % (config.plugins.FritzCall.hostname.value, parms)
		getPage(url).addCallback(lambda x:self._gotPageCalls(callback,x)).addErrback(self._errorCalls)

	def _gotPageCalls(self, callback, csv=""):
		def _resolveNumber(number):
			if number.isdigit():
				if config.plugins.FritzCall.internal.value and len(number) > 3 and number[0] == "0": number = number[1:]
				# strip CbC prefix
				if config.plugins.FritzCall.country.value == '0049':
					if re.match('^0100\d\d', number):
						number = number[6:]
					elif re.match('^010\d\d', number):
						number = number[5:]
				if config.plugins.FritzCall.prefix.value and number and number[0] != '0':		# should only happen for outgoing
					number = config.plugins.FritzCall.prefix.value + number
				name = phonebook.search(number)
				if name:
					found = re.match('(.*?)\n.*', name)
					if found:
						name = found.group(1)
					number = name
			elif number == "":
				number = _("UNKNOWN")
			# if len(number) > 20: number = number[:20]
			return number

		if csv:
			debug("[FritzCallFBF] _gotPageCalls: got csv, setting callList")
			if self._callScreen:
				self._callScreen.updateStatus(_("done"))
			# check for error: wrong password or password not set... TODO
			found = re.search('Melden Sie sich mit dem Kennwort der FRITZ!Box an', csv)
			if found:
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
			debug("[FritzCallFBF] _gotPageCalls: got no csv, no callList, leaving")
			return
			
		_callList = []
		for line in lines:
			# Typ;Datum;Name;Rufnummer;Nebenstelle;Eigene Rufnummer;Dauer
			found = re.match("^(" + self._callType + ");([^;]*);([^;]*);([^;]*);([^;]*);([^;]*);([^;]*)", line)
			if found:
				direct = found.group(1)
				date = found.group(2)
				length = found.group(7)
				remote = _resolveNumber(found.group(4))
				if not remote and direct != FBF_OUT_CALLS and found.group(3):
					remote = found.group(3)
				found1 = re.match('Internet: (.*)', found.group(6))
				if found1:
					here = _resolveNumber(found1.group(1))
				else:
					here = _resolveNumber(found.group(6))
				
				# strip CbC prefix for Germany
				number = found.group(4)
				if config.plugins.FritzCall.country.value == '0049':
					if re.match('^0100\d\d', number):
						number = number[6:]
					elif re.match('^010\d\d', number):
						number = number[5:]
				if config.plugins.FritzCall.prefix.value and number and number[0] != '0':		# should only happen for outgoing
					number = config.plugins.FritzCall.prefix.value + number
				_callList.append((number, date, here, direct, remote, length))

		# debug("[FritzCallFBF] _gotPageCalls result:\n" + text

		if callback:
			# debug("[FritzCallFBF] _gotPageCalls call callback with\n" + text
			callback(_callList)
		self._callScreen = None

	def _errorCalls(self, error):
		debug("[FritzCallFBF] _errorCalls: %s" % (error))
		text = _("FRITZ!Box - Could not load calls: %s") % error
		self._notify(text)

	def dial(self, number):
		''' initiate a call to number '''
		self.number = number
		self._login(self._dial)
		
	def _dial(self, html):
		if html:
			found = re.match('.*<p class="errorMessage">FEHLER:&nbsp;([^<]*)</p>', html, re.S)
			if found:
				self._errorDial('Login: ' + found.group(1))
				return
		url = "http://%s/cgi-bin/webcm" % config.plugins.FritzCall.hostname.value
		parms = urlencode({
			'getpage':'../html/de/menus/menu2.html',
			'var:pagename':'fonbuch',
			'var:menu':'home',
			'telcfg:settings/UseClickToDial':'1',
			'telcfg:settings/DialPort':config.plugins.FritzCall.extension.value,
			'telcfg:command/Dial':self.number,
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

	def _okDial(self, html):
		debug("[FritzCallFBF] okDial")

	def _errorDial(self, error):
		debug("[FritzCallFBF] errorDial: $s" % error)
		text = _("FRITZ!Box - Dialling failed: %s") % error
		self._notify(text)

	def changeWLAN(self, statusWLAN):
		''' get status info from FBF '''
		debug("[FritzCallFBF] changeWLAN start")
		if not statusWLAN or (statusWLAN <> '1' and statusWLAN <> '0'):
			return
		self.statusWLAN = statusWLAN
		self._login(self._changeWLAN)
		
	def _changeWLAN(self, html):
		if html:
			found = re.match('.*<p class="errorMessage">FEHLER:&nbsp;([^<]*)</p>', html, re.S)
			if found:
				self._errorChangeWLAN('Login: ' + found.group(1))
				return
		url = "http://%s/cgi-bin/webcm" % config.plugins.FritzCall.hostname.value
		parms = urlencode({
			'getpage':'../html/de/menus/menu2.html',
			'var:lang':'de',
			'var:pagename':'wlan',
			'var:menu':'wlan',
			'wlan:settings/ap_enabled':str(self.statusWLAN),
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

	def _okChangeWLAN(self, html):
		debug("[FritzCallFBF] okDial")

	def _errorChangeWLAN(self, error):
		debug("[FritzCallFBF] _errorChangeWLAN: $s" % error)
		text = _("FRITZ!Box - Failed changing WLAN: %s") % error
		self._notify(text)

	def changeMailbox(self, whichMailbox):
		''' switch mailbox on/off '''
		debug("[FritzCallFBF] changeMailbox start: " + str(whichMailbox))
		self.whichMailbox = whichMailbox
		self._login(self._changeMailbox)

	def _changeMailbox(self, html):
		if html:
			found = re.match('.*<p class="errorMessage">FEHLER:&nbsp;([^<]*)</p>', html, re.S)
			if found:
				self._errorChangeMailbox('Login: ' + found.group(1))
				return
		debug("[FritzCallFBF] _changeMailbox")
		url = "http://%s/cgi-bin/webcm" % config.plugins.FritzCall.hostname.value
		if self.whichMailbox == -1:
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
		elif self.whichMailbox > 4:
			debug("[FritzCallFBF] changeMailbox invalid mailbox number")
		else:
			if self.info[FBF_tamActive][self.whichMailbox+1]:
				state = '0'
			else:
				state = '1'
			parms = urlencode({
				'tam:settings/TAM'+str(self.whichMailbox)+'/Active':state,
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

	def _okChangeMailbox(self, html):
		debug("[FritzCallFBF] _okChangeMailbox")

	def _errorChangeMailbox(self, error):
		debug("[FritzCallFBF] _errorChangeMailbox: $s" % error)
		text = _("FRITZ!Box - Failed changing Mailbox: %s") % error
		self._notify(text)

	def getInfo(self, callback):
		''' get status info from FBF '''
		debug("[FritzCallFBF] getInfo")
		self._login(lambda x:self._getInfo(callback,x))
		
	def _getInfo(self, callback, html):
		# http://192.168.178.1/cgi-bin/webcm?getpage=../html/de/menus/menu2.html&var:lang=de&var:pagename=home&var:menu=home
		debug("[FritzCallFBF] _getInfo: verify login")
		if html:
			found = re.match('.*<p class="errorMessage">FEHLER:&nbsp;([^<]*)</p>', html, re.S)
			if found:
				self._errorGetInfo('Login: ' + found.group(1))
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
				i=1
				for entry in entries:
					state = entry.group(1)
					if state == '1':
						tamActive[0] += 1
						tamActive[i] = True
					i += 1
				# debug("[FritzCallFBF] _okGetInfo tamActive: " + str(tamActive))
		
			if html.find('countDect2') != -1:
				entries = re.compile('if \("1" == "1"\) countDect2\+\+;', re.S).findall(html)
				dectActive = len(entries)
				# debug("[FritzCallFBF] _okGetInfo dectActive: " + str(dectActive))

			# not used for now
			found = re.match('.*var g_intFaxActive = "0";\s*if \("1" != ""\) {\s*g_intFaxActive = "1";\s*}\s*', html, re.S)
			if found:
				faxActive = True
				# debug("[FritzCallFBF] _okGetInfo faxActive")

			# not used for now
			if html.find('cntRufumleitung') != -1:
				entries = re.compile('mode = "1";\s*ziel = "[^"]+";\s*if \(mode == "1" \|\| ziel != ""\)\s*{\s*g_RufumleitungAktiv = true;', re.S).findall(html)
				rufumlActive = len(entries)
				entries = re.compile('if \("([^"]*)"=="([^"]*)"\) isAllIncoming\+\+;', re.S).finditer(html)
				isAllIncoming = 0
				for entry in entries:
					# debug("[FritzCallFBF] _okGetInfo rufumlActive add isAllIncoming")
					if entry.group(1) == entry.group(2): isAllIncoming += 1
				if isAllIncoming==2 and rufumlActive>0: rufumlActive -= 1
				# debug("[FritzCallFBF] _okGetInfo rufumlActive: " + str(rufumlActive))

			# /cgi-bin/webcm?getpage=../html/de/home/home_dsl.txt
			# { "dsl_carrier_state": "5", "umts_enabled": "0", "ata_mode": "0", "isusbgsm": "", "dsl_ds_nrate": "3130", "dsl_us_nrate": "448", "hint_dsl_no_cable": "0", "wds_enabled": "0", "wds_hop": "0", "isata": "" } 
			found = re.match('.*function DslStateDisplay \(state\){\s*var state = "(\d+)";', html, re.S)
			if found:
				# debug("[FritzCallFBF] _okGetInfo DslState: " + found.group(1))
				dslState = [ found.group(1), None ] # state, speed
				found = re.match('.*function DslStateDisplay \(state\){\s*var state = "\d+";.*?if \("3130" != "0"\) str = "([^"]*)";', html, re.S)
				if found:
					# debug("[FritzCallFBF] _okGetInfo DslSpeed: " + found.group(1).strip())
					dslState[1] = found.group(1).strip()
			else:
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
		
			# /cgi-bin/webcm?getpage=../html/de/home/home_wlan.txt
			# { "ap_enabled": "1", "active_stations": "0", "encryption": "4", "wireless_stickandsurf_enabled": "0", "is_macfilter_active": "0", "wmm_enabled": "1", "wlan_state": [ "end" ] }
			found = re.match('.*function WlanStateLed \(state\){.*?return StateLed\("(\d+)"\);\s*}', html, re.S)
			if found:
				# debug("[FritzCallFBF] _okGetInfo WlanState: " + found.group(1))
				wlanState = [ found.group(1), 0, 0 ] # state, encryption, number of devices
				found = re.match('.*var (?:g_)?encryption = "(\d+)";', html, re.S)
				if found:
					# debug("[FritzCallFBF] _okGetInfo WlanEncrypt: " + found.group(1))
					wlanState[1] = found.group(1)
			else:
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

			return (boxInfo, upTime, ipAddress, wlanState, dslState, tamActive, dectActive, faxActive, rufumlActive)

		debug("[FritzCallFBF] _okGetInfo")
		info = readInfo(html)
		debug("[FritzCallFBF] _okGetInfo info: " + str(info))
		self.info = info
		if callback:
			callback(info)

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
			dslState = [ found.group(1), None ]
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
		text = _("FRITZ!Box - Error getting status: %s") % error
		self._notify(text)
		# linkP = open("/tmp/FritzCall_errorGetInfo.htm", "w")
		# linkP.write(error)
		# linkP.close()

	def reset(self):
		self._login(self._reset)

	def _reset(self, html):
		# POSTDATA=getpage=../html/reboot.html&errorpage=../html/de/menus/menu2.html&var:lang=de&var:pagename=home&var:errorpagename=home&var:menu=home&var:pagemaster=&time:settings/time=1242207340%2C-120&var:tabReset=0&logic:command/reboot=../gateway/commands/saveconfig.html
		if html:
			found = re.match('.*<p class="errorMessage">FEHLER:&nbsp;([^<]*)</p>', html, re.S)
			if found:
				self._errorReset('Login: ' + found.group(1))
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

	def _okReset(self, html):
		debug("[FritzCallFBF] _okReset")

	def _errorReset(self, error):
		debug("[FritzCallFBF] _errorReset: %s" % (error))
		text = _("FRITZ!Box - Error resetting: %s") % error
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

fritzbox = FritzCallFBF()

class FritzMenu(Screen,HelpableScreen):
	def __init__(self, session):
		fontSize = scaleV(24,21) # indeed this is font size +2
		noButtons = 2 # reset, wlan

		if not fritzbox or not fritzbox.info: return

		if fritzbox.info[FBF_tamActive]:
			noButtons += 1 # toggle mailboxes
		width = max(DESKTOP_WIDTH - scaleH(500,250), noButtons*140+(noButtons+1)*10)
		# boxInfo 2 lines, gap, internet 2 lines, gap, dsl/wlan each 1 line, gap, buttons
		height = 5 + 2*fontSize + 10 + 2*fontSize + 10 + 2*fontSize + 10 + 40 + 5
		if fritzbox.info[FBF_tamActive] is not None: height += fontSize
		if fritzbox.info[FBF_dectActive] is not None: height += fontSize
		if fritzbox.info[FBF_faxActive] is not None: height += fontSize
		if fritzbox.info[FBF_rufumlActive] is not None: height += fontSize
		buttonsGap = (width-noButtons*140)/(noButtons+1)
		buttonsVPos = height-40-5

		varLinePos = 4
		if fritzbox.info[FBF_tamActive] is not None:
			mailboxLine = """
				<widget name="FBFMailbox" position="%d,%d" size="%d,%d" font="Regular;%d" />
				<widget name="mailbox_inactive" pixmap="skin_default/buttons/button_green_off.png" position="%d,%d" size="15,16" transparent="1" alphatest="on"/>
				<widget name="mailbox_active" pixmap="skin_default/buttons/button_green.png" position="%d,%d" size="15,16" transparent="1" alphatest="on"/>
				<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
				<widget name="key_yellow" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				""" % (
						40, 5+2*fontSize+10+varLinePos*fontSize+10, # position mailbox
						width-40-20, fontSize, # size mailbox
						fontSize-2,
						20, 5+2*fontSize+10+varLinePos*fontSize+10+(fontSize-16)/2, # position button mailbox
						20, 5+2*fontSize+10+varLinePos*fontSize+10+(fontSize-16)/2, # position button mailbox
						noButtons*buttonsGap+(noButtons-1)*140, buttonsVPos,
						noButtons*buttonsGap+(noButtons-1)*140, buttonsVPos,
				)
			varLinePos += 1
		else:
			mailboxLine = ""

		if fritzbox.info[FBF_dectActive] is not None:
			dectLine = """
				<widget name="FBFDect" position="%d,%d" size="%d,%d" font="Regular;%d" />
				<widget name="dect_inactive" pixmap="skin_default/buttons/button_green_off.png" position="%d,%d" size="15,16" transparent="1" alphatest="on"/>
				<widget name="dect_active" pixmap="skin_default/buttons/button_green.png" position="%d,%d" size="15,16" transparent="1" alphatest="on"/>
				""" %(
						40, 5+2*fontSize+10+varLinePos*fontSize+10, # position dect
						width-40-20, fontSize, # size dect
						fontSize-2,
						20, 5+2*fontSize+10+varLinePos*fontSize+10+(fontSize-16)/2, # position button dect
						20, 5+2*fontSize+10+varLinePos*fontSize+10+(fontSize-16)/2, # position button dect
				)
			varLinePos += 1
		else:
			dectLine = ""

		if fritzbox.info[FBF_faxActive] is not None:
			faxLine = """
				<widget name="FBFFax" position="%d,%d" size="%d,%d" font="Regular;%d" />
				<widget name="fax_inactive" pixmap="skin_default/buttons/button_green_off.png" position="%d,%d" size="15,16" transparent="1" alphatest="on"/>
				<widget name="fax_active" pixmap="skin_default/buttons/button_green.png" position="%d,%d" size="15,16" transparent="1" alphatest="on"/>
				""" %(
						40, 5+2*fontSize+10+varLinePos*fontSize+10, # position dect
						width-40-20, fontSize, # size dect
						fontSize-2,
						20, 5+2*fontSize+10+varLinePos*fontSize+10+(fontSize-16)/2, # position button dect
						20, 5+2*fontSize+10+varLinePos*fontSize+10+(fontSize-16)/2, # position button dect
				)
			varLinePos += 1
		else:
			faxLine = ""

		if fritzbox.info[FBF_rufumlActive] is not None:
			rufumlLine = """
				<widget name="FBFRufuml" position="%d,%d" size="%d,%d" font="Regular;%d" />
				<widget name="rufuml_inactive" pixmap="skin_default/buttons/button_green_off.png" position="%d,%d" size="15,16" transparent="1" alphatest="on"/>
				<widget name="rufuml_active" pixmap="skin_default/buttons/button_green.png" position="%d,%d" size="15,16" transparent="1" alphatest="on"/>
				""" %(
						40, 5+2*fontSize+10+varLinePos*fontSize+10, # position dect
						width-40-20, fontSize, # size dect
						fontSize-2,
						20, 5+2*fontSize+10+varLinePos*fontSize+10+(fontSize-16)/2, # position button dect
						20, 5+2*fontSize+10+varLinePos*fontSize+10+(fontSize-16)/2, # position button dect
				)
			varLinePos += 1
		else:
			rufumlLine = ""
	
		self.skin = """
			<screen name="FritzMenu" position="%d,%d" size="%d,%d" title="%s" >
				<widget name="FBFInfo" position="%d,%d" size="%d,%d" font="Regular;%d" />
				<widget name="FBFInternet" position="%d,%d" size="%d,%d" font="Regular;%d" />
				<widget name="internet_inactive" pixmap="skin_default/buttons/button_green_off.png" position="%d,%d" size="15,16" transparent="1" alphatest="on"/>
				<widget name="internet_active" pixmap="skin_default/buttons/button_green.png" position="%d,%d" size="15,16" transparent="1" alphatest="on"/>
				<widget name="FBFDsl" position="%d,%d" size="%d,%d" font="Regular;%d" />
				<widget name="dsl_inactive" pixmap="skin_default/buttons/button_green_off.png" position="%d,%d" size="15,16" transparent="1" alphatest="on"/>
				<widget name="dsl_active" pixmap="skin_default/buttons/button_green.png" position="%d,%d" size="15,16" transparent="1" alphatest="on"/>
				<widget name="FBFWlan" position="%d,%d" size="%d,%d" font="Regular;%d" />
				<widget name="wlan_inactive" pixmap="skin_default/buttons/button_green_off.png" position="%d,%d" size="15,16" transparent="1" alphatest="on"/>
				<widget name="wlan_active" pixmap="skin_default/buttons/button_green.png" position="%d,%d" size="15,16" transparent="1" alphatest="on"/>
				%s
				%s
				%s
				%s
				<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
				<widget name="key_red" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
				<widget name="key_green" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			</screen>""" % (
						(DESKTOP_WIDTH - width) / 2, (DESKTOP_HEIGHT - height) / 2, # position
						width, height, # size
						_("FRITZ!Box Fon Status"),
						40, 5, # position info
						width-2*40, 2*fontSize, # size info
						fontSize-2,
						40, 5+2*fontSize+10, # position internet
						width-40, 2*fontSize, # size internet
						fontSize-2,
						20, 5+2*fontSize+10+(fontSize-16)/2, # position button internet
						20, 5+2*fontSize+10+(fontSize-16)/2, # position button internet
						40, 5+2*fontSize+10+2*fontSize+10, # position dsl
						width-40-20, fontSize, # size dsl
						fontSize-2,
						20, 5+2*fontSize+10+2*fontSize+10+(fontSize-16)/2, # position button dsl
						20, 5+2*fontSize+10+2*fontSize+10+(fontSize-16)/2, # position button dsl
						40, 5+2*fontSize+10+3*fontSize+10, # position wlan
						width-40-20, fontSize, # size wlan
						fontSize-2,
						20, 5+2*fontSize+10+3*fontSize+10+(fontSize-16)/2, # position button wlan
						20, 5+2*fontSize+10+3*fontSize+10+(fontSize-16)/2, # position button wlan
						mailboxLine,
						dectLine,
						faxLine,
						rufumlLine,
						buttonsGap, buttonsVPos, buttonsGap, buttonsVPos,
						buttonsGap+140+buttonsGap, buttonsVPos, buttonsGap+140+buttonsGap, buttonsVPos,
						)

		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		# TRANSLATORS: keep it short, this is a button
		self["key_red"] = Button(_("Reset"))
		# TRANSLATORS: keep it short, this is a button
		self["key_green"] = Button(_("Toggle WLAN"))
		self._mailboxActive = False
		if fritzbox.info[FBF_tamActive] is not None:
			# TRANSLATORS: keep it short, this is a button
			self["key_yellow"] = Button(_("Toggle Mailbox"))
			self["menuActions"] = ActionMap(["OkCancelActions", "ColorActions", "NumberActions", "EPGSelectActions"],
											{
											"cancel": self._exit,
											"ok": self._exit,
											"red": self._reset,
											"green": self._toggleWlan,
											"yellow": (lambda: self._toggleMailbox(-1)),
											"0": (lambda: self._toggleMailbox(0)),
											"1": (lambda: self._toggleMailbox(1)),
											"2": (lambda: self._toggleMailbox(2)),
											"3": (lambda: self._toggleMailbox(3)),
											"4": (lambda: self._toggleMailbox(4)),
											"info": self._getInfo,
											}, -2)
			# TRANSLATORS: keep it short, this is a help text
			self.helpList.append((self["menuActions"], "ColorActions", [("yellow", _("Toggle all mailboxes"))]))
			# TRANSLATORS: keep it short, this is a help text
			self.helpList.append((self["menuActions"], "NumberActions", [("0", _("Toggle 1. mailbox"))]))
			# TRANSLATORS: keep it short, this is a help text
			self.helpList.append((self["menuActions"], "NumberActions", [("1", _("Toggle 2. mailbox"))]))
			# TRANSLATORS: keep it short, this is a help text
			self.helpList.append((self["menuActions"], "NumberActions", [("2", _("Toggle 3. mailbox"))]))
			# TRANSLATORS: keep it short, this is a help text
			self.helpList.append((self["menuActions"], "NumberActions", [("3", _("Toggle 4. mailbox"))]))
			# TRANSLATORS: keep it short, this is a help text
			self.helpList.append((self["menuActions"], "NumberActions", [("4", _("Toggle 5. mailbox"))]))
			self["FBFMailbox"] = Label(_('Mailbox'))
			self["mailbox_inactive"] = Pixmap()
			self["mailbox_active"] = Pixmap()
			self["mailbox_active"].hide()
		else:
			self["menuActions"] = ActionMap(["OkCancelActions", "ColorActions", "EPGSelectActions"],
											{
											"cancel": self._exit,
											"ok": self._exit,
											"green": self._toggleWlan,
											"red": self._reset,
											"info": self._getInfo,
											}, -2)

		# TRANSLATORS: keep it short, this is a help text
		self.helpList.append((self["menuActions"], "OkCancelActions", [("cancel", _("Quit"))]))
		# TRANSLATORS: keep it short, this is a help text
		self.helpList.append((self["menuActions"], "OkCancelActions", [("ok", _("Quit"))]))
		# TRANSLATORS: keep it short, this is a help text
		self.helpList.append((self["menuActions"], "ColorActions", [("green", _("Toggle WLAN"))]))
		# TRANSLATORS: keep it short, this is a help text
		self.helpList.append((self["menuActions"], "ColorActions", [("red", _("Reset"))]))
		# TRANSLATORS: keep it short, this is a help text
		self.helpList.append((self["menuActions"], "EPGSelectActions", [("info", _("Refresh status"))]))

		self["FBFInfo"] = Label(_('Getting status from FRITZ!Box Fon...'))

		self["FBFInternet"] = Label('Internet')
		self["internet_inactive"] = Pixmap()
		self["internet_active"] = Pixmap()
		self["internet_active"].hide()

		self["FBFDsl"] = Label('DSL')
		self["dsl_inactive"] = Pixmap()
		self["dsl_inactive"].hide()
		self["dsl_active"] = Pixmap()
		self["dsl_active"].hide()

		self["FBFWlan"] = Label('WLAN ')
		self["wlan_inactive"] = Pixmap()
		self["wlan_inactive"].hide()
		self["wlan_active"] = Pixmap()
		self["wlan_active"].hide()
		self._wlanActive = False

		if fritzbox.info[FBF_dectActive] is not None: 
			self["FBFDect"] = Label('DECT')
			self["dect_inactive"] = Pixmap()
			self["dect_active"] = Pixmap()
			self["dect_active"].hide()

		if fritzbox.info[FBF_faxActive] is not None: 
			self["FBFFax"] = Label('Fax')
			self["fax_inactive"] = Pixmap()
			self["fax_active"] = Pixmap()
			self["fax_active"].hide()

		if fritzbox.info[FBF_rufumlActive] is not None: 
			self["FBFRufuml"] = Label(_('Call redirection'))
			self["rufuml_inactive"] = Pixmap()
			self["rufuml_active"] = Pixmap()
			self["rufuml_active"].hide()

		self._timer = eTimer()
		self._timer.callback.append(self._getInfo)
		self.onShown.append(lambda: self._timer.start(5000))
		self.onHide.append(lambda: self._timer.stop())
		self._getInfo()

	def _getInfo(self):
		fritzbox.getInfo(self._fillMenu)

	def _fillMenu(self, status):
		(boxInfo, upTime, ipAddress, wlanState, dslState, tamActive, dectActive, faxActive, rufumlActive) = status
		self._wlanActive = (wlanState[0] == '1')
		self._mailboxActive = False
		try:
			if boxInfo:
				self["FBFInfo"].setText(boxInfo.replace(', ', '\n'))
			else:
				self["FBFInfo"].setText('BoxInfo ' + _('Status not available'))

			if ipAddress:
				if upTime:
					self["FBFInternet"].setText('Internet ' + _('IP Address:') + ' ' + ipAddress + '\n' + _('Connected since') + ' ' + upTime)
				else:
					self["FBFInternet"].setText('Internet ' + _('IP Address:') + ' ' + ipAddress)
				self["internet_inactive"].hide()
				self["internet_active"].show()
			else:
				self["internet_active"].hide()
				self["internet_inactive"].show()

			if dslState:
				if dslState[0]=='5':
					self["dsl_inactive"].hide()
					self["dsl_active"].show()
					if dslState[1]:
						self["FBFDsl"].setText('DSL ' + dslState[1])
				else:
					self["dsl_active"].hide()
					self["dsl_inactive"].show()
			else:
				self["FBFDsl"].setText('DSL ' + _('Status not available'))
				self["dsl_active"].hide()
				self["dsl_inactive"].hide()

			if wlanState:
				if wlanState[0]=='1':
					self["wlan_inactive"].hide()
					self["wlan_active"].show()
					message = 'WLAN'
					if wlanState[1]=='0':
						message += ' ' + _('not encrypted')
					else:
						message += ' ' + _('encrypted')
					if wlanState[2]:
						if wlanState[2]=='0':
							message = message + ', ' + _('no device active')
						elif wlanState[2]=='1':
							message = message + ', ' + _('one device active')
						else:
							message = message + ', ' + wlanState[2] + ' ' + _('devices active')
					self["FBFWlan"].setText(message)
				else:
					self["wlan_active"].hide()
					self["wlan_inactive"].show()
					self["FBFWlan"].setText('WLAN')
			else:
				self["FBFWlan"].setText('WLAN ' + _('Status not available'))
				self["wlan_active"].hide()
				self["wlan_inactive"].hide()

			if fritzbox.info[FBF_tamActive]:
				if  not tamActive or tamActive[0] == 0:
					self._mailboxActive = False
					self["mailbox_active"].hide()
					self["mailbox_inactive"].show()
					self["FBFMailbox"].setText(_('No mailbox active'))
				else:
					self._mailboxActive = True
					message = '('
					for i in range(5):
						if tamActive[i+1]:
							message = message + str(i) + ','
					message = message[:-1] + ')'
					self["mailbox_inactive"].hide()
					self["mailbox_active"].show()
					if tamActive[0] == 1:
						self["FBFMailbox"].setText(_('One mailbox active') + ' ' + message)
					else:
						self["FBFMailbox"].setText(str(tamActive[0]) + ' ' + _('mailboxes active') + ' ' + message)
	
			if fritzbox.info[FBF_dectActive] and dectActive:
				self["dect_inactive"].hide()
				self["dect_active"].show()
				if dectActive == 0:
					self["FBFDect"].setText(_('No DECT phone registered'))
				else:
					if dectActive == 1:
						self["FBFDect"].setText(_('One DECT phone registered'))
					else:
						self["FBFDect"].setText(str(dectActive) + ' ' + _('DECT phones registered'))

			if fritzbox.info[FBF_faxActive] and faxActive:
				self["fax_inactive"].hide()
				self["fax_active"].show()
				self["FBFFax"].setText(_('Software fax active'))

			if fritzbox.info[FBF_rufumlActive] is not None and rufumlActive is not None:
				if rufumlActive == 0:
					self["rufuml_active"].hide()
					self["rufuml_inactive"].show()
					self["FBFRufuml"].setText(_('No call redirection active'))
				else:
					self["rufuml_inactive"].hide()
					self["rufuml_active"].show()
					if rufumlActive == 1:
						self["FBFRufuml"].setText(_('One call redirection active'))
					else:
						self["FBFRufuml"].setText(str(rufumlActive) + ' ' + _('call redirections active'))

		except KeyError:
			debug("[FritzCallFBF] _fillMenu: " + traceback.format_exc())

	def _toggleWlan(self):
		if self._wlanActive:
			debug("[FritzMenu] toggleWlan off")
			fritzbox.changeWLAN('0')
		else:
			debug("[FritzMenu] toggleWlan off")
			fritzbox.changeWLAN('1')

	def _toggleMailbox(self, which):
		debug("[FritzMenu] toggleMailbox")
		if fritzbox.info[FBF_tamActive]:
			debug("[FritzMenu] toggleMailbox off")
			fritzbox.changeMailbox(which)

	def _reset(self):
		fritzbox.reset()
		self._exit()

	def _exit(self):
		self._timer.stop()
		self.close()


class FritzDisplayCalls(Screen, HelpableScreen):

	def __init__(self, session, text=""):
		if config.plugins.FritzCall.fullscreen.value:
			self.width = DESKTOP_WIDTH
			self.height = DESKTOP_HEIGHT
			backMainPng = ""
			if os.path.exists(resolveFilename(SCOPE_SKIN_IMAGE, DESKTOP_SKIN + "/menu/back-main.png")):
				backMainPng = DESKTOP_SKIN + "/menu/back-main.png"
			elif os.path.exists(resolveFilename(SCOPE_SKIN_IMAGE, "Kerni-HD1/menu/back-main.png")):
				backMainPng = "Kerni-HD1/menu/back-main.png"
			elif os.path.exists(resolveFilename(SCOPE_SKIN_IMAGE, "Kerni-HD1-picon/menu/back-main.png")):
				backMainPng = "Kerni-HD1-picon/menu/back-main.png"
			if backMainPng:
					backMainLine = """<ePixmap position="0,0" zPosition="-10" size="%d,%d" pixmap="%s" transparent="1" />""" % (self.width, self.height, backMainPng)
			else:
				backMainLine = ""
			debug("[FritzDisplayCalls] backMainLine: " + backMainLine)
				
			# TRANSLATORS: this is a window title. Avoid the use of non ascii chars
			self.skin = """
				<screen name="FritzDisplayCalls" position="0,0" size="%d,%d" title="%s" flags="wfNoBorder">
					%s
					<widget source="global.CurrentTime" render="Label" position="%d,%d" size="%d,%d" font="Regular;%d" halign="right" backgroundColor="#0b67a2" transparent="1">
						<convert type="ClockToText">Default</convert>
					</widget>
					<widget source="global.CurrentTime" render="Label" position="%d,%d" size="%d,%d" font="Regular;%d" halign="right" backgroundColor="#0b67a2" transparent="1">
						<convert type="ClockToText">Date</convert>
					</widget>
					<eLabel text="%s" position="%d,%d" size="%d,%d" font="Regular;%d" halign="center" backgroundColor="#0b67a2" transparent="1"/>
			
					<widget name="statusbar" position="%d,%d"  size="%d,%d" font="Regular;%d" backgroundColor="#353e575e" transparent="1" />
					<widget name="entries" position="%d,%d" size="%d,%d" scrollbarMode="showOnDemand" transparent="1" />
			
					<ePixmap pixmap="skin_default/buttons/red.png" 		position="%d,%d" 	size="%d,%d" alphatest="on" />
					<ePixmap pixmap="skin_default/buttons/green.png" 	position="%d,%d" 	size="%d,%d" alphatest="on" />
					<ePixmap pixmap="skin_default/buttons/yellow.png" 	position="%d,%d" 	size="%d,%d" alphatest="on" />
					<ePixmap pixmap="skin_default/buttons/blue.png" 	position="%d,%d" 	size="%d,%d" alphatest="on" />
					<widget name="key_red" 	position="%d,%d" 	size="%d,%d" zPosition="1" font="Regular;%d" halign="left" backgroundColor="black" transparent="1" />
					<widget name="key_green" 	position="%d,%d" 	size="%d,%d" zPosition="1" font="Regular;%d" halign="left" backgroundColor="black" transparent="1" />
					<widget name="key_yellow" 	position="%d,%d" 	size="%d,%d" zPosition="1" font="Regular;%d" halign="left" backgroundColor="black" transparent="1" />
					<widget name="key_blue" 	position="%d,%d" 	size="%d,%d" zPosition="1" font="Regular;%d" halign="left" backgroundColor="black" transparent="1" />
					<ePixmap position="%d,%d" size="%d,%d" zPosition="2" pixmap="%s" transparent="1" alphatest="blend" />		
				</screen>""" % (
							self.width, self.height, _("Phone calls"),
							backMainLine,
							scaleH(1130, XXX), scaleV(40, XXX), scaleH(80, XXX), scaleV(26, XXX), scaleV(26, XXX), # time
							scaleH(900, XXX), scaleV(70, XXX), scaleH(310, XXX), scaleV(22, XXX), scaleV(20, XXX), # date
							"FritzCall " + _("Phone calls"), scaleH(500, XXX), scaleV(63, XXX), scaleH(330, XXX), scaleV(30, XXX), scaleV(27, XXX), # eLabel
							scaleH(80, XXX), scaleV(150, XXX), scaleH(280, XXX), scaleV(200, XXX), scaleV(22, XXX), # statusbar
							scaleH(420, XXX), scaleV(120, XXX), scaleH(790, XXX), scaleV(438, XXX), # entries
							scaleH(450, XXX), scaleV(588, XXX), scaleH(21, XXX), scaleV(21, XXX), # red
							scaleH(640, XXX), scaleV(588, XXX), scaleH(21, XXX), scaleV(21, XXX), # green
							scaleH(830, XXX), scaleV(588, XXX), scaleH(21, XXX), scaleV(21, XXX), # yellow
							scaleH(1020, XXX), scaleV(588, XXX), scaleH(21, XXX), scaleV(21, XXX), # blue
							scaleH(480, XXX), scaleV(587, XXX), scaleH(160, XXX), scaleV(22, XXX), scaleV(20, XXX), # red
							scaleH(670, XXX), scaleV(587, XXX), scaleH(160, XXX), scaleV(22, XXX), scaleV(20, XXX), # green
							scaleH(860, XXX), scaleV(587, XXX), scaleH(160, XXX), scaleV(22, XXX), scaleV(20, XXX), # yellow
							scaleH(1050, XXX), scaleV(587, XXX), scaleH(160, XXX), scaleV(22, XXX), scaleV(20, XXX), # blue
							scaleH(120, XXX), scaleV(430, XXX), scaleH(150, XXX), scaleV(110, XXX), resolveFilename(SCOPE_PLUGINS, "Extensions/FritzCall/images/fritz.png") # Fritz Logo size and pixmap
														)
		else:
			self.width = scaleH(1100, 570)
			debug("[FritzDisplayCalls] width: " + str(self.width))
			# TRANSLATORS: this is a window title. Avoid the use of non ascii chars
			self.skin = """
				<screen name="FritzDisplayCalls" position="%d,%d" size="%d,%d" title="%s" >
					<eLabel position="0,0" size="%d,2" backgroundColor="#aaaaaa" />
					<widget name="statusbar" position="%d,%d" size="%d,%d" font="Regular;%d" backgroundColor="#aaaaaa" transparent="1" />
					<eLabel position="0,%d" size="%d,2" backgroundColor="#aaaaaa" />
					<widget name="entries" position="%d,%d" size="%d,%d" scrollbarMode="showOnDemand" />
					<eLabel position="0,%d" size="%d,2" backgroundColor="#aaaaaa" />
					<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
					<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
					<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
					<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
					<widget name="key_red" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
					<widget name="key_green" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
					<widget name="key_yellow" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
					<widget name="key_blue" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				</screen>""" % (
							scaleH(90, 75), scaleV(100, 78), # position 
							scaleH(1100, 570), scaleV(560, 430), # size
							_("Phone calls"),
							scaleH(1100, 570), # eLabel width
							scaleH(40, 5), scaleV(10, 5), # statusbar position
							scaleH(1050, 560), scaleV(25, 22), # statusbar size
							scaleV(21, 21), # statusbar font size
							scaleV(40, 28), # eLabel position vertical
							scaleH(1100, 570), # eLabel width
							scaleH(40, 5), scaleV(55, 40), # entries position
							scaleH(1040, 560), scaleV(458, 340), # entries size
							scaleV(518, 390), # eLabel position vertical
							scaleH(1100, 570), # eLabel width
							scaleH(20, 5), scaleV(525, 395), # widget red
							scaleH(290, 145), scaleV(525, 395), # widget green
							scaleH(560, 285), scaleV(525, 395), # widget yellow
							scaleH(830, 425), scaleV(525, 395), # widget blue
							scaleH(20, 5), scaleV(525, 395), scaleV(22, 21), # widget red
							scaleH(290, 145), scaleV(525, 395), scaleV(22, 21), # widget green
							scaleH(560, 285), scaleV(525, 395), scaleV(22, 21), # widget yellow
							scaleH(830, 425), scaleV(525, 395), scaleV(22, 21), # widget blue
														)

		Screen.__init__(self, session)
		HelpableScreen.__init__(self)

		# TRANSLATORS: keep it short, this is a button
		self["key_yellow"] = Button(_("All"))
		# TRANSLATORS: keep it short, this is a button
		self["key_red"] = Button(_("Missed"))
		# TRANSLATORS: keep it short, this is a button
		self["key_blue"] = Button(_("Incoming"))
		# TRANSLATORS: keep it short, this is a button
		self["key_green"] = Button(_("Outgoing"))

		self["setupActions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"yellow": (lambda: self.display(FBF_ALL_CALLS)),
			"red": (lambda: self.display(FBF_MISSED_CALLS)),
			"blue": (lambda: self.display(FBF_IN_CALLS)),
			"green": (lambda: self.display(FBF_OUT_CALLS)),
			"cancel": self.ok,
			"ok": self.showEntry, }, - 2)

		# TRANSLATORS: keep it short, this is a help text
		self.helpList.append((self["setupActions"], "OkCancelActions", [("ok", _("Show details of entry"))]))
		# TRANSLATORS: keep it short, this is a help text
		self.helpList.append((self["setupActions"], "OkCancelActions", [("cancel", _("Quit"))]))
		# TRANSLATORS: keep it short, this is a help text
		self.helpList.append((self["setupActions"], "ColorActions", [("yellow", _("Display all calls"))]))
		# TRANSLATORS: keep it short, this is a help text
		self.helpList.append((self["setupActions"], "ColorActions", [("red", _("Display missed calls"))]))
		# TRANSLATORS: keep it short, this is a help text
		self.helpList.append((self["setupActions"], "ColorActions", [("blue", _("Display incoming calls"))]))
		# TRANSLATORS: keep it short, this is a help text
		self.helpList.append((self["setupActions"], "ColorActions", [("green", _("Display outgoing calls"))]))

		self["statusbar"] = Label(_("Getting calls from FRITZ!Box..."))
		self["entries"] = MenuList([], True, content=eListboxPythonMultiContent)
		fontSize = scaleV(22, 18)
		fontHeight = scaleV(24, 20)
		self["entries"].l.setFont(0, gFont("Regular", fontSize))
		self["entries"].l.setItemHeight(fontHeight)

		debug("[FritzDisplayCalls] init: '''%s'''" % config.plugins.FritzCall.fbfCalls.value)
		self.display()

	def ok(self):
		self.close()

	def display(self, which=config.plugins.FritzCall.fbfCalls.value):
		debug("[FritzDisplayCalls] display")
		config.plugins.FritzCall.fbfCalls.value = which
		config.plugins.FritzCall.fbfCalls.save()
		self.header = fbfCallsChoices[which]
		fritzbox.getCalls(self, self.gotCalls, which)

	def gotCalls(self, callList):
		debug("[FritzDisplayCalls] gotCalls")
		self.updateStatus(self.header + " (" + str(len(callList)) + ")")
		dateFieldWidth = scaleH(140,100)
		dirFieldWidth = 16
		lengthFieldWidth = scaleH(50,50)
		remoteFieldWidth = scaleH(140,100)
		scrollbarWidth = scaleH(35,35)
		if config.plugins.FritzCall.fullscreen.value:
			fieldWidth = 790 -dateFieldWidth -5 -dirFieldWidth -5 -lengthFieldWidth -5 -remoteFieldWidth -scrollbarWidth -5
			fontSize = scaleV(22,20)
		else:
			fieldWidth = self.width -scaleH(60, 5) -dateFieldWidth -5 -dirFieldWidth -5 -lengthFieldWidth -5 -remoteFieldWidth -scrollbarWidth -5
			fontSize = scaleV(24,20)
		sortlist = []
		for (number, date, remote, direct, here, length) in callList:
			found = re.match("(\d\d.\d\d.)\d\d( \d\d:\d\d)", date)
			if found: date = found.group(1) + found.group(2)
			if direct == FBF_OUT_CALLS:
				dir = LoadPixmap(resolveFilename(SCOPE_PLUGINS, "Extensions/FritzCall/images/callout.png"))
			elif direct == FBF_IN_CALLS:
				dir = LoadPixmap(resolveFilename(SCOPE_PLUGINS, "Extensions/FritzCall/images/callin.png"))
			else:
				dir = LoadPixmap(resolveFilename(SCOPE_PLUGINS, "Extensions/FritzCall/images/callinfailed.png"))
			# debug("[FritzDisplayCalls] gotCalls: d: %d; f: %d; d: %d; r: %d" %(dateFieldWidth, fieldWidth, dirFieldWidth, remoteFieldWidth))
			sortlist.append([number,
							 (eListboxPythonMultiContent.TYPE_TEXT, 0, 0, dateFieldWidth, fontSize, 0, RT_HALIGN_LEFT, date),
							 (eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, dateFieldWidth+5, 0, dirFieldWidth, 16, dir),
							 (eListboxPythonMultiContent.TYPE_TEXT, dateFieldWidth+5+dirFieldWidth+5, 0, fieldWidth, fontSize, 0, RT_HALIGN_LEFT, here),
							 (eListboxPythonMultiContent.TYPE_TEXT, dateFieldWidth+5+dirFieldWidth+5+fieldWidth+5, 0, lengthFieldWidth, fontSize, 0, RT_HALIGN_LEFT, length),
							 (eListboxPythonMultiContent.TYPE_TEXT, dateFieldWidth+5+dirFieldWidth+5+fieldWidth+5+lengthFieldWidth+5, 0, remoteFieldWidth, fontSize, 0, RT_HALIGN_RIGHT, remote)
							 ])

		self["entries"].setList(sortlist)

	def updateStatus(self, text):
		self["statusbar"].setText(_("Getting calls from FRITZ!Box...") + ' ' + text)

	def showEntry(self):
		debug("[FritzDisplayCalls] showEntry")
		cur = self["entries"].getCurrent()
		if cur:
			if cur[0]:
				debug("[FritzDisplayCalls] showEntry %s" % (cur[0]))
				number = cur[0]
				fullname = phonebook.search(cur[0])
				if fullname:
					# we have a name for this number
					name = fullname
					self.session.open(FritzOfferAction, self, number, name)
				else:
					# we don't
					self.session.open(FritzOfferAction, self, number)
			else:
				# we do not even have a number...
				self.session.open(MessageBox,
						  _("UNKNOWN"),
						  type=MessageBox.TYPE_INFO)


class FritzOfferAction(Screen):

	def __init__(self, session, parent, number, name=""):
		noButtons = 3
		width = max(scaleH(-1,440), noButtons*140)
		height = scaleV(-1,176) # = 5 + 126 + 40 + 5; 6 lines of text possible
		buttonsGap = (width-noButtons*140)/(noButtons+1)
		buttonsVPos = height-40-5
		# TRANSLATORS: this is a window title. Avoid the use of non ascii chars
		self.skin = """
			<screen name="FritzOfferAction" position="%d,%d" size="%d,%d" title="%s" >
				<widget name="text" position="5,5" size="%d,%d" font="Regular;%d" />
				<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
				<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
				<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
				<widget name="key_red" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_green" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_yellow" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			</screen>""" % (
							(DESKTOP_WIDTH - width) / 2,
							(DESKTOP_HEIGHT - height) / 2,
							width,
							height,
							_("Do what?"),
							width - 10,
							height - 10 - 40,
							scaleH(22,21),
							buttonsGap, buttonsVPos,
							buttonsGap+140+buttonsGap, buttonsVPos,
							buttonsGap+2*(140+buttonsGap), buttonsVPos,
							buttonsGap, buttonsVPos,
							buttonsGap+140+buttonsGap, buttonsVPos,
							buttonsGap+2*(140+buttonsGap), buttonsVPos,
							) 
		debug("[FritzOfferAction] init: %s, %s" %(number, name))
		Screen.__init__(self, session)
	
		# TRANSLATORS: keep it short, this is a button
		self["key_red"] = Button(_("Lookup"))
		# TRANSLATORS: keep it short, this is a button
		self["key_green"] = Button(_("Call"))
		# TRANSLATORS: keep it short, this is a button
		self["key_yellow"] = Button(_("Save"))
		# TRANSLATORS: keep it short, this is a button
		# self["key_blue"] = Button(_("Search"))

		self["FritzOfferActions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"red": self.lookup,
			"green": self.call,
			"yellow": self.add,
			"cancel": self.exit,
			"ok": self.exit, }, - 2)

		self["text"] = Label(number + "\n\n" + name.replace(", ", "\n"))
		self.actualNumber = number
		self.actualName = name.replace("\n", ", ")
		self.parent = parent
		self.lookupState = 0

	def lookup(self):
		phonebookLocation = config.plugins.FritzCall.phonebookLocation.value
		if self.lookupState == 0:
			self.lookupState = 1
			self["text"].setText(self.actualNumber + "\n\n" + _("Reverse searching..."))
			ReverseLookupAndNotifier(self.actualNumber, self.lookedUp, "UTF-8", config.plugins.FritzCall.country.value)
			return
		if self.lookupState == 1 and os.path.exists(phonebookLocation + "/PhoneBook.csv"):
			self["text"].setText(self.actualNumber + "\n\n" + _("Searching in Outlook export..."))
			self.lookupState = 2
			self.lookedUp(self.actualNumber, FritzOutlookCSV.findNumber(self.actualNumber, phonebookLocation + "/PhoneBook.csv")) #@UndefinedVariable
			return
		else:
			self.lookupState = 2
		if self.lookupState == 2 and os.path.exists(phonebookLocation + "/PhoneBook.ldif"):
			self["text"].setText(self.actualNumber + "\n\n" + _("Searching in LDIF..."))
			self.lookupState = 0
			FritzLDIF.findNumber(self.actualNumber, open(phonebookLocation + "/PhoneBook.ldif"), self.lookedUp)
			return
		else:
			self.lookupState = 0
			self.lookup()

	def lookedUp(self, number, name):
		if not name:
			if self.lookupState == 1:
				name = _("No result from reverse lookup")
			elif self.lookupState == 2:
				name = _("No result from Outlook export")
			else:
				name = _("No result from LDIF")
		self.actualNumber = number
		self.actualName = name
		message = number + "\n\n" + name.replace(", ", "\n")
		self["text"].setText(str(message))

	def call(self):
		debug("[FritzOfferAction] add: %s" %self.actualNumber)
		fritzbox.dial(self.actualNumber)
		self.exit()

	def add(self):
		debug("[FritzOfferAction] add: %s, %s" %(self.actualNumber, self.actualName))
		phonebook.FritzDisplayPhonebook(self.session).add(self.parent, self.actualNumber, self.actualName)
		self.exit()

	def exit(self):
		self.close()


class FritzCallPhonebook:
	def __init__(self):
		debug("[FritzCallPhonebook] init")
		# Beware: strings in phonebook.phonebook have to be in utf-8!
		self.phonebook = {}
		self.reload()

	def reload(self):
		debug("[FritzCallPhonebook] reload")
		# Beware: strings in phonebook.phonebook have to be in utf-8!
		self.phonebook = {}

		if not config.plugins.FritzCall.enable.value:
			return

		phonebookFilename = config.plugins.FritzCall.phonebookLocation.value + "/PhoneBook.txt"
		if config.plugins.FritzCall.phonebook.value and os.path.exists(phonebookFilename):
			debug("[FritzCallPhonebook] reload: read " + phonebookFilename)
			phonebookTxtCorrupt = False
			for line in open(phonebookFilename):
				try:
					# Beware: strings in phonebook.phonebook have to be in utf-8!
					line = line.decode("utf-8")
				except UnicodeDecodeError: # this is just for the case, somebody wrote latin1 chars into PhoneBook.txt
					try:
						line = line.decode("iso-8859-1")
						debug("[FritzCallPhonebook] Fallback to ISO-8859-1 in %s" % line)
						phonebookTxtCorrupt = True
					except:
						debug("[FritzCallPhonebook] Could not parse internal Phonebook Entry %s" % line)
						phonebookTxtCorrupt = True
				line = line.encode("utf-8")
				if re.match("^\d+#.*$", line):
					try:
						number, name = line.split("#")
						if not self.phonebook.has_key(number):
							# Beware: strings in phonebook.phonebook have to be in utf-8!
							self.phonebook[number] = name
					except ValueError: # how could this possibly happen?!?!
						debug("[FritzCallPhonebook] Could not parse internal Phonebook Entry %s" % line)
						phonebookTxtCorrupt = True
				else:
					debug("[FritzCallPhonebook] Could not parse internal Phonebook Entry %s" % line)
					phonebookTxtCorrupt = True

			if phonebookTxtCorrupt:
				# dump phonebook to PhoneBook.txt
				debug("[FritzCallPhonebook] dump Phonebook.txt")
				os.rename(phonebookFilename, phonebookFilename + ".bck")
				fNew = open(phonebookFilename, 'w')
				# Beware: strings in phonebook.phonebook are utf-8!
				for (number, name) in self.phonebook.iteritems():
					# Beware: strings in PhoneBook.txt have to be in utf-8!
					fNew.write(number + "#" + name.encode("utf-8"))
				fNew.close()

#===============================================================================
#		#
#		# read entries from Outlook export
#		#
#		# not reliable with coding yet
#		# 
#		# import csv exported from Outlook 2007 with csv(Windows)
#		csvFilename = "/tmp/PhoneBook.csv"
#		if config.plugins.FritzCall.phonebook.value and os.path.exists(csvFilename):
#			try:
#				readOutlookCSV(csvFilename, self.add)
#				os.rename(csvFilename, csvFilename + ".done")
#			except ImportError:
#				debug("[FritzCallPhonebook] CSV import failed" %line)
#===============================================================================

		
#===============================================================================
#		#
#		# read entries from LDIF
#		#
#		# import ldif exported from Thunderbird 2.0.0.19
#		ldifFilename = "/tmp/PhoneBook.ldif"
#		if config.plugins.FritzCall.phonebook.value and os.path.exists(ldifFilename):
#			try:
#				parser = MyLDIF(open(ldifFilename), self.add)
#				parser.parse()
#				os.rename(ldifFilename, ldifFilename + ".done")
#			except ImportError:
#				debug("[FritzCallPhonebook] LDIF import failed" %line)
#===============================================================================
		
		if config.plugins.FritzCall.fritzphonebook.value:
			fritzbox.loadFritzBoxPhonebook()

		if DESKTOP_WIDTH <> 1280 or DESKTOP_HEIGHT <> 720:
			config.plugins.FritzCall.fullscreen.value = False

	def search(self, number):
		# debug("[FritzCallPhonebook] Searching for %s" %number
		name = None
		if config.plugins.FritzCall.phonebook.value or config.plugins.FritzCall.fritzphonebook.value:
			if self.phonebook.has_key(number):
				name = self.phonebook[number].replace(", ", "\n").strip()
		return name

	def add(self, number, name):
		'''
		
		@param number: number of entry
		@param name: name of entry, has to be in utf-8
		'''
		debug("[FritzCallPhonebook] add")
		name = name.replace("\n", ", ").replace('#','') # this is just for safety reasons. add should only be called with newlines converted into commas
		self.remove(number)
		self.phonebook[number] = name;
		if number and number <> 0:
			if config.plugins.FritzCall.phonebook.value:
				try:
					name = name.strip() + "\n"
					string = "%s#%s" % (number, name)
					# Beware: strings in PhoneBook.txt have to be in utf-8!
					f = open(config.plugins.FritzCall.phonebookLocation.value + "/PhoneBook.txt", 'a')
					f.write(string)
					f.close()
					debug("[FritzCallPhonebook] added %s with %s to Phonebook.txt" % (number, name.strip()))
					return True
	
				except IOError:
					return False

	def remove(self, number):
		if number in self.phonebook:
			debug("[FritzCallPhonebook] remove entry in phonebook")
			del self.phonebook[number]
			if config.plugins.FritzCall.phonebook.value:
				try:
					phonebookFilename = config.plugins.FritzCall.phonebookLocation.value + "/PhoneBook.txt"
					debug("[FritzCallPhonebook] remove entry in Phonebook.txt")
					fOld = open(phonebookFilename, 'r')
					fNew = open(phonebookFilename + str(os.getpid()), 'w')
					line = fOld.readline()
					while (line):
						if not re.match("^" + number + "#.*$", line):
							fNew.write(line)
						line = fOld.readline()
					fOld.close()
					fNew.close()
					os.remove(phonebookFilename)
					os.rename(phonebookFilename + str(os.getpid()),	phonebookFilename)
					debug("[FritzCallPhonebook] removed %s from Phonebook.txt" % number)
					return True
	
				except IOError:
					pass
		return False

	class FritzDisplayPhonebook(Screen, HelpableScreen, NumericalTextInput):
	
		def __init__(self, session):
			if config.plugins.FritzCall.fullscreen.value:
				self.width = DESKTOP_WIDTH
				self.height = DESKTOP_HEIGHT
				backMainPng = ""
				if os.path.exists(resolveFilename(SCOPE_SKIN_IMAGE, DESKTOP_SKIN + "/menu/back-main.png")):
					backMainPng = DESKTOP_SKIN + "/menu/back-main.png"
				elif os.path.exists(resolveFilename(SCOPE_SKIN_IMAGE, "Kerni-HD1/menu/back-main.png")):
					backMainPng = "Kerni-HD1/menu/back-main.png"
				elif os.path.exists(resolveFilename(SCOPE_SKIN_IMAGE, "Kerni-HD1-picon/menu/back-main.png")):
					backMainPng = "Kerni-HD1-picon/menu/back-main.png"
				if backMainPng:
					backMainLine = """<ePixmap position="0,0" zPosition="-10" size="%d,%d" pixmap="%s" transparent="1" />""" % (self.width, self.height, backMainPng)
				else:
					backMainLine = ""
				debug("[FritzDisplayPhonebook] backMainLine: " + backMainLine)
					
				# TRANSLATORS: this is a window title. Avoid the use of non ascii chars
				self.skin = """
					<screen name="FritzdisplayPhonebook" position="0,0" size="%d,%d" title="%s" flags="wfNoBorder">
						%s
						<widget source="global.CurrentTime" render="Label" position="%d,%d" size="%d,%d" font="Regular;%d" halign="right" backgroundColor="#0b67a2" transparent="1">
							<convert type="ClockToText">Default</convert>
						</widget>
						<widget source="global.CurrentTime" render="Label" position="%d,%d" size="%d,%d" font="Regular;%d" halign="right" backgroundColor="#0b67a2" transparent="1">
							<convert type="ClockToText">Date</convert>
						</widget>
						<eLabel text="%s" position="%d,%d" size="%d,%d" font="Regular;%d" halign="center" backgroundColor="#0b67a2" transparent="1"/>
				
						<widget name="entries" position="%d,%d" size="%d,%d" scrollbarMode="showOnDemand" transparent="1" />
				
						<ePixmap pixmap="skin_default/buttons/red.png" 		position="%d,%d" 	size="%d,%d" alphatest="on" />
						<ePixmap pixmap="skin_default/buttons/green.png" 	position="%d,%d" 	size="%d,%d" alphatest="on" />
						<ePixmap pixmap="skin_default/buttons/yellow.png" 	position="%d,%d" 	size="%d,%d" alphatest="on" />
						<ePixmap pixmap="skin_default/buttons/blue.png" 	position="%d,%d" 	size="%d,%d" alphatest="on" />
						<widget name="key_red" 	position="%d,%d" 	size="%d,%d" zPosition="1" font="Regular;%d" halign="left" backgroundColor="black" transparent="1" />
						<widget name="key_green" 	position="%d,%d" 	size="%d,%d" zPosition="1" font="Regular;%d" halign="left" backgroundColor="black" transparent="1" />
						<widget name="key_yellow" 	position="%d,%d" 	size="%d,%d" zPosition="1" font="Regular;%d" halign="left" backgroundColor="black" transparent="1" />
						<widget name="key_blue" 	position="%d,%d" 	size="%d,%d" zPosition="1" font="Regular;%d" halign="left" backgroundColor="black" transparent="1" />
						<ePixmap position="%d,%d" size="%d,%d" zPosition="2" pixmap="%s" transparent="1" alphatest="blend" />	
					</screen>""" % (
									self.width, self.height, _("Phonebook"),
									backMainLine,
									scaleH(1130, XXX), scaleV(40, XXX), scaleH(80, XXX), scaleV(26, XXX), scaleV(26, XXX), # time
									scaleH(900, XXX), scaleV(70, XXX), scaleH(310, XXX), scaleV(22, XXX), scaleV(20, XXX), # date
									"FritzCall " + _("Phonebook"), scaleH(80, XXX), scaleV(63, XXX), scaleH(300, XXX), scaleV(30, XXX), scaleV(27, XXX), # eLabel
									scaleH(420, XXX), scaleV(120, XXX), scaleH(790, XXX), scaleV(438, XXX), # entries
									scaleH(450, XXX), scaleV(588, XXX), scaleH(21, XXX), scaleV(21, XXX), # red
									scaleH(640, XXX), scaleV(588, XXX), scaleH(21, XXX), scaleV(21, XXX), # green
									scaleH(830, XXX), scaleV(588, XXX), scaleH(21, XXX), scaleV(21, XXX), # yellow
									scaleH(1020, XXX), scaleV(588, XXX), scaleH(21, XXX), scaleV(21, XXX), # blue
									scaleH(480, XXX), scaleV(587, XXX), scaleH(160, XXX), scaleV(22, XXX), scaleV(20, XXX), # red
									scaleH(670, XXX), scaleV(587, XXX), scaleH(160, XXX), scaleV(22, XXX), scaleV(20, XXX), # green
									scaleH(860, XXX), scaleV(587, XXX), scaleH(160, XXX), scaleV(22, XXX), scaleV(20, XXX), # yellow
									scaleH(1050, XXX), scaleV(587, XXX), scaleH(160, XXX), scaleV(22, XXX), scaleV(20, XXX), # blue
									scaleH(120, XXX), scaleV(430, XXX), scaleH(150, XXX), scaleV(110, XXX), resolveFilename(SCOPE_PLUGINS, "Extensions/FritzCall/images/fritz.png") # Fritz Logo size and pixmap
																)
			else:
				self.width = scaleH(1100, 570)
				debug("[FritzDisplayPhonebook] width: " + str(self.width))
				# TRANSLATORS: this is a window title. Avoid the use of non ascii chars
				self.skin = """
					<screen name="FritzDisplayPhonebook" position="%d,%d" size="%d,%d" title="%s" >
						<eLabel position="0,0" size="%d,2" backgroundColor="#aaaaaa" />
						<widget name="entries" position="%d,%d" size="%d,%d" scrollbarMode="showOnDemand" />
						<eLabel position="0,%d" size="%d,2" backgroundColor="#aaaaaa" />
						<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
						<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
						<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
						<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
						<widget name="key_red" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
						<widget name="key_green" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
						<widget name="key_yellow" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
						<widget name="key_blue" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
					</screen>""" % (
							scaleH(90, 75), scaleV(100, 73), # position 
							scaleH(1100, 570), scaleV(560, 430), # size
							_("Phonebook"),
							scaleH(1100, 570), # eLabel width
							scaleH(40, 5), scaleV(20, 5), # entries position
							scaleH(1040, 560), scaleV(488, 380), # entries size
							scaleV(518, 390), # eLabel position vertical
							scaleH(1100, 570), # eLabel width
							scaleH(20, 5), scaleV(525, 395), # ePixmap red
							scaleH(290, 145), scaleV(525, 395), # ePixmap green
							scaleH(560, 285), scaleV(525, 395), # ePixmap yellow
							scaleH(830, 425), scaleV(525, 395), # ePixmap blue
							scaleH(20, 5), scaleV(525, 395), scaleV(22, 21), # widget red
							scaleH(290, 145), scaleV(525, 395), scaleV(22, 21), # widget green
							scaleH(560, 285), scaleV(525, 395), scaleV(22, 21), # widget yellow
							scaleH(830, 425), scaleV(525, 395), scaleV(22, 21), # widget blue
							)
	
			Screen.__init__(self, session)
			NumericalTextInput.__init__(self)
			HelpableScreen.__init__(self)
		
			# TRANSLATORS: keep it short, this is a button
			self["key_red"] = Button(_("Delete"))
			# TRANSLATORS: keep it short, this is a button
			self["key_green"] = Button(_("New"))
			# TRANSLATORS: keep it short, this is a button
			self["key_yellow"] = Button(_("Edit"))
			# TRANSLATORS: keep it short, this is a button
			self["key_blue"] = Button(_("Search"))
	
			self["setupActions"] = ActionMap(["OkCancelActions", "ColorActions"],
			{
				"red": self.delete,
				"green": self.add,
				"yellow": self.edit,
				"blue": self.search,
				"cancel": self.exit,
				"ok": self.showEntry, }, - 2)
	
			# TRANSLATORS: keep it short, this is a help text
			self.helpList.append((self["setupActions"], "OkCancelActions", [("ok", _("Show details of entry"))]))
			# TRANSLATORS: keep it short, this is a help text
			self.helpList.append((self["setupActions"], "OkCancelActions", [("cancel", _("Quit"))]))
			# TRANSLATORS: keep it short, this is a help text
			self.helpList.append((self["setupActions"], "ColorActions", [("red", _("Delete entry"))]))
			# TRANSLATORS: keep it short, this is a help text
			self.helpList.append((self["setupActions"], "ColorActions", [("green", _("Add entry to phonebook"))]))
			# TRANSLATORS: keep it short, this is a help text
			self.helpList.append((self["setupActions"], "ColorActions", [("yellow", _("Edit selected entry"))]))
			# TRANSLATORS: keep it short, this is a help text
			self.helpList.append((self["setupActions"], "ColorActions", [("blue", _("Search (case insensitive)"))]))
	
			self["entries"] = MenuList([], True, content=eListboxPythonMultiContent)
			fontSize = scaleV(22, 18)
			fontHeight = scaleV(24, 20)
			self["entries"].l.setFont(0, gFont("Regular", fontSize))
			self["entries"].l.setItemHeight(fontHeight)
			debug("[FritzCallPhonebook] displayPhonebook init")
			self.display()
	
		def display(self, filter=""):
			debug("[FritzCallPhonebook] displayPhonebook/display")
			self.sortlist = []
			# Beware: strings in phonebook.phonebook are utf-8!
			sortlistHelp = sorted((name.lower(), name, number) for (number, name) in phonebook.phonebook.iteritems())
			for (low, name, number) in sortlistHelp:
				if number == "01234567890":
					continue
				try:
					low = low.decode("utf-8")
				except (UnicodeDecodeError, UnicodeEncodeError):  # this should definitely not happen
					try:
						low = low.decode("iso-8859-1")
					except:
						debug("[FritzCallPhonebook] displayPhonebook/display: corrupt phonebook entry for %s" % number)
						# self.session.open(MessageBox, _("Corrupt phonebook entry\nfor number %s\nDeleting.") %number, type = MessageBox.TYPE_ERROR)
						phonebook.remove(number)
						continue
				else:
					if filter:
						filter = filter.lower()
						if low.find(filter) == - 1:
							continue
					name = name.strip().decode("utf-8")
					number = number.strip().decode("utf-8")
					found = re.match("([^,]*),.*", name)   # strip address information from the name part
					if found:
						shortname = found.group(1)
					else:
						shortname = name
					numberFieldWidth = scaleV(200,150)
					fieldWidth = self.width -5 -numberFieldWidth -10 -scaleH(90,45)
					number = number.encode("utf-8", "replace")
					name = name.encode("utf-8", "replace")
					shortname = shortname.encode('utf-8', 'replace')
					self.sortlist.append([(number,
								   name),
								   (eListboxPythonMultiContent.TYPE_TEXT, 0, 0, fieldWidth, scaleH(24,20), 0, RT_HALIGN_LEFT, shortname),
								   (eListboxPythonMultiContent.TYPE_TEXT, fieldWidth +5, 0, numberFieldWidth, scaleH(24,20), 0, RT_HALIGN_LEFT, number)
								   ])
				
			self["entries"].setList(self.sortlist)
	
		def showEntry(self):
			cur = self["entries"].getCurrent()
			if cur and cur[0]:
				debug("[FritzCallPhonebook] displayPhonebook/showEntry (%s,%s)" % (cur[0][0], cur[0][1]))
				number = cur[0][0]
				name = cur[0][1]
				self.session.open(FritzOfferAction, self, number, name)
	
		def delete(self):
			cur = self["entries"].getCurrent()
			if cur and cur[0]:
				debug("[FritzCallPhonebook] displayPhonebook/delete " + cur[0][0])
				self.session.openWithCallback(
					self.deleteConfirmed,
					MessageBox,
					_("Do you really want to delete entry for\n\n%(number)s\n\n%(name)s?") 
					% { 'number':str(cur[0][0]), 'name':str(cur[0][1]).replace(", ", "\n") }
								)
			else:
				self.session.open(MessageBox, _("No entry selected"), MessageBox.TYPE_INFO)
	
		def deleteConfirmed(self, ret):
			debug("[FritzCallPhonebook] displayPhonebook/deleteConfirmed")
			#
			# if ret: delete number from sortlist, delete number from phonebook.phonebook and write it to disk
			#
			cur = self["entries"].getCurrent()
			if cur:
				if ret:
					# delete number from sortlist, delete number from phonebook.phonebook and write it to disk
					debug("[FritzCallPhonebook] displayPhonebook/deleteConfirmed: remove " + cur[0][0])
					phonebook.remove(cur[0][0])
					self.display()
				# else:
					# self.session.open(MessageBox, _("Not deleted."), MessageBox.TYPE_INFO)
			else:
				self.session.open(MessageBox, _("No entry selected"), MessageBox.TYPE_INFO)
	
		def add(self, parent=None, number="", name=""):
			class addScreen(Screen, ConfigListScreen):
				'''ConfiglistScreen with two ConfigTexts for Name and Number'''
	
				def __init__(self, session, parent, number="", name=""):
					#
					# setup screen with two ConfigText and OK and ABORT button
					# 
					noButtons = 2
					width = max(scaleH(-1,570), noButtons*140)
					height = scaleV(-1,100) # = 5 + 126 + 40 + 5; 6 lines of text possible
					buttonsGap = (width-noButtons*140)/(noButtons+1)
					buttonsVPos = height-40-5
					# TRANSLATORS: this is a window title. Avoid the use of non ascii chars
					self.skin = """
						<screen position="%d,%d" size="%d,%d" title="%s" >
						<widget name="config" position="5,5" size="%d,%d" scrollbarMode="showOnDemand" />
						<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
						<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
						<widget name="key_red" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
						<widget name="key_green" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
						</screen>""" % (
										(DESKTOP_WIDTH - width) / 2,
										(DESKTOP_HEIGHT - height) / 2,
										width,
										height,
										_("Add entry to phonebook"),
										width - 5 - 5,
										height - 5 - 40 - 5,
										buttonsGap, buttonsVPos,
										buttonsGap+140+buttonsGap, buttonsVPos,
										buttonsGap, buttonsVPos,
										buttonsGap+140+buttonsGap, buttonsVPos,
										)
					Screen.__init__(self, session)
					self.session = session
					self.parent = parent
					# TRANSLATORS: keep it short, this is a button
					self["key_red"] = Button(_("Cancel"))
					# TRANSLATORS: keep it short, this is a button
					self["key_green"] = Button(_("OK"))
					self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
					{
						"cancel": self.cancel,
						"red": self.cancel,
						"green": self.add,
						"ok": self.add,
					}, - 2)
	
					self.list = [ ]
					ConfigListScreen.__init__(self, self.list, session=session)
					config.plugins.FritzCall.name.value = name
					config.plugins.FritzCall.number.value = number
					self.list.append(getConfigListEntry(_("Name"), config.plugins.FritzCall.name))
					self.list.append(getConfigListEntry(_("Number"), config.plugins.FritzCall.number))
					self["config"].list = self.list
					self["config"].l.setList(self.list)
	
				def add(self):
					# get texts from Screen
					# add (number,name) to sortlist and phonebook.phonebook and disk
					self.number = config.plugins.FritzCall.number.value
					self.name = config.plugins.FritzCall.name.value
					if not self.number or not self.name:
						self.session.open(MessageBox, _("Entry incomplete."), type=MessageBox.TYPE_ERROR)
						return
					# add (number,name) to sortlist and phonebook.phonebook and disk
	#					oldname = phonebook.search(self.number)
	#					if oldname:
	#						self.session.openWithCallback(
	#							self.overwriteConfirmed,
	#							MessageBox,
	#							_("Do you really want to overwrite entry for %(number)s\n\n%(name)s\n\nwith\n\n%(newname)s?")
	#							% {
	#							'number':self.number,
	#							'name': oldname,
	#							'newname':self.name.replace(", ","\n")
	#							}
	#							)
	#						self.close()
	#						return
					phonebook.add(self.number, self.name)
					self.close()
					self.parent.display()
	
				def overwriteConfirmed(self, ret):
					if ret:
						phonebook.remove(self.number)
						phonebook.add(self.number, self.name)
						self.parent.display()
	
				def cancel(self):
					self.close()
	
			debug("[FritzCallPhonebook] displayPhonebook/add")
			if not parent:
				parent = self
			self.session.open(addScreen, parent, number, name)
	
		def edit(self):
			debug("[FritzCallPhonebook] displayPhonebook/edit")
			cur = self["entries"].getCurrent()
			if cur is None:
				self.session.open(MessageBox, _("No entry selected"), MessageBox.TYPE_INFO)
			else:
				(number, name) = cur[0]
				self.add(self, number, name)
	
		def search(self):
			debug("[FritzCallPhonebook] displayPhonebook/search")
			self.help_window = self.session.instantiateDialog(NumericalTextInputHelpDialog, self)
			self.help_window.show()
			self.session.openWithCallback(self.doSearch, InputBox, _("Enter Search Terms"), _("Search phonebook"))
	
		def doSearch(self, searchTerms):
			if not searchTerms: searchTerms = ""
			debug("[FritzCallPhonebook] displayPhonebook/doSearch: " + searchTerms)
			if self.help_window:
				self.session.deleteDialog(self.help_window)
				self.help_window = None
			self.display(searchTerms)
	
		def exit(self):
			self.close()

phonebook = FritzCallPhonebook()

class FritzCallSetup(Screen, ConfigListScreen, HelpableScreen):

	def __init__(self, session, args=None):
		if config.plugins.FritzCall.fullscreen.value:
			self.width = DESKTOP_WIDTH
			self.height = DESKTOP_HEIGHT
			backMainPng = ""
			backMainLine = ""
			if os.path.exists(resolveFilename(SCOPE_SKIN_IMAGE, DESKTOP_SKIN + "/menu/back-main.png")):
				backMainPng = DESKTOP_SKIN + "/menu/back-main.png"
			elif os.path.exists(resolveFilename(SCOPE_SKIN_IMAGE, "Kerni-HD1/menu/back-main.png")):
				backMainPng = "Kerni-HD1/menu/back-main.png"
			elif os.path.exists(resolveFilename(SCOPE_SKIN_IMAGE, "Kerni-HD1-picon/menu/back-main.png")):
				backMainPng = "Kerni-HD1-picon/menu/back-main.png"
			if backMainPng:
				backMainLine = """<ePixmap position="0,0" zPosition="-10" size="%d,%d" pixmap="%s" transparent="1" />""" % (self.width, self.height, backMainPng)
			else:
				backMainLine = ""
			debug("[FritzCallSetup] backMainLine: " + backMainLine)
			# TRANSLATORS: this is a window title. Avoid the use of non ascii chars
			self.skin = """
				<screen name="FritzCallSetup" position="0,0" size="%d,%d" title="%s" flags="wfNoBorder">
					%s
					<widget source="global.CurrentTime" render="Label" position="%d,%d" size="%d,%d" font="Regular;%d" halign="right" backgroundColor="#0b67a2" transparent="1">
						<convert type="ClockToText">Default</convert>
					</widget>
					<widget source="global.CurrentTime" render="Label" position="%d,%d" size="%d,%d" font="Regular;%d" halign="right" backgroundColor="#0b67a2" transparent="1">
						<convert type="ClockToText">Date</convert>
					</widget>
					<eLabel text="%s" position="%d,%d" size="%d,%d" font="Regular;%d" halign="center" backgroundColor="#0b67a2" transparent="1"/>
			
					<widget name="consideration" position="%d,%d"  size="%d,%d" font="Regular;%d" halign="center" backgroundColor="#353e575e" transparent="1" />
					<widget name="config" position="%d,%d" size="%d,%d" scrollbarMode="showOnDemand" transparent="1" />
			
					<ePixmap pixmap="skin_default/buttons/red.png" 		position="%d,%d" 	size="%d,%d" alphatest="on" />
					<ePixmap pixmap="skin_default/buttons/green.png" 	position="%d,%d" 	size="%d,%d" alphatest="on" />
					<ePixmap pixmap="skin_default/buttons/yellow.png" 	position="%d,%d" 	size="%d,%d" alphatest="on" />
					<ePixmap pixmap="skin_default/buttons/blue.png" 	position="%d,%d" 	size="%d,%d" alphatest="on" />
					<ePixmap pixmap="skin_default/buttons/key_info.png" 	position="%d,%d" 	size="%d,%d" alphatest="on" />
					<ePixmap pixmap="skin_default/buttons/key_menu.png" 	position="%d,%d" 	size="%d,%d" alphatest="on" />
					<widget name="key_red" position="%d,%d" 		size="%d,%d" zPosition="1" font="Regular;%d" halign="left" backgroundColor="black" transparent="1" />
					<widget name="key_green"  position="%d,%d" 	size="%d,%d" zPosition="1" font="Regular;%d" halign="left" backgroundColor="black" transparent="1" />
					<widget name="key_yellow" position="%d,%d" 	size="%d,%d" zPosition="1" font="Regular;%d" halign="left" backgroundColor="black" transparent="1" />
					<widget name="key_blue" position="%d,%d" 	size="%d,%d" zPosition="1" font="Regular;%d" halign="left" backgroundColor="black" transparent="1" />
					<ePixmap position="%d,%d" size="%d,%d" zPosition="2" pixmap="%s" transparent="1" alphatest="blend" />		
				</screen>""" % (
								self.width, self.height, _("FritzCall Setup"),
								backMainLine,
								scaleH(1130, XXX), scaleV(40, XXX), scaleH(80, XXX), scaleV(26, XXX), scaleV(26, XXX), # time
								scaleH(900, XXX), scaleV(70, XXX), scaleH(310, XXX), scaleV(22, XXX), scaleV(20, XXX), # date
								_("FritzCall Setup"), scaleH(500, XXX), scaleV(63, XXX), scaleH(330, XXX), scaleV(30, XXX), scaleV(27, XXX), # eLabel
								scaleH(80, XXX), scaleV(150, XXX), scaleH(250, XXX), scaleV(200, XXX), scaleV(22, XXX), # consideration
								scaleH(420, XXX), scaleV(125, XXX), scaleH(790, XXX), scaleV(428, XXX), # config
								scaleH(150, XXX), scaleV(588, XXX), scaleH(21, XXX), scaleV(21, XXX), # red
								scaleH(350, XXX), scaleV(588, XXX), scaleH(21, XXX), scaleV(21, XXX), # green
								scaleH(550, XXX), scaleV(588, XXX), scaleH(21, XXX), scaleV(21, XXX), # yellow
								scaleH(750, XXX), scaleV(588, XXX), scaleH(21, XXX), scaleV(21, XXX), # blue
								scaleH(1050, XXX), scaleV(586, XXX), scaleH(35, XXX), scaleV(24, XXX), # info
								scaleH(1150, XXX), scaleV(586, XXX), scaleH(35, XXX), scaleV(24, XXX), # menu
								scaleH(175, XXX), scaleV(587, XXX), scaleH(160, XXX), scaleV(22, XXX), scaleV(20, XXX), # red
								scaleH(375, XXX), scaleV(587, XXX), scaleH(160, XXX), scaleV(22, XXX), scaleV(20, XXX), # green
								scaleH(575, XXX), scaleV(587, XXX), scaleH(160, XXX), scaleV(22, XXX), scaleV(20, XXX), # yellow
								scaleH(775, XXX), scaleV(587, XXX), scaleH(160, XXX), scaleV(22, XXX), scaleV(20, XXX), # blue
								scaleH(120, XXX), scaleV(430, XXX), scaleH(150, XXX), scaleV(110, XXX), resolveFilename(SCOPE_PLUGINS, "Extensions/FritzCall/images/fritz.png") # Fritz Logo size and pixmap
																) 
		else:
			self.width = scaleH(20+4*(140+90)+2*(35+40)+20, 4*140+2*35)
			width = self.width
			debug("[FritzCallSetup] width: " + str(self.width))
			# TRANSLATORS: this is a window title. Avoid the use of non ascii chars
			self.skin = """
				<screen name="FritzCallSetup" position="%d,%d" size="%d,%d" title="%s" >
				<eLabel position="0,0" size="%d,2" backgroundColor="#aaaaaa" />
				<widget name="consideration" position="%d,%d" halign="center" size="%d,%d" font="Regular;%d" backgroundColor="#20040404" transparent="1" />
				<eLabel position="0,%d" size="%d,2" backgroundColor="#aaaaaa" />
				<widget name="config" position="%d,%d" size="%d,%d" scrollbarMode="showOnDemand" backgroundColor="#20040404" transparent="1" />
				<eLabel position="0,%d" size="%d,2" backgroundColor="#aaaaaa" />
				<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
				<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
				<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
				<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
				<widget name="key_red" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_green" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_yellow" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_blue" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<ePixmap position="%d,%d" zPosition="4" size="35,25" pixmap="skin_default/buttons/key_info.png" transparent="1" alphatest="on" />
				<ePixmap position="%d,%d" zPosition="4" size="35,25" pixmap="skin_default/buttons/key_menu.png" transparent="1" alphatest="on" />
				</screen>""" % (
							(DESKTOP_WIDTH-width)/2, scaleV(100, 73), # position 
							width, scaleV(560, 430), # size
							_("FritzCall Setup") + 
							" (" + "$Revision$"[1: - 1] + 
							"$Date$"[7:23] + ")",
							width, # eLabel width
							scaleH(40, 20), scaleV(10, 5), # consideration position
							scaleH(width-80, width-40), scaleV(25, 45), # consideration size
							scaleV(22, 20), # consideration font size
							scaleV(40, 50), # eLabel position vertical
							width, # eLabel width
							scaleH(40, 5), scaleV(60, 57), # config position
							scaleH(width-80, width-10), scaleV(453, 328), # config size
							scaleV(518, 390), # eLabel position vertical
							width, # eLabel width
							scaleH(20, 0), scaleV(525, 395), # pixmap red
							scaleH(20+140+90, 140), scaleV(525, 395), # pixmap green
							scaleH(20+2*(140+90), 2*140), scaleV(525, 395), # pixmap yellow
							scaleH(20+3*(140+90), 3*140), scaleV(525, 395), # pixmap blue
							scaleH(20, 0), scaleV(525, 395), scaleV(21, 21), # pixmap red
							scaleH(20+(140+90), 140), scaleV(525, 395), scaleV(21, 21), # widget green
							scaleH(20+2*(140+90), 2*140), scaleV(525, 395), scaleV(21, 21), # widget yellow
							scaleH(20+3*(140+90), 3*140), scaleV(525, 395), scaleV(21, 21), # widget blue
							scaleH(20+4*(140+90), 4*140), scaleV(532, 402), # button info
							scaleH(20+4*(140+90)+(35+40), 4*140+35), scaleV(532, 402) # button menu
														)

		Screen.__init__(self, session)
		HelpableScreen.__init__(self)
		self.session = session

		self["consideration"] = Label(_("You need to enable the monitoring on your FRITZ!Box by dialing #96*5*!"))
		self.list = []

		# Initialize Buttons
		# TRANSLATORS: keep it short, this is a button
		self["key_red"] = Button(_("Cancel"))
		# TRANSLATORS: keep it short, this is a button
		self["key_green"] = Button(_("OK"))
		# TRANSLATORS: keep it short, this is a button
		self["key_yellow"] = Button(_("Phone calls"))
		# TRANSLATORS: keep it short, this is a button
		self["key_blue"] = Button(_("Phonebook"))
		# TRANSLATORS: keep it short, this is a button
		self["key_info"] = Button(_("About FritzCall"))
		# TRANSLATORS: keep it short, this is a button
		self["key_menu"] = Button(_("FRITZ!Box Fon Status"))

		self["setupActions"] = ActionMap(["ColorActions", "OkCancelActions", "MenuActions", "EPGSelectActions"],
		{
			"red": self.cancel,
			"green": self.save,
			"yellow": self.displayCalls,
			"blue": self.displayPhonebook,
			"cancel": self.cancel,
			"ok": self.save,
			"menu": self.menu,
			"info": self.about,
		}, - 2)

		# TRANSLATORS: keep it short, this is a help text
		self.helpList.append((self["setupActions"], "ColorActions", [("red", _("quit"))]))
		# TRANSLATORS: keep it short, this is a help text
		self.helpList.append((self["setupActions"], "ColorActions", [("green", _("save and quit"))]))
		# TRANSLATORS: keep it short, this is a help text
		self.helpList.append((self["setupActions"], "ColorActions", [("yellow", _("display calls"))]))
		# TRANSLATORS: keep it short, this is a help text
		self.helpList.append((self["setupActions"], "ColorActions", [("blue", _("display phonebook"))]))
		# TRANSLATORS: keep it short, this is a help text
		self.helpList.append((self["setupActions"], "OkCancelActions", [("ok", _("save and quit"))]))
		# TRANSLATORS: keep it short, this is a help text
		self.helpList.append((self["setupActions"], "OkCancelActions", [("cancel", _("quit"))]))
		# TRANSLATORS: keep it short, this is a help text
		self.helpList.append((self["setupActions"], "MenuActions", [("menu", _("FRITZ!Box Fon Status"))]))
		# TRANSLATORS: keep it short, this is a help text
		self.helpList.append((self["setupActions"], "EPGSelectActions", [("info", _("About FritzCall"))]))

		ConfigListScreen.__init__(self, self.list, session=session)
		self.createSetup()


	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.createSetup()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.createSetup()

	def createSetup(self):
		self.list = [ ]
		self.list.append(getConfigListEntry(_("Call monitoring"), config.plugins.FritzCall.enable))
		if config.plugins.FritzCall.enable.value:
			self.list.append(getConfigListEntry(_("Mute on call"), config.plugins.FritzCall.muteOnCall))
			self.list.append(getConfigListEntry(_("FRITZ!Box FON address (Name or IP)"), config.plugins.FritzCall.hostname))

			self.list.append(getConfigListEntry(_("Show after Standby"), config.plugins.FritzCall.afterStandby))

			self.list.append(getConfigListEntry(_("Show Calls for specific MSN"), config.plugins.FritzCall.filter))
			if config.plugins.FritzCall.filter.value:
				self.list.append(getConfigListEntry(_("MSN to show (separated by ,)"), config.plugins.FritzCall.filtermsn))

			self.list.append(getConfigListEntry(_("Show Outgoing Calls"), config.plugins.FritzCall.showOutgoing))
			if config.plugins.FritzCall.showOutgoing.value:
				self.list.append(getConfigListEntry(_("Areacode to add to Outgoing Calls (if necessary)"), config.plugins.FritzCall.prefix))
			self.list.append(getConfigListEntry(_("Timeout for Call Notifications (seconds)"), config.plugins.FritzCall.timeout))
			self.list.append(getConfigListEntry(_("Reverse Lookup Caller ID (select country below)"), config.plugins.FritzCall.lookup))
			if config.plugins.FritzCall.lookup.value:
				self.list.append(getConfigListEntry(_("Country"), config.plugins.FritzCall.country))

			self.list.append(getConfigListEntry(_("Password Accessing FRITZ!Box"), config.plugins.FritzCall.password))
			self.list.append(getConfigListEntry(_("Extension number to initiate call on"), config.plugins.FritzCall.extension))
			self.list.append(getConfigListEntry(_("Read PhoneBook from FRITZ!Box"), config.plugins.FritzCall.fritzphonebook))
			if config.plugins.FritzCall.fritzphonebook.value:
				self.list.append(getConfigListEntry(_("Append type of number"), config.plugins.FritzCall.showType))
				self.list.append(getConfigListEntry(_("Append shortcut number"), config.plugins.FritzCall.showShortcut))
				self.list.append(getConfigListEntry(_("Append vanity name"), config.plugins.FritzCall.showVanity))

			self.list.append(getConfigListEntry(_("Use internal PhoneBook"), config.plugins.FritzCall.phonebook))
			if config.plugins.FritzCall.phonebook.value:
				self.list.append(getConfigListEntry(_("PhoneBook Location"), config.plugins.FritzCall.phonebookLocation))
				if config.plugins.FritzCall.lookup.value:
					self.list.append(getConfigListEntry(_("Automatically add new Caller to PhoneBook"), config.plugins.FritzCall.addcallers))

			self.list.append(getConfigListEntry(_("Strip Leading 0"), config.plugins.FritzCall.internal))
			# self.list.append(getConfigListEntry(_("Default display mode for FRITZ!Box calls"), config.plugins.FritzCall.fbfCalls))
			if DESKTOP_WIDTH == 1280 and DESKTOP_HEIGHT == 720:
				self.list.append(getConfigListEntry(_("Full screen display"), config.plugins.FritzCall.fullscreen))
			self.list.append(getConfigListEntry(_("Debug"), config.plugins.FritzCall.debug))

		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def save(self):
#		debug("[FritzCallSetup] save"
		for x in self["config"].list:
			x[1].save()
		if fritz_call:
			fritz_call.connect()
		self.close()

	def cancel(self):
#		debug("[FritzCallSetup] cancel"
		for x in self["config"].list:
			x[1].cancel()
		self.close()

	def displayCalls(self):
		self.session.open(FritzDisplayCalls)

	def displayPhonebook(self):
		self.session.open(phonebook.FritzDisplayPhonebook)

	def about(self):
		self.session.open(FritzAbout)

	def menu(self):
		self.session.open(FritzMenu)

standbyMode = False

class FritzCallList:
	def __init__(self):
		self.callList = [ ]
	
	def add(self, event, date, number, caller, phone):
		debug("[FritzCallList] add")
		if len(self.callList) > 10:
			if self.callList[0] != "Start":
				self.callList[0] = "Start"
			del self.callList[1]

		self.callList.append((event, number, date, caller, phone))
	
	def display(self):
		debug("[FritzCallList] display")
		global standbyMode
		global my_global_session
		standbyMode = False
		# Standby.inStandby.onClose.remove(self.display) object does not exist anymore...
		# build screen from call list
		text = "\n"
		if self.callList[0] == "Start":
			text = text + _("Last 10 calls:\n")
			del self.callList[0]

		for call in self.callList:
			(event, number, date, caller, phone) = call
			if event == "RING":
				direction = "->"
			else:
				direction = "<-"

			# shorten the date info
			found = re.match(".*(\d\d.\d\d.)\d\d( \d\d:\d\d)", date)
			if found: date = found.group(1) + found.group(2)

			# our phone could be of the form "0123456789 (home)", then we only take "home"
			found = re.match(".*\((.*)\)", phone)
			if found: phone = found.group(1)

			#  if we have an unknown number, show the number
			if caller == _("UNKNOWN") and number != "":
				caller = number
			else:
				# strip off the address part of the remote number, if there is any
				found = re.match("(.*)\n.*", caller)
				if found: caller = found.group(1)

			while (len(caller) + len(phone)) > 40:
				if len(caller) > len(phone):
					caller = caller[: - 1]
				else:
					phone = phone[: - 1]

			text = text + "%s %s %s %s\n" % (date, caller, direction, phone)

		debug("[FritzCallList] display: '%s %s %s %s'" % (date, caller, direction, phone))
		# display screen
		Notifications.AddNotification(MessageBox, text, type=MessageBox.TYPE_INFO)
		# my_global_session.open(FritzDisplayCalls, text) # TODO please HELP: from where can I get a session?
		self.callList = [ ]
		self.text = ""

callList = FritzCallList()

from GlobalActions import globalActionMap
def notifyCall(event, date, number, caller, phone):
	if Standby.inStandby is None or config.plugins.FritzCall.afterStandby.value == "each":
		if config.plugins.FritzCall.muteOnCall.value:
			globalActionMap.actions["volumeMute"]()
		if event == "RING":
			text = _("Incoming Call on %(date)s from\n---------------------------------------------\n%(number)s\n%(caller)s\n---------------------------------------------\nto: %(phone)s") % { 'date':date, 'number':number, 'caller':caller, 'phone':phone }
		else:
			text = _("Outgoing Call on %(date)s to\n---------------------------------------------\n%(number)s\n%(caller)s\n---------------------------------------------\nfrom: %(phone)s") % { 'date':date, 'number':number, 'caller':caller, 'phone':phone }
		debug("[FritzCall] notifyCall:\n%s" % text)
		Notifications.AddNotification(MessageBox, text, type=MessageBox.TYPE_INFO, timeout=config.plugins.FritzCall.timeout.value)
	elif config.plugins.FritzCall.afterStandby.value == "inList":
		#
		# if not yet done, register function to show call list
		global standbyMode
		if not standbyMode :
			standbyMode = True
			Standby.inStandby.onHide.append(callList.display) #@UndefinedVariable
		# add text/timeout to call list
		callList.add(event, date, number, caller, phone)
		debug("[FritzCall] notifyCall: added to callList")
	else: # this is the "None" case
		debug("[FritzCall] notifyCall: standby and no show")


#===============================================================================
#		We need a separate class for each invocation of reverseLookup to retain
#		the necessary data for the notification
#===============================================================================

countries = { }
reverselookupMtime = 0

class FritzReverseLookupAndNotifier:
	def __init__(self, event, number, caller, phone, date):
		'''
		
		Initiate a reverse lookup for the given number in the configured country
		
		@param event: CALL or RING
		@param number: number to be looked up
		@param caller: caller including name and address
		@param phone: Number (and name) of or own phone
		@param date: date of call
		'''
		debug("[FritzReverseLookupAndNotifier] reverse Lookup for %s!" % number)
		self.event = event
		self.number = number
		self.caller = caller
		self.phone = phone
		self.date = date

		if number[0] != "0":
			self.notifyAndReset(number, caller)
			return

		ReverseLookupAndNotifier(number, self.notifyAndReset, "UTF-8", config.plugins.FritzCall.country.value)

	def notifyAndReset(self, number, caller):
		'''
		
		this gets called with the result of the reverse lookup
		
		@param number: number
		@param caller: name and address of remote. it comes in with name, address and city separated by commas
		'''
		debug("[FritzReverseLookupAndNotifier] got: " + caller)
#===============================================================================
#		if not caller and os.path.exists(config.plugins.FritzCall.phonebookLocation.value + "/PhoneBook.csv"):
#			caller = FritzOutlookCSV.findNumber(number, config.plugins.FritzCall.phonebookLocation.value + "/PhoneBook.csv") #@UndefinedVariable
#			debug("[FritzReverseLookupAndNotifier] got from Outlook csv: " + caller)
#===============================================================================
#===============================================================================
#		if not caller and os.path.exists(config.plugins.FritzCall.phonebookLocation.value + "/PhoneBook.ldif"):
#			caller = FritzLDIF.findNumber(number, open(config.plugins.FritzCall.phonebookLocation.value + "/PhoneBook.ldif"))
#			debug("[FritzReverseLookupAndNotifier] got from ldif: " + caller)
#===============================================================================

		if caller:
			self.caller = caller.replace(", ", "\n").replace('#','')
			if self.number != 0 and config.plugins.FritzCall.addcallers.value and self.event == "RING":
				debug("[FritzReverseLookupAndNotifier] add to phonebook")
				phonebook.add(self.number, self.caller)
		else:
			self.caller = _("UNKNOWN")
		notifyCall(self.event, self.date, self.number, self.caller, self.phone)
		# kill that object...

class FritzProtocol(LineReceiver):
	def __init__(self):
		debug("[FritzProtocol] " + "$Revision$"[1:-1]	+ "$Date$"[7:23] + " starting")
		self.resetValues()

	def resetValues(self):
		debug("[FritzProtocol] resetValues")
		self.number = '0'
		self.caller = None
		self.phone = None
		self.date = '0'

	def notifyAndReset(self, timeout=config.plugins.FritzCall.timeout.value):
		notifyCall(self.event, self.date, self.number, self.caller, self.phone)
		self.resetValues()

	def lineReceived(self, line):
		debug("[FritzProtocol] lineReceived: %s" % line)
#15.07.06 00:38:54;CALL;1;4;<from/extern>;<to/our msn>;
#15.07.06 00:38:58;DISCONNECT;1;0;
#15.07.06 00:39:22;RING;0;<from/extern>;<to/our msn>;
#15.07.06 00:39:27;DISCONNECT;0;0;
		a = line.split(';')
		(self.date, self.event) = a[0:2]

		if self.event == "RING" or (self.event == "CALL" and config.plugins.FritzCall.showOutgoing.value):
			phone = a[4]

			if self.event == "RING":
				number = a[3] 
			else:
				number = a[5]
				
			debug("[FritzProtocol] lineReceived phone: '''%s''' number: '''%s'''" % (phone, number))

			filtermsns = config.plugins.FritzCall.filtermsn.value.split(",")
			for i in range(len(filtermsns)):
				filtermsns[i] = filtermsns[i].strip()
			if not (config.plugins.FritzCall.filter.value and phone not in filtermsns):
				debug("[FritzProtocol] lineReceived no filter hit")
				phonename = phonebook.search(phone)		   # do we have a name for the number of our side?
				if phonename is not None:
					self.phone = "%s (%s)" % (phone, phonename)
				else:
					self.phone = phone

				if config.plugins.FritzCall.internal.value and len(number) > 3 and number[0] == "0":
					debug("[FritzProtocol] lineReceived: strip leading 0")
					self.number = number[1:]
				else:
					self.number = number
					if self.event == "CALL" and self.number[0] != '0':					  # should only happen for outgoing
						debug("[FritzProtocol] lineReceived: add local prefix")
						self.number = config.plugins.FritzCall.prefix.value + self.number

				# check, whether we are in Germany and number has call-by-call prefix. If so strip it
				if self.event == "CALL" and config.plugins.FritzCall.country.value == '0049':
					if re.match('^0100\d\d', self.number):
						debug("[FritzProtocol] lineReceived: strip CbC 0100.. prefix")
						self.number = self.number[6:]
					elif re.match('^010\d\d', self.number):
						debug("[FritzProtocol] lineReceived: strip CbC 010.. prefix")
						self.number = self.number[5:]

				if self.number is not "":
					debug("[FritzProtocol] lineReceived phonebook.search: %s" % self.number)
					self.caller = phonebook.search(self.number)
					debug("[FritzProtocol] lineReceived phonebook.search reault: %s" % self.caller)
					if (self.caller is None) and config.plugins.FritzCall.lookup.value:
						FritzReverseLookupAndNotifier(self.event, self.number, self.caller, self.phone, self.date)
						return							# reverselookup is supposed to handle the message itself 

				if self.caller is None:
					self.caller = _("UNKNOWN")

				self.notifyAndReset()

class FritzClientFactory(ReconnectingClientFactory):
	initialDelay = 20
	maxDelay = 30

	def __init__(self):
		self.hangup_ok = False

	def startedConnecting(self, connector):
		Notifications.AddNotification(MessageBox, _("Connecting to FRITZ!Box..."), type=MessageBox.TYPE_INFO, timeout=2)

	def buildProtocol(self, addr):
		global fritzbox, phonebook
		Notifications.AddNotification(MessageBox, _("Connected to FRITZ!Box!"), type=MessageBox.TYPE_INFO, timeout=4)
		self.resetDelay()
		initDebug()
		fritzbox = FritzCallFBF()
		phonebook = FritzCallPhonebook()
		return FritzProtocol()

	def clientConnectionLost(self, connector, reason):
		if not self.hangup_ok:
			Notifications.AddNotification(MessageBox, _("Connection to FRITZ!Box! lost\n (%s)\nretrying...") % reason.getErrorMessage(), type=MessageBox.TYPE_INFO, timeout=config.plugins.FritzCall.timeout.value)
		ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

	def clientConnectionFailed(self, connector, reason):
		Notifications.AddNotification(MessageBox, _("Connecting to FRITZ!Box failed\n (%s)\nretrying...") % reason.getErrorMessage(), type=MessageBox.TYPE_INFO, timeout=config.plugins.FritzCall.timeout.value)
		ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)

class FritzCall:
	def __init__(self):
		self.dialog = None
		self.d = None
		self.connect()

	def connect(self):
		self.abort()
		if config.plugins.FritzCall.enable.value:
			f = FritzClientFactory()
			self.d = (f, reactor.connectTCP(config.plugins.FritzCall.hostname.value, 1012, f)) #@UndefinedVariable

	def shutdown(self):
		self.abort()

	def abort(self):
		if self.d is not None:
			self.d[0].hangup_ok = True
			self.d[0].stopTrying()
			self.d[1].disconnect()
			self.d = None

def displayCalls(session, servicelist=None):
	session.open(FritzDisplayCalls)

def displayPhonebook(session, servicelist=None):
	session.open(phonebook.FritzDisplayPhonebook)

def displayFBFStatus(session, servicelist=None):
	session.open(FritzMenu)

def main(session):
	session.open(FritzCallSetup)

fritz_call = None

def autostart(reason, **kwargs):
	global fritz_call

	# ouch, this is a hack
	if kwargs.has_key("session"):
		global my_global_session
		my_global_session = kwargs["session"]
		return

	debug("[FRITZ!Call] - Autostart")
	if reason == 0:
		fritz_call = FritzCall()
	elif reason == 1:
		fritz_call.shutdown()
		fritz_call = None

def Plugins(**kwargs):
	what = _("Display FRITZ!box-Fon calls on screen")
	what_calls = _("Phone calls")
	what_phonebook = _("Phonebook")
	what_status = _("FRITZ!Box Fon Status")
	return [ PluginDescriptor(name="FritzCall", description=what, where=PluginDescriptor.WHERE_PLUGINMENU, icon="plugin.png", fnc=main),
		PluginDescriptor(name=what_calls, description=what_calls, where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=displayCalls),
		PluginDescriptor(name=what_phonebook, description=what_phonebook, where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=displayPhonebook),
		PluginDescriptor(name=what_status, description=what_status, where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=displayFBFStatus),
		PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc=autostart) ]
