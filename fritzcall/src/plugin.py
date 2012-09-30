# -*- coding: utf-8 -*-
'''
$Author: michael $
$Revision: 683 $
$Date: 2012-09-30 13:04:26 +0200 (Sun, 30 Sep 2012) $
$Id: plugin.py 683 2012-09-30 11:04:26Z michael $
'''
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.NumericalTextInputHelpDialog import NumericalTextInputHelpDialog
from Screens.InputBox import InputBox
from Screens import Standby
from Screens.HelpMenu import HelpableScreen

from enigma import eTimer, eSize, ePoint #@UnresolvedImport # pylint: disable=E0611
from enigma import eDVBVolumecontrol
from enigma import eBackgroundFileEraser
#BgFileEraser = eBackgroundFileEraser.getInstance()
#BgFileEraser.erase("blabla.txt")

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Button import Button
from Components.Pixmap import Pixmap
from Components.Sources.List import List
from Components.config import config, ConfigSubsection, ConfigSelection, ConfigEnableDisable, getConfigListEntry, ConfigText, ConfigInteger
from Components.ConfigList import ConfigListScreen
from Components.Harddisk import harddiskmanager
try:
	from Components.config import ConfigPassword
except ImportError:
	ConfigPassword = ConfigText

from Plugins.Plugin import PluginDescriptor
from Tools import Notifications
from Tools.NumericalTextInput import NumericalTextInput
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_SKIN_IMAGE, SCOPE_CONFIG, SCOPE_MEDIA
from Tools.LoadPixmap import LoadPixmap
from GlobalActions import globalActionMap # for muting

from twisted.internet import reactor #@UnresolvedImport
from twisted.internet.protocol import ReconnectingClientFactory #@UnresolvedImport
from twisted.protocols.basic import LineReceiver #@UnresolvedImport
from twisted.web.client import getPage #@UnresolvedImport

from urllib import urlencode 
import re, time, os, hashlib, traceback

from nrzuname import ReverseLookupAndNotifier, html2unicode
import FritzOutlookCSV, FritzLDIF
from . import _, initDebug, debug #@UnresolvedImport # pylint: disable=E0611,F0401

from enigma import getDesktop
DESKTOP_WIDTH = getDesktop(0).size().width()
DESKTOP_HEIGHT = getDesktop(0).size().height()

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
#config.plugins.FritzCall.muteOnCall = ConfigSelection(choices=[(None, _("no")), ("ring", _("on ring")), ("connect", _("on connect"))])
#config.plugins.FritzCall.muteOnCall = ConfigSelection(choices=[(None, _("no")), ("ring", _("on ring"))])
config.plugins.FritzCall.muteOnCall = ConfigEnableDisable(default=False)
config.plugins.FritzCall.hostname = ConfigText(default="fritz.box", fixed_size=False)
config.plugins.FritzCall.afterStandby = ConfigSelection(choices=[("none", _("show nothing")), ("inList", _("show as list")), ("each", _("show each call"))])
config.plugins.FritzCall.filter = ConfigEnableDisable(default=False)
config.plugins.FritzCall.filtermsn = ConfigText(default="", fixed_size=False)
config.plugins.FritzCall.filtermsn.setUseableChars('0123456789,')
config.plugins.FritzCall.filterCallList = ConfigEnableDisable(default=True)
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
config.plugins.FritzCall.connectionVerbose = ConfigEnableDisable(default=True)
config.plugins.FritzCall.ignoreUnknown = ConfigEnableDisable(default=False)
config.plugins.FritzCall.reloadPhonebookTime = ConfigInteger(default=8, limits=(0, 99))


def getMountedDevs():
	def handleMountpoint(loc):
		# debug("[FritzCall] handleMountpoint: %s" %repr(loc))
		mp = loc[0]
		while mp[-1] == '/':
			mp = mp[:-1]
		#=======================================================================
		# if os.path.exists(os.path.join(mp, "PhoneBook.txt")):
		#	if os.access(os.path.join(mp, "PhoneBook.txt"), os.W_OK):
		#		desc = ' *'
		#	else:
		#		desc = ' -'
		# else:
		#	desc = ''
		# desc = loc[1] + desc
		#=======================================================================
		desc = loc[1]
		return (mp, desc + " (" + mp + ")")

	mountedDevs = [(resolveFilename(SCOPE_CONFIG), _("Flash")),
				   (resolveFilename(SCOPE_MEDIA, "cf"), _("Compact Flash")),
				   (resolveFilename(SCOPE_MEDIA, "usb"), _("USB Device"))]
	mountedDevs += map(lambda p: (p.mountpoint, (_(p.description) if p.description else "")), harddiskmanager.getMountedPartitions(True))
	mediaDir = resolveFilename(SCOPE_MEDIA)
	for p in os.listdir(mediaDir):
		if os.path.join(mediaDir, p) not in [path[0] for path in mountedDevs]:
			mountedDevs.append((os.path.join(mediaDir, p), _("Media directory")))
	debug("[FritzCall] getMountedDevs1: %s" %repr(mountedDevs))
	mountedDevs = filter(lambda path: os.path.isdir(path[0]) and os.access(path[0], os.W_OK|os.X_OK), mountedDevs)
	# put this after the write/executable check, that is far too slow...
	netDir = resolveFilename(SCOPE_MEDIA, "net")
	if os.path.isdir(netDir):
		mountedDevs += map(lambda p: (os.path.join(netDir, p), _("Network mount")), os.listdir(netDir))
	mountedDevs = map(handleMountpoint, mountedDevs)
	return mountedDevs
config.plugins.FritzCall.phonebookLocation = ConfigSelection(choices=getMountedDevs())

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

avon = {}

def initAvon():
	avonFileName = resolveFilename(SCOPE_PLUGINS, "Extensions/FritzCall/avon.dat")
	if os.path.exists(avonFileName):
		for line in open(avonFileName):
			line = line.decode("iso-8859-1").encode('utf-8')
			if line[0] == '#':
				continue
			parts = line.split(':')
			if len(parts) == 2:
				avon[parts[0].replace('-','').replace('*','').replace('/','')] = parts[1]

def resolveNumberWithAvon(number, countrycode):
	if not number or number[0] != '0':
		return ""
		
	countrycode = countrycode.replace('00','+')
	if number[:2] == '00':
		normNumber = '+' + number[2:]
	elif number[:1] == '0':
		normNumber = countrycode + number[1:]
	else: # this should can not happen, but safety first
		return ""
	
	# debug('normNumer: ' + normNumber)
	for i in reversed(range(min(10, len(number)))):
		if avon.has_key(normNumber[:i]):
			return '[' + avon[normNumber[:i]].strip() + ']'
	return ""

def handleReverseLookupResult(name):
	found = re.match("NA: ([^;]*);VN: ([^;]*);STR: ([^;]*);HNR: ([^;]*);PLZ: ([^;]*);ORT: ([^;]*)", name)
	if found:
		( name, firstname, street, streetno, zipcode, city ) = (found.group(1),
												found.group(2),
												found.group(3),
												found.group(4),
												found.group(5),
												found.group(6)
												)
		if firstname:
			name += ' ' + firstname
		if street or streetno or zipcode or city:
			name += ', '
		if street:
			name += street
		if streetno:
			name += ' ' + streetno
		if (street or streetno) and (zipcode or city):
			name += ', '
		if zipcode and city:
			name += zipcode + ' ' + city
		elif zipcode:
			name += zipcode
		elif city:
			name += city
	return name

from xml.dom.minidom import parse
cbcInfos = {}
def initCbC():
	callbycallFileName = resolveFilename(SCOPE_PLUGINS, "Extensions/FritzCall/callbycall_world.xml")
	if os.path.exists(callbycallFileName):
		dom = parse(callbycallFileName)
		for top in dom.getElementsByTagName("callbycalls"):
			for cbc in top.getElementsByTagName("country"):
				code = cbc.getAttribute("code").replace("+","00")
				cbcInfos[code] = cbc.getElementsByTagName("callbycall")
	else:
		debug("[FritzCall] initCbC: callbycallFileName does not exist?!?!")

def stripCbCPrefix(number, countrycode):
	if number and number[:2] != "00" and cbcInfos.has_key(countrycode):
		for cbc in cbcInfos[countrycode]:
			if len(cbc.getElementsByTagName("length"))<1 or len(cbc.getElementsByTagName("prefix"))<1:
				debug("[FritzCall] stripCbCPrefix: entries for " + countrycode + " %s invalid")
				return number
			length = int(cbc.getElementsByTagName("length")[0].childNodes[0].data)
			prefix = cbc.getElementsByTagName("prefix")[0].childNodes[0].data
			# if re.match('^'+prefix, number):
			if number[:len(prefix)] == prefix:
				return number[length:]
	return number

class FritzAbout(Screen):

	def __init__(self, session):
		textFieldWidth = scaleV(350, 250)
		width = 5 + 150 + 20 + textFieldWidth + 5 + 175 + 5
		height = 5 + 175 + 5 + 25 + 5
		self.skin = """
			<screen name="FritzAbout" position="center,center" size="%d,%d" title="About FritzCall" >
				<widget name="text" position="175,%d" size="%d,%d" font="Regular;%d" />
				<ePixmap position="5,37" size="150,110" pixmap="%s" transparent="1" alphatest="blend" />
				<ePixmap position="%d,5" size="175,175" pixmap="%s" transparent="1" alphatest="blend" />
				<widget name="url" position="20,185" size="%d,25" font="Regular;%d" />
			</screen>""" % (
							width, height, # size
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
							"$Author: michael $"[1:-2] + "\n" +
							"$Revision: 683 $"[1:-2] + "\n" + 
							"$Date: 2012-09-30 13:04:26 +0200 (Sun, 30 Sep 2012) $"[1:23] + "\n"
							)
		self["url"] = Label("http://wiki.blue-panel.com/index.php/FritzCall")
		self.onLayoutFinish.append(self.setWindowTitle)

	def setWindowTitle(self):
		# TRANSLATORS: this is a window title.
		self.setTitle(_("About FritzCall"))

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
		self._phoneBookID = '0'
		self.info = None # (boxInfo, upTime, ipAddress, wlanState, dslState, tamActive, dectActive)
		self.getInfo(None)
		self.blacklist = ([], [])
		self.readBlacklist()

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

	def loadFritzBoxPhonebook(self):
		debug("[FritzCallFBF] loadFritzBoxPhonebook")
		if config.plugins.FritzCall.fritzphonebook.value:
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

		debug("[FritzCallFBF] _parseFritzBoxPhonebook")

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
					debug("[FritzCallFBF] _parseFritzBoxPhonebook: name: %s" %found.group(1))
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
						debug("[FritzCallFBF] Adding '''%s''' with '''%s''' from FRITZ!Box Phonebook!" % (thisname.strip(), thisnumber))
						# Beware: strings in phonebook.phonebook have to be in utf-8!
						phonebook.phonebook[thisnumber] = thisname

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
					debug("[FritzCallFBF] Adding '''%s''' with '''%s''' from FRITZ!Box Phonebook!" % (name, thisnumber))
					# Beware: strings in phonebook.phonebook have to be in utf-8!
					phonebook.phonebook[thisnumber] = name
				else:
					debug("[FritzCallFBF] ignoring empty number for %s" % name)
				continue
		elif self._md5Sid == '0000000000000000': # retry, it could be a race condition
			debug("[FritzCallFBF] _parseFritzBoxPhonebook: retry loading phonebook")
			self.loadFritzBoxPhonebook()
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
	
						thisnumber = self.cleanNumber(thisnumbers[i])
						debug("[FritzCallFBF] _parseFritzBoxPhonebookNew: Adding '''%s''' with '''%s''' from FRITZ!Box Phonebook!" % (thisname.strip(), thisnumber))
						# Beware: strings in phonebook.phonebook have to be in utf-8!
						phonebook.phonebook[thisnumber] = thisname
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
			name = phonebook.search(number)
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

fritzbox = None

class FritzMenu(Screen, HelpableScreen):
	def __init__(self, session):
		fontSize = scaleV(24, 21) # indeed this is font size +2
		noButtons = 2 # reset, wlan

		if not fritzbox or not fritzbox.info:
			return

		if fritzbox.info[FBF_tamActive]:
			noButtons += 1 # toggle mailboxes
		width = max(DESKTOP_WIDTH - scaleH(500, 250), noButtons*140+(noButtons+1)*10)
		# boxInfo 2 lines, gap, internet 2 lines, gap, dsl/wlan each 1 line, gap, buttons
		height = 5 + 2*fontSize + 10 + 2*fontSize + 10 + 2*fontSize + 10 + 40 + 5
		if fritzbox.info[FBF_tamActive] is not None:
			height += fontSize
		if fritzbox.info[FBF_dectActive] is not None:
			height += fontSize
		if fritzbox.info[FBF_faxActive] is not None:
			height += fontSize
		if fritzbox.info[FBF_rufumlActive] is not None:
			height += fontSize
		buttonsGap = (width-noButtons*140)/(noButtons+1)
		buttonsVPos = height-40-5

		varLinePos = 4
		if fritzbox.info[FBF_tamActive] is not None:
			mailboxLine = """
				<widget name="FBFMailbox" position="%d,%d" size="%d,%d" font="Regular;%d" />
				<widget name="mailbox_inactive" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="on"/>
				<widget name="mailbox_active" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="on"/>
				<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
				<widget name="key_yellow" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				""" % (
						40, 5+2*fontSize+10+varLinePos*fontSize+10, # position mailbox
						width-40-20, fontSize, # size mailbox
						fontSize-2,
						"skin_default/buttons/button_green_off.png",
						20, 5+2*fontSize+10+varLinePos*fontSize+10+(fontSize-16)/2, # position button mailbox
						"skin_default/buttons/button_green.png",
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
				<widget name="dect_inactive" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="on"/>
				<widget name="dect_active" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="on"/>
				""" % (
						40, 5+2*fontSize+10+varLinePos*fontSize+10, # position dect
						width-40-20, fontSize, # size dect
						fontSize-2,
						"skin_default/buttons/button_green_off.png",
						20, 5+2*fontSize+10+varLinePos*fontSize+10+(fontSize-16)/2, # position button dect
						"skin_default/buttons/button_green.png",
						20, 5+2*fontSize+10+varLinePos*fontSize+10+(fontSize-16)/2, # position button dect
				)
			varLinePos += 1
		else:
			dectLine = ""

		if fritzbox.info[FBF_faxActive] is not None:
			faxLine = """
				<widget name="FBFFax" position="%d,%d" size="%d,%d" font="Regular;%d" />
				<widget name="fax_inactive" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="on"/>
				<widget name="fax_active" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="on"/>
				""" % (
						40, 5+2*fontSize+10+varLinePos*fontSize+10, # position dect
						width-40-20, fontSize, # size dect
						fontSize-2,
						"skin_default/buttons/button_green_off.png",
						20, 5+2*fontSize+10+varLinePos*fontSize+10+(fontSize-16)/2, # position button dect
						"skin_default/buttons/button_green.png",
						20, 5+2*fontSize+10+varLinePos*fontSize+10+(fontSize-16)/2, # position button dect
				)
			varLinePos += 1
		else:
			faxLine = ""

		if fritzbox.info[FBF_rufumlActive] is not None:
			rufumlLine = """
				<widget name="FBFRufuml" position="%d,%d" size="%d,%d" font="Regular;%d" />
				<widget name="rufuml_inactive" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="on"/>
				<widget name="rufuml_active" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="on"/>
				""" % (
						40, 5+2*fontSize+10+varLinePos*fontSize+10, # position dect
						width-40-20, fontSize, # size dect
						fontSize-2,
						"skin_default/buttons/button_green_off.png",
						20, 5+2*fontSize+10+varLinePos*fontSize+10+(fontSize-16)/2, # position button dect
						"skin_default/buttons/button_green.png",
						20, 5+2*fontSize+10+varLinePos*fontSize+10+(fontSize-16)/2, # position button dect
				)
			varLinePos += 1
		else:
			rufumlLine = ""
	
		self.skin = """
			<screen name="FritzMenu" position="center,center" size="%d,%d" title="FRITZ!Box Fon Status" >
				<widget name="FBFInfo" position="%d,%d" size="%d,%d" font="Regular;%d" />
				<widget name="FBFInternet" position="%d,%d" size="%d,%d" font="Regular;%d" />
				<widget name="internet_inactive" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="on"/>
				<widget name="internet_active" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="on"/>
				<widget name="FBFDsl" position="%d,%d" size="%d,%d" font="Regular;%d" />
				<widget name="dsl_inactive" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="on"/>
				<widget name="dsl_active" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="on"/>
				<widget name="FBFWlan" position="%d,%d" size="%d,%d" font="Regular;%d" />
				<widget name="wlan_inactive" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="on"/>
				<widget name="wlan_active" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="on"/>
				%s
				%s
				%s
				%s
				<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="on" />
				<widget name="key_red" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="on" />
				<widget name="key_green" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			</screen>""" % (
						width, height, # size
						40, 5, # position info
						width-2*40, 2*fontSize, # size info
						fontSize-2,
						40, 5+2*fontSize+10, # position internet
						width-40, 2*fontSize, # size internet
						fontSize-2,
						"skin_default/buttons/button_green_off.png",
						20, 5+2*fontSize+10+(fontSize-16)/2, # position button internet
						"skin_default/buttons/button_green.png",
						20, 5+2*fontSize+10+(fontSize-16)/2, # position button internet
						40, 5+2*fontSize+10+2*fontSize+10, # position dsl
						width-40-20, fontSize, # size dsl
						fontSize-2,
						"skin_default/buttons/button_green_off.png",
						20, 5+2*fontSize+10+2*fontSize+10+(fontSize-16)/2, # position button dsl
						"skin_default/buttons/button_green.png",
						20, 5+2*fontSize+10+2*fontSize+10+(fontSize-16)/2, # position button dsl
						40, 5+2*fontSize+10+3*fontSize+10, # position wlan
						width-40-20, fontSize, # size wlan
						fontSize-2,
						"skin_default/buttons/button_green_off.png",
						20, 5+2*fontSize+10+3*fontSize+10+(fontSize-16)/2, # position button wlan
						"skin_default/buttons/button_green.png",
						20, 5+2*fontSize+10+3*fontSize+10+(fontSize-16)/2, # position button wlan
						mailboxLine,
						dectLine,
						faxLine,
						rufumlLine,
						buttonsGap, buttonsVPos, "skin_default/buttons/red.png", buttonsGap, buttonsVPos,
						buttonsGap+140+buttonsGap, buttonsVPos, "skin_default/buttons/green.png", buttonsGap+140+buttonsGap, buttonsVPos,
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
		self.onHide.append(self._timer.stop)
		self._getInfo()
		self.onLayoutFinish.append(self.setWindowTitle)

	def setWindowTitle(self):
		# TRANSLATORS: this is a window title.
		self.setTitle(_("FRITZ!Box Fon Status"))

	def _getInfo(self):
		if fritzbox:
			fritzbox.getInfo(self._fillMenu)

	def _fillMenu(self, status):
		(boxInfo, upTime, ipAddress, wlanState, dslState, tamActive, dectActive, faxActive, rufumlActive) = status
		if wlanState:
			self._wlanActive = (wlanState[0] == '1')
		self._mailboxActive = False
		try:
			if not self.has_key("FBFInfo"): # screen is closed already
				return

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
				if dslState[0] == '5':
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
				if wlanState[0 ] == '1':
					self["wlan_inactive"].hide()
					self["wlan_active"].show()
					message = 'WLAN'
					if wlanState[1] == '0':
						message += ' ' + _('not encrypted')
					else:
						message += ' ' + _('encrypted')
					if wlanState[2]:
						if wlanState[2] == '0':
							message = message + ', ' + _('no device active')
						elif wlanState[2] == '1':
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
	
			if fritzbox.info[FBF_dectActive] and dectActive and self.has_key("dect_inactive"):
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

	def __init__(self, session, text=""): #@UnusedVariable # pylint: disable=W0613
		self.width = DESKTOP_WIDTH * scaleH(75, 85)/100
		self.height = DESKTOP_HEIGHT * 0.75
		dateFieldWidth = scaleH(180, 105)
		dirFieldWidth = 16
		lengthFieldWidth = scaleH(55, 45)
		scrollbarWidth = scaleH(35, 35)
		entriesWidth = self.width -scaleH(40, 5) -5
		hereFieldWidth = entriesWidth -dirFieldWidth -5 -dateFieldWidth -5 -lengthFieldWidth -scrollbarWidth
		fieldWidth = entriesWidth -dirFieldWidth -5 -5 -scrollbarWidth
		fontSize = scaleV(22, 20)
		itemHeight = 2*fontSize+5
		entriesHeight = self.height -scaleV(15, 10) -5 -fontSize -5 -5 -5 -40 -5
		buttonGap = (self.width -4*140)/5
		buttonV = self.height -40
		debug("[FritzDisplayCalls] width: " + str(self.width))
		self.skin = """
			<screen name="FritzDisplayCalls" position="center,center" size="%d,%d" title="Phone calls" >
				<eLabel position="0,0" size="%d,2" backgroundColor="#aaaaaa" />
				<widget name="statusbar" position="%d,%d" size="%d,%d" font="Regular;%d" backgroundColor="#aaaaaa" transparent="1" />
				<eLabel position="0,%d" size="%d,2" backgroundColor="#aaaaaa" />
				<widget source="entries" render="Listbox" position="%d,%d" size="%d,%d" scrollbarMode="showOnDemand" transparent="1">
					<convert type="TemplatedMultiContent">
						{"template": [
								MultiContentEntryText(pos = (%d,%d), size = (%d,%d), font=0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 1), # index 0 is the number, index 1 is date
								MultiContentEntryPixmapAlphaTest(pos = (%d,%d), size = (%d,%d), png = 2), # index 1 i direction pixmap
								MultiContentEntryText(pos = (%d,%d), size = (%d,%d), font=1, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 3), # index 2 is remote name/number
								MultiContentEntryText(pos = (%d,%d), size = (%d,%d), font=0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 4), # index 3 is length of call
								MultiContentEntryText(pos = (%d,%d), size = (%d,%d), font=0, flags = RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text = 5), # index 4 is my number/name for number
							],
						"fonts": [gFont("Regular", %d), gFont("Regular", %d)],
						"itemHeight": %d
						}
					</convert>
				</widget>
				<eLabel position="0,%d" size="%d,2" backgroundColor="#aaaaaa" />
				<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="on" />
				<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="on" />
				<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="on" />
				<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="on" />
				<widget name="key_red" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_green" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_yellow" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_blue" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			</screen>""" % (
						# scaleH(90, 75), scaleV(100, 78), # position 
						self.width, self.height, # size
						self.width, # eLabel width
						scaleH(40, 5), scaleV(10, 5), # statusbar position
						self.width, fontSize+5, # statusbar size
						scaleV(21, 21), # statusbar font size
						scaleV(10, 5)+5+fontSize+5, # eLabel position vertical
						self.width, # eLabel width
						scaleH(40, 5), scaleV(10, 5)+5+fontSize+5+5, # entries position
						entriesWidth, entriesHeight, # entries size
						5+dirFieldWidth+5, fontSize+5, dateFieldWidth, fontSize, # date pos/size
						5, (itemHeight-dirFieldWidth)/2, dirFieldWidth, dirFieldWidth, # dir pos/size
						5+dirFieldWidth+5, 5, fieldWidth, fontSize, # caller pos/size
						2+dirFieldWidth+2+dateFieldWidth+5, fontSize+5, lengthFieldWidth, fontSize, # length pos/size
						2+dirFieldWidth+2+dateFieldWidth+5+lengthFieldWidth+5, fontSize+5, hereFieldWidth, fontSize, # my number pos/size
						fontSize-4, fontSize, # fontsize
						itemHeight, # itemHeight
						buttonV-5, # eLabel position vertical
						self.width, # eLabel width
						buttonGap, buttonV, "skin_default/buttons/red.png", # widget red
						2*buttonGap+140, buttonV, "skin_default/buttons/green.png", # widget green
						3*buttonGap+2*140, buttonV, "skin_default/buttons/yellow.png", # widget yellow
						4*buttonGap+3*140, buttonV, "skin_default/buttons/blue.png", # widget blue
						buttonGap, buttonV, scaleV(22, 21), # widget red
						2*buttonGap+140, buttonV, scaleV(22, 21), # widget green
						3*buttonGap+2*140, buttonV, scaleV(22, 21), # widget yellow
						4*buttonGap+3*140, buttonV, scaleV(22, 21), # widget blue
														)
		# debug("[FritzDisplayCalls] skin: " + self.skin)
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
		self.list = []
		self["entries"] = List(self.list)
		#=======================================================================
		# fontSize = scaleV(22, 18)
		# fontHeight = scaleV(24, 20)
		# self["entries"].l.setFont(0, gFont("Regular", fontSize))
		# self["entries"].l.setItemHeight(fontHeight)
		#=======================================================================
		debug("[FritzDisplayCalls] init: '''%s'''" % config.plugins.FritzCall.fbfCalls.value)
		self.display()
		self.onLayoutFinish.append(self.setWindowTitle)

	def setWindowTitle(self):
		# TRANSLATORS: this is a window title.
		self.setTitle(_("Phone calls"))

	def ok(self):
		self.close()

	def display(self, which=config.plugins.FritzCall.fbfCalls.value):
		debug("[FritzDisplayCalls] display")
		config.plugins.FritzCall.fbfCalls.value = which
		config.plugins.FritzCall.fbfCalls.save()
		fritzbox.getCalls(self, lambda x: self.gotCalls(x, which), which)

	def gotCalls(self, listOfCalls, which):
		debug("[FritzDisplayCalls] gotCalls")
		self.updateStatus(fbfCallsChoices[which] + " (" + str(len(listOfCalls)) + ")")

		directout = LoadPixmap(resolveFilename(SCOPE_PLUGINS, "Extensions/FritzCall/images/callout.png"))
		directin = LoadPixmap(resolveFilename(SCOPE_PLUGINS, "Extensions/FritzCall/images/callin.png"))
		directfailed = LoadPixmap(resolveFilename(SCOPE_PLUGINS, "Extensions/FritzCall/images/callinfailed.png"))
		def pixDir(direct):
			if direct == FBF_OUT_CALLS:
				direct = directout
			elif direct == FBF_IN_CALLS:
				direct = directin
			else:
				direct = directfailed
			return direct

		# debug("[FritzDisplayCalls] gotCalls: %s" %repr(listOfCalls))
		self.list = [(number, date[:6] + ' ' + date[9:14], pixDir(direct), remote, length, here) for (number, date, direct, remote, length, here) in listOfCalls]
		self["entries"].setList(self.list)
		if len(self.list) > 1:
			self["entries"].setIndex(1)

	def updateStatus(self, text):
		if self.has_key("statusbar"):
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
				elif cur[3]:
					name = cur[3]
					self.session.open(FritzOfferAction, self, number, name)
				else:
					# we don't
					fullname = resolveNumberWithAvon(number, config.plugins.FritzCall.country.value)
					if fullname:
						name = fullname
						self.session.open(FritzOfferAction, self, number, name)
					else:
						self.session.open(FritzOfferAction, self, number)
			else:
				# we do not even have a number...
				self.session.open(MessageBox,
						  _("UNKNOWN"),
						  type=MessageBox.TYPE_INFO)


class FritzOfferAction(Screen):

	def __init__(self, session, parent, number, name=""):
		# the layout will completely be recalculated in finishLayout
		self.skin = """
			<screen name="FritzOfferAction" title="Do what?" >
				<widget name="text" size="%d,%d" font="Regular;%d" />
				<widget name="FacePixmap" size="%d,%d" alphatest="on" />
				<widget name="key_red_p" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="on" />
				<widget name="key_green_p" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="on" />
				<widget name="key_yellow_p" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="on" />
				<widget name="key_red" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_green" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_yellow" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			</screen>""" % (
							DESKTOP_WIDTH, DESKTOP_HEIGHT, # set maximum size
							scaleH(22,21), # text
							DESKTOP_WIDTH, DESKTOP_HEIGHT, # set maximum size
							"skin_default/buttons/red.png",
							"skin_default/buttons/green.png",
							"skin_default/buttons/yellow.png",
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
			"red": self._lookup,
			"green": self._call,
			"yellow": self._add,
			"cancel": self._exit,
			"ok": self._exit, }, - 2)

		self._session = session
		if config.plugins.FritzCall.internal.value and len(number) > 3 and number[0] == "0":
			number = number[1:]
		self._number = number
		self._name = name.replace("\n", ", ")
		self["text"] = Label(number + "\n\n" + name.replace(", ", "\n"))
		self._parent = parent
		self._lookupState = 0
		self["key_red_p"] = Pixmap()
		self["key_green_p"] = Pixmap()
		self["key_yellow_p"] = Pixmap()
		self["FacePixmap"] = Pixmap()
		self.onLayoutFinish.append(self._finishLayout)
		self.onLayoutFinish.append(self.setWindowTitle)

	def setWindowTitle(self):
		# TRANSLATORS: this is a window title.
		self.setTitle(_("Do what?"))

	def _finishLayout(self):
		# pylint: disable=W0142
		debug("[FritzCall] FritzOfferAction/finishLayout number: %s/%s" % (self._number, self._name))

		faceFile = findFace(self._number, self._name)
		picPixmap = LoadPixmap(faceFile)
		if not picPixmap:	# that means most probably, that the picture is not 8 bit...
			Notifications.AddNotification(MessageBox, _("Found picture\n\n%s\n\nBut did not load. Probably not PNG, 8-bit") %faceFile, type = MessageBox.TYPE_ERROR)
			picPixmap = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/icons/input_error.png"))
		picSize = picPixmap.size()
		self["FacePixmap"].instance.setPixmap(picPixmap)

		noButtons = 3
		# recalculate window size
		textSize = self["text"].getSize()
		textSize = (textSize[0]+20, textSize[1]+20) # don't know, why, but size is too small
		debug("[FritzCall] FritzOfferAction/finishLayout textsize: %s/%s" % textSize)
		textSize = eSize(*textSize)
		width = max(scaleH(620, 545), noButtons*145, picSize.width() + textSize.width() + 30)
		height = max(picSize.height()+5, textSize.height()+5, scaleV(-1, 136)) + 5 + 40 + 5
		buttonsGap = (width-noButtons*140)/(noButtons+1)
		buttonsVPos = height-40-5
		wSize = (width,	height)
		wSize = eSize(*wSize)

		# center the smaller vertically
		hGap = (width-picSize.width()-textSize.width())/3
		picPos = (hGap, (height-50-picSize.height())/2+5)
		textPos = (hGap+picSize.width()+hGap, (height-50-textSize.height())/2+5)

		# resize screen
		self.instance.resize(wSize)
		# resize text
		self["text"].instance.resize(textSize)
		# resize pixmap
		self["FacePixmap"].instance.resize(picSize)
		# move buttons
		buttonPos = (buttonsGap, buttonsVPos)
		self["key_red_p"].instance.move(ePoint(*buttonPos))
		self["key_red"].instance.move(ePoint(*buttonPos))
		buttonPos = (buttonsGap+140+buttonsGap, buttonsVPos)
		self["key_green_p"].instance.move(ePoint(*buttonPos))
		self["key_green"].instance.move(ePoint(*buttonPos))
		buttonPos = (buttonsGap+140+buttonsGap+140+buttonsGap, buttonsVPos)
		self["key_yellow_p"].instance.move(ePoint(*buttonPos))
		self["key_yellow"].instance.move(ePoint(*buttonPos))
		# move text
		self["text"].instance.move(ePoint(*textPos))
		# move pixmap
		self["FacePixmap"].instance.move(ePoint(*picPos))
		# center window
		self.instance.move(ePoint((DESKTOP_WIDTH-wSize.width())/2, (DESKTOP_HEIGHT-wSize.height())/2))

	def _setTextAndResize(self, message):
		# pylint: disable=W0142
		self["text"].instance.resize(eSize(*(DESKTOP_WIDTH, DESKTOP_HEIGHT)))
		self["text"].setText(self._number + "\n\n" + message)
		self._finishLayout()

	def _lookup(self):
		phonebookLocation = config.plugins.FritzCall.phonebookLocation.value
		if self._lookupState == 0:
			self._lookupState = 1
			self._setTextAndResize(_("Reverse searching..."))
			ReverseLookupAndNotifier(self._number, self._lookedUp, "UTF-8", config.plugins.FritzCall.country.value)
			return
		if self._lookupState == 1 and os.path.exists(os.path.join(phonebookLocation, "PhoneBook.csv")):
			self._setTextAndResize(_("Searching in Outlook export..."))
			self._lookupState = 2
			self._lookedUp(self._number, FritzOutlookCSV.findNumber(self._number, os.path.join(phonebookLocation, "PhoneBook.csv"))) #@UndefinedVariable
			return
		else:
			self._lookupState = 2
		if self._lookupState == 2 and os.path.exists(os.path.join(phonebookLocation, "PhoneBook.ldif")):
			self._setTextAndResize(_("Searching in LDIF..."))
			self._lookupState = 0
			FritzLDIF.FindNumber(self._number, open(os.path.join(phonebookLocation, "PhoneBook.ldif")), self._lookedUp)
			return
		else:
			self._lookupState = 0
			self._lookup()

	def _lookedUp(self, number, name):
		name = handleReverseLookupResult(name)
		if not name:
			if self._lookupState == 1:
				name = _("No result from reverse lookup")
			elif self._lookupState == 2:
				name = _("No result from Outlook export")
			else:
				name = _("No result from LDIF")
		self._name = name
		self._number = number
		debug("[FritzOfferAction] lookedUp: " + str(name.replace(", ", "\n")))
		self._setTextAndResize(str(name.replace(", ", "\n")))

	def _call(self):
		if fritzbox:
			debug("[FritzOfferAction] call: %s" %self._number)
			self.session.open(MessageBox, _("Calling %s") %self._number, type=MessageBox.TYPE_INFO)
			fritzbox.dial(self._number)
		else:
			debug("[FritzOfferAction] call: no fritzbox object?!?!")
			self.session.open(MessageBox, _("FRITZ!Box not available for calling"), type=MessageBox.TYPE_INFO)

	def _add(self):
		debug("[FritzOfferAction] add: %s, %s" %(self._number, self._name))
		phonebook.FritzDisplayPhonebook(self._session).add(self._parent, self._number, self._name)
		self._exit()

	def _exit(self):
		self.close()


class FritzCallPhonebook:
	def __init__(self):
		debug("[FritzCallPhonebook] init")
		# Beware: strings in phonebook.phonebook have to be in utf-8!
		self.phonebook = {}
		if config.plugins.FritzCall.reloadPhonebookTime.value > 0:
			self.loop = eTimer()
			self.loop.callback.append(self.startReload)
			self.loop.start(config.plugins.FritzCall.reloadPhonebookTime.value*60*60*1000, 1)
		self.reload()

	def startReload(self):
		self.loop.stop()
		debug("[FritzCallPhonebook] reloading phonebooks " + time.ctime())
		self.reload()
		self.loop.start(config.plugins.FritzCall.reloadPhonebookTime.value*60*60*1000, 1)

	def reload(self):
		debug("[FritzCallPhonebook] reload")
		# Beware: strings in phonebook.phonebook have to be in utf-8!
		self.phonebook = {}

		if not config.plugins.FritzCall.enable.value:
			return

		phonebookFilename = os.path.join(config.plugins.FritzCall.phonebookLocation.value, "PhoneBook.txt")
		if config.plugins.FritzCall.phonebook.value and os.path.exists(phonebookFilename):
			debug("[FritzCallPhonebook] reload: read " + phonebookFilename)
			phonebookTxtCorrupt = False
			self.phonebook = {}
			for line in open(phonebookFilename):
				try:
					# Beware: strings in phonebook.phonebook have to be in utf-8!
					line = line.decode("utf-8")
				except UnicodeDecodeError: # this is just for the case, somebody wrote latin1 chars into PhoneBook.txt
					try:
						line = line.decode("iso-8859-1")
						debug("[FritzCallPhonebook] Fallback to ISO-8859-1 in %s" % line)
						phonebookTxtCorrupt = True
					except UnicodeDecodeError:
						debug("[FritzCallPhonebook] Could not parse internal Phonebook Entry %s" % line)
						phonebookTxtCorrupt = True
				line = line.encode("utf-8")
				elems = line.split('#')
				if len(elems) == 2:
					try:
						self.phonebook[elems[0]] = elems[1]
					except ValueError: # how could this possibly happen?!?!
						debug("[FritzCallPhonebook] Could not parse internal Phonebook Entry %s" % line)
						phonebookTxtCorrupt = True
				else:
					debug("[FritzCallPhonebook] Could not parse internal Phonebook Entry %s" % line)
					phonebookTxtCorrupt = True
					
				#===============================================================
				# found = re.match("^(\d+)#(.*)$", line)
				# if found:
				#	try:
				#		self.phonebook[found.group(1)] = found.group(2)
				#	except ValueError: # how could this possibly happen?!?!
				#		debug("[FritzCallPhonebook] Could not parse internal Phonebook Entry %s" % line)
				#		phonebookTxtCorrupt = True
				# else:
				#	debug("[FritzCallPhonebook] Could not parse internal Phonebook Entry %s" % line)
				#	phonebookTxtCorrupt = True
				#===============================================================

			if phonebookTxtCorrupt:
				# dump phonebook to PhoneBook.txt
				debug("[FritzCallPhonebook] dump Phonebook.txt")
				try:
					os.rename(phonebookFilename, phonebookFilename + ".bck")
					fNew = open(phonebookFilename, 'w')
					# Beware: strings in phonebook.phonebook are utf-8!
					for (number, name) in self.phonebook.iteritems():
						# Beware: strings in PhoneBook.txt have to be in utf-8!
						fNew.write(number + "#" + name.encode("utf-8"))
					fNew.close()
				except (IOError, OSError):
					debug("[FritzCallPhonebook] error renaming or writing to %s" %phonebookFilename)

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
		
		if fritzbox and config.plugins.FritzCall.fritzphonebook.value:
			fritzbox.loadFritzBoxPhonebook()

	def search(self, number):
		# debug("[FritzCallPhonebook] Searching for %s" %number)
		name = ""
		if not self.phonebook or not number:
			return

		if config.plugins.FritzCall.prefix.value:
			prefix = config.plugins.FritzCall.prefix.value
			if number[0] != '0':
				number = prefix + number
				# debug("[FritzCallPhonebook] search: added prefix: %s" %number)
			elif number[:len(prefix)] == prefix and self.phonebook.has_key(number[len(prefix):]):
				# debug("[FritzCallPhonebook] search: same prefix")
				name = self.phonebook[number[len(prefix):]]
				# debug("[FritzCallPhonebook] search: result: %s" %name)
		else:
			prefix = ""
				
		if not name and self.phonebook.has_key(number):
			name = self.phonebook[number]
				
		return name.replace(", ", "\n").strip()

	def add(self, number, name):
		'''
		
		@param number: number of entry
		@param name: name of entry, has to be in utf-8
		'''
		debug("[FritzCallPhonebook] add")
		name = name.replace("\n", ", ").replace('#','') # this is just for safety reasons. add should only be called with newlines converted into commas
		self.remove(number)
		self.phonebook[number] = name
		if number and number != 0:
			if config.plugins.FritzCall.phonebook.value:
				try:
					name = name.strip() + "\n"
					string = "%s#%s" % (number, name)
					# Beware: strings in PhoneBook.txt have to be in utf-8!
					f = open(os.path.join(config.plugins.FritzCall.phonebookLocation.value, "PhoneBook.txt"), 'a')
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
					phonebookFilename = os.path.join(config.plugins.FritzCall.phonebookLocation.value, "PhoneBook.txt")
					debug("[FritzCallPhonebook] remove entry in Phonebook.txt")
					fOld = open(phonebookFilename, 'r')
					fNew = open(phonebookFilename + str(os.getpid()), 'w')
					line = fOld.readline()
					while (line):
						elems = line.split('#')
						if len(elems) == 2 and not elems[0] == number:
							fNew.write(line)
						line = fOld.readline()
					fOld.close()
					fNew.close()
					# os.remove(phonebookFilename)
					eBackgroundFileEraser.getInstance().erase(phonebookFilename)
					os.rename(phonebookFilename + str(os.getpid()),	phonebookFilename)
					debug("[FritzCallPhonebook] removed %s from Phonebook.txt" % number)
					return True
	
				except (IOError, OSError):
					debug("[FritzCallPhonebook] error removing %s from %s" %(number, phonebookFilename))
		return False

	class FritzDisplayPhonebook(Screen, HelpableScreen, NumericalTextInput):
	
		def __init__(self, session):
			self.entriesWidth = DESKTOP_WIDTH * scaleH(75, 85)/100
			self.height = DESKTOP_HEIGHT * 0.75
			numberFieldWidth = scaleH(220, 160)
			fieldWidth = self.entriesWidth -5 -numberFieldWidth -10
			fontSize = scaleV(22, 18)
			fontHeight = scaleV(24, 20)
			buttonGap = (self.entriesWidth-4*140)/5
			debug("[FritzDisplayPhonebook] width: " + str(self.entriesWidth))
			self.skin = """
				<screen name="FritzDisplayPhonebook" position="center,center" size="%d,%d" title="Phonebook" >
					<eLabel position="0,0" size="%d,2" backgroundColor="#aaaaaa" />
					<widget source="entries" render="Listbox" position="%d,%d" size="%d,%d" scrollbarMode="showOnDemand" transparent="1">
						<convert type="TemplatedMultiContent">
							{"template": [
									MultiContentEntryText(pos = (%d,%d), size = (%d,%d), font=0, flags = RT_HALIGN_LEFT, text = 1), # index 0 is the name, index 1 is shortname
									MultiContentEntryText(pos = (%d,%d), size = (%d,%d), font=0, flags = RT_HALIGN_LEFT, text = 2), # index 2 is number
								],
							"fonts": [gFont("Regular", %d)],
							"itemHeight": %d
							}
						</convert>
					</widget>
					<eLabel position="0,%d" size="%d,2" backgroundColor="#aaaaaa" />
					<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="on" />
					<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="on" />
					<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="on" />
					<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="on" />
					<widget name="key_red" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
					<widget name="key_green" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
					<widget name="key_yellow" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
					<widget name="key_blue" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				</screen>""" % (
						# scaleH(90, 75), scaleV(100, 73), # position 
						self.entriesWidth, self.height, # size
						self.entriesWidth, # eLabel width
						scaleH(40, 5), scaleV(20, 5), # entries position
						self.entriesWidth-scaleH(40, 5), self.height-scaleV(20, 5)-5-5-40, # entries size
						0, 0, fieldWidth, scaleH(24,20), # name pos/size
						fieldWidth +5, 0, numberFieldWidth, scaleH(24,20), # dir pos/size
						fontSize, # fontsize
						fontHeight, # itemHeight
						self.height-40-5, # eLabel position vertical
						self.entriesWidth, # eLabel width
						buttonGap, self.height-40, "skin_default/buttons/red.png", # ePixmap red
						2*buttonGap+140, self.height-40, "skin_default/buttons/green.png", # ePixmap green
						3*buttonGap+2*140, self.height-40, "skin_default/buttons/yellow.png", # ePixmap yellow
						4*buttonGap+3*140, self.height-40, "skin_default/buttons/blue.png", # ePixmap blue
						buttonGap, self.height-40, scaleV(22, 21), # widget red
						2*buttonGap+140, self.height-40, scaleV(22, 21), # widget green
						3*buttonGap+2*140, self.height-40, scaleV(22, 21), # widget yellow
						4*buttonGap+3*140, self.height-40, scaleV(22, 21), # widget blue
						)
	
			# debug("[FritzDisplayCalls] skin: " + self.skin)
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
	
			self["entries"] = List([])
			debug("[FritzCallPhonebook] displayPhonebook init")
			self.help_window = None
			self.sortlist = []
			self.onLayoutFinish.append(self.setWindowTitle)
			self.display()

		def setWindowTitle(self):
			# TRANSLATORS: this is a window title.
			self.setTitle(_("Phonebook"))

		def display(self, filterNumber=""):
			debug("[FritzCallPhonebook] displayPhonebook/display")
			self.sortlist = []
			# Beware: strings in phonebook.phonebook are utf-8!
			sortlistHelp = sorted((name.lower(), name, number) for (number, name) in phonebook.phonebook.iteritems())
			for (low, name, number) in sortlistHelp:
				if number == "01234567890":
					continue
				try:
					low = low.decode("utf-8")
				except UnicodeDecodeError:  # this should definitely not happen
					try:
						low = low.decode("iso-8859-1")
					except UnicodeDecodeError:
						debug("[FritzCallPhonebook] displayPhonebook/display: corrupt phonebook entry for %s" % number)
						# self.session.open(MessageBox, _("Corrupt phonebook entry\nfor number %s\nDeleting.") %number, type = MessageBox.TYPE_ERROR)
						phonebook.remove(number)
						continue
				else:
					if filterNumber:
						filterNumber = filterNumber.lower()
						if low.find(filterNumber) == - 1:
							continue
					name = name.strip().decode("utf-8")
					number = number.strip().decode("utf-8")
					comma = name.find(',')
					if comma != -1:
						shortname = name[:comma]
					else:
						shortname = name
					number = number.encode("utf-8", "replace")
					name = name.encode("utf-8", "replace")
					shortname = shortname.encode('utf-8', 'replace')
					self.sortlist.append((name, shortname, number))
				
			self["entries"].setList(self.sortlist)
	
		def showEntry(self):
			cur = self["entries"].getCurrent()
			if cur:
				debug("[FritzCallPhonebook] displayPhonebook/showEntry %s" % (repr(cur)))
				number = cur[2]
				name = cur[0]
				self.session.open(FritzOfferAction, self, number, name)
	
		def delete(self):
			cur = self["entries"].getCurrent()
			if cur:
				debug("[FritzCallPhonebook] displayPhonebook/delete %s" % (repr(cur)))
				self.session.openWithCallback(
					self.deleteConfirmed,
					MessageBox,
					_("Do you really want to delete entry for\n\n%(number)s\n\n%(name)s?") 
					% { 'number':str(cur[2]), 'name':str(cur[0]).replace(", ", "\n") }
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
					debug("[FritzCallPhonebook] displayPhonebook/deleteConfirmed %s" % (repr(cur)))
					phonebook.remove(cur[2])
					self.display()
				# else:
					# self.session.open(MessageBox, _("Not deleted."), MessageBox.TYPE_INFO)
			else:
				self.session.open(MessageBox, _("No entry selected"), MessageBox.TYPE_INFO)
	
		def add(self, parent=None, number="", name=""):
			class AddScreen(Screen, ConfigListScreen):
				'''ConfiglistScreen with two ConfigTexts for Name and Number'''
	
				def __init__(self, session, parent, number="", name=""):
					#
					# setup screen with two ConfigText and OK and ABORT button
					# 
					noButtons = 2
					width = max(scaleH(-1, 570), noButtons*140)
					height = scaleV(-1, 100) # = 5 + 126 + 40 + 5; 6 lines of text possible
					buttonsGap = (width-noButtons*140)/(noButtons+1)
					buttonsVPos = height-40-5
					self.skin = """
						<screen position="center,center" size="%d,%d" title="Add entry to phonebook" >
						<widget name="config" position="5,5" size="%d,%d" scrollbarMode="showOnDemand" />
						<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="on" />
						<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="on" />
						<widget name="key_red" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
						<widget name="key_green" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
						</screen>""" % (
										width, height,
										width - 5 - 5, height - 5 - 40 - 5,
										buttonsGap, buttonsVPos, "skin_default/buttons/red.png",
										buttonsGap+140+buttonsGap, buttonsVPos, "skin_default/buttons/green.png",
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
					self.name = name
					self.number = number
					config.plugins.FritzCall.name.value = name
					config.plugins.FritzCall.number.value = number
					self.list.append(getConfigListEntry(_("Name"), config.plugins.FritzCall.name))
					self.list.append(getConfigListEntry(_("Number"), config.plugins.FritzCall.number))
					self["config"].list = self.list
					self["config"].l.setList(self.list)
					self.onLayoutFinish.append(self.setWindowTitle)
			
				def setWindowTitle(self):
					# TRANSLATORS: this is a window title.
					self.setTitle(_("Add entry to phonebook"))

				def add(self):
					# get texts from Screen
					# add (number,name) to sortlist and phonebook.phonebook and disk
					self.name = config.plugins.FritzCall.name.value
					self.number = config.plugins.FritzCall.number.value
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
			self.session.open(AddScreen, parent, number, name)
	
		def edit(self):
			debug("[FritzCallPhonebook] displayPhonebook/edit")
			cur = self["entries"].getCurrent()
			if cur is None:
				self.session.open(MessageBox, _("No entry selected"), MessageBox.TYPE_INFO)
			else:
				self.add(self, cur[2], cur[0])
	
		def search(self):
			debug("[FritzCallPhonebook] displayPhonebook/search")
			self.help_window = self.session.instantiateDialog(NumericalTextInputHelpDialog, self)
			self.help_window.show()
			# VirtualKeyboard instead of InputBox?
			self.session.openWithCallback(self.doSearch, InputBox, _("Enter Search Terms"), _("Search phonebook"))
	
		def doSearch(self, searchTerms):
			if not searchTerms:
				searchTerms = ""
			debug("[FritzCallPhonebook] displayPhonebook/doSearch: " + searchTerms)
			if self.help_window:
				self.session.deleteDialog(self.help_window)
				self.help_window = None
			self.display(searchTerms)
	
		def exit(self):
			self.close()

phonebook = FritzCallPhonebook()

class FritzCallSetup(Screen, ConfigListScreen, HelpableScreen):

	def __init__(self, session, args=None): #@UnusedVariable # pylint: disable=W0613
		self.width = scaleH(20+4*(140+90)+2*(35+40)+20, 4*140+2*35)
		width = self.width
		debug("[FritzCallSetup] width: " + str(self.width))
		self.skin = """
			<screen name="FritzCallSetup" position="center,center" size="%d,%d" title="FritzCall Setup" >
			<eLabel position="0,0" size="%d,2" backgroundColor="#aaaaaa" />
			<widget name="consideration" position="%d,%d" halign="center" size="%d,%d" font="Regular;%d" backgroundColor="#20040404" transparent="1" />
			<eLabel position="0,%d" size="%d,2" backgroundColor="#aaaaaa" />
			<widget name="config" position="%d,%d" size="%d,%d" scrollbarMode="showOnDemand" backgroundColor="#20040404" transparent="1" />
			<eLabel position="0,%d" size="%d,2" backgroundColor="#aaaaaa" />
			<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="on" />
			<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="on" />
			<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="on" />
			<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="on" />
			<widget name="key_red" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_green" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_yellow" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_blue" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<ePixmap position="%d,%d" zPosition="4" size="35,25" pixmap="%s" transparent="1" alphatest="on" />
			<ePixmap position="%d,%d" zPosition="4" size="35,25" pixmap="%s" transparent="1" alphatest="on" />
			</screen>""" % (
						# (DESKTOP_WIDTH-width)/2, scaleV(100, 73), # position 
						width, scaleV(560, 430), # size
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
						scaleH(20, 0), scaleV(525, 395), "skin_default/buttons/red.png", # pixmap red
						scaleH(20+140+90, 140), scaleV(525, 395), "skin_default/buttons/green.png", # pixmap green
						scaleH(20+2*(140+90), 2*140), scaleV(525, 395), "skin_default/buttons/yellow.png", # pixmap yellow
						scaleH(20+3*(140+90), 3*140), scaleV(525, 395), "skin_default/buttons/blue.png", # pixmap blue
						scaleH(20, 0), scaleV(525, 395), scaleV(21, 21), # widget red
						scaleH(20+(140+90), 140), scaleV(525, 395), scaleV(21, 21), # widget green
						scaleH(20+2*(140+90), 2*140), scaleV(525, 395), scaleV(21, 21), # widget yellow
						scaleH(20+3*(140+90), 3*140), scaleV(525, 395), scaleV(21, 21), # widget blue
						scaleH(20+4*(140+90), 4*140), scaleV(532, 402), "skin_default/buttons/key_info.png", # button info
						scaleH(20+4*(140+90)+(35+40), 4*140+35), scaleV(532, 402), "skin_default/buttons/key_menu.png", # button menu
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

		# get new list of locations for PhoneBook.txt
		self._mountedDevs = getMountedDevs()
		self.createSetup()
		self.onLayoutFinish.append(self.setWindowTitle)

	def setWindowTitle(self):
		# TRANSLATORS: this is a window title.
		self.setTitle(_("FritzCall Setup") + " (" + "$Revision: 683 $"[1: - 1] + "$Date: 2012-09-30 13:04:26 +0200 (Sun, 30 Sep 2012) $"[7:23] + ")")

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
			self.list.append(getConfigListEntry(_("FRITZ!Box FON address (Name or IP)"), config.plugins.FritzCall.hostname))

			self.list.append(getConfigListEntry(_("Show after Standby"), config.plugins.FritzCall.afterStandby))

			self.list.append(getConfigListEntry(_("Show only calls for specific MSN"), config.plugins.FritzCall.filter))
			if config.plugins.FritzCall.filter.value:
				self.list.append(getConfigListEntry(_("MSN to show (separated by ,)"), config.plugins.FritzCall.filtermsn))
				self.list.append(getConfigListEntry(_("Filter also list of calls"), config.plugins.FritzCall.filterCallList))
			self.list.append(getConfigListEntry(_("Mute on call"), config.plugins.FritzCall.muteOnCall))

			self.list.append(getConfigListEntry(_("Show Outgoing Calls"), config.plugins.FritzCall.showOutgoing))
			# not only for outgoing: config.plugins.FritzCall.showOutgoing.value:
			self.list.append(getConfigListEntry(_("Areacode to add to calls without one (if necessary)"), config.plugins.FritzCall.prefix))
			self.list.append(getConfigListEntry(_("Timeout for Call Notifications (seconds)"), config.plugins.FritzCall.timeout))
			self.list.append(getConfigListEntry(_("Reverse Lookup Caller ID (select country below)"), config.plugins.FritzCall.lookup))
			if config.plugins.FritzCall.lookup.value:
				self.list.append(getConfigListEntry(_("Country"), config.plugins.FritzCall.country))

			# TODO: make password unreadable?
			self.list.append(getConfigListEntry(_("Password Accessing FRITZ!Box"), config.plugins.FritzCall.password))
			self.list.append(getConfigListEntry(_("Extension number to initiate call on"), config.plugins.FritzCall.extension))
			self.list.append(getConfigListEntry(_("Read PhoneBook from FRITZ!Box"), config.plugins.FritzCall.fritzphonebook))
			if config.plugins.FritzCall.fritzphonebook.value:
				self.list.append(getConfigListEntry(_("Append type of number"), config.plugins.FritzCall.showType))
				self.list.append(getConfigListEntry(_("Append shortcut number"), config.plugins.FritzCall.showShortcut))
				self.list.append(getConfigListEntry(_("Append vanity name"), config.plugins.FritzCall.showVanity))

			self.list.append(getConfigListEntry(_("Use internal PhoneBook"), config.plugins.FritzCall.phonebook))
			if config.plugins.FritzCall.phonebook.value:
				if config.plugins.FritzCall.phonebookLocation.value in self._mountedDevs:
					config.plugins.FritzCall.phonebookLocation.setChoices(self._mountedDevs, config.plugins.FritzCall.phonebookLocation.value)
				else:
					config.plugins.FritzCall.phonebookLocation.setChoices(self._mountedDevs)
				path = config.plugins.FritzCall.phonebookLocation.value
				# check whether we can write to PhoneBook.txt
				if os.path.exists(os.path.join(path[0], "PhoneBook.txt")):
					if not os.access(os.path.join(path[0], "PhoneBook.txt"), os.W_OK):
						debug("[FritzCallSetup] createSetup: %s/PhoneBook.txt not writable, resetting to default" %(path[0]))
						config.plugins.FritzCall.phonebookLocation.setChoices(self._mountedDevs)
				elif not (os.path.isdir(path[0]) and os.access(path[0], os.W_OK|os.X_OK)):
					debug("[FritzCallSetup] createSetup: directory %s not writable, resetting to default" %(path[0]))
					config.plugins.FritzCall.phonebookLocation.setChoices(self._mountedDevs)

				self.list.append(getConfigListEntry(_("PhoneBook Location"), config.plugins.FritzCall.phonebookLocation))
				if config.plugins.FritzCall.lookup.value:
					self.list.append(getConfigListEntry(_("Automatically add new Caller to PhoneBook"), config.plugins.FritzCall.addcallers))

			if config.plugins.FritzCall.phonebook.value or config.plugins.FritzCall.fritzphonebook.value:
				self.list.append(getConfigListEntry(_("Reload interval for phonebooks (hours)"), config.plugins.FritzCall.reloadPhonebookTime))

			self.list.append(getConfigListEntry(_("Strip Leading 0"), config.plugins.FritzCall.internal))
			# self.list.append(getConfigListEntry(_("Default display mode for FRITZ!Box calls"), config.plugins.FritzCall.fbfCalls))
			self.list.append(getConfigListEntry(_("Display connection infos"), config.plugins.FritzCall.connectionVerbose))
			self.list.append(getConfigListEntry(_("Ignore callers with no phone number"), config.plugins.FritzCall.ignoreUnknown))
			self.list.append(getConfigListEntry(_("Debug"), config.plugins.FritzCall.debug))

		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def save(self):
#		debug("[FritzCallSetup] save"
		for x in self["config"].list:
			x[1].save()
		if config.plugins.FritzCall.phonebookLocation.isChanged():
			global phonebook
			phonebook = FritzCallPhonebook()
		if fritz_call:
			if config.plugins.FritzCall.enable.value:
				fritz_call.connect()
			else:
				fritz_call.shutdown()
		self.close()

	def cancel(self):
#		debug("[FritzCallSetup] cancel"
		for x in self["config"].list:
			x[1].cancel()
		self.close()

	def displayCalls(self):
		if config.plugins.FritzCall.enable.value:
			if fritzbox:
				self.session.open(FritzDisplayCalls)
			else:
				self.session.open(MessageBox, _("Cannot get calls from FRITZ!Box"), type=MessageBox.TYPE_INFO)
		else:
			self.session.open(MessageBox, _("Plugin not active"), type=MessageBox.TYPE_INFO)

	def displayPhonebook(self):
		if phonebook:
			if config.plugins.FritzCall.enable.value:
				self.session.open(phonebook.FritzDisplayPhonebook)
			else:
				self.session.open(MessageBox, _("Plugin not active"), type=MessageBox.TYPE_INFO)
		else:
			self.session.open(MessageBox, _("No phonebook"), type=MessageBox.TYPE_INFO)

	def about(self):
		self.session.open(FritzAbout)

	def menu(self):
		if config.plugins.FritzCall.enable.value:
			if fritzbox and fritzbox.info:
				self.session.open(FritzMenu)
			else:
				self.session.open(MessageBox, _("Cannot get infos from FRITZ!Box"), type=MessageBox.TYPE_INFO)
		else:
			self.session.open(MessageBox, _("Plugin not active"), type=MessageBox.TYPE_INFO)

standbyMode = False

class FritzCallList:
	def __init__(self):
		self.callList = [ ]
	
	def add(self, event, date, number, caller, phone):
		debug("[FritzCallList] add: %s %s" % (number, caller))
		if len(self.callList) > 10:
			if self.callList[0] != "Start":
				self.callList[0] = "Start"
			del self.callList[1]

		self.callList.append((event, number, date, caller, phone))
	
	def display(self):
		debug("[FritzCallList] display")
		global standbyMode
		standbyMode = False
		# Standby.inStandby.onClose.remove(self.display) object does not exist anymore...
		# build screen from call list
		text = "\n"

		if not self.callList:
			text = _("no calls") 
		else:
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
				date = date[:6] + date[9:14]
	
				# our phone could be of the form "0123456789 (home)", then we only take "home"
				oBrack = phone.find('(')
				cBrack = phone.find(')')
				if oBrack != -1 and cBrack != -1:
					phone = phone[oBrack+1:cBrack]
	
				# should not happen, for safety reasons
				if not caller:
					caller = _("UNKNOWN")
				
				#  if we have an unknown number, show the number
				if caller == _("UNKNOWN") and number != "":
					caller = number
				else:
					# strip off the address part of the remote caller/callee, if there is any
					nl = caller.find('\n')
					if nl != -1:
						caller = caller[:nl]
					elif caller[0] == '[' and caller[-1] == ']':
						# that means, we've got an unknown number with a city added from avon.dat 
						if (len(number) + 1 + len(caller) + len(phone)) <= 40:
							caller = number + ' ' + caller
						else:
							caller = number
	
				while (len(caller) + len(phone)) > 40:
					if len(caller) > len(phone):
						caller = caller[: - 1]
					else:
						phone = phone[: - 1]
	
				text = text + "%s %s %s %s\n" % (date, caller, direction, phone)
				debug("[FritzCallList] display: '%s %s %s %s'" % (date, caller, direction, phone))

		# display screen
		Notifications.AddNotification(MessageBox, text, type=MessageBox.TYPE_INFO)
		# TODO please HELP: from where can I get a session?
		# my_global_session.open(FritzDisplayCalls, text)
		self.callList = [ ]

callList = FritzCallList()

def findFace(number, name):
	debug("[FritzCall] findFace number/name: %s/%s" % (number, name))
	if name:
		sep = name.find(',')
		if sep != -1:
			name = name[:sep]
		sep = name.find('\n')
		if sep != -1:
			name = name[:sep]
	else:
		name = _("UNKNOWN")

	facesDir = os.path.join(config.plugins.FritzCall.phonebookLocation.value, "FritzCallFaces")
	numberFile = os.path.join(facesDir, number)
	nameFile = os.path.join(facesDir, name)
	facesFile = ""
	if number and os.path.exists(numberFile):
		facesFile = numberFile
	elif number and os.path.exists(numberFile + ".png"):
		facesFile = numberFile + ".png"
	elif number and os.path.exists(numberFile + ".PNG"):
		facesFile = numberFile + ".PNG"
	elif name and os.path.exists(nameFile + ".png"):
		facesFile = nameFile + ".png"
	elif name and os.path.exists(nameFile + ".PNG"):
		facesFile = nameFile + ".PNG"
	else:
		facesFile = resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/icons/input_info.png")

	debug("[FritzCall] findFace result: %s" % (facesFile))
	return facesFile

class MessageBoxPixmap(Screen):
	def __init__(self, session, text, number = "", name = "", timeout = -1):
		self.skin = """
	<screen name="MessageBoxPixmap" position="center,center" size="600,10" title="New Call">
		<widget name="text" position="115,8" size="520,0" font="Regular;%d" />
		<widget name="InfoPixmap" pixmap="%s" position="5,5" size="100,100" alphatest="on" />
	</screen>
		""" % (
			# scaleH(350, 60), scaleV(175, 245),
			scaleV(24, 22), resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/icons/input_info.png")
			)
		debug("[FritzCall] MessageBoxPixmap number: %s" % number)
		Screen.__init__(self, session)
		# MessageBox.__init__(self, session, text, type=MessageBox.TYPE_INFO, timeout=timeout)
		self["text"] = Label(text)
		self["InfoPixmap"] = Pixmap()
		self._session = session
		self._number = number
		self._name = name
		self._timerRunning = False
		self._timer = None
		self._timeout = timeout
		self._origTitle = None
		self._initTimeout()
		self.onLayoutFinish.append(self._finishLayout)
		self["actions"] = ActionMap(["OkCancelActions"],
		{
			"cancel": self._exit,
			"ok": self._exit, }, - 2)

	def _finishLayout(self):
		# pylint: disable=W0142
		debug("[FritzCall] MessageBoxPixmap/setInfoPixmap number: %s/%s" % (self._number, self._name))

		self.setTitle(_("New call"))

		faceFile = findFace(self._number, self._name)
		picPixmap = LoadPixmap(faceFile)
		if not picPixmap:	# that means most probably, that the picture is not 8 bit...
			Notifications.AddNotification(MessageBox, _("Found picture\n\n%s\n\nBut did not load. Probably not PNG, 8-bit") %faceFile, type = MessageBox.TYPE_ERROR)
			picPixmap = LoadPixmap(resolveFilename(SCOPE_SKIN_IMAGE, "skin_default/icons/input_error.png"))
		picSize = picPixmap.size()
		self["InfoPixmap"].instance.setPixmap(picPixmap)

		# recalculate window size
		textSize = self["text"].getSize()
		textSize = (textSize[0]+20, textSize[1]+20) # don't know, why, but size is too small
		textSize = eSize(*textSize)
		width = max(scaleH(600, 280), picSize.width() + textSize.width() + 30)
		height = max(scaleV(300, 250), picSize.height()+10, textSize.height()+10)
		wSize = (width, height)
		wSize = eSize(*wSize)

		# center the smaller vertically
		hGap = (width-picSize.width()-textSize.width())/3
		picPos = (hGap, (height-picSize.height())/2+1)
		textPos = (hGap+picSize.width()+hGap, (height-textSize.height())/2+1)

		# resize screen
		self.instance.resize(wSize)
		# resize text
		self["text"].instance.resize(textSize)
		# resize pixmap
		self["InfoPixmap"].instance.resize(picSize)
		# move text
		self["text"].instance.move(ePoint(*textPos))
		# move pixmap
		self["InfoPixmap"].instance.move(ePoint(*picPos))
		# center window
		self.instance.move(ePoint((DESKTOP_WIDTH-wSize.width())/2, (DESKTOP_HEIGHT-wSize.height())/2))

	def _initTimeout(self):
		if self._timeout > 0:
			self._timer = eTimer()
			self._timer.callback.append(self._timerTick)
			self.onExecBegin.append(self._startTimer)
			self._origTitle = None
			if self.execing:
				self._timerTick()
			else:
				self.onShown.append(self.__onShown)
			self._timerRunning = True
		else:
			self._timerRunning = False

	def __onShown(self):
		self.onShown.remove(self.__onShown)
		self._timerTick()

	def _startTimer(self):
		self._timer.start(1000)

#===============================================================================
#	def stopTimer(self):
#		if self._timerRunning:
#			del self._timer
#			self.setTitle(self._origTitle)
#			self._timerRunning = False
#===============================================================================

	def _timerTick(self):
		if self.execing:
			self._timeout -= 1
			if self._origTitle is None:
				self._origTitle = self.instance.getTitle()
			self.setTitle(self._origTitle + " (" + str(self._timeout) + ")")
			if self._timeout == 0:
				self._timer.stop()
				self._timerRunning = False
				self._exit()

	def _exit(self):
		self.close()

mutedOnConnID = None
def notifyCall(event, date, number, caller, phone, connID):
	if Standby.inStandby is None or config.plugins.FritzCall.afterStandby.value == "each":
		if event == "RING":
			global mutedOnConnID
			if config.plugins.FritzCall.muteOnCall.value and not mutedOnConnID:
				debug("[FritzCall] mute on connID: %s" % connID)
				mutedOnConnID = connID
				# eDVBVolumecontrol.getInstance().volumeMute() # with this, we get no mute icon...
				if not eDVBVolumecontrol.getInstance().isMuted():
					globalActionMap.actions["volumeMute"]()
			text = _("Incoming Call on %(date)s at %(time)s from\n---------------------------------------------\n%(number)s\n%(caller)s\n---------------------------------------------\nto: %(phone)s") % { 'date':date[:8], 'time':date[9:], 'number':number, 'caller':caller, 'phone':phone }
		else:
			text = _("Outgoing Call on %(date)s at %(time)s to\n---------------------------------------------\n%(number)s\n%(caller)s\n---------------------------------------------\nfrom: %(phone)s") % { 'date':date[:8], 'time':date[9:], 'number':number, 'caller':caller, 'phone':phone }
		debug("[FritzCall] notifyCall:\n%s" % text)
		# Notifications.AddNotification(MessageBox, text, type=MessageBox.TYPE_INFO, timeout=config.plugins.FritzCall.timeout.value)
		Notifications.AddNotification(MessageBoxPixmap, text, number=number, name=caller, timeout=config.plugins.FritzCall.timeout.value)
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

	# user exit
	# call FritzCallserAction.sh in the same dir as Phonebook.txt with the following parameters:
	# event: "RING" (incomning) or "CALL" (outgoing)
	# date of event, format: "dd.mm.yy hh.mm.ss"
	# telephone number which is calling/is called
	# caller's name and address, format Name\n Street\n ZIP City
	# line/number which is called/which is used for calling
	userActionScript = os.path.join(config.plugins.FritzCall.phonebookLocation.value, "FritzCallUserAction.sh")
	if os.path.exists(userActionScript) and os.access(userActionScript, os.X_OK):
		cmd = userActionScript + ' "' + event + '" "' + date + '" "' + number + '" "' + caller + '" "' + phone + '"'
		debug("[FritzCall] notifyCall: calling: %s" % cmd)
		os.system(cmd)


#===============================================================================
#		We need a separate class for each invocation of reverseLookup to retain
#		the necessary data for the notification
#===============================================================================

countries = { }
reverselookupMtime = 0

class FritzReverseLookupAndNotifier:
	def __init__(self, event, number, caller, phone, date, connID):
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
		self.connID = connID

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
		self.number = number
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

		name = handleReverseLookupResult(caller)
		if name:
			self.caller = name.replace(", ", "\n").replace('#','')
			# TODO: I don't know, why we store only for incoming calls...
			# if self.number != 0 and config.plugins.FritzCall.addcallers.value and self.event == "RING":
			if self.number != 0 and config.plugins.FritzCall.addcallers.value:
				debug("[FritzReverseLookupAndNotifier] add to phonebook")
				phonebook.add(self.number, self.caller)
		else:
			name = resolveNumberWithAvon(self.number, config.plugins.FritzCall.country.value)
			if not name:
				self.caller = _("UNKNOWN")
			else:
				self.caller = name
		notifyCall(self.event, self.date, self.number, self.caller, self.phone, self.connID)
		# kill that object...

class FritzProtocol(LineReceiver):
	def __init__(self):
		debug("[FritzProtocol] " + "$Revision: 683 $"[1:-1]	+ "$Date: 2012-09-30 13:04:26 +0200 (Sun, 30 Sep 2012) $"[7:23] + " starting")
		global mutedOnConnID
		mutedOnConnID = None
		self.number = '0'
		self.caller = None
		self.phone = None
		self.date = '0'
		self.event = None
		self.connID = None

	def resetValues(self):
		debug("[FritzProtocol] resetValues")
		self.number = '0'
		self.caller = None
		self.phone = None
		self.date = '0'
		self.event = None
		self.connID = None

	def notifyAndReset(self):
		notifyCall(self.event, self.date, self.number, self.caller, self.phone, self.connID)
		self.resetValues()

	def lineReceived(self, line):
		debug("[FritzProtocol] lineReceived: %s" % line)
#15.07.06 00:38:54;CALL;1;4;<from/our msn>;<to/extern>;
#15.07.06 00:38:58;DISCONNECT;1;0;
#15.07.06 00:39:22;RING;0;<from/extern>;<to/our msn>;
#15.07.06 00:39:27;DISCONNECT;0;0;
		anEvent = line.split(';')
		(self.date, self.event) = anEvent[0:2]
		self.connID = anEvent[2]

		filtermsns = config.plugins.FritzCall.filtermsn.value.split(",")
		for i in range(len(filtermsns)):
			filtermsns[i] = filtermsns[i].strip()

		if config.plugins.FritzCall.ignoreUnknown.value:
			if self.event == "RING":
				if not anEvent[3]:
					debug("[FritzProtocol] lineReceived: call from unknown phone; skipping")
					return
				elif not anEvent[5]:
					debug("[FritzProtocol] lineReceived: call to unknown phone; skipping")
					return

		# debug("[FritzProtocol] Volcontrol dir: %s" % dir(eDVBVolumecontrol.getInstance()))
		# debug("[FritzCall] unmute on connID: %s?" %self.connID)
		global mutedOnConnID
		if self.event == "DISCONNECT" and config.plugins.FritzCall.muteOnCall.value and mutedOnConnID == self.connID:
			debug("[FritzCall] unmute on connID: %s!" % self.connID)
			mutedOnConnID = None
			# eDVBVolumecontrol.getInstance().volumeUnMute()
			if eDVBVolumecontrol.getInstance().isMuted():
				globalActionMap.actions["volumeMute"]()
		# not supported so far, because, taht would mean muting on EVERY connect, regardless of RING or CALL or filter active
		#=======================================================================
		# elif self.event == "CONNECT" and config.plugins.FritzCall.muteOnCall.value == "connect":
		#	debug("[FritzCall] mute on connID: %s" % self.connID)
		#	mutedOnConnID = self.connID
		#	# eDVBVolumecontrol.getInstance().volumeMute() # with this, we get no mute icon...
		#	if not eDVBVolumecontrol.getInstance().isMuted():
		#		globalActionMap.actions["volumeMute"]()
		#=======================================================================
		elif self.event == "RING" or (self.event == "CALL" and config.plugins.FritzCall.showOutgoing.value):
			phone = anEvent[4]
			if self.event == "RING":
				number = anEvent[3] 
				if fritzbox and number in fritzbox.blacklist[0]:
					debug("[FritzProtocol] lineReceived phone: '''%s''' blacklisted number: '''%s'''" % (phone, number))
					return 
			else:
				number = anEvent[5]
				if number in fritzbox.blacklist[1]:
					debug("[FritzProtocol] lineReceived phone: '''%s''' blacklisted number: '''%s'''" % (phone, number))
					return 

			debug("[FritzProtocol] lineReceived phone: '''%s''' number: '''%s'''" % (phone, number))

			if not (config.plugins.FritzCall.filter.value and phone not in filtermsns):
				debug("[FritzProtocol] lineReceived no filter hit")
				if phone:
					phonename = phonebook.search(phone)		   # do we have a name for the number of our side?
					if phonename:
						self.phone = "%s (%s)" % (phone, phonename)
					else:
						self.phone = phone
				else:
					self.phone = _("UNKNOWN")

				if not number:
					debug("[FritzProtocol] lineReceived: no number")
					self.number = _("number suppressed")
					self.caller = _("UNKNOWN")
				else:
					if config.plugins.FritzCall.internal.value and len(number) > 3 and number[0] == "0":
						debug("[FritzProtocol] lineReceived: strip leading 0")
						self.number = number[1:]
					else:
						self.number = number
						if self.event == "CALL" and self.number[0] != '0':					  # should only happen for outgoing
							debug("[FritzProtocol] lineReceived: add local prefix")
							self.number = config.plugins.FritzCall.prefix.value + self.number
	
					# strip CbC prefixes
					if self.event == "CALL":
						number = stripCbCPrefix(self.number, config.plugins.FritzCall.country.value)
	
					debug("[FritzProtocol] lineReceived phonebook.search: %s" % self.number)
					self.caller = phonebook.search(self.number)
					debug("[FritzProtocol] lineReceived phonebook.search reault: %s" % self.caller)
					if not self.caller:
						if config.plugins.FritzCall.lookup.value:
							FritzReverseLookupAndNotifier(self.event, self.number, self.caller, self.phone, self.date, self.connID)
							return							# reverselookup is supposed to handle the message itself
						else:
							self.caller = _("UNKNOWN")

				self.notifyAndReset()

class FritzClientFactory(ReconnectingClientFactory):
	initialDelay = 200
	maxDelay = 30

	def __init__(self):
		self.hangup_ok = False
	def startedConnecting(self, connector): #@UnusedVariable # pylint: disable=W0613
		if config.plugins.FritzCall.connectionVerbose.value:
			debug("[FRITZ!FritzClientFactory] - startedConnecting")
			Notifications.AddNotification(MessageBox, _("Connecting to FRITZ!Box..."), type=MessageBox.TYPE_INFO, timeout=2)

	def buildProtocol(self, addr): #@UnusedVariable # pylint: disable=W0613
		global fritzbox, phonebook
		if config.plugins.FritzCall.connectionVerbose.value:
			debug("[FRITZ!FritzClientFactory] - buildProtocol")
			Notifications.AddNotification(MessageBox, _("Connected to FRITZ!Box!"), type=MessageBox.TYPE_INFO, timeout=4)
		self.resetDelay()
		initDebug()
		initCbC()
		initAvon()
		fritzbox = FritzCallFBF()
		phonebook = FritzCallPhonebook()
		return FritzProtocol()

	def clientConnectionLost(self, connector, reason):
		global fritzbox
		if not self.hangup_ok and config.plugins.FritzCall.connectionVerbose.value:
			debug("[FRITZ!FritzClientFactory] - clientConnectionLost")
			Notifications.AddNotification(MessageBox, _("Connection to FRITZ!Box! lost\n (%s)\nretrying...") % reason.getErrorMessage(), type=MessageBox.TYPE_INFO, timeout=config.plugins.FritzCall.timeout.value)
		ReconnectingClientFactory.clientConnectionLost(self, connector, reason)
		# config.plugins.FritzCall.enable.value = False
		fritzbox = None

	def clientConnectionFailed(self, connector, reason):
		global fritzbox
		if not self.hangup_ok and config.plugins.FritzCall.connectionVerbose.value:
			debug("[FRITZ!FritzClientFactory] - clientConnectionFailed")
			Notifications.AddNotification(MessageBox, _("Connecting to FRITZ!Box failed\n (%s)\nretrying...") % reason.getErrorMessage(), type=MessageBox.TYPE_INFO, timeout=config.plugins.FritzCall.timeout.value)
		ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)
		# config.plugins.FritzCall.enable.value = False
		fritzbox = None
		
class FritzCall:
	def __init__(self):
		self.dialog = None
		self.desc = None
		if config.plugins.FritzCall.enable.value:
			self.connect()

	def connect(self):
		self.abort()
		if config.plugins.FritzCall.enable.value:
			fact = FritzClientFactory()
			self.desc = (fact, reactor.connectTCP(config.plugins.FritzCall.hostname.value, 1012, fact)) #@UndefinedVariable # pylint: disable=E1101

	def shutdown(self):
		self.abort()

	def abort(self):
		if self.desc is not None:
			self.desc[0].hangup_ok = True
			self.desc[0].stopTrying()
			self.desc[1].disconnect()
			self.desc = None

def displayCalls(session, servicelist=None): #@UnusedVariable # pylint: disable=W0613
	if config.plugins.FritzCall.enable.value:
		if fritzbox:
			session.open(FritzDisplayCalls)
		else:
			Notifications.AddNotification(MessageBox, _("Cannot get calls from FRITZ!Box"), type=MessageBox.TYPE_INFO)
	else:
		Notifications.AddNotification(MessageBox, _("Plugin not active"), type=MessageBox.TYPE_INFO)

def displayPhonebook(session, servicelist=None): #@UnusedVariable # pylint: disable=W0613
	if phonebook:
		if config.plugins.FritzCall.enable.value:
			session.open(phonebook.FritzDisplayPhonebook)
		else:
			Notifications.AddNotification(MessageBox, _("Plugin not active"), type=MessageBox.TYPE_INFO)
	else:
		Notifications.AddNotification(MessageBox, _("No phonebook"), type=MessageBox.TYPE_INFO)

def displayFBFStatus(session, servicelist=None): #@UnusedVariable # pylint: disable=W0613
	if config.plugins.FritzCall.enable.value:
		if fritzbox and fritzbox.info:
			session.open(FritzMenu)
		else:
			Notifications.AddNotification(MessageBox, _("Cannot get infos from FRITZ!Box"), type=MessageBox.TYPE_INFO)
	else:
		Notifications.AddNotification(MessageBox, _("Plugin not active"), type=MessageBox.TYPE_INFO)

def main(session, servicelist=None):
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

def Plugins(**kwargs): #@UnusedVariable # pylint: disable=W0613,C0103
	what = _("Display FRITZ!box-Fon calls on screen")
	what_calls = _("Phone calls")
	what_phonebook = _("Phonebook")
	what_status = _("FRITZ!Box Fon Status")
	return [ PluginDescriptor(name="FritzCall", description=what, where=PluginDescriptor.WHERE_PLUGINMENU, icon="plugin.png", fnc=main),
		PluginDescriptor(name=what_calls, description=what_calls, where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=displayCalls),
		PluginDescriptor(name=what_phonebook, description=what_phonebook, where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=displayPhonebook),
		PluginDescriptor(name=what_status, description=what_status, where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=displayFBFStatus),
		PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc=autostart) ]
