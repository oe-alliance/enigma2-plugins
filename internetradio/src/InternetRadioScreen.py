#
# InternetRadio E2
#
# Coded by Dr.Best (c) 2012
# Support: www.dreambox-tools.info
# E-Mail: dr.best@dreambox-tools.info
#
# This plugin is open source but it is NOT free software.
#
# This plugin may only be distributed to and executed on hardware which
# is licensed by Dream Multimedia GmbH.
# In other words:
# It's NOT allowed to distribute any parts of this plugin or its source code in ANY way
# to hardware which is NOT licensed by Dream Multimedia GmbH.
# It's NOT allowed to execute this plugin and its source code or even parts of it in ANY way
# on hardware which is NOT licensed by Dream Multimedia GmbH.
#
# If you want to use or modify the code or parts of it,
# you have to keep MY license and inform me about the modifications by mail.
#

from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.config import config
from enigma import getDesktop, eTimer, eConsoleAppContainer, eActionMap, eMusicPlayer
from Screens.MessageBox import MessageBox
from Components.Sources.StaticText import StaticText
from urllib import quote
from twisted.web.client import downloadPage
from Screens.ChoiceBox import ChoiceBox
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Components.Input import Input
from Screens.InputBox import InputBox
from timer import TimerEntry
from Components.ProgressBar import ProgressBar
from Components.SystemInfo import SystemInfo
import os
import string
import xml.etree.cElementTree
from Tools.BoundFunction import boundFunction

from InternetRadioFavoriteConfig import InternetRadioFavoriteConfig
from InternetRadioInformationScreen import InternetRadioInformationScreen
from InternetRadioOledDisplay import InternetRadioOledDisplay
from InternetRadioSetup import InternetRadioSetup
from InternetRadioCover import InternetRadioCover
from InternetRadioList import InternetRadioList
from InternetRadioWebFunctions import sendUrlCommand
from InternetRadioClasses import InternetRadioFilter, InternetRadioStation
from InternetRadioVisualization import InternetRadioVisualization
from InternetRadioPiPTVPlayer import InternetRadioPiPTVPlayer

# for localized messages
from . import _


containerStreamripper = None

class InternetRadioScreen(Screen, InternetRadioVisualization, InternetRadioPiPTVPlayer):

	FILTERLIST = 0
	STATIONLIST = 1
	FAVORITELIST = 2
	SEARCHLIST = 3
	STREAMRIPPER_BIN = '/usr/bin/streamripper'
	
	sz_w = getDesktop(0).size().width()
	if sz_w == 1280:
		# helper for skinning ;)
#		count = 16
#		skincontent = ""
#		skincontent2 = ""
#		posx = 830
#		x = 0
#		while True:
#			skincontent += "<widget name=\"progress_%d\" zPosition=\"3\" position=\"%d,470\" size=\"25,200\" transparent=\"1\" orientation=\"orBottomToTop\" pixmap=\"/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png\" />\n" % (x,posx)
#			skincontent2 += "<widget name=\"top_%d\" position=\"%d,465\" zPosition=\"6\" size=\"25,5\" transparent=\"1\" pixmap=\"/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png\" />\n" % (x,posx)

#			posx += 25
#			x += 1
#			if x == count:
#				break

		skin = """
			<screen name="InternetRadioScreen" position="0,0" size="1280,720" flags="wfNoBorder" backgroundColor="#00000000" title="InternetRadio">
				<widget transparent="1" name="video" position="0,0" size="1280,720" zPosition="9"/>
				<ePixmap position="50,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
				<ePixmap position="200,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
				<ePixmap position="350,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
				<ePixmap position="500,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
				<widget render="Label" source="key_red" position="50,30" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget render="Label" source="key_green" position="200,30" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget render="Label" source="key_yellow" position="350,30" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget render="Label" source="key_blue" position="500,30" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="headertext" position="50,77" zPosition="1" size="1180,23" font="Regular;20" transparent="1"  foregroundColor="#fcc000" backgroundColor="#00000000"/>
				<widget name="list" position="50,110" zPosition="2" size="1180,340" scrollbarMode="showOnDemand" transparent="0"  backgroundColor="#00000000"/>
				<widget name="statustext" position="50,470" zPosition="1" size="1240,18" font="Regular;16" transparent="0"  backgroundColor="#00000000"/>
				<widget name="cover" zPosition="2" position="50,490" size="51,55" />
				<eLabel name="stationCap" position="50,550" size="85,20" text="Station:" font="Regular;18" transparent="1"  zPosition="1" backgroundColor="#00000000"/>
				<widget name="station" position="125,550" zPosition="1" size="825,20" font="Regular;18" transparent="1"  backgroundColor="#00000000"/>
				<eLabel name="titleCap" position="50,575" size="65,20" text="Title:" font="Regular;18" transparent="1"  zPosition="1" backgroundColor="#00000000"/>
				<widget name="title" position="105,575" zPosition="1" size="720,40" font="Regular;18" transparent="1"  backgroundColor="#00000000"/>
				<widget name="console" position="50,620" zPosition="1" size="900,50" font="Regular;18" transparent="1"  backgroundColor="#00000000"/>
				<widget name="progress_0" zPosition="3" position="830,470" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_1" zPosition="3" position="855,470" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_2" zPosition="3" position="880,470" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_3" zPosition="3" position="905,470" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_4" zPosition="3" position="930,470" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_5" zPosition="3" position="955,470" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_6" zPosition="3" position="980,470" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_7" zPosition="3" position="1005,470" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_8" zPosition="3" position="1030,470" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_9" zPosition="3" position="1055,470" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_10" zPosition="3" position="1080,470" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_11" zPosition="3" position="1105,470" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_12" zPosition="3" position="1130,470" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_13" zPosition="3" position="1155,470" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_14" zPosition="3" position="1180,470" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_15" zPosition="3" position="1205,470" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="top_0" position="830,465" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_1" position="855,465" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_2" position="880,465" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_3" position="905,465" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_4" position="930,465" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_5" position="955,465" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_6" position="980,465" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_7" position="1005,465" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_8" position="1030,465" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_9" position="1055,465" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_10" position="1080,465" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_11" position="1105,465" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_12" position="1130,465" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_13" position="1155,465" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_14" position="1180,465" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_15" position="1205,465" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
			</screen>"""

	elif sz_w == 1024:
		skin = """
			<screen name="InternetRadioScreen" position="0,0" size="1024,576" flags="wfNoBorder" backgroundColor="#00000000" title="InternetRadio">
				<widget transparent="1" name="video" position="0,0" size="1024,576" zPosition="9"/>
				<ePixmap position="50,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
				<ePixmap position="200,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
				<ePixmap position="350,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
				<ePixmap position="500,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
				<widget render="Label" source="key_red" position="50,30" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget render="Label" source="key_green" position="200,30" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget render="Label" source="key_yellow" position="350,30" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget render="Label" source="key_blue" position="500,30" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="headertext" position="50,77" zPosition="1" size="900,23" font="Regular;20" transparent="1"  foregroundColor="#fcc000" backgroundColor="#00000000"/>
				<widget name="list" position="50,120" zPosition="2" size="940,249" scrollbarMode="showOnDemand" transparent="0"  backgroundColor="#00000000"/>
				<widget name="statustext" position="50,370" zPosition="1" size="940,20" font="Regular;16" transparent="0"  backgroundColor="#00000000"/>
				<widget name="title" position="50,400" zPosition="1" size="825,40" font="Regular;18" transparent="1"  backgroundColor="#00000000"/>
				<widget name="station" position="50,445" zPosition="1" size="825,40" font="Regular;18" transparent="1"  backgroundColor="#00000000"/>
				<widget name="console" position="50,490" zPosition="1" size="850,50" font="Regular;18" transparent="1"  backgroundColor="#00000000"/>
				<widget name="progress_0" zPosition="3" position="810,440" size="10,100" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small-fs8.png" />
				<widget name="progress_1" zPosition="3" position="820,440" size="10,100" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small-fs8.png" />
				<widget name="progress_2" zPosition="3" position="830,440" size="10,100" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small-fs8.png" />
				<widget name="progress_3" zPosition="3" position="840,440" size="10,100" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small-fs8.png" />
				<widget name="progress_4" zPosition="3" position="850,440" size="10,100" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small-fs8.png" />
				<widget name="progress_5" zPosition="3" position="860,440" size="10,100" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small-fs8.png" />
				<widget name="progress_6" zPosition="3" position="870,440" size="10,100" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small-fs8.png" />
				<widget name="progress_7" zPosition="3" position="880,440" size="10,100" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small-fs8.png" />
				<widget name="progress_8" zPosition="3" position="890,440" size="10,100" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small-fs8.png" />
				<widget name="progress_9" zPosition="3" position="900,440" size="10,100" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small-fs8.png" />
				<widget name="progress_10" zPosition="3" position="910,440" size="10,100" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small-fs8.png" />
				<widget name="progress_11" zPosition="3" position="920,440" size="10,100" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small-fs8.png" />
				<widget name="progress_12" zPosition="3" position="930,440" size="10,100" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small-fs8.png" />
				<widget name="progress_13" zPosition="3" position="940,440" size="10,100" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small-fs8.png" />
				<widget name="progress_14" zPosition="3" position="950,440" size="10,100" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small-fs8.png" />
				<widget name="progress_15" zPosition="3" position="960,440" size="10,100" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small-fs8.png" />
				<widget name="top_0" position="810,440" zPosition="6" size="10,3" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small_top-fs8.png" />
				<widget name="top_1" position="820,440" zPosition="6" size="10,3" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small_top-fs8.png" />
				<widget name="top_2" position="830,440" zPosition="6" size="10,3" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small_top-fs8.png" />
				<widget name="top_3" position="840,440" zPosition="6" size="10,3" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small_top-fs8.png" />
				<widget name="top_4" position="850,440" zPosition="6" size="10,3" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small_top-fs8.png" />
				<widget name="top_5" position="860,440" zPosition="6" size="10,3" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small_top-fs8.png" />
				<widget name="top_6" position="870,440" zPosition="6" size="10,3" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small_top-fs8.png" />
				<widget name="top_7" position="880,440" zPosition="6" size="10,3" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small_top-fs8.png" />
				<widget name="top_8" position="890,440" zPosition="6" size="10,3" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small_top-fs8.png" />
				<widget name="top_9" position="900,440" zPosition="6" size="10,3" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small_top-fs8.png" />
				<widget name="top_10" position="910,440" zPosition="6" size="10,3" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small_top-fs8.png" />
				<widget name="top_11" position="920,440" zPosition="6" size="10,3" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small_top-fs8.png" />
				<widget name="top_12" position="930,440" zPosition="6" size="10,3" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small_top-fs8.png" />
				<widget name="top_13" position="940,440" zPosition="6" size="10,3" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small_top-fs8.png" />
				<widget name="top_14" position="950,440" zPosition="6" size="10,3" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small_top-fs8.png" />
				<widget name="top_15" position="960,440" zPosition="6" size="10,3" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small_top-fs8.png" />
			</screen>"""
	else:
		skin = """
			<screen name="InternetRadioScreen" position="0,0" size="720,576" flags="wfNoBorder" backgroundColor="#00000000" title="InternetRadio">
				<widget transparent="1" name="video" position="0,0" size="720,576" zPosition="9"/>
				<ePixmap position="50,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/red.png" transparent="1" alphatest="on" />
				<ePixmap position="210,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/green.png" transparent="1" alphatest="on" />
				<ePixmap position="370,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/yellow.png" transparent="1" alphatest="on" />
				<ePixmap position="530,30" zPosition="4" size="140,40" pixmap="skin_default/buttons/blue.png" transparent="1" alphatest="on" />
				<widget render="Label" source="key_red" position="50,30" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget render="Label" source="key_green" position="210,30" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget render="Label" source="key_yellow" position="370,30" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget render="Label" source="key_blue" position="530,30" size="140,40" zPosition="5" valign="center" halign="center" backgroundColor="red" font="Regular;21" transparent="1" foregroundColor="white" shadowColor="black" shadowOffset="-1,-1" />
				<widget name="headertext" position="50,77" zPosition="1" size="620,23" font="Regular;20" transparent="1"  foregroundColor="#fcc000" backgroundColor="#00000000"/>
				<widget name="list" position="50,120" zPosition="2" size="620,249" scrollbarMode="showOnDemand" transparent="0"  backgroundColor="#00000000"/>
				<widget name="statustext" position="50,370" zPosition="1" size="620,20" font="Regular;16" transparent="0"  backgroundColor="#00000000"/>
				<widget name="title" position="50,400" zPosition="1" size="525,40" font="Regular;18" transparent="1"  backgroundColor="#00000000"/>
				<widget name="station" position="50,445" zPosition="1" size="525,40" font="Regular;18" transparent="1"  backgroundColor="#00000000"/>
				<widget name="console" position="50,490" zPosition="1" size="450,50" font="Regular;18" transparent="1"  backgroundColor="#00000000"/>
				<widget name="progress_0" zPosition="3" position="510,440" size="10,100" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small-fs8.png" />
				<widget name="progress_1" zPosition="3" position="520,440" size="10,100" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small-fs8.png" />
				<widget name="progress_2" zPosition="3" position="530,440" size="10,100" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small-fs8.png" />
				<widget name="progress_3" zPosition="3" position="540,440" size="10,100" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small-fs8.png" />
				<widget name="progress_4" zPosition="3" position="550,440" size="10,100" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small-fs8.png" />
				<widget name="progress_5" zPosition="3" position="560,440" size="10,100" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small-fs8.png" />
				<widget name="progress_6" zPosition="3" position="570,440" size="10,100" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small-fs8.png" />
				<widget name="progress_7" zPosition="3" position="580,440" size="10,100" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small-fs8.png" />
				<widget name="progress_8" zPosition="3" position="590,440" size="10,100" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small-fs8.png" />
				<widget name="progress_9" zPosition="3" position="600,440" size="10,100" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small-fs8.png" />
				<widget name="progress_10" zPosition="3" position="610,440" size="10,100" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small-fs8.png" />
				<widget name="progress_11" zPosition="3" position="620,440" size="10,100" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small-fs8.png" />
				<widget name="progress_12" zPosition="3" position="630,440" size="10,100" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small-fs8.png" />
				<widget name="progress_13" zPosition="3" position="640,440" size="10,100" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small-fs8.png" />
				<widget name="progress_14" zPosition="3" position="650,440" size="10,100" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small-fs8.png" />
				<widget name="progress_15" zPosition="3" position="660,440" size="10,100" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small-fs8.png" />
				<widget name="top_0" position="510,440" zPosition="6" size="10,3" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small_top-fs8.png" />
				<widget name="top_1" position="520,440" zPosition="6" size="10,3" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small_top-fs8.png" />
				<widget name="top_2" position="530,440" zPosition="6" size="10,3" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small_top-fs8.png" />
				<widget name="top_3" position="540,440" zPosition="6" size="10,3" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small_top-fs8.png" />
				<widget name="top_4" position="550,440" zPosition="6" size="10,3" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small_top-fs8.png" />
				<widget name="top_5" position="560,440" zPosition="6" size="10,3" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small_top-fs8.png" />
				<widget name="top_6" position="570,440" zPosition="6" size="10,3" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small_top-fs8.png" />
				<widget name="top_7" position="580,440" zPosition="6" size="10,3" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small_top-fs8.png" />
				<widget name="top_8" position="590,440" zPosition="6" size="10,3" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small_top-fs8.png" />
				<widget name="top_9" position="600,440" zPosition="6" size="10,3" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small_top-fs8.png" />
				<widget name="top_10" position="610,440" zPosition="6" size="10,3" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small_top-fs8.png" />
				<widget name="top_11" position="620,440" zPosition="6" size="10,3" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small_top-fs8.png" />
				<widget name="top_12" position="630,440" zPosition="6" size="10,3" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small_top-fs8.png" />
				<widget name="top_13" position="640,440" zPosition="6" size="10,3" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small_top-fs8.png" />
				<widget name="top_14" position="650,440" zPosition="6" size="10,3" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small_top-fs8.png" />
				<widget name="top_15" position="660,440" zPosition="6" size="10,3" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/green_small_top-fs8.png" />
			</screen>"""
	
	def __init__(self, session, url = None, radioStation = None):
		self.session = session
		Screen.__init__(self, session)
		InternetRadioVisualization.__init__(self)
		self.currentService = self.session.nav.getCurrentlyPlayingServiceReference()
		InternetRadioPiPTVPlayer.__init__(self,session, self.currentService, self.setPiPPlayerEnabled)
		self.session.nav.stopService()
		self["cover"] = InternetRadioCover(self.coverLoaded)
		self["key_red"] = StaticText(_("Record"))
		self["key_green"] = StaticText(config.plugins.internetradio.filter.value)
		self["key_yellow"] = StaticText(_("Stations"))
		self["key_blue"] = StaticText(_("Favorites"))

		self.mode = self.FAVORITELIST
		self["list"] = InternetRadioList()
		self["statustext"] = Label()
		self["actions"] = ActionMap(["WizardActions", "ColorActions", "EPGSelectActions"],
		{
			"ok": self.ok_pressed,
			"back": self.close,
			"input_date_time": self.menu_pressed,
			"red": self.red_pressed,
			"green": self.green_pressed,
			"yellow": self.yellow_pressed,
			"blue": self.blue_pressed,
			"info" : self.info_pressed,
			
		}, -1)

		self.stationList = []
		self.stationListIndex = 0

		self.filterList = []
		self.filterListIndex = 0

		self.favoriteList = []
		self.favoriteListIndex = 0

		self.stationListFiltered = []

		
		self.favoriteConfig = InternetRadioFavoriteConfig()
		
		

		self["title"] = Label()
		self["station"] = Label()
		self["headertext"] = Label()
		self["console"] = Label()


		self.stationHeaderText = ""
		self.searchInternetRadioString = ""


		self.currentPlayingStation = None 

		self.onClose.append(self.__onClose)
		self.onLayoutFinish.append(self.startRun)
		self.onExecBegin.append(self.onBeginExec)

		self.musicPlayer = eMusicPlayer(self.BANDS)
		#self.musicPlayer.callback.append(self.musicPlayerCallBack)
		self.musicPlayer.callback.get().append(self.musicPlayerCallBack)

		self.try_url = ""
		self.url_tried = 0
		
		self.stationListURL = "http://www.radio-browser.info/xml.php"
		self.filterSwitch = { _("Countries"):_("Genres"), _("Genres"):_("Countries")}


		self.visuCleanerTimer = eTimer()
		self.visuCleanerTimer.callback.append(self.visuCleanerTimerCallback)

		self.clearStatusTextTimer = eTimer()
		self.clearStatusTextTimer.callback.append(self.clearStatusTextTimerCallback)

		self.fullScreenAutoActivationTimer = eTimer()
		self.fullScreenAutoActivationTimer.callback.append(self.fullScreenAutoActivationTimerCallback)
		
		self.visible = True
		
		self.fullScreen = session.instantiateDialog(InternetRadioFullScreen)
		eActionMap.getInstance().bindAction('', -0x7FFFFFFF, self.autoActivationKeyPressed)

		global containerStreamripper
		if containerStreamripper is None:
			containerStreamripper = eConsoleAppContainer()

		containerStreamripper.dataAvail.append(self.streamripperDataAvail)
		containerStreamripper.appClosed.append(self.streamripperClosed)

		if url is not None and radioStation is not None:
			self.playRadioStation(url, radioStation)
		elif containerStreamripper.running():
			self["key_red"].setText(_("Stop record"))
			# just to hear to recording music when starting the plugin...
			self.currentPlayingStation = InternetRadioStation(name = _("Recording stream station"))
			self.playServiceStream("http://localhost:9191")
	
	def onBeginExec(self):
		if config.plugins.internetradio.visualization.value in ("2", "3"):
			self.summaries.setLabelVisibility(True)			

	def visualizationConfigOnChange(self, configElement = None):
		if config.plugins.internetradio.visualization.value in ("0", "1"):
			self.musicPlayer.setBands(self.BANDS)
			self.summaries.setLabelVisibility(False)
		elif config.plugins.internetradio.visualization.value == "2":
			self.musicPlayer.setBands(self.BANDS)
			self.summaries.setLabelVisibility(True)
		elif config.plugins.internetradio.visualization.value == "3":
			if config.plugins.internetradio.fullscreenlayout.value != "0":
				self.musicPlayer.setBands(0)
			self.summaries.setLabelVisibility(True)
		if config.plugins.internetradio.visualization.value in ("1", "3"):
			self.hideControls()

	def fullscreenlayoutConfigOnChange(self, configElement = None):
		if config.plugins.internetradio.visualization.value == "3" and config.plugins.internetradio.fullscreenlayout.value != "0":
			self.musicPlayer.setBands(0)
		else:
			self.musicPlayer.setBands(self.BANDS)

	def fullscreenautoactivationConfigOnChange(self, configElement = None):
		if config.plugins.internetradio.fullscreenautoactivation.value == "-1":
			self.fullScreenAutoActivationTimer.stop()
		else:
			self.fullScreenAutoActivationTimer.start(int(config.plugins.internetradio.fullscreenautoactivation.value)*1000)

	def autoActivationKeyPressed(self, key = None, flag = None):
		self.fullScreenAutoActivationTimer.stop()
		if  self.shown == True and self.visible == True and config.plugins.internetradio.fullscreenautoactivation.value != "-1":
			self.fullScreenAutoActivationTimer.start(int(config.plugins.internetradio.fullscreenautoactivation.value)*1000)
		return 0

	def fullScreenAutoActivationTimerCallback(self):
		self.fullScreenAutoActivationTimer.stop()
		self.showFullScreen()

	def startRun(self):
		self.setPiPTVPlayerEnabled(False)
		config.plugins.internetradio.visualization.addNotifier(self.visualizationConfigOnChange, initial_call = True)
		config.plugins.internetradio.fullscreenautoactivation.addNotifier(self.fullscreenautoactivationConfigOnChange, initial_call = True)
		config.plugins.internetradio.fullscreenlayout.addNotifier(self.fullscreenlayoutConfigOnChange, initial_call = False)
		self.setPBtoNull()
		self.setProperties()
		self.getFavoriteList()
		self.visuCleanerTimer.start(1000)
		if self.currentPlayingStation is None and config.plugins.internetradio.startupname.value != "" and config.plugins.internetradio.startuptext.value != "":
			self["list"].moveToFavorite(config.plugins.internetradio.startupname.value, config.plugins.internetradio.startuptext.value)
			url = config.plugins.internetradio.startuptext.value
			self.currentPlayingStation = InternetRadioStation(name = config.plugins.internetradio.startupname.value, url = url)
			self.url_tried = 0
			self.try_url = url
			if url.endswith(".pls") or url.endswith(".m3u") or url.endswith(".asx"):
				self.setStatusText(_("Getting streaming data from %s") % url)
				sendUrlCommand(url, None,10).addCallback(self.callbackPlayList).addErrback(self.callbackStationListError)
			else:
				self.playServiceStream(url)

	def info_pressed(self):
		meta = self.musicPlayer.getMetaInfos()
		self.session.open(InternetRadioInformationScreen, meta)

	def showFullScreen(self):
		if self.fullScreen.isVisible() == False:
			self.visible = False
			self.fullScreen.setVisibility(True)
			if config.plugins.internetradio.fullscreenlayout.value in ("0","1"):
				self.fullScreen.setStation(self["station"].getText())
				self.fullScreen.setText(self["title"].getText())
			else:
				self.fullScreen.setStation("")
				self.fullScreen.setText("")
			eActionMap.getInstance().bindAction('', -0x7FFFFFFF, self.fullScreenKeyPressed)
			
	def fullScreenKeyPressed(self, key = None, flag = None):
		if self.fullScreen.isVisible():
			self.visible = True
			self.fullScreen.setVisibility(False)
			eActionMap.getInstance().unbindAction('', self.fullScreenKeyPressed)
			self.autoActivationKeyPressed()
			return 1
		else:
			return 0

	def visuCleanerTimerCallback(self):
		self.visuCleanerTimer.stop()
		if self.needCleanup() == True:
			code = 0
			v = (-80,) * self.BANDS
			self.musicPlayerCallBack(code,v,True)

	def musicPlayerCallBack(self, code = None, v = None, cleanup = False):
		if self.visuCleanerTimer.isActive():
			self.visuCleanerTimer.stop()
		if code == 0 and len(v) > 0:
			if config.plugins.internetradio.visualization.value in ("0","1"):
				self.summaries.setValues(v)
			if self.fullScreen.isVisible() and config.plugins.internetradio.fullscreenlayout.value == "0":
				self.fullScreen.setValues(v)
			if self.visible and config.plugins.internetradio.visualization.value in ("0","2"):
				self.setValues(v)
		elif code == 1:
			cleanup = True
			if (len(v[0]) !=0):
				if len(v[1]) != 0:
					sTitle = "%s - %s" % (v[0],v[1])
				else:
					sTitle = v[0]
				if config.plugins.internetradio.googlecover.value:
					url = "http://images.google.de/images?q=%s&btnG=Bilder-Suche" % quote(sTitle)
					sendUrlCommand(url, None,10).addCallback(self.GoogleImageCallback).addErrback(self.Error)
			else:
				sTitle = "n/a"
			self["title"].setText(sTitle)
			self.summaries.setText(sTitle)
			if self.fullScreen.isVisible() and config.plugins.internetradio.fullscreenlayout.value in ("0", "1"):
				self.fullScreen.setText(sTitle)
		elif code == -2:
			cleanup = True
			if v[0] in (5, 6): # text/uri-list - this can't be decoded.
				self.url_tried += 1
				if self.url_tried == 1:
					self.setStatusText(_("Getting streaming data from\n%s") % self.try_url)
					sendUrlCommand(self.try_url, None,10).addCallback(self.callbackPlayList).addErrback(self.callbackStationListError)
				else:
					self.setStatusText("Error: %s" % v[1], 15000)
					self.currentPlayingStation = None
			else:
				self.setStatusText("Error: %s" % v[1], 15000)
				self.currentPlayingStation = None
		elif code == -5:
			cleanup = True
			if v[0] == 0:
				text = "trying to start %s..." % v[1]
			elif v[0] == 1:
				text = "playing %s..." % v[1]
			elif v[0] == 2:
				text = "%s stopped playing..." % v[1]
			else:
				text = ""
			self.setStatusText(text)
		else:
			if v and len(v) > 2:
				self.setStatusText("Error: %s" % v[1], 15000)
			cleanup = True

		if cleanup == True:
			self.visuCleanerTimer.start(100)

	def streamripperClosed(self, retval):
		if retval == 0:
			self["console"].setText("")
		self["key_red"].setText(_("Record"))

	def streamripperDataAvail(self, data):
		sData = data.replace('\n','')
		self["console"].setText(sData)

	def InputBoxStartRecordingCallback(self, returnValue = None):
		if returnValue:
			recordingLength =  int(returnValue) * 60
			if not os.path.exists(config.plugins.internetradio.dirname.value):
				os.mkdir(config.plugins.internetradio.dirname.value)
			args = []
			args.append(self.currentPlayingStation.url)
			args.append('-d')
			args.append(config.plugins.internetradio.dirname.value)
			args.append('-r')
			args.append('9191')
			if recordingLength != 0:
				args.append('-l')
				args.append("%d" % int(recordingLength))
			if config.plugins.internetradio.riptosinglefile.value:
				args.append('-a')
				args.append('-A')
			if not config.plugins.internetradio.createdirforeachstream.value:
				args.append('-s')
			if config.plugins.internetradio.addsequenceoutputfile.value:
				args.append('-q')
			cmd = [self.STREAMRIPPER_BIN, self.STREAMRIPPER_BIN] + args
			containerStreamripper.execute(*cmd)
			self["key_red"].setText(_("Stop record"))
			
	def deleteRecordingConfirmed(self,val):
		if val:
			containerStreamripper.sendCtrlC()

	def red_pressed(self):
		if containerStreamripper.running():
			self.session.openWithCallback(self.deleteRecordingConfirmed, MessageBox, _("Do you really want to stop the recording?"))
		else:
			if self.currentPlayingStation and len(self.currentPlayingStation.url) != 0:
				self.session.openWithCallback(self.InputBoxStartRecordingCallback, InputBox, windowTitle = _("Recording length"),  title=_("Enter in minutes (0 means unlimited)"), text="0", type=Input.NUMBER)
			else:
				self.session.open(MessageBox, _("Only running streamings can be recorded!"), type = MessageBox.TYPE_INFO,timeout = 20 )

	def green_pressed(self):
		if self.mode != self.FILTERLIST:
			self.mode = self.FILTERLIST
			if len(self.filterList):
				self["headertext"].setText(_("InternetRadio filter list (%s)") % config.plugins.internetradio.filter.value)
				self["list"].setMode(self.mode)
				self["list"].setList(self.filterList)
				self["list"].moveToIndex(self.filterListIndex)
			else:
				self.getFilterList()
		else:
			config.plugins.internetradio.filter.value = self.filterSwitch[config.plugins.internetradio.filter.value]
			config.plugins.internetradio.filter.save()
			self["key_green"].setText(config.plugins.internetradio.filter.value)
			self.getFilterList()

	def yellow_pressed(self):
		if self.mode != self.STATIONLIST:
			if len(self.stationList) and len(self.stationListFiltered):
				self.setStationList()
			else:
				self.stationListIndex = 0
				if config.plugins.internetradio.filter.value == _("Countries"):
					self.getStationList(_("All Countries"))
				else:
					self.getStationList(_("All Genres"))
				
	def blue_pressed(self):
		if self.mode != self.FAVORITELIST:
			self.getFavoriteList(self.favoriteListIndex)

	def getFavoriteList(self, favoriteListIndex = 0):
		self.mode = self.FAVORITELIST
		self["headertext"].setText(_("Favorite list"))
		self["list"].setMode(self.mode)
		favoriteList = self.favoriteConfig.getFavoriteList()
		self["list"].setList(favoriteList)
		if len(favoriteList):
			self["list"].moveToIndex(favoriteListIndex)

	def getFilterList(self):
		self.setStatusText(_("Getting InternetRadio %s list...") % config.plugins.internetradio.filter.value)
		self.stationListIndex = 0
		if len(self.stationList) == 0:
			sendUrlCommand(self.stationListURL, None,10).addCallback(self.callbackFilterList).addErrback(self.callbackFilterListError)
		else:
			self.setFilterList()

	def callbackFilterList(self, xmlstring):
		self.stationList = self.fillStationList(xmlstring)
		self.setFilterList()
		
	def setFilterList(self):
		self["headertext"].setText(_("InternetRadio filter list (%s)") % config.plugins.internetradio.filter.value)
		self.filterListIndex = 0
		self.mode = self.FILTERLIST
		self["list"].setMode(self.mode)
		if config.plugins.internetradio.filter.value == _("Countries"):
			self.filterList  = self.fillCountryList()
		else:
			self.filterList  = self.fillGenreList()
		self["list"].setList(self.filterList)
		if len(self.filterList):
			self["list"].moveToIndex(self.filterListIndex)

	def callbackFilterListError(self, error = None):
		if error is not None:
			try:
				self.setStatusText(_("%s...") % str(error.getErrorMessage()), 15000)
			except: pass
			
	def fillGenreList(self):
		genreList = []
		genres = {} # stupid helper... FIXME!
		for items in self.stationList:
			for genre in items.tags.split(","):
				genre = genre.strip().lower()
				if not genres.has_key(genre):
					genres[genre] = 0 # FIXME 
					genreList.append(((InternetRadioFilter(name = genre)),))
		genreList =  sorted(genreList, key=lambda genrelist: genrelist[0].name)
		genreList.insert(0,((InternetRadioFilter(name = _("All Genres"))),))
		return genreList
		
	def fillCountryList(self):
		countryList = []
		countries = {} # stupid helper... FIXME!
		for items in self.stationList:
			country = items.country.lower()
			if not countries.has_key(country):
				countries[country] = 0 # FIXME 
				countryList.append(((InternetRadioFilter(name = items.country)),))
		countryList = sorted(countryList, key=lambda countrylist: countrylist[0].name)
		countryList.insert(0,((InternetRadioFilter(name = _("All Countries"))),))
		return countryList

	def ok_pressed(self):
		if self.visible:
			sel = None
			try:
				sel = self["list"].l.getCurrentSelection()[0]
			except:return
			if sel is None:
				return
			else:
				if self.mode == self.FILTERLIST:
					self.stationListIndex = 0
					self.filterListIndex = self["list"].getCurrentIndex()
					self.getStationList(sel.name)
				elif self.mode in (self.STATIONLIST, self.FAVORITELIST):
					goOn = True
					currentPlayingStation = None
					if self.mode == self.STATIONLIST:
						url = sel.url.rstrip().strip().lower()
						currentPlayingStation = sel
						currentPlayingStation.url = ""
						self.stationListIndex = self["list"].getCurrentIndex()
					else:
						self.favoriteListIndex = self["list"].getCurrentIndex()
						if sel.configItem.type.value == 0:
							url = sel.configItem.text.value
							currentPlayingStation = InternetRadioStation(name = sel.configItem.name.value, tags = sel.configItem.tags.value, country = sel.configItem.country.value, homepage = sel.configItem.homepage.value)
						else:
							goOn = False
							if sel.configItem.type.value in (1,2):
								self.stationListIndex = 0
								self.filterList = []
								if sel.configItem.type.value == 1:
										f = _("Genres")
								else:
										f = _("Countries")
								config.plugins.internetradio.filter.value = f
								config.plugins.internetradio.filter.save()
								self["key_green"].setText(config.plugins.internetradio.filter.value)
								self.mode = self.FILTERLIST
								self.getStationList(sel.configItem.name.value)
					if goOn == True:
						self.playRadioStation(url, currentPlayingStation)
				
				elif self.mode == self.SEARCHLIST and self.searchInternetRadioString != "":
					self.searchInternetRadio(self.searchInternetRadioString)

	def playRadioStation(self, url, radioStation):
		self.stopPlaying()
		self.currentPlayingStation = radioStation
		self.url_tried = 0
		self.try_url = url
		if url.endswith(".pls") or url.endswith(".m3u") or url.endswith(".asx"):
			self.setStatusText(_("Getting streaming data from %s") % url)
			sendUrlCommand(url, None,10).addCallback(self.callbackPlayList).addErrback(self.callbackStationListError)
		else:
			self.playServiceStream(url)
			
	def stopPlaying(self):
		self.musicPlayer.play("")
		self.currentPlayingStation = None 
		self["title"].setText("")
		self["station"].setText("")
		self.summaries.setText("")
		self["cover"].hide()
		self.visuCleanerTimer.start(100)

	def callbackPlayList(self, result):
		found = False
		parts = string.split(result.lower(),"\n")
		if parts[0].startswith("http://"):
					url = parts[0]
					found = True
					self.playServiceStream(url.rstrip().strip())
		elif parts[0].find("[playlist]") != -1:
			for lines in parts:
				if lines.find("file1=") != -1:
					line = string.split(lines,"file1=")
					found = True
					self.playServiceStream(line[-1].rstrip().strip())
					break
		elif parts[0].find("#extm3u") != -1:
			for lines in parts:
				if lines.startswith("http://"):
					found = True
					self.playServiceStream(lines.rstrip().strip())
					break

		elif parts[0].lower().find("asx version") != -1:
			stationList = []
			try:
				root = xml.etree.cElementTree.fromstring(result.lower())
			except: 
				root = None
			if root:
				for childs in root.findall("entry"):
					for childs2 in childs.findall("ref"):
						url = childs2.get("href")
						if len(url):
							found = True
							self.playServiceStream(url.rstrip().strip())
							break
					if found:
						break
		if not found:
			self.currentPlayingStation = None
			self.setStatusText(_("No streaming data found..."), 15000)

	def getStationList(self,filter_string):
		self.stationHeaderText = _("InternetRadio station list for filter: %s") % filter_string
		self["headertext"].setText(self.stationHeaderText)
		self.setStatusText(_("Getting %s") %  self.stationHeaderText)

		if len(self.stationList) == 0:
			self.stationListIndex = 0
			sendUrlCommand(self.stationListURL, None,10).addCallback(boundFunction(self.callbackStationList,filter_string)).addErrback(self.callbackStationListError)
		else:
			self.stationListFiltered = self.getFilteredStationList(filter_string)
			self.setStationList()

	def callbackStationList(self, filter_string, xmlstring):
		self.stationList = self.fillStationList(xmlstring)
		self.stationListFiltered = self.getFilteredStationList(filter_string)
		self.setStationList()
		
	def setStationList(self):
		self.setStatusText("")
		self.mode = self.STATIONLIST
		self["headertext"].setText(self.stationHeaderText)
		self["list"].setMode(self.mode)
		self["list"].setList(self.stationListFiltered)
		if len(self.stationList):
			self["list"].moveToIndex(self.stationListIndex)
		
	def getFilteredStationList(self, filter_string):
		if self.mode == self.SEARCHLIST:
			return [ (x,) for x in self.stationList if ( self.searchInternetRadioString in x.tags.lower() or self.searchInternetRadioString in x.name.lower())]
		else:
			self.searchInternetRadioString = ""
			if filter_string != _("All Genres") and filter_string != _("All Countries"):
				if config.plugins.internetradio.filter.value == _("Countries"):
					return [ (x,) for x in self.stationList if ( filter_string == x.country)]
				else:
					return [ (x,) for x in self.stationList if ( filter_string in x.tags)]
			else:
				return [ (x,) for x in self.stationList]

	def fillStationList(self,xmlstring):
		stationList = []
		try:
			root = xml.etree.cElementTree.fromstring(xmlstring)
		except: return []
		for childs in root.findall("station"):
			stationList.append(InternetRadioStation(name = childs.get("name").encode('utf-8','ignore'), 
								tags = childs.get("tags").encode('utf-8','ignore'), country = childs.get("country").encode('utf-8','ignore'), url = childs.get("url"),
								language = childs.get("language").encode('utf-8','ignore'), id = childs.get("id"), homepage = childs.get("homepage").encode('utf-8','ignore')))
		return sorted(stationList, key=lambda stations: stations.name)
		

	def menu_pressed(self):
		self.fullScreenAutoActivationTimer.stop()
		options = [(_("Config"), self.config),(_("Search"), self.search),]
		if self.mode == self.FAVORITELIST and self.getSelectedItem() is not None:
			options.extend(((_("rename current selected favorite"), self.renameFavorite),))
			options.extend(((_("remove current selected favorite"), self.removeFavorite),))
			if config.plugins.internetradio.startupname.value != "":
				options.extend(((_("do not play a service on startup"), boundFunction(self.startUpStation,False)),))
			if self.getSelectedItem().configItem.type.value == 0:
				options.extend(((_("play current selected favorite on startup"), boundFunction(self.startUpStation,True)),))
		elif self.mode == self.FILTERLIST and self.getSelectedItem() is not None:
			options.extend(((_("Add current selected genre to favorite"), self.addFilterToFavorite),))
		elif self.mode == self.STATIONLIST and self.getSelectedItem() is not None:
			options.extend(((_("Add current selected station to favorite"), self.addStationToFavorite),))
		if self.currentPlayingStation and len(self.currentPlayingStation.url) != 0:
			options.extend(((_("Add current playing stream to favorite"), self.addCurrentStreamToFavorite),))
		options.extend(((_("Fullscreen"), self.showFullScreen),))
		if SystemInfo.get("NumVideoDecoders", 1) > 1:
			options.extend(((_("Show TV"), boundFunction(self.setPiPPlayerEnabled,True)),))
		self.session.openWithCallback(self.menuCallback, ChoiceBox,list = options)

	def menuCallback(self, ret):
		ret and ret[1]()

	def setPiPPlayerEnabled(self, value):
		if value:
			self["actions"].setEnabled(False)
			self.fullScreenAutoActivationTimer.stop()
			self.hide()
			self.visible = False
			self.setPiPTVPlayerEnabled(True)
		else:
			self.currentService = self.currService
			self["actions"].setEnabled(True)
			self.show()
			self.visible = True
			self.autoActivationKeyPressed()			


	def startUpStation(self, add):
		if add == True:
			sel = self.getSelectedItem()
			if sel and sel.configItem.type.value == 0:
				config.plugins.internetradio.startupname.value = sel.configItem.name.value
				config.plugins.internetradio.startuptext.value = sel.configItem.text.value
		else:
			config.plugins.internetradio.startupname.value = ""
			config.plugins.internetradio.startuptext.value = ""
		config.plugins.internetradio.save()

	def addFilterToFavorite(self):
		sel = self.getSelectedItem()
		if sel is not None:
			if config.plugins.internetradio.filter.value == _("Countries"):
				favoritetype = 2
			else:
				favoritetype = 1
			self.favoriteConfig.addFavorite(name = sel.name, text = sel.name, favoritetype = favoritetype, tags = "", country = "", homepage = "")			

	def addStationToFavorite(self):
		sel = self.getSelectedItem()
		if sel is not None:
			self.favoriteConfig.addFavorite(name = sel.name, text = sel.url, favoritetype = 0, tags = sel.genre, country = sel.country, homepage = sel.homepage)			
		
	def addCurrentStreamToFavorite(self):
		self.favoriteConfig.addFavorite(name = self.currentPlayingStation.name, text = self.currentPlayingStation.url, favoritetype = 0, tags =self.currentPlayingStation.tags, country = self.currentPlayingStation.country, homepage = self.currentPlayingStation.homepage)

	def renameFavorite(self):
		sel = self.getSelectedItem()
		if sel is not None:
			self.session.openWithCallback(boundFunction(self.renameFavoriteFinished, sel.configItem), VirtualKeyBoard, title = _("Enter new name for favorite item"), text = sel.configItem.name.value)

	def renameFavoriteFinished(self, configItem, text = None):
		if text:
			self.favoriteConfig.renameFavorite(configItem, text)
			self.favoriteListIndex = self["list"].getCurrentIndex()
			self.getFavoriteList(self.favoriteListIndex)

	def removeFavorite(self):
		sel = self.getSelectedItem()
		if sel is not None:
			self.favoriteConfig.removeFavorite(sel.configItem)
			self.favoriteListIndex = self["list"].getCurrentIndex()
			if self.favoriteListIndex >= 1:
				self.favoriteListIndex -= 1
			self.getFavoriteList(self.favoriteListIndex)

	def search(self):
		self.session.openWithCallback(self.searchInternetRadio, VirtualKeyBoard, title = _("Enter text to search for"))

	def searchInternetRadio(self, searchstring = None):
		if searchstring:
			self.stationHeaderText =  _("InternetRadio station list for search-criteria: %s") % searchstring
			self["headertext"].setText(self.stationHeaderText)
			self.setStatusText(_("Searching InternetRadio for %s...") % searchstring)
			self.mode = self.SEARCHLIST
			self.searchInternetRadioString = searchstring.lower()
			self.stationListIndex = 0
			if len(self.stationList) == 0:
				self.stationListIndex = 0
				sendUrlCommand(self.stationListURL, None,10).addCallback(boundFunction(self.callbackStationList,"")).addErrback(self.callbackStationListError)
			else:
				self.stationListFiltered = self.getFilteredStationList("")
				self.setStationList()

	def config(self):
		self.session.open(InternetRadioSetup)

	def callbackStationListError(self, error = None):
		if error is not None:
			try:
				self.setStatusText(_("%s ...") % str(error.getErrorMessage()), 15000)
			except: pass

	def Error(self, error = None):
		if error is not None:
			try:
				self.setStatusText(str(error.getErrorMessage()), 15000)
			except: pass
	
	def __onClose(self):
		self.session.deleteDialog(self.fullScreen)
		self.fullScreen = None
		eActionMap.getInstance().unbindAction('', self.autoActivationKeyPressed)
		self.session.nav.playService(self.currentService)
		containerStreamripper.dataAvail.remove(self.streamripperDataAvail)
		containerStreamripper.appClosed.remove(self.streamripperClosed)
		# fallback to earlier enigma versions FIXME Delete that when commiting
		try:
			config.plugins.internetradio.visualization.removeNotifier(self.visualizationConfigOnChange)
			config.plugins.internetradio.fullscreenautoactivation.removeNotifier(self.fullscreenautoactivationConfigOnChange)
			config.plugins.internetradio.fullscreenlayout.removeNotifier(self.fullscreenlayoutConfigOnChange)
		
		except:
			config.plugins.internetradio.visualization.notifiers.remove(self.visualizationConfigOnChange)
			config.plugins.internetradio.fullscreenautoactivation.notifiers.remove(self.fullscreenautoactivationConfigOnChange)
			config.plugins.internetradio.fullscreenlayout.notifiers.remove(self.fullscreenlayoutConfigOnChange)

	def GoogleImageCallback(self, result):
		foundPos = result.find("imgres?imgurl=")
		foundPos2 = result.find("&amp;imgrefurl=")
		if foundPos != -1 and foundPos2 != -1:
			print "[InternetRadio] downloading cover from %s " % result[foundPos+14:foundPos2]
			downloadPage(result[foundPos+14:foundPos2] ,"/tmp/.cover").addCallback(self.coverDownloadFinished).addErrback(self.coverDownloadFailed)

	def coverDownloadFailed(self,result):
        	print "[InternetRadio] cover download failed: %s " % result
		self["cover"].hide()

	def coverDownloadFinished(self,result):
		print "[InternetRadio] cover download finished"
		self["cover"].updateIcon("/tmp/.cover")

	def coverLoaded(self):
		self["cover"].show()
		
	def playServiceStream(self, url):
		self.musicPlayer.play(url)
		if self.currentPlayingStation:
			self.currentPlayingStation.url = url
			self["station"].setText(self.currentPlayingStation.name)
		self["title"].setText(_("Title: n/a"))

	def createSummary(self):
		return InternetRadioOledDisplay

	def getSelectedItem(self):
		sel = None
		try:
			sel = self["list"].l.getCurrentSelection()[0]
		except:return None
		return sel
		
	def closePlayer(self):
		self.fullScreenKeyPressed()
		self.close()

	def setStatusText(self, text, cleartimertime = 3000):
		self.clearStatusTextTimer.stop()
		self["statustext"].setText(text)
		self.clearStatusTextTimer.start(cleartimertime)

	def clearStatusTextTimerCallback(self):
		self.clearStatusTextTimer.stop()
		self["statustext"].setText("")

	# used from webinterface
	def updateFullscreenStationName(self, stationname):
		if self.fullScreen.isVisible():
			self.fullScreen.setStation(stationname)

	# used from webinterface
	def getCurrentPlayingStation(self):
		if self.currentPlayingStation and self.currentPlayingStation.url != "":
			return (True, "%s - %s" % (self["station"].getText(), self["title"].getText()))
		else:
			return (False, _("nothing playing..."))
		
	# used from webinterface
	def getStreamingInfos(self):
		return self.musicPlayer.getMetaInfos()

	# used from webinterface
	def updateFavoriteList(self):
		if self.mode == self.FAVORITELIST:
			index = self["list"].getCurrentIndex()
			self.favoriteConfig.loadFavoriteConfig() # reload favorites
			favoriteList = self.favoriteConfig.getFavoriteList()
			self["list"].setList(favoriteList)
			if len(favoriteList):
				self["list"].moveToIndex(index)
		
class InternetRadioFullScreen(Screen, InternetRadioVisualization):

	sz_w = getDesktop(0).size().width()
	if sz_w == 1280:

		skin = """
			<screen name="InternetRadioFullScreen" position="0,0" size="1280,720" flags="wfNoBorder" backgroundColor="#00000000" title="InternetRadio">
				<widget name="station" position="50,120" zPosition="1" size="1180,20" font="Regular;18" transparent="1"  halign="center" foregroundColor="#356835" backgroundColor="#00000000"/>
				<widget name="title" position="50,550" zPosition="1" size="1180,80" font="Regular;22" transparent="1"  halign="center" foregroundColor="#4e9a4e" backgroundColor="#00000000"/>
				<widget name="progress_0" zPosition="3" position="440,240" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_1" zPosition="3" position="465,240" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_2" zPosition="3" position="490,240" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_3" zPosition="3" position="515,240" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_4" zPosition="3" position="540,240" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_5" zPosition="3" position="565,240" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_6" zPosition="3" position="590,240" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_7" zPosition="3" position="615,240" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_8" zPosition="3" position="640,240" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_9" zPosition="3" position="665,240" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_10" zPosition="3" position="690,240" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_11" zPosition="3" position="715,240" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_12" zPosition="3" position="740,240" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_13" zPosition="3" position="765,240" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_14" zPosition="3" position="790,240" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_15" zPosition="3" position="815,240" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="top_0" position="440,235" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_1" position="465,235" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_2" position="490,235" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_3" position="515,235" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_4" position="540,235" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_5" position="565,235" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_6" position="590,235" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_7" position="615,235" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_8" position="640,235" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_9" position="665,235" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_10" position="690,235" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_11" position="715,235" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_12" position="740,235" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_13" position="765,235" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_14" position="790,235" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_15" position="815,235" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
			</screen>"""

	elif sz_w == 1024:
		skin = """
			<screen name="InternetRadioFullScreen" position="0,0" size="1024,576" flags="wfNoBorder" backgroundColor="#00000000" title="InternetRadio">
				<widget name="station" position="50,120" zPosition="1" size="924,20" font="Regular;18" transparent="1"  halign="center" foregroundColor="#356835" backgroundColor="#00000000"/>
				<widget name="title" position="50,400" zPosition="1" size="924,80" font="Regular;22" transparent="1"  halign="center" foregroundColor="#4e9a4e" backgroundColor="#00000000"/>
				<widget name="progress_0" zPosition="3" position="312,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_1" zPosition="3" position="337,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_2" zPosition="3" position="362,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_3" zPosition="3" position="387,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_4" zPosition="3" position="412,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_5" zPosition="3" position="437,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_6" zPosition="3" position="462,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_7" zPosition="3" position="487,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_8" zPosition="3" position="512,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_9" zPosition="3" position="537,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_10" zPosition="3" position="562,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_11" zPosition="3" position="587,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_12" zPosition="3" position="612,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_13" zPosition="3" position="637,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_14" zPosition="3" position="662,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_15" zPosition="3" position="687,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="top_0" position="312,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_1" position="337,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_2" position="362,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_3" position="387,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_4" position="412,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_5" position="437,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_6" position="462,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_7" position="487,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_8" position="512,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_9" position="537,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_10" position="562,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_11" position="587,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_12" position="612,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_13" position="637,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_14" position="662,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_15" position="687,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
			</screen>"""



			
	else:
		skin = """
			<screen name="InternetRadioFullScreen" position="0,0" size="720,576" flags="wfNoBorder" backgroundColor="#00000000" title="InternetRadio">
				<widget name="station" position="50,120" zPosition="1" size="620,20" font="Regular;18" transparent="1"  halign="center" foregroundColor="#356835" backgroundColor="#00000000"/>
				<widget name="title" position="50,400" zPosition="1" size="620,80" font="Regular;22" transparent="1"  halign="center" foregroundColor="#4e9a4e" backgroundColor="#00000000"/>
				<widget name="progress_0" zPosition="3" position="170,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_1" zPosition="3" position="195,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_2" zPosition="3" position="220,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_3" zPosition="3" position="245,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_4" zPosition="3" position="270,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_5" zPosition="3" position="295,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_6" zPosition="3" position="320,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_7" zPosition="3" position="345,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_8" zPosition="3" position="370,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_9" zPosition="3" position="395,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_10" zPosition="3" position="420,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_11" zPosition="3" position="445,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_12" zPosition="3" position="470,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_13" zPosition="3" position="495,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_14" zPosition="3" position="520,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="progress_15" zPosition="3" position="545,138" size="25,200" transparent="1" orientation="orBottomToTop" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green-fs8.png" />
				<widget name="top_0" position="170,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_1" position="195,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_2" position="220,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_3" position="245,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_4" position="270,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_5" position="295,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_6" position="320,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_7" position="345,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_8" position="370,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_9" position="395,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_10" position="420,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_11" position="445,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_12" position="470,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_13" position="495,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_14" position="520,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
				<widget name="top_15" position="545,133" zPosition="6" size="25,5" transparent="1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/InternetRadio/images/bar_green_top-fs8.png" />
			</screen>"""


	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		InternetRadioVisualization.__init__(self)
		self["title"] =  Label("")
		self["station"] = Label("")
		self.onLayoutFinish.append(self.startRun)
		self.visible = False

	def startRun(self):
		self.setProperties()
		self.hideControls()

	def setText(self, title):
		self["title"].setText(title)

	def setStation(self, station):
		self["station"].setText(station)


	def setVisibility(self, visible):
		if visible:
			if config.plugins.internetradio.fullscreenlayout.value != "0":
				self.hideControls()
			self.show()
		else:
			self.hide()
		self.visible = visible

	def isVisible(self):
		return self.visible
