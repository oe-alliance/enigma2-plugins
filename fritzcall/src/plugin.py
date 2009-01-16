# -*- coding: utf-8 -*-
#===============================================================================
# $Author$
# $Revision$
# $Date$
#==============================
from Screens.Screen import Screen #@UnresolvedImport
from Screens.MessageBox import MessageBox #@UnresolvedImport
from Screens.NumericalTextInputHelpDialog import NumericalTextInputHelpDialog #@UnresolvedImport
from Screens.InputBox import InputBox #@UnresolvedImport
from Screens import Standby #@UnresolvedImport
from Screens.HelpMenu import HelpableScreen #@UnresolvedImport

from enigma import getDesktop #@UnresolvedImport
DESKTOP_WIDTH = getDesktop(0).size().width()
DESKTOP_HEIGHT = getDesktop(0).size().height()

from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT #@UnresolvedImport

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

from twisted.internet import reactor
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.protocols.basic import LineReceiver
from twisted.web.client import getPage

from urllib import urlencode 
import re, time, os

from nrzuname import ReverseLookupAndNotifier

import gettext
from Tools.Directories import resolveFilename, SCOPE_PLUGINS #@UnresolvedImport
try:
	_ = gettext.translation('FritzCall', resolveFilename(SCOPE_PLUGINS, "Extensions/FritzCall/locale"), [config.osd.language.getText()]).gettext
except IOError:
	pass


my_global_session = None

# TODO: debug config option and then debug(to defined debug file...
config.plugins.FritzCall = ConfigSubsection()
config.plugins.FritzCall.enable = ConfigEnableDisable(default = False)
config.plugins.FritzCall.muteOnCall = ConfigEnableDisable(default = False)
config.plugins.FritzCall.hostname = ConfigText(default = "fritz.box", fixed_size = False)
config.plugins.FritzCall.afterStandby = ConfigSelection(choices = [("none", _("show nothing")), ("inList", _("show as list")), ("each", _("show each call"))])
config.plugins.FritzCall.filter = ConfigEnableDisable(default = False)
config.plugins.FritzCall.filtermsn = ConfigText(default = "", fixed_size = False)
config.plugins.FritzCall.filtermsn.setUseableChars('0123456789,')
config.plugins.FritzCall.showOutgoing = ConfigEnableDisable(default = False)
config.plugins.FritzCall.timeout = ConfigInteger(default = 15, limits = (0,60))
config.plugins.FritzCall.lookup = ConfigEnableDisable(default = False)
config.plugins.FritzCall.internal = ConfigEnableDisable(default = False)
config.plugins.FritzCall.fritzphonebook = ConfigEnableDisable(default = False)
config.plugins.FritzCall.phonebook = ConfigEnableDisable(default = False)
config.plugins.FritzCall.addcallers = ConfigEnableDisable(default = False)
config.plugins.FritzCall.phonebookLocation = ConfigSelection(choices = [("/etc/enigma2/PhoneBook.txt", _("Flash")), ("/media/usb/PhoneBook.txt", _("USB Stick")), ("/media/cf/PhoneBook.txt", _("CF Drive")), ("/media/hdd/PhoneBook.txt", _("Harddisk"))])
config.plugins.FritzCall.password = ConfigPassword(default = "", fixed_size = False)
config.plugins.FritzCall.extension = ConfigText(default = '1', fixed_size = False)
config.plugins.FritzCall.extension.setUseableChars('0123456789')
config.plugins.FritzCall.showType = ConfigEnableDisable(default = True)
config.plugins.FritzCall.showShortcut = ConfigEnableDisable(default = False)
config.plugins.FritzCall.showVanity = ConfigEnableDisable(default = False)
config.plugins.FritzCall.prefix = ConfigText(default = "", fixed_size = False)
config.plugins.FritzCall.prefix.setUseableChars('0123456789')
config.plugins.FritzCall.fullscreen = ConfigEnableDisable(default = False)
config.plugins.FritzCall.debug = ConfigEnableDisable(default = False)

countryCodes = [
	("0049", _("Germany")),
	("0031", _("The Netherlands")),
	("0033", _("France")),
	("0039", _("Italy")),
	("0041", _("Switzerland")),
	("0043", _("Austria"))
	]
config.plugins.FritzCall.country = ConfigSelection(choices = countryCodes)

FBF_ALL_CALLS = "."
FBF_IN_CALLS = "1"
FBF_MISSED_CALLS = "2"
FBF_OUT_CALLS = "3"
fbfCallsChoices = {FBF_ALL_CALLS: _("All calls"),
				   FBF_IN_CALLS: _("Incoming calls"),
				   FBF_MISSED_CALLS: _("Missed calls"),
				   FBF_OUT_CALLS: _("Outgoing calls")
				   }
config.plugins.FritzCall.fbfCalls = ConfigSelection(choices = fbfCallsChoices)

config.plugins.FritzCall.name = ConfigText(default = "", fixed_size = False)
config.plugins.FritzCall.number= ConfigText(default = "", fixed_size = False)
config.plugins.FritzCall.number.setUseableChars('0123456789')

def initDebug():
	try:
		os.remove("/tmp/FritzDebug.log")
	except:
		pass

# from time import localtime()
def debug(message):
	# ltim = localtime()
	# headerstr = "%04d%02d%02d %02d:%02d " %(ltim[0],ltim[1],ltim[2],ltim[3],ltim[4])
	# message = headerstr + message
	if config.plugins.FritzCall.debug.value:
		deb = open("/tmp/FritzDebug.log", "aw")
		deb.write(message + "\n")
		deb.close()

def html2utf8(in_html):
	try:
		import htmlentitydefs

		# TODO: first convert some WML codes; does not work?!?!
		# in_html = in_html.replace("&#xDF;;", "ß").replace("&#xE4;", "ä").replace("&#xF6;", "ö").replace("&#xFC;", "ü").replace("&#xC4;", "Ä").replace("&#xD6;", "Ö").replace("&#xDC;", "Ü")

		htmlentitynamemask = re.compile('(&(\D{1,5}?);)')
		entitydict = {}
		entities = htmlentitynamemask.finditer(in_html)
		for x in entities:
			entitydict[x.group(1)] = x.group(2)
		for key, name in entitydict.items():
			try:
				entitydict[key] = htmlentitydefs.name2codepoint[name]
			except KeyError:
				debug("[FritzCallhtml2utf8] KeyError " + key + "/" + name)
				pass

		htmlentitynumbermask = re.compile('(&#(\d{1,5}?);)')
		entities = htmlentitynumbermask.finditer(in_html)
		for x in entities:
			entitydict[x.group(1)] = x.group(2)
		for key, codepoint in entitydict.items():
			try:
				in_html = in_html.replace(key, (unichr(int(codepoint)).encode('utf8', "replace")))
			except ValueError:
				debug( "[FritzCallhtml2utf8] ValueError " + key + "/" + str(codepoint))
				pass
	except ImportError:
		try:
			return in_html.replace("&amp;", "&").replace("&szlig;", "ß").replace("&auml;", "ä").replace("&ouml;", "ö").replace("&uuml;", "ü").replace("&Auml;", "Ä").replace("&Ouml;", "Ö").replace("&Uuml;", "Ü")
		except UnicodeDecodeError:
			pass
	return in_html


class FritzCallFBF:
	def __init__(self):
		debug("[FritzCallFBF] __init__")
		self.callScreen= None
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
		text = _("FRITZ!Box Login failed! - Error: %s") %error
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

	def login(self, callback = None):
		debug("[FritzCallFBF] Login")
		if config.plugins.FritzCall.password.value != "":
			if self.callScreen:
				self.callScreen.updateStatus(_("Getting calls from FRITZ!Box...") + _("login"))
			parms = "login:command/password=%s" %(config.plugins.FritzCall.password.value)
			url = "http://%s/cgi-bin/webcm" %(config.plugins.FritzCall.hostname.value)
			getPage(url,
				method="POST",
				headers = {'Content-Type': "application/x-www-form-urlencoded",'Content-Length': str(len(parms))
						}, postdata=parms).addCallback(self._gotPageLogin).addCallback(callback).addErrback(self.errorLogin)
		elif callback:
			callback()

	def errorLoad(self, error):
		text = _("Could not load phonebook from FRITZ!Box - Error: %s") %error
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
			parms = urlencode({'getpage':'../html/de/menus/menu2.html', 'var:lang':'de','var:pagename':'fonbuch','var:menu':'fon'})
			url = "http://%s/cgi-bin/webcm?%s" %(config.plugins.FritzCall.hostname.value, parms)

			getPage(url).addCallback(self._gotPageLoad).addErrback(self.errorLoad)

	def parseFritzBoxPhonebook(self, html):
		debug("[FritzCallFBF] parseFritzBoxPhonebook")

		table = html2utf8(html.replace("\xa0"," ").decode("ISO-8859-1", "replace"))
		if re.search('TrFonName', table):
			#===============================================================================
			#				 New Style: 7170 / 7270 (FW 54.04.58, 54.04.63-11941) 
			#	We expect one line with TrFonName followed by several lines with
			#	TrFonNr(Type,Number,Shortcut,Vanity), which all belong to the name in TrFonName.
			#===============================================================================
			# entrymask = re.compile('(TrFonName\("[^"]+", "[^"]+", "[^"]+"\);</SCRIPT>\s+[<SCRIPT type=text/javascript>TrFonNr\("[^"]+", "[^"]+", "[^"]+", "[^"]+"\);</SCRIPT>\s+]+)<SCRIPT type=text/javascript>document.write(TrFon1());</SCRIPT>', re.DOTALL)
			# entrymask = re.compile('(TrFonName\("[^"]+", "[^"]+", "[^"]+"\);.*?[.*?TrFonNr\("[^"]+", "[^"]+", "[^"]+", "[^"]+"\);.*?]+).*?document.write(TrFon1());', re.DOTALL)
			entrymask = re.compile('(TrFonName\("[^"]+", "[^"]+", "[^"]*"\);.*?)TrFon1\(\)', re.S)
			entries = entrymask.finditer(html)
			for entry in entries:
				# debug(entry.group(1)
				found = re.match('TrFonName\("[^"]*", "([^"]+)", "[^"]*"\);', entry.group(1))
				if found:
					name = found.group(1)
				else:
					continue
				detailmask = re.compile('TrFonNr\("([^"]*)", "([^"]*)", "([^"]*)", "([^"]*)"\);', re.S)
				details = detailmask.finditer(entry.group(1))
				for found in details:
					thisname = name

					type = found.group(1)
					if config.plugins.FritzCall.showType.value:
						if type == "mobile":
							thisname = thisname + " (" +_("mobile") + ")"
						elif type == "home":
							thisname = thisname + " (" +_("home") + ")"
						elif type == "work":
							thisname = thisname + " (" +_("work") + ")"

					if config.plugins.FritzCall.showShortcut.value and found.group(3):
						thisname = thisname + ", " + _("Shortcut") + ": " + found.group(3)
					if config.plugins.FritzCall.showVanity.value and found.group(4):
						thisname = thisname + ", " + _("Vanity") + ": " + found.group(4)

					thisnumber = found.group(2).strip()
					thisname = html2utf8(thisname.strip())
					if thisnumber:
						debug("[FritzCallFBF] Adding '''%s''' with '''%s''' from FRITZ!Box Phonebook!" %(thisname, thisnumber))
						phonebook.phonebook[thisnumber] = thisname
					else:
						debug("[FritzCallFBF] ignoring empty number for %s" %thisname)
					continue

		elif re.search('TrFon', table):
			#===============================================================================
			#				Old Style: 7050 (FW 14.04.33)
			#	We expect one line with TrFon(No,Name,Number,Shortcut,Vanity)
			#===============================================================================				
			entrymask = re.compile('TrFon\("[^"]*", "([^"]*)", "([^"]*)", "([^"]*)", "([^"]*)"\)', re.S)
			entries = entrymask.finditer(html)
			for found in entries:
				name = found.group(1).strip()
				thisnumber = found.group(2).strip()
				if config.plugins.FritzCall.showShortcut.value and found.group(3):
					name = name + ", " + _("Shortcut") + ": " + found.group(3)
				if config.plugins.FritzCall.showVanity.value and found.group(4):
					name = name + ", " +_("Vanity") +": " + found.group(4)
				if thisnumber:
					name = html2utf8(name)
					debug("[FritzCallFBF] Adding '''%s''' with '''%s''' from FRITZ!Box Phonebook!" %(name, thisnumber))
					phonebook.phonebook[thisnumber] = name
				else:
					debug("[FritzCallFBF] ignoring empty number for %s" %name)
				continue
		else:
			self.notify(_("Could not parse FRITZ!Box Phonebook entry"))

	def errorCalls(self, error):
		text = _("Could not load calls from FRITZ!Box - Error: %s") %error
		self.notify(text)

	def _gotPageCalls(self, csv = ""):
		def _resolveNumber(number):
			if number.isdigit():
				if config.plugins.FritzCall.internal.value and len(number) > 3 and number[0]=="0": number = number[1:]
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

			csv = csv.decode('iso-8859-1','replace').encode('utf-8','replace')
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
		parms = urlencode({'getpage':'../html/de/menus/menu2.html', 'var:lang':'de','var:pagename':'foncalls','var:menu':'fon'})
		url = "http://%s/cgi-bin/webcm?%s" %(config.plugins.FritzCall.hostname.value, parms)
		getPage(url).addCallback(self._getCalls1).addErrback(self.errorCalls)

	def _getCalls1(self, html = ""):
		#
		# finally we should have successfully lgged in and filled the csv
		#
		debug("[FritzCallFBF] _getCalls1")
		if self.callScreen:
			self.callScreen.updateStatus(_("Getting calls from FRITZ!Box...") + _("finishing"))
		parms = urlencode({'getpage':'../html/de/FRITZ!Box_Anrufliste.csv'})
		url = "http://%s/cgi-bin/webcm?%s" %(config.plugins.FritzCall.hostname.value, parms)
		getPage(url).addCallback(self._gotPageCalls).addErrback(self.errorCalls)

	def dial(self, number):
		''' initiate a call to number '''
		self.number = number
		self.login(self._dial)
		
	def _dial(self, html=None):
		url = "http://%s/cgi-bin/webcm" %config.plugins.FritzCall.hostname.value
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
			headers = {
					'Content-Type': "application/x-www-form-urlencoded",
					'Content-Length': str(len(parms))},
			postdata=parms).addCallback(self._okDial).addErrback(self._errorDial)

	def _okDial(self, html):
		debug("[FritzCallFBF] okDial")
		linkP =  open("/tmp/FritzCallDialOK.htm", "w")
		linkP.write(html)
		linkP.close()

	def _errorDial(self, error):
		debug("[FritzCallFBF] errorDial: $s" %error)
		linkP =  open("/tmp/FritzCallDialError.htm", "w")
		linkP.write(error)
		linkP.close()
		text = _("Dialling failed - Error: %s") %error
		self.notify(text)

	def hangup(self):
		''' hangup call on port; not used for now '''
		url = "http://%s/cgi-bin/webcm" %config.plugins.FritzCall.hostname.value
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
			headers = {
					'Content-Type': "application/x-www-form-urlencoded",
					'Content-Length': str(len(parms))},
			postdata=parms)


fritzbox = FritzCallFBF()

class FritzDisplayCalls(Screen, HelpableScreen):


	def __init__(self, session, text = ""):
		if config.plugins.FritzCall.fullscreen.value:
			self.width = DESKTOP_WIDTH
			self.height = DESKTOP_HEIGHT
			width = self.width
			height = self.height
			# TRANSLATORS: this is a window title. Avoid the use of non ascii chars
			self.skin = """
				<screen name="FritzDisplayCalls" position="0,0" size="%d,%d"	title="%s" flags="wfNoBorder">
					<widget source="global.CurrentTime" render="Label" position="%d,40" size="80,26" font="Regular;26" halign="right" backgroundColor="#0b67a2" transparent="1">
						<convert type="ClockToText">Default</convert>
					</widget>
					<widget source="global.CurrentTime" render="Label" position="%d,70" size="310,22" font="Regular;20" halign="right" backgroundColor="#0b67a2" transparent="1">
						<convert type="ClockToText">Date</convert>
					</widget>
					<eLabel text="%s" position="%d,63" size="330,30" font="Regular;27" halign="center" backgroundColor="#0b67a2" transparent="1"/>
					<widget name="statusbar" position="%d,%d"  size="%d,%d" 	font="Regular;22" backgroundColor="#353e575e" transparent="1" />
					<widget name="entries" position="%d,%d" size="%d,%d" scrollbarMode="showOnDemand" transparent="1" />
					<ePixmap pixmap="skin_default/buttons/red.png" 		position="%d,%d" 	size="21,21" alphatest="on" />
					<ePixmap pixmap="skin_default/buttons/green.png" 	position="%d,%d" 	size="21,21" alphatest="on" />
					<ePixmap pixmap="skin_default/buttons/yellow.png" 	position="%d,%d" 	size="21,21" alphatest="on" />
					<ePixmap pixmap="skin_default/buttons/blue.png" 	position="%d,%d" 	size="21,21" alphatest="on" />
					<widget name="key_red" 		position="%d,%d" 		size="160,22" zPosition="1" font="Regular;20" halign="left" backgroundColor="black" transparent="1" />
					<widget name="key_green" 	position="%d,%d" 		size="160,22" zPosition="1" font="Regular;20" halign="left" backgroundColor="black" transparent="1" />
					<widget name="key_yellow" 	position="%d,%d" 		size="160,22" zPosition="1" font="Regular;20" halign="left" backgroundColor="black" transparent="1" />
					<widget name="key_blue" 	position="%d,%d" 	size="160,22" zPosition="1" font="Regular;20" halign="left" backgroundColor="black" transparent="1" />
					<ePixmap position="%d,%d" size="%d,%d" zPosition="2" pixmap="%s" transparent="1" alphatest="blend" />		
				</screen>""" % (
							width, height, _("Phone calls"),
							width -150,
							width -380,
							"FritzCall " + _("Phone calls"), width * 20 / 1280, # Label
							width * 80 / 1280,	height * 150 / 720, # statusbar position
							width * 250 / 1280, height * 200 / 720, # statusbar size
							width * 420 / 1280,	height * 120 / 720, # entries position
							width * 790 / 1280, height * 438 / 720, # entries size
							25, height * 600 / 720, # red
							25 + ((width-25)/4), height * 600 / 720, # green
							25 + ((width-25)/4)*2, height * 600 / 720, # yellow
							25 + ((width-25)/4)*3, height * 600 / 720, # blue
							25+25,	height * 600 / 720, # red
							25+25+((width-25)/4), height * 600 / 720, # green
							25+25+((width-25)/4)*2,	height * 600 / 720, # yellow
							25+25+((width-25)/4)*3,	height * 600 / 720, # blue
							width * 50 / 1280,	height * 430 / 720, # Fritz Logo position
							# width * 150 / 1280,	height * 110 / 720, # Fritz Logo size
							150, 110, resolveFilename(SCOPE_PLUGINS, "Extensions/FritzCall/fritz.png") # Fritz Logo size and pixmap
							)
		else:
			width = DESKTOP_WIDTH -150
			height = DESKTOP_HEIGHT -156
			self.width = width
			self.height = height
			# TRANSLATORS: this is a window title. Avoid the use of non ascii chars
			self.skin = """
				<screen name="FritzDisplayCalls" position="%d,%d" size="%d,%d" title="%s" >
					<widget name="statusbar" position="0,0" size="%d,22" font="Regular;21" />
					<widget name="entries" position="0,22" size="%d,%d" scrollbarMode="showOnDemand" />
					<ePixmap position="5,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
					<ePixmap position="145,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
					<ePixmap position="285,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
					<ePixmap position="425,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
					<widget name="key_red" position="5,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
					<widget name="key_green" position="145,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
					<widget name="key_yellow" position="285,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
					<widget name="key_blue" position="425,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				</screen>""" % (
							(DESKTOP_WIDTH - width) / 2,
							(DESKTOP_HEIGHT - height) / 2,
							width,
							height,
							_("Phone calls"),
							width,
							width,
							height - 22 - 40,
							height -40, height -40, height -40, height -40,
							height -40, height -40, height -40, height -40
							)

		Screen.__init__(self, session)
		HelpableScreen.__init__(self)

		# TRANSLATORS: keep it short, this is a button
		self["key_red"] = Button(_("All"))
		# TRANSLATORS: keep it short, this is a button
		self["key_green"] = Button(_("Missed"))
		# TRANSLATORS: keep it short, this is a button
		self["key_yellow"] = Button(_("Incoming"))
		# TRANSLATORS: keep it short, this is a button
		self["key_blue"] = Button(_("Outgoing"))

		self["setupActions"] = ActionMap(["OkCancelActions", "ColorActions"],
		{
			"red": self.displayAllCalls,
			"green": self.displayMissedCalls,
			"yellow": self.displayInCalls,
			"blue": self.displayOutCalls,
			"cancel": self.ok,
			"ok": self.showEntry,}, -2)

		# TRANSLATORS: this is a help text, keep it short
		self.helpList.append((self["setupActions"], "OkCancelActions", [("ok", _("Show details of entry"))]))
		# TRANSLATORS: this is a help text, keep it short
		self.helpList.append((self["setupActions"], "OkCancelActions", [("cancel", _("Quit"))]))
		# TRANSLATORS: this is a help text, keep it short
		self.helpList.append((self["setupActions"], "ColorActions", [("red", _("Display all calls"))]))
		# TRANSLATORS: this is a help text, keep it short
		self.helpList.append((self["setupActions"], "ColorActions", [("green", _("Display missed calls"))]))
		# TRANSLATORS: this is a help text, keep it short
		self.helpList.append((self["setupActions"], "ColorActions", [("yellow", _("Display incoming calls"))]))
		# TRANSLATORS: this is a help text, keep it short
		self.helpList.append((self["setupActions"], "ColorActions", [("blue", _("Display outgoing calls"))]))

		self["statusbar"] = Label(_("Getting calls from FRITZ!Box..."))
		self["entries"] = MenuList([], True, content = eListboxPythonMultiContent)
		if DESKTOP_WIDTH >= 1280:
			self["entries"].l.setFont(0, gFont("Console", 22))
			self["entries"].l.setItemHeight(24)
		else:
			self["entries"].l.setFont(0, gFont("Console", 16))
			self["entries"].l.setItemHeight(20)

		debug("[FritzDisplayCalls] init: '''%s'''" %config.plugins.FritzCall.fbfCalls.value)
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
		# TODO: colculate number of chars, we can display
		if DESKTOP_WIDTH >= 1280:
			noChars = 60
		else:
			noChars = 40
		for (number, date, remote, direct, here) in callList:
			while (len(remote) + len(here)) > noChars:
				if len(remote) > len(here):
					remote = remote[:-1]
				else:
					here = here[:-1]
			found = re.match("(\d\d.\d\d.)\d\d( \d\d:\d\d)", date)
			if found: date = found.group(1) + found.group(2)
			if direct == FBF_OUT_CALLS:
				message = date + " " + remote + " -> " + here
			else:
				message = date + " " + here + " -> " + remote
			sortlist.append([number, (eListboxPythonMultiContent.TYPE_TEXT, 0, 0, self.width-10, 20, 0, RT_HALIGN_LEFT, message)])
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
						  type = MessageBox.TYPE_INFO)


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
						width -10,
						height -10 -40,
						height -5 -40, height -5 -40, height -5 -40, height -5 -40, height -5 -40, height -5 -40 # Buttons
						) 

	def __init__(self, session, parent, number, name = ""):
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
			"ok": self.exit,}, -2)

		self["text"] = Label(number + "\n\n" + name.replace(", ","\n"))
		self.actualNumber = number
		self.actualName = name
		self.parent = parent

	def lookup(self):
		ReverseLookupAndNotifier(self.actualNumber, self.lookedUp, "UTF-8", config.plugins.FritzCall.country.value)

	def lookedUp(self, number, name):
		self.actualNumber = number
		self.actualName = name
		self["text"].setText(number + "\n\n" + name.replace(", ","\n"))

	def call(self):
		fritzbox.dial(self.actualNumber)
		self.exit()

	def add(self):
		phonebook.FritzDisplayPhonebook(self.session).add(self.parent, self.actualNumber, self.actualName)
		self.exit()

	def exit(self):
		self.close()


class FritzCallPhonebook:
	def __init__(self):
		self.phonebook = {}
		self.reload()

	def reload(self):
		debug("[FritzCallPhonebook] reload")
		self.phonebook = {}

		if not config.plugins.FritzCall.enable.value:
			return

		if config.plugins.FritzCall.phonebook.value and os.path.exists(config.plugins.FritzCall.phonebookLocation.value):
			phonebookTxtCorrupt = False
			for line in open(config.plugins.FritzCall.phonebookLocation.value):
				if re.match("^\d+#.*$", line):
					try:
						number, name = line.split("#")
						if not self.phonebook.has_key(number):
							self.phonebook[number] = name
					except ValueError: # how could this possibly happen?!?!
						debug("[FritzCallPhonebook] Could not parse internal Phonebook Entry %s" %line)
						phonebookTxtCorrupt = True
				else:
					debug("[FritzCallPhonebook] Could not parse internal Phonebook Entry %s" %line)
					phonebookTxtCorrupt = True

			if phonebookTxtCorrupt:
				# dump phonebook to PhoneBook.txt
				debug("[FritzCallPhonebook] dump Phonebook.txt")
				os.rename(config.plugins.FritzCall.phonebookLocation.value,
						config.plugins.FritzCall.phonebookLocation.value + ".bck")
				fNew = open(config.plugins.FritzCall.phonebookLocation.value, 'w')
				for (number, name) in self.phonebook.iteritems():
					fNew.write(number + "#" + name)
				fNew.close()

		if config.plugins.FritzCall.fritzphonebook.value:
			fritzbox.loadFritzBoxPhonebook()

	def search(self, number):
		# debug("[FritzCallPhonebook] Searching for %s" %number
		name = None
		if config.plugins.FritzCall.phonebook.value or config.plugins.FritzCall.fritzphonebook.value:
			if self.phonebook.has_key(number):
				name = self.phonebook[number].replace(", ", "\n").strip()
		return name

	def add(self, number, name):
		debug("[FritzCallPhonebook] add")
		#===============================================================================
		#		It could happen, that two reverseLookups are running in parallel,
		#		so check first, whether we have already added the number to the phonebook.
		#===============================================================================
		name = name.replace("\n", ", ") # this is just for safety reasons. add should only be called with newlines converted into commas
		self.phonebook[number] = name;
		if number and number <> 0 and config.plugins.FritzCall.addcallers.value:
			if config.plugins.FritzCall.phonebook.value:
				try:
					f = open(config.plugins.FritzCall.phonebookLocation.value, 'a')
					name = name.strip() + "\n"
					string = "%s#%s" %(number, name)
					f.write(string)
					f.close()
					debug("[FritzCallPhonebook] added %s with %s to Phonebook.txt" %(number, name))
					return True
	
				except IOError:
					return False

	def remove(self, number):
		debug("[FritzCallPhonebook] remove")
		if number in self.phonebook:
			debug("[FritzCallPhonebook] remove entry in phonebook")
			del self.phonebook[number]
			if config.plugins.FritzCall.phonebook.value:
				try:
					debug("[FritzCallPhonebook] remove entry in Phonebook.txt")
					fOld = open(config.plugins.FritzCall.phonebookLocation.value, 'r')
					fNew = open(config.plugins.FritzCall.phonebookLocation.value + str(os.getpid()), 'w')
					line = fOld.readline()
					while (line):
						if not re.match("^"+number+"#.*$", line):
							fNew.write(line)
						line = fOld.readline()
					fOld.close()
					fNew.close()
					os.remove(config.plugins.FritzCall.phonebookLocation.value)
					os.rename(config.plugins.FritzCall.phonebookLocation.value + str(os.getpid()),
							config.plugins.FritzCall.phonebookLocation.value)
					debug("[FritzCallPhonebook] removed %s from Phonebook.txt" %number)
					return True
	
				except IOError:
					pass
		return False

	class FritzDisplayPhonebook(Screen, HelpableScreen, NumericalTextInput):

		def __init__(self, session):
			if config.plugins.FritzCall.fullscreen.value:
				self.width = DESKTOP_WIDTH
				self.height = DESKTOP_HEIGHT
				width = self.width
				height = self.height
				# TRANSLATORS: this is a window title. Avoid the use of non ascii chars
				self.skin = """
					<screen name="FritzDisplayPhonebook" position="0,0" size="%d,%d" title="%s" flags="wfNoBorder">
						<widget source="global.CurrentTime" render="Label" position="%d,40" size="80,26" font="Regular;26" halign="right" backgroundColor="#0b67a2" transparent="1">
							<convert type="ClockToText">Default</convert>
						</widget>
						<widget source="global.CurrentTime" render="Label" position="%d,70" size="310,22" font="Regular;20" halign="right" backgroundColor="#0b67a2" transparent="1">
							<convert type="ClockToText">Date</convert>
						</widget>
						<eLabel text="%s" position="%d,63" 	size="300,30" font="Regular;27" halign="center" backgroundColor="#0b67a2" transparent="1"/>
	
						<widget name="entries" 	position="%d,%d" size="%d,%d" 	scrollbarMode="showOnDemand" transparent="1" />
	
						<ePixmap pixmap="skin_default/buttons/red.png" 		position="%d,%d" 	size="21,21" alphatest="on" />
						<ePixmap pixmap="skin_default/buttons/green.png" 	position="%d,%d" 	size="21,21" alphatest="on" />
						<ePixmap pixmap="skin_default/buttons/yellow.png" 	position="%d,%d" 	size="21,21" alphatest="on" />
						<ePixmap pixmap="skin_default/buttons/blue.png" 	position="%d,%d" 	size="21,21" alphatest="on" />
						<widget name="key_red" 	position="%d,%d" 	size="160,22" zPosition="1" font="Regular;20" halign="left" backgroundColor="black" transparent="1" />
						<widget name="key_green" 	position="%d,%d" 	size="160,22" zPosition="1" font="Regular;20" halign="left" backgroundColor="black" transparent="1" />
						<widget name="key_yellow" 	position="%d,%d" 	size="160,22" zPosition="1" font="Regular;20" halign="left" backgroundColor="black" transparent="1" />
						<widget name="key_blue" 	position="%d,%d" 	size="160,22" zPosition="1" font="Regular;20" halign="left" backgroundColor="black" transparent="1" />
						<ePixmap position="%d,%d" size="%d,%d" zPosition="2" pixmap="%s" transparent="1" alphatest="blend" />	
					</screen>""" % (
								width, height, _("Phonebook"),
								width -150,
								width -380,
								"FritzCall " + _("Phonebook"), width * 20 / 1280, # Label
								width * 420 / 1280,	height * 120 / 720, # entries position
								width * 790 / 1280, height * 438 / 720, # entries size
								25, height * 600 / 720, # red
								25 + ((width-25)/4), height * 600 / 720, # green
								25 + ((width-25)/4)*2, height * 600 / 720, # yellow
								25 + ((width-25)/4)*3, height * 600 / 720, # blue
								25+25,	height * 600 / 720, # red
								25+25+((width-25)/4), height * 600 / 720, # green
								25+25+((width-25)/4)*2,	height * 600 / 720, # yellow
								25+25+((width-25)/4)*3,	height * 600 / 720, # blue
								width * 50 / 1280,	height * 430 / 720, # Fritz Logo position
								# width * 150 / 1280,	height * 110 / 720, # Fritz Logo size
								150, 110, resolveFilename(SCOPE_PLUGINS, "Extensions/FritzCall/fritz.png") # Fritz Logo size and pixmap
								)
			else:
				self.width = DESKTOP_WIDTH -150 # 5 + 4x140 + 5
				self.height = DESKTOP_HEIGHT -146 # 5 + ??? + 5 + 40 + 5
				width = self.width
				height = self.height
				# TRANSLATORS: this is a window title. Avoid the use of non ascii chars
				self.skin = """
					<screen name="FritzDisplayPhonebook" position="%d,%d" size="%d,%d" title="%s" >
						<widget name="entries" position="5,5" size="%d,%d" scrollbarMode="showOnDemand" />
						<ePixmap position="5,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
						<ePixmap position="145,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
						<ePixmap position="285,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
						<ePixmap position="425,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
						<widget name="key_red" position="5,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
						<widget name="key_green" position="145,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
						<widget name="key_yellow" position="285,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
						<widget name="key_blue" position="425,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
					</screen>""" % (
								(DESKTOP_WIDTH - width) / 2,
								(DESKTOP_HEIGHT - height) / 2,
								width,
								height,
								_("Phonebook"),
								width -5 -5, height -5 -40 -5, # entries size
								height -5 -40, height -5 -40, height -5 -40, height -5 -40, # Pixmaps
								height -5 -40, height -5 -40, height -5 -40, height -5 -40  # Buttons
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
				"ok": self.showEntry,}, -2)

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

			self["entries"] = MenuList([], True, content = eListboxPythonMultiContent)
			if DESKTOP_WIDTH >= 1280:
				self["entries"].l.setFont(0, gFont("Console", 22))
				self["entries"].l.setItemHeight(24)
			else:
				self["entries"].l.setFont(0, gFont("Console", 16))
				self["entries"].l.setItemHeight(20)
			debug("[FritzCallPhonebook] displayPhonebook init")
			self.display()

		def display(self, filter=""):
			debug("[FritzCallPhonebook] displayPhonebook/display")
			self.sortlist = []
			sortlistHelp = sorted((name.lower(), name, number) for (number, name) in phonebook.phonebook.iteritems())
			for (low, name, number) in sortlistHelp:
				if number == "01234567890":
					continue
				try:
					low = low.decode("utf-8")
					if filter:
						filter = filter.lower()
						if low.find(filter) == -1:
							continue
					name = name.strip().decode("utf-8")
					number = number.strip().decode("utf-8")
					found = re.match("([^,]*),.*", name)   # strip address information from the name part
					if found:
						shortname = found.group(1)
					else:
						shortname = name
					# TODO: colculate number of chars, we can display
					if DESKTOP_WIDTH >= 1280:
						if len(shortname) > 40:
							shortname = shortname[:40]
						message = u"%-40s  %-18s" %(shortname, number)
					else:
						if len(shortname) > 35:
							shortname = shortname[:35]
						message = u"%-35s  %-18s" %(shortname, number)
					message = message.encode("utf-8")
					# debug("[FritzCallPhonebook] displayPhonebook/display: add " + message
					self.sortlist.append([(number.encode("utf-8","replace"),
								   name.encode("utf-8","replace")),
								   (eListboxPythonMultiContent.TYPE_TEXT, 0, 0, self.width-10, 20, 0, RT_HALIGN_LEFT, message)])
				except UnicodeDecodeError:  # this should definitely not happen
					debug("[FritzCallPhonebook] displayPhonebook/display: corrupt phonebook entry for %s" %number)
					# self.session.open(MessageBox, _("Corrupt phonebook entry\nfor number %s\nDeleting.") %number, type = MessageBox.TYPE_ERROR)
					phonebook.remove(number)
					continue
				
			self["entries"].setList(self.sortlist)

		def showEntry(self):
			cur = self["entries"].getCurrent()
			if cur and cur[0]:
				debug("[FritzCallPhonebook] displayPhonebook/showEntry (%s,%s)" % (cur[0][0],cur[0][1]))
				number = cur[0][0]
				name = phonebook.search(number).replace('\n',', ')
				self.session.open(FritzOfferAction, self, number, name)

		def delete(self):
			cur = self["entries"].getCurrent()
			if cur and cur[0]:
				debug("[FritzCallPhonebook] displayPhonebook/delete " + cur[0][0])
				self.session.openWithCallback(
					self.deleteConfirmed,
					MessageBox,
					_("Do you really want to delete entry for\n\n%(number)s\n\n%(name)s?") 
					% { 'number':str(cur[0][0]), 'name':str(cur[0][1]).replace(", ","\n") }
				)
			else:
				self.session.open(MessageBox,_("No entry selected"), MessageBox.TYPE_INFO)

		def deleteConfirmed(self, ret):
			debug("[FritzCallPhonebook] displayPhonebook/deleteConfirmed")
			#
			# if ret: delete number from sortlist, delete number from phonebook.phonebook and write it to disk
			#
			cur = self["entries"].getCurrent()
			if cur:
				if ret:
					# delete number from sortlist, delete number from phonebook.phonebook and write it to disk
					debug("[FritzCallPhonebook] displayPhonebook/deleteConfirmed: remove " +cur[0][0])
					phonebook.remove(cur[0][0])
					self.display()
				# else:
					# self.session.open(MessageBox, _("Not deleted."), MessageBox.TYPE_INFO)
			else:
				self.session.open(MessageBox,_("No entry selected"), MessageBox.TYPE_INFO)

		def add(self, parent = None, number = "", name=""):
			class addScreen(Screen, ConfigListScreen):
				'''ConfiglistScreen with two ConfigTexts for Name and Number'''
				width = 570
				height = 75
				# TRANSLATORS: this is a window title. Avoid the use of non ascii chars
				skin = """
					<screen position="%d,%d" size="%d,%d" title="%s" >
					<widget name="config" position="5,5" size="%d,%d" scrollbarMode="showOnDemand" />
					<ePixmap position="145,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
					<ePixmap position="285,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
					<widget name="key_red" position="145,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
					<widget name="key_green" position="285,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
					</screen>"""  % (
									(DESKTOP_WIDTH - width) / 2,
									(DESKTOP_HEIGHT - height) / 2,
									width,
									height,
									_("Add entry to phonebook"),
									width -5 -5,
									height -5 -40 -5,
									height -40 -5, height -40 -5, height -40 -5, height -40 -5
									 )


				def __init__(self, session, parent, number = "", name = ""):
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
					}, -2)

					self.list = [ ]
					ConfigListScreen.__init__(self, self.list, session = session)
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
						self.session.open(MessageBox, _("Entry incomplete."), type = MessageBox.TYPE_ERROR)
						return
					# add (number,name) to sortlist and phonebook.phonebook and disk
					oldname = phonebook.search(self.number)
					if oldname:
						self.session.openWithCallback(
							self.overwriteConfirmed,
							MessageBox,
							_("Do you really want to overwrite entry for %(number)s\n\n%(name)s\n\nwith\n\n%(newname)s?")
							% {
							'number':self.number,
							'name': oldname,
							'newname':self.name.replace(", ","\n")
							}
							)
						self.close()
						return
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
				self.session.open(MessageBox,_("No entry selected"), MessageBox.TYPE_INFO)
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

	def __init__(self, session, args = None):
		if config.plugins.FritzCall.fullscreen.value:
			self.width = DESKTOP_WIDTH
			self.height = DESKTOP_HEIGHT
			width = self.width
			height = self.height
			# TRANSLATORS: this is a window title. Avoid the use of non ascii chars
			self.skin = """
				<screen name="FritzCallSetup" position="0,0" size="%d,%d" title="%s" flags="wfNoBorder">
					<widget source="global.CurrentTime" render="Label" position="%d,40" size="80,26" font="Regular;26" halign="right" backgroundColor="#0b67a2" transparent="1">
						<convert type="ClockToText">Default</convert>
					</widget>
					<widget source="global.CurrentTime" render="Label" position="%d,70" size="310,22" font="Regular;20" halign="right" backgroundColor="#0b67a2" transparent="1">
						<convert type="ClockToText">Date</convert>
					</widget>
					<eLabel text="%s" position="%d,63" size="330,30" font="Regular;27" halign="center" backgroundColor="#0b67a2" transparent="1"/>
			
					<widget name="consideration" position="%d,%d" size="%d,%d" font="Regular;22" halign="center" backgroundColor="#353e575e" transparent="1" />
					<widget name="config" position="%d,%d" size="%d,%d" scrollbarMode="showOnDemand" transparent="1" />
			
					<ePixmap pixmap="skin_default/buttons/red.png" 		position="%d,%d" 	size="21,21" alphatest="on" />
					<ePixmap pixmap="skin_default/buttons/green.png" 	position="%d,%d" 	size="21,21" alphatest="on" />
					<ePixmap pixmap="skin_default/buttons/yellow.png" 	position="%d,%d" 	size="21,21" alphatest="on" />
					<ePixmap pixmap="skin_default/buttons/blue.png" 	position="%d,%d" 	size="21,21" alphatest="on" />
					<widget name="key_red" 	position="%d,%d" 	size="160,22" zPosition="1" font="Regular;20" halign="left" backgroundColor="black" transparent="1" />
					<widget name="key_green" 	position="%d,%d" 	size="160,22" zPosition="1" font="Regular;20" halign="left" backgroundColor="black" transparent="1" />
					<widget name="key_yellow" 	position="%d,%d" 	size="160,22" zPosition="1" font="Regular;20" halign="left" backgroundColor="black" transparent="1" />
					<widget name="key_blue" 	position="%d,%d" 	size="160,22" zPosition="1" font="Regular;20" halign="left" backgroundColor="black" transparent="1" />
					<ePixmap position="%d,%d" size="%d,%d" zPosition="2" pixmap="%s" transparent="1" alphatest="blend" />		
				</screen>""" % (
								width, height, # size
								_("FritzCall Setup"),
								width -150,
								width -380,
								_("FritzCall Setup"), width * 20 / 1280, # Label
								width * 50 / 1280, height * 150 / 720, # consideration position
								width * 250 / 1280,	height * 250 / 720, # consideration size
								width * 300 / 1280,	height * 120 / 720, # config position
								width * 950 / 1280, height * 438 / 720, # config size
								25, height * 600 / 720, # red
								25 + ((width-25)/4), height * 600 / 720, # green
								25 + ((width-25)/4)*2, height * 600 / 720, # yellow
								25 + ((width-25)/4)*3, height * 600 / 720, # blue
								25+25,	height * 600 / 720, # red
								25+25+((width-25)/4), height * 600 / 720, # green
								25+25+((width-25)/4)*2,	height * 600 / 720, # yellow
								25+25+((width-25)/4)*3,	height * 600 / 720, # blue
								width * 50 / 1280,	height * 430 / 720, # Fritz Logo position
								# width * 150 / 1280,	height * 110 / 720, # Fritz Logo size
								150, 110, resolveFilename(SCOPE_PLUGINS, "Extensions/FritzCall/fritz.png") # Fritz Logo size and pixmap
								) 
		else:
			self.width = DESKTOP_WIDTH -150 # = 5 + 4x140 + 5
			self.height = DESKTOP_HEIGHT -146 # = 5 + 330 + 50 + 40 + 5
			width = self.width
			height = self.height
			# TRANSLATORS: this is a window title. Avoid the use of non ascii chars
			self.skin = """
				<screen name="FritzCallSetup" position="%d,%d" size="%d,%d" title="%s" >
				<widget name="config" position="5,5" size="%d,%d" scrollbarMode="showOnDemand" />
				<widget name="consideration" position="20,%d" font="Regular;20" halign="center" size="%d,50" />
				<ePixmap position="5,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
				<ePixmap position="145,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
				<ePixmap position="285,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
				<ePixmap position="425,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
				<widget name="key_red" position="5,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_green" position="145,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_yellow" position="285,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_blue" position="425,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				</screen>""" % (
							(DESKTOP_WIDTH - width) / 2,
							(DESKTOP_HEIGHT - height) / 2,
							width,
							height,
							_("FritzCall Setup"),
							width -5 -5,
							height -5 -5 -50 -5 -40 -5,
							height -50 -5 -40 -5,
							width -20 -20,
							height -40 -5, height -40 -5, height -40 -5, height -40 -5,
							height -40 -5, height -40 -5, height -40 -5, height -40 -5
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

		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"red": self.cancel,
			"green": self.save,
			"yellow": self.displayCalls,
			"blue": self.displayPhonebook,
			"cancel": self.cancel,
			"save": self.save,
			"ok": self.save,
		}, -2)

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

		ConfigListScreen.__init__(self, self.list, session = session)
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
			# TODO: self.list.append(getConfigListEntry(_("Full screen display"), config.plugins.FritzCall.fullscreen))
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
					caller = caller[:-1]
				else:
					phone = phone[:-1]

			text = text + "%s %s %s %s\n" %(date, caller, direction, phone)

		debug("[FritzCallList] display: '%s %s %s %s'" %(date, caller, direction, phone))
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
		debug("[FritzCall] notifyCall:\n%s" %text)
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
		debug("[FritzReverseLookupAndNotifier] reverse Lookup for %s!" %number)
		self.event = event
		self.number = number
		self.caller = caller
		self.phone = phone
		self.date = date

		if number[0] != "0":
			self.notifyAndReset()
			return

		ReverseLookupAndNotifier(number, self.notifyAndReset, "UTF-8", config.plugins.FritzCall.country.value)

	def notifyAndReset(self, number, caller):
		'''
		
		this gets called with the result of the reverse lookup
		
		@param number: number
		@param caller: name and address of remote. it comes in with name, address and city separated by commas
		'''
		debug("[FritzReverseLookupAndNotifier] got: " + caller)
		if caller:
			self.caller = caller.replace(", ", "\n")
			if self.number != 0 and config.plugins.FritzCall.addcallers.value and self.event == "RING":
				debug("[FritzReverseLookupAndNotifier] add to phonebook")
				phonebook.add(self.number, self.caller.replace("\n", ", "))
		else:
			self.caller = _("UNKNOWN")
		notifyCall(self.event, self.date, self.number, self.caller, self.phone)
		# kill that object...


class FritzProtocol(LineReceiver):
	def __init__(self):
		debug("[FritzProtocol] __init__")
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
		debug("[FritzProtocol] lineReceived: %s" %line)
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
					self.phone = "%s (%s)" %(phone, phonename)
				else:
					self.phone = phone

				if config.plugins.FritzCall.internal.value and len(number) > 3 and number[0]=="0":
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
					debug("[FritzProtocol] lineReceived phonebook.search: %s" %self.number)
					self.caller = phonebook.search(self.number)
					debug("[FritzProtocol] lineReceived phonebook.search reault: %s" %self.caller)
					if (self.caller is None) and config.plugins.FritzCall.lookup.value:
						FritzReverseLookupAndNotifier(self.event, self.number, self.caller, self.phone, self.date)
						return							# reverselookup is supposed to handle the message itself 

				if self.caller is None:
					self.caller = _("UNKNOWN")

				self.notifyAndReset()

class FritzClientFactory(ReconnectingClientFactory):
	initialDelay = 20
	maxDelay = 500

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

def displayCalls(session, servicelist):
	session.open(FritzDisplayCalls)

def displayPhonebook(session, servicelist):
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
	return [ PluginDescriptor(name="FritzCall", description=what, where = PluginDescriptor.WHERE_PLUGINMENU, icon = "plugin.png", fnc=main),
		PluginDescriptor(name=what_calls, description=what_calls, where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=displayCalls),
		PluginDescriptor(name=what_phonebook, description=what_phonebook, where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=displayPhonebook),
		PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc = autostart) ]
