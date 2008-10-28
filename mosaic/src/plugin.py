##
## Mosaic
## by AliAbdul
## needs the aio-screengrabber by seddi
##
from Components.ActionMap import NumberActionMap
from Components.AVSwitch import AVSwitch
from Components.config import config, ConfigSubsection, ConfigInteger
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.VideoWindow import VideoWindow
from enigma import eConsoleAppContainer, eServiceCenter, eServiceReference, eTimer, loadPic, loadPNG
from Plugins.Plugin import PluginDescriptor
from Screens.ChannelSelection import BouquetSelector
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.Directories import fileExists, resolveFilename, SCOPE_SKIN_IMAGE

################################################

grab_binary = "/usr/bin/grab"
grab_picture = "/tmp/.mosaic.bmp"

config_limits = (3, 30)
config.plugins.Mosaic = ConfigSubsection()
config.plugins.Mosaic.countdown = ConfigInteger(default=5, limits=config_limits)

playingIcon = loadPNG(resolveFilename(SCOPE_SKIN_IMAGE, 'skin_default/icons/ico_mp_play.png'))
pausedIcon = loadPNG(resolveFilename(SCOPE_SKIN_IMAGE, 'skin_default/icons/ico_mp_pause.png'))

Session = None
Servicelist = None
bouquetSel = None
dlg_stack = []

################################################

class Mosaic(Screen):
	PLAY = 0
	PAUSE = 1

	skin = """
	<screen position="0,0" size="720,576" title="Mosaic" flags="wfNoBorder" backgroundColor="#ffffff" >
		<widget name="playState" position="55,55" size="16,16" alphatest="on" />
		<eLabel position="78,54" size="180,144" />
		<eLabel position="274,54" size="180,144" />
		<eLabel position="470,54" size="180,144" />
		<eLabel position="78,221" size="180,144" />
		<eLabel position="274,221" size="180,144" />
		<eLabel position="470,221" size="180,144" />
		<eLabel position="78,388" size="180,144" />
		<eLabel position="274,388" size="180,144" />
		<eLabel position="470,388" size="180,144" />
		<widget name="channel1" position="80,32" size="176,20" font="Regular;18" backgroundColor="#ffffff" foregroundColor="#000000" />
		<widget name="channel2" position="276,32" size="176,20" font="Regular;18" backgroundColor="#ffffff" foregroundColor="#000000" />
		<widget name="channel3" position="472,32" size="176,20" font="Regular;18" backgroundColor="#ffffff" foregroundColor="#000000" />
		<widget name="channel4" position="80,198" size="176,20" font="Regular;18" backgroundColor="#ffffff" foregroundColor="#000000" />
		<widget name="channel5" position="276,198" size="176,20" font="Regular;18" backgroundColor="#ffffff" foregroundColor="#000000" />
		<widget name="channel6" position="472,198" size="176,20" font="Regular;18" backgroundColor="#ffffff" foregroundColor="#000000" />
		<widget name="channel7" position="80,366" size="176,20" font="Regular;18" backgroundColor="#ffffff" foregroundColor="#000000" />
		<widget name="channel8" position="276,366" size="176,20" font="Regular;18" backgroundColor="#ffffff" foregroundColor="#000000" />
		<widget name="channel9" position="472,366" size="176,20" font="Regular;18" backgroundColor="#ffffff" foregroundColor="#000000" />
		<widget name="window1" position="78,54" zPosition="1" size="180,144" />
		<widget name="window2" position="274,54" zPosition="1" size="180,144" />
		<widget name="window3" position="470,54" zPosition="1" size="180,144" />
		<widget name="window4" position="78,221" zPosition="1" size="180,144" />
		<widget name="window5" position="274,221" zPosition="1" size="180,144" />
		<widget name="window6" position="470,221" zPosition="1" size="180,144" />
		<widget name="window7" position="78,388" zPosition="1" size="180,144" />
		<widget name="window8" position="274,388" zPosition="1" size="180,144" />
		<widget name="window9" position="470,388" zPosition="1" size="180,144" />
		<widget name="video1" position="78,54" zPosition="2" size="180,144" backgroundColor="#ffffffff" />
		<widget name="video2" position="274,54" zPosition="2" size="180,144" backgroundColor="#ffffffff" />
		<widget name="video3" position="470,54" zPosition="2" size="180,144" backgroundColor="#ffffffff" />
		<widget name="video4" position="78,221" zPosition="2" size="180,144" backgroundColor="#ffffffff" />
		<widget name="video5" position="274,221" zPosition="2" size="180,144" backgroundColor="#ffffffff" />
		<widget name="video6" position="470,221" zPosition="2" size="180,144" backgroundColor="#ffffffff" />
		<widget name="video7" position="78,388" zPosition="2" size="180,144" backgroundColor="#ffffffff" />
		<widget name="video8" position="274,388" zPosition="2" size="180,144" backgroundColor="#ffffffff" />
		<widget name="video9" position="470,388" zPosition="2" size="180,144" backgroundColor="#ffffffff" />
		<widget name="event1" position="78,54" size="180,20" zPosition="3" font="Regular;18" backgroundColor="#000000" foregroundColor="#ffffff" />
		<widget name="event2" position="274,54" size="180,20" zPosition="3" font="Regular;18" backgroundColor="#000000" foregroundColor="#ffffff" />
		<widget name="event3" position="470,54" size="180,20" zPosition="3" font="Regular;18" backgroundColor="#000000" foregroundColor="#ffffff" />
		<widget name="event4" position="78,221" size="180,20" zPosition="3" font="Regular;18" backgroundColor="#000000" foregroundColor="#ffffff" />
		<widget name="event5" position="274,221" size="180,20" zPosition="3" font="Regular;18" backgroundColor="#000000" foregroundColor="#ffffff" />
		<widget name="event6" position="470,221" size="180,20" zPosition="3" font="Regular;18" backgroundColor="#000000" foregroundColor="#ffffff" />
		<widget name="event7" position="78,388" size="180,20" zPosition="3" font="Regular;18" backgroundColor="#000000" foregroundColor="#ffffff" />
		<widget name="event8" position="274,388" size="180,20" zPosition="3" font="Regular;18" backgroundColor="#000000" foregroundColor="#ffffff" />
		<widget name="event9" position="470,388" size="180,20" zPosition="3" font="Regular;18" backgroundColor="#000000" foregroundColor="#ffffff" />
		<widget name="countdown" position="80,535" size="175,20" font="Regular;18" backgroundColor="#ffffff" foregroundColor="#000000" />
		<widget name="count" position="472,535" size="175,20" font="Regular;18" backgroundColor="#ffffff" foregroundColor="#000000" halign="right" />
	</screen>"""

	def __init__(self, session, services):
		Screen.__init__(self, session)
		
		self.session = session
		self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
		self.container = eConsoleAppContainer()
		self.aspect = AVSwitch().getAspectRatioSetting()
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
			self["video" + str(i)] = VideoWindow(decoder = 0)
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
				"ok": self.close,
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
		self.updateTimer.timeout.get().append(self.updateCountdown)
		self.checkTimer = eTimer()
		self.checkTimer.timeout.get().append(self.checkGrab)
		
		self.container.appClosed.append(self.showNextScreenshot)
		self.checkTimer.start(500, 1)

	def checkGrab(self):
		if fileExists(grab_binary):
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
		else:
			self.session.openWithCallback(self.exit, MessageBox, _("%s does not exist!") % grab_binary, MessageBox.TYPE_ERROR, timeout=5)

	def exit(self, callback=None):
		self.close()

	def closeWithOldService(self):
		self.session.nav.playService(self.oldService)
		self.close()

	def numberPressed(self, number):
		ref = self.window_refs[number-1]
		if ref is not None:
			self.session.nav.playService(ref)
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
		if self.container.execute("%s -v %s" % (grab_binary, grab_picture)):
			self.showNextScreenshot(-1)

	def showNextScreenshot(self, callback):
		# Resize screenshot and show in the current window
		picture = loadPic(grab_picture, 180, 144, self.aspect, 1, 0, 1)
		self["window" + str(self.current_window)].instance.setPixmap(picture)
		
		# Hide current video-window and show the running event-name
		self["video" + str(self.current_window)].hide()
		self["event" + str(self.current_window)].show()
		
		# Get next ref
		self.current_refidx += 1
		if self.current_refidx > (len(self.ref_list) -1):
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
		self.window_refs[self.current_window-1] = ref
		
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

def getBouquetServices(bouquet):
	services = []
	Servicelist = eServiceCenter.getInstance().list(bouquet)
	if not Servicelist is None:
		while True:
			service = Servicelist.getNext()
			if not service.valid():
				break
			if service.flags & (eServiceReference.isDirectory | eServiceReference.isMarker):
				continue
			services.append(service)
	return services

def openMosaic(bouquet):
	services = getBouquetServices(bouquet)
	if len(services):
		dlg_stack.append(Session.openWithCallback(closed, Mosaic, services))
		return True
	return False

def cleanup():
	global Session
	Session = None
	global Servicelist
	Servicelist = None

def closed(ret=False):
	closedScreen = dlg_stack.pop()
	global bouquetSel
	if bouquetSel and closedScreen == bouquetSel:
		bouquetSel = None
	dlgs = len(dlg_stack)
	if ret and dlgs > 0:
		dlg_stack[dlgs-1].close(dlgs > 1)
	if dlgs <= 0:
		cleanup()

def main(session, servicelist, **kwargs):
	global Session
	Session = session
	global Servicelist
	Servicelist = servicelist
	
	bouquets = Servicelist.getBouquetList()
	if bouquets is None:
		cnt = 0
	else:
		cnt = len(bouquets)
	
	if cnt > 1:
		global bouquetSel
		bouquetSel = Session.openWithCallback(closed, BouquetSelector, bouquets, openMosaic, enableWrapAround=True)
		dlg_stack.append(bouquetSel)
	elif cnt == 1:
		if not openMosaic(bouquets[0][1]):
			cleanup()

def Plugins(**kwargs):
	return PluginDescriptor(name=_("Mosaic"), where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=main)
