# -*- coding: UTF-8 -*-
# Mosaic by AliAbdul
from Components.ActionMap import NumberActionMap
from Components.config import config, ConfigSubsection, ConfigInteger
from Components.Console import Console
from Components.Label import Label
from Components.Language import language
from Components.Pixmap import Pixmap
from Components.VideoWindow import VideoWindow
from enigma import eServiceCenter, eServiceReference, eTimer, getDesktop, loadPNG
from Plugins.Plugin import PluginDescriptor
from Screens.ChannelSelection import BouquetSelector
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.Directories import resolveFilename, SCOPE_SKIN_IMAGE, SCOPE_LANGUAGE, SCOPE_PLUGINS
from Tools.LoadPixmap import LoadPixmap
import os
import gettext

################################################

grab_binary = "/usr/bin/grab"
grab_picture = "/tmp/mosaic.jpg"
grab_errorlog = "/tmp/mosaic.log"

config_limits = (3, 30)
config.plugins.Mosaic = ConfigSubsection()
config.plugins.Mosaic.countdown = ConfigInteger(default=5, limits=config_limits)

playingIcon = loadPNG(resolveFilename(SCOPE_SKIN_IMAGE, 'skin_default/icons/ico_mp_play.png'))
pausedIcon = loadPNG(resolveFilename(SCOPE_SKIN_IMAGE, 'skin_default/icons/ico_mp_pause.png'))

################################################

PluginLanguageDomain = "Mosaic"
PluginLanguagePath = "Extensions/Mosaic/locale/"

def localeInit():
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))

def _(txt):
	if gettext.dgettext(PluginLanguageDomain, txt):
		return gettext.dgettext(PluginLanguageDomain, txt)
	else:
		print "[" + PluginLanguageDomain + "] fallback to default translation for " + txt
		return gettext.gettext(txt)

language.addCallback(localeInit())

################################################

class Mosaic(Screen):
	PLAY = 0
	PAUSE = 1

	desktop = getDesktop(0)
	size = desktop.size()
	width = size.width()
	height = size.height()
	windowWidth = width / 4
	windowHeight = height / 4

	positions = []
	x = 80
	y = 50
	for i in range(1, 10):
		positions.append([x, y])
		x += windowWidth
		x += ((width - 160) - (windowWidth * 3)) / 2
		if (i == 3) or (i == 6):
			y = y + windowHeight + 20
			x = 80

	skin = ""
	skin += """<screen position="0,0" size="%d,%d" title="Mosaic" flags="wfNoBorder" backgroundColor="#ffffff" >""" % (width, height)
	skin += """<widget name="playState" position="55,55" size="16,16" alphatest="on" />"""
	skin += """<eLabel position="%d,%d" size="%d,%d" />""" % (positions[0][0] - 2, positions[0][1] - 1, windowWidth, windowHeight)
	skin += """<eLabel position="%d,%d" size="%d,%d" />""" % (positions[1][0] - 2, positions[1][1] - 1, windowWidth, windowHeight)
	skin += """<eLabel position="%d,%d" size="%d,%d" />""" % (positions[2][0] - 2, positions[2][1] - 1, windowWidth, windowHeight)
	skin += """<eLabel position="%d,%d" size="%d,%d" />""" % (positions[3][0] - 2, positions[3][1] - 1, windowWidth, windowHeight)
	skin += """<eLabel position="%d,%d" size="%d,%d" />""" % (positions[4][0] - 2, positions[4][1] - 1, windowWidth, windowHeight)
	skin += """<eLabel position="%d,%d" size="%d,%d" />""" % (positions[5][0] - 2, positions[5][1] - 1, windowWidth, windowHeight)
	skin += """<eLabel position="%d,%d" size="%d,%d" />""" % (positions[6][0] - 2, positions[6][1] - 1, windowWidth, windowHeight)
	skin += """<eLabel position="%d,%d" size="%d,%d" />""" % (positions[7][0] - 2, positions[7][1] - 1, windowWidth, windowHeight)
	skin += """<eLabel position="%d,%d" size="%d,%d" />""" % (positions[8][0] - 2, positions[8][1] - 1, windowWidth, windowHeight)
	skin += """<widget name="channel1" position="%d,%d" size="%d,20" font="Regular;18" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (positions[0][0], positions[0][1] - 18, windowWidth - 4)
	skin += """<widget name="channel2" position="%d,%d" size="%d,20" font="Regular;18" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (positions[1][0], positions[1][1] - 18, windowWidth - 4)
	skin += """<widget name="channel3" position="%d,%d" size="%d,20" font="Regular;18" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (positions[2][0], positions[2][1] - 18, windowWidth - 4)
	skin += """<widget name="channel4" position="%d,%d" size="%d,20" font="Regular;18" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (positions[3][0], positions[3][1] - 18, windowWidth - 4)
	skin += """<widget name="channel5" position="%d,%d" size="%d,20" font="Regular;18" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (positions[4][0], positions[4][1] - 18, windowWidth - 4)
	skin += """<widget name="channel6" position="%d,%d" size="%d,20" font="Regular;18" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (positions[5][0], positions[5][1] - 18, windowWidth - 4)
	skin += """<widget name="channel7" position="%d,%d" size="%d,20" font="Regular;18" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (positions[6][0], positions[6][1] - 18, windowWidth - 4)
	skin += """<widget name="channel8" position="%d,%d" size="%d,20" font="Regular;18" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (positions[7][0], positions[7][1] - 18, windowWidth - 4)
	skin += """<widget name="channel9" position="%d,%d" size="%d,20" font="Regular;18" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (positions[8][0], positions[8][1] - 18, windowWidth - 4)
	skin += """<widget name="window1" position="%d,%d" zPosition="1" size="%d,%d" />""" % (positions[0][0] - 2, positions[0][1] - 1, windowWidth, windowHeight)
	skin += """<widget name="window2" position="%d,%d" zPosition="1" size="%d,%d" />""" % (positions[1][0] - 2, positions[1][1] - 1, windowWidth, windowHeight)
	skin += """<widget name="window3" position="%d,%d" zPosition="1" size="%d,%d" />""" % (positions[2][0] - 2, positions[2][1] - 1, windowWidth, windowHeight)
	skin += """<widget name="window4" position="%d,%d" zPosition="1" size="%d,%d" />""" % (positions[3][0] - 2, positions[3][1] - 1, windowWidth, windowHeight)
	skin += """<widget name="window5" position="%d,%d" zPosition="1" size="%d,%d" />""" % (positions[4][0] - 2, positions[4][1] - 1, windowWidth, windowHeight)
	skin += """<widget name="window6" position="%d,%d" zPosition="1" size="%d,%d" />""" % (positions[5][0] - 2, positions[5][1] - 1, windowWidth, windowHeight)
	skin += """<widget name="window7" position="%d,%d" zPosition="1" size="%d,%d" />""" % (positions[6][0] - 2, positions[6][1] - 1, windowWidth, windowHeight)
	skin += """<widget name="window8" position="%d,%d" zPosition="1" size="%d,%d" />""" % (positions[7][0] - 2, positions[7][1] - 1, windowWidth, windowHeight)
	skin += """<widget name="window9" position="%d,%d" zPosition="1" size="%d,%d" />""" % (positions[8][0] - 2, positions[8][1] - 1, windowWidth, windowHeight)
	skin += """<widget name="video1" position="%d,%d" zPosition="2" size="%d,%d" backgroundColor="#ffffffff" />""" % (positions[0][0] - 2, positions[0][1] - 1, windowWidth, windowHeight)
	skin += """<widget name="video2" position="%d,%d" zPosition="2" size="%d,%d" backgroundColor="#ffffffff" />""" % (positions[1][0] - 2, positions[1][1] - 1, windowWidth, windowHeight)
	skin += """<widget name="video3" position="%d,%d" zPosition="2" size="%d,%d" backgroundColor="#ffffffff" />""" % (positions[2][0] - 2, positions[2][1] - 1, windowWidth, windowHeight)
	skin += """<widget name="video4" position="%d,%d" zPosition="2" size="%d,%d" backgroundColor="#ffffffff" />""" % (positions[3][0] - 2, positions[3][1] - 1, windowWidth, windowHeight)
	skin += """<widget name="video5" position="%d,%d" zPosition="2" size="%d,%d" backgroundColor="#ffffffff" />""" % (positions[4][0] - 2, positions[4][1] - 1, windowWidth, windowHeight)
	skin += """<widget name="video6" position="%d,%d" zPosition="2" size="%d,%d" backgroundColor="#ffffffff" />""" % (positions[5][0] - 2, positions[5][1] - 1, windowWidth, windowHeight)
	skin += """<widget name="video7" position="%d,%d" zPosition="2" size="%d,%d" backgroundColor="#ffffffff" />""" % (positions[6][0] - 2, positions[6][1] - 1, windowWidth, windowHeight)
	skin += """<widget name="video8" position="%d,%d" zPosition="2" size="%d,%d" backgroundColor="#ffffffff" />""" % (positions[7][0] - 2, positions[7][1] - 1, windowWidth, windowHeight)
	skin += """<widget name="video9" position="%d,%d" zPosition="2" size="%d,%d" backgroundColor="#ffffffff" />""" % (positions[8][0] - 2, positions[8][1] - 1, windowWidth, windowHeight)
	skin += """<widget name="event1" position="%d,%d" size="%d,20" zPosition="3" font="Regular;18" backgroundColor="#000000" foregroundColor="#ffffff" />""" % (positions[0][0] - 2, positions[0][1] - 1, windowWidth)
	skin += """<widget name="event2" position="%d,%d" size="%d,20" zPosition="3" font="Regular;18" backgroundColor="#000000" foregroundColor="#ffffff" />""" % (positions[1][0] - 2, positions[1][1] - 1, windowWidth)
	skin += """<widget name="event3" position="%d,%d" size="%d,20" zPosition="3" font="Regular;18" backgroundColor="#000000" foregroundColor="#ffffff" />""" % (positions[2][0] - 2, positions[2][1] - 1, windowWidth)
	skin += """<widget name="event4" position="%d,%d" size="%d,20" zPosition="3" font="Regular;18" backgroundColor="#000000" foregroundColor="#ffffff" />""" % (positions[3][0] - 2, positions[3][1] - 1, windowWidth)
	skin += """<widget name="event5" position="%d,%d" size="%d,20" zPosition="3" font="Regular;18" backgroundColor="#000000" foregroundColor="#ffffff" />""" % (positions[4][0] - 2, positions[4][1] - 1, windowWidth)
	skin += """<widget name="event6" position="%d,%d" size="%d,20" zPosition="3" font="Regular;18" backgroundColor="#000000" foregroundColor="#ffffff" />""" % (positions[5][0] - 2, positions[5][1] - 1, windowWidth)
	skin += """<widget name="event7" position="%d,%d" size="%d,20" zPosition="3" font="Regular;18" backgroundColor="#000000" foregroundColor="#ffffff" />""" % (positions[6][0] - 2, positions[6][1] - 1, windowWidth)
	skin += """<widget name="event8" position="%d,%d" size="%d,20" zPosition="3" font="Regular;18" backgroundColor="#000000" foregroundColor="#ffffff" />""" % (positions[7][0] - 2, positions[7][1] - 1, windowWidth)
	skin += """<widget name="event9" position="%d,%d" size="%d,20" zPosition="3" font="Regular;18" backgroundColor="#000000" foregroundColor="#ffffff" />""" % (positions[8][0] - 2, positions[8][1] - 1, windowWidth)

	skin += """<widget name="countdown" position="80,%d" size="%d,20" font="Regular;18" backgroundColor="#ffffff" foregroundColor="#000000" />""" % (height - 50, windowWidth)
	skin += """<widget name="count" position="%d,%d" size="%d,20" font="Regular;18" backgroundColor="#ffffff" foregroundColor="#000000" halign="right" />
	</screen>""" % (positions[2][0], height - 50, windowWidth)

	def __init__(self, session, services):
		Screen.__init__(self, session)

		self.session = session
		self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
		self.consoleCmd = ""
		self.Console = Console()
		self.serviceHandler = eServiceCenter.getInstance()
		self.ref_list = services
		self.window_refs = [None, None, None, None, None, None, None, None, None]
		self.current_refidx = 0
		self.current_window = 1
		self.countdown = config.plugins.Mosaic.countdown.value
		self.working = False
		self.state = self.PLAY

		self["playState"] = Pixmap()
		for i in range(1, 10):
			self["window" + str(i)] = Pixmap()
			self["video" + str(i)] = VideoWindow(decoder=0, fb_width=self.width, fb_height=self.height)
			self["video" + str(i)].hide()
			self["channel" + str(i)] = Label("")
			self["event" + str(i)] = Label("")
			self["event" + str(i)].hide()
		self["video1"].decoder = 0
		self["video1"].show()
		self["countdown"] = Label()
		self.updateCountdownLabel()
		self["count"] = Label()

		self["actions"] = NumberActionMap(["MosaicActions"],
			{
				"ok": self.exit,
				"cancel": self.closeWithOldService,
				"green": self.play,
				"yellow": self.pause,
				"channelup": self.countdownPlus,
				"channeldown": self.countdownMinus,
				"1": self.numberPressed,
				"2": self.numberPressed,
				"3": self.numberPressed,
				"4": self.numberPressed,
				"5": self.numberPressed,
				"6": self.numberPressed,
				"7": self.numberPressed,
				"8": self.numberPressed,
				"9": self.numberPressed
			}, prio=-1)

		self.updateTimer = eTimer()
		self.updateTimer.callback.append(self.updateCountdown)
		self.checkTimer = eTimer()
		self.checkTimer.callback.append(self.checkGrab)
		self.checkTimer.start(500, 1)

	def checkGrab(self):
		# Start the first service in the bouquet and show the service-name
		ref = self.ref_list[0]
		self.window_refs[0] = ref
		info = self.serviceHandler.info(ref)
		name = info.getName(ref).replace('\xc2\x86', '').replace('\xc2\x87', '')
		event_name = self.getEventName(info, ref)
		self["channel1"].setText(name)
		self["event1"].setText(event_name)
		self.session.nav.playService(ref)
		self["count"].setText(_("Channel: ") + "1 / " + str(len(self.ref_list)))
		self["playState"].instance.setPixmap(playingIcon)
		# Start updating the video-screenshots
		self.updateTimer.start(1, 1)

	def exit(self, callback=None):
		self.deleteConsoleCallbacks()
		self.close()

	def deleteConsoleCallbacks(self):
		if self.Console.appContainers.has_key(self.consoleCmd):
			del self.Console.appContainers[self.consoleCmd].dataAvail[:]
			del self.Console.appContainers[self.consoleCmd].appClosed[:]
			del self.Console.appContainers[self.consoleCmd]
			del self.Console.extra_args[self.consoleCmd]
			del self.Console.callbacks[self.consoleCmd]

	def closeWithOldService(self):
		self.session.nav.playService(self.oldService)
		self.deleteConsoleCallbacks()
		self.close()

	def numberPressed(self, number):
		ref = self.window_refs[number - 1]
		if ref is not None:
			self.session.nav.playService(ref)
			self.deleteConsoleCallbacks()
			self.close()

	def play(self):
		if self.working == False and self.state == self.PAUSE:
			self.state = self.PLAY
			self.updateTimer.start(1000, 1)
			self["playState"].instance.setPixmap(playingIcon)

	def pause(self):
		if self.working == False and self.state == self.PLAY:
			self.state = self.PAUSE
			self.updateTimer.stop()
			self["playState"].instance.setPixmap(pausedIcon)

	def countdownPlus(self):
		self.changeCountdown(1)

	def countdownMinus(self):
		self.changeCountdown(-1)

	def changeCountdown(self, direction):
		if self.working == False:
			configNow = config.plugins.Mosaic.countdown.value
			configNow += direction

			if configNow < config_limits[0]:
				configNow = config_limits[0]
			elif configNow > config_limits[1]:
				configNow = config_limits[1]

			config.plugins.Mosaic.countdown.value = configNow
			config.plugins.Mosaic.countdown.save()

			self.updateCountdownLabel()

	def makeNextScreenshot(self):
		# Grab video
		if not self.Console:
			self.Console = Console()
		self.consoleCmd = "%s -v -r %d -l -j 100 %s" % (grab_binary, self.windowWidth, grab_picture)
		self.Console.ePopen(self.consoleCmd, self.showNextScreenshot)

	def showNextScreenshot(self, result, retval, extra_args):
		if retval == 0:
			# Show screenshot in the current window
			pic = LoadPixmap(grab_picture)
			self["window" + str(self.current_window)].instance.setPixmap(pic)

			# Hide current video-window and show the running event-name
			self["video" + str(self.current_window)].hide()
			self["event" + str(self.current_window)].show()

			# Get next ref
			self.current_refidx += 1
			if self.current_refidx > (len(self.ref_list) - 1):
				self.current_refidx = 0

			# Play next ref
			ref = self.ref_list[self.current_refidx]
			info = self.serviceHandler.info(ref)
			name = info.getName(ref).replace('\xc2\x86', '').replace('\xc2\x87', '')
			event_name = self.getEventName(info, ref)
			self.session.nav.playService(ref)

			# Get next window index
			self.current_window += 1
			if self.current_window > 9:
				self.current_window = 1

			# Save the ref
			self.window_refs[self.current_window - 1] = ref

			# Save the event-name and hide the label
			self["event" + str(self.current_window)].hide()
			self["event" + str(self.current_window)].setText(event_name)

			# Show the new video-window
			self["video" + str(self.current_window)].show()
			self["video" + str(self.current_window)].decoder = 0

			# Show the servicename
			self["channel" + str(self.current_window)].setText(name)
			self["count"].setText(_("Channel: ") + str(self.current_refidx + 1) + " / " + str(len(self.ref_list)))

			# Restart timer
			self.working = False
			self.updateTimer.start(1, 1)
		else:
			print "[Mosaic] retval: %d result: %s" % (retval, result)

			try:
				f = open(grab_errorlog, "w")
				f.write("retval: %d\nresult: %s" % (retval, result))
				f.close()
			except:
				pass

			self.session.openWithCallback(self.exit, MessageBox, _("Error while creating screenshot. You need grab version 0.8 or higher!"), MessageBox.TYPE_ERROR, timeout=5)

	def updateCountdown(self, callback=None):
		self.countdown -= 1
		self.updateCountdownLabel()
		if self.countdown == 0:
			self.countdown = config.plugins.Mosaic.countdown.value
			self.working = True
			self.makeNextScreenshot()
		else:
			self.updateTimer.start(1000, 1)

	def updateCountdownLabel(self):
		self["countdown"].setText("%s %s / %s" % (_("Countdown:"), str(self.countdown), str(config.plugins.Mosaic.countdown.value)))

	def getEventName(self, info, ref):
		event = info.getEvent(ref)
		if event is not None:
			eventName = event.getEventName()
			if eventName is None:
				eventName = ""
		else:
			eventName = ""
		return eventName

################################################
# Most stuff stolen from the GraphMultiEPG

Session = None
Servicelist = None
BouquetSelectorScreen = None

def getBouquetServices(bouquet):
	services = []
	Servicelist = eServiceCenter.getInstance().list(bouquet)
	if Servicelist is not None:
		while True:
			service = Servicelist.getNext()
			if not service.valid():
				break
			if service.flags & (eServiceReference.isDirectory | eServiceReference.isMarker):
				continue
			services.append(service)
	return services

def closeBouquetSelectorScreen(ret=None):
	if BouquetSelectorScreen is not None:
		BouquetSelectorScreen.close()

def openMosaic(bouquet):
	if bouquet is not None:
		services = getBouquetServices(bouquet)
		if len(services):
			Session.openWithCallback(closeBouquetSelectorScreen, Mosaic, services)

def main(session, servicelist, **kwargs):
	global Session
	Session = session
	global Servicelist
	Servicelist = servicelist
	global BouquetSelectorScreen

	bouquets = Servicelist.getBouquetList()
	if bouquets is not None:
		if len(bouquets) == 1:
			openMosaic(bouquets[0][1])
		elif len(bouquets) > 1:
			BouquetSelectorScreen = Session.open(BouquetSelector, bouquets, openMosaic, enableWrapAround=True)

def Plugins(**kwargs):
	return PluginDescriptor(name=_("Mosaic"), where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main)
