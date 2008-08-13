# -*- coding: utf-8 -*-
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens import Standby

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Button import Button
from Components.config import config, ConfigSubsection, ConfigSelection, ConfigIP, ConfigEnableDisable, getConfigListEntry, ConfigText, ConfigInteger
from Components.ConfigList import ConfigListScreen
from Components.ScrollLabel import ScrollLabel

from Plugins.Plugin import PluginDescriptor
from Tools import Notifications

from twisted.internet import reactor
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.protocols.basic import LineReceiver
from twisted.web.client import getPage

from os import path as os_path
from urllib import urlencode 
import re

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
config.plugins.FritzCall.country = ConfigSelection(choices = [("DE", _("Germany")), ("CH", _("Switzerland")), ("IT", _("Italy")), ("AT", _("Austria"))])

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
				in_html = in_html.replace(key, (unichr(int(codepoint)).encode('utf8')))
			except ValueError:
				pass
	except ImportError:
		return in_html.replace("&amp;", "&").replace("&szlig;", "ß").replace("&auml;", "ä").replace("&ouml;", "ö").replace("&uuml;", "ü").replace("&Auml;", "Ä").replace("&Ouml;", "Ö").replace("&Uuml;", "Ü")
	return in_html

class FritzCallFBF:
	def __init__(self):
		print "[FritzCallFBF] __init__"
		self.missedCallback = None
		self.loginCallback = None

	def notify(self, text):
		Notifications.AddNotification(MessageBox, text, type=MessageBox.TYPE_ERROR, timeout=config.plugins.FritzCall.timeout.value)

	def errorLogin(self, error):
		text = _("FRITZ!Box Login failed! - Error: %s") %error
		self.notify(text)

	def _gotPageLogin(self, html):
#		print "[FritzCallPhonebook] _gotPageLogin"
		# workaround: exceptions in gotPage-callback were ignored
		try:
			print "[FritzCallFBF] _gotPageLogin: verify login"
			found = re.match('.*<p class="errorMessage">FEHLER:&nbsp;Das angegebene Kennwort', html, re.S)
			if found:
				text = _("FRITZ!Box Login failed! - Wrong Password!")
				self.notify(text)
			else:
				self.loginCallback()
			loginCallback = None
		except:
			import traceback, sys
			traceback.print_exc(file=sys.stdout)
			#raise e

	def login(self):
		print "[FritzCallFBF] Login"
		if config.plugins.FritzCall.password.value != "":
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

		table = html2utf8(html)
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
					thisname = thisname.strip()
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
					print "[FritzCallFBF] Adding '''%s''' with '''%s''' from FRITZ!Box Phonebook!" %(name, thisnumber)
					phonebook.phonebook[thisnumber] = name
				else:
					print "[FritzCallFBF] ignoring empty number for %s" %name
				continue
		else:
			self.notify(_("Could not parse FRITZ!Box Phonebook entry"))

	def errorCalls(self, error):
		text = _("Could not load missed calls from FRITZ!Box - Error: %s") %error
		self.notify(text)

	def _gotPageCalls(self, html):
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

		# check for error: wrong password or password not set... TODO
		found = re.search('Melden Sie sich mit dem Kennwort der FRITZ!Box an', html)
		if found:
			text = _("You need to set the password of the FRITZ!Box\nin the configuration dialog to display missed calls\n\nIt could be a communication issue, just try again.")
			# self.session.open(MessageBox, text, MessageBox.TYPE_ERROR, timeout=config.plugins.FritzCall.timeout.value)
			self.notify(text)
			return

		# print "[FritzCallFBF] _gotPageCalls:\n" + html
		lines = html.splitlines()
		text = ""
		for line in lines:
			# print line
			found = re.match(".*2;([^;]*);;([^;]*);;([^;]*)", line)
			if found:
				date = found.group(1)
				caller = _resolveNumber(found.group(2))
				callee = _resolveNumber(found.group(3))
				while (len(caller) + len(callee)) > 40:
					if len(caller) > len(callee):
						caller = caller[:-1]
					else:
						callee = callee[:-1]
				found = re.match("(\d\d.\d\d.)\d\d( \d\d:\d\d)", date)
                                if found: date = found.group(1) + found.group(2)
				text = text + "\n" + date + " " + caller + " -> " + callee

		# print "[FritzCallFBF] _gotPageCalls result:\n" + text

		if self.missedCallback is not None:
			# print "[FritzCallFBF] _gotPageCalls call callback with\n" + text
			self.missedCallback(text = text)
			self.missedCallback = None

	def getMissedCalls(self, callback):
		#
		# call sequence must be:
		# - login
		# - getPage -> _gotPageLogin
		# - loginCallback (_getMissedCalls)
		# - getPage -> _getMissedCalls1
		print "[FritzCallFBF] getMissedCalls"
		self.missedCallback = callback
		self.loginCallback = self._getMissedCalls
		self.login()

	def _getMissedCalls(self):
		#
		# we need this to fill Anrufliste.csv
		# http://repeater1/cgi-bin/webcm?getpage=../html/de/menus/menu2.html&var:lang=de&var:menu=fon&var:pagename=foncalls
		#
		print "[FritzCallFBF] _getMissedCalls"
		host = "%d.%d.%d.%d" %tuple(config.plugins.FritzCall.hostname.value)
		parms = urlencode({'getpage':'../html/de/menus/menu2.html', 'var:lang':'de','var:pagename':'foncalls','var:menu':'fon'})
		url = "http://%s/cgi-bin/webcm?%s" %(host, parms)
		getPage(url).addCallback(self._getMissedCalls1).addErrback(self.errorCalls)

	def _getMissedCalls1(self, html):
		#
		# finally we should have successfully lgged in and filled the csv
		#
		print "[FritzCallFBF] _getMissedCalls1"
		host = "%d.%d.%d.%d" %tuple(config.plugins.FritzCall.hostname.value)
		parms = urlencode({'getpage':'../html/de/FRITZ!Box_Anrufliste.csv'})
		url = "http://%s/cgi-bin/webcm?%s" %(host, parms)
		getPage(url).addCallback(self._gotPageCalls).addErrback(self.errorCalls)

fritzbox = FritzCallFBF()

class FritzDisplayMissedCalls(Screen):

	skin = """
		<screen name="FritzDisplayMissedCalls" position="100,90" size="550,420" title="Missed calls" >
			<widget name="statusbar" position="0,0" size="550,22" font="Regular;22" />
			<widget name="list" position="0,22" size="550,398" font="Regular;22" />
		</screen>"""

	def __init__(self, session, text = ""):
		self.skin = FritzDisplayMissedCalls.skin
		Screen.__init__(self, session)

		self["setupActions"] = ActionMap(["OkCancelActions", "DirectionActions"],
		{
			"down": self.pageDown,
			"up": self.pageUp,
			"right": self.pageDown,
			"left": self.pageUp,
			"cancel": self.ok,
			"save": self.ok,
			"ok": self.ok,}, -2)
		
		if text == "":
			self["statusbar"] = Label(_("Getting missed calls from FRITZ!Box..."))
			self["list"] = ScrollLabel("")
			fritzbox.getMissedCalls(self.gotMissedCalls)
		else:
			self["statusbar"] = Label(_("Missed calls during Standby"))
			self["list"] = ScrollLabel(text)

	def ok(self):
		self.close()

	def pageDown(self):
		self["list"].pageDown()

	def pageUp(self):
		self["list"].pageUp()

	def gotMissedCalls(self, text):
		# print "[FritzDisplayMissedCalls] gotMissedCalls:\n" + text
		self["statusbar"].setText(_("Missed calls"))
		self["list"].setText(text)


class FritzCallPhonebook:
	def __init__(self):
		self.phonebook = {}
		self.reload()

	def notify(self, text):
		Notifications.AddNotification(MessageBox, text, type=MessageBox.TYPE_ERROR, timeout=config.plugins.FritzCall.timeout.value)

	def create(self):
		try:
			f = open(config.plugins.FritzCall.phonebookLocation.value, 'w')
			f.write("01234567890#Name, Street, Location (Keep the Spaces!!!)\n");
			f.close()
			return True
		except IOError:
			return False

	def reload(self):
		print "[FritzCallPhonebook] reload"
		self.phonebook.clear()

		if not config.plugins.FritzCall.enable.value:
			return

		exists = False
		
		if config.plugins.FritzCall.phonebook.value:
			if not os_path.exists(config.plugins.FritzCall.phonebookLocation.value):
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
		print "[FritzCallPhonebook] Searching for %s" %number
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
		if phonebook.search(number) is None and number <> 0 and config.plugins.FritzCall.phonebook.value and config.plugins.FritzCall.addcallers.value:
			try:
				f = open(config.plugins.FritzCall.phonebookLocation.value, 'a')
				name = name.strip() + "\n"
				string = "%s#%s" %(number, name)
				self.phonebook[number] = name;
				f.write(string)
				f.close()
				print "[FritzCallPhonebook] added %s with %sto Phonebook.txt" %(number, name)
				return True

			except IOError:
				return False

phonebook = FritzCallPhonebook()

class FritzCallSetup(ConfigListScreen, Screen):
	skin = """
		<screen position="100,90" size="550,420" title="FritzCall Setup" >
		<widget name="config" position="20,10" size="510,300" scrollbarMode="showOnDemand" />
		<widget name="consideration" position="20,320" font="Regular;20" halign="center" size="510,50" />
		<ePixmap position="5,375" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
		<ePixmap position="145,375" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
		<ePixmap position="285,375" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
		<widget name="key_red" position="5,375" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_green" position="145,375" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		<widget name="key_yellow" position="285,375" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
		</screen>"""

	def __init__(self, session, args = None):

		Screen.__init__(self, session)
		self.session = session

		self["consideration"] = Label(_("You need to enable the monitoring on your FRITZ!Box by dialing #96*5*!"))
		self.list = []

		# Initialize Buttons
		self["key_red"] = Button(_("Cancel"))
		self["key_green"] = Button(_("OK"))
		self["key_yellow"] = Button(_("Missed Calls"))

		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"cancel": self.cancel,
			"red": self.cancel,  	# not strictly needed, better for clarity
			"save": self.save,
			"green": self.save,  	# not strictly needed, better for clarity
			"yellow": self.displayMissedCalls,
			"ok": self.save,
		}, -2)

		ConfigListScreen.__init__(self, self.list)
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
			self.list.append(getConfigListEntry(_("Timeout for Call Notifications (seconds)"), config.plugins.FritzCall.timeout))
			self.list.append(getConfigListEntry(_("Reverse Lookup Caller ID (DE,CH,IT,AT only)"), config.plugins.FritzCall.lookup))
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
				self.list.append(getConfigListEntry(_("Automatically add new Caller to PhoneBook"), config.plugins.FritzCall.addcallers))

			self.list.append(getConfigListEntry(_("Strip Leading 0"), config.plugins.FritzCall.internal))
			self.list.append(getConfigListEntry(_("Prefix for Outgoing Calls"), config.plugins.FritzCall.prefix))

		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def save(self):
#		print "[FritzCallSetup] save"
		for x in self["config"].list:
			x[1].save()
		if fritz_call is not None:
			fritz_call.connect()

			if config.plugins.FritzCall.phonebook.value:
				if not os_path.exists(config.plugins.FritzCall.phonebookLocation.value):
					if not phonebook.create():
						Notifications.AddNotification(MessageBox, _("Can't create PhoneBook.txt"), type=MessageBox.TYPE_INFO, timeout=config.plugins.FritzCall.timeout.value)
				else:
					print "[FritzCallSetup] called phonebook.reload()"
					phonebook.reload()

		self.close()

	def cancel(self):
#		print "[FritzCallSetup] cancel"
		for x in self["config"].list:
			x[1].cancel()
		self.close()

	def displayMissedCalls(self):
		self.session.open(FritzDisplayMissedCalls)


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
		# my_global_session.open(FritzDisplayMissedCalls, text) # TODO please HELP: from where can I get a session?
		self.callList = [ ]
		self.text = ""

callList = FritzCallList()

def notifyCall(event, date, number, caller, phone):
	if Standby.inStandby is None or config.plugins.FritzCall.afterStandby.value == "each":
		if event == "RING":
			text = _("Incoming Call on %s from\n---------------------------------------------\n%s\n%s\n---------------------------------------------\nto: %s") % (date, number, caller, phone)
		else:
			text = _("Outgoing Call on %s to\n---------------------------------------------\n%s\n%s\n---------------------------------------------\nfrom: %s") % (date, number, caller, phone)
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

class FritzReverseLookupAndNotifier:
	def __init__(self, event, number, caller, phone, date):
		self.event = event
		self.number = number
		self.caller = caller
		self.phone = phone
		self.date = date

		countries = {
					"0049": ("http://www.dasoertliche.de/?form_name=search_inv&ph=%s", self.gotPageDasOertliche, self.gotErrorDasOertliche),
					"0041": ("http://tel.search.ch/result.html?name=&m...&tel=%s", self.gotPageTelSearchCH, self.gotErrorLast),
					"0039": ("http://www.paginebianche.it/execute.cgi?btt=1&ts=106&cb=8&mr=10&rk=&om=&qs=%s", self.gotPagePaginebiancheIT, self.gotErrorLast),
					"0043": ("http://www.telefonabc.at/result.aspx?telpre=%s&telnr=%s&exact=1", self.gotTelefonabcAT, self.gotErrorLast)
					}

		print "[FritzReverseLookupAndNotifier] reverse Lookup for %s!" %self.number

		if config.plugins.FritzCall.country.value == "DE":
			countrycode = "0049"
		elif config.plugins.FritzCall.country.value == "CH":
			countrycode = "0041"
		elif config.plugins.FritzCall.country.value == "IT":
			countrycode = "0039"
		elif config.plugins.FritzCall.country.value == "AT":
			countrycode = "0043"
		else:
			print "[FritzReverseLookupAndNotifier] reverse Lookup: unknown country?!?!"
			countrycode = "0049"

		if self.number[:2] == "00":
			countrycode = self.number[:4]

		if countries.has_key(countrycode):
			(url, callBack, errBack) = countries[countrycode]
			if countrycode != "0043":
				url = url %self.number.replace(countrycode,"0")
			else:	   # for Austria we must separate the number
				number = self.number.replace(countrycode,"0")
				if number[:2] == "01":  # Wien
					print "[FritzReverseLookupAndNotifier] AT: Wien"
					url = url % ("01", number[2:])
				elif number[1:4] in ["316", "463", "512", "650", "662", "660", "664", "676", "678", "680", "681", "688", "699", "720", "732"]:
					print "[FritzReverseLookupAndNotifier] AT: short prefix"
					url = url % (number[:4], number[4:])
				else:
					print "[FritzReverseLookupAndNotifier] AT: others"
					url = url % (number[:5], number[5:])
				
			getPage(url, method="GET").addCallback(callBack).addErrback(errBack)
		else:
			print "[FritzReverseLookupAndNotifier] call from country, which is not handled"


	def notifyAndReset(self, timeout=config.plugins.FritzCall.timeout.value):
		notifyCall(self.event, self.date, self.number, self.caller, self.phone)
		# kill that object...

	def gotErrorLast(self, error):
		self.caller = _("UNKNOWN")
		self.notifyAndReset()

	def gotErrorDasOertliche(self, error):			 # so we try Klicktel
		url = "http://www.klicktel.de/telefonbuch/backwardssearch.html?newSearch=1&boxtype=backwards&vollstaendig=%s" %self.number
		getPage(url, method="GET").addCallback(self.gotPageKlicktel).addErrback(self.gotErrorLast)

	def gotPageDasOertliche(self, html):
		print "[FritzReverseLookupAndNotifier] gotPageDasOertliche"
		try:
			found = re.match('.*<td.*?class="cel-data border.*?>(.*?)</td>', html, re.S)
			if found:
				td = found.group(1)					# group(1) is the content of (.*?) in our pattern
				td = td.decode("ISO-8859-1").encode("UTF-8")
				found = re.match('.*<div.*</div>.*<div>.*<a.*class="entry">([^<]*)</a>.*</div>(.*)', td, re.S)
				if found:
					name = found.group(1)
					td = found.group(2)
					text = re.sub("<.*?>", "", td)		# remove tags and their content
					text = text.split("\n")
					#===============================================================================
					# 
					#	The logic here is as follows:
					#	
					#	We are looking for a line
					#	containing 5 digits (PLZ) followed by a space followed by a word at the
					#	end of the line. If found, we assume, that that is the address. The right
					#	one at time of writing was 10.
					#	
					#===============================================================================

					addrLine = 10	# as of 08.06.08 that was the correct one
					for i in range(0,len(text)-1):   # look for a line containing the address, i.e. "PLZ Name" at the end of the line
						if re.search('\d\d\d\d\d \S+$', text[i].replace("&nbsp;", " ").strip()):
							addrLine = i
							break
					address = text[addrLine].replace("&nbsp;", " ").replace(", ", "\n").strip();
					print "[FritzReverseLookupAndNotifier] Reverse lookup succeeded with DasOertliche:\nName: %s\n\nAddress: %s" %(name, address)

					self.caller = "%s\n%s" %(name, address)

					if self.event == "RING":
						phonebook.add(self.number, self.caller.replace("\n", ", "))

					self.notifyAndReset()
					return True

		except:
			import traceback, sys
			traceback.print_exc(file=sys.stdout)
			#raise e

		url = "http://www.klicktel.de/telefonbuch/backwardssearch.html?newSearch=1&boxtype=backwards&vollstaendig=%s" %self.number
		getPage(url, method="GET").addCallback(self.gotPageKlicktel).addErrback(self.gotErrorKlicktel)
		
	def gotPageKlicktel(self, html):
		print "[FritzReverseLookupAndNotifier] gotPageKlicktel"
		try:
			html = html.decode("ISO-8859-1").encode("UTF-8")
			html = html.replace("<br />", ", ")
			found = re.match('.*<a class="head" href=".*" title=""><span class="title">(.*)</span></a>.*<span class="location">([\S ,]+)</span>', html, re.S)
			if found:
				name = found.group(1)
				address = found.group(2)
				print "[FritzProtocol] Reverse lookup succeeded with Klicktel:\nName: %s\n\nAddress: %s" %(name, address)

				self.caller = "%s\n%s" %(name, address)

				if self.event == "RING":
					phonebook.add(self.number, self.caller.replace("\n", ", "))
			
				self.notifyAndReset()
				return True

		except:
			import traceback, sys
			traceback.print_exc(file=sys.stdout)
			#raise e
		self.caller = _("UNKNOWN")
		self.notifyAndReset()


	def gotPageTelSearchCH(self, html):
		print "[FritzReverseLookupAndNotifier] gotPageTelSearchCH"
		try:
			html = html.decode("ISO-8859-1").encode("UTF-8")
			html = html.replace("<br />", ", ")
			found = re.match('.*<table class="record">.*<a href="[^"]+">([\S ,]+)</a>.*<div class="raddr">([\S ,]+)</div>.*</table>', html, re.S)
			if found:
				name = found.group(1).replace(",","")
				address = found.group(2)
				print "[FritzProtocol] Reverse lookup succeeded:\nName: %s\n\nAddress: %s" %(name, address)

				self.caller = "%s, %s" %(name, address)

				if self.number != 0 and config.plugins.FritzCall.addcallers.value and self.event == "RING":
					phonebook.add(self.number, self.caller)
					
				self.notifyAndReset()
				return True

		except:
			import traceback, sys
			traceback.print_exc(file=sys.stdout)
			#raise e
		self.caller = _("UNKNOWN")
		self.notifyAndReset()


	def gotPagePaginebiancheIT(self, html):
		print "[FritzReverseLookupAndNotifier] gotPagePaginebiancheIT"
		try:
			html = html.decode("ISO-8859-1").encode("UTF-8")
			found = re.match('.*<div class="client-identifying-pg(.*class="org">.*class="postal-code">.*</span>.*class="locality">.*</span>.*class="region">.*</span>.*class="street-address">.*)</span></p></address>', html, re.S)
			if found:
				html = found.group(1)
				found = re.match('.*class="org">([^<]*).*class="postal-code">([^<]*).*</span>.*class="locality">([^<]*).*</span>.*class="region">([^<]*).*</span>.*class="street-address">([^<]*).*', html, re.S)
				if found:
					name = found.group(1)
					postalcode = found.group(2)
					locality = found.group(3)
					region = found.group(4)
					streetaddress = found.group(5).replace(",","")
					address =  streetaddress+ ", " + postalcode + " " + locality + " " + region
					print "[FritzProtocol] Reverse lookup succeeded:\nName: %s\n\nAddress: %s" %(name, address)

					self.caller = "%s, %s" %(name, address)

					if self.number != 0 and config.plugins.FritzCall.addcallers.value and self.event == "RING":
						phonebook.add(self.number, self.caller)

					self.notifyAndReset()
					return True

		except:
			import traceback, sys
			traceback.print_exc(file=sys.stdout)
			#raise e
		self.caller = _("UNKNOWN")
		self.notifyAndReset()


	def gotTelefonabcAT(self, html):
		print "[FritzReverseLookupAndNotifier] gotTelefonabcAT"
		try:
			html = html.decode("ISO-8859-1").encode("UTF-8")
			html = html.replace("<b>","").replace("</b>","")
			found = re.match('.*(<td class="name">.*.*<td colspan="2" class="address small">.*</td>)', html, re.S)
			if found:
				html = found.group(1)
				found = re.match('.*<td class="name">\r\n([^<]*)</td>.*<td colspan="2" class="address small">\r\n([^<]*)</td>', html, re.S)
				if found:
					name = found.group(1)
					address =  found.group(2)
					myprint("[FritzProtocol] Reverse lookup succeeded:\nName: %s\n\nAddress: %s" %(name, address))

					self.caller = "%s, %s" %(name, address)

					if self.number != 0 and config.plugins.FritzCall.addcallers.value and self.event == "RING":
						phonebook.add(self.number, self.caller)

					self.notifyAndReset()
					return True

		except:
			import traceback, sys
			traceback.print_exc(file=sys.stdout)
			#raise e
		self.caller = _("UNKNOWN")
		self.notifyAndReset()



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

				if self.event == "CALL" and self.number[0] != '0':			  		  # should only happen for outgoing
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

def displayMissedCalls(session, servicelist):
	session.open(FritzDisplayMissedCalls)

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
	what_missed = _("Missed calls")
	if os_path.exists("plugin.png"):
		return [ PluginDescriptor(name="FritzCall", description=what, where = PluginDescriptor.WHERE_PLUGINMENU, icon = "plugin.png", fnc=main),
			PluginDescriptor(name=what_missed, description=what_missed, where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=displayMissedCalls),
			PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc = autostart) ]
	else:
		return [ PluginDescriptor(name="FritzCall", description=what, where = PluginDescriptor.WHERE_PLUGINMENU, fnc=main),
			PluginDescriptor(name=what_missed, description=what_missed, where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=displayMissedCalls),
			PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc = autostart) ]
