# -*- coding: utf-8 -*-
#===============================================================================
# $Author$
# $Revision$
# $Date$
# $Id$
#==============================
from Screens.Screen import Screen #@UnresolvedImport
from Screens.MessageBox import MessageBox #@UnresolvedImport
from Screens.NumericalTextInputHelpDialog import NumericalTextInputHelpDialog #@UnresolvedImport
from Screens.InputBox import InputBox #@UnresolvedImport
from Screens import Standby #@UnresolvedImport
from Screens.HelpMenu import HelpableScreen #@UnresolvedImport

from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT, RT_HALIGN_RIGHT #@UnresolvedImport

from Components.MenuList import MenuList #@UnresolvedImport
from Components.ActionMap import ActionMap #@UnresolvedImport
from Components.Label import Label #@UnresolvedImport
from Components.Button import Button #@UnresolvedImport
from Components.config import config, ConfigSubsection, ConfigSelection, ConfigEnableDisable, getConfigListEntry, ConfigText, ConfigInteger #@UnresolvedImport
try:
	from Components.config import ConfigPassword
except ImportError:
	ConfigPassword = ConfigText
from Components.ConfigList import ConfigListScreen #@UnresolvedImport

from Plugins.Plugin import PluginDescriptor #@UnresolvedImport
from Tools import Notifications #@UnresolvedImport
from Tools.NumericalTextInput import NumericalTextInput #@UnresolvedImport
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_SKIN_IMAGE #@UnresolvedImport
from Tools.LoadPixmap import LoadPixmap #@UnresolvedImport

from twisted.internet import reactor #@UnresolvedImport
from twisted.internet.protocol import ReconnectingClientFactory #@UnresolvedImport
from twisted.protocols.basic import LineReceiver #@UnresolvedImport
from twisted.web.client import getPage #@UnresolvedImport

from urllib import urlencode 
import re, time, os

from nrzuname import ReverseLookupAndNotifier, html2unicode
import FritzOutlookCSV, FritzLDIF
from . import _, debug #@UnresolvedImport

from enigma import getDesktop #@UnresolvedImport
DESKTOP_WIDTH = getDesktop(0).size().width()
DESKTOP_HEIGHT = getDesktop(0).size().height()
DESKTOP_SKIN = config.skin.primary_skin.value.replace("/skin.xml", "")
XXX = 0 # TODO: Platzhalter für fullscreen SD skin
#
# this is pure magic.
# It returns the first value, if HD (1280x720),
# the second if SD (720x576),
# else something scaled accordingly
#
def scaleH(y2, y1):
	return scale(y2, y1, 1280, 720, DESKTOP_WIDTH)
def scaleV(y2, y1):
	return scale(y2, y1, 720, 576, DESKTOP_HEIGHT)
def scale(y2, y1, x2, x1, x):
	return (y2 - y1) * (x - x1) / (x2 - x1) + y1

my_global_session = None

config.plugins.FritzCall = ConfigSubsection()
config.plugins.FritzCall.enable = ConfigEnableDisable(default=False)
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
config.plugins.FritzCall.phonebookLocation = ConfigSelection(choices=[("/etc/enigma2", _("Flash")), ("/media/usb", _("USB Stick")), ("/media/cf", _("CF Drive")), ("/media/hdd", _("Harddisk"))])
config.plugins.FritzCall.password = ConfigPassword(default="", fixed_size=False)
config.plugins.FritzCall.extension = ConfigText(default='1', fixed_size=False)
config.plugins.FritzCall.extension.setUseableChars('0123456789')
config.plugins.FritzCall.showType = ConfigEnableDisable(default=True)
config.plugins.FritzCall.showShortcut = ConfigEnableDisable(default=False)
config.plugins.FritzCall.showVanity = ConfigEnableDisable(default=False)
config.plugins.FritzCall.prefix = ConfigText(default="", fixed_size=False)
config.plugins.FritzCall.prefix.setUseableChars('0123456789')
config.plugins.FritzCall.fullscreen = ConfigEnableDisable(default=False)
config.plugins.FritzCall.debug = ConfigEnableDisable(default=False)

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

def initDebug():
	try:
		os.remove("/tmp/FritzDebug.log")
	except:
		pass

class FritzAbout(Screen):
	textFieldWidth = 250
	width = 5 + 150 + 20 + textFieldWidth + 5 + 175 + 5
	height = 5 + 175 + 5 + 25 + 5
	# TRANSLATORS: this is a window title. Avoid the use of non ascii chars
	skin = """
		<screen name="FritzAbout" position="%d,%d" size="%d,%d" title="%s" >
			<widget name="text" position="175,%d" size="%d,%d" font="Regular;%d" />
			<ePixmap position="5,37" size="150,110" pixmap="%s" transparent="1" alphatest="blend" />
			<ePixmap position="%d,5" size="175,175" pixmap="%s" transparent="1" alphatest="blend" />
			<widget name="url" position="10,185" size="%d,25" font="Regular;%d" />
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
						width-20, # url width
						scaleV(24,21) # url font size
						)

	def __init__(self, session):
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


class FritzCallFBF:
	def __init__(self):
		debug("[FritzCallFBF] __init__")
		self.callScreen = None
		self.loggedIn = False
		self.Callback = None
		self.timestamp = 0
		self.callList = []
		self.callType = config.plugins.FritzCall.fbfCalls.value

	def notify(self, text):
		debug("[FritzCallFBF] notify")
		if self.callScreen:
			debug("[FritzCallFBF] notify: try to close callScreen")
			self.callScreen.close()
			self.callScreen = None
		Notifications.AddNotification(MessageBox, text, type=MessageBox.TYPE_ERROR, timeout=config.plugins.FritzCall.timeout.value)

	def errorLogin(self, error):
		text = _("FRITZ!Box Login failed! - Error: %s") % error
		self.notify(text)

	def _gotPageLogin(self, html):
#		debug("[FritzCallPhonebook] _gotPageLogin"
		# workaround: exceptions in gotPage-callback were ignored
		if self.callScreen:
			self.callScreen.updateStatus(_("Getting calls from FRITZ!Box...") + _("login verification"))
		try:
			debug("[FritzCallFBF] _gotPageLogin: verify login")
			found = re.match('.*<p class="errorMessage">FEHLER:&nbsp;Das angegebene Kennwort', html, re.S)
			if found:
				text = _("FRITZ!Box Login failed! - Wrong Password!")
				self.notify(text)
			else:
				if self.callScreen:
					self.callScreen.updateStatus(_("Getting calls from FRITZ!Box...") + _("login ok"))
				self.loggedIn = True
		except:
			import traceback, sys
			traceback.print_exc(file=sys.stdout)
			#raise e

	def login(self, callback=None):
		debug("[FritzCallFBF] Login")
		if config.plugins.FritzCall.password.value != "":
			if self.callScreen:
				self.callScreen.updateStatus(_("Getting calls from FRITZ!Box...") + _("login"))
			parms = "login:command/password=%s" % (config.plugins.FritzCall.password.value)
			url = "http://%s/cgi-bin/webcm" % (config.plugins.FritzCall.hostname.value)
			getPage(url,
				method="POST",
				headers={'Content-Type': "application/x-www-form-urlencoded", 'Content-Length': str(len(parms))
						}, postdata=parms).addCallback(self._gotPageLogin).addCallback(callback).addErrback(self.errorLogin)
		elif callback:
			callback()

	def errorLoad(self, error):
		text = _("Could not load phonebook from FRITZ!Box - Error: %s") % error
		self.notify(text)

	def _gotPageLoad(self, html):
		debug("[FritzCallFBF] _gotPageLoad")
		# workaround: exceptions in gotPage-callback were ignored
		try:
			self.parseFritzBoxPhonebook(html)
		except:
			import traceback, sys
			traceback.print_exc(file=sys.stdout)
			#raise e

	def loadFritzBoxPhonebook(self):
		debug("[FritzCallFBF] loadFritzBoxPhonebook")
		if config.plugins.FritzCall.fritzphonebook.value:
			debug("[FritzCallFBF] loadFritzBoxPhonebook: logging in")
			self.login(self._loadFritzBoxPhonebook)

	def _loadFritzBoxPhonebook(self, html=None):
			parms = urlencode({'getpage':'../html/de/menus/menu2.html', 'var:lang':'de', 'var:pagename':'fonbuch', 'var:menu':'fon'})
			url = "http://%s/cgi-bin/webcm?%s" % (config.plugins.FritzCall.hostname.value, parms)

			getPage(url).addCallback(self._gotPageLoad).addErrback(self.errorLoad)

	def parseFritzBoxPhonebook(self, html):
		debug("[FritzCallFBF] parseFritzBoxPhonebook")

		if re.search('TrFonName', html):
			#===============================================================================
			#				 New Style: 7170 / 7270 (FW 54.04.58, 54.04.63-11941)
			#							7141 (FW 40.04.68) 22.03.2009
			#							7170 (FW 29.04.70) 22.03.2009
			#							7270: (FW 54.04.70)
			#	We expect one line with TrFonName followed by several lines with
			#	TrFonNr(Type,Number,Shortcut,Vanity), which all belong to the name in TrFonName.
			#===============================================================================
			html = html2unicode(html.decode('utf-8')).encode('utf-8')
			entrymask = re.compile('(TrFonName\("[^"]+", "[^"]+", "[^"]*"\);.*?)TrFon1\(\)', re.S)
			entries = entrymask.finditer(html)
			for entry in entries:
				# debug(entry.group(1)
				# TrFonName (id, name, category)
				found = re.match('TrFonName\("[^"]*", "([^"]+)", "[^"]*"\);', entry.group(1))
				if found:
					name = found.group(1).strip().replace(',','')
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
		else:
			self.notify(_("Could not parse FRITZ!Box Phonebook entry"))

	def errorCalls(self, error):
		text = _("Could not load calls from FRITZ!Box - Error: %s") % error
		self.notify(text)

	def _gotPageCalls(self, csv=""):
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
			if self.callScreen:
				self.callScreen.updateStatus(_("Getting calls from FRITZ!Box...") + _("done"))
			# check for error: wrong password or password not set... TODO
			found = re.search('Melden Sie sich mit dem Kennwort der FRITZ!Box an', csv)
			if found:
				text = _("You need to set the password of the FRITZ!Box\nin the configuration dialog to display calls\n\nIt could be a communication issue, just try again.")
				# self.session.open(MessageBox, text, MessageBox.TYPE_ERROR, timeout=config.plugins.FritzCall.timeout.value)
				self.notify(text)
				return

			csv = csv.decode('iso-8859-1', 'replace').encode('utf-8', 'replace')
			lines = csv.splitlines()
			self.callList = lines
		elif self.callList:
			debug("[FritzCallFBF] _gotPageCalls: got no csv, but have callList")
			if self.callScreen:
				self.callScreen.updateStatus(_("Getting calls from FRITZ!Box...") + _("done, using last list"))
			lines = self.callList
		else:
			debug("[FritzCallFBF] _gotPageCalls: got no csv, no callList, leaving")
			return
			
		callList = []
		for line in lines:
			# debug(line
			# Typ;Datum;Name;Rufnummer;Nebenstelle;Eigene Rufnummer;Dauer
			found = re.match("^(" + self.callType + ");([^;]*);([^;]*);([^;]*);([^;]*);([^;]*)", line)
			if found:
				direct = found.group(1)
				date = found.group(2)
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
				callList.append((number, date, here, direct, remote))

		# debug("[FritzCallFBF] _gotPageCalls result:\n" + text

		if self.Callback is not None:
			# debug("[FritzCallFBF] _gotPageCalls call callback with\n" + text
			self.Callback(callList)
			self.Callback = None
		self.callScreen = None

	def getCalls(self, callScreen, callback, type):
		#
		# call sequence must be:
		# - login
		# - getPage -> _gotPageLogin
		# - loginCallback (_getCalls)
		# - getPage -> _getCalls1
		debug("[FritzCallFBF] getCalls")
		self.callScreen = callScreen
		self.callType = type
		self.Callback = callback
		if (time.time() - self.timestamp) > 180: 
			debug("[FritzCallFBF] getCalls: outdated data, login and get new ones")
			self.timestamp = time.time()
			self.login(self._getCalls)
		elif not self.callList:
			debug("[FritzCallFBF] getCalls: time is ok, but no callList")
			self._getCalls1()
		else:
			debug("[FritzCallFBF] getCalls: time is ok, callList is ok")
			self._gotPageCalls()

	def _getCalls(self, html=None):
		#
		# we need this to fill Anrufliste.csv
		# http://repeater1/cgi-bin/webcm?getpage=../html/de/menus/menu2.html&var:lang=de&var:menu=fon&var:pagename=foncalls
		#
		debug("[FritzCallFBF] _getCalls")
		if self.callScreen:
			self.callScreen.updateStatus(_("Getting calls from FRITZ!Box...") + _("preparing"))
		parms = urlencode({'getpage':'../html/de/menus/menu2.html', 'var:lang':'de', 'var:pagename':'foncalls', 'var:menu':'fon'})
		url = "http://%s/cgi-bin/webcm?%s" % (config.plugins.FritzCall.hostname.value, parms)
		getPage(url).addCallback(self._getCalls1).addErrback(self.errorCalls)

	def _getCalls1(self, html=""):
		#
		# finally we should have successfully lgged in and filled the csv
		#
		debug("[FritzCallFBF] _getCalls1")
		if self.callScreen:
			self.callScreen.updateStatus(_("Getting calls from FRITZ!Box...") + _("finishing"))
		parms = urlencode({'getpage':'../html/de/FRITZ!Box_Anrufliste.csv'})
		url = "http://%s/cgi-bin/webcm?%s" % (config.plugins.FritzCall.hostname.value, parms)
		getPage(url).addCallback(self._gotPageCalls).addErrback(self.errorCalls)

	def dial(self, number):
		''' initiate a call to number '''
		self.number = number
		self.login(self._dial)
		
	def _dial(self, html=None):
		url = "http://%s/cgi-bin/webcm" % config.plugins.FritzCall.hostname.value
		parms = urlencode({
			'getpage':'../html/de/menus/menu2.html',
			# 'id':'uiPostForm',
			# 'name':'uiPostForm',
			'login:command/password': config.plugins.FritzCall.password.value,
			'var:pagename':'fonbuch',
			'var:menu':'home',
			'telcfg:settings/UseClickToDial':'1',
			'telcfg:settings/DialPort':config.plugins.FritzCall.extension.value,
			'telcfg:command/Dial':self.number
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
		linkP = open("/tmp/FritzCallDialOK.htm", "w")
		linkP.write(html)
		linkP.close()

	def _errorDial(self, error):
		debug("[FritzCallFBF] errorDial: $s" % error)
		linkP = open("/tmp/FritzCallDialError.htm", "w")
		linkP.write(error)
		linkP.close()
		text = _("Dialling failed - Error: %s") % error
		self.notify(text)

	def hangup(self):
		''' hangup call on port; not used for now '''
		url = "http://%s/cgi-bin/webcm" % config.plugins.FritzCall.hostname.value
		parms = urlencode({
			#'getpage':'../html/de/menus/menu2.html',
			'id':'uiPostForm',
			'name':'uiPostForm',
			'login:command/password': config.plugins.FritzCall.password.value,
			#'var:pagename':'fonbuch',
			#'var:menu':'home',
			'telcfg:settings/UseClickToDial':'1',
			'telcfg:settings/DialPort':config.plugins.FritzCall.extension.value,
			'telcfg:command/Hangup':''
			})
		debug("[FritzCallFBF] hangup url: '" + url + "' parms: '" + parms + "'")
		getPage(url,
			method="POST",
			headers={
					'Content-Type': "application/x-www-form-urlencoded",
					'Content-Length': str(len(parms))},
			postdata=parms)

fritzbox = FritzCallFBF()


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
					<widget name="entries" position="%d,%d" size="%d,%d" scrollbarMode="showOnDemand" backgroundColor="#aaaaaa" transparent="1" />
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
							scaleV(22, 21), # statusbar font size
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
							scaleH(20, 5), scaleV(525, 395), scaleV(24, 21), # widget red
							scaleH(290, 145), scaleV(525, 395), scaleV(24, 21), # widget green
							scaleH(560, 285), scaleV(525, 395), scaleV(24, 21), # widget yellow
							scaleH(830, 425), scaleV(525, 395), scaleV(24, 21), # widget blue
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
			"yellow": self.displayAllCalls,
			"red": self.displayMissedCalls,
			"blue": self.displayInCalls,
			"green": self.displayOutCalls,
			"cancel": self.ok,
			"ok": self.showEntry, }, - 2)

		# TRANSLATORS: this is a help text, keep it short
		self.helpList.append((self["setupActions"], "OkCancelActions", [("ok", _("Show details of entry"))]))
		# TRANSLATORS: this is a help text, keep it short
		self.helpList.append((self["setupActions"], "OkCancelActions", [("cancel", _("Quit"))]))
		# TRANSLATORS: this is a help text, keep it short
		self.helpList.append((self["setupActions"], "ColorActions", [("yellow", _("Display all calls"))]))
		# TRANSLATORS: this is a help text, keep it short
		self.helpList.append((self["setupActions"], "ColorActions", [("red", _("Display missed calls"))]))
		# TRANSLATORS: this is a help text, keep it short
		self.helpList.append((self["setupActions"], "ColorActions", [("blue", _("Display incoming calls"))]))
		# TRANSLATORS: this is a help text, keep it short
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

	def displayAllCalls(self):
		debug("[FritzDisplayCalls] displayAllCalls")
		self.display(FBF_ALL_CALLS)

	def displayMissedCalls(self):
		debug("[FritzDisplayCalls] displayMissedCalls")
		self.display(FBF_MISSED_CALLS)

	def displayInCalls(self):
		debug("[FritzDisplayCalls] displayInCalls")
		self.display(FBF_IN_CALLS)

	def displayOutCalls(self):
		debug("[FritzDisplayCalls] displayOutCalls")
		self.display(FBF_OUT_CALLS)

	def display(self, which=config.plugins.FritzCall.fbfCalls.value):
		debug("[FritzDisplayCalls] display")
		config.plugins.FritzCall.fbfCalls.value = which
		config.plugins.FritzCall.fbfCalls.save()
		self.header = fbfCallsChoices[which]
		fritzbox.getCalls(self, self.gotCalls, which)

	def gotCalls(self, callList):
		debug("[FritzDisplayCalls] gotCalls")
		self.updateStatus(self.header + " (" + str(len(callList)) + ")")
		sortlist = []
		for (number, date, remote, direct, here) in callList:
			found = re.match("(\d\d.\d\d.)\d\d( \d\d:\d\d)", date)
			if found: date = found.group(1) + found.group(2)
			if direct == FBF_OUT_CALLS:
				dir = LoadPixmap(resolveFilename(SCOPE_PLUGINS, "Extensions/FritzCall/images/callout.png"))
			elif direct == FBF_IN_CALLS:
				dir = LoadPixmap(resolveFilename(SCOPE_PLUGINS, "Extensions/FritzCall/images/callin.png"))
			else:
				dir = LoadPixmap(resolveFilename(SCOPE_PLUGINS, "Extensions/FritzCall/images/callinfailed.png"))
			dateFieldWidth = scaleH(150,100)
			dirFieldWidth = 16
			remoteFieldWidth = scaleH(250,100)
			scrollbarWidth = scaleH(90,45)
			fieldWidth = self.width -dateFieldWidth -5 -dirFieldWidth -5 -remoteFieldWidth -scrollbarWidth -5
			# debug("[FritzDisplayCalls] gotCalls: d: %d; f: %d; d: %d; r: %d" %(dateFieldWidth, fieldWidth, dirFieldWidth, remoteFieldWidth))
			sortlist.append([number,
							 (eListboxPythonMultiContent.TYPE_TEXT, 0, 0, dateFieldWidth, scaleV(24,20), 0, RT_HALIGN_LEFT, date),
							 (eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, dateFieldWidth+5, 0, dirFieldWidth, 16, dir),
							 (eListboxPythonMultiContent.TYPE_TEXT, dateFieldWidth+5+dirFieldWidth+5, 0, fieldWidth, scaleV(24,20), 0, RT_HALIGN_LEFT, here),
							 (eListboxPythonMultiContent.TYPE_TEXT, dateFieldWidth+5+dirFieldWidth+5+fieldWidth+5, 0, remoteFieldWidth, scaleV(24,20), 0, RT_HALIGN_RIGHT, remote)
							 ])

		self["entries"].setList(sortlist)

	def updateStatus(self, text):
		self["statusbar"].setText(text)

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
	# TRANSLATORS: this is a window title. Avoid the use of non ascii chars
	width = 430 # = 5 + 3x140 + 5; 3 Buttons
	height = 176 # = 5 + 126 + 40 + 5; 6 lines of text possible
	skin = """
		<screen name="FritzOfferAction" position="%d,%d" size="%d,%d" title="%s" >
			<widget name="text" position="5,5" size="%d,%d" font="Regular;21" />
			<ePixmap position="5,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap position="145,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap position="285,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<widget name="key_red" position="5,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_green" position="145,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_yellow" position="285,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		</screen>""" % (
						(DESKTOP_WIDTH - width) / 2,
						(DESKTOP_HEIGHT - height) / 2,
						width,
						height,
						_("Do what?"),
						width - 10,
						height - 10 - 40,
						height - 5 - 40, height - 5 - 40, height - 5 - 40, height - 5 - 40, height - 5 - 40, height - 5 - 40 # Buttons
												) 

	def __init__(self, session, parent, number, name=""):
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
						<widget name="entries" position="%d,%d" size="%d,%d" scrollbarMode="showOnDemand" backgroundColor="#20040404" transparent="1" />
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
							scaleH(20, 5), scaleV(525, 395), scaleV(24, 21), # widget red
							scaleH(290, 145), scaleV(525, 395), scaleV(24, 21), # widget green
							scaleH(560, 285), scaleV(525, 395), scaleV(24, 21), # widget yellow
							scaleH(830, 425), scaleV(525, 395), scaleV(24, 21), # widget blue
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
	
			# TRANSLATORS: this is a help text, keep it short
			self.helpList.append((self["setupActions"], "OkCancelActions", [("ok", _("Show details of entry"))]))
			# TRANSLATORS: this is a help text, keep it short
			self.helpList.append((self["setupActions"], "OkCancelActions", [("cancel", _("Quit"))]))
			# TRANSLATORS: this is a help text, keep it short
			self.helpList.append((self["setupActions"], "ColorActions", [("red", _("Delete entry"))]))
			# TRANSLATORS: this is a help text, keep it short
			self.helpList.append((self["setupActions"], "ColorActions", [("green", _("Add entry to phonebook"))]))
			# TRANSLATORS: this is a help text, keep it short
			self.helpList.append((self["setupActions"], "ColorActions", [("yellow", _("Edit selected entry"))]))
			# TRANSLATORS: this is a help text, keep it short
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
				width = 570
				height = 100
				# TRANSLATORS: this is a window title. Avoid the use of non ascii chars
				skin = """
					<screen position="%d,%d" size="%d,%d" title="%s" >
					<widget name="config" position="5,5" size="%d,%d" scrollbarMode="showOnDemand" />
					<ePixmap position="145,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
					<ePixmap position="285,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
					<widget name="key_red" position="145,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
					<widget name="key_green" position="285,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
					</screen>""" % (
									(DESKTOP_WIDTH - width) / 2,
									(DESKTOP_HEIGHT - height) / 2,
									width,
									height,
									_("Add entry to phonebook"),
									width - 5 - 5,
									height - 5 - 40 - 5,
									height - 40 - 5, height - 40 - 5, height - 40 - 5, height - 40 - 5
																		 )
	
	
				def __init__(self, session, parent, number="", name=""):
					#
					# setup screen with two ConfigText and OK and ABORT button
					# 
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
				</screen>""" % (
							scaleH(90, 75), scaleV(100, 73), # position 
							scaleH(1100, 570), scaleV(560, 430), # size
							_("FritzCall Setup") + 
							" (" + "$Revision$"[1: - 1] + 
							"$Date$"[7:23] + ")",
							scaleH(1100, 570), # eLabel width
							scaleH(40, 20), scaleV(10, 5), # consideration position
							scaleH(1050, 530), scaleV(25, 45), # consideration size
							scaleV(22, 20), # consideration font size
							scaleV(40, 50), # eLabel position vertical
							scaleH(1100, 570), # eLabel width
							scaleH(40, 5), scaleV(60, 57), # config position
							scaleH(1040, 560), scaleV(453, 328), # config size
							scaleV(518, 390), # eLabel position vertical
							scaleH(1100, 570), # eLabel width
							scaleH(20, 5), scaleV(525, 395), # widget red
							scaleH(290, 145), scaleV(525, 395), # widget green
							scaleH(560, 285), scaleV(525, 395), # widget yellow
							scaleH(830, 425), scaleV(525, 395), # widget blue
							scaleH(20, 5), scaleV(525, 395), scaleV(24, 21), # widget red
							scaleH(290, 145), scaleV(525, 395), scaleV(24, 21), # widget green
							scaleH(560, 285), scaleV(525, 395), scaleV(24, 21), # widget yellow
							scaleH(830, 425), scaleV(525, 395), scaleV(24, 21), # widget blue
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

		self["setupActions"] = ActionMap(["SetupActions", "ColorActions", "MenuActions"],
		{
			"red": self.cancel,
			"green": self.save,
			"yellow": self.displayCalls,
			"blue": self.displayPhonebook,
			"cancel": self.cancel,
			"save": self.save,
			"ok": self.save,
			"menu": self.about,
			"info": self.about,
		}, - 2)

		# TRANSLATORS: this is a help text, keep it short
		self.helpList.append((self["setupActions"], "SetupActions", [("ok", _("save and quit"))]))
		# TRANSLATORS: this is a help text, keep it short
		self.helpList.append((self["setupActions"], "SetupActions", [("save", _("save and quit"))]))
		# TRANSLATORS: this is a help text, keep it short
		self.helpList.append((self["setupActions"], "SetupActions", [("cancel", _("quit"))]))
		# TRANSLATORS: this is a help text, keep it short
		self.helpList.append((self["setupActions"], "ColorActions", [("red", _("quit"))]))
		# TRANSLATORS: this is a help text, keep it short
		self.helpList.append((self["setupActions"], "ColorActions", [("green", _("save and quit"))]))
		# TRANSLATORS: this is a help text, keep it short
		self.helpList.append((self["setupActions"], "ColorActions", [("yellow", _("display calls"))]))
		# TRANSLATORS: this is a help text, keep it short
		self.helpList.append((self["setupActions"], "ColorActions", [("blue", _("display phonebook"))]))
		# TRANSLATORS: this is a help text, keep it short
		self.helpList.append((self["setupActions"], "MenuActions", [("info", _("About FritzCall"))]))
		# TRANSLATORS: this is a help text, keep it short
		self.helpList.append((self["setupActions"], "MenuActions", [("menu", _("About FritzCall"))]))

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
		if fritz_call is not None:
			fritz_call.connect()
			debug("[FritzCallSetup] called phonebook.reload()")
			phonebook.reload()
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

from GlobalActions import globalActionMap #@UnresolvedImport
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
			Standby.inStandby.onHide.append(callList.display)
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
		Notifications.AddNotification(MessageBox, _("Connected to FRITZ!Box!"), type=MessageBox.TYPE_INFO, timeout=4)
		self.resetDelay()
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
			initDebug()

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
	return [ PluginDescriptor(name="FritzCall", description=what, where=PluginDescriptor.WHERE_PLUGINMENU, icon="plugin.png", fnc=main),
		PluginDescriptor(name=what_calls, description=what_calls, where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=displayCalls),
		PluginDescriptor(name=what_phonebook, description=what_phonebook, where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=displayPhonebook),
		PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc=autostart) ]
