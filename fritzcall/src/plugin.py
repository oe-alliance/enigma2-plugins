# -*- coding: utf-8 -*-
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.NumericalTextInputHelpDialog import NumericalTextInputHelpDialog
from Screens.InputBox import InputBox
from Screens import Standby
from Screens.HelpMenu import HelpableScreen

from enigma import eListboxPythonMultiContent, gFont, RT_HALIGN_LEFT

from Components.MenuList import MenuList
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Button import Button
from Components.config import config, ConfigSubsection, ConfigSelection, ConfigIP, ConfigEnableDisable, getConfigListEntry, ConfigText, ConfigInteger
from Components.ConfigList import ConfigListScreen
from Components.ScrollLabel import ScrollLabel

from Plugins.Plugin import PluginDescriptor
from Tools import Notifications
from Tools.NumericalTextInput import NumericalTextInput

from twisted.internet import reactor
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.protocols.basic import LineReceiver
from twisted.web.client import getPage

from xml.dom.minidom import parse

from urllib import urlencode 
import re, time, os

import gettext
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
try:
	_ = gettext.translation('FritzCall', resolveFilename(SCOPE_PLUGINS, "Extensions/FritzCall/locale"), [config.osd.language.getText()]).gettext
except IOError:
	pass


my_global_session = None

config.plugins.FritzCall = ConfigSubsection()
config.plugins.FritzCall.enable = ConfigEnableDisable(default = False)
config.plugins.FritzCall.hostname = ConfigIP(default = [192, 168, 178, 1])
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
config.plugins.FritzCall.password = ConfigText(default = "", fixed_size = False)
config.plugins.FritzCall.showType = ConfigEnableDisable(default = True)
config.plugins.FritzCall.showShortcut = ConfigEnableDisable(default = False)
config.plugins.FritzCall.showVanity = ConfigEnableDisable(default = False)
config.plugins.FritzCall.prefix = ConfigText(default = "", fixed_size = False)
config.plugins.FritzCall.prefix.setUseableChars('0123456789')

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


def html2utf8(in_html):
	try:
		import htmlentitydefs
		htmlentitynumbermask = re.compile('(&#(\d{1,5}?);)')
		htmlentitynamemask = re.compile('(&(\D{1,5}?);)')
		entities = htmlentitynamemask.finditer(in_html)
		entitydict = {}
		for x in entities:
			entitydict[x.group(1)] = x.group(2)
		for key, name in entitydict.items():
			try:
				entitydict[key] = htmlentitydefs.name2codepoint[name]
			except KeyError:
				pass
		entities = htmlentitynumbermask.finditer(in_html)
		for x in entities:
			entitydict[x.group(1)] = x.group(2)
		for key, codepoint in entitydict.items():
			try:
				in_html = in_html.replace(key, (unichr(int(codepoint)).encode('utf8', "replace")))
			except ValueError:
				pass
	except ImportError:
		return in_html.replace("&amp;", "&").replace("&szlig;", "ß").replace("&auml;", "ä").replace("&ouml;", "ö").replace("&uuml;", "ü").replace("&Auml;", "Ä").replace("&Ouml;", "Ö").replace("&Uuml;", "Ü")
	return in_html


class FritzCallFBF:
	def __init__(self):
		print "[FritzCallFBF] __init__"
		self.callScreen= None
		self.loggedIn = False
		self.Callback = None
		self.loginCallback = None
		self.timestamp = 0
		self.callList = []
		self.callType = config.plugins.FritzCall.fbfCalls.value

	def notify(self, text):
		print "[FritzCallFBF] notify"
		if self.callScreen:
			print "[FritzCallFBF] notify: try to close callScreen"
			self.callScreen.close()
			self.callScreen = None
		Notifications.AddNotification(MessageBox, text, type=MessageBox.TYPE_ERROR, timeout=config.plugins.FritzCall.timeout.value)

	def errorLogin(self, error):
		text = _("FRITZ!Box Login failed! - Error: %s") %error
		self.notify(text)

	def _gotPageLogin(self, html):
#		print "[FritzCallPhonebook] _gotPageLogin"
		# workaround: exceptions in gotPage-callback were ignored
		if self.callScreen:
			self.callScreen.updateStatus(_("Getting calls from FRITZ!Box...") + _("login verification"))
		try:
			print "[FritzCallFBF] _gotPageLogin: verify login"
			found = re.match('.*<p class="errorMessage">FEHLER:&nbsp;Das angegebene Kennwort', html, re.S)
			if found:
				text = _("FRITZ!Box Login failed! - Wrong Password!")
				self.notify(text)
			else:
				if self.callScreen:
					self.callScreen.updateStatus(_("Getting calls from FRITZ!Box...") + _("login ok"))
				self.loggedIn = True
				self.loginCallback()
			loginCallback = None
		except:
			import traceback, sys
			traceback.print_exc(file=sys.stdout)
			#raise e

	def login(self):
		print "[FritzCallFBF] Login"
		if config.plugins.FritzCall.password.value != "":
			if self.callScreen:
				self.callScreen.updateStatus(_("Getting calls from FRITZ!Box...") + _("login"))
			host = "%d.%d.%d.%d" %tuple(config.plugins.FritzCall.hostname.value)
			uri =  "/cgi-bin/webcm"
			parms = "login:command/password=%s" %(config.plugins.FritzCall.password.value)
			url = "http://%s%s" %(host, uri)
			getPage(url, method="POST", headers = {'Content-Type': "application/x-www-form-urlencoded",'Content-Length': str(len(parms))}, postdata=parms).addCallback(self._gotPageLogin).addErrback(self.errorLogin)
		else:
			self.loginCallback()
			self.loginCallback = None

	def errorLoad(self, error):
		text = _("Could not load phonebook from FRITZ!Box - Error: %s") %error
		self.notify(text)

	def _gotPageLoad(self, html):
		print "[FritzCallFBF] _gotPageLoad"
		# workaround: exceptions in gotPage-callback were ignored
		try:
			self.parseFritzBoxPhonebook(html)
		except:
			import traceback, sys
			traceback.print_exc(file=sys.stdout)
			#raise e

	def loadFritzBoxPhonebook(self):
		print "[FritzCallFBF] loadFritzBoxPhonebook"
		if config.plugins.FritzCall.fritzphonebook.value:
			print "[FritzCallFBF] loadFritzBoxPhonebook: logging in"
			self.loginCallback = self._loadFritzBoxPhonebook
			self.login()

	def _loadFritzBoxPhonebook(self):
			host = "%d.%d.%d.%d" %tuple(config.plugins.FritzCall.hostname.value)
			uri = "/cgi-bin/webcm"# % tuple(config.plugins.FritzCall.hostname.value)
			parms = urlencode({'getpage':'../html/de/menus/menu2.html', 'var:lang':'de','var:pagename':'fonbuch','var:menu':'fon'})
			url = "http://%s%s?%s" %(host, uri, parms)

			getPage(url).addCallback(self._gotPageLoad).addErrback(self.errorLoad)

	def parseFritzBoxPhonebook(self, html):
		print "[FritzCallFBF] parseFritzBoxPhonebook"

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
				# print entry.group(1)
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
						print "[FritzCallFBF] Adding '''%s''' with '''%s''' from FRITZ!Box Phonebook!" %(thisname, thisnumber)
						phonebook.phonebook[thisnumber] = thisname
					else:
						print "[FritzCallFBF] ignoring empty number for %s" %thisname
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
					print "[FritzCallFBF] Adding '''%s''' with '''%s''' from FRITZ!Box Phonebook!" %(name, thisnumber)
					phonebook.phonebook[thisnumber] = name
				else:
					print "[FritzCallFBF] ignoring empty number for %s" %name
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
			print "[FritzCallFBF] _gotPageCalls: got csv, setting callList"
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
			print "[FritzCallFBF] _gotPageCalls: got no csv, but have callList"
			if self.callScreen:
				self.callScreen.updateStatus(_("Getting calls from FRITZ!Box...") + _("done, using last list"))
			lines = self.callList
		else:
			print "[FritzCallFBF] _gotPageCalls: got no csv, no callList, leaving"
			return
			
		callList = []
		for line in lines:
			# print line
			# Typ;Datum;Name;Rufnummer;Nebenstelle;Eigene Rufnummer;Dauer
			found = re.match("^(" + self.callType + ");([^;]*);([^;]*);([^;]*);([^;]*);([^;]*)", line)
			if found:
				direct = found.group(1)
				date = found.group(2)
				if direct != FBF_OUT_CALLS and found.group(3):
					remote = found.group(3)
				else:
					remote = _resolveNumber(found.group(4))
				found1 = re.match('Internet: (.*)', found.group(6))
				if found1:
					here = _resolveNumber(found1.group(1))
				else:
					here = _resolveNumber(found.group(6))
				callList.append((found.group(4), date, here, direct, remote))

		# print "[FritzCallFBF] _gotPageCalls result:\n" + text

		if self.Callback is not None:
			# print "[FritzCallFBF] _gotPageCalls call callback with\n" + text
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
		print "[FritzCallFBF] getCalls"
		self.callScreen = callScreen
		self.callType = type
		self.Callback = callback
		if (time.time() - self.timestamp) > 180: 
			print "[FritzCallFBF] getCalls: outdated data, login and get new ones"
			self.timestamp = time.time()
			self.loginCallback = self._getCalls
			self.login()
		elif not self.callList:
			print "[FritzCallFBF] getCalls: time is ok, but no callList"
			self._getCalls1()
		else:
			print "[FritzCallFBF] getCalls: time is ok, callList is ok"
			self._gotPageCalls()

	def _getCalls(self):
		#
		# we need this to fill Anrufliste.csv
		# http://repeater1/cgi-bin/webcm?getpage=../html/de/menus/menu2.html&var:lang=de&var:menu=fon&var:pagename=foncalls
		#
		print "[FritzCallFBF] _getCalls"
		if self.callScreen:
			self.callScreen.updateStatus(_("Getting calls from FRITZ!Box...") + _("preparing"))
		host = "%d.%d.%d.%d" %tuple(config.plugins.FritzCall.hostname.value)
		parms = urlencode({'getpage':'../html/de/menus/menu2.html', 'var:lang':'de','var:pagename':'foncalls','var:menu':'fon'})
		url = "http://%s/cgi-bin/webcm?%s" %(host, parms)
		getPage(url).addCallback(self._getCalls1).addErrback(self.errorCalls)

	def _getCalls1(self, html = ""):
		#
		# finally we should have successfully lgged in and filled the csv
		#
		print "[FritzCallFBF] _getCalls1"
		if self.callScreen:
			self.callScreen.updateStatus(_("Getting calls from FRITZ!Box...") + _("finishing"))
		host = "%d.%d.%d.%d" %tuple(config.plugins.FritzCall.hostname.value)
		parms = urlencode({'getpage':'../html/de/FRITZ!Box_Anrufliste.csv'})
		url = "http://%s/cgi-bin/webcm?%s" %(host, parms)
		getPage(url).addCallback(self._gotPageCalls).addErrback(self.errorCalls)

	def dial(self, number):
		''' initiate a call to number '''
		#
		# does not work... if anybody wants to make it work, feel free
		# I not convinced of FBF's style to establish a connection: first get the connection, then ring the local phone?!?!
		#  
		return
		# http://fritz.box/cgi-bin/webcm
		# getpage=../html/de/menus/menu2.html
		# var:lang=de
		# var:pagename=foncalls
		# var:menu=home
		# var:pagemaster=
		# var:showsetup=
		# var:showall=
		# var:showDialing=08001235005
		# telcfg:settings/UseJournal=1
		# telcfg:command/Dial=08001235005
		self.login()
		url = "http://%s/cgi-bin/webcm" %("%d.%d.%d.%d" %tuple(config.plugins.FritzCall.hostname.value))
		parms = urlencode({
			'getpage':'../html/de/menus/menu2.html',
			'errorpage':'../html/de/menus/menu2.html',
			'var:lang':'de',
			'var:pagename':'foncalls',
			'var:errorpagename':'foncalls',
			'var:menu':'home',
			'var:pagemaster':'',
			'var:settings/time':'0,0',
			'var:showsetup':'',
			'var:showall':'',
			'var:showDialing':number,
			'var:tabFoncall':'',
			'var:TestPort':'',
			'var:kurzwahl':'',
			'var:kwCode':'',
			'var:kwVanity':'',
			'var:kwNumber':'',
			'var:kwName':'',
			'telcfg:settings/UseJournal':'1',
			'telcfg:command/Dial':number
			})
		print "[FritzCallFBF] dial url: '" + url + "' parms: '" + parms + "'"
		getPage(url, method="POST", headers = {'Content-Type': "application/x-www-form-urlencoded",'Content-Length': str(len(parms))}, postdata=parms)



fritzbox = FritzCallFBF()

class FritzDisplayCalls(Screen, HelpableScreen):

	# TRANSLATORS: this is a window title. Avoid the use of non ascii chars
	skin = """
		<screen name="FritzDisplayCalls" position="100,90" size="570,420" title="%s" >
			<widget name="statusbar" position="0,0" size="570,22" font="Regular;21" />
			<widget name="entries" position="0,22" size="570,358" scrollbarMode="showOnDemand" />
			<ePixmap position="5,375" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
			<ePixmap position="145,375" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
			<ePixmap position="285,375" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
			<ePixmap position="425,375" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
			<widget name="key_red" position="5,375" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_green" position="145,375" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_yellow" position="285,375" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_blue" position="425,375" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		</screen>""" % _("Phone calls")

	def __init__(self, session, text = ""):
		self.skin = FritzDisplayCalls.skin
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
		self["entries"].l.setFont(0, gFont("Console", 16))
		self["entries"].l.setItemHeight(20)

		print "[FritzDisplayCalls] init: '''%s'''" %config.plugins.FritzCall.fbfCalls.value
		self.displayCalls()

	def ok(self):
		self.close()

	def displayAllCalls(self):
		print "[FritzDisplayCalls] displayAllCalls"
		config.plugins.FritzCall.fbfCalls.value = FBF_ALL_CALLS
		config.plugins.FritzCall.fbfCalls.save()
		self.displayCalls()

	def displayMissedCalls(self):
		print "[FritzDisplayCalls] displayMissedCalls"
		config.plugins.FritzCall.fbfCalls.value = FBF_MISSED_CALLS
		config.plugins.FritzCall.fbfCalls.save()
		self.displayCalls()

	def displayInCalls(self):
		print "[FritzDisplayCalls] displayInCalls"
		config.plugins.FritzCall.fbfCalls.value = FBF_IN_CALLS
		config.plugins.FritzCall.fbfCalls.save()
		self.displayCalls()

	def displayOutCalls(self):
		print "[FritzDisplayCalls] displayOutCalls"
		config.plugins.FritzCall.fbfCalls.value = FBF_OUT_CALLS
		config.plugins.FritzCall.fbfCalls.save()
		self.displayCalls()

	def displayCalls(self):
		print "[FritzDisplayCalls] displayCalls"
		self.header = fbfCallsChoices[config.plugins.FritzCall.fbfCalls.value]
		fritzbox.getCalls(self, self.gotCalls, config.plugins.FritzCall.fbfCalls.value)

	def gotCalls(self, callList):
		print "[FritzDisplayCalls] gotCalls"
		self.updateStatus(self.header + " (" + str(len(callList)) + ")")
		sortlist = []
		for (number, date, remote, direct, here) in callList:
			while (len(remote) + len(here)) > 40:
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
			sortlist.append([number, (eListboxPythonMultiContent.TYPE_TEXT, 0, 0, 560, 20, 0, RT_HALIGN_LEFT, message)])
		self["entries"].setList(sortlist)

	def showEntry(self):
		print "[FritzDisplayCalls] showEntry"
		cur = self["entries"].getCurrent()
		if cur:
			print "[FritzDisplayCalls] showEntry %s" % (cur[0])
			if cur[0]:
				fullname = phonebook.search(cur[0])
				if fullname:
					self.session.open(MessageBox,
							  cur[0] + "\n\n" + fullname.replace(", ","\n"),
							  type = MessageBox.TYPE_INFO)
				else:
					self.session.open(MessageBox,
							  cur[0],
							  type = MessageBox.TYPE_INFO)
			else:
				self.session.open(MessageBox,
						  _("UNKNOWN"),
						  type = MessageBox.TYPE_INFO)

	def updateStatus(self, text):
		self["statusbar"].setText(text)


class FritzCallPhonebook:
	def __init__(self):
		self.phonebook = {}
		self.reload()

	def create(self):
		try:
			f = open(config.plugins.FritzCall.phonebookLocation.value, 'w')
			f.write("01234567890#Name, Street, Location (Keep the Spaces!!!)\n");
			f.close()
			return True
		except IOError:
			Notifications.AddNotification(MessageBox, _("Can't create PhoneBook.txt"), type=MessageBox.TYPE_INFO, timeout=config.plugins.FritzCall.timeout.value)
			return False

	def reload(self):
		print "[FritzCallPhonebook] reload"
		self.phonebook = {}

		if not config.plugins.FritzCall.enable.value:
			return

		exists = False
		
		if config.plugins.FritzCall.phonebook.value:
			if not os.path.exists(config.plugins.FritzCall.phonebookLocation.value):
				if(self.create()):
					exists = True
			else:
				exists = True
	
			if exists:
				for line in open(config.plugins.FritzCall.phonebookLocation.value):
					try:
						number, name = line.split("#")
						if not self.phonebook.has_key(number):
							self.phonebook[number] = name
					except ValueError:
						print "[FritzCallPhonebook] Could not parse internal Phonebook Entry %s" %line

		if config.plugins.FritzCall.fritzphonebook.value:
			fritzbox.loadFritzBoxPhonebook()

	def search(self, number):
		# print "[FritzCallPhonebook] Searching for %s" %number
		name = None
		if config.plugins.FritzCall.phonebook.value or config.plugins.FritzCall.fritzphonebook.value:
			if self.phonebook.has_key(number):
				name = self.phonebook[number].replace(", ", "\n").strip()
		return name

	def add(self, number, name):
		print "[FritzCallPhonebook] add"
		#===============================================================================
		#		It could happen, that two reverseLookups are running in parallel,
		#		so check first, whether we have already added the number to the phonebook.
		#===============================================================================
		self.phonebook[number] = name;
		if number <> 0 and config.plugins.FritzCall.phonebook.value and config.plugins.FritzCall.addcallers.value:
			try:
				f = open(config.plugins.FritzCall.phonebookLocation.value, 'a')
				name = name.strip() + "\n"
				string = "%s#%s" %(number, name)
				f.write(string)
				f.close()
				print "[FritzCallPhonebook] added %s with %sto Phonebook.txt" %(number, name)
				return True

			except IOError:
				return False

	def remove(self, number):
		print "[FritzCallPhonebook] remove"
		if number in self.phonebook:
			print "[FritzCallPhonebook] remove entry in phonebook"
			del self.phonebook[number]
			if config.plugins.FritzCall.phonebook.value and config.plugins.FritzCall.addcallers.value:
				try:
					print "[FritzCallPhonebook] remove entry in Phonebook.txt"
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
					print "[FritzCallPhonebook] removed %s from Phonebook.txt" %number
					return True
	
				except IOError:
					pass
		return False

	class displayPhonebook(Screen, HelpableScreen, NumericalTextInput):
		# TRANSLATORS: this is a window title. Avoid the use of non ascii chars
		skin = """
			<screen name="FritzDisplayPhonebook" position="100,90" size="570,420" title="%s" >
				<widget name="entries" position="5,5" size="560,370" scrollbarMode="showOnDemand" />
				<ePixmap position="5,375" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
				<ePixmap position="145,375" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
				<ePixmap position="285,375" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
				<ePixmap position="425,375" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
				<widget name="key_red" position="5,375" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_green" position="145,375" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_yellow" position="285,375" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_blue" position="425,375" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			</screen>""" % _("Phonebook")

		def __init__(self, session):
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
			self["entries"].l.setFont(0, gFont("Console", 16))
			self["entries"].l.setItemHeight(20)
			print "[FritzCallPhonebook] displayPhonebook init"
			self.display()

		def display(self, filter=""):
			print "[FritzCallPhonebook] displayPhonebook/display"
			self.sortlist = []
			sortlistHelp = sorted((name.lower(), name, number) for (number, name) in phonebook.phonebook.iteritems())
			for (low, name, number) in sortlistHelp:
				if number == "01234567890":
					continue
				low = low.decode("utf-8")
				if filter:
					filter = filter.lower()
					if low.find(filter) == -1:
						continue
				name = name.strip().decode("utf-8")
				number = number.strip().decode("utf-8")
				found = re.match("([^,]*),.*", name)
				if found:
					shortname = found.group(1)
				if len(name) > 35:
					shortname = name[:35]
				else:
					shortname = name
				message = u"%-35s  %-18s" %(shortname, number)
				message = message.encode("utf-8")
				# print "[FritzCallPhonebook] displayPhonebook/display: add " + message
				self.sortlist.append([(number.encode("utf-8","replace"),
							   name.encode("utf-8","replace")),
							   (eListboxPythonMultiContent.TYPE_TEXT, 0, 0, 560, 20, 0, RT_HALIGN_LEFT, message)])

			self["entries"].setList(self.sortlist)

		def showEntry(self):
			cur = self["entries"].getCurrent()
			print "[FritzCallPhonebook] displayPhonebook/showEntry (%s,%s)" % (cur[0][0],cur[0][1])
			if cur:
				fullname = phonebook.search(cur[0][0])
				if fullname:
					self.session.open(MessageBox,
							  cur[0][0] + "\n\n" + fullname.replace(", ","\n"),
							  type = MessageBox.TYPE_INFO)
				else:
					self.session.open(MessageBox,
							  cur[0][0],
							  type = MessageBox.TYPE_INFO)

		def delete(self):
			cur = self["entries"].getCurrent()
			print "[FritzCallPhonebook] displayPhonebook/delete " + cur[0][0]
			if cur:
				self.session.openWithCallback(
					self.deleteConfirmed,
					MessageBox,
					_("Do you really want to delete entry for\n\n%(number)s\n\n%(name)s?") 
					% { 'number':str(cur[0][0]), 'name':str(cur[0][1]).replace(", ","\n") }
				)
			else:
				self.session.open(MessageBox,_("No entry selected"), MessageBox.TYPE_INFO)

		def deleteConfirmed(self, ret):
			print "[FritzCallPhonebook] displayPhonebook/deleteConfirmed"
			#
			# if ret: delete number from sortlist, delete number from phonebook.phonebook and write it to disk
			#
			cur = self["entries"].getCurrent()
			if cur:
				if ret:
					# delete number from sortlist, delete number from phonebook.phonebook and write it to disk
					print "[FritzCallPhonebook] displayPhonebook/deleteConfirmed: remove " +cur[0][0]
					phonebook.remove(cur[0][0])
					self.display()
				# else:
					# self.session.open(MessageBox, _("Not deleted."), MessageBox.TYPE_INFO)
			else:
				self.session.open(MessageBox,_("No entry selected"), MessageBox.TYPE_INFO)

		def add(self):
			class addScreen(Screen, ConfigListScreen):
				'''ConfiglistScreen with two ConfigTexts for Name and Number'''
				# TRANSLATORS: this is a window title. Avoid the use of non ascii chars
				skin = """
					<screen position="100,150" size="570,130" title="%s" >
					<widget name="config" position="5,5" size="560,75" scrollbarMode="showOnDemand" />
					<ePixmap position="145,85" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
					<ePixmap position="285,85" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
					<widget name="key_red" position="145,85" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
					<widget name="key_green" position="285,85" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
					</screen>"""  % _("Add entry to phonebook")

				def __init__(self, session, parent):
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
					config.plugins.FritzCall.name.value = ""
					config.plugins.FritzCall.number.value = ""
					self.list.append(getConfigListEntry(_("Name"), config.plugins.FritzCall.name))
					self.list.append(getConfigListEntry(_("Number"), config.plugins.FritzCall.number))
					self["config"].list = self.list
					self["config"].l.setList(self.list)


				def add(self):
					# get texts from Screen
					# add (number,name) to sortlist and phonebook.phonebook and disk
					self.number = config.plugins.FritzCall.number.value
					self.name = config.plugins.FritzCall.name.value
					# add (number,name) to sortlist and phonebook.phonebook and disk
					oldname = phonebook.search(self.number)
					if oldname:
						self.session.openWithCallback(
							self.overwriteConfirmed,
							MessageBox,
							_("Do you really want to overwrite entry for\n%(number)s\n\n%(name)s\n\nwith\n\n%(newname)s?")
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
						phonebook.add(self.number, self.name)
						self.parent.display()
					self.close()

				def cancel(self):
					self.close()

			print "[FritzCallPhonebook] displayPhonebook/add"
			# self.session.open(MessageBox, "Not yet implemented.", type = MessageBox.TYPE_INFO)
			# return
			self.session.open(addScreen, self)

		def edit(self):
			# Edit selected Timer
			class editScreen(Screen, ConfigListScreen):
				'''ConfiglistScreen with two ConfigTexts for Name and Number'''
				# TRANSLATORS: this is a window title. Avoid the use of non ascii chars
				skin = """
					<screen position="100,150" size="570,130" title="%s" >
					<widget name="config" position="5,5" size="560,75" scrollbarMode="showOnDemand" />
					<ePixmap position="145,85" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
					<ePixmap position="285,85" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
					<widget name="key_red" position="145,85" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
					<widget name="key_green" position="285,85" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
					</screen>""" % _("Edit phonebook entry").decode("utf-8")

				def __init__(self, session, parent, name, number):
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
						"green": self.edit,
						"ok": self.edit,
					}, -2)

					self.list = [ ]
					ConfigListScreen.__init__(self, self.list, session = session)
					# config.plugins.FritzCall.name.value = config.plugins.FritzCall.name.value.replace(", ","\n")
					self.name = name
					self.number = number
					config.plugins.FritzCall.name.value = name
					config.plugins.FritzCall.number.value = number
					self.list.append(getConfigListEntry(_("Name"), config.plugins.FritzCall.name))
					self.list.append(getConfigListEntry(_("Number"), config.plugins.FritzCall.number))
					self["config"].list = self.list
					self["config"].l.setList(self.list)


				def edit(self):
					print "[FritzCallPhonebook] displayPhonebook/edit: add (%s,%s)" %(config.plugins.FritzCall.number.value,config.plugins.FritzCall.name.value)
					self.newname = config.plugins.FritzCall.name.value.replace("\n",", ")
					self.newnumber = config.plugins.FritzCall.number.value
					if self.number != self.newnumber:
						if phonebook.search(self.newnumber):
							self.session.openWithCallback(
								self.overwriteConfirmed,
								MessageBox,
								_("Do you really want to overwrite entry for\n%(number)s\n\n%(name)s\n\nwith\n\n%(newname)s?")
								% {
								'number':self.newnumber,
								'name':phonebook.search(self.newnumber).replace(", ","\n"),
								'newname': self.newname
								}
								)
							self.close()
							return
						else:
							phonebook.remove(self.number)
					phonebook.add(self.newnumber, self.newname)
					self.close()
					self.parent.display()

				def overwriteConfirmed(self, ret):
					if ret:
						phonebook.add(self.newnumber, self.newname)
						self.parent.display()
					self.close()
						

				def cancel(self):
					self.close()

			print "[FritzCallPhonebook] displayPhonebook/edit"
			# self.session.open(MessageBox, "Not yet implemented.", type = MessageBox.TYPE_INFO)
			# return
			cur = self["entries"].getCurrent()
			if cur is None:
				self.session.open(MessageBox,_("No entry selected"), MessageBox.TYPE_INFO)
			else:
				(number, name) = cur[0]
				self.session.open(editScreen, self, str(name), str(number))

		def search(self):
			print "[FritzCallPhonebook] displayPhonebook/search"
			self.help_window = self.session.instantiateDialog(NumericalTextInputHelpDialog, self)
			self.help_window.show()
			self.session.openWithCallback(self.doSearch, InputBox, _("Enter Search Terms"), _("Search phonebook"))

		def doSearch(self, searchTerms):
			if not searchTerms: searchTerms = ""
			print "[FritzCallPhonebook] displayPhonebook/doSearch: " + searchTerms
			if self.help_window:
				self.session.deleteDialog(self.help_window)
				self.help_window = None
			self.display(searchTerms)

		def exit(self):
			self.close()

phonebook = FritzCallPhonebook()


class FritzCallSetup(Screen, ConfigListScreen, HelpableScreen):
	# TRANSLATORS: this is a window title. Avoid the use of non ascii chars
	skin = """
		<screen position="100,90" size="570,420" title="%s" >
		<widget name="config" position="5,10" size="560,300" scrollbarMode="showOnDemand" />
		<widget name="consideration" position="20,320" font="Regular;20" halign="center" size="510,50" />
		<ePixmap position="5,375" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
		<ePixmap position="145,375" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
		<ePixmap position="285,375" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
		<ePixmap position="425,375" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
		<widget name="key_red" position="5,375" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_green" position="145,375" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_yellow" position="285,375" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_blue" position="425,375" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		</screen>""" % _("FritzCall Setup")

	def __init__(self, session, args = None):

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
			self.list.append(getConfigListEntry(_("FRITZ!Box FON IP address"), config.plugins.FritzCall.hostname))

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

		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def save(self):
#		print "[FritzCallSetup] save"
		for x in self["config"].list:
			x[1].save()
		if fritz_call is not None:
			fritz_call.connect()
			print "[FritzCallSetup] called phonebook.reload()"
			phonebook.reload()

		self.close()

	def cancel(self):
#		print "[FritzCallSetup] cancel"
		for x in self["config"].list:
			x[1].cancel()
		self.close()

	def displayCalls(self):
		self.session.open(FritzDisplayCalls)

	def displayPhonebook(self):
		self.session.open(phonebook.displayPhonebook)


standbyMode = False

class FritzCallList:
	def __init__(self):
		self.callList = [ ]
	
	def add(self, event, date, number, caller, phone):
		print "[FritzCallList] add"
		if len(self.callList) > 10:
			if self.callList[0] != "Start":
				self.callList[0] = "Start"
			del self.callList[1]

		self.callList.append((event, number, date, caller, phone))
	
	def display(self):
		print "[FritzCallList] display"
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
			found = re.match(".*(\d\d.\d\d.)\d\d( \d\d:\d\d)", date)
			if found: date = found.group(1) + found.group(2)
			found = re.match(".*\((.*)\)", phone)
			if found: phone = found.group(1)
			# if len(phone) > 20: phone = phone[:20]

			if caller == _("UNKNOWN") and number != "":
				caller = number
			else:
				found = re.match("(.*)\n.*", caller)
				if found: caller = found.group(1)
			# if len(caller) > 20: caller = caller[:20]
			while (len(caller) + len(phone)) > 40:
				if len(caller) > len(phone):
					caller = caller[:-1]
				else:
					phone = phone[:-1]

			text = text + "%s %s %s %s\n" %(date, caller, direction, phone)

		print "[FritzCallList] display: '%s %s %s %s'" %(date, caller, direction, phone)
		# display screen
		Notifications.AddNotification(MessageBox, text, type=MessageBox.TYPE_INFO)
		# my_global_session.open(FritzDisplayCalls, text) # TODO please HELP: from where can I get a session?
		self.callList = [ ]
		self.text = ""

callList = FritzCallList()

def notifyCall(event, date, number, caller, phone):
	if Standby.inStandby is None or config.plugins.FritzCall.afterStandby.value == "each":
		if event == "RING":
			text = _("Incoming Call on %(date)s from\n---------------------------------------------\n%(number)s\n%(caller)s\n---------------------------------------------\nto: %(phone)s") % { 'date':date, 'number':number, 'caller':caller, 'phone':phone }
		else:
			text = _("Outgoing Call on %(date)s to\n---------------------------------------------\n%(number)s\n%(caller)s\n---------------------------------------------\nfrom: %(phone)s") % { 'date':date, 'number':number, 'caller':caller, 'phone':phone }
		print "[FritzCall] notifyCall:\n%s" %text
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
		print "[FritzCall] notifyCall: added to callList"
	else: # this is the "None" case
		print "[FritzCall] notifyCall: standby and no show"


#===============================================================================
#		We need a separate class for each invocation of reverseLookup to retain
#		the necessary data for the notification
#===============================================================================

countries = { }

class FritzReverseLookupAndNotifier:
	def __init__(self, event, number, caller, phone, date):
		print "[FritzReverseLookupAndNotifier] reverse Lookup for %s!" %number
		self.event = event
		self.number = number
		self.caller = caller
		self.phone = phone
		self.date = date
		self.currentWebsite = None
		self.nextWebsiteNo = 0

		if not countries:
			dom = parse(resolveFilename(SCOPE_PLUGINS, "Extensions/FritzCall/reverselookup.xml"))
			for top in dom.getElementsByTagName("reverselookup"):
				for country in top.getElementsByTagName("country"):
					code = country.getAttribute("code").replace("+","00")
					countries[code] = country.getElementsByTagName("website")

		self.countrycode = config.plugins.FritzCall.country.value

		if number[0] != "0":
			self.caller = _("UNKNOWN")
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
				print "[FritzReverseLookupAndNotifier] Country cannot be reverse handled"
				self.caller = _("UNKNOWN")
				self.notifyAndReset()
				return

		if countries.has_key(self.countrycode):
			print "[FritzReverseLookupAndNotifier] Found website for reverse lookup"
			self.websites = countries[self.countrycode]
			self.nextWebsiteNo = 1
			self.handleWebsite(self.websites[0])
		else:
			print "[FritzReverseLookupAndNotifier] Country cannot be reverse handled"
			self.caller = _("UNKNOWN")
			self.notifyAndReset()
			return

	def handleWebsite(self, website):
		print "[FritzReverseLookupAndNotifier] handleWebsite: " + website.getAttribute("name")
		if self.number[:2] == "00":
			number = website.getAttribute("prefix") + self.number.replace(self.countrycode,"")
		else:
			number = self.number

		url = website.getAttribute("url")
		if re.search('$AREACODE',url) or re.search('$PFXAREACODE',url):
			print "[FritzReverseLookupAndNotifier] handleWebsite: (PFX)ARECODE cannot be handled"
			self.caller = _("UNKNOWN")
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
			print "[FritzReverseLookupAndNotifier] handleWebsite: cannot handle websites with no $NUMBER in url"
			self.caller = _("UNKNOWN")
			self.notifyAndReset()
			return
		print "[FritzReverseLookupAndNotifier] Url to query: " + url
		url = url.encode("UTF-8", "replace")
		self.currentWebsite = website
		getPage(url, method="GET").addCallback(self._gotPage).addErrback(self._gotError)

	def _gotPage(self, page):
		print "[FritzReverseLookupAndNotifier] _gotPage"
		found = re.match('.*content=".*?charset=([^"]+)"',page,re.S)
		if found:
			print "[FritzReverseLookupAndNotifier] Charset: " + found.group(1)
			page = page.replace("\xa0"," ").decode(found.group(1), "replace")
		else:
			page = page.replace("\xa0"," ").decode("ISO-8859-1", "replace")

		for entry in self.currentWebsite.getElementsByTagName("entry"):
			# print "[FritzReverseLookupAndNotifier] _gotPage: try entry"
			details = []
			for what in ["name", "street", "city", "zipcode"]:
				pat = "(.*)" + self.getPattern(entry, what)
				# print "[FritzReverseLookupAndNotifier] _gotPage: look for '''%s''' with '''%s'''" %( what, pat )
				found = re.match(pat, page, re.S|re.M)
				if found:
					# print "[FritzReverseLookupAndNotifier] _gotPage: found for '''%s''': '''%s'''" %( what, found.group(2) )
					item = found.group(2).replace("&nbsp;"," ").replace("</b>","").replace(",","")
					item = html2utf8(item)
					details.append(item.strip())
					# print "[FritzReverseLookupAndNotifier] _gotPage: got '''%s''': '''%s'''" %( what, item.strip() )
				else:
					break

			if len(details) != 4:
				continue
			else:
				name = details[0]
				address =  details[1] + ", " + details[3] + " " + details[2]
				print "[FritzReverseLookupAndNotifier] _gotPage: Reverse lookup succeeded:\nName: %s\nAddress: %s" %(name, address)
				self.caller = "%s, %s" %(name, address)
				if self.number != 0 and config.plugins.FritzCall.addcallers.value and self.event == "RING":
					phonebook.add(self.number, self.caller)

				self.caller = self.caller.replace(", ", "\n").encode("UTF-8", "replace")
				self.notifyAndReset()
				return True
				break
		else:
			self._gotError("[FritzReverseLookupAndNotifier] _gotPage: Nothing found at %s" %self.currentWebsite.getAttribute("name"))
			
	def _gotError(self, error = ""):
		print "[FritzReverseLookupAndNotifier] _gotError - Error: %s" %error
		if self.nextWebsiteNo >= len(self.websites):
			print "[FritzReverseLookupAndNotifier] _gotError: I give up"
			self.caller = _("UNKNOWN")
			self.notifyAndReset()
			return
		else:
			print "[FritzReverseLookupAndNotifier] _gotError: try next website"
			self.nextWebsiteNo = self.nextWebsiteNo+1
			self.handleWebsite(self.websites[self.nextWebsiteNo-1])

	def getPattern(self, website, which):
		pat1 = website.getElementsByTagName(which)
		if len(pat1) > 1:
			print "Something strange: more than one %s for website %s" %(which, website.getAttribute("name"))
		return pat1[0].childNodes[0].data

	def notifyAndReset(self, timeout=config.plugins.FritzCall.timeout.value):
		notifyCall(self.event, self.date, self.number, self.caller, self.phone)
		# kill that object...


class FritzProtocol(LineReceiver):
	def __init__(self):
		print "[FritzProtocol] __init__"
		self.resetValues()

	def resetValues(self):
		print "[FritzProtocol] resetValues"
		self.number = '0'
		self.caller = None
		self.phone = None
		self.date = '0'

	def notifyAndReset(self, timeout=config.plugins.FritzCall.timeout.value):
		notifyCall(self.event, self.date, self.number, self.caller, self.phone)
		self.resetValues()

	def lineReceived(self, line):
		print "[FritzProtocol] lineReceived: %s" %line
#15.07.06 00:38:54;CALL;1;4;<from/extern>;<to/our msn>;
#15.07.06 00:38:58;DISCONNECT;1;0;
#15.07.06 00:39:22;RING;0;<from/extern>;<to/our msn>;
#15.07.06 00:39:27;DISCONNECT;0;0;
		a = []
		a = line.split(';')
		(self.date, self.event) = a[0:2]

		if self.event == "RING" or (self.event == "CALL" and config.plugins.FritzCall.showOutgoing.value):
			phone = a[4]
			 
			if self.event == "RING":
				number = a[3] 
			else:
				number = a[5]
				
			print "[FritzProtocol] lineReceived phone: '''%s''' number: '''%s'''" % (phone, number)

			filtermsns = config.plugins.FritzCall.filtermsn.value.split(",")
			for i in range(len(filtermsns)):
				filtermsns[i] = filtermsns[i].strip()
			if not (config.plugins.FritzCall.filter.value and phone not in filtermsns):
				print "[FritzProtocol] lineReceived no filter hit"
				phonename = phonebook.search(phone)		   # do we have a name for the number of our side?
				if phonename is not None:
					self.phone = "%s (%s)" %(phone, phonename)
				else:
					self.phone = phone

				if config.plugins.FritzCall.internal.value and len(number) > 3 and number[0]=="0":
					self.number = number[1:]
				else:
					self.number = number

				if self.event == "CALL" and self.number[0] != '0':					  # should only happen for outgoing
					self.number = config.plugins.FritzCall.prefix.value + self.number

				if self.number is not "":
					print "[FritzProtocol] lineReceived phonebook.search: %s" %self.number
					self.caller = phonebook.search(self.number)
					print "[FritzProtocol] lineReceived phonebook.search reault: %s" %self.caller
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
			self.d = (f, reactor.connectTCP("%d.%d.%d.%d" % tuple(config.plugins.FritzCall.hostname.value), 1012, f))

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
	session.open(phonebook.displayPhonebook)

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

	print "[FRITZ!Call] - Autostart"
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
