from Screens.Screen import Screen
from Screens.Setup import SetupSummary
from Screens.MessageBox import MessageBox
from Components.ConfigList import ConfigList, ConfigListScreen
from Components.config import config, getConfigListEntry, ConfigSelection, ConfigSubsection, ConfigYesNo, ConfigSubDict
from Components.ServiceEventTracker import ServiceEventTracker
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.Pixmap import Pixmap
from enigma import iPlayableService, iServiceInformation, eTimer
from Plugins.Plugin import PluginDescriptor
from Plugins.SystemPlugins.Videomode.VideoHardware import video_hw # depends on Videomode Plugin

session = [ ]

default = (config.av.videomode[config.av.videoport.value].value, _("default"))
preferedmodes = [mode[0] for mode in video_hw.getModeList(config.av.videoport.value) if mode[0] != default[0]]
preferedmodes.append(default)
resolutions = (('sd_i_50', (_("SD 25/50HZ Interlace Mode"))), ('sd_i_60', (_("SD 30/60HZ Interlace Mode"))), \
			('sd_p_50', (_("SD 25/50HZ Progressive Mode"))), ('sd_p_60', (_("SD 30/60HZ Progressive Mode"))), \
			('hd_i', (_("HD Interlace Mode"))), ('hd_p', (_("HD Progressive Mode"))), \
			('p720_24', (_("Enable 720p24 Mode"))), ('p1080_24', (_("Enable 1080p24 Mode"))), \
			('p1080_25', (_("Enable 1080p25 Mode"))), ('p1080_30', (_("Enable 1080p30 Mode"))))

config.plugins.autoresolution = ConfigSubsection()
config.plugins.autoresolution.enable = ConfigYesNo(default = False)
config.plugins.autoresolution.videoresolution = ConfigSubDict()
videoresolution_dictionary = {}
for mode in resolutions:
	if mode[0].startswith('p1080'):
		choices = ['1080p24', '1080p25', '1080p30'] + preferedmodes
	elif mode[0] == 'p720_24':
		choices = ['720p24', '1080p24'] + preferedmodes
	else:
		choices = preferedmodes
	config.plugins.autoresolution.videoresolution[mode[0]] = ConfigSelection(default = default[0], choices = choices)
	videoresolution_dictionary[mode[0]] = (config.plugins.autoresolution.videoresolution[mode[0]])
config.plugins.autoresolution.showinfo = ConfigYesNo(default = True)
config.plugins.autoresolution.testmode = ConfigYesNo(default = False)
config.plugins.autoresolution.deinterlacer = ConfigSelection(default = "auto", choices =
		[("auto", _("auto")), ("off", _("off")), ("on", _("on"))])
config.plugins.autoresolution.delay_switch_mode = ConfigSelection(default = "1000", choices = [
		("1000", "1 " + _("second")), ("2000", "2 " + _("seconds")), ("3000", "3 " + _("seconds")),
		("4000", "4 " + _("seconds")), ("5000", "5 " + _("seconds")), ("6000", "6 " + _("seconds")), ("7000", "7 " + _("seconds")),
		("8000", "8 " + _("seconds")), ("9000", "9 " + _("seconds")), ("10000", "10 " + _("seconds"))])

def setDeinterlacer(configElement):
	mode = config.plugins.autoresolution.deinterlacer.value
	print "[AutoRes] switch deinterlacer mode to %s" % mode
	f = open('/proc/stb/vmpeg/deinterlace' , "w")
	f.write("%s\n" % mode)
	f.close()
config.plugins.autoresolution.deinterlacer.addNotifier(setDeinterlacer)

frqdic = { 23976: '24', \
		24000: '24', \
		25000: '25', \
		29970: '30', \
		30000: '30', \
		50000: '50', \
		59940: '60', \
		60000: '60'}

class AutoRes(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.__event_tracker = ServiceEventTracker(screen = self, eventmap =
			{
				iPlayableService.evVideoSizeChanged: self.__evVideoSizeChanged,
				iPlayableService.evVideoProgressiveChanged: self.__evVideoProgressiveChanged,
				iPlayableService.evVideoFramerateChanged: self.__evVideoFramerateChanged,
			})
		self.timer = eTimer()
		self.timer.callback.append(self.determineContent)
		self.lastmode = config.av.videomode[config.av.videoport.value].value

	def __evVideoFramerateChanged(self):
		print "[AutoRes] got event evFramerateChanged"
		if self.timer.isActive():
			self.timer.stop()
		if config.plugins.autoresolution.enable.value:
			self.timer.start(int(config.plugins.autoresolution.delay_switch_mode.value))

	def __evVideoSizeChanged(self):
		print "[AutoRes] got event evVideoSizeChanged"
		if self.timer.isActive():
			self.timer.stop()
		if config.plugins.autoresolution.enable.value:
			self.timer.start(int(config.plugins.autoresolution.delay_switch_mode.value))

	def __evVideoProgressiveChanged(self):
		print "[AutoRes] got event evVideoProgressiveChanged"
		if self.timer.isActive():
			self.timer.stop()
		if config.plugins.autoresolution.enable.value:
			self.timer.start(int(config.plugins.autoresolution.delay_switch_mode.value))

	def determineContent(self):
		self.timer.stop()
		service = session.nav.getCurrentService()
		info = service and service.info()
		height = info and info.getInfo(iServiceInformation.sVideoHeight)
		width = info and info.getInfo(iServiceInformation.sVideoWidth)
		framerate = info and info.getInfo(iServiceInformation.sFrameRate)
		frate = str(framerate)[:2] #fallback?
		if frqdic.has_key(framerate):
			frate = frqdic[framerate]
		progressive = info and info.getInfo(iServiceInformation.sProgressive)
		if progressive == 1:
			prog = 'p'
		else:
			prog = 'i'
		print "[AutoRes] new content is %sx%s%s%s" %(width, height, prog, frate)
		self.determineVideoMode(width, height, prog, frate)

	def determineVideoMode(self, width, height, prog, frate):
		if (height >= 900 or width >= 1600) and frate in ('24', '25', '30') and prog == 'p': 	# 1080p content
			new_mode = 'p1080_%s' % frate
		elif (height >= 576 or width >= 720) and frate == '24' and prog == 'p': 		# 720p24 detection
			new_mode = 'p720_24'
		elif height > 576 or width > 720: 							#asume higher then 576 or greater then 720 is hd content
			new_mode = 'hd_%s' % prog
		else:											# SD Content
			if frate in ('25', '50'):
				new_mode = 'sd_%s_50' % prog
			else:
				new_mode = 'sd_%s_60' % prog
		if videoresolution_dictionary.has_key(new_mode):
			new_mode = videoresolution_dictionary[new_mode].value
			print '[AutoRes] determined videomode', new_mode
			if new_mode != self.lastmode:
				self.lastmode = new_mode
				self.contentlabeltxt = "Videocontent: %sx%s%s %sHZ" % (width, height, prog, frate)
				self.changeVideomode(new_mode)

	def changeVideomode(self, mode):
		if mode.find("1080p") != -1 or mode.find("720p24") != -1:
			print "[AutoRes] switching to", mode
			v = open('/proc/stb/video/videomode' , "w")
			v.write("%s\n" % mode)
			v.close()
			resolutionlabeltxt = "Videomode: %s" % mode
		else:
			port = config.av.videoport.value
			rate = config.av.videorate[mode].value
			print "[AutoRes] switching to %s %s %s" % (port, mode, rate)
			video_hw.setMode(port, mode, rate)
			resolutionlabeltxt = 'Videomode: %s %s %s' % (port, mode, rate)
		if config.plugins.autoresolution.showinfo.value:
			resolutionlabel["restxt"].setText(resolutionlabeltxt)
			resolutionlabel["content"].setText(self.contentlabeltxt)
			resolutionlabel.show()
		if config.plugins.autoresolution.testmode.value:
			self.session.openWithCallback(
				self.confirm,
				MessageBox,
				_("Autoresolution Plugin Testmode:\nIs %s ok?") % (resolutionlabeltxt),
				MessageBox.TYPE_YESNO,
				timeout = 15,
				default = False
			)

	def confirm(self, confirmed):
		if not confirmed:
			port = config.av.videoport.value
			mode = config.av.videomode[port].value
			rate = config.av.videorate[mode].value
			if config.plugins.autoresolution.showinfo.value:
				resolutionlabel["restxt"].setText("Videomode: %s %s %s" % (port, mode, rate))
				resolutionlabel.show()
			video_hw.setMode(port, mode, rate)

class ResolutionLabel(Screen):
	skin = """
		<screen position="50,40" size="250,36" flags="wfNoBorder" >
			<widget name="content" position="0,0" size="250,18" font="Regular;16" />
			<widget name="restxt" position="0,18" size="250,18" font="Regular;16" />
		</screen>"""
	def __init__(self, session):
		Screen.__init__(self, session)

		self["content"] = Label()
		self["restxt"] = Label()

		self.hideTimer = eTimer()
		self.hideTimer.callback.append(self.hide)

		self.onShow.append(self.hide_me)
		self.onHide.append(self.clean_me)

	def hide_me(self):
		self.hideTimer.start(config.usage.infobar_timeout.index * 1500, True)

	def clean_me(self):
		self["restxt"].setText("")
		self["content"].setText("")


class AutoResSetupMenu(Screen, ConfigListScreen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skinName = "Setup"
		self.setup_title = _("Autoresolution videomode setup")

		self.onChangedEntry = [ ]
		self.list = [ ]
		ConfigListScreen.__init__(self, self.list, session = session, on_change = self.changedEntry)

		self["actions"] = ActionMap(["SetupActions"],
			{
				"cancel": self.keyCancel,
				"save": self.apply,
			}, -2)

		self["title"] = Label(_("Autoresolution settings"))

		self["oktext"] = Label(_("OK"))
		self["canceltext"] = Label(_("Cancel"))

		self["ok"] = Pixmap()
		self["cancel"] = Pixmap()

		self.createSetup()

	def createSetup(self):
		self.list = [
			getConfigListEntry(_("Enable Autoresolution"), config.plugins.autoresolution.enable)
		]
		if config.plugins.autoresolution.enable.value:
			for mode, label in resolutions:
				self.list.append(getConfigListEntry(label, videoresolution_dictionary[mode]))
			self.list.extend((
				getConfigListEntry(_("Show info screen"), config.plugins.autoresolution.showinfo),
				getConfigListEntry(_("Delay x seconds after service started"), config.plugins.autoresolution.delay_switch_mode),
				getConfigListEntry(_("Running in testmode"), config.plugins.autoresolution.testmode),
				getConfigListEntry(_("Deinterlacer mode"), config.plugins.autoresolution.deinterlacer)
			))
		self["config"].list = self.list
		self["config"].setList(self.list)

	def apply(self):
		for x in self["config"].list:
			x[1].save()
		self.close()

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.createSetup()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.createSetup()

	# for summary:
	def changedEntry(self):
		for x in self.onChangedEntry:
			x()

	def getCurrentEntry(self):
		return self["config"].getCurrent()[0]

	def getCurrentValue(self):
		return str(self["config"].getCurrent()[1].getText())

	def createSummary(self):
		return SetupSummary


def autostart(reason, **kwargs):
	global session, resolutionlabel
	if "session" in kwargs:
		session = kwargs["session"]
		resolutionlabel = session.instantiateDialog(ResolutionLabel)
		AutoRes(session)

def startSetup(menuid):
	if menuid != "system":
		return [ ]
	return [("Autoresolution...", autoresSetup, "autores_setup", 45)]

def autoresSetup(session, **kwargs):
	session.open(AutoResSetupMenu)

def Plugins(path, **kwargs):
	return [PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART], fnc = autostart), \
		PluginDescriptor(name="Autoresolution", description=_("Autoresolution Switch"), where = PluginDescriptor.WHERE_MENU, fnc=startSetup) ]
