# -*- coding: utf-8 -*-
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.config import config, ConfigSubsection, ConfigSelection, ConfigIP, ConfigEnableDisable, getConfigListEntry, ConfigText, ConfigInteger
from Components.ConfigList import ConfigListScreen

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
try:
		_ = gettext.translation('fritzcall', '/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/po', [config.osd.language.getText()]).gettext
except IOError:
		pass


my_global_session = None

config.plugins.FritzCall = ConfigSubsection()
config.plugins.FritzCall.enable = ConfigEnableDisable(default = False)
config.plugins.FritzCall.hostname = ConfigIP(default = [192, 168, 178, 1])
config.plugins.FritzCall.filter = ConfigEnableDisable(default = False)
config.plugins.FritzCall.filtermsn = ConfigText(default = "", fixed_size = False)
config.plugins.FritzCall.showOutgoing = ConfigEnableDisable(default = False)
config.plugins.FritzCall.timeout = ConfigInteger(default = 15, limits = (0,60))
config.plugins.FritzCall.lookup = ConfigEnableDisable(default = False)
config.plugins.FritzCall.internal = ConfigEnableDisable(default = False)
config.plugins.FritzCall.fritzphonebook = ConfigEnableDisable(default = False)
config.plugins.FritzCall.phonebook = ConfigEnableDisable(default = False)
config.plugins.FritzCall.addcallers = ConfigEnableDisable(default = False)
config.plugins.FritzCall.phonebookLocation = ConfigSelection(choices = [("/media/usb/PhoneBook.txt", _("USB Stick")), ("/media/cf/PhoneBook.txt", _("CF Drive")), ("/media/hdd/PhoneBook.txt", _("Harddisk"))])
config.plugins.FritzCall.password = ConfigText(default = "", fixed_size = False)
config.plugins.FritzCall.prefix = ConfigText(default = "", fixed_size = False)

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

	def errorLogin(self, error):
		text = _("Fritz!Box Login failed! - Error: %s") %error
		self.notify(text)

	def errorLoad(self, error):
		text = _("Could not load phonebook from Fritz!Box - Error: %s") %error
		self.notify(text)

	def loadFritzBoxPhonebook(self):
		print "[FritzCallPhonebook] loadFritzBoxPhonebook"

		host = "%d.%d.%d.%d" %tuple(config.plugins.FritzCall.hostname.value)
		uri = "/cgi-bin/webcm"# % tuple(config.plugins.FritzCall.hostname.value)
		parms = urlencode({'getpage':'../html/de/menus/menu2.html', 'var:lang':'de','var:pagename':'fonbuch','var:menu':'fon'})

		url = "http://%s%s?%s" %(host, uri, parms)

		getPage(url).addCallback(self._gotPageLoad).addErrback(self.errorLoad)

	def parseFritzBoxPhonebook(self, html):
		print "[FritzCallPhonebook] parseFritzBoxPhonebook"
		found = re.match('.*<table id="tList".*?</tr>\n(.*?)</table>', html, re.S)

		if found:
			table = found.group(1)
			if re.search('TrFonName', table):		   # this is the new style
				#===============================================================================
				#				7170 / 7270 / New Style
				#	We expect one line with TrFonName followed by several lines with
				#	TrFonNr(Kind,Number,Shortcut,Vanity), which all belong to the name in TrFonName.
				#===============================================================================
				text = table.split('\n')
				for line in text:
					found = re.match('.*TrFonName\(".*", "(.*)", ".*"\)', line, re.S)
					if found:
						name = found.group(1)
						continue
					found = re.match('.*TrFonNr\("(.*)", "(.*)", "(.*)", "(.*)"\)', line, re.S) # TrFonNr(Art,Nummer,Kurzwahl,Vanity)
					if found:
						thisname = name

						kind = found.group(1)
						if kind == "mobile":
							thisname = thisname + " (" +_("mobile") + ")"
						elif kind == "home":
							thisname = thisname + " (" +_("home") + ")"
						elif kind == "work":
							thisname = thisname + " (" +_("work") + ")"

						if found.group(3):
							thisname = thisname + ", " + _("Shortcut") + ": " + found.group(3)
						if found.group(4):
							thisname = thisname + ", " + _("Vanity") + ": " + found.group(4)

						thisnumber = found.group(2)
						thisname = thisname.replace("&amp;", "&").replace("&szlig;", "ß").replace("&auml;", "ä").replace("&ouml;", "ö").replace("&uuml;", "ü").replace("&Auml;", "Ä").replace("&Ouml;", "Ö").replace("&Uuml;", "Ü")
						print "[FritzCallPhonebook] Adding '''%s''' with '''%s''' from Fritz!Box Phonebook!" %(thisname, thisnumber)
						self.phonebook[thisnumber.strip()] = thisname.strip()
						continue
			elif re.search('TrFon', table):
				#===============================================================================
				#				7050 / Old Style
				#	We expect one line with TrFon(No,Name,Number,Shortcut,Vanity)
				#===============================================================================				
				text = table.split('\n')
				for line in text:
					found = re.match('.*TrFon\(".*", "(.*)", "(.*)", "(.*)", "(.*)"\)', line, re.S)
					if found:
						name = found.group(1)
						thisnumber = found.group(2)
						if found.group(3):
							name = name + ", " + _("Kurzwahl") + ": " + found.group(3)
						if found.group(4):
							name = name + ", " +_("Vanity") +": " + found.group(4)
						name = name.replace("&amp;", "&").replace("&szlig;", "ß").replace("&auml;", "ä").replace("&ouml;", "ö").replace("&uuml;", "ü").replace("&Auml;", "Ä").replace("&Ouml;", "Ö").replace("&Uuml;", "Ü")
						print "[FritzCallPhonebook] Adding '''%s''' with '''%s''' from Fritz!Box Phonebook!" %(name, thisnumber)
						self.phonebook[thisnumber.strip()] = name.strip()
			else:
				self.notify(_("Could not parse Fritz!Box Phonebook entry"))
		else:
			print "[FritzCallPhonebook] Could not read Fritz!Box Phonebook"
			# self.notify(_("Could not read Fritz!Box Phonebook"))


	def _gotPageLogin(self, html):
#		print "[FritzCallPhonebook] _gotPageLogin"
		# workaround: exceptions in gotPage-callback were ignored
		try:
			self.verifyLogin(html)
		except:
			import traceback, sys
			traceback.print_exc(file=sys.stdout)
			#raise e

	def _gotPageLoad(self, html):
#		print "[FritzCallPhonebook] _gotPageLoad"
		# workaround: exceptions in gotPage-callback were ignored
		try:
			self.parseFritzBoxPhonebook(html)
		except:
			import traceback, sys
			traceback.print_exc(file=sys.stdout)
			#raise e

	def login(self):
		print "[FritzCallPhonebook] Login"

		host = "%d.%d.%d.%d" %tuple(config.plugins.FritzCall.hostname.value)
		uri =  "/cgi-bin/webcm"
		parms = "login:command/password=%s" %(config.plugins.FritzCall.password.value)
		url = "http://%s%s" %(host, uri)

		getPage(url, method="POST", headers = {'Content-Type': "application/x-www-form-urlencoded",'Content-Length': str(len(parms))}, postdata=parms).addCallback(self._gotPageLogin).addErrback(self.errorLogin)

	def verifyLogin(self, html):
		# print "[FritzCallPhonebook] verifyLogin - html: %s" %html
		found = re.match('.*<p class="errorMessage">FEHLER:&nbsp;Das angegebene Kennwort', html, re.S)
		if not found:
			self.loadFritzBoxPhonebook()
		else:
			text = _("Fritz!Box Login failed! - Wrong Password!")
			self.notify(text)

	def reload(self):
		print "[FritzCallPhonebook] reload"
		self.phonebook.clear()
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
			if config.plugins.FritzCall.password.value != "":
				self.login()
			else:
				self.loadFritzBoxPhonebook()

	def search(self, number):
		print "[FritzCallPhonebook] Searching for %s" %number
		name = None
		if config.plugins.FritzCall.phonebook.value or config.plugins.FritzCall.fritzphonebook.value:
			if self.phonebook.has_key(number):
				name = self.phonebook[number].replace(", ", "\n").strip()
		return name

	def add(self, number, name):
		print "[FritzCallPhonebook] add"
		if config.plugins.FritzCall.phonebook.value and config.plugins.FritzCall.addcallers.value:
			try:
				f = open(config.plugins.FritzCall.phonebookLocation.value, 'a')
				name = name.strip() + "\n"
				string = "%s#%s" %(number, name)
				self.phonebook[number] = name;
				f.write(string)
				f.close()
				return True

			except IOError:
				return False

phonebook = FritzCallPhonebook()

class FritzCallSetup(ConfigListScreen, Screen):
	skin = """
		<screen position="100,90" size="550,420" title="FritzCall Setup" >
		<widget name="config" position="20,10" size="510,300" scrollbarMode="showOnDemand" />
		<widget name="consideration" position="20,320" font="Regular;20" halign="center" size="510,50" />
		</screen>"""

	def __init__(self, session, args = None):

		Screen.__init__(self, session)

		self["consideration"] = Label(_("You need to enable the monitoring on your Fritz!Box by dialing #96*5*!"))
		self.list = []

		self["setupActions"] = ActionMap(["SetupActions"],
		{
			"save": self.save,
			"cancel": self.cancel,
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
			self.list.append(getConfigListEntry(_("Fritz!Box FON IP address"), config.plugins.FritzCall.hostname))

			self.list.append(getConfigListEntry(_("Show Calls for specific MSN"), config.plugins.FritzCall.filter))
			if config.plugins.FritzCall.filter.value:
				self.list.append(getConfigListEntry(_("MSN to show"), config.plugins.FritzCall.filtermsn))

			self.list.append(getConfigListEntry(_("Show Outgoing Calls"), config.plugins.FritzCall.showOutgoing))
			self.list.append(getConfigListEntry(_("Timeout for Call Notifications (seconds)"), config.plugins.FritzCall.timeout))
			self.list.append(getConfigListEntry(_("Reverse Lookup Caller ID (DE only)"), config.plugins.FritzCall.lookup))

			self.list.append(getConfigListEntry(_("Read PhoneBook from Fritz!Box"), config.plugins.FritzCall.fritzphonebook))
			if config.plugins.FritzCall.fritzphonebook.value:
				self.list.append(getConfigListEntry(_("Password Accessing Fritz!Box"), config.plugins.FritzCall.password))

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

class FritzProtocol(LineReceiver):
	def __init__(self):
#		print "[FritzProtocol] __init__"
		self.resetValues()

	def resetValues(self):
#		print "[FritzProtocol] resetValues"
		self.number = '0'
		self.caller = None
		self.phone = None
		self.date = '0'

	def notify(self, text, timeout=config.plugins.FritzCall.timeout.value):
		Notifications.AddNotification(MessageBox, text, type=MessageBox.TYPE_INFO, timeout=timeout)

	def handleIncoming(self):
#		print "[FritzProtocol] handle Incoming!"

		text = _("Incoming Call ")
		if self.caller is not None:
			text += _("on %s from\n---------------------------------------------\n%s\n%s\n---------------------------------------------\nto: %s") % (self.date, self.number, self.caller, self.phone)
		else:
			text += _("on %s from\n---------------------------------------------\n%s (UNKNOWN)\n---------------------------------------------\nto: %s") % (self.date, self.number, self.phone)

		self.notify(text)
		self.resetValues()

	def handleOutgoing(self):
#		print "[FritzProtocol] handle Outgoing!"
		text = _("Outgoing Call ")
		if(self.caller is not None):
			text += _("on %s to\n---------------------------------------------\n%s\n%s\n---------------------------------------------\nfrom: %s") % (self.date, self.number, self.caller, self.phone)
		else:
			text += _("on %s to\n---------------------------------------------\n%s (UNKNOWN)\n\n---------------------------------------------\nfrom: %s") % (self.date, self.number, self.phone)#

		self.notify(text)
		self.resetValues()

	def handleEvent(self):
#		print "[FritzProtocol] handleEvent!"
		if self.event == "RING":
			self.handleIncoming()
		elif self.event == "CALL":
			self.handleOutgoing()

	def handleEventOnError(self, error):
#		print "[FritzProtocol] handleEventOnError - Error :%s" %error
		self.handleEvent()

	def _gotPage(self, data):
#		print "[FritzProtocol] _gotPage"
		try:
			self.gotPage(data)
		except:
			import traceback, sys
			traceback.print_exc(file=sys.stdout)
			#raise e
			self.handleEvent()

	def gotPage(self, html):
#		print "[FritzProtocol] gotPage"
		found = re.match('.*<td.*?class="cel-data border.*?>(.*?)</td>', html, re.S)
		if found:
			td = found.group(1)					# group(1) is the content of (.*?) in our pattern
			td.decode("ISO-8859-1").encode("UTF-8")
			text = re.sub("<.*?>", "", td)		# remove tags and their content
			text = text.split("\n")
			#===============================================================================
			# 
			#	The logic here is as follows:
			#
			#	The first line in the table, which has a word followed by a space
			#	followed by a word is the name. As of the time of writing that was line 3,
			#	but that could change in the future.
			#	
			#	Starting from the next line after that we are looking for a line
			#	containing 5 digits (PLZ) followed by a space followed by a word at the
			#	end of the line. If found, we assume, that that is the address. The right
			#	one at time of writing was 10.
			#	
			#===============================================================================
			nameLine = 3	 # as of 08.06.08
			if not re.search('\S+ \S+', text[nameLine].replace("&nbsp;", " ").strip()):
				for i in range(0,len(text)-1):
					if re.search('\S+ \S+', text[i].replace("&nbsp;", " ").strip()):
						nameLine = i
						break
			name = text[nameLine].replace("&nbsp;", " ").strip()

			addrLine = 10	# as of 08.06.08 that was the correct one
			for i in range(nameLine+1,len(text)-1):   # look for a line containing the address, i.e. "PLZ Name" at the end of the line
				if re.search('\d\d\d\d\d \S+$', text[i].replace("&nbsp;", " ").strip()):
					addrLine = i
					break
			address = text[addrLine].replace("&nbsp;", " ").replace(", ", "\n").strip();
			print "[FritzProtocol] Reverse lookup succeeded:\nName: %s\n\nAddress: %s" %(name, address)

			self.caller = "%s\n%s" %(name, address)

			#Autoadd to PhoneBook.txt if enabled
			if config.plugins.FritzCall.addcallers.value and self.event == "RING":
				phonebook.add(self.number, self.caller.replace("\n", ", "))
#		else:
#			print "[FritzProtocol] Reverse lookup without result!"

		self.handleEvent()

	def reverseLookup(self):
#		print "[FritzProtocol] reverse Lookup!"
		url = "http://www.dasoertliche.de/?form_name=search_inv&ph=%s" %self.number
		getPage(url,method="GET").addCallback(self._gotPage).addErrback(self.handleEventOnError)

	def lineReceived(self, line):
#		print "[FritzProtocol] lineReceived"
#15.07.06 00:38:54;CALL;1;4;<provider>;<callee>;
#15.07.06 00:38:58;DISCONNECT;1;0;
#15.07.06 00:39:22;RING;0;<caller>;<outgoing msn>;
#15.07.06 00:39:27;DISCONNECT;0;0;

		a = line.split(';')
		(self.date, self.event) = a[0:2]

		#incoming Call
		if self.event == "RING":
			phone = a[4]

			if not config.plugins.FritzCall.filter.value or config.plugins.FritzCall.filtermsn.value == phone:
				phonename = phonebook.search(phone)
				if phonename is not None:
					self.phone = "%s (%s)" %(phone, phonename)
				else:
					self.phone = phone

				if config.plugins.FritzCall.internal.value and len(a[3]) > 3 and a[3][0]=="0":
					self.number = a[3][1:]
				else:
					self.number = a[3]

				self.caller = phonebook.search(self.number)
				if (self.caller is None) and config.plugins.FritzCall.lookup.value:
					self.reverseLookup()
				else:
					self.handleEvent()

		#Outgoing Call
		elif config.plugins.FritzCall.showOutgoing.value and self.event == "CALL":
			phone = a[4]

			if not config.plugins.FritzCall.filter.value or config.plugins.FritzCall.filtermsn.value == phone:
				phonename = phonebook.search(phone)
				if phonename is not None:
					self.phone = "%s (%s)" %(phone, phonename)
				else:
					self.phone = phone

				if config.plugins.FritzCall.internal.value and len(a[5]) > 3 and a[5][0]=="0":
					self.number = a[5][1:]
				else:
					self.number = a[5]

				if self.number[0] != '0':
					self.number = config.plugins.FritzCall.prefix.value + self.number

				self.caller = phonebook.search(self.number)

				if (self.caller is None) and config.plugins.FritzCall.lookup.value:
					self.reverseLookup()
				else:
					self.handleEvent()


class FritzClientFactory(ReconnectingClientFactory):
	initialDelay = 20
	maxDelay = 500

	def __init__(self):
		self.hangup_ok = False

	def startedConnecting(self, connector):
		Notifications.AddNotification(MessageBox, _("Connecting to Fritz!Box..."), type=MessageBox.TYPE_INFO, timeout=2)

	def buildProtocol(self, addr):
		Notifications.AddNotification(MessageBox, _("Connected to Fritz!Box!"), type=MessageBox.TYPE_INFO, timeout=4)
		self.resetDelay()
		return FritzProtocol()

	def clientConnectionLost(self, connector, reason):
		if not self.hangup_ok:
			Notifications.AddNotification(MessageBox, _("Connection to Fritz!Box! lost\n (%s)\nretrying...") % reason.getErrorMessage(), type=MessageBox.TYPE_INFO, timeout=config.plugins.FritzCall.timeout.value)
		ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

	def clientConnectionFailed(self, connector, reason):
		Notifications.AddNotification(MessageBox, _("Connecting to Fritz!Box failed\n (%s)\nretrying...") % reason.getErrorMessage(), type=MessageBox.TYPE_INFO, timeout=config.plugins.FritzCall.timeout.value)
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

	print "[Fritz!Call] - Autostart"
	if reason == 0:
		fritz_call = FritzCall()
	elif reason == 1:
		fritz_call.shutdown()
		fritz_call = None

def Plugins(**kwargs):
	 return [ PluginDescriptor(name="FritzCall", description=_("Display Fritzbox-Fon calls on screen"), where = PluginDescriptor.WHERE_PLUGINMENU, fnc=main),
		 PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc = autostart) ]
