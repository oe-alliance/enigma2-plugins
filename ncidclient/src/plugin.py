# -*- coding: utf-8 -*-
'''
$Author: sreichholf $
'''
from enigma import eTimer, eSize, ePoint, getDesktop, eDVBVolumecontrol, eBackgroundFileEraser

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.NumericalTextInputHelpDialog import NumericalTextInputHelpDialog
from Screens.InputBox import InputBox
from Screens import Standby
from Screens.HelpMenu import HelpableScreen

from Components.config import config, ConfigSubsection, ConfigSelection, ConfigEnableDisable, getConfigListEntry, ConfigText, ConfigInteger
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Button import Button
from Components.Pixmap import Pixmap
from Components.Sources.List import List
from Components.ConfigList import ConfigListScreen
from Components.Harddisk import harddiskmanager

from Plugins.Plugin import PluginDescriptor
from Tools import Notifications
from Tools.NumericalTextInput import NumericalTextInput
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_SKIN_IMAGE, SCOPE_CONFIG, SCOPE_MEDIA
from Tools.LoadPixmap import LoadPixmap
from GlobalActions import globalActionMap # for muting

from twisted.internet import reactor
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.protocols.basic import LineReceiver

import re
import os

from datetime import datetime

from . import debug, _
from reverselookup import ReverseLookupAndNotify

my_global_session = None

COUNTRY_CODES = [
	("0049", _("Germany")),
	("0031", _("The Netherlands")),
	("0033", _("France")),
	("0039", _("Italy")),
	("0041", _("Switzerland")),
	("0043", _("Austria"))
	]

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
		y2 = y1 * 1280 / 720
	elif y1 == -1:
		y1 = y2 * 720 / 1280
	return scale(y2, y1, 1280, 720, DESKTOP_WIDTH)


def scaleV(y2, y1):
	if y2 == -1:
		y2 = y1 * 720 / 576
	elif y1 == -1:
		y1 = y2 * 576 / 720
	return scale(y2, y1, 720, 576, DESKTOP_HEIGHT)


def scale(y2, y1, x2, x1, x):
	return (y2 - y1) * (x - x1) / (x2 - x1) + y1


def getMountedDevices():
	def handleMountpoint(loc):
		# debug("[NcidClient] handleMountpoint: %s" %repr(loc))
		mp = loc[0]
		while mp[-1] == '/':
			mp = mp[:-1]

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
	debug("[NcidClient] getMountedDevices1: %s" % repr(mountedDevs))
	mountedDevs = filter(lambda path: os.path.isdir(path[0]) and os.access(path[0], os.W_OK | os.X_OK), mountedDevs)
	# put this after the write/executable check, that is far too slow...
	netDir = resolveFilename(SCOPE_MEDIA, "net")
	if os.path.isdir(netDir):
		mountedDevs += map(lambda p: (os.path.join(netDir, p), _("Network mount")), os.listdir(netDir))
	mountedDevs = map(handleMountpoint, mountedDevs)
	return mountedDevs


config.plugins.NcidClient = ConfigSubsection()
config.plugins.NcidClient.debug = ConfigEnableDisable(default=False)
config.plugins.NcidClient.muteOnCall = ConfigEnableDisable(default=False)
config.plugins.NcidClient.hostname = ConfigText(default="easy.box", fixed_size=False)
config.plugins.NcidClient.port = ConfigInteger(limits=[1, 65535], default=3333)
config.plugins.NcidClient.afterStandby = ConfigSelection(choices=[("none", _("show nothing")), ("inList", _("show as list")), ("each", _("show each call"))])
config.plugins.NcidClient.timeout = ConfigInteger(default=15, limits=(0, 60))
config.plugins.NcidClient.lookup = ConfigEnableDisable(default=False)
config.plugins.NcidClient.internal = ConfigEnableDisable(default=False)

config.plugins.NcidClient.addcallers = ConfigEnableDisable(default=False)
config.plugins.NcidClient.enable = ConfigEnableDisable(default=True)
config.plugins.NcidClient.extension = ConfigText(default='1', fixed_size=False)
config.plugins.NcidClient.extension.setUseableChars('0123456789')
config.plugins.NcidClient.showType = ConfigEnableDisable(default=True)
config.plugins.NcidClient.prefix = ConfigText(default="", fixed_size=False)
config.plugins.NcidClient.prefix.setUseableChars('0123456789')
config.plugins.NcidClient.connectionVerbose = ConfigEnableDisable(default=True)
config.plugins.NcidClient.phonebook = ConfigEnableDisable(default=False)
config.plugins.NcidClient.phonebookLocation = ConfigSelection(choices=getMountedDevices())
config.plugins.NcidClient.country = ConfigSelection(choices=COUNTRY_CODES)
config.plugins.NcidClient.name = ConfigText(default="", fixed_size=False)
config.plugins.NcidClient.number = ConfigText(default="", fixed_size=False)
config.plugins.NcidClient.number.setUseableChars('0123456789')

phonebook = None
ncidsrv = None

avon = {}


def initAvon():
	avonFileName = resolveFilename(SCOPE_PLUGINS, "Extensions/NcidClient/avon.dat")
	if os.path.exists(avonFileName):
		with open(avonFileName) as file:
			for line in file:
				line = line.decode("iso-8859-1").encode('utf-8')
				if line[0] == '#':
					continue
				parts = line.split(':')
				if len(parts) == 2:
					avon[parts[0].replace('-', '').replace('*', '').replace('/', '')] = parts[1]


def resolveNumberWithAvon(number, countrycode):
	if not number or number[0] != '0':
		return ""

	countrycode = countrycode.replace('00', '+')
	if number[:2] == '00':
		normNumber = '+' + number[2:]
	elif number[:1] == '0':
		normNumber = countrycode + number[1:]
	else: # this should can not happen, but safety first
		return ""

	# debug('normNumer: ' + normNumber)
	for i in reversed(range(min(10, len(number)))):
		if normNumber[:i] in avon:
			return '[' + avon[normNumber[:i]].strip() + ']'
	return ""


def handleReverseLookupResult(name):
	found = re.match("NA: ([^;]*);VN: ([^;]*);STR: ([^;]*);HNR: ([^;]*);PLZ: ([^;]*);ORT: ([^;]*)", name)
	if found:
		(name, firstname, street, streetno, zipcode, city) = (found.group(1),
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
	callbycallFileName = resolveFilename(SCOPE_PLUGINS, "Extensions/NcidClient/callbycall_world.xml")
	if os.path.exists(callbycallFileName):
		dom = parse(callbycallFileName)
		for top in dom.getElementsByTagName("callbycalls"):
			for cbc in top.getElementsByTagName("country"):
				code = cbc.getAttribute("code").replace("+", "00")
				cbcInfos[code] = cbc.getElementsByTagName("callbycall")
	else:
		debug("[NcidClient] initCbC: callbycallFileName does not exist?!?!")


def stripCbCPrefix(number, countrycode):
	if number and number[:2] != "00" and countrycode in cbcInfos:
		for cbc in cbcInfos[countrycode]:
			if len(cbc.getElementsByTagName("length")) < 1 or len(cbc.getElementsByTagName("prefix")) < 1:
				debug("[NcidClient] stripCbCPrefix: entries for " + countrycode + " %s invalid")
				return number
			length = int(cbc.getElementsByTagName("length")[0].childNodes[0].data)
			prefix = cbc.getElementsByTagName("prefix")[0].childNodes[0].data
			# if re.match('^'+prefix, number):
			if number[:len(prefix)] == prefix:
				return number[length:]
	return number


FBF_boxInfo = 0
FBF_upTime = 1
FBF_ipAddress = 2
FBF_wlanState = 3
FBF_dslState = 4
FBF_tamActive = 5
FBF_dectActive = 6
FBF_faxActive = 7
FBF_rufumlActive = 8


class NcidCall:
	def __init__(self):
		debug("[NcidCall] __init__")
		self._callScreen = None
		self._callTimestamp = 0
		self._callList = []

	def _notify(self, text):
		debug("[NcidCall] notify: " + text)
		self._md5LoginTimestamp = None
		if self._callScreen:
			debug("[NcidCall] notify: try to close callScreen")
			self._callScreen.close()
			self._callScreen = None
		Notifications.AddNotification(MessageBox, text, type=MessageBox.TYPE_ERROR, timeout=config.plugins.NcidClient.timeout.value)


class NcidClientPhonebook:
	def __init__(self):
		debug("[NcidClientPhonebook] init")
		# Beware: strings in phonebook.phonebook have to be in utf-8!
		self.phonebook = {}
		self.reload()

	def reload(self):
		debug("[NcidClientPhonebook] reload")
		# Beware: strings in phonebook.phonebook have to be in utf-8!
		self.phonebook = {}

		if not config.plugins.NcidClient.enable.value:
			return

		phonebookFilename = os.path.join(config.plugins.NcidClient.phonebookLocation.value, "PhoneBook.txt")
		if config.plugins.NcidClient.phonebook.value and os.path.exists(phonebookFilename):
			debug("[NcidClientPhonebook] reload: read " + phonebookFilename)
			phonebookTxtCorrupt = False
			self.phonebook = {}
			for line in open(phonebookFilename):
				try:
					# Beware: strings in phonebook.phonebook have to be in utf-8!
					line = line.decode("utf-8")
				except UnicodeDecodeError: # this is just for the case, somebody wrote latin1 chars into PhoneBook.txt
					try:
						line = line.decode("iso-8859-1")
						debug("[NcidClientPhonebook] Fallback to ISO-8859-1 in %s" % line)
						phonebookTxtCorrupt = True
					except UnicodeDecodeError:
						debug("[NcidClientPhonebook] Could not parse internal Phonebook Entry %s" % line)
						phonebookTxtCorrupt = True
				line = line.encode("utf-8")
				elems = line.split('#')
				if len(elems) == 2:
					try:
						self.phonebook[elems[0]] = elems[1]
					except ValueError: # how could this possibly happen?!?!
						debug("[NcidClientPhonebook] Could not parse internal Phonebook Entry %s" % line)
						phonebookTxtCorrupt = True
				else:
					debug("[NcidClientPhonebook] Could not parse internal Phonebook Entry %s" % line)
					phonebookTxtCorrupt = True

			if phonebookTxtCorrupt:
				# dump phonebook to PhoneBook.txt
				debug("[NcidClientPhonebook] dump Phonebook.txt")
				try:
					os.rename(phonebookFilename, phonebookFilename + ".bck")
					fNew = open(phonebookFilename, 'w')
					# Beware: strings in phonebook.phonebook are utf-8!
					for (number, name) in self.phonebook.iteritems():
						# Beware: strings in PhoneBook.txt have to be in utf-8!
						fNew.write(number + "#" + name.encode("utf-8"))
					fNew.close()
				except (IOError, OSError):
					debug("[NcidClientPhonebook] error renaming or writing to %s" % phonebookFilename)

	def search(self, number):
		# debug("[NcidClientPhonebook] Searching for %s" %number)
		name = ""
		if not self.phonebook or not number:
			return

		if config.plugins.NcidClient.prefix.value:
			prefix = config.plugins.NcidClient.prefix.value
			if number[0] != '0':
				number = prefix + number
				# debug("[NcidClientPhonebook] search: added prefix: %s" %number)
			elif number[:len(prefix)] == prefix and number[len(prefix):] in self.phonebook:
				# debug("[NcidClientPhonebook] search: same prefix")
				name = self.phonebook[number[len(prefix):]]
				# debug("[NcidClientPhonebook] search: result: %s" %name)
		else:
			prefix = ""

		if not name and number in self.phonebook:
			name = self.phonebook[number]

		return name.replace(", ", "\n").strip()

	def add(self, number, name):
		'''

		@param number: number of entry
		@param name: name of entry, has to be in utf-8
		'''
		debug("[NcidClientPhonebook] add")
		name = name.replace("\n", ", ").replace('#', '') # this is just for safety reasons. add should only be called with newlines converted into commas
		self.remove(number)
		self.phonebook[number] = name
		if number and number != 0:
			if config.plugins.NcidClient.phonebook.value:
				try:
					name = name.strip() + "\n"
					string = "%s#%s" % (number, name)
					# Beware: strings in PhoneBook.txt have to be in utf-8!
					f = open(os.path.join(config.plugins.NcidClient.phonebookLocation.value, "PhoneBook.txt"), 'a')
					f.write(string)
					f.close()
					debug("[NcidClientPhonebook] added %s with %s to Phonebook.txt" % (number, name.strip()))
					return True

				except IOError:
					return False

	def remove(self, number):
		if number in self.phonebook:
			debug("[NcidClientPhonebook] remove entry in phonebook")
			del self.phonebook[number]
			if config.plugins.NcidClient.phonebook.value:
				try:
					phonebookFilename = os.path.join(config.plugins.NcidClient.phonebookLocation.value, "PhoneBook.txt")
					debug("[NcidClientPhonebook] remove entry in Phonebook.txt")
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
					os.rename(phonebookFilename + str(os.getpid()), phonebookFilename)
					debug("[NcidClientPhonebook] removed %s from Phonebook.txt" % number)
					return True

				except (IOError, OSError):
					debug("[NcidClientPhonebook] error removing %s from %s" % (number, phonebookFilename))
		return False

	class NcidDisplayPhonebook(Screen, NumericalTextInput):

		def __init__(self, session):
			self.entriesWidth = DESKTOP_WIDTH * scaleH(75, 85) / 100
			self.height = DESKTOP_HEIGHT * 0.75
			numberFieldWidth = scaleH(220, 160)
			fieldWidth = self.entriesWidth - 5 - numberFieldWidth - 10
			fontSize = scaleV(22, 18)
			fontHeight = scaleV(24, 20)
			buttonGap = (self.entriesWidth - 4 * 140) / 5
			debug("[NcidDisplayPhonebook] width: " + str(self.entriesWidth))
			self.skin = """
				<screen name="NcidDisplayPhonebook" position="center,center" size="%d,%d" title="Phonebook" >
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
						self.entriesWidth - scaleH(40, 5), self.height - scaleV(20, 5) - 5 - 5 - 40, # entries size
						0, 0, fieldWidth, scaleH(24, 20), # name pos/size
						fieldWidth + 5, 0, numberFieldWidth, scaleH(24, 20), # dir pos/size
						fontSize, # fontsize
						fontHeight, # itemHeight
						self.height - 40 - 5, # eLabel position vertical
						self.entriesWidth, # eLabel width
						buttonGap, self.height - 40, "skin_default/buttons/red.png", # ePixmap red
						2 * buttonGap + 140, self.height - 40, "skin_default/buttons/green.png", # ePixmap green
						3 * buttonGap + 2 * 140, self.height - 40, "skin_default/buttons/yellow.png", # ePixmap yellow
						4 * buttonGap + 3 * 140, self.height - 40, "skin_default/buttons/blue.png", # ePixmap blue
						buttonGap, self.height - 40, scaleV(22, 21), # widget red
						2 * buttonGap + 140, self.height - 40, scaleV(22, 21), # widget green
						3 * buttonGap + 2 * 140, self.height - 40, scaleV(22, 21), # widget yellow
						4 * buttonGap + 3 * 140, self.height - 40, scaleV(22, 21), # widget blue
						)

			# debug("[NcidDisplayCalls] skin: " + self.skin)
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
				"ok": self.showEntry, }, -2)

			self["entries"] = List([])
			debug("[NcidClientPhonebook] displayPhonebook init")
			self.help_window = None
			self.sortlist = []
			self.onLayoutFinish.append(self.setWindowTitle)
			self.display()

		def setWindowTitle(self):
			# TRANSLATORS: this is a window title.
			self.setTitle(_("Phonebook"))

		def display(self, filterNumber=""):
			debug("[NcidClientPhonebook] displayPhonebook/display")
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
						debug("[NcidClientPhonebook] displayPhonebook/display: corrupt phonebook entry for %s" % number)
						# self.session.open(MessageBox, _("Corrupt phonebook entry\nfor number %s\nDeleting.") %number, type = MessageBox.TYPE_ERROR)
						phonebook.remove(number)
						continue
				else:
					if filterNumber:
						filterNumber = filterNumber.lower()
						if low.find(filterNumber) == -1:
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
				debug("[NcidClientPhonebook] displayPhonebook/showEntry %s" % (repr(cur)))
				number = cur[2]
				name = cur[0]
				self.session.open(NcidOfferAction, self, number, name)

		def delete(self):
			cur = self["entries"].getCurrent()
			if cur:
				debug("[NcidClientPhonebook] displayPhonebook/delete %s" % (repr(cur)))
				self.session.openWithCallback(
					self.deleteConfirmed,
					MessageBox,
					_("Do you really want to delete entry for\n\n%(number)s\n\n%(name)s?")
					% {'number': str(cur[2]), 'name': str(cur[0]).replace(", ", "\n")}
								)
			else:
				self.session.open(MessageBox, _("No entry selected"), MessageBox.TYPE_INFO)

		def deleteConfirmed(self, ret):
			debug("[NcidClientPhonebook] displayPhonebook/deleteConfirmed")
			#
			# if ret: delete number from sortlist, delete number from phonebook.phonebook and write it to disk
			#
			cur = self["entries"].getCurrent()
			if cur:
				if ret:
					# delete number from sortlist, delete number from phonebook.phonebook and write it to disk
					debug("[NcidClientPhonebook] displayPhonebook/deleteConfirmed %s" % (repr(cur)))
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
					width = max(scaleH(-1, 570), noButtons * 140)
					height = scaleV(-1, 100) # = 5 + 126 + 40 + 5; 6 lines of text possible
					buttonsGap = (width - noButtons * 140) / (noButtons + 1)
					buttonsVPos = height - 40 - 5
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
										buttonsGap + 140 + buttonsGap, buttonsVPos, "skin_default/buttons/green.png",
										buttonsGap, buttonsVPos,
										buttonsGap + 140 + buttonsGap, buttonsVPos,
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
					}, -2)

					self.list = []
					ConfigListScreen.__init__(self, self.list, session=session)
					self.name = name
					self.number = number
					config.plugins.NcidClient.name.value = name
					config.plugins.NcidClient.number.value = number
					self.list.append(getConfigListEntry(_("Name"), config.plugins.NcidClient.name))
					self.list.append(getConfigListEntry(_("Number"), config.plugins.NcidClient.number))
					self["config"].list = self.list
					self["config"].l.setList(self.list)
					self.onLayoutFinish.append(self.setWindowTitle)

				def setWindowTitle(self):
					# TRANSLATORS: this is a window title.
					self.setTitle(_("Add entry to phonebook"))

				def add(self):
					# get texts from Screen
					# add (number,name) to sortlist and phonebook.phonebook and disk
					self.name = config.plugins.NcidClient.name.value
					self.number = config.plugins.NcidClient.number.value
					if not self.number or not self.name:
						self.session.open(MessageBox, _("Entry incomplete."), type=MessageBox.TYPE_ERROR)
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

			debug("[NcidClientPhonebook] displayPhonebook/add")
			if not parent:
				parent = self
			self.session.open(AddScreen, parent, number, name)

		def edit(self):
			debug("[NcidClientPhonebook] displayPhonebook/edit")
			cur = self["entries"].getCurrent()
			if cur is None:
				self.session.open(MessageBox, _("No entry selected"), MessageBox.TYPE_INFO)
			else:
				self.add(self, cur[2], cur[0])

		def search(self):
			debug("[NcidClientPhonebook] displayPhonebook/search")
			self.help_window = self.session.instantiateDialog(NumericalTextInputHelpDialog, self)
			self.help_window.show()
			# VirtualKeyboard instead of InputBox?
			self.session.openWithCallback(self.doSearch, InputBox, _("Enter Search Terms"), _("Search phonebook"))

		def doSearch(self, searchTerms):
			if not searchTerms:
				searchTerms = ""
			debug("[NcidClientPhonebook] displayPhonebook/doSearch: " + searchTerms)
			if self.help_window:
				self.session.deleteDialog(self.help_window)
				self.help_window = None
			self.display(searchTerms)

		def exit(self):
			self.close()


phonebook = NcidClientPhonebook()


class NcidClientSetup(Screen, ConfigListScreen):

	def __init__(self, session, args=None): #@UnusedVariable # pylint: disable=W0613
		self.width = scaleH(20 + 4 * (140 + 90) + 2 * (35 + 40) + 20, 4 * 140 + 2 * 35)
		width = self.width
		debug("[NcidClientSetup] width: " + str(self.width))
		self.skin = """
			<screen name="NcidClientSetup" position="center,center" size="%d,%d" title="NcidClient Setup" >
			<eLabel position="0,0" size="%d,2" backgroundColor="#aaaaaa" />
			<eLabel position="0,%d" size="%d,2" backgroundColor="#aaaaaa" />
			<widget name="config" position="%d,%d" size="%d,%d" scrollbarMode="showOnDemand" backgroundColor="#20040404" transparent="1" />
			<eLabel position="0,%d" size="%d,2" backgroundColor="#aaaaaa" />
			<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="on" />
			<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="on" />
			<widget name="key_red" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			<widget name="key_green" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
			</screen>""" % (
						# (DESKTOP_WIDTH-width)/2, scaleV(100, 73), # position
						width, scaleV(560, 430), # size
						width, # eLabel width
						scaleV(40, 50), # eLabel position vertical
						width, # eLabel width
						scaleH(40, 5), scaleV(60, 57), # config position
						scaleH(width - 80, width - 10), scaleV(453, 328), # config size
						scaleV(518, 390), # eLabel position vertical
						width, # eLabel width
						scaleH(20, 0), scaleV(525, 395), "skin_default/buttons/red.png", # pixmap red
						scaleH(20 + 140 + 90, 140), scaleV(525, 395), "skin_default/buttons/green.png", # pixmap green
						scaleH(20, 0), scaleV(525, 395), scaleV(21, 21), # widget red
						scaleH(20 + (140 + 90), 140), scaleV(525, 395), scaleV(21, 21), # widget green
													)

		Screen.__init__(self, session)
		self.session = session

		self.list = []

		# Initialize Buttons
		# TRANSLATORS: keep it short, this is a button
		self["key_red"] = Button(_("Cancel"))
		# TRANSLATORS: keep it short, this is a button
		self["key_green"] = Button(_("OK"))

		self["setupActions"] = ActionMap(["ColorActions", "OkCancelActions", "MenuActions", "EPGSelectActions"],
		{
			"red": self.cancel,
			"green": self.save,
			"cancel": self.cancel,
			"ok": self.save,
		}, -2)

		ConfigListScreen.__init__(self, self.list, session=session)

		# get new list of locations for PhoneBook.txt
		self._mountedDevices = getMountedDevices()
		self.createSetup()
		self.onLayoutFinish.append(self.setWindowTitle)

	def setWindowTitle(self):
		# TRANSLATORS: this is a window title.
		self.setTitle(_("NCID Client - Setup"))

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.createSetup()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.createSetup()

	def createSetup(self):
		self.list = []
		self.list.append(getConfigListEntry(_("Call monitoring"), config.plugins.NcidClient.enable))
		if config.plugins.NcidClient.enable.value:
			self.list.append(getConfigListEntry(_("NCID server (Name or IP)"), config.plugins.NcidClient.hostname))
			self.list.append(getConfigListEntry(_("NCID server listening port (1-65535)"), config.plugins.NcidClient.port))

			self.list.append(getConfigListEntry(_("Show after Standby"), config.plugins.NcidClient.afterStandby))

			# not only for outgoing: config.plugins.NcidClient.showOutgoing.value:
			self.list.append(getConfigListEntry(_("Areacode to add to calls without one (if necessary)"), config.plugins.NcidClient.prefix))
			self.list.append(getConfigListEntry(_("Timeout for Call Notifications (seconds)"), config.plugins.NcidClient.timeout))
			self.list.append(getConfigListEntry(_("Reverse Lookup Caller ID (select country below)"), config.plugins.NcidClient.lookup))
			if config.plugins.NcidClient.lookup.value:
				self.list.append(getConfigListEntry(_("Country"), config.plugins.NcidClient.country))

			self.list.append(getConfigListEntry(_("Use internal PhoneBook"), config.plugins.NcidClient.phonebook))
			if config.plugins.NcidClient.phonebook.value:
				if config.plugins.NcidClient.phonebookLocation.value in self._mountedDevices:
					config.plugins.NcidClient.phonebookLocation.setChoices(self._mountedDevices, config.plugins.NcidClient.phonebookLocation.value)
				else:
					config.plugins.NcidClient.phonebookLocation.setChoices(self._mountedDevices)
				path = config.plugins.NcidClient.phonebookLocation.value
				# check whether we can write to PhoneBook.txt
				if os.path.exists(os.path.join(path[0], "PhoneBook.txt")):
					if not os.access(os.path.join(path[0], "PhoneBook.txt"), os.W_OK):
						debug("[NcidClientSetup] createSetup: %s/PhoneBook.txt not writable, resetting to default" % (path[0]))
						config.plugins.NcidClient.phonebookLocation.setChoices(self._mountedDevices)
				elif not (os.path.isdir(path[0]) and os.access(path[0], os.W_OK | os.X_OK)):
					debug("[NcidClientSetup] createSetup: directory %s not writable, resetting to default" % (path[0]))
					config.plugins.NcidClient.phonebookLocation.setChoices(self._mountedDevices)

				self.list.append(getConfigListEntry(_("PhoneBook Location"), config.plugins.NcidClient.phonebookLocation))
				if config.plugins.NcidClient.lookup.value:
					self.list.append(getConfigListEntry(_("Automatically add new Caller to PhoneBook"), config.plugins.NcidClient.addcallers))

			self.list.append(getConfigListEntry(_("Strip Leading 0"), config.plugins.NcidClient.internal))
			self.list.append(getConfigListEntry(_("Show connection information popups"), config.plugins.NcidClient.connectionVerbose))

		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def save(self):
#		debug("[NcidClientSetup] save"
		for x in self["config"].list:
			x[1].save()
		if config.plugins.NcidClient.phonebookLocation.isChanged():
			global phonebook
			phonebook = NcidClientPhonebook()
		if ncid_call:
			if config.plugins.NcidClient.enable.value:
				ncid_call.connect()
			else:
				ncid_call.shutdown()
		self.close()

	def cancel(self):
#		debug("[NcidClientSetup] cancel"
		for x in self["config"].list:
			x[1].cancel()
		self.close()

	def displayPhonebook(self):
		if phonebook:
			if config.plugins.NcidClient.enable.value:
				self.session.open(phonebook.NcidDisplayPhonebook)
			else:
				self.session.open(MessageBox, _("Plugin not active"), type=MessageBox.TYPE_INFO)
		else:
			self.session.open(MessageBox, _("No phonebook"), type=MessageBox.TYPE_INFO)


standbyMode = False


class NcidCallList:
	def __init__(self):
		self.callList = []

	def add(self, date, number, caller):
		debug("[NcidCallList] add: %s %s" % (number, caller))
		if len(self.callList) > 10:
			if self.callList[0] != "Start":
				self.callList[0] = "Start"
			del self.callList[1]

		self.callList.append((number, date, caller))

	def display(self):
		debug("[NcidCallList] display")
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
				(number, date, caller) = call

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
						if (len(number) + 1 + len(caller)) <= 40:
							caller = number + ' ' + caller
						else:
							caller = number

				while (len(caller)) > 40:
					caller = caller[:-1]

				text = text + "%s - %s\n" % (date, caller)
				debug("[NcidCallList] display: '%s - %s'" % (date, caller))

		# display screen
		Notifications.AddNotification(MessageBox, text, type=MessageBox.TYPE_INFO)
		# TODO please HELP: from where can I get a session?
		# my_global_session.open(NcidDisplayCalls, text)
		self.callList = []


callList = NcidCallList()

global_muted = None


def notifyCall(date, number, caller):
	if Standby.inStandby is None or config.plugins.NcidClient.afterStandby.value == "each":
		global global_muted
		if config.plugins.NcidClient.muteOnCall.value and not global_muted:
			# eDVBVolumecontrol.getInstance().volumeMute() # with this, we get no mute icon...
			if not eDVBVolumecontrol.getInstance().isMuted():
				globalActionMap.actions["volumeMute"]()
		text = _("Incoming Call on %s from\n---------------------------------------------\n%s\n%s\n---------------------------------------------") % (date, number, caller)
		debug("[NcidClient] notifyCall:\n%s" % text)
		Notifications.AddNotification(MessageBox, text, type=MessageBox.TYPE_INFO, timeout=config.plugins.NcidClient.timeout.value)
		#Notifications.AddNotification(MessageBoxPixmap, text, number=number, name=caller, timeout=config.plugins.NcidClient.timeout.value)
	elif config.plugins.NcidClient.afterStandby.value == "inList":
		#
		# if not yet done, register function to show call list
		global standbyMode
		if not standbyMode:
			standbyMode = True
			Standby.inStandby.onHide.append(callList.display) #@UndefinedVariable
		# add text/timeout to call list
		callList.add(date, number, caller)
		debug("[NcidClient] notifyCall: added to callList")
	else: # this is the "None" case
		debug("[NcidClient] notifyCall: standby and no show")


#===============================================================================
#		We need a separate class for each invocation of reverseLookup to retain
#		the necessary data for the notification
#===============================================================================

countries = {}
reverselookupMtime = 0


class NcidReverseLookupAndNotify:
	def __init__(self, number, caller, date):
		'''

		Initiate a reverse lookup for the given number in the configured country
		@param number: number to be looked up
		@param caller: caller including name and address
		@param date: date of call
		'''
		debug("[NcidReverseLookupAndNotify] reverse Lookup for %s!" % number)
		self.number = number
		self.caller = caller
		self.date = date

		if number[0] != "0":
			self.notifyAndReset(number, caller)
			return

		ReverseLookupAndNotify(number, self.notifyAndReset, "UTF-8", config.plugins.NcidClient.country.value)

	def notifyAndReset(self, number, caller):
		'''

		this gets called with the result of the reverse lookup

		@param number: number
		@param caller: name and address of remote. it comes in with name, address and city separated by commas
		'''
		debug("[NcidReverseLookupAndNotify] got: %s" % caller)
		self.number = number
		name = handleReverseLookupResult(caller)
		if name:
			self.caller = name.replace(", ", "\n").replace('#', '')

			if self.number != 0 and config.plugins.NcidClient.addcallers.value:
				debug("[NcidReverseLookupAndNotify] add to phonebook")
				phonebook.add(self.number, self.caller)
		else:
			name = resolveNumberWithAvon(self.number, config.plugins.NcidClient.country.value)
			if not name:
				self.caller = _("UNKNOWN")
			else:
				self.caller = name
		notifyCall(self.date, self.number, self.caller)


class NcidLineReceiver(LineReceiver):
	def __init__(self):
		global global_muted
		global_muted = None
		self.resetValues()

	def resetValues(self):
		self.number = None
		self.caller = None
		self.date = '01011970'
		self.time = '0001'
		self.line = ''

	def notifyAndReset(self):
		notifyCall(self.date, self.number, self.caller)
		self.resetValues()

	def lineReceived(self, line):
		debug("[NcidLineReceiver] lineReceived: %s" % line)
#200 NCID Server:  ARC_ncidd 0.01
#CIDLOG: *DATE*21102010*TIME*1454*LINE**NMBR*089999999999*MESG*NONE*NAME*NO NAME*
#CIDLOG: *DATE*21102010*TIME*1456*LINE**NMBR*089999999999*MESG*NONE*NAME*NO NAME*
#CID: *DATE*22102010*TIME*1502*LINE**NMBR*089999999999*MESG*NONE*NAME*NO NAME*

#Callog entries begin with CIDLOG, "current" events begin with CID
#we don't want to do anything with log-entries
		if line.startswith("CID:"):
			line = line[6:]
			debug("[NcidLineReceiver.lineReceived] filtered Line: %s" % line)
		else:
			return

		items = line.split('*')

		for i in range(0, len(items)):
			item = items[i]

			if item == 'DATE':
				self.date = items[i + 1]
			elif item == 'TIME':
				self.time = items[i + 1]
			elif item == 'LINE':
				self.line = items[i + 1]
			elif item == 'NMBR':
				self.number = items[i + 1]
                        elif item == 'NAME':
                                self.myName = items[i + 1]

                if not self.myName:
                        self.myName = _("UNKNOWN")

                date = None
                try:
                        date = datetime.strptime("%s - %s" % (self.date, self.time), "%d%m%Y - %H%M")
                except:
                        date = datetime.strptime("%s - %s" % (self.date, self.time), "%m%d%Y - %H%M")

		self.date = date.strftime("%d.%m.%Y - %H:%M")

		if not self.number:
			debug("[NcidLineReceiver] lineReceived: no number")
			self.number = _("number suppressed")
			self.caller = self.myName
		else:
			if config.plugins.NcidClient.internal.value and len(self.number) > 3 and self.number[0] == "0":
				debug("[NcidLineReceiver] lineReceived: strip leading 0")
				self.number = self.number[1:]
			else:
				if self.number[0] != '0':
					debug("[NcidLineReceiver] lineReceived: add local prefix")
					self.number = config.plugins.NcidClient.prefix.value + self.number

			self.number = stripCbCPrefix(self.number, config.plugins.NcidClient.country.value)

			debug("[NcidLineReceiver] lineReceived phonebook.search: %s" % self.number)
			self.caller = phonebook.search(self.number)
			debug("[NcidLineReceiver] lineReceived phonebook.search reault: %s" % self.caller)
			if not self.caller:
				if config.plugins.NcidClient.lookup.value:
					NcidReverseLookupAndNotify(self.number, self.caller, self.date)
					return							# reverselookup is supposed to handle the message itself
				else:
					self.caller = self.myName

		self.notifyAndReset()


class NcidClientFactory(ReconnectingClientFactory):
	initialDelay = 20
	maxDelay = 30

	def __init__(self):
		self.hangup_ok = False

	def startedConnecting(self, connector): #@UnusedVariable # pylint: disable=W0613
		if config.plugins.NcidClient.connectionVerbose.value:
			Notifications.AddNotification(MessageBox, _("Connecting to NCID Server..."), type=MessageBox.TYPE_INFO, timeout=2)

	def buildProtocol(self, addr): #@UnusedVariable # pylint: disable=W0613
		global ncidsrv, phonebook
		if config.plugins.NcidClient.connectionVerbose.value:
			Notifications.AddNotification(MessageBox, _("Connected to NCID Server"), type=MessageBox.TYPE_INFO, timeout=4)
		self.resetDelay()
		initAvon()
		ncidsrv = NcidCall()
		phonebook = NcidClientPhonebook()
		return NcidLineReceiver()

	def clientConnectionLost(self, connector, reason):
		global ncidsrv
		if not self.hangup_ok and config.plugins.NcidClient.connectionVerbose.value:
			Notifications.AddNotification(MessageBox, _("Connection to NCID Server lost\n (%s)\nretrying...") % reason.getErrorMessage(), type=MessageBox.TYPE_INFO, timeout=config.plugins.NcidClient.timeout.value)
		ReconnectingClientFactory.clientConnectionLost(self, connector, reason)
		# config.plugins.NcidClient.enable.value = False
		ncidsrv = None

	def clientConnectionFailed(self, connector, reason):
		global ncidsrv
		if config.plugins.NcidClient.connectionVerbose.value:
			Notifications.AddNotification(MessageBox, _("Connecting to NCID Server failed\n (%s)\nretrying...") % reason.getErrorMessage(), type=MessageBox.TYPE_INFO, timeout=config.plugins.NcidClient.timeout.value)
		ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)
		# config.plugins.NcidClient.enable.value = False
		ncidsrv = None


class NcidClient:
	def __init__(self):
		self.dialog = None
		self.desc = None
		if config.plugins.NcidClient.enable.value:
			self.connect()

	def connect(self):
		self.abort()
		if config.plugins.NcidClient.enable.value:
			factory = NcidClientFactory()
			self.desc = (factory, reactor.connectTCP(config.plugins.NcidClient.hostname.value, config.plugins.NcidClient.port.value, factory))

	def shutdown(self):
		self.abort()

	def abort(self):
		if self.desc is not None:
			self.desc[0].hangup_ok = True
			self.desc[0].stopTrying()
			self.desc[1].disconnect()
			self.desc = None


def main(session):
	session.open(NcidClientSetup)


ncid_call = None


def autostart(reason, **kwargs):
	global ncid_call

	# ouch, this is a hack
	if "session" in kwargs:
		global my_global_session
		my_global_session = kwargs["session"]
		return

	debug("[NcidClient] - Autostart")
	if reason == 0:
		ncid_call = NcidClient()
	elif reason == 1:
		ncid_call.shutdown()
		ncid_call = None


def Plugins(**kwargs): #@UnusedVariable # pylint: disable=W0613,C0103
	what = _("Display Fon calls on screen")
	return [PluginDescriptor(name="NCID Client", description=what, where=PluginDescriptor.WHERE_PLUGINMENU, icon="plugin.png", fnc=main),
		PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc=autostart)]
