# -*- coding: utf-8 -*-
'''
Update rev
$Author: michael $
$Revision: 1481 $
$Date: 2017-07-04 10:28:00 +0200 (Tue, 04 Jul 2017) $
$Id: plugin.py 1481 2017-07-04 08:28:00Z michael $
'''


# C0111 (Missing docstring)
# C0103 (Invalid name)
# C0301 (line too long)
# W0603 (global statement)
# W0141 (map, filter, etc.)
# W0110 lambda with map,filter
# W0403 Relative import
# W1401 Anomalous backslash in string
# C0302 too-many-lines
# E401 multiple imports on one line
# E501 line too long (85 > 79 characters)
# pylint: disable=C0111,C0103,C0301,W0603,W0403,C0302,W0312

import re, time, os, traceback, json
from itertools import cycle, izip
import base64
from logging import NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL
import logging
from xml.dom.minidom import parse
import binascii

from enigma import getDesktop
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.NumericalTextInputHelpDialog import NumericalTextInputHelpDialog
from Screens.InputBox import InputBox
from Screens import Standby
from Screens.HelpMenu import HelpableScreen
from Screens.LocationBox import LocationBox

from enigma import eTimer, eSize, ePoint  # @UnresolvedImport # pylint: disable=E0611
from enigma import eDVBVolumecontrol, eConsoleAppContainer  # @UnresolvedImport # pylint: disable=E0611
# BgFileEraser = eBackgroundFileEraser.getInstance()
# BgFileEraser.erase("blabla.txt")

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Button import Button
from Components.Pixmap import Pixmap
from Components.Sources.List import List
from Components.ConfigList import ConfigListScreen
from Components.config import config, ConfigSubsection, ConfigSelection, ConfigDirectory, \
	getConfigListEntry, ConfigText, ConfigInteger, ConfigYesNo, ConfigOnOff, ConfigPassword

from Plugins.Plugin import PluginDescriptor
from Tools import Notifications
from Tools.NumericalTextInput import NumericalTextInput
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_CONFIG, SCOPE_CURRENT_SKIN, \
	SCOPE_CURRENT_PLUGIN
from Tools.LoadPixmap import LoadPixmap
from GlobalActions import globalActionMap  # for muting

from twisted.internet import reactor  # @UnresolvedImport
from twisted.internet.protocol import ReconnectingClientFactory  # @UnresolvedImport
from twisted.protocols.basic import LineReceiver  # @UnresolvedImport

import FritzOutlookCSV, FritzLDIF
from nrzuname import ReverseLookupAndNotifier
from . import _, __  # @UnresolvedImport # pylint: disable=W0611,F0401

# import codecs
# encode = lambda x : codecs.encode(x, "rot13")
# decode = lambda x : codecs.decode(x, "rot13")

# decode = encode = lambda x : ''.join(chr(ord(c)^ord(k)) for c,k in izip(x, cycle('secret key')))
def encode(x):
	return base64.encodestring(''.join(chr(ord(c) ^ ord(k)) for c, k in izip(x, cycle('secret key')))).strip()
def decode(x):
	return ''.join(chr(ord(c) ^ ord(k)) for c, k in izip(base64.decodestring(x), cycle('secret key')))

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

my_global_session = None

config.plugins.FritzCall = ConfigSubsection()
config.plugins.FritzCall.fwVersion = ConfigSelection(choices = [(None, _("not configured")), ("old", _("before 05.27")), ("05.27", "05.27, 05.28"), ("05.50", _("05.29 until below 6.35")), ("06.35", _("06.35 and newer"))], default = None)
# config.plugins.FritzCall.fwVersion = ConfigSelection(choices = [(None, _("not configured")), ("old", _("before 05.27")), ("05.27", "05.27, 05.28"), ("05.50", _("05.29 until below 6.35")), ("06.35", _("06.35 and newer")), ("upnp", "Experimental")], default = None)
# config.plugins.FritzCall.fwVersion = ConfigSelection(choices=[(None, _("not configured")), ("old", _("before 05.27")), ("05.27", "05.27, 05.28"), ("05.50", _("05.29 and newer"))], default=None)
config.plugins.FritzCall.debug = ConfigSelection(choices = [
														(str(NOTSET), _("nothing")),
														(str(DEBUG), "DEBUG"),
														(str(INFO), "INFO"),
														(str(WARNING), "WARNING"),
														(str(ERROR), "ERROR"),
														(str(CRITICAL), "CRITICAL")],
												default = str(ERROR))
# config.plugins.FritzCall.muteOnCall = ConfigSelection(choices=[(None, _("no")), ("ring", _("on ring")), ("connect", _("on connect"))])
# config.plugins.FritzCall.muteOnCall = ConfigSelection(choices=[(None, _("no")), ("ring", _("on ring"))])
config.plugins.FritzCall.muteOnCall = ConfigYesNo(default = False)
config.plugins.FritzCall.muteOnOutgoingCall = ConfigYesNo(default = False)
config.plugins.FritzCall.hostname = ConfigText(default = "fritz.box", fixed_size = False)
config.plugins.FritzCall.afterStandby = ConfigSelection(choices = [("none", _("show nothing")), ("inList", _("show as list")), ("each", _("show each call"))])
config.plugins.FritzCall.filter = ConfigYesNo(default = False)
config.plugins.FritzCall.filtermsn = ConfigText(default = "", fixed_size = False)
config.plugins.FritzCall.filtermsn.setUseableChars('0123456789,')
config.plugins.FritzCall.filterCallList = ConfigYesNo(default = True)
config.plugins.FritzCall.showBlacklistedCalls = ConfigYesNo(default = False)
config.plugins.FritzCall.showOutgoingCalls = ConfigYesNo(default = False)
config.plugins.FritzCall.timeout = ConfigInteger(default = 15, limits = (0, 60))
config.plugins.FritzCall.lookup = ConfigYesNo(default = False)
config.plugins.FritzCall.internal = ConfigYesNo(default = False)
config.plugins.FritzCall.fritzphonebook = ConfigYesNo(default = False)
config.plugins.FritzCall.fritzphonebookName = ConfigText(default = _('Phonebook'), fixed_size = False)
config.plugins.FritzCall.fritzphonebookShowInternal = ConfigYesNo(default = True)
config.plugins.FritzCall.phonebook = ConfigYesNo(default = False)
config.plugins.FritzCall.addcallers = ConfigYesNo(default = False)
config.plugins.FritzCall.enable = ConfigOnOff(default = False)
config.plugins.FritzCall.username = ConfigText(default = 'BoxAdmin', fixed_size = False)
config.plugins.FritzCall.password = ConfigPassword(default = "", fixed_size = False)
config.plugins.FritzCall.extension = ConfigText(default = '1', fixed_size = False)
config.plugins.FritzCall.extension.setUseableChars('0123456789')
config.plugins.FritzCall.showType = ConfigYesNo(default = True)
config.plugins.FritzCall.showShortcut = ConfigYesNo(default = False)
config.plugins.FritzCall.showVanity = ConfigYesNo(default = False)
config.plugins.FritzCall.prefix = ConfigText(default = "", fixed_size = False)
config.plugins.FritzCall.prefix.setUseableChars('0123456789')
config.plugins.FritzCall.connectionVerbose = ConfigYesNo(default = True)
config.plugins.FritzCall.ignoreUnknown = ConfigYesNo(default = False)
config.plugins.FritzCall.reloadPhonebookTime = ConfigInteger(default = 8, limits = (0, 99))
config.plugins.FritzCall.FritzExtendedSearchFaces = ConfigYesNo(default = False)
config.plugins.FritzCall.FritzExtendedSearchNames = ConfigYesNo(default = False)
config.plugins.FritzCall.phonebookLocation = ConfigDirectory(default = resolveFilename(SCOPE_CONFIG))
config.plugins.FritzCall.advancedSkin = ConfigYesNo(default = False)
config.plugins.FritzCall.guestSSID = ConfigText(default = "FRITZ!Box Gastzugang", fixed_size = False)
config.plugins.FritzCall.guestSecure = ConfigYesNo(default = True)
config.plugins.FritzCall.guestPassword = ConfigPassword(default = encode("guestguest!!!"), fixed_size = False)

guestWLANUptime = [(None, _('Not deactivating after time')), "15", "30", "45", "60", "90", "120", "180", "240", "300", "360", "480", "600", "720", "900", "1080", "1260"]
config.plugins.FritzCall.guestUptime = ConfigSelection(choices = guestWLANUptime, default = "30")

countryCodes = [
	("0049", _("Germany")),
	("0031", _("The Netherlands")),
	("0033", _("France")),
	("0039", _("Italy")),
	("0041", _("Switzerland")),
	("0043", _("Austria")),
	("", _("Others"))
	]
config.plugins.FritzCall.country = ConfigSelection(choices = countryCodes)
config.plugins.FritzCall.countrycode = ConfigText(default = "0049", fixed_size = False)
config.plugins.FritzCall.countrycode.setUseableChars('0123456789')

FBF_ALL_CALLS = "."
FBF_IN_CALLS = "1"
FBF_MISSED_CALLS = "2"
FBF_OUT_CALLS = "3"
FBF_BLOCKED_CALLS = "4"
fbfCallsChoices = {
				FBF_ALL_CALLS: _("All calls"),
				FBF_IN_CALLS: _("Incoming calls"),
				FBF_MISSED_CALLS: _("Missed calls"),
				FBF_OUT_CALLS: _("Outgoing calls")
				}
config.plugins.FritzCall.fbfCalls = ConfigSelection(choices = fbfCallsChoices)

config.plugins.FritzCall.name = ConfigText(default = "", fixed_size = False)
config.plugins.FritzCall.number = ConfigText(default = "", fixed_size = False)
config.plugins.FritzCall.number.setUseableChars('0123456789')

logger = logging.getLogger("FritzCall")
logger.setLevel(int(config.plugins.FritzCall.debug.value))
fileHandler = logging.FileHandler('/tmp/FritzDebug.log', mode = 'w')
fileHandler.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s %(name)-26s %(funcName)s %(message)-15s', '%Y-%m-%d %H:%M:%S'))
logger.addHandler(fileHandler)

debug = logger.debug
info = logger.info
warn = logger.warn
error = logger.error
exception = logger.exception

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
				avon[parts[0].replace('-', '').replace('*', '').replace('/', '')] = parts[1]

def resolveNumberWithAvon(number, countrycode):
	if not countrycode or not number or number[0] != '0':
		return ""

	countrycode = countrycode.replace('00', '+')
	if number[:2] == '00':
		normNumber = '+' + number[2:]
	elif number[:1] == '0':
		normNumber = countrycode + number[1:]
	else:  # this should can not happen, but safety first
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

cbcInfos = {}
def initCbC():
	callbycallFileName = resolveFilename(SCOPE_PLUGINS, "Extensions/FritzCall/callbycall_world.xml")
	if os.path.exists(callbycallFileName):
		dom = parse(callbycallFileName)
		for top in dom.getElementsByTagName("callbycalls"):
			for cbc in top.getElementsByTagName("country"):
				code = cbc.getAttribute("code").replace("+", "00")
				cbcInfos[code] = cbc.getElementsByTagName("callbycall")
	else:
		error("[FritzCall] initCbC: callbycallFileName does not exist?!?!")

def stripCbCPrefix(number, countrycode):
	if not countrycode:
		return number

	if number and number[:2] != "00" and countrycode in cbcInfos:
		for cbc in cbcInfos[countrycode]:
			if len(cbc.getElementsByTagName("length")) < 1 or len(cbc.getElementsByTagName("prefix")) < 1:
				warn("[FritzCall] stripCbCPrefix: entries for " + countrycode + " %s invalid")
				return number
			length = int(cbc.getElementsByTagName("length")[0].childNodes[0].data)
			prefix = cbc.getElementsByTagName("prefix")[0].childNodes[0].data
			# if re.match('^'+prefix, number):
			if number[:len(prefix)] == prefix:
				return number[length:]
	return number

import FritzCallFBF  # wrong-import-position # pylint: disable=

class FritzAbout(Screen):

	def __init__(self, session):
		if not config.plugins.FritzCall.advancedSkin.value:
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
								width, height,  # size
								(height - scaleV(150, 130)) / 2,  # text vertical position
								textFieldWidth,
								scaleV(150, 130),  # text height
								scaleV(24, 21),  # text font size
								resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/FritzCall/images/fritz.png"),  # 150x110
								5 + 150 + 5 + textFieldWidth + 5,  # qr code horizontal offset
								resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/FritzCall/images/website.png"),  # 175x175
								width - 40,  # url width
								scaleV(24, 21)  # url font size
								)
		else:
			if DESKTOP_WIDTH <= 720:
				self.skin = """
				<!-- SD screen -->
				<screen name="FritzAbout" position="center,center" size="580,240" title=" ">
					<ePixmap alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/fritz.png" position="5,50" size="150,110" />
					<widget font="Regular;18" name="text" position="175,10" size="210,160" />
					<ePixmap alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/website.png" position="400,10" size="175,175" />
					<widget font="Regular;18" foregroundColor="#bab329" halign="center" name="url" position="10,205" size="560,25" />
				</screen>"""
			elif DESKTOP_WIDTH <= 1280:
				self.skin = """
				<!-- HD screen -->
				<screen name="FritzAbout" position="center,center" size="780,240" title=" ">
					<ePixmap alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/fritz.png" position="10,50" size="150,110" />
					<widget font="Regular;22" name="text" position="200,10" size="350,160" />
					<ePixmap alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/website.png" position="580,10" size="175,175" />
					<widget font="Regular;22" foregroundColor="#bab329" halign="center" name="url" position="10,200" size="760,40" />
				</screen>"""
			elif DESKTOP_WIDTH <= 1920:
				self.skin = """
				<!-- Fullhd screen -->
				<screen name="FritzAbout" position="center,center" size="880,300" title=" ">
					<ePixmap alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/fritz.png" position="10,50" size="150,110" />
					<widget font="Regular;30" name="text" position="200,10" size="450,220" />
					<ePixmap alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/website.png" position="680,30" size="175,175" />
					<widget font="Regular;30" foregroundColor="#bab329" halign="center" name="url" position="10,250" size="860,40" />
				</screen>
				"""
			else:
				self.skin = """
				<!-- UHD screen -->
				<screen name="FritzAbout" position="center,center" size="1880,460" title=" ">
					<ePixmap alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/fritz.png" position="10,60" size="300,220" />
					<widget font="Regular;60" name="text" position="350,10" size="1100,360" />
					<ePixmap alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/website.png" position="1570,20" size="300,300" />
					<widget font="Regular;58" foregroundColor="#bab329" halign="center" name="url" position="10,380" size="1860,65" />
				</screen>"""

		Screen.__init__(self, session)
		self["aboutActions"] = ActionMap(["OkCancelActions"],
		{
			"cancel": self.exit,
			"ok": self.exit,
		}, -2)
		self["text"] = Label(
							"FritzCall Plugin" + "\n\n" +
							"$Author: michael $"[1:-2] + "\n" +
							"$Revision: 1481 $"[1:-2] + "\n" +
							"$Date: 2017-07-04 10:28:00 +0200 (Tue, 04 Jul 2017) $"[1:23] + "\n"
							)
		self["url"] = Label("http://wiki.blue-panel.com/index.php/FritzCall")
		self.onLayoutFinish.append(self.setWindowTitle)

	def setWindowTitle(self):
		# TRANSLATORS: this is a window title.
		self.setTitle(_("About FritzCall"))

	def exit(self):
		self.close()

from FritzCallFBF import FBF_dectActive, FBF_faxActive, FBF_rufumlActive, FBF_tamActive, FBF_wlanState  # wrong-import-position # pylint: disable=
class FritzMenu(Screen, HelpableScreen):
	def __init__(self, session):
		if not fritzbox or not fritzbox.information:
			return

		if config.plugins.FritzCall.fwVersion.value == "old" or config.plugins.FritzCall.fwVersion.value == "05.27":
			fontSize = scaleV(24, 21)  # indeed this is font size +2
			noButtons = 2  # reset, wlan

			if fritzbox.information[FBF_tamActive]:
				noButtons += 1  # toggle mailboxes
			width = max(DESKTOP_WIDTH - scaleH(500, 250), noButtons * 140 + (noButtons + 1) * 10)
			# boxInfo 2 lines, gap, internet 2 lines, gap, dsl/wlan each 1 line, gap, buttons
			height = 5 + 2 * fontSize + 10 + 2 * fontSize + 10 + 2 * fontSize + 10 + 40 + 5
			if fritzbox.information[FBF_tamActive] is not None:
				height += fontSize
			if fritzbox.information[FBF_dectActive] is not None:
				height += fontSize
			if fritzbox.information[FBF_faxActive] is not None:
				height += fontSize
			if fritzbox.information[FBF_rufumlActive] is not None:
				height += fontSize
			buttonsGap = (width - noButtons * 140) / (noButtons + 1)
			buttonsVPos = height - 40 - 5

			varLinePos = 4
			if fritzbox.information[FBF_tamActive] is not None:
				mailboxLine = """
					<widget name="FBFMailbox" position="%d,%d" size="%d,%d" font="Regular;%d" />
					<widget name="mailbox_inactive" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="blend"/>
					<widget name="mailbox_active" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="blend"/>
					<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="blend" />
					<widget name="key_yellow" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
					""" % (
							40, 5 + 2 * fontSize + 10 + varLinePos * fontSize + 10,  # position mailbox
							width - 40 - 20, fontSize,  # size mailbox
							fontSize - 2,
							"skin_default/buttons/button_green_off.png",
							20, 5 + 2 * fontSize + 10 + varLinePos * fontSize + 10 + (fontSize - 16) / 2,  # position button mailbox
							"skin_default/buttons/button_green.png",
							20, 5 + 2 * fontSize + 10 + varLinePos * fontSize + 10 + (fontSize - 16) / 2,  # position button mailbox
							noButtons * buttonsGap + (noButtons - 1) * 140, buttonsVPos,
							noButtons * buttonsGap + (noButtons - 1) * 140, buttonsVPos,
					)
				varLinePos += 1
			else:
				mailboxLine = ""

			if fritzbox.information[FBF_dectActive] is not None:
				dectLine = """
					<widget name="FBFDect" position="%d,%d" size="%d,%d" font="Regular;%d" />
					<widget name="dect_inactive" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="blend"/>
					<widget name="dect_active" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="blend"/>
					""" % (
							40, 5 + 2 * fontSize + 10 + varLinePos * fontSize + 10,  # position dect
							width - 40 - 20, fontSize,  # size dect
							fontSize - 2,
							"skin_default/buttons/button_green_off.png",
							20, 5 + 2 * fontSize + 10 + varLinePos * fontSize + 10 + (fontSize - 16) / 2,  # position button dect
							"skin_default/buttons/button_green.png",
							20, 5 + 2 * fontSize + 10 + varLinePos * fontSize + 10 + (fontSize - 16) / 2,  # position button dect
					)
				varLinePos += 1
			else:
				dectLine = ""

			if fritzbox.information[FBF_faxActive] is not None:
				faxLine = """
					<widget name="FBFFax" position="%d,%d" size="%d,%d" font="Regular;%d" />
					<widget name="fax_inactive" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="blend"/>
					<widget name="fax_active" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="blend"/>
					""" % (
							40, 5 + 2 * fontSize + 10 + varLinePos * fontSize + 10,  # position dect
							width - 40 - 20, fontSize,  # size dect
							fontSize - 2,
							"skin_default/buttons/button_green_off.png",
							20, 5 + 2 * fontSize + 10 + varLinePos * fontSize + 10 + (fontSize - 16) / 2,  # position button dect
							"skin_default/buttons/button_green.png",
							20, 5 + 2 * fontSize + 10 + varLinePos * fontSize + 10 + (fontSize - 16) / 2,  # position button dect
					)
				varLinePos += 1
			else:
				faxLine = ""

			if fritzbox.information[FBF_rufumlActive] is not None:
				rufumlLine = """
					<widget name="FBFRufuml" position="%d,%d" size="%d,%d" font="Regular;%d" />
					<widget name="rufuml_inactive" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="blend"/>
					<widget name="rufuml_active" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="blend"/>
					""" % (
							40, 5 + 2 * fontSize + 10 + varLinePos * fontSize + 10,  # position dect
							width - 40 - 20, fontSize,  # size dect
							fontSize - 2,
							"skin_default/buttons/button_green_off.png",
							20, 5 + 2 * fontSize + 10 + varLinePos * fontSize + 10 + (fontSize - 16) / 2,  # position button dect
							"skin_default/buttons/button_green.png",
							20, 5 + 2 * fontSize + 10 + varLinePos * fontSize + 10 + (fontSize - 16) / 2,  # position button dect
					)
				varLinePos += 1
			else:
				rufumlLine = ""

			self.skin = """
				<screen name="FritzMenu" position="center,center" size="%d,%d" title="FRITZ!Box Fon Status" >
					<widget name="FBFInfo" position="%d,%d" size="%d,%d" font="Regular;%d" />
					<widget name="FBFInternet" position="%d,%d" size="%d,%d" font="Regular;%d" />
					<widget name="internet_inactive" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="blend"/>
					<widget name="internet_active" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="blend"/>
					<widget name="FBFDsl" position="%d,%d" size="%d,%d" font="Regular;%d" />
					<widget name="dsl_inactive" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="blend"/>
					<widget name="dsl_active" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="blend"/>
					<widget name="FBFWlan" position="%d,%d" size="%d,%d" font="Regular;%d" />
					<widget name="wlan_inactive" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="blend"/>
					<widget name="wlan_active" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="blend"/>
					%s
					%s
					%s
					%s
					<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="blend" />
					<widget name="key_red" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
					<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="blend" />
					<widget name="key_green" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				</screen>""" % (
							width, height,  # size
							40, 5,  # position information
							width - 2 * 40, 2 * fontSize,  # size information
							fontSize - 2,
							40, 5 + 2 * fontSize + 10,  # position internet
							width - 40, 2 * fontSize,  # size internet
							fontSize - 2,
							"skin_default/buttons/button_green_off.png",
							20, 5 + 2 * fontSize + 10 + (fontSize - 16) / 2,  # position button internet
							"skin_default/buttons/button_green.png",
							20, 5 + 2 * fontSize + 10 + (fontSize - 16) / 2,  # position button internet
							40, 5 + 2 * fontSize + 10 + 2 * fontSize + 10,  # position dsl
							width - 40 - 20, fontSize,  # size dsl
							fontSize - 2,
							"skin_default/buttons/button_green_off.png",
							20, 5 + 2 * fontSize + 10 + 2 * fontSize + 10 + (fontSize - 16) / 2,  # position button dsl
							"skin_default/buttons/button_green.png",
							20, 5 + 2 * fontSize + 10 + 2 * fontSize + 10 + (fontSize - 16) / 2,  # position button dsl
							40, 5 + 2 * fontSize + 10 + 3 * fontSize + 10,  # position wlan
							width - 40 - 20, fontSize,  # size wlan
							fontSize - 2,
							"skin_default/buttons/button_green_off.png",
							20, 5 + 2 * fontSize + 10 + 3 * fontSize + 10 + (fontSize - 16) / 2,  # position button wlan
							"skin_default/buttons/button_green.png",
							20, 5 + 2 * fontSize + 10 + 3 * fontSize + 10 + (fontSize - 16) / 2,  # position button wlan
							mailboxLine,
							dectLine,
							faxLine,
							rufumlLine,
							buttonsGap, buttonsVPos, "skin_default/buttons/red.png", buttonsGap, buttonsVPos,
							buttonsGap + 140 + buttonsGap, buttonsVPos, "skin_default/buttons/green.png", buttonsGap + 140 + buttonsGap, buttonsVPos,
							)

			Screen.__init__(self, session)
			HelpableScreen.__init__(self)
			# TRANSLATORS: keep it short, this is a button
			self["key_red"] = Button(_("Reset"))
			# TRANSLATORS: keep it short, this is a button
			self["key_green"] = Button(_("Toggle WLAN"))
			self._mailboxActive = False
			if fritzbox.information[FBF_tamActive] is not None:
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

			if fritzbox.information[FBF_dectActive] is not None:
				self["FBFDect"] = Label('DECT')
				self["dect_inactive"] = Pixmap()
				self["dect_active"] = Pixmap()
				self["dect_active"].hide()

			if fritzbox.information[FBF_faxActive] is not None:
				self["FBFFax"] = Label('Fax')
				self["fax_inactive"] = Pixmap()
				self["fax_active"] = Pixmap()
				self["fax_active"].hide()

			if fritzbox.information[FBF_rufumlActive] is not None:
				self["FBFRufuml"] = Label(_('Call diversion'))
				self["rufuml_inactive"] = Pixmap()
				self["rufuml_active"] = Pixmap()
				self["rufuml_active"].hide()
		else:  # not (config.plugins.FritzCall.fwVersion.value == "old" or config.plugins.FritzCall.fwVersion.value == "05.27")
			if not config.plugins.FritzCall.advancedSkin.value:
				fontSize = scaleV(24, 21)  # indeed this is font size +2

				noButtons = 2
				width = max(DESKTOP_WIDTH - scaleH(500, 250), noButtons * 140 + (noButtons + 1) * 10)
				# boxInfo 2 lines, gap, internet 2 lines, gap, dsl/wlan/dect/fax/rufuml/gast each 1 line, gap
				height = 5 + 2 * fontSize + 10 + 2 * fontSize + 10 + 6 * fontSize + 10 + 40 + 5
				buttonsGap = (width - noButtons * 140) / (noButtons + 1)
				buttonsVPos = height - 40 - 5

				self.skin = """
					<screen name="FritzMenuNew" position="center,center" size="%d,%d" title="FRITZ!Box Fon Status" >
						<widget name="FBFInfo" position="%d,%d" size="%d,%d" font="Regular;%d" />
						<widget name="FBFInternet" position="%d,%d" size="%d,%d" font="Regular;%d" />
						<widget name="internet_inactive" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="blend"/>
						<widget name="internet_active" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="blend"/>
						<widget name="FBFDsl" position="%d,%d" size="%d,%d" font="Regular;%d" />
						<widget name="dsl_inactive" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="blend"/>
						<widget name="dsl_active" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="blend"/>
						<widget name="FBFWlan" position="%d,%d" size="%d,%d" font="Regular;%d" />
						<widget name="wlan_inactive" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="blend"/>
						<widget name="wlan_active" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="blend"/>
						<widget name="FBFDect" position="%d,%d" size="%d,%d" font="Regular;%d" />
						<widget name="dect_inactive" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="blend"/>
						<widget name="dect_active" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="blend"/>
						<widget name="FBFFax" position="%d,%d" size="%d,%d" font="Regular;%d" />
						<widget name="fax_inactive" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="blend"/>
						<widget name="fax_active" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="blend"/>
						<widget name="FBFRufuml" position="%d,%d" size="%d,%d" font="Regular;%d" />
						<widget name="rufuml_inactive" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="blend"/>
						<widget name="rufuml_active" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="blend"/>
						<widget name="FBFGast" position="%d,%d" size="%d,%d" font="Regular;%d" />
						<widget name="gast_inactive" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="blend"/>
						<widget name="gast_active" pixmap="%s" position="%d,%d" size="15,16" transparent="1" alphatest="blend"/>
						<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="blend" />
						<widget name="key_green" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
						<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="blend" />
						<widget name="key_yellow" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;16" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
					</screen>""" % (
								width, height,  # size
								40, 5,  # position information
								width - 2 * 40, 2 * fontSize,  # size information
								fontSize - 2,
								40, 5 + 2 * fontSize + 10,  # position internet
								width - 40, 2 * fontSize,  # size internet
								fontSize - 2,
								"skin_default/buttons/button_green_off.png",
								20, 5 + 2 * fontSize + 10 + (fontSize - 16) / 2,  # position button internet
								"skin_default/buttons/button_green.png",
								20, 5 + 2 * fontSize + 10 + (fontSize - 16) / 2,  # position button internet
								40, 5 + 2 * fontSize + 10 + 2 * fontSize + 10,  # position dsl
								width - 40 - 20, fontSize,  # size dsl
								fontSize - 2,
								"skin_default/buttons/button_green_off.png",
								20, 5 + 2 * fontSize + 10 + 2 * fontSize + 10 + (fontSize - 16) / 2,  # position button dsl
								"skin_default/buttons/button_green.png",
								20, 5 + 2 * fontSize + 10 + 2 * fontSize + 10 + (fontSize - 16) / 2,  # position button dsl
								40, 5 + 2 * fontSize + 10 + 3 * fontSize + 10,  # position wlan
								width - 40 - 20, fontSize,  # size wlan
								fontSize - 2,
								"skin_default/buttons/button_green_off.png",
								20, 5 + 2 * fontSize + 10 + 3 * fontSize + 10 + (fontSize - 16) / 2,  # position button wlan
								"skin_default/buttons/button_green.png",
								20, 5 + 2 * fontSize + 10 + 3 * fontSize + 10 + (fontSize - 16) / 2,  # position button wlan
								40, 5 + 2 * fontSize + 10 + 4 * fontSize + 10,  # position dect
								width - 40 - 20, fontSize,  # size dect
								fontSize - 2,
								"skin_default/buttons/button_green_off.png",
								20, 5 + 2 * fontSize + 10 + 4 * fontSize + 10 + (fontSize - 16) / 2,  # position button dect
								"skin_default/buttons/button_green.png",
								20, 5 + 2 * fontSize + 10 + 4 * fontSize + 10 + (fontSize - 16) / 2,  # position button dect
								40, 5 + 2 * fontSize + 10 + 5 * fontSize + 10,  # position fax
								width - 40 - 20, fontSize,  # size fax
								fontSize - 2,
								"skin_default/buttons/button_green_off.png",
								20, 5 + 2 * fontSize + 10 + 5 * fontSize + 10 + (fontSize - 16) / 2,  # position button fax
								"skin_default/buttons/button_green.png",
								20, 5 + 2 * fontSize + 10 + 5 * fontSize + 10 + (fontSize - 16) / 2,  # position button fax
								40, 5 + 2 * fontSize + 10 + 6 * fontSize + 10,  # position rufuml
								width - 40 - 20, fontSize,  # size rufuml
								fontSize - 2,
								"skin_default/buttons/button_green_off.png",
								20, 5 + 2 * fontSize + 10 + 6 * fontSize + 10 + (fontSize - 16) / 2,  # position button rufuml
								"skin_default/buttons/button_green.png",
								20, 5 + 2 * fontSize + 10 + 6 * fontSize + 10 + (fontSize - 16) / 2,  # position button rufuml
								40, 5 + 2 * fontSize + 10 + 7 * fontSize + 10,  # position gast
								width - 40 - 20, fontSize,  # size gast
								fontSize - 2,
								"skin_default/buttons/button_green_off.png",
								20, 5 + 2 * fontSize + 10 + 7 * fontSize + 10 + (fontSize - 16) / 2,  # position button gast
								"skin_default/buttons/button_green.png",
								20, 5 + 2 * fontSize + 10 + 7 * fontSize + 10 + (fontSize - 16) / 2,  # position button gast
								buttonsGap, buttonsVPos, "skin_default/buttons/green.png", buttonsGap, buttonsVPos,
								2 * buttonsGap + 140, buttonsVPos, "skin_default/buttons/yellow.png", 2 * buttonsGap + 140, buttonsVPos,
								)
			else:
				if DESKTOP_WIDTH <= 720:
					self.skin = """
						<!-- SD screen -->
						<screen name="FritzMenuNew" position="center,center" size="600,370" title="FRITZ!Box Fon Status">
							<widget name="FBFInfo" position="40,10" size="550,50" font="Regular;20" />
							<widget name="FBFInternet" position="40,70" size="550,45" font="Regular;18" />
							<widget name="internet_inactive" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/inaktiv.png" position="20,72" size="8,20" alphatest="blend"/>
							<widget name="internet_active" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/aktiv.png" position="20,72" size="8,20" alphatest="blend"/>
							<widget name="FBFDsl" position="40,144" size="550,25" font="Regular;18" />
							<widget name="dsl_inactive" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/inaktiv.png" position="20,140" size="8,20" alphatest="blend"/>
							<widget name="dsl_active" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/aktiv.png" position="20,140" size="8,20" alphatest="blend"/>
							<widget name="FBFWlan" position="40,169" size="550,25" font="Regular;18" />
							<widget name="wlan_inactive" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/inaktiv.png" position="20,165" size="8,20" alphatest="blend"/>
							<widget name="wlan_active" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/aktiv.png" position="20,165" size="8,20" alphatest="blend"/>
							<widget name="FBFDect" position="40,194" size="550,25" font="Regular;18" />
							<widget name="dect_inactive" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/inaktiv.png" position="20,190" size="8,20" alphatest="blend"/>
							<widget name="dect_active" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/aktiv.png" position="20,190" size="8,20" alphatest="blend"/>
							<widget name="FBFFax" position="40,219" size="550,25" font="Regular;18" />
							<widget name="fax_inactive" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/inaktiv.png" position="20,215" size="8,20" alphatest="blend"/>
							<widget name="fax_active" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/aktiv.png" position="20,215" size="8,20" alphatest="blend"/>
							<widget name="FBFRufuml" position="40,244" size="550,25" font="Regular;18" />
							<widget name="rufuml_inactive" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/inaktiv.png" position="20,240" size="8,20" alphatest="blend"/>
							<widget name="rufuml_active" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/aktiv.png" position="20,240" size="8,20" alphatest="blend"/>
							<widget name="FBFGast" position="40,269" size="550,25" font="Regular;18" />
							<widget name="gast_inactive" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/inaktiv.png" position="20,265" size="8,20" alphatest="blend"/>
							<widget name="gast_active" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/aktiv.png" position="20,265" size="8,20" alphatest="blend"/>
							<widget font="Regular;18" halign="center" name="key_red" position="10,330" size="160,22" />
							<widget font="Regular;18" halign="center" name="key_green" position="180,330" size="160,22" />
							<widget font="Regular;18" halign="center" name="key_yellow" position="350,330" size="240,22" />
							<eLabel position="10,355" size="160,10" backgroundColor="#9f1313" />
							<eLabel position="180,355" size="160,10" backgroundColor="#1f771f" />
							<eLabel position="350,355" size="240,10" backgroundColor="#a08500" />
						</screen>"""
				elif DESKTOP_WIDTH <= 1280:
					self.skin = """
						<!-- HD screen -->
						<screen name="FritzMenuNew" position="center,center" size="800,430" title="FRITZ!Box Fon Status">
							<widget name="FBFInfo" position="60,10" size="730,60" font="Regular;20" />
							<widget name="FBFInternet" position="60,80" size="730,50" font="Regular;20" />
							<widget name="internet_inactive" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/inaktiv.png" position="20,82" size="8,25" alphatest="blend"/>
							<widget name="internet_active" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/aktiv.png" position="20,82" size="8,25" alphatest="blend"/>
							<widget name="FBFDsl" position="60,154" size="730,30" font="Regular;20" />
							<widget name="dsl_inactive" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/inaktiv.png" position="20,152" size="8,25" alphatest="blend"/>
							<widget name="dsl_active" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/aktiv.png" position="20,152" size="8,25" alphatest="blend"/>
							<widget name="FBFWlan" position="60,184" size="730,30" font="Regular;20" />
							<widget name="wlan_inactive" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/inaktiv.png" position="20,182" size="8,25" alphatest="blend"/>
							<widget name="wlan_active" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/aktiv.png" position="20,182" size="8,25" alphatest="blend"/>
							<widget name="FBFDect" position="60,214" size="730,30" font="Regular;20" />
							<widget name="dect_inactive" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/inaktiv.png" position="20,212" size="8,25" alphatest="blend"/>
							<widget name="dect_active" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/aktiv.png" position="20,212" size="8,25" alphatest="blend"/>
							<widget name="FBFFax" position="60,244" size="730,30" font="Regular;20" />
							<widget name="fax_inactive" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/inaktiv.png" position="20,242" size="8,25" alphatest="blend"/>
							<widget name="fax_active" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/aktiv.png" position="20,242" size="8,25" alphatest="blend"/>
							<widget name="FBFRufuml" position="60,274" size="730,30" font="Regular;20" />
							<widget name="rufuml_inactive" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/inaktiv.png" position="20,272" size="8,25" alphatest="blend"/>
							<widget name="rufuml_active" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/aktiv.png" position="20,272" size="8,25" alphatest="blend"/>
							<widget name="FBFGast" position="60,304" size="730,30" font="Regular;20" />
							<widget name="gast_inactive" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/inaktiv.png" position="20,302" size="8,25" alphatest="blend"/>
							<widget name="gast_active" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/aktiv.png" position="20,302" size="8,25" alphatest="blend"/>
							<widget font="Regular;20" halign="center" name="key_red" position="10,375" size="220,30" />
							<widget font="Regular;20" halign="center" name="key_green" position="240,375" size="220,30" />
							<widget font="Regular;20" halign="center" name="key_yellow" position="470,375" size="320,30" />
							<eLabel position="10,410" size="220,10" backgroundColor="#9f1313" />
							<eLabel position="240,410" size="220,10" backgroundColor="#1f771f" />
							<eLabel position="470,410" size="320,10" backgroundColor="#a08500" />
						</screen> """
				elif DESKTOP_WIDTH <= 1920:
					self.skin = """
						<!-- Fullhd screen -->
						<screen name="FritzMenuNew" position="center,center" size="1100,660" title="FRITZ!Box Fon Status">
							<widget name="FBFInfo" position="60,10" size="980,80" font="Regular;30" />
							<widget name="FBFInternet" position="60,122" size="980,80" font="Regular;28" />
							<widget name="internet_inactive" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/inaktiv.png" position="20,125" size="10,35" alphatest="blend"/>
							<widget name="internet_active" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/aktiv.png" position="20,125" size="10,35" alphatest="blend"/>
							<widget name="FBFDsl" position="60,233" size="980,40" font="Regular;28" />
							<widget name="dsl_inactive" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/inaktiv.png" position="20,230" size="10,35" alphatest="blend"/>
							<widget name="dsl_active" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/aktiv.png" position="20,230" size="10,35" alphatest="blend"/>
							<widget name="FBFWlan" position="60,283" size="980,40" font="Regular;28" />
							<widget name="wlan_inactive" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/inaktiv.png" position="20,280" size="10,35" alphatest="blend"/>
							<widget name="wlan_active" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/aktiv.png" position="20,280" size="10,35" alphatest="blend"/>
							<widget name="FBFDect" position="60,333" size="980,40" font="Regular;28" />
							<widget name="dect_inactive" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/inaktiv.png" position="20,330" size="10,35" alphatest="blend"/>
							<widget name="dect_active" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/aktiv.png" position="20,330" size="10,35" alphatest="blend"/>
							<widget name="FBFFax" position="60,383" size="980,40" font="Regular;28" />
							<widget name="fax_inactive" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/inaktiv.png" position="20,380" size="10,35" alphatest="blend"/>
							<widget name="fax_active" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/aktiv.png" position="20,380" size="10,35" alphatest="blend"/>
							<widget name="FBFRufuml" position="60,433" size="980,40" font="Regular;28" />
							<widget name="rufuml_inactive" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/inaktiv.png" position="20,430" size="10,35" alphatest="blend"/>
							<widget name="rufuml_active" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/aktiv.png" position="20,430" size="10,35" alphatest="blend"/>
							<widget name="FBFGast" position="60,483" size="980,80" font="Regular;28" />
							<widget name="gast_inactive" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/inaktiv.png" position="20,480" size="10,35" alphatest="blend"/>
							<widget name="gast_active" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/aktiv.png" position="20,480" size="10,35" alphatest="blend"/>
							<widget font="Regular;30" halign="center" name="key_red" position="10,590" size="300,40" />
							<widget font="Regular;30" halign="center" name="key_green" position="330,590" size="300,40" />
							<widget font="Regular;30" halign="center" name="key_yellow" position="650,590" size="440,40" />
							<eLabel position="10,640" size="300,8" backgroundColor="#9f1313"/>
							<eLabel position="330,640" size="300,8" backgroundColor="#1f771f" />
							<eLabel position="650,640" size="440,8" backgroundColor="#a08500" />
						</screen>"""
				else:
					self.skin = """
						<!-- UHD screen -->
						<screen name="FritzMenuNew" position="center,center" size="2400,1270" title="FRITZ!Box Fon Status">
							<widget name="FBFInfo" position="80,10" size="2300,150" font="Regular;65" />
							<widget name="FBFInternet" position="80,200" size="2100,130" font="Regular;60" />
							<widget name="internet_inactive" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/inaktiv.png" position="20,205" size="20,70" alphatest="blend"/>
							<widget name="internet_active" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/aktiv.png" position="20,205" size="20,70" alphatest="blend"/>
							<widget name="FBFDsl" position="80,397" size="2300,70" font="Regular;60" />
							<widget name="dsl_inactive" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/inaktiv.png" position="20,395" size="20,70" alphatest="blend"/>
							<widget name="dsl_active" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/aktiv.png" position="20,395" size="20,70" alphatest="blend"/>
							<widget name="FBFWlan" position="80,517" size="2300,70" font="Regular;60" />
							<widget name="wlan_inactive" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/inaktiv.png" position="20,515" size="20,70" alphatest="blend"/>
							<widget name="wlan_active" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/aktiv.png" position="20,515" size="20,70" alphatest="blend"/>
							<widget name="FBFDect" position="80,617" size="2300,70" font="Regular;60" />
							<widget name="dect_inactive" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/inaktiv.png" position="20,615" size="20,70" alphatest="blend"/>
							<widget name="dect_active" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/aktiv.png" position="20,615" size="20,70" alphatest="blend"/>
							<widget name="FBFFax" position="80,727" size="2300,70" font="Regular;60" />
							<widget name="fax_inactive" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/inaktiv.png" position="20,725" size="20,70" alphatest="blend"/>
							<widget name="fax_active" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/aktiv.png" position="20,725" size="20,70" alphatest="blend"/>
							<widget name="FBFRufuml" position="80,837" size="2300,70" font="Regular;60" />
							<widget name="rufuml_inactive" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/inaktiv.png" position="20,835" size="20,70" alphatest="blend"/>
							<widget name="rufuml_active" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/aktiv.png" position="20,785" size="20,70" alphatest="blend"/>
							<widget name="FBFGast" position="80,947" size="2300,70" font="Regular;60" />
							<widget name="gast_inactive" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/inaktiv.png" position="20,945" size="20,70" alphatest="blend"/>
							<widget name="gast_active" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/FritzCall/images/aktiv.png" position="20,945" size="20,70" alphatest="blend"/>
							<widget font="Regular;60" halign="center" name="key_red" position="20,1140" size="650,70" />
							<widget font="Regular;60" halign="center" name="key_green" position="700,1140" size="650,70" />
							<widget font="Regular;60" halign="center" name="key_yellow" position="1380,1140" size="1000,70" />
							<eLabel position="20,1230" size="650,20" backgroundColor="#9f1313" />
							<eLabel position="700,1230" size="650,20" backgroundColor="#1f771f" />
							<eLabel position="1380,1230" size="1000,20" backgroundColor="#a08500" />
						</screen>"""

			Screen.__init__(self, session)
			HelpableScreen.__init__(self)
			# TRANSLATORS: keep it short, this is a button
			self["menuActions"] = ActionMap(["OkCancelActions", "ColorActions", "EPGSelectActions"],
											{
											"cancel": self._exit,
											"ok": self._exit,
											"green": self._toggleWlan,
											"yellow": self._toggleGast,
											"red": self._reset,  # no button, does not work
											"info": self._getInfo,
											}, -2)

			# TRANSLATORS: keep it short, this is a help text
			self.helpList.append((self["menuActions"], "OkCancelActions", [("cancel", _("Quit"))]))
			# TRANSLATORS: keep it short, this is a help text
			self.helpList.append((self["menuActions"], "OkCancelActions", [("ok", _("Quit"))]))
			# TRANSLATORS: keep it short, this is a help text
			self.helpList.append((self["menuActions"], "ColorActions", [("green", _("Toggle WLAN"))]))
			# TRANSLATORS: keep it short, this is a help text
			self.helpList.append((self["menuActions"], "ColorActions", [("yellow", _("Toggle WLAN guest access"))]))
			# TRANSLATORS: keep it short, this is a help text
			self.helpList.append((self["menuActions"], "ColorActions", [("red", _("Reset"))]))
			# TRANSLATORS: keep it short, this is a help text
			self.helpList.append((self["menuActions"], "EPGSelectActions", [("info", _("Refresh status"))]))

			# TRANSLATORS: keep it short, this is a button
			self["key_red"] = Button(_("Reset"))
			# TRANSLATORS: keep it short, this is a button
			self["key_green"] = Button(_("Toggle WLAN"))
			# TRANSLATORS: keep it short, this is a button
			self["key_yellow"] = Button(_("Activate WLAN guest access"))

			self["FBFInfo"] = Label(_('Getting status from FRITZ!Box Fon...'))

			self["FBFInternet"] = Label('Internet')
			self["internet_inactive"] = Pixmap()
			self["internet_inactive"].hide()
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

			self["FBFDect"] = Label('DECT')
			self["dect_inactive"] = Pixmap()
			self["dect_inactive"].hide()
			self["dect_active"] = Pixmap()
			self["dect_active"].hide()

			self["FBFFax"] = Label('Fax')
			self["fax_inactive"] = Pixmap()
			self["fax_inactive"].hide()
			self["fax_active"] = Pixmap()
			self["fax_active"].hide()

			self["FBFRufuml"] = Label(_('Call redirection'))
			self["rufuml_inactive"] = Pixmap()
			self["rufuml_inactive"].hide()
			self["rufuml_active"] = Pixmap()
			self["rufuml_active"].hide()

			self["FBFGast"] = Label(_('Guest access'))
			self["gast_inactive"] = Pixmap()
			self["gast_inactive"].hide()
			self["gast_active"] = Pixmap()
			self["gast_active"].hide()
			self._guestActive = ""

		self._getInfo()
		self.onLayoutFinish.append(self.setWindowTitle)

	def setWindowTitle(self):
		# TRANSLATORS: this is a window title.
		self.setTitle(_("FRITZ!Box Fon Status"))

	def _getInfo(self):
		if fritzbox:
			fritzbox.getInfo(self._fillMenu)
			self._fillMenu(fritzbox.information, True)

	def _fillMenu(self, status, refreshing = False):
		(boxInfo, upTime, ipAddress, wlanState, dslState, tamActive, dectActive, faxActive, rufumlActive, guestAccess) = status
		if wlanState:
			self._wlanActive = (wlanState[0] == '1')
		self._guestActive = guestAccess
		self._mailboxActive = False
		try:
			if "FBFInfo" not in self:  # screen is closed already
				return

			if refreshing:
				self["FBFInfo"].setText(_("Refreshing..."))
			else:
				if boxInfo:
					self["FBFInfo"].setText(boxInfo)
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
					if dslState[2]:
						message = dslState[2]
					else:
						message = "DSL"
					if dslState[1]:
						message = message + ' ' + dslState[1]
					self["FBFDsl"].setText(message)
				else:
					self["dsl_active"].hide()
					self["dsl_inactive"].show()
			else:
				self["FBFDsl"].setText('DSL ' + _('Status not available'))
				self["dsl_active"].hide()
				self["dsl_inactive"].hide()

			if wlanState:
				if wlanState[0] == '1':
					self["wlan_inactive"].hide()
					self["wlan_active"].show()
					message = 'WLAN'
					if wlanState[1] == '0':
						message += ' ' + _('not encrypted')
					elif wlanState[1] == '1':
						message += ' ' + _('encrypted')
					if wlanState[2]:
						if wlanState[2] == '0':
							message = message + ', ' + _('no device active')
						elif wlanState[2] == '1' or wlanState[2] == 'ein':
							message = message + ', ' + _('one device active')
						else:
							message = message + ', ' + wlanState[2] + ' ' + _('devices active')
					if len(wlanState) == 4:
						message = message + ", " + wlanState[3]
					self["FBFWlan"].setText(message)
				else:
					self["wlan_active"].hide()
					self["wlan_inactive"].show()
					self["FBFWlan"].setText('WLAN')
			else:
				self["FBFWlan"].setText('WLAN ' + _('Status not available'))
				self["wlan_active"].hide()
				self["wlan_inactive"].hide()

			if fritzbox.information[FBF_tamActive] and "mailbox_active" in self:
				if not tamActive or tamActive[0] == 0:
					self._mailboxActive = False
					self["mailbox_active"].hide()
					self["mailbox_inactive"].show()
					self["FBFMailbox"].setText(_('No mailbox active'))
				else:
					self._mailboxActive = True
					message = ''
					for i in range(min(len(tamActive) - 1, 5)):
						if tamActive[i + 1]:
							message = message + str(i) + ','
					if message:
						message = '(' + message[:-1] + ')'
					self["mailbox_inactive"].hide()
					self["mailbox_active"].show()
					if tamActive[0] == 1:
						self["FBFMailbox"].setText(_('One mailbox active') + ' ' + message)
					else:
						self["FBFMailbox"].setText(str(tamActive[0]) + ' ' + _('mailboxes active') + ' ' + message)

			if dectActive and "dect_inactive" in self:
				self["dect_inactive"].hide()
				self["dect_active"].show()
				if dectActive == 0:
					self["FBFDect"].setText(_('No DECT phone registered'))
				else:
					if dectActive == "ein" or dectActive == "1" or dectActive == 1:
						self["FBFDect"].setText(_('One DECT phone registered'))
					else:
						self["FBFDect"].setText(str(dectActive) + ' ' + _('DECT phones registered'))
			else:
				self["dect_active"].hide()
				self["dect_inactive"].show()
				self["FBFDect"].setText(_('DECT inactive'))

			if faxActive:
				self["fax_inactive"].hide()
				self["fax_active"].show()
				self["FBFFax"].setText(_('Software fax active'))
			else:
				self["fax_active"].hide()
				self["fax_inactive"].show()
				self["FBFFax"].setText(_('Software fax inactive'))

			if rufumlActive:
				self["rufuml_inactive"].hide()
				self["rufuml_active"].show()
				if rufumlActive == -1:  # means no number available
					self["FBFRufuml"].setText(_('Call diversion active'))
				elif rufumlActive == 1:
					self["FBFRufuml"].setText(_('One call diversion active'))
				else:
					self["FBFRufuml"].setText(str(rufumlActive) + ' ' + _('call diversions active'))
			else:
				self["rufuml_active"].hide()
				self["rufuml_inactive"].show()
				self["FBFRufuml"].setText(_('No call diversion active'))

			if guestAccess:
				self["gast_inactive"].hide()
				self["gast_active"].show()
				self["FBFGast"].setText(_('Guest access on ') + guestAccess)
			else:
				self["gast_active"].hide()
				self["gast_inactive"].show()
				self["FBFGast"].setText(_('Guest access not active'))

			if guestAccess and (guestAccess.find('WLAN') != -1 or guestAccess.find('WIFI') != -1):
				# TRANSLATORS: keep it short, this is a button
				self["key_yellow"].setText(_("Deactivate WLAN guest access"))
			else:
				# TRANSLATORS: keep it short, this is a button
				self["key_yellow"].setText(_("Activate WLAN guest access"))

		except KeyError:
			error("[FritzCallFBF] _fillMenu: " + traceback.format_exc())

	def _toggleWlan(self, callback=None):
		self["FBFInfo"].setText(_("Setting...") + " WLAN")
		if self._wlanActive:
			info("[FritzMenu] toggleWlan off")
			if callback:
				fritzbox.changeWLAN('0', callback)
			else:
				fritzbox.changeWLAN('0', self._getInfo)
		else:
			info("[FritzMenu] toggleWlan on")
			if callback:
				fritzbox.changeWLAN('1', callback)
			else:
				fritzbox.changeWLAN('1', self._getInfo)

	def _toggleMailbox(self, which):
		debug("[FritzMenu]")
		if fritzbox.information[FBF_tamActive]:
			info("[FritzMenu] toggleMailbox off")
			fritzbox.changeMailbox(which, self._getInfo)

	def _toggleGast(self):
		self["FBFInfo"].setText(_("Setting...") + ' ' + _("Guest access"))
		if fritzbox.information[FBF_wlanState][0] != '1':
			self["FBFInfo"].setText(_("WLAN not active"))
			# self._toggleWlan(self._toggleGast)
			return
		fritzbox.changeGuestAccess(self._guestActive, self._getInfo)

	def _reset(self):
		fritzbox.reset()
		self._exit()

	def _exit(self):
		self.close()


class FritzDisplayCalls(Screen, HelpableScreen):

	def __init__(self, session, text = ""):  # @UnusedVariable # pylint: disable=W0613
		if not config.plugins.FritzCall.advancedSkin.value:
			self.width = DESKTOP_WIDTH * scaleH(75, 85) / 100
			self.height = DESKTOP_HEIGHT * 0.75
			dateFieldWidth = scaleH(180, 105)
			dirFieldWidth = 16
			lengthFieldWidth = scaleH(55, 45)
			scrollbarWidth = scaleH(35, 35)
			entriesWidth = self.width - scaleH(40, 5) - 5
			hereFieldWidth = entriesWidth - dirFieldWidth - 5 - dateFieldWidth - 5 - lengthFieldWidth - scrollbarWidth
			fieldWidth = entriesWidth - dirFieldWidth - 5 - 5 - scrollbarWidth
			fontSize = scaleV(22, 20)
			itemHeight = 2 * fontSize + 5
			entriesHeight = self.height - scaleV(15, 10) - 5 - fontSize - 5 - 5 - 5 - 40 - 5
			buttonGap = (self.width - 4 * 140) / 5
			buttonV = self.height - 40
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
									MultiContentEntryPixmapAlphaBlend(pos = (%d,%d), size = (%d,%d), png = 2), # index 1 i direction pixmap
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
					<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="blend" />
					<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="blend" />
					<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="blend" />
					<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="blend" />
					<widget name="key_red" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
					<widget name="key_green" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
					<widget name="key_yellow" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
					<widget name="key_blue" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				</screen>""" % (
							# scaleH(90, 75), scaleV(100, 78), # position
							self.width, self.height,  # size
							self.width,  # eLabel width
							scaleH(40, 5), scaleV(10, 5),  # statusbar position
							self.width, fontSize + 5,  # statusbar size
							scaleV(21, 21),  # statusbar font size
							scaleV(10, 5) + 5 + fontSize + 5,  # eLabel position vertical
							self.width,  # eLabel width
							scaleH(40, 5), scaleV(10, 5) + 5 + fontSize + 5 + 5,  # entries position
							entriesWidth, entriesHeight,  # entries size
							5 + dirFieldWidth + 5, fontSize + 5, dateFieldWidth, fontSize,  # date pos/size
							5, (itemHeight - dirFieldWidth) / 2, dirFieldWidth, dirFieldWidth,  # dir pos/size
							5 + dirFieldWidth + 5, 5, fieldWidth, fontSize,  # caller pos/size
							2 + dirFieldWidth + 2 + dateFieldWidth + 5, fontSize + 5, lengthFieldWidth, fontSize,  # length pos/size
							2 + dirFieldWidth + 2 + dateFieldWidth + 5 + lengthFieldWidth + 5, fontSize + 5, hereFieldWidth, fontSize,  # my number pos/size
							fontSize - 4, fontSize,  # fontsize
							itemHeight,  # itemHeight
							buttonV - 5,  # eLabel position vertical
							self.width,  # eLabel width
							buttonGap, buttonV, "skin_default/buttons/red.png",  # widget red
							2 * buttonGap + 140, buttonV, "skin_default/buttons/green.png",  # widget green
							3 * buttonGap + 2 * 140, buttonV, "skin_default/buttons/yellow.png",  # widget yellow
							4 * buttonGap + 3 * 140, buttonV, "skin_default/buttons/blue.png",  # widget blue
							buttonGap, buttonV, scaleV(22, 21),  # widget red
							2 * buttonGap + 140, buttonV, scaleV(22, 21),  # widget green
							3 * buttonGap + 2 * 140, buttonV, scaleV(22, 21),  # widget yellow
							4 * buttonGap + 3 * 140, buttonV, scaleV(22, 21),  # widget blue
							)
		else:
			if DESKTOP_WIDTH <= 720:
				self.skin = """
					<!-- SD screen -->
					<screen name="FritzDisplayCalls" position="center,center" size="620,460" title="Phone calls" >
							<widget name="statusbar" position="10,10" halign="center" foregroundColor="#bab329" size="590,25" font="Regular;18"/>
							<eLabel position="10,35" size="590,2" backgroundColor="#aaaaaa" />
							<widget source="entries" render="Listbox" position="10,45" size="600,360" enableWrapAround="1" scrollbarMode="showOnDemand">
								<convert type="TemplatedMultiContent">
									{"template": [
											MultiContentEntryText(pos = (50,24), size = (150,21), font=1, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 1), # index 0 is the number, index 1 is date
											MultiContentEntryPixmapAlphaBlend(pos = (5,5), size = (35,35), png = 2), # index 1 i direction pixmap
											MultiContentEntryText(pos = (50,0), size = (530,24), font=0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 3), # index 2 is remote name/number
											MultiContentEntryText(pos = (220,24), size = (80,21), font=1, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 4), # index 3 is length of call
											MultiContentEntryText(pos = (320,24), size = (240,21), font=1, flags = RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text = 5), # index 4 is my number/name for number
										],
									"fonts": [gFont("Regular", 18), gFont("Regular", 16)],
									"itemHeight": 45
									}
								</convert>
							</widget>
							<widget name="key_red" position="10,415" size="140,20" halign="center" font="Regular;18" />
							<widget name="key_green" position="160,415" size="140,20" halign="center" font="Regular;18" />
							<widget name="key_yellow" position="310,415" size="140,20"  halign="center" font="Regular;18" />
							<widget name="key_blue" position="460,415" size="140,20" halign="center" font="Regular;18" />
							<eLabel position="10,440" size="140,10" backgroundColor="#9f1313"/>
							<eLabel position="160,440" size="140,10" backgroundColor="#1f771f" />
							<eLabel position="310,440" size="140,10" backgroundColor="#a08500" />
							<eLabel position="460,440" size="140,10" backgroundColor="#0039f0"/>
					</screen>"""
			elif DESKTOP_WIDTH <= 1280:
				self.skin = """
					<!-- HD screen -->
					<screen name="FritzDisplayCalls" position="center,center" size="850,560" title="Phone calls" >
							<widget name="statusbar" position="10,8" halign="center" foregroundColor="#bab329" size="830,30" font="Regular;20"/>
							<eLabel position="10,40" size="830,2" backgroundColor="#aaaaaa" />
							<widget source="entries" render="Listbox" position="10,50" size="830,440" enableWrapAround="1" scrollbarMode="showOnDemand">
								<convert type="TemplatedMultiContent">
									{"template": [
											MultiContentEntryText(pos = (55,30), size = (200,25), font=1, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 1), # index 0 is the number, index 1 is date
											MultiContentEntryPixmapAlphaBlend(pos = (5,10), size = (35,35), png = 2), # index 1 i direction pixmap
											MultiContentEntryText(pos = (55,0), size = (760,30), font=0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 3), # index 2 is remote name/number
											MultiContentEntryText(pos = (270,30), size = (100,25), font=1, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 4), # index 3 is length of call
											MultiContentEntryText(pos = (390,30), size = (400,25), font=1, flags = RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text = 5), # index 4 is my number/name for number
										],
									"fonts": [gFont("Regular", 20), gFont("Regular", 18)],
									"itemHeight": 55
									}
								</convert>
							</widget>
							<widget name="key_red" position="10,510" size="200,25" halign="center" font="Regular;20" />
							<widget name="key_green" position="220,510" size="200,25" halign="center" font="Regular;20" />
							<widget name="key_yellow" position="430,510" size="200,25"  halign="center" font="Regular;20" />
							<widget name="key_blue" position="640,510" size="200,25" halign="center" font="Regular;20" />
							<eLabel position="10,540" size="200,10" backgroundColor="#9f1313"/>
							<eLabel position="220,540" size="200,10" backgroundColor="#1f771f" />
							<eLabel position="430,540" size="200,10" backgroundColor="#a08500" />
							<eLabel position="640,540" size="200,10" backgroundColor="#0039f0"/>
					</screen>"""
			elif DESKTOP_WIDTH <= 1920:
				self.skin = """
					<!-- Fullhd screen -->
					<screen name="FritzDisplayCalls" position="center,center" size="1450,850" title="Phone calls" >
							<widget name="statusbar" position="10,10" halign="center" foregroundColor="#bab329" size="1430,40" font="Regular;30"/>
							<eLabel position="10,55" size="1430,2" backgroundColor="#aaaaaa" />
							<widget source="entries" render="Listbox" position="10,65" size="1430,680" enableWrapAround="1" scrollbarMode="showOnDemand">
								<convert type="TemplatedMultiContent">
									{"template": [
											MultiContentEntryText(pos = (5,0), size = (180,40), flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 1), # index 0 is the number, index 1 is date
											MultiContentEntryPixmapAlphaBlend(pos = (190,2), size = (35,35), png = 2), # index 1 i direction pixmap
											MultiContentEntryText(pos = (245,2), size = (600,40), flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 3), # index 2 is remote name/number
											MultiContentEntryText(pos = (860,0), size = (120,40), flags = RT_HALIGN_CENTER|RT_VALIGN_CENTER, text = 4), # index 3 is length of call
											MultiContentEntryText(pos = (1000,0), size = (390,40), flags = RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text = 5), # index 4 is my number/name for number
										],
									"fonts": [gFont("Regular", 28)],
									"itemHeight": 40
									}
								</convert>
							</widget>
							<widget name="key_red" position="10,780" size="350,40" halign="center" font="Regular;30" />
							<widget name="key_green" position="370,780" size="350,40" halign="center" font="Regular;30" />
							<widget name="key_yellow" position="730,780" size="350,40"  halign="center" font="Regular;30" />
							<widget name="key_blue" position="1090,780" size="350,40" halign="center" font="Regular;30" />
							<eLabel position="10,830" size="350,8" backgroundColor="#9f1313"/>
							<eLabel position="370,830" size="350,8" backgroundColor="#1f771f" />
							<eLabel position="730,830" size="350,8" backgroundColor="#a08500" />
							<eLabel position="1090,830" size="350,8" backgroundColor="#0039f0"/>
					</screen>"""
			else:
				self.skin = """
					<!-- UHD screen -->
					<screen name="FritzDisplayCalls" position="center,center" size="2560,1540" title="Phone calls" >
							<widget name="statusbar" position="10,10" halign="center" foregroundColor="#bab329" size="2540,80" font="Regular;65"/>
							<eLabel position="10,100" size="2540,4" backgroundColor="#aaaaaa" />
							<widget source="entries" render="Listbox" position="10,110" size="2540,1260" enableWrapAround="1" scrollbarMode="showOnDemand">
								<convert type="TemplatedMultiContent">
									{"template": [
											MultiContentEntryText(pos = (1100,0), size = (420,70), flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 1), # index 0 is the number, index 1 is date
											MultiContentEntryPixmapAlphaBlend(pos = (5,10), size = (50,50), png = 2), # index 1 i direction pixmap
											MultiContentEntryText(pos = (80,0), size = (1000,70), flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 3), # index 2 is remote name/number
											MultiContentEntryText(pos = (1540,0), size = (200,70), flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 4), # index 3 is length of call
											MultiContentEntryText(pos = (1760,0), size = (740,70), flags = RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text = 5), # index 4 is my number/name for number
										],
									"fonts": [gFont("Regular", 58)],
									"itemHeight": 70
									}
								</convert>
							</widget>
							<widget name="key_red" position="10,1420" size="600,70" halign="center" font="Regular;60" />
							<widget name="key_green" position="660,1420" size="600,70" halign="center" font="Regular;60" />
							<widget name="key_yellow" position="1310,1420" size="600,70"  halign="center" font="Regular;60" />
							<widget name="key_blue" position="1950,1420" size="600,70" halign="center" font="Regular;60" />
							<eLabel position="10,1510" size="600,20" backgroundColor="#9f1313"/>
							<eLabel position="660,1510" size="600,20" backgroundColor="#1f771f" />
							<eLabel position="1310,1510" size="600,20" backgroundColor="#a08500" />
							<eLabel position="1950,1510" size="600,20" backgroundColor="#0039f0"/>
					</screen>"""

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
			"ok": self.showEntry, }, -2)

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
		debug("[FritzDisplayCalls] '''%s'''", config.plugins.FritzCall.fbfCalls.value)
		self.display(config.plugins.FritzCall.fbfCalls.value)
		self.onLayoutFinish.append(self.setWindowTitle)

	def setWindowTitle(self):
		# TRANSLATORS: this is a window title.
		self.setTitle(_("Phone calls"))

	def ok(self):
		self.close()

	def display(self, which = None):
		debug("[FritzDisplayCalls]")
		if which:
			config.plugins.FritzCall.fbfCalls.value = which
			config.plugins.FritzCall.fbfCalls.save()
		else:
			which = config.plugins.FritzCall.fbfCalls.value
		fritzbox.getCalls(self, lambda x: self.gotCalls(x, which), which)

	def gotCalls(self, listOfCalls, which):
		debug("[FritzDisplayCalls]")
		self.updateStatus(fbfCallsChoices[which] + " (" + str(len(listOfCalls)) + ")")

		callPngPath = "Extensions/FritzCall/images"
		if config.plugins.FritzCall.advancedSkin.value:
			callPngPath = callPngPath + "/MODERN"
		debug("[FritzDisplayCalls] callPngPath: %s", callPngPath)
		directout = LoadPixmap(resolveFilename(SCOPE_CURRENT_PLUGIN, callPngPath + "/callout.png"))
		directin = LoadPixmap(resolveFilename(SCOPE_CURRENT_PLUGIN, callPngPath + "/callin.png"))
		directfailed = LoadPixmap(resolveFilename(SCOPE_CURRENT_PLUGIN, callPngPath + "/callinfailed.png"))
		directrejected = LoadPixmap(resolveFilename(SCOPE_CURRENT_PLUGIN, callPngPath + "/callrejected.png"))

		def pixDir(param):
			if param == FBF_OUT_CALLS:
				direct = directout
			elif param == FBF_IN_CALLS:
				direct = directin
			elif param == FBF_MISSED_CALLS:
				direct = directfailed
			else:
				direct = directrejected
			return direct

		# debug("[FritzDisplayCalls] %s" %repr(listOfCalls))
		self.list = [(number, date[:6] + ' ' + date[9:14], pixDir(direct), remote, length, here) for (number, date, direct, remote, length, here) in listOfCalls]
		self["entries"].setList(self.list)
		#=======================================================================
		# if len(self.list) > 1:
		# 	self["entries"].setIndex(1)
		#=======================================================================

	def updateStatus(self, text):
		if "statusbar" in self:
			self["statusbar"].setText(_("Getting calls from FRITZ!Box...") + ' ' + text)

	def showEntry(self):
		debug("[FritzDisplayCalls]")
		cur = self["entries"].getCurrent()
		if cur:
			if cur[0]:
				# debug("[FritzDisplayCalls] %s" % (cur[0]))
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
					fullname = resolveNumberWithAvon(number, config.plugins.FritzCall.countrycode.value)
					if fullname:
						name = fullname
						self.session.open(FritzOfferAction, self, number, name)
					else:
						self.session.open(FritzOfferAction, self, number)
			else:
				# we do not even have a number...
				self.session.open(MessageBox,
								_("UNKNOWN"),
								type = MessageBox.TYPE_INFO)


class FritzOfferAction(Screen):

	def __init__(self, session, parent, number, name = ""):
		if not config.plugins.FritzCall.advancedSkin.value:
			# the layout will completely be recalculated in finishLayout
			self.skin = """
				<screen name="FritzOfferAction" title="Do what?" >
					<widget name="text" size="%d,%d" font="Regular;%d" />
					<widget name="FacePixmap" size="%d,%d" alphatest="blend" />
					<widget name="key_red_p" zPosition="4" size="%s,%s" pixmap="%s" transparent="1" alphatest="blend" />
					<widget name="key_green_p" zPosition="4" size="%s,%s" pixmap="%s" transparent="1" alphatest="blend" />
					<widget name="key_yellow_p" zPosition="4" size="%s,%s" pixmap="%s" transparent="1" alphatest="blend" />
					<widget name="key_red" zPosition="5" size="%s,%s" valign="center" halign="center" font="Regular;%s" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
					<widget name="key_green" zPosition="5" size="%s,%s" valign="center" halign="center" font="Regular;%s" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
					<widget name="key_yellow" zPosition="5" size="%s,%s" valign="center" halign="center" font="Regular;%s" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				</screen>""" % (
								DESKTOP_WIDTH, DESKTOP_HEIGHT, scaleV(25, 22),  # set maximum size
								DESKTOP_WIDTH, DESKTOP_HEIGHT,  # set maximum size
								140, 40, "skin_default/buttons/red.png",
								140, 40, "skin_default/buttons/green.png",
								140, 40, "skin_default/buttons/yellow.png",
								140, 40, scaleV(21, 21),
								140, 40, scaleV(21, 21),
								140, 40, scaleV(21, 21),
								)
		else:
			if DESKTOP_WIDTH <= 720:
				self.skin = """
					<!-- SD screen -->
					<screen name="FritzOfferAction" position="center,center" size="490,230" title=" ">
						<widget name="FacePixmap" position="10,10" size="160,160" alphatest="blend" />
						<widget name="text" position="220,40" size="260,120" font="Regular;18"/>
						<widget font="Regular;18" halign="center" name="key_red" position="10,190" size="150,22" />
						<widget font="Regular;18" halign="center" name="key_green" position="170,190" size="150,22" />
						<widget font="Regular;18" halign="center" name="key_yellow" position="330,190" size="150,22" />
						<eLabel position="10,215" size="150,10" backgroundColor="#9f1313"/>
						<eLabel position="170,215" size="150,10" backgroundColor="#1f771f" />
						<eLabel position="330,215" size="150,10" backgroundColor="#a08500" />
					</screen>
					"""
			elif DESKTOP_WIDTH <= 1280:
				self.skin = """
					<!-- HD screen -->
					<screen name="FritzOfferAction" position="center,center" size="700,320" title=" ">
						<widget name="FacePixmap" position="10,10" size="230,230" alphatest="blend" />
						<widget name="text" position="290,80" size="400,150" font="Regular;20"/>
						<widget font="Regular;20" halign="center" name="key_red" position="10,270" size="200,25" />
						<widget font="Regular;20" halign="center" name="key_green" position="250,270" size="200,25" />
						<widget font="Regular;20" halign="center" name="key_yellow" position="490,270" size="200,25" />
						<eLabel position="10,300" size="200,10" backgroundColor="#9f1313"/>
						<eLabel position="250,300" size="200,10" backgroundColor="#1f771f" />
						<eLabel position="490,300" size="200,10" backgroundColor="#a08500" />
					</screen>
					"""
			elif DESKTOP_WIDTH <= 1920:
				self.skin = """
					<!-- Fullhd screen -->
					<screen name="FritzOfferAction" position="center,center" size="1160,480" title=" ">
						<widget name="FacePixmap" position="10,10" size="400,400" alphatest="blend" />
						<widget name="text" position="470,110" size="680,280" font="Regular;30"/>
						<widget font="Regular;30" halign="center" name="key_red" position="10,420" size="300,40" />
						<widget font="Regular;30" halign="center" name="key_green" position="430,420" size="300,40" />
						<widget font="Regular;30" halign="center" name="key_yellow" position="850,420" size="300,40" />
						<eLabel position="10,460" size="300,8" backgroundColor="#9f1313"/>
						<eLabel position="430,460" size="300,8" backgroundColor="#1f771f" />
						<eLabel position="850,460" size="300,8" backgroundColor="#a08500" />
					</screen>
					"""
			else:
				self.skin = """
					<!-- UHD screen -->
					<screen name="FritzOfferAction" position="center,center" size="2080,940" title=" ">
						<widget name="FacePixmap" position="10,10" size="800,800" alphatest="blend" />
						<widget name="text" position="900,300" size="1150,500" font="Regular;60"/>
						<widget font="Regular;60" halign="center" name="key_red" position="10,830" size="600,70" />
						<widget font="Regular;60" halign="center" name="key_green" position="740,830" size="600,70" />
						<widget font="Regular;60" halign="center" name="key_yellow" position="1470,830" size="600,70" />
						<eLabel position="10,910" size="600,20" backgroundColor="#9f1313"/>
						<eLabel position="740,910" size="600,20" backgroundColor="#1f771f" />
						<eLabel position="1470,910" size="600,20" backgroundColor="#a08500" />
					</screen>
					"""

		debug("[FritzOfferAction] %s, %s", __(number), __(name))
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
			"ok": self._exit, }, -2)

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
		debug("[FritzOfferAction] number: %s/%s", __(self._number), __(self._name))

		faceFile = findFace(self._number, self._name)
		picPixmap = LoadPixmap(faceFile)
		if not picPixmap:  # that means most probably, that the picture is not 8 bit...
			Notifications.AddNotification(MessageBox, _("Found picture\n\n%s\n\nBut did not load. Probably not PNG, 8-bit") % faceFile, type = MessageBox.TYPE_ERROR)
			if DESKTOP_WIDTH <= 720:
				picPixmap = LoadPixmap(resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/FritzCall/images/no-face-error-sd.png"))
			elif DESKTOP_WIDTH <= 1280:
				picPixmap = LoadPixmap(resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/FritzCall/images/no-face-error-hd.png"))
			elif DESKTOP_WIDTH <= 1920:
				picPixmap = LoadPixmap(resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/FritzCall/images/no-face-error-fhd.png"))
			else:
				picPixmap = LoadPixmap(resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/FritzCall/images/no-face-error-uhd.png"))

		picSize = picPixmap.size()
		self["FacePixmap"].instance.setPixmap(picPixmap)
		if config.plugins.FritzCall.advancedSkin.value:
			debug("skip layout manipulation")
			return

		noButtons = 3
		buttonSize = (self["key_red_p"].instance.size().width(), self["key_red_p"].instance.size().height())
		debug("[FritzOfferAction] buttonSize:" + repr(buttonSize))

		# recalculate window size
		textSize = self["text"].getSize()
		textSize = (textSize[0] + 20, textSize[1] + 20)  # don't know, why, but size is too small
		debug("[FritzOfferAction] textsize: " + repr(textSize))
		textSize = eSize(*textSize)

		gapSizeH = scaleH(-1, 5)
		width = max(scaleH(-1, 545), noButtons * (buttonSize[0] + gapSizeH) + gapSizeH, picSize.width() + textSize.width() + 30)
		height = max(picSize.height() + 5, textSize.height() + 5, scaleV(-1, 136)) + 5 + buttonSize[1] + 5
		buttonsGap = (width - noButtons * buttonSize[0]) / (noButtons + 1)
		buttonsVPos = height - buttonSize[1] - 5
		wSize = (width, height)

		wSize = eSize(*wSize)

		# center the smaller vertically
		hGap = (width - picSize.width() - textSize.width()) / 3
		picPos = (hGap, (height - 5 - buttonSize[1] - picSize.height()) / 2 + 5)
		textPos = (hGap + picSize.width() + hGap, (height - 5 - buttonSize[1] - 5 - textSize.height()) / 2 + 5)

		# resize screen
		self.instance.resize(wSize)
		# resize text
		self["text"].instance.resize(textSize)
		# resize pixmap
		self["FacePixmap"].instance.resize(picSize)
		self["FacePixmap"].instance.setPixmap(picPixmap)
		# move buttons
		buttonPos = (buttonsGap, buttonsVPos)
		self["key_red_p"].instance.move(ePoint(*buttonPos))
		self["key_red"].instance.move(ePoint(*buttonPos))
		buttonPos = (buttonsGap + buttonSize[0] + buttonsGap, buttonsVPos)
		self["key_green_p"].instance.move(ePoint(*buttonPos))
		self["key_green"].instance.move(ePoint(*buttonPos))
		buttonPos = (buttonsGap + buttonSize[0] + buttonsGap + buttonSize[0] + buttonsGap, buttonsVPos)
		self["key_yellow_p"].instance.move(ePoint(*buttonPos))
		self["key_yellow"].instance.move(ePoint(*buttonPos))
		# move text
		self["text"].instance.move(ePoint(*textPos))
		# move pixmap
		self["FacePixmap"].instance.move(ePoint(*picPos))
		# center window
		self.instance.move(ePoint((DESKTOP_WIDTH - wSize.width()) / 2, (DESKTOP_HEIGHT - wSize.height()) / 2))

	def _setTextAndResize(self, message):
		self["text"].instance.resize(eSize(*(DESKTOP_WIDTH, DESKTOP_HEIGHT)))
		self["text"].setText(self._number + "\n\n" + message)
		self._finishLayout()

	def _lookup(self):
		phonebookLocation = config.plugins.FritzCall.phonebookLocation.value
		if self._lookupState == 0:
			self._lookupState = 1
			self._setTextAndResize(_("Reverse searching..."))
			ReverseLookupAndNotifier(self._number, self._lookedUp, "UTF-8", config.plugins.FritzCall.countrycode.value)
			return
		if self._lookupState == 1 and os.path.exists(os.path.join(phonebookLocation, "PhoneBook.csv")):
			self._setTextAndResize(_("Searching in Outlook export..."))
			self._lookupState = 2
			self._lookedUp(self._number, FritzOutlookCSV.findNumber(self._number, os.path.join(phonebookLocation, "PhoneBook.csv")))  # @UndefinedVariable
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
		info("[FritzOfferAction]\n" + str(name.replace(", ", "\n")))
		self._setTextAndResize(str(name.replace(", ", "\n")))

	def _call(self):
		if fritzbox:
			debug("[FritzOfferAction]  %s", self._number)
			self.session.open(MessageBox, _("Calling %s") % self._number, type = MessageBox.TYPE_INFO)
			fritzbox.dial(self._number)
		else:
			error("[FritzOfferAction] no fritzbox object?!?!")
			self.session.open(MessageBox, _("FRITZ!Box not available for calling"), type = MessageBox.TYPE_INFO)

	def _add(self):
		debug("[FritzOfferAction] %s, %s", self._number, self._name)
		phonebook.FritzDisplayPhonebook(self._session).add(self._parent, self._number, self._name)
		self._exit()

	def _exit(self):
		self.close()

OneHour = 60 * 60 * 1000
# OneHour = 1000
class FritzCallPhonebook(object):
	def __init__(self):
		debug("[FritzCallPhonebook]")
		# Beware: strings in phonebook.phonebook have to be in utf-8!
		self.phonebook = {}
		if config.plugins.FritzCall.reloadPhonebookTime.value > 0:
			debug("[FritzCallPhonebook] start timer with " + repr(config.plugins.FritzCall.reloadPhonebookTime.value))
			self.loop = eTimer()

			# newer OE versions don't have the callback
			try:
				self.loop_conn = self.loop.timeout.connect(self.reload)
			except AttributeError:
				self.loop.callback.append(self.reload)

			self.loop.start(config.plugins.FritzCall.reloadPhonebookTime.value * OneHour, False)
		self.reload()

	def reload(self):
		debug("[FritzCallPhonebook] " + time.ctime())

		# Beware: strings in phonebook.phonebook have to be in utf-8!
		self.phonebook = {}

		if not config.plugins.FritzCall.enable.value:
			return

		phonebookFilenameOld = os.path.join(config.plugins.FritzCall.phonebookLocation.value, "PhoneBook.txt")
		phonebookFilename = os.path.join(config.plugins.FritzCall.phonebookLocation.value, "PhoneBook.json")
		if config.plugins.FritzCall.phonebook.value:
			if os.path.exists(phonebookFilename):
				# read json
				debug("[FritzCallPhonebook] read " + phonebookFilename)

				try:
					for k, v in json.loads(open(phonebookFilename).read().decode("utf-8")).items():
						# TODO if we change the value to a list of lines, we have to adapt this here
						self.phonebook[k.encode("utf-8")] = v.encode("utf-8")
				except (ValueError, UnicodeError, IOError) as e:
					error("[FritzCallPhonebook] Could not load %s: %s", phonebookFilename, str(e))
					Notifications.AddNotification(MessageBox, _("Could not load phonebook: %s") % (phonebookFilename + ": " + str(e)), type = MessageBox.TYPE_ERROR)

				# debug(repr(self.phonebook))
			elif os.path.exists(phonebookFilenameOld):  # read old format and dump to json
				debug("[FritzCallPhonebook] read " + phonebookFilenameOld)
				phonebookTxtCorrupt = False
				self.phonebook = {}
				for line in open(phonebookFilenameOld):
					# debug("[FritzCallPhonebook] got line from Phonebook.txt: %s" % ___(line))
					try:
						# Beware: strings in phonebook.phonebook have to be in utf-8!
						line = line.decode("utf-8")
					except UnicodeDecodeError:  # this is just for the case, somebody wrote latin1 chars into PhoneBook.txt
						try:
							line = line.decode("iso-8859-1")
							debug("[FritzCallPhonebook] Fallback to ISO-8859-1 in %s", line)
							phonebookTxtCorrupt = True
						except UnicodeDecodeError:
							error("[FritzCallPhonebook] Could not parse internal Phonebook Entry %s", line)
							phonebookTxtCorrupt = True
					line = line.encode("utf-8")
					elems = line.split('#')
					if len(elems) == 2:
						try:
							# debug("[FritzCallPhonebook] Adding '''%s''' with '''%s''' from internal phonebook!" % (__(elems[1].strip()), __(elems[0], False)))
							self.phonebook[elems[0]] = elems[1].strip()
						except ValueError:  # how could this possibly happen?!?!
							error("[FritzCallPhonebook] Could not parse internal Phonebook Entry %s", line)
							phonebookTxtCorrupt = True
					else:
						error("[FritzCallPhonebook] Could not parse internal Phonebook Entry %s", line)
						phonebookTxtCorrupt = True

				if phonebookTxtCorrupt:
					# dump phonebook to PhoneBook.txt
					debug("[FritzCallPhonebook] dump Phonebook.txt")
					try:
						os.rename(phonebookFilenameOld, phonebookFilenameOld + ".bck")
						fNew = open(phonebookFilenameOld, 'w')
						# Beware: strings in phonebook.phonebook are utf-8!
						for (number, name) in self.phonebook.iteritems():
							# Beware: strings in PhoneBook.txt have to be in utf-8!
							fNew.write(number + "#" + name.encode("utf-8"))
						fNew.close()
					except (IOError, OSError):
						error("[FritzCallPhonebook] error renaming or writing to %s", phonebookFilenameOld)

				os.rename(phonebookFilenameOld, phonebookFilenameOld + ".old")
				json.dump(self.phonebook, open(phonebookFilename, "w"), ensure_ascii=False, encoding="utf-8", indent=0, separators=(',', ': '), sort_keys=True)

		if fritzbox:
			if config.plugins.FritzCall.fritzphonebook.value:
				debug("[FritzCallPhonebook] config.plugins.FritzCall.fritzphonebook.value %s", repr(config.plugins.FritzCall.fritzphonebook.value))
				fritzbox.loadFritzBoxPhonebook(self)
			else:
				debug("[FritzCallPhonebook] config.plugins.FritzCall.fritzphonebook.value %s", repr(config.plugins.FritzCall.fritzphonebook.value))
				fritzbox.phonebook = self


#===============================================================================
# 		#
# 		# read entries from Outlook export
# 		#
# 		# not reliable with coding yet
# 		#
# 		# import csv exported from Outlook 2007 with csv(Windows)
# 		csvFilename = "/tmp/PhoneBook.csv"
# 		if config.plugins.FritzCall.phonebook.value and os.path.exists(csvFilename):
# 			try:
# 				readOutlookCSV(csvFilename, self.add)
# 				os.rename(csvFilename, csvFilename + ".done")
# 			except ImportError:
# 				debug("[FritzCallPhonebook] CSV import failed" %line)
#===============================================================================


#===============================================================================
# 		#
# 		# read entries from LDIF
# 		#
# 		# import ldif exported from Thunderbird 2.0.0.19
# 		ldifFilename = "/tmp/PhoneBook.ldif"
# 		if config.plugins.FritzCall.phonebook.value and os.path.exists(ldifFilename):
# 			try:
# 				parser = MyLDIF(open(ldifFilename), self.add)
# 				parser.parse()
# 				os.rename(ldifFilename, ldifFilename + ".done")
# 			except ImportError:
# 				debug("[FritzCallPhonebook] LDIF import failed" %line)
#===============================================================================

	def search(self, number, default = None, extended = True):
		# debug("[FritzCallPhonebook] Searching for %s" %number)
		name = ""
		if not self.phonebook or not number:
			return name

		if config.plugins.FritzCall.prefix.value:
			prefix = config.plugins.FritzCall.prefix.value
			if number[0] != '0':
				number = prefix + number
				# debug("[FritzCallPhonebook] added prefix: %s" %number)
			elif number[:len(prefix)] == prefix and number[len(prefix):] in self.phonebook:
				# debug("[FritzCallPhonebook] same prefix")
				name = self.phonebook[number[len(prefix):]]
				# debug("[FritzCallPhonebook] result: %s" %name)
		else:
			prefix = ""

		if not name and number in self.phonebook:
			name = self.phonebook[number]

		if not name and default:
			name = default

		if not name and extended and config.plugins.FritzCall.FritzExtendedSearchNames.value:
			for k in range(len(number) - 1, 0, -1):
				# debug("[FritzCallPhonebook] extended search: check: %s" %number[:k])
				name = self.search(number[:k], default, False)
				if name:
					# debug("[FritzCallPhonebook] search result for shortened number: %s" % name)
					break

		return name.replace(", ", "\n").strip()

	def add(self, number, name):
		'''

		@param number: number of entry
		@param name: name of entry, has to be in utf-8
		'''
		debug("[FritzCallPhonebook]")
		name = name.replace("\n", ", ")  # this is just for safety reasons. add should only be called with newlines converted into commas
		self.remove(number)
		self.phonebook[number] = name
		if number and number != 0:
			if config.plugins.FritzCall.phonebook.value:
				try:
# 					name = name.strip() + "\n"
# 					string = "%s#%s" % (number, name)
# 					# Beware: strings in Phonebook.json have to be in utf-8!
# 					f = open(os.path.join(config.plugins.FritzCall.phonebookLocation.value, "PhoneBook.txt"), 'a')
# 					f.write(string)
# 					f.close()
					phonebookFilename = os.path.join(config.plugins.FritzCall.phonebookLocation.value, "PhoneBook.json")
					# check whether PhoneBook.json exists, if not drop empty JSOn file
					if not os.path.isfile(phonebookFilename):
						json.dump({}, open(phonebookFilename, "w"), ensure_ascii=False, encoding="utf-8", indent=0, separators=(',', ': '), sort_keys=True)
						info("[FritzCallPhonebook] empty Phonebook.json created")

					phonebookTmp = {}
					for k, v in json.loads(open(phonebookFilename).read().decode("utf-8")).items():
						phonebookTmp[k.encode("utf-8")] = v.encode("utf-8")
					phonebookTmp[number] = name
					json.dump(self.phonebook, open(phonebookFilename, "w"), ensure_ascii=False, encoding="utf-8", indent=0, separators=(',', ': '), sort_keys=True)
					info("[FritzCallPhonebook] added %s with %s to Phonebook.json", number, name.strip())
					return True
				except IOError:
					return False

	def remove(self, number):
		if number in self.phonebook:
			debug("[FritzCallPhonebook]")
			del self.phonebook[number]
			if config.plugins.FritzCall.phonebook.value:
				try:
# 					phonebookFilename = os.path.join(config.plugins.FritzCall.phonebookLocation.value, "PhoneBook.json")
# 					debug("[FritzCallPhonebook] remove entry in Phonebook.json")
# 					fOld = open(phonebookFilename, 'r')
# 					fNew = open(phonebookFilename + str(os.getpid()), 'w')
# 					line = fOld.readline()
# 					while line:
# 						elems = line.split('#')
# 						if len(elems) == 2 and elems[0] != number:
# 							fNew.write(line)
# 						line = fOld.readline()
# 					fOld.close()
# 					fNew.close()
# 					# os.remove(phonebookFilename)
# 					eBackgroundFileEraser.getInstance().erase(phonebookFilename)
# 					os.rename(phonebookFilename + str(os.getpid()), 	phonebookFilename)
					phonebookFilename = os.path.join(config.plugins.FritzCall.phonebookLocation.value, "PhoneBook.json")
					phonebookTmp = {}
					for k, v in json.loads(open(phonebookFilename).read().decode("utf-8")).items():
						phonebookTmp[k.encode("utf-8")] = v.encode("utf-8")
					del phonebookTmp[number]
					json.dump(self.phonebook, open(phonebookFilename, "w"), ensure_ascii=False, encoding="utf-8", indent=0, separators=(',', ': '), sort_keys=True)
					info("[FritzCallPhonebook] removed %s from Phonebook.json", number)
					return True

				except (IOError, OSError):
					error("[FritzCallPhonebook] error removing %s from %s", number, phonebookFilename)
		return False

	class FritzDisplayPhonebook(Screen, HelpableScreen, NumericalTextInput):

		def __init__(self, session):
			if not config.plugins.FritzCall.advancedSkin.value:
				self.entriesWidth = DESKTOP_WIDTH * scaleH(75, 85) / 100
				self.height = DESKTOP_HEIGHT * 0.75
				numberFieldWidth = scaleH(220, 160)
				fieldWidth = self.entriesWidth - 5 - numberFieldWidth - 10
				fontSize = scaleV(22, 18)
				fontHeight = scaleV(24, 20)
				buttonGap = (self.entriesWidth - 4 * 140) / 5
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
						<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="blend" />
						<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="blend" />
						<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="blend" />
						<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="blend" />
						<widget name="key_red" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
						<widget name="key_green" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
						<widget name="key_yellow" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
						<widget name="key_blue" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
					</screen>""" % (
							# scaleH(90, 75), scaleV(100, 73), # position
							self.entriesWidth, self.height,  # size
							self.entriesWidth,  # eLabel width
							scaleH(40, 5), scaleV(20, 5),  # entries position
							self.entriesWidth - scaleH(40, 5), self.height - scaleV(20, 5) - 5 - 5 - 40,  # entries size
							0, 0, fieldWidth, scaleH(24, 20),  # name pos/size
							fieldWidth + 5, 0, numberFieldWidth, scaleH(24, 20),  # dir pos/size
							fontSize,  # fontsize
							fontHeight,  # itemHeight
							self.height - 40 - 5,  # eLabel position vertical
							self.entriesWidth,  # eLabel width
							buttonGap, self.height - 40, "skin_default/buttons/red.png",  # ePixmap red
							2 * buttonGap + 140, self.height - 40, "skin_default/buttons/green.png",  # ePixmap green
							3 * buttonGap + 2 * 140, self.height - 40, "skin_default/buttons/yellow.png",  # ePixmap yellow
							4 * buttonGap + 3 * 140, self.height - 40, "skin_default/buttons/blue.png",  # ePixmap blue
							buttonGap, self.height - 40, scaleV(22, 21),  # widget red
							2 * buttonGap + 140, self.height - 40, scaleV(22, 21),  # widget green
							3 * buttonGap + 2 * 140, self.height - 40, scaleV(22, 21),  # widget yellow
							4 * buttonGap + 3 * 140, self.height - 40, scaleV(22, 21),  # widget blue
							)
			else:
				if DESKTOP_WIDTH <= 720:
					self.skin = """
					<!-- SD screen -->
					<screen name="FritzDisplayPhonebook" position="center,center" size="620,460" title="Phonebook" >
							<widget source="entries" render="Listbox" position="10,5" size="600,400" enableWrapAround="1" scrollbarMode="showOnDemand">
								<convert type="TemplatedMultiContent">
									{"template": [
											MultiContentEntryText(pos = (5,0), size = (400,25), font=0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 1), # index 0 is the name, index 1 is shortname
											MultiContentEntryText(pos = (415,0), size = (145,25), font=0, flags = RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text = 2), # index 2 is number
										],
									"fonts": [gFont("Regular", 18)],
									"itemHeight": 25
									}
								</convert>
							</widget>
							<widget name="key_red" position="10,415" size="140,20" halign="center" font="Regular;18" />
							<widget name="key_green" position="160,415" size="140,20" halign="center" font="Regular;18" />
							<widget name="key_yellow" position="310,415" size="140,20"  halign="center" font="Regular;18" />
							<widget name="key_blue" position="460,415" size="140,20" halign="center" font="Regular;18" />
							<eLabel position="10,440" size="140,10" backgroundColor="#9f1313"/>
							<eLabel position="160,440" size="140,10" backgroundColor="#1f771f" />
							<eLabel position="310,440" size="140,10" backgroundColor="#a08500" />
							<eLabel position="460,440" size="140,10" backgroundColor="#0039f0"/>
					</screen>
					"""
				elif DESKTOP_WIDTH <= 1280:
					self.skin = """
					<!-- HD screen -->
					<screen name="FritzDisplayPhonebook" position="center,center" size="850,560" title="Phonebook" >
							<widget source="entries" render="Listbox" position="10,10" size="830,480" enableWrapAround="1" scrollbarMode="showOnDemand">
								<convert type="TemplatedMultiContent">
									{"template": [
											MultiContentEntryText(pos = (5,0), size = (500,30), font=0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 1), # index 0 is the name, index 1 is shortname
											MultiContentEntryText(pos = (520,0), size = (270,30), font=0, flags = RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text = 2), # index 2 is number
										],
									"fonts": [gFont("Regular", 20)],
									"itemHeight": 30
											}
								</convert>
							</widget>
							<widget name="key_red" position="10,510" size="200,25" halign="center" font="Regular;20" />
							<widget name="key_green" position="220,510" size="200,25" halign="center" font="Regular;20" />
							<widget name="key_yellow" position="430,510" size="200,25"  halign="center" font="Regular;20" />
							<widget name="key_blue" position="640,510" size="200,25" halign="center" font="Regular;20" />
							<eLabel position="10,540" size="200,10" backgroundColor="#9f1313"/>
							<eLabel position="220,540" size="200,10" backgroundColor="#1f771f" />
							<eLabel position="430,540" size="200,10" backgroundColor="#a08500" />
							<eLabel position="640,540" size="200,10" backgroundColor="#0039f0"/>
					</screen>
					"""
				elif DESKTOP_WIDTH <= 1920:
					self.skin = """
					<!-- Fullhd screen -->
					<screen name="FritzDisplayPhonebook" position="center,center" size="1450,850" title="Phonebook" >
							<widget source="entries" render="Listbox" position="10,10" size="1430,640" enableWrapAround="1" scrollbarMode="showOnDemand">
								<convert type="TemplatedMultiContent">
									{"template": [
											MultiContentEntryText(pos = (5,0), size = (980,40), font=0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 1), # index 0 is the name, index 1 is shortname
											MultiContentEntryText(pos = (1000,0), size = (390,40), font=0, flags = RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text = 2), # index 2 is number
										],
									"fonts": [gFont("Regular", 28)],
									"itemHeight": 40
											}
								</convert>
							</widget>
							<widget name="key_red" position="10,780" size="350,40" halign="center" font="Regular;30" />
							<widget name="key_green" position="370,780" size="350,40" halign="center" font="Regular;30" />
							<widget name="key_yellow" position="730,780" size="350,40"  halign="center" font="Regular;30" />
							<widget name="key_blue" position="1090,780" size="350,40" halign="center" font="Regular;30" />
							<eLabel position="10,830" size="350,8" backgroundColor="#9f1313"/>
							<eLabel position="370,830" size="350,8" backgroundColor="#1f771f" />
							<eLabel position="730,830" size="350,8" backgroundColor="#a08500" />
							<eLabel position="1090,830" size="350,8" backgroundColor="#0039f0"/>
					</screen>
					"""
				else:
					self.skin = """
					<!-- UHD screen -->
					<screen name="FritzDisplayPhonebook" position="center,center" size="2560,1540" title="Phonebook" >
							<widget source="entries" render="Listbox" position="10,10" size="2540,1330" enableWrapAround="1" scrollbarMode="showOnDemand">
								<convert type="TemplatedMultiContent">
									{"template": [
											MultiContentEntryText(pos = (20,0), size = (1900,70), font=0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = 1), # index 0 is the name, index 1 is shortname
											MultiContentEntryText(pos = (1950,0), size = (550,70), font=0, flags = RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text = 2), # index 2 is number
										],
									"fonts": [gFont("Regular", 58)],
									"itemHeight": 70
											}
								</convert>
							</widget>
							<widget name="key_red" position="10,1420" size="600,70" halign="center" font="Regular;60" />
							<widget name="key_green" position="660,1420" size="600,70" halign="center" font="Regular;60" />
							<widget name="key_yellow" position="1310,1420" size="600,70"  halign="center" font="Regular;60" />
							<widget name="key_blue" position="1950,1420" size="600,70" halign="center" font="Regular;60" />
							<eLabel position="10,1510" size="600,20" backgroundColor="#9f1313"/>
							<eLabel position="660,1510" size="600,20" backgroundColor="#1f771f" />
							<eLabel position="1310,1510" size="600,20" backgroundColor="#a08500" />
							<eLabel position="1950,1510" size="600,20" backgroundColor="#0039f0"/>
					</screen>
					"""

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
				"ok": self.showEntry, }, -2)

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
			debug("[FritzDisplayPhonebook]")
			self.help_window = None
			self.sortlist = []
			self.onLayoutFinish.append(self.setWindowTitle)
			self.display()

		def setWindowTitle(self):
			# TRANSLATORS: this is a window title.
			self.setTitle(_("Phonebook"))

		def display(self, filterNumber = ""):
			debug("[FritzDisplayPhonebook]")
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
						error("[FritzDisplayPhonebook] displayPhonebook/display: corrupt phonebook entry for %s", number)
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
				debug("[FritzDisplayPhonebook] %s", repr(cur))
				number = cur[2]
				name = cur[0]
				self.session.open(FritzOfferAction, self, number, name)

		def delete(self):
			cur = self["entries"].getCurrent()
			if cur:
				debug("[FritzDisplayPhonebook] %s", repr(cur))
				self.session.openWithCallback(
					self.deleteConfirmed,
					MessageBox,
					_("Do you really want to delete entry for\n\n%(number)s\n\n%(name)s?")
					% {'number':str(cur[2]), 'name':str(cur[0]).replace(", ", "\n")}
								)
			else:
				self.session.open(MessageBox, _("No entry selected"), MessageBox.TYPE_INFO)

		def deleteConfirmed(self, ret):
			debug("[FritzDisplayPhonebook]")
			#
			# if ret: delete number from sortlist, delete number from phonebook.phonebook and write it to disk
			#
			cur = self["entries"].getCurrent()
			if cur:
				if ret:
					# delete number from sortlist, delete number from phonebook.phonebook and write it to disk
					debug("[FritzDisplayPhonebook] %s", repr(cur))
					phonebook.remove(cur[2])
					self.display()
				# else:
					# self.session.open(MessageBox, _("Not deleted."), MessageBox.TYPE_INFO)
			else:
				self.session.open(MessageBox, _("No entry selected"), MessageBox.TYPE_INFO)

		def add(self, parent = None, number = "", name = ""):
			class AddScreen(Screen, ConfigListScreen):
				'''ConfiglistScreen with two ConfigTexts for Name and Number'''

				def __init__(self, session, parent, number = "", name = ""):
					if not config.plugins.FritzCall.advancedSkin.value:  #
						# setup screen with two ConfigText and OK and ABORT button
						#
						noButtons = 2
						width = max(scaleH(-1, 570), noButtons * 140)
						height = scaleV(-1, 100)  # = 5 + 126 + 40 + 5; 6 lines of text possible
						buttonsGap = (width - noButtons * 140) / (noButtons + 1)
						buttonsVPos = height - 40 - 5
						self.skin = """
							<screen position="center,center" size="%d,%d" title="Add entry to phonebook" >
							<widget name="config" position="5,5" size="%d,%d" scrollbarMode="showOnDemand" />
							<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="blend" />
							<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="blend" />
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
					else:
						if DESKTOP_WIDTH <= 720:
							self.skin = """
							<!-- SD screen -->
							<screen name="AddScreen" position="center,center" size="590,140" title="Add entry to phonebook" >
									<widget name="config" position="10,10" size="570,75" itemHeight="25" enableWrapAround="1" scrollbarMode="showOnDemand"/>
									<widget name="key_red" position="10,95" size="150,22" halign="center" font="Regular;18" />
									<widget name="key_green" position="430,95" size="150,22" halign="center" font="Regular;18" />
									<eLabel position="10,120" size="150,10" backgroundColor="#9f1313" />
									<eLabel position="430,120" size="150,10" backgroundColor="#1f771f" />
							</screen>
							"""
						elif DESKTOP_WIDTH <= 1280:
							self.skin = """
							<!-- HD screen -->
							<screen name="AddScreen" position="center,center" size="850,160" title="Add entry to phonebook" >
									<widget name="config" position="10,10" size="830,90" itemHeight="30" enableWrapAround="1" scrollbarMode="showOnDemand"/>
									<widget name="key_red" position="10,110" size="200,25" halign="center" font="Regular;20" />
									<widget name="key_green" position="640,110" size="200,25" halign="center" font="Regular;20" />
									<eLabel position="10,140" size="200,10" backgroundColor="#9f1313" />
									<eLabel position="640,140" size="200,10" backgroundColor="#1f771f" />
							</screen>
							"""
						elif DESKTOP_WIDTH <= 1920:
							self.skin = """
							<!-- Fullhd screen -->
							<screen name="AddScreen" position="center,center" size="1250,210" title="Add entry to phonebook" >
									<widget name="config" position="10,10" size="1230,120" itemHeight="40" enableWrapAround="1" scrollbarMode="showOnDemand"/>
									<widget name="key_red" position="10,140" size="300,40" halign="center" font="Regular;30" />
									<widget name="key_green" position="940,140" size="300,40" halign="center" font="Regular;30" />
									<eLabel position="10,190" size="300,8" backgroundColor="#9f1313"/>
									<eLabel position="940,190" size="300,8" backgroundColor="#1f771f"/>
							</screen>
							"""
						else:
							self.skin = """
							<!-- UHD screen -->
							<screen name="AddScreen" position="center,center" size="2250,350" title="Add entry to phonebook" >
									<widget name="config" position="10,10" size="2230,210" itemHeight="70" enableWrapAround="1" scrollbarMode="showOnDemand"/>
									<widget name="key_red" position="10,240" size="600,70" halign="center" font="Regular;60" />
									<widget name="key_green" position="1640,240" size="600,70" halign="center" font="Regular;60" />
									<eLabel position="10,320" size="600,20" backgroundColor="#9f1313"/>
									<eLabel position="1640,320" size="600,20" backgroundColor="#1f771f"/>
							</screen>
							"""

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
					ConfigListScreen.__init__(self, self.list, session = session)
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
					if self.number != "":
						# TRANSLATORS: this is a window title.
						self.setTitle(_("Edit selected entry"))
					else:
					# TRANSLATORS: this is a window title.
						self.setTitle(_("Add entry to phonebook"))

				def add(self):
					# get texts from Screen
					# add (number,name) to sortlist and phonebook.phonebook and disk
					self.name = config.plugins.FritzCall.name.value
					self.number = config.plugins.FritzCall.number.value
					if not self.number or not self.name:
						self.session.open(MessageBox, _("Entry incomplete."), type = MessageBox.TYPE_ERROR)
						return
					# add (number,name) to sortlist and phonebook.phonebook and disk
	# 					oldname = phonebook.search(self.number)
	# 					if oldname:
	# 						self.session.openWithCallback(
	# 							self.overwriteConfirmed,
	# 							MessageBox,
	# 							_("Do you really want to overwrite entry for %(number)s\n\n%(name)s\n\nwith\n\n%(newname)s?")
	# 							% {
	# 							'number':self.number,
	# 							'name': oldname,
	# 							'newname':self.name.replace(", ","\n")
	# 							}
	# 							)
	# 						self.close()
	# 						return
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

			debug("[FritzDisplayPhonebook]")
			if not parent:
				parent = self
			self.session.open(AddScreen, parent, number, name)

		def edit(self):
			debug("[FritzDisplayPhonebook]")
			cur = self["entries"].getCurrent()
			if cur is None:
				self.session.open(MessageBox, _("No entry selected"), MessageBox.TYPE_INFO)
			else:
				self.add(self, cur[2], cur[0])

		def search(self):
			debug("[FritzDisplayPhonebook]")
			self.help_window = self.session.instantiateDialog(NumericalTextInputHelpDialog, self)
			self.help_window.show()
			# VirtualKeyboard instead of InputBox?
			self.session.openWithCallback(self.doSearch, InputBox, _("Enter Search Terms"), _("Search phonebook"))

		def doSearch(self, searchTerms):
			if not searchTerms:
				searchTerms = ""
			debug("[FritzDisplayPhonebook]: " + searchTerms)
			if self.help_window:
				self.session.deleteDialog(self.help_window)
				self.help_window = None
			self.display(searchTerms)

		def exit(self):
			self.close()

phonebook = FritzCallPhonebook()

class FritzCallSetup(Screen, ConfigListScreen, HelpableScreen):

	def __init__(self, session, args = None):  # @UnusedVariable # pylint: disable=W0613
		if not config.plugins.FritzCall.advancedSkin.value:
			self.width = scaleH(20 + 4 * (140 + 90) + 2 * (35 + 40) + 20, 4 * 140 + 2 * 35)
			width = self.width
			debug("[FritzCallSetup] width: " + str(self.width))
			self.skin = """
				<screen name="FritzCallSetup" position="center,center" size="%d,%d" title="FritzCall Setup" >
				<eLabel position="0,0" size="%d,2" backgroundColor="#aaaaaa" />
				<widget name="consideration" position="%d,%d" halign="center" size="%d,%d" font="Regular;%d" backgroundColor="#20040404" transparent="1" />
				<eLabel position="0,%d" size="%d,2" backgroundColor="#aaaaaa" />
				<widget name="config" position="%d,%d" size="%d,%d" scrollbarMode="showOnDemand" backgroundColor="#20040404" transparent="1" />
				<eLabel position="0,%d" size="%d,2" backgroundColor="#aaaaaa" />
				<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="blend" />
				<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="blend" />
				<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="blend" />
				<ePixmap position="%d,%d" zPosition="4" size="140,40" pixmap="%s" transparent="1" alphatest="blend" />
				<widget name="key_red" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_green" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_yellow" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="key_blue" position="%d,%d" zPosition="5" size="140,40" valign="center" halign="center" font="Regular;%d" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<ePixmap position="%d,%d" zPosition="4" size="35,25" pixmap="%s" transparent="1" alphatest="blend" />
				<ePixmap position="%d,%d" zPosition="4" size="35,25" pixmap="%s" transparent="1" alphatest="blend" />
				</screen>""" % (
							# (DESKTOP_WIDTH-width)/2, scaleV(100, 73), # position
							width, scaleV(560, 430),  # size
							width,  # eLabel width
							scaleH(40, 20), scaleV(10, 5),  # consideration position
							scaleH(width - 80, width - 40), scaleV(25, 45),  # consideration size
							scaleV(22, 20),  # consideration font size
							scaleV(40, 50),  # eLabel position vertical
							width,  # eLabel width
							scaleH(40, 5), scaleV(60, 57),  # config position
							scaleH(width - 80, width - 10), scaleV(453, 328),  # config size
							scaleV(518, 390),  # eLabel position vertical
							width,  # eLabel width
							scaleH(20, 0), scaleV(525, 395), "skin_default/buttons/red.png",  # pixmap red
							scaleH(20 + 140 + 90, 140), scaleV(525, 395), "skin_default/buttons/green.png",  # pixmap green
							scaleH(20 + 2 * (140 + 90), 2 * 140), scaleV(525, 395), "skin_default/buttons/yellow.png",  # pixmap yellow
							scaleH(20 + 3 * (140 + 90), 3 * 140), scaleV(525, 395), "skin_default/buttons/blue.png",  # pixmap blue
							scaleH(20, 0), scaleV(525, 395), scaleV(21, 21),  # widget red
							scaleH(20 + (140 + 90), 140), scaleV(525, 395), scaleV(21, 21),  # widget green
							scaleH(20 + 2 * (140 + 90), 2 * 140), scaleV(525, 395), scaleV(21, 21),  # widget yellow
							scaleH(20 + 3 * (140 + 90), 3 * 140), scaleV(525, 395), scaleV(21, 21),  # widget blue
							scaleH(20 + 4 * (140 + 90), 4 * 140), scaleV(532, 402), "skin_default/buttons/key_info.png",  # button information
							scaleH(20 + 4 * (140 + 90) + (35 + 40), 4 * 140 + 35), scaleV(532, 402), "skin_default/buttons/key_menu.png",  # button menu
							)
		else:
			if DESKTOP_WIDTH <= 720:
				self.skin = """
					<!-- SD screen -->
					<screen name="FritzCallSetup" position="center,center" size="660,460" title="FritzCall Setup" >
							<widget name="consideration" position="10,10" halign="center" foregroundColor="#bab329" size="640,25" font="Regular;18"/>
							<eLabel position="10,35" size="640,2" backgroundColor="#aaaaaa" />
							<widget name="config" position="10,50" size="640,350" itemHeight="25" enableWrapAround="1" scrollbarMode="showOnDemand"/>
							<widget name="key_red" position="10,415" size="130,20" halign="center" font="Regular;18" />
							<widget name="key_green" position="150,415" size="130,20" halign="center" font="Regular;18" />
							<widget name="key_yellow" position="290,415" size="130,20"  halign="center" font="Regular;18" />
							<widget name="key_blue" position="430,415" size="130,20" halign="center" font="Regular;18" />
							<eLabel position="10,440" size="130,10" backgroundColor="#9f1313"/>
							<eLabel position="150,440" size="130,10" backgroundColor="#1f771f" />
							<eLabel position="290,440" size="130,10" backgroundColor="#a08500" />
							<eLabel position="430,440" size="130,10" backgroundColor="#0039f0"/>
							<eLabel font="Regular;17" foregroundColor="#aaaaaa" position="570,435" size="50,20" text="Menu" />
							<eLabel font="Regular;17" foregroundColor="#aaaaaa" position="630,435" size="30,20" text="Info" />
					</screen>
					"""
			elif DESKTOP_WIDTH <= 1280:
				self.skin = """
					<!-- HD screen -->
					<screen name="FritzCallSetup" position="center,center" size="1020,560" title="FritzCall Setup" >
							<widget name="consideration" position="10,8" halign="center" foregroundColor="#bab329" size="1000,30" font="Regular;20"/>
							<eLabel position="10,40" size="1000,2" backgroundColor="#aaaaaa" />
							<widget name="config" position="10,50" size="1000,450" itemHeight="30" enableWrapAround="1" scrollbarMode="showOnDemand"/>
							<widget name="key_red" position="10,510" size="200,25" halign="center" font="Regular;20" />
							<widget name="key_green" position="220,510" size="200,25" halign="center" font="Regular;20" />
							<widget name="key_yellow" position="430,510" size="200,25"  halign="center" font="Regular;20" />
							<widget name="key_blue" position="640,510" size="200,25" halign="center" font="Regular;20" />
							<eLabel position="10,540" size="200,10" backgroundColor="#9f1313"/>
							<eLabel position="220,540" size="200,10" backgroundColor="#1f771f" />
							<eLabel position="430,540" size="200,10" backgroundColor="#a08500" />
							<eLabel position="640,540" size="200,10" backgroundColor="#0039f0"/>
							<eLabel font="Regular;20" foregroundColor="#aaaaaa" position="880,530" size="70,25" text="Menu" />
							<eLabel font="Regular;20" foregroundColor="#aaaaaa" position="960,530" size="60,25" text="Info" />
					</screen>
					"""
			elif DESKTOP_WIDTH <= 1920:
				self.skin = """
					<!-- Fullhd screen -->
					<screen name="FritzCallSetup" position="center,center" size="1550,850" title="FritzCall Setup" >
						<widget name="consideration" position="10,10" halign="center" foregroundColor="#bab329" size="1530,40" font="Regular;30"/>
						<eLabel position="10,55" size="1530,2" backgroundColor="#aaaaaa" />
						<widget name="config" position="10,65" size="1530,680" itemHeight="40" enableWrapAround="1" scrollbarMode="showOnDemand"/>
						<widget name="key_red" position="10,780" size="320,40" halign="center" font="Regular;30" />
						<widget name="key_green" position="340,780" size="320,40" halign="center" font="Regular;30" />
						<widget name="key_yellow" position="670,780" size="320,40"  halign="center" font="Regular;30" />
						<widget name="key_blue" position="1000,780" size="320,40" halign="center" font="Regular;30" />
						<eLabel position="10,830" size="320,8" backgroundColor="#9f1313"/>
						<eLabel position="340,830" size="320,8" backgroundColor="#1f771f" />
						<eLabel position="670,830" size="320,8" backgroundColor="#a08500" />
						<eLabel position="1000,830" size="320,8" backgroundColor="#0039f0"/>
						<eLabel font="Regular;30" foregroundColor="#aaaaaa" position="1350,810" size="90,35" text="Menu" />
						<eLabel font="Regular;30" foregroundColor="#aaaaaa" position="1470,810" size="80,35" text="Info" />
					</screen>
					"""
			else:
				self.skin = """
					<!-- UHD screen -->
					<screen name="FritzCallSetup" position="center,center" size="3180,1540" title="FritzCall Setup" >
						<widget name="consideration" position="10,10" halign="center" foregroundColor="#bab329" size="3160,80" font="Regular;65"/>
						<eLabel position="10,100" size="3160,4" backgroundColor="#aaaaaa" />
						<widget name="config" position="10,110" size="3160,1260" itemHeight="70" enableWrapAround="1" scrollbarMode="showOnDemand"/>
						<widget name="key_red" position="10,1420" size="600,70" halign="center" font="Regular;60" />
						<widget name="key_green" position="660,1420" size="600,70" halign="center" font="Regular;60" />
						<widget name="key_yellow" position="1310,1420" size="600,70"  halign="center" font="Regular;60" />
						<widget name="key_blue" position="1950,1420" size="600,70" halign="center" font="Regular;60" />
						<eLabel position="10,1510" size="600,20" backgroundColor="#9f1313"/>
						<eLabel position="660,1510" size="600,20" backgroundColor="#1f771f" />
						<eLabel position="1310,1510" size="600,20" backgroundColor="#a08500" />
						<eLabel position="1950,1510" size="600,20" backgroundColor="#0039f0"/>
						<eLabel font="Regular;65" foregroundColor="#aaaaaa" position="2700,1445" size="280,75" text="Menu" />
						<eLabel font="Regular;65" foregroundColor="#aaaaaa" position="3000,1445" size="160,75" text="Info" />
					</screen>
					"""

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
		}, -2)

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

		ConfigListScreen.__init__(self, self.list, session = session)

		try:
			config.plugins.FritzCall.guestPassword.value = decode(config.plugins.FritzCall.guestPassword.value)
		except binascii.Error:
			config.plugins.FritzCall.guestPassword.value = ""
		try:
			config.plugins.FritzCall.password.value = decode(config.plugins.FritzCall.password.value)
		except binascii.Error:
			config.plugins.FritzCall.password.value = ""

		# get new list of locations for Phonebook.json
		self.createSetup()
		self.onLayoutFinish.append(self.setWindowTitle)

	def setWindowTitle(self):
		# TRANSLATORS: this is a window title.
		self.setTitle(_("FritzCall Setup") + " (" + "$Revision: 1481 $"[1:-1] + "$Date: 2017-07-04 10:28:00 +0200 (Tue, 04 Jul 2017) $"[7:23] + ")")

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.createSetup()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.createSetup()

	def createSetup(self):
		self.list = []
		self.list.append(getConfigListEntry(_("Call monitoring"), config.plugins.FritzCall.enable))
		if config.plugins.FritzCall.enable.value:
			self.list.append(getConfigListEntry(_("FRITZ!Box FON address (Name or IP)"), config.plugins.FritzCall.hostname))
			self.list.append(getConfigListEntry(_("FRITZ!Box FON firmware version"), config.plugins.FritzCall.fwVersion))

			self.list.append(getConfigListEntry(_("Show after Standby"), config.plugins.FritzCall.afterStandby))

			self.list.append(getConfigListEntry(_("Show only calls for specific MSN"), config.plugins.FritzCall.filter))
			if config.plugins.FritzCall.filter.value:
				self.list.append(getConfigListEntry(_("MSN to show (separated by ,)"), config.plugins.FritzCall.filtermsn))
				self.list.append(getConfigListEntry(_("Filter also list of calls"), config.plugins.FritzCall.filterCallList))

			self.list.append(getConfigListEntry(_("Mute on incoming call"), config.plugins.FritzCall.muteOnCall))
			self.list.append(getConfigListEntry(_("Mute on outgoing calls"), config.plugins.FritzCall.muteOnOutgoingCall))

			self.list.append(getConfigListEntry(_("Show Blocked Calls"), config.plugins.FritzCall.showBlacklistedCalls))
			self.list.append(getConfigListEntry(_("Show Outgoing Calls"), config.plugins.FritzCall.showOutgoingCalls))
			# not only for outgoing: config.plugins.FritzCall.showOutgoingCalls.value:
			self.list.append(getConfigListEntry(_("Areacode to add to calls without one (if necessary)"), config.plugins.FritzCall.prefix))
			self.list.append(getConfigListEntry(_("Timeout for Call Notifications (seconds)"), config.plugins.FritzCall.timeout))

			self.list.append(getConfigListEntry(_("Country"), config.plugins.FritzCall.country))
			if config.plugins.FritzCall.country.value:
				self.list.append(getConfigListEntry(_("Reverse Lookup Caller ID"), config.plugins.FritzCall.lookup))
				config.plugins.FritzCall.countrycode.value = config.plugins.FritzCall.country.value
			# else:
			self.list.append(getConfigListEntry(_("Countrycode (e.g. 0044 for UK, 0034 for Spain, etc.)"), config.plugins.FritzCall.countrycode))

			if config.plugins.FritzCall.fwVersion.value is not None:
				if config.plugins.FritzCall.fwVersion.value == "05.50" or config.plugins.FritzCall.fwVersion.value == "06.35"or config.plugins.FritzCall.fwVersion.value == "upnp":
					self.list.append(getConfigListEntry(_("User name Accessing FRITZ!Box"), config.plugins.FritzCall.username))
				self.list.append(getConfigListEntry(_("Password Accessing FRITZ!Box"), config.plugins.FritzCall.password))
				self.list.append(getConfigListEntry(_("Extension number to initiate call on"), config.plugins.FritzCall.extension))
# 				if config.plugins.FritzCall.fwVersion.value == "05.50" or config.plugins.FritzCall.fwVersion.value == "06.35":
# 					self.list.append(getConfigListEntry(_("Name of WLAN guest network"), config.plugins.FritzCall.guestSSID))
# 					self.list.append(getConfigListEntry(_("Secure WLAN guest network"), config.plugins.FritzCall.guestSecure))
# 					self.list.append(getConfigListEntry(_("Password of WLAN guest network"), config.plugins.FritzCall.guestPassword))
# 					self.list.append(getConfigListEntry(_("Minutes of uptime of WLAN guest network"), config.plugins.FritzCall.guestUptime))
				self.list.append(getConfigListEntry(_("Read PhoneBook from FRITZ!Box"), config.plugins.FritzCall.fritzphonebook))
				if config.plugins.FritzCall.fritzphonebook.value:
					self.list.append(getConfigListEntry(_("FRITZ!Box PhoneBook to read"), config.plugins.FritzCall.fritzphonebookName))
					if config.plugins.FritzCall.fwVersion.value == "06.35":
						self.list.append(getConfigListEntry(_("Show also internal numbers"), config.plugins.FritzCall.fritzphonebookShowInternal))
					self.list.append(getConfigListEntry(_("Append type of number"), config.plugins.FritzCall.showType))
					self.list.append(getConfigListEntry(_("Append shortcut number"), config.plugins.FritzCall.showShortcut))
					self.list.append(getConfigListEntry(_("Append vanity name"), config.plugins.FritzCall.showVanity))
			else:
				config.plugins.FritzCall.fritzphonebook.value = False

			self.list.append(getConfigListEntry(_("Use internal PhoneBook"), config.plugins.FritzCall.phonebook))
			if config.plugins.FritzCall.phonebook.value:
				if config.plugins.FritzCall.lookup.value:
					self.list.append(getConfigListEntry(_("Automatically add new Caller to PhoneBook"), config.plugins.FritzCall.addcallers))
			self.list.append(getConfigListEntry(_("PhoneBook and Faces Location"), config.plugins.FritzCall.phonebookLocation))

			if config.plugins.FritzCall.phonebook.value or config.plugins.FritzCall.fritzphonebook.value:
				self.list.append(getConfigListEntry(_("Reload interval for phonebooks (hours)"), config.plugins.FritzCall.reloadPhonebookTime))

			if config.plugins.FritzCall.phonebook.value or config.plugins.FritzCall.fritzphonebook.value:
				self.list.append(getConfigListEntry(_("Extended Search for names"), config.plugins.FritzCall.FritzExtendedSearchNames))
			self.list.append(getConfigListEntry(_("Extended Search for faces"), config.plugins.FritzCall.FritzExtendedSearchFaces))

			self.list.append(getConfigListEntry(_("Strip Leading 0"), config.plugins.FritzCall.internal))
			# self.list.append(getConfigListEntry(_("Default display mode for FRITZ!Box calls"), config.plugins.FritzCall.fbfCalls))
			self.list.append(getConfigListEntry(_("Display connection infos"), config.plugins.FritzCall.connectionVerbose))
			self.list.append(getConfigListEntry(_("Ignore callers with no phone number"), config.plugins.FritzCall.ignoreUnknown))
			self.list.append(getConfigListEntry(_("Log level"), config.plugins.FritzCall.debug))
			self.list.append(getConfigListEntry(_("Make it more skin friendly"), config.plugins.FritzCall.advancedSkin))

		self["config"].list = self.list
		self["config"].l.setList(self.list)

	def save(self):
# 		debug("[FritzCallSetup]"
		global fritzbox
		if self["config"].getCurrent()[1] == config.plugins.FritzCall.phonebookLocation:
			self.session.openWithCallback(self.LocationBoxClosed, LocationBox, _("PhoneBook and Faces Location"), currDir = config.plugins.FritzCall.phonebookLocation.value)

		if fritzbox and config.plugins.FritzCall.password.isChanged():
			fritzbox.password = config.plugins.FritzCall.password.value
		config.plugins.FritzCall.password.value = encode(config.plugins.FritzCall.password.value)
		if fritzbox and config.plugins.FritzCall.guestPassword.isChanged():
			fritzbox.guestPassword = config.plugins.FritzCall.guestPassword.value
		config.plugins.FritzCall.guestPassword.value = encode(config.plugins.FritzCall.guestPassword.value)

		for x in self["config"].list:
			# debug("Save " + repr(x[1].value))
			x[1].save()

		if not config.plugins.FritzCall.fwVersion.value:
			Notifications.AddNotification(MessageBox, _("To enjoy more functionalities of your FRITZ!Box, configure the firmware version!"), type = MessageBox.TYPE_INFO, timeout = 4)
			fritzbox = FritzCallFBF.FritzCallFBF_dummy()
			config.plugins.FritzCall.fritzphonebook.value = False
		elif config.plugins.FritzCall.fwVersion.value == "old":
			fritzbox = FritzCallFBF.FritzCallFBF()
		elif config.plugins.FritzCall.fwVersion.value == "05.27":
			fritzbox = FritzCallFBF.FritzCallFBF_05_27()
		elif config.plugins.FritzCall.fwVersion.value == "05.50":
			fritzbox = FritzCallFBF.FritzCallFBF_05_50()
		elif config.plugins.FritzCall.fwVersion.value == "06.35":
# 				fritzbox = FritzCallFBF.FritzCallFBF_06_35()
# 			elif config.plugins.FritzCall.fwVersion.value == "upnp":
			fritzbox = FritzCallFBF.FritzCallFBF_upnp()
		else:
			Notifications.AddNotification(MessageBox, _("FRITZ!Box firmware version not configured! Please set it in the configuration."), type = MessageBox.TYPE_INFO, timeout = 0)

		phonebook.reload()

		logger.setLevel(int(config.plugins.FritzCall.debug.value))

		if fritz_call:
			if config.plugins.FritzCall.enable.value:
				fritz_call.connect()
			else:
				fritz_call.shutdown()
		self.close()

	def LocationBoxClosed(self, path):
		if path is not None:
			config.plugins.FritzCall.phonebookLocation.setValue(path)

	def cancel(self):
# 		debug("[FritzCallSetup]"
		config.plugins.FritzCall.password.value = encode(config.plugins.FritzCall.password.value)
		config.plugins.FritzCall.guestPassword.value = encode(config.plugins.FritzCall.guestPassword.value)
		for x in self["config"].list:
			x[1].cancel()
		self.close()

	def displayCalls(self):
		if config.plugins.FritzCall.enable.value:
			if fritzbox and config.plugins.FritzCall.fwVersion.value:
				self.session.open(FritzDisplayCalls)
			else:
				self.session.open(MessageBox, _("Cannot get calls from FRITZ!Box"), type = MessageBox.TYPE_INFO)
		else:
			self.session.open(MessageBox, _("Plugin not enabled"), type = MessageBox.TYPE_INFO)

	def displayPhonebook(self):
		if phonebook:
			if config.plugins.FritzCall.enable.value:
				self.session.open(phonebook.FritzDisplayPhonebook)
			else:
				self.session.open(MessageBox, _("Plugin not enabled"), type = MessageBox.TYPE_INFO)
		else:
			self.session.open(MessageBox, _("No phonebook"), type = MessageBox.TYPE_INFO)

	def about(self):
		self.session.open(FritzAbout)

	def menu(self):
		if config.plugins.FritzCall.enable.value:
			if fritzbox and fritzbox.information:
				self.session.open(FritzMenu)
			else:
				self.session.open(MessageBox, _("Cannot get infos from FRITZ!Box yet\nStill initialising or wrong firmware version"), type = MessageBox.TYPE_INFO)
		else:
			self.session.open(MessageBox, _("Plugin not enabled"), type = MessageBox.TYPE_INFO)

standbyMode = False

class FritzCallList(object):
	def __init__(self):
		self.callList = []

	def add(self, event, date, number, caller, phone):
		debug("[FritzCallList] %s %s", number, caller)
		if len(self.callList) > 10:
			if self.callList[0] != "Start":
				self.callList[0] = "Start"
			del self.callList[1]

		self.callList.append((event, number, date, caller, phone))

	def display(self):
		debug("[FritzCallList]")
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

				# shorten the date information
				date = date[:6] + date[9:14]

				# our phone could be of the form "0123456789 (home)", then we only take "home"
				oBrack = phone.find('(')
				cBrack = phone.find(')')
				if oBrack != -1 and cBrack != -1:
					phone = phone[oBrack + 1:cBrack]

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
						caller = caller[:-1]
					else:
						phone = phone[:-1]

				text = text + "%s %s %s %s\n" % (date, caller, direction, phone)
				debug("[FritzCallList] '%s %s %s %s'", date, caller, direction, phone)

		# display screen
		Notifications.AddNotification(MessageBox, text, type = MessageBox.TYPE_INFO)
		self.callList = []

callList = FritzCallList()

def findFace(number, name):
	# debug("[FritzCall] number/name: %s/%s" % (number, name))
	if name:
		sep = name.find(',')
		if sep != -1:
			name = name[:sep]
		sep = name.find('\n')
		if sep != -1:
			name = name[:sep]
	else:
		name = _("UNKNOWN")
	# debug("[FritzCall] looking for: %s" %name)

	facesDir = os.path.join(config.plugins.FritzCall.phonebookLocation.value, "FritzCallFaces")
	# debug("[FritzCall] looking in: %s" %facesDir)
	facesFile = None

	if not os.path.isdir(facesDir):
		error("[FritzCall] findFace facesdir does not exist: %s", facesDir)
	else:
		files = os.listdir(facesDir)
		# debug("[FritzCall] listdir: %s" %repr(files))
		myFiles = [f for f in files if re.match(re.escape(number) + r"\.[png|PNG]", f)]
		if not myFiles:
			myFiles = [f for f in files if re.match(re.escape(name) + r"\.[png|PNG]", f)]

		if not myFiles:
			sep = name.find(' (')
			if sep != -1:
				name = name[:sep]
			myFiles = [f for f in files if re.match(re.escape(name) + r"\.[png|PNG]", f)]

		if myFiles:
			# debug("[FritzCall] found: %s" %repr(myFiles))
			facesFile = os.path.join(facesDir, myFiles[0])

		if not facesFile and config.plugins.FritzCall.FritzExtendedSearchFaces.value:
			for k in range(len(number) - 1, 0, -1):
				# debug("[FritzCall] extended search: %s" %number[:k])
				myFiles = [f for f in files if re.match(re.escape(number[:k]) + r"\.[png|PNG]", f)]
				if myFiles:
					facesFile = os.path.join(facesDir, myFiles[0])
					break

	if not facesFile:
		if DESKTOP_WIDTH <= 720:
			facesFile = resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/FritzCall/images/no-face-sd.png")
		elif DESKTOP_WIDTH <= 1280:
			facesFile = resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/FritzCall/images/no-face-hd.png")
		elif DESKTOP_WIDTH <= 1920:
			facesFile = resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/FritzCall/images/no-face-fhd.png")
		else:
			facesFile = resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/FritzCall/images/no-face-uhd.png")

	info("[FritzCall] result: %s", __(facesFile))
	return facesFile

class MessageBoxPixmap(Screen):
	def __init__(self, session, text, number = "", name = "", timeout = -1):
		if not config.plugins.FritzCall.advancedSkin.value:
			self.skin = """
		<screen name="MessageBoxPixmap" position="center,center" size="600,10" title="New Call">
			<widget name="text" position="115,8" size="520,0" font="Regular;%d" />
			<widget name="InfoPixmap" pixmap="%s" position="5,5" size="100,100" alphatest="blend" />
		</screen>
			""" % (
				# scaleH(350, 60), scaleV(175, 245),
				scaleV(25, 22), resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/input_info.png")
				)
			debug("[FritzCall] MessageBoxPixmap number: %s", number)
		else:
			if DESKTOP_WIDTH <= 720:
				self.skin = """
				<!-- SD screen -->
				<screen name="MessageBoxPixmap" position="center,center" size="490,200" title="New Call">
					<widget name="InfoPixmap" position="10,10" size="160,160" alphatest="blend" />
					<widget name="text" halign="left" valign="center" position="220,10" size="260,180" font="Regular;18"/>
				</screen>
				"""
			elif DESKTOP_WIDTH <= 1280:
				self.skin = """
				<!-- HD screen -->
				<screen name="MessageBoxPixmap" position="center,center" size="700,270" title="New Call">
					<widget name="InfoPixmap" position="10,10" size="230,230" alphatest="blend" />
					<widget name="text" halign="left" valign="center" position="290,10" size="400,250" font="Regular;20"/>
				</screen>
				"""
			elif DESKTOP_WIDTH <= 1920:
				self.skin = """
				<!-- Fullhd screen -->
				<screen name="MessageBoxPixmap" position="center,center" size="1150,420" title="New Call">
					<widget name="InfoPixmap" position="10,10" size="400,400" alphatest="blend" />
					<widget name="text" halign="left" valign="center" position="470,10" size="670,400" font="Regular;30"/>
				</screen>
				"""
			else:
				self.skin = """
				<!-- UHD screen -->
				<screen name="MessageBoxPixmap" position="center,center" size="2080,820" title="New Call">
					<widget name="InfoPixmap" position="10,10" size="800,800" alphatest="blend" />
					<widget name="text" halign="left" valign="center" position="900,10" size="1150,800" font="Regular;60"/>
				</screen>
				"""

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
			"ok": self._exit, }, -2)

	def _finishLayout(self):
		debug("[FritzCall] MessageBoxPixmap/setInfoPixmap number: %s/%s", self._number, self._name)

		self.setTitle(_("New call"))

		faceFile = findFace(self._number, self._name)
		picPixmap = LoadPixmap(faceFile)
		if not picPixmap:  # that means most probably, that the picture is not 8 bit...
			Notifications.AddNotification(MessageBox, _("Found picture\n\n%s\n\nBut did not load. Probably not PNG, 8-bit") % faceFile, type = MessageBox.TYPE_ERROR)
			if DESKTOP_WIDTH <= 720:
				picPixmap = LoadPixmap(resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/FritzCall/images/no-face-error-sd.png"))
			elif DESKTOP_WIDTH <= 1280:
				picPixmap = LoadPixmap(resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/FritzCall/images/no-face-error-hd.png"))
			elif DESKTOP_WIDTH <= 1920:
				picPixmap = LoadPixmap(resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/FritzCall/images/no-face-error-fhd.png"))
			else:
				picPixmap = LoadPixmap(resolveFilename(SCOPE_CURRENT_PLUGIN, "Extensions/FritzCall/images/no-face-error-uhd.png"))
		picSize = picPixmap.size()
		self["InfoPixmap"].instance.setPixmap(picPixmap)
		if config.plugins.FritzCall.advancedSkin.value:
			debug("skip layout manipulation")
			return

		# recalculate window size
		textSize = self["text"].getSize()
		textSize = (textSize[0] + 20, textSize[1] + 20)  # don't know, why, but size is too small
		textSize = eSize(*textSize)
		width = max(scaleH(600, 280), picSize.width() + textSize.width() + 30)
		height = max(scaleV(300, 250), picSize.height() + 10, textSize.height() + 10)
		wSize = (width, height)
		wSize = eSize(*wSize)

		# center the smaller vertically
		hGap = (width - picSize.width() - textSize.width()) / 3
		picPos = (hGap, (height - picSize.height()) / 2 + 1)
		textPos = (hGap + picSize.width() + hGap, (height - textSize.height()) / 2 + 1)

		# resize screen
		self.instance.resize(wSize)
		# resize text
		self["text"].instance.resize(textSize)
		# resize pixmap
		self["InfoPixmap"].instance.resize(picSize)
		self["InfoPixmap"].instance.setPixmap(picPixmap)
		# move text
		self["text"].instance.move(ePoint(*textPos))
		# move pixmap
		self["InfoPixmap"].instance.move(ePoint(*picPos))
		# center window
		self.instance.move(ePoint((DESKTOP_WIDTH - wSize.width()) / 2, (DESKTOP_HEIGHT - wSize.height()) / 2))

	def _initTimeout(self):
		if self._timeout > 0:
			self._timer = eTimer()

			# newer OE versions don't have the callback
			try:
				self._timer_conn = self._timer.timeout.connect(self._timerTick)
			except AttributeError:
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
# 	def stopTimer(self):
# 		if self._timerRunning:
# 			del self._timer
# 			self.setTitle(self._origTitle)
# 			self._timerRunning = False
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

def runUserActionScript(event, date, number, caller, phone):
	# user exit
	# call FritzCallserAction.sh in the same dir as Phonebook.json with the following parameters:
	# event: "RING" (incomning) or "CALL" (outgoing)
	# date of event, format: "dd.mm.yy hh.mm.ss"
	# telephone number which is calling/is called
	# caller's name and address, format Name\n Street\n ZIP City
	# line/number which is called/which is used for calling
	userActionScript = os.path.join(config.plugins.FritzCall.phonebookLocation.value, "FritzCallUserAction.sh")
	if os.path.exists(userActionScript) and os.access(userActionScript, os.X_OK):
		cmd = userActionScript + ' "' + event + '" "' + date + '" "' + number + '" "' + caller + '" "' + phone + '"'
		info("[FritzCall] calling: %s", cmd)
		eConsoleAppContainer().execute(cmd)

userActionList = [runUserActionScript]
def registerUserAction(fun):
	#===========================================================================
	# other plugins can register a function, which is then called for each displayed call
	# it must take the arguments event,date,number,caller,phone
	#
	# example:
	# def FritzCallEvent(event,date,number,caller,phone):
	# ......
	#
	# try:
	# 	from Plugins.Extensions.FritzCall.plugin import registerUserAction as FritzCallRegisterUserAction
	# 	FritzCallRegisterUserAction(FritzCallEvent)
	# except:
	# 	print "import of FritzCall failed"
	#===========================================================================
	info("[FritzCall] register: %s", fun.__name__)
	userActionList.append(fun)

mutedOnConnID = None
def notifyCall(event, date, number, caller, phone, connID): # @UnusedVariable # pylint: disable=W0613
	if Standby.inStandby is None or config.plugins.FritzCall.afterStandby.value == "each":
		if event == "RING":
			text = _("Incoming Call on %(date)s at %(time)s from\n---------------------------------------------\n%(number)s\n%(caller)s\n---------------------------------------------\nto: %(phone)s") % {'date':date[:8], 'time':date[9:], 'number':number, 'caller':caller, 'phone':phone}
		else:
			text = _("Outgoing Call on %(date)s at %(time)s to\n---------------------------------------------\n%(number)s\n%(caller)s\n---------------------------------------------\nfrom: %(phone)s") % {'date':date[:8], 'time':date[9:], 'number':number, 'caller':caller, 'phone':phone}
		info("[FritzCall]\n%s", text)
		# Notifications.AddNotification(MessageBox, text, type=MessageBox.TYPE_INFO, timeout=config.plugins.FritzCall.timeout.value)
		Notifications.AddNotification(MessageBoxPixmap, text, number = number, name = caller, timeout = config.plugins.FritzCall.timeout.value)
	elif config.plugins.FritzCall.afterStandby.value == "inList":
		#
		# if not yet done, register function to show call list
		global standbyMode
		if not standbyMode:
			standbyMode = True
			Standby.inStandby.onHide.append(callList.display)  # @UndefinedVariable
		# add text/timeout to call list
		callList.add(event, date, number, caller, phone)
		info("[FritzCall] added to callList")
	else:  # this is the "None" case
		info("[FritzCall] standby and no show")

	for fun in userActionList:
		info("[FritzCall] call user action: %s", fun.__name__)
		fun(event, date, number, caller, phone)


#===============================================================================
# 		We need a separate class for each invocation of reverseLookup to retain
# 		the necessary data for the notification
#===============================================================================

countries = {}
reverselookupMtime = 0

class FritzReverseLookupAndNotifier(object):
	def __init__(self, event, number, caller, phone, date, connID):
		'''

		Initiate a reverse lookup for the given number in the configured country

		@param event: CALL or RING
		@param number: number to be looked up
		@param caller: caller including name and address
		@param phone: Number (and name) of or own phone
		@param date: date of call
		'''
		info("[FritzReverseLookupAndNotifier] reverse Lookup for %s!", number)
		self.event = event
		self.number = number
		self.caller = caller
		self.phone = phone
		self.date = date
		self.connID = connID

		if number[0] != "0":
			self.notifyAndReset(number, caller)
			return

		ReverseLookupAndNotifier(number, self.notifyAndReset, "UTF-8", config.plugins.FritzCall.countrycode.value)

	def notifyAndReset(self, number, caller):
		'''

		this gets called with the result of the reverse lookup

		@param number: number
		@param caller: name and address of remote. it comes in with name, address and city separated by commas
		'''
		info("[FritzReverseLookupAndNotifier] got: " + caller)
		self.number = number
#===============================================================================
# 		if not caller and os.path.exists(config.plugins.FritzCall.phonebookLocation.value + "/PhoneBook.csv"):
# 			caller = FritzOutlookCSV.findNumber(number, config.plugins.FritzCall.phonebookLocation.value + "/PhoneBook.csv") #@UndefinedVariable
# 			debug("[FritzReverseLookupAndNotifier] got from Outlook csv: " + caller)
#===============================================================================
#===============================================================================
# 		if not caller and os.path.exists(config.plugins.FritzCall.phonebookLocation.value + "/PhoneBook.ldif"):
# 			caller = FritzLDIF.findNumber(number, open(config.plugins.FritzCall.phonebookLocation.value + "/PhoneBook.ldif"))
# 			debug("[FritzReverseLookupAndNotifier] got from ldif: " + caller)
#===============================================================================

		name = handleReverseLookupResult(caller)
		if name:
			self.caller = name.replace(", ", "\n")
			if self.number != 0 and config.plugins.FritzCall.addcallers.value:
				info("[FritzReverseLookupAndNotifier] add to phonebook")
				phonebook.add(self.number, self.caller)
		else:
			name = resolveNumberWithAvon(self.number, config.plugins.FritzCall.countrycode.value)
			if not name:
				self.caller = _("UNKNOWN")
			else:
				self.caller = name
		notifyCall(self.event, self.date, self.number, self.caller, self.phone, self.connID)
		# kill that object...

class FritzProtocol(LineReceiver):  # pylint: disable=W0223
	def __init__(self):
		info("[FritzProtocol] " + "$Revision: 1481 $"[1:-1] + "$Date: 2017-07-04 10:28:00 +0200 (Tue, 04 Jul 2017) $"[7:23] + " starting")
		global mutedOnConnID
		mutedOnConnID = None
		self.number = '0'
		self.caller = None
		self.phone = None
		self.date = '0'
		self.event = None
		self.connID = None

	def resetValues(self):
		debug("[FritzProtocol]")
		self.number = '0'
		self.caller = None
		self.phone = None
		self.date = '0'
		self.event = None
		self.connID = None

	def notifyAndReset(self):
		notifyCall(self.event, self.date, self.number, self.caller, self.phone, self.connID)
		self.resetValues()

# 	def pauseEnigma2(self):
# 		debug("")
# 		getPage("http://127.0.0.1/web/remotecontrol?command=164").addCallback(self.pauseEnigma2_cb).addErrback(self.pauseEnigma2_eb)
# 
# 	def pauseEnigma2_cb(self, result):
# 		debug(repr(result))
# 
# 	def pauseEnigma2_eb(self, result):
# 		debug(repr(result))

	def lineReceived(self, line):
		debug("[FritzProtocol] %s", line)
# 15.07.06 00:38:54;CALL;1;4;<from/our msn>;<to/extern>;
# 15.07.06 00:38:58;DISCONNECT;1;0;
# 15.07.06 00:39:22;RING;0;<from/extern>;<to/our msn>;
# 15.07.06 00:39:27;DISCONNECT;0;0;
		anEvent = line.split(';')
		(self.date, self.event) = anEvent[0:2]
		self.connID = anEvent[2]

		filtermsns = config.plugins.FritzCall.filtermsn.value.split(",")
		filtermsns = [i.strip() for i in filtermsns]

		if config.plugins.FritzCall.ignoreUnknown.value:
			if self.event == "RING":
				if not anEvent[3]:
					debug("[FritzProtocol] call from unknown phone; skipping")
					return
				elif not anEvent[5]:
					debug("[FritzProtocol] call to unknown phone; skipping")
					return

		# debug("[FritzProtocol] Volcontrol dir: %s" % dir(eDVBVolumecontrol.getInstance()))
		# debug("[FritzCall] unmute on connID: %s?" %self.connID)
		global mutedOnConnID
		if Standby.inStandby is None and not mutedOnConnID:
			info("[FritzCall] check mute")
			if (self.event == "RING" and config.plugins.FritzCall.muteOnCall.value) or (self.event == "CALL" and config.plugins.FritzCall.muteOnOutgoingCall.value):
				info("[FritzCall] mute on connID: %s", self.connID)
				mutedOnConnID = self.connID
				# eDVBVolumecontrol.getInstance().volumeMute() # with this, we get no mute icon...
				if not eDVBVolumecontrol.getInstance().isMuted():
					globalActionMap.actions["volumeMute"]()
				# self.pauseEnigma2()
		if self.event == "DISCONNECT"and (config.plugins.FritzCall.muteOnCall.value or config.plugins.FritzCall.muteOnOutgoingCall.value) and mutedOnConnID == self.connID:
			debug("[FritzCall] unmute on connID: %s!", self.connID)
			mutedOnConnID = None
			# eDVBVolumecontrol.getInstance().volumeUnMute()
			if eDVBVolumecontrol.getInstance().isMuted():
				globalActionMap.actions["volumeMute"]()
				# self.pauseEnigma2()
		# not supported so far, because, taht would mean muting on EVERY connect, regardless of RING or CALL or filter active
		#=======================================================================
		# elif self.event == "CONNECT" and config.plugins.FritzCall.muteOnCall.value == "connect":
		# 	debug("[FritzCall] mute on connID: %s" % self.connID)
		# 	mutedOnConnID = self.connID
		# 	# eDVBVolumecontrol.getInstance().volumeMute() # with this, we get no mute icon...
		# 	if not eDVBVolumecontrol.getInstance().isMuted():
		# 		globalActionMap.actions["volumeMute"]()
		#=======================================================================
		elif self.event == "RING" or (self.event == "CALL" and config.plugins.FritzCall.showOutgoingCalls.value):
			phone = anEvent[4]
			if self.event == "RING":
				number = anEvent[3]
			else:
				number = anEvent[5]

			if fritzbox and fritzbox.blacklist and not config.plugins.FritzCall.showBlacklistedCalls.value:
				if self.event == "RING":
					if number in fritzbox.blacklist[0]:
						info("[FritzProtocol] phone: '''%s''' blacklisted number: '''%s'''", phone, number)
						return
				else:
					if number in fritzbox.blacklist[1]:
						info("[FritzProtocol] phone: '''%s''' blacklisted number: '''%s'''", phone, number)
						return

			info("[FritzProtocol] phone: '''%s''' number: '''%s'''", phone, number)

			if not (config.plugins.FritzCall.filter.value and phone not in filtermsns):
				debug("[FritzProtocol] no filter hit")
				if phone:
					phonename = phonebook.search(phone)  # do we have a name for the number of our side?
					if phonename:
						self.phone = "%s (%s)" % (phone, phonename)
					else:
						self.phone = phone
				else:
					self.phone = _("UNKNOWN")

				if not number:
					debug("[FritzProtocol] no number")
					self.number = _("number suppressed")
					self.caller = _("UNKNOWN")
				else:
					if config.plugins.FritzCall.internal.value and len(number) > 3 and number[0] == "0":
						debug("[FritzProtocol] strip leading 0")
						self.number = number[1:]
					else:
						self.number = number
						if self.event == "CALL" and self.number[0] != '0':  # should only happen for outgoing
							debug("[FritzProtocol] add local prefix")
							self.number = config.plugins.FritzCall.prefix.value + self.number

					# strip CbC prefixes
					if self.event == "CALL":
						number = stripCbCPrefix(self.number, config.plugins.FritzCall.countrycode.value)

					info("[FritzProtocol] phonebook.search: %s", self.number)
					self.caller = phonebook.search(self.number)
					info("[FritzProtocol] phonebook.search result: %s", self.caller)

					if not self.caller:
						if config.plugins.FritzCall.lookup.value:
							FritzReverseLookupAndNotifier(self.event, self.number, self.caller, self.phone, self.date, self.connID)
							return  # reverselookup is supposed to handle the message itself
						else:
							self.caller = _("UNKNOWN")

				self.notifyAndReset()

class FritzClientFactory(ReconnectingClientFactory):
	initialDelay = 20
	maxDelay = 30

	def __init__(self):
		self.hangup_ok = False

	def startedConnecting(self, connector):  # @UnusedVariable # pylint: disable=W0613
		#=======================================================================
		# if not config.plugins.FritzCall.fwVersion.value:
		# 	Notifications.AddNotification(MessageBox, _("FRITZ!Box firmware version not configured! Please set it in the configuration."), type=MessageBox.TYPE_INFO, timeout=0)
		#=======================================================================

		if config.plugins.FritzCall.connectionVerbose.value:
			info("[FRITZ!FritzClientFactory]")
			Notifications.AddNotification(MessageBox, _("Connecting to FRITZ!Box..."), type = MessageBox.TYPE_INFO, timeout = 2)

	def buildProtocol(self, addr):  # @UnusedVariable # pylint: disable=W0613
		global fritzbox
		if config.plugins.FritzCall.connectionVerbose.value:
			info("[FRITZ!FritzClientFactory]")
			Notifications.AddNotification(MessageBox, _("Connected to FRITZ!Box!"), type = MessageBox.TYPE_INFO, timeout = 4)
		self.resetDelay()
		# initDebug()
		initCbC()
		initAvon()

		try:
			decode(config.plugins.FritzCall.password.value)
		except binascii.Error:
			Notifications.AddNotification(MessageBox, _("There might be a problem with your FritzCall %spassword.\nCheck in the configuration.") % "", type = MessageBox.TYPE_WARNING)
			config.plugins.FritzCall.password.value = encode(config.plugins.FritzCall.password.value)
			config.plugins.FritzCall.password.save()
		try:
			decode(config.plugins.FritzCall.guestPassword.value)
		except binascii.Error:
			Notifications.AddNotification(MessageBox, _("There might be a problem with your FritzCall %spassword.\nCheck in the configuration.") % _("guest "), type = MessageBox.TYPE_WARNING)
			config.plugins.FritzCall.guestPassword.value = encode(config.plugins.FritzCall.guestPassword.value)
			config.plugins.FritzCall.guestPassword.save()

		if not config.plugins.FritzCall.fwVersion.value:
			Notifications.AddNotification(MessageBox, _("To enjoy more functionalities of your FRITZ!Box, configure the firmware version!"), type = MessageBox.TYPE_INFO, timeout = 4)
			fritzbox = FritzCallFBF.FritzCallFBF_dummy()
			config.plugins.FritzCall.fritzphonebook.value = False
		elif config.plugins.FritzCall.fwVersion.value == "old":
			fritzbox = FritzCallFBF.FritzCallFBF()
		elif config.plugins.FritzCall.fwVersion.value == "05.27":
			fritzbox = FritzCallFBF.FritzCallFBF_05_27()
		elif config.plugins.FritzCall.fwVersion.value == "05.50":
			fritzbox = FritzCallFBF.FritzCallFBF_05_50()
		elif config.plugins.FritzCall.fwVersion.value == "06.35":
# 			fritzbox = FritzCallFBF.FritzCallFBF_06_35()
# 		elif config.plugins.FritzCall.fwVersion.value == "upnp":
			fritzbox = FritzCallFBF.FritzCallFBF_upnp()
		else:
			fritzbox = None
			Notifications.AddNotification(MessageBox, _("FRITZ!Box firmware version not configured! Please set it in the configuration."), type = MessageBox.TYPE_INFO, timeout = 0)
		phonebook.reload()
		return FritzProtocol()

	def clientConnectionLost(self, connector, reason):
		global fritzbox
		if not self.hangup_ok and config.plugins.FritzCall.connectionVerbose.value:
			warn("[FRITZ!FritzClientFactory] - clientConnectionLost")
			Notifications.AddNotification(MessageBox, _("Connection to FRITZ!Box! lost\n (%s)\nretrying...") % reason.getErrorMessage(), type = MessageBox.TYPE_INFO, timeout = config.plugins.FritzCall.timeout.value)
		ReconnectingClientFactory.clientConnectionLost(self, connector, reason)
		fritzbox = None

	def clientConnectionFailed(self, connector, reason):
		global fritzbox
		if config.plugins.FritzCall.connectionVerbose.value:
			Notifications.AddNotification(MessageBox, _("Connecting to FRITZ!Box failed\n (%s)\nretrying...") % reason.getErrorMessage(), type = MessageBox.TYPE_INFO, timeout = config.plugins.FritzCall.timeout.value)
		ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)
		fritzbox = None

class FritzCall(object):
	def __init__(self):
		self.dialog = None
		self.desc = None
		if config.plugins.FritzCall.enable.value:
			self.connect()

	def connect(self):
		self.abort()
		if config.plugins.FritzCall.enable.value:
			fact = FritzClientFactory()
			self.desc = (fact, reactor.connectTCP(config.plugins.FritzCall.hostname.value, 1012, fact))  # @UndefinedVariable # pylint: disable=E1101

	def shutdown(self):
		self.abort()

	def abort(self):
		if self.desc is not None:
			self.desc[0].hangup_ok = True
			self.desc[0].stopTrying()
			self.desc[1].disconnect()
			self.desc = None

def displayCalls(session, servicelist = None):  # @UnusedVariable # pylint: disable=W0613
	if config.plugins.FritzCall.enable.value:
		if fritzbox and config.plugins.FritzCall.fwVersion.value:
			session.open(FritzDisplayCalls)
		else:
			Notifications.AddNotification(MessageBox, _("Cannot get calls from FRITZ!Box"), type = MessageBox.TYPE_INFO)
	else:
		Notifications.AddNotification(MessageBox, _("Plugin not enabled"), type = MessageBox.TYPE_INFO)

def displayPhonebook(session, servicelist = None):  # @UnusedVariable # pylint: disable=W0613
	if phonebook:
		if config.plugins.FritzCall.enable.value:
			session.open(phonebook.FritzDisplayPhonebook)
		else:
			Notifications.AddNotification(MessageBox, _("Plugin not enabled"), type = MessageBox.TYPE_INFO)
	else:
		Notifications.AddNotification(MessageBox, _("No phonebook"), type = MessageBox.TYPE_INFO)

def displayFBFStatus(session, servicelist = None):  # @UnusedVariable # pylint: disable=W0613
	if config.plugins.FritzCall.enable.value:
		if fritzbox and fritzbox.information:
			session.open(FritzMenu)
		else:
			Notifications.AddNotification(MessageBox, _("Cannot get infos from FRITZ!Box yet\nStill initialising or wrong firmware version"), type = MessageBox.TYPE_INFO)
	else:
		Notifications.AddNotification(MessageBox, _("Plugin not enabled"), type = MessageBox.TYPE_INFO)

def main(session, **kwargs):  # @UnusedVariable  pylint: disable=W0613
	session.open(FritzCallSetup)

fritz_call = None

def autostart(reason, **kwargs):
	global fritz_call

	# ouch, this is a hack
	if "session" in kwargs:
		global my_global_session
		my_global_session = kwargs["session"]
		return

	info("[FRITZ!Call]")
	if reason == 0:
		if not fritz_call:
			fritz_call = FritzCall()
	elif reason == 1:
		fritz_call.shutdown()
		fritz_call = None

def Plugins(**kwargs):  # @UnusedVariable # pylint: disable=W0613,C0103
	what = _("Display FRITZ!box-Fon calls on screen")
	what_calls = _("Phone calls")
	what_phonebook = _("Phonebook")
	what_status = _("FRITZ!Box Fon Status")
	return [PluginDescriptor(name = "FritzCall", description = what, where = PluginDescriptor.WHERE_PLUGINMENU, icon = "plugin.png", fnc = main),
		PluginDescriptor(name = what_calls, description = what_calls, where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc = displayCalls),
		PluginDescriptor(name = what_phonebook, description = what_phonebook, where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc = displayPhonebook),
		PluginDescriptor(name = what_status, description = what_status, where = PluginDescriptor.WHERE_EXTENSIONSMENU, fnc = displayFBFStatus),
		PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc = autostart)]
